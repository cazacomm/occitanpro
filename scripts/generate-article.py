#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Génération automatique d'un article de blog pour Occitan Pro.

Principe (identique au setup Adesign) :
  1. lit blog-config.json
  2. extrait la liste des sujets suggérés de BLOG_WORKFLOW.md (§ « sujets d'articles suggérés »)
  3. scanne /blog/*/index.html pour savoir quels sujets sont déjà traités (marqueur d'idempotence)
  4. choisit le prochain sujet non traité, dans l'ordre séquentiel
  5. demande le contenu à l'API OpenAI (JSON strict)
  6. valide le contenu (longueur, FAQ, règles éditoriales de BLOG_WORKFLOW.md)
  7. relit le GABARIT depuis l'article existant (jamais de template dupliqué ici)
  8. écrit /blog/<slug>/index.html, ajoute la carte dans /blog/index.html,
     met à jour sitemap.xml, rss.xml et llms.txt

Aucune écriture n'a lieu avant que TOUT ait été généré et validé : en cas d'échec,
le dépôt reste strictement inchangé.

Codes de sortie :
   0  un article a été généré (ou simulé en --dry-run)
   1  erreur
  78  aucun sujet nouveau à traiter (rien à faire, ce n'est pas une erreur)
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import unicodedata
from datetime import datetime, timezone, timedelta

# --------------------------------------------------------------------------- #
# Constantes
# --------------------------------------------------------------------------- #

EXIT_OK = 0
EXIT_ERROR = 1
EXIT_NOTHING_TO_DO = 78

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
CONFIG_PATH = os.path.join(ROOT, "blog-config.json")

MONTHS_FR = {
    1: "janvier", 2: "février", 3: "mars", 4: "avril", 5: "mai", 6: "juin",
    7: "juillet", 8: "août", 9: "septembre", 10: "octobre", 11: "novembre",
    12: "décembre",
}
DAYS_EN = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
MONTHS_EN = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
             "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")

# Règles éditoriales de BLOG_WORKFLOW.md : rien de tout ceci ne doit être inventé.
FORBIDDEN_PATTERNS = [
    (r"\d[\d\s]*(?:€|euros?\b)", "montant en euros"),
    (r"\d+(?:[.,]\d+)?\s*%", "pourcentage chiffré"),
    (r"\barticle\s+L\.?\s*\d", "référence à un article de loi"),
    (r"\b(?:fondé|créé|crée|existe)\s+(?:en|depuis)\s+(?:19|20)\d{2}", "date de fondation"),
    (r"\bdepuis\s+(?:19|20)\d{2}\b", "date de fondation"),
    (r"\bSIRET\b", "mention SIRET"),
    (r"\bdécret\s+n[°o]", "référence réglementaire"),
    (r"\bnorme\s+NF\s?[A-Z]", "référence normative"),
]

# --------------------------------------------------------------------------- #
# Log
# --------------------------------------------------------------------------- #


def log(msg: str) -> None:
    print(msg, flush=True)


def fail(msg: str) -> "NoReturn":  # type: ignore[valid-type]
    log("[ERREUR] %s" % msg)
    sys.exit(EXIT_ERROR)


# --------------------------------------------------------------------------- #
# Utilitaires
# --------------------------------------------------------------------------- #


def read(path: str) -> str:
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def slugify(value: str) -> str:
    value = unicodedata.normalize("NFKD", value)
    value = "".join(c for c in value if not unicodedata.combining(c))
    value = value.lower().replace("'", " ").replace("’", " ")
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return re.sub(r"-{2,}", "-", value).strip("-")


def strip_tags(html: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html)).strip()


def word_count(html: str) -> int:
    return len(strip_tags(html).split())


def esc_attr(text: str) -> str:
    return (text.replace("&", "&amp;").replace('"', "&quot;")
                .replace("<", "&lt;").replace(">", "&gt;"))


def date_fr(dt: datetime) -> str:
    return "%d %s %d" % (dt.day, MONTHS_FR[dt.month], dt.year)


def date_rfc822(dt: datetime) -> str:
    return "%s, %02d %s %d 09:00:00 +0200" % (
        DAYS_EN[dt.weekday()], dt.day, MONTHS_EN[dt.month - 1], dt.year)


# --------------------------------------------------------------------------- #
# 1. Configuration
# --------------------------------------------------------------------------- #


def load_config() -> dict:
    if not os.path.exists(CONFIG_PATH):
        fail("blog-config.json introuvable (%s)" % CONFIG_PATH)
    try:
        cfg = json.loads(read(CONFIG_PATH))
    except json.JSONDecodeError as exc:
        fail("blog-config.json illisible : %s" % exc)
    for key in ("site_name", "site_url", "reference_article", "workflow_doc"):
        if not cfg.get(key):
            fail("clé manquante dans blog-config.json : %s" % key)
    cfg["site_url"] = cfg["site_url"].rstrip("/")
    return cfg


# --------------------------------------------------------------------------- #
# 2. Sujets suggérés (BLOG_WORKFLOW.md)
# --------------------------------------------------------------------------- #


def parse_topics(cfg: dict) -> list[dict]:
    """Extrait la liste numérotée de la section « sujets d'articles suggérés »."""
    path = os.path.join(ROOT, cfg["workflow_doc"])
    if not os.path.exists(path):
        fail("%s introuvable" % cfg["workflow_doc"])
    doc = read(path)

    start = re.search(r"^##\s+.*sujets d'articles suggér", doc, re.M | re.I)
    if not start:
        fail("section « sujets d'articles suggérés » absente de %s" % cfg["workflow_doc"])
    rest = doc[start.end():]
    nxt = re.search(r"^##\s+", rest, re.M)
    section = rest[: nxt.start()] if nxt else rest

    topics = []
    for m in re.finditer(r"^(\d+)\.\s+\*\*(.+?)\*\*\s*(?:[—–-]\s*(.*))?$", section, re.M):
        topics.append({
            "n": int(m.group(1)),
            "title": m.group(2).strip(),
            "hint": (m.group(3) or "").strip(),
        })
    if not topics:
        fail("aucun sujet numéroté trouvé dans %s" % cfg["workflow_doc"])
    topics.sort(key=lambda t: t["n"])
    return topics


# --------------------------------------------------------------------------- #
# 3. Articles déjà publiés
# --------------------------------------------------------------------------- #


def scan_existing(cfg: dict) -> tuple[set[int], set[str]]:
    """Renvoie (numéros de sujets déjà traités, slugs existants)."""
    blog_dir = os.path.join(ROOT, "blog")
    marker_re = re.compile(
        r"<!--\s*%s:\s*(\d+)\s*-->" % re.escape(cfg.get("topic_marker_prefix", "topic")))
    done: set[int] = set()
    slugs: set[str] = set()

    if not os.path.isdir(blog_dir):
        fail("répertoire /blog introuvable")

    for name in sorted(os.listdir(blog_dir)):
        article = os.path.join(blog_dir, name, "index.html")
        if not os.path.isfile(article):
            continue
        slugs.add(name)
        m = marker_re.search(read(article))
        if m:
            done.add(int(m.group(1)))
    return done, slugs


def pick_topic(topics: list[dict], done: set[int], slugs: set[str],
               forced: int | None) -> dict | None:
    if forced is not None:
        for t in topics:
            if t["n"] == forced:
                if t["n"] in done:
                    log("[INFO] sujet %d déjà traité (marqueur présent)." % forced)
                    return None
                return t
        fail("sujet %d absent de la liste" % forced)

    for t in topics:
        if t["n"] in done:
            continue
        if slugify(t["title"])[:60] in slugs:
            log("[INFO] sujet %d : un dossier de slug proche existe déjà, ignoré." % t["n"])
            continue
        return t
    return None


# --------------------------------------------------------------------------- #
# 4. Appel OpenAI
# --------------------------------------------------------------------------- #


def build_prompt(cfg: dict, topic: dict) -> tuple[str, str]:
    links = "\n".join(
        "- <a href=\"%s\">%s</a>" % (l["href"], l["label"])
        for l in cfg.get("internal_links", []))
    facts = "\n".join("- %s" % f for f in cfg.get("facts", []))
    kw = ", ".join(cfg.get("geo_keywords", []))
    n_faq = int(cfg.get("faq_questions_count", 5))
    target = int(cfg.get("target_word_count", 1300))

    system = (
        "Tu es rédacteur web SEO francophone spécialisé dans le contenu local pour TPE. "
        "Tu écris pour %s, %s, implanté en %s. "
        "Ton : %s. Tu écris en %s, à la voix active, sans superlatifs creux ni jargon marketing. "
        "Tu réponds UNIQUEMENT avec un objet JSON valide, sans texte autour."
        % (cfg["site_name"], cfg["sector"], cfg["location"],
           cfg.get("tone", "expert-conseil"), cfg.get("language", "fr"))
    )

    user = f"""Rédige un article de blog complet sur le sujet suivant.

SUJET N°{topic['n']} : {topic['title']}
ANGLE ATTENDU : {topic['hint'] or 'à traiter de manière pratique et concrète'}

ANCRAGE LOCAL OBLIGATOIRE
Cite naturellement le territoire dans le corps du texte. Mots-clés géographiques
disponibles : {kw}.

FAITS VÉRIFIÉS SUR LE CLUB (les seuls que tu as le droit d'affirmer)
{facts}

INTERDICTIONS ABSOLUES (règles éditoriales du client, aucune exception)
- Ne JAMAIS inventer de prix, tarif, montant, fourchette de prix ou cotisation.
- Ne JAMAIS inventer de chiffre précis : statistique, pourcentage, nombre de clients,
  chiffre d'affaires, nombre de recommandations.
- Ne JAMAIS inventer de nom de client, de témoignage ou de citation.
- Ne JAMAIS inventer de réglementation, d'obligation légale, de norme ou de référence de texte.
- Ne JAMAIS inventer de date de fondation du club ni d'événement non listé dans les faits ci-dessus.
En cas de doute sur un chiffre, formule-le qualitativement
(« une vingtaine de membres », « plusieurs secteurs ») au lieu de l'inventer.

LIENS INTERNES
Insère 2 à 3 de ces liens dans le corps du texte, en HTML, avec une ancre naturelle :
{links}

FORMAT DE SORTIE — un objet JSON avec exactement ces clés :
{{
  "slug": "slug-en-minuscules-avec-tirets, 3 à 6 mots, sans accent, contenant le mot-clé principal et si possible l'ancrage local",
  "seo_title": "titre de la balise <title>, 50 à 60 caractères, sans le nom du site",
  "title": "titre H1 de l'article, accrocheur et explicite",
  "breadcrumb_label": "libellé court pour le fil d'ariane, 3 à 6 mots",
  "meta_description": "une seule phrase de MOINS DE 150 caractères, avec l'ancrage local",
  "category": "étiquette de rubrique en 1 à 3 mots",
  "excerpt": "résumé de 2 à 3 phrases pour la carte du blog et le flux RSS",
  "cover_alt": "texte alternatif descriptif de l'image de couverture",
  "lead": "chapô de 3 à 5 lignes en texte brut, sans balise HTML",
  "body_html": "le corps de l'article en HTML",
  "faq_heading": "titre H2 de la section FAQ",
  "faq": [{{"question": "...", "answer": "..."}}]
}}

CONTRAINTES DE CONTENU
- "body_html" fait environ {target} mots (entre 1200 et 1500), et NE CONTIENT NI le chapô,
  NI la FAQ, NI d'appel à l'action final : ces éléments sont ajoutés séparément.
- "body_html" n'utilise QUE ces balises : <h2>, <h3>, <p>, <ul>, <ol>, <li>, <strong>, <em>, <a>.
  Jamais de <h1>, <script>, <style>, <img>, <div> ni d'attribut de style.
- Structure : 4 à 6 sections <h2>, dont plusieurs avec des sous-parties <h3>.
- Au moins une liste (<ul> ou <ol>).
- "faq" contient exactement {n_faq} questions. Les réponses sont en TEXTE BRUT
  (aucune balise HTML), de 2 à 4 phrases, et répondent directement à la question.
- Tout le contenu est en français, avec les apostrophes typographiques normales (').
"""
    return system, user


def call_openai(cfg: dict, system: str, user: str, extra: str | None = None) -> dict:
    try:
        from openai import OpenAI
    except ImportError:
        fail("le paquet 'openai' n'est pas installé (pip install openai)")

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        fail("variable d'environnement OPENAI_API_KEY absente")

    messages = [{"role": "system", "content": system},
                {"role": "user", "content": user}]
    if extra:
        messages.append({"role": "user", "content": extra})

    client = OpenAI(api_key=api_key)
    try:
        resp = client.chat.completions.create(
            model=cfg.get("openai_model", "gpt-4o-mini"),
            temperature=float(cfg.get("openai_temperature", 0.7)),
            response_format={"type": "json_object"},
            messages=messages,
        )
    except Exception as exc:  # réseau, quota, auth, modèle indisponible…
        fail("appel OpenAI échoué : %s" % exc)

    content = (resp.choices[0].message.content or "").strip()
    if hasattr(resp, "usage") and resp.usage:
        log("[INFO] tokens : %s prompt + %s completion"
            % (resp.usage.prompt_tokens, resp.usage.completion_tokens))
    try:
        return json.loads(content)
    except json.JSONDecodeError as exc:
        fail("réponse OpenAI non parsable en JSON : %s" % exc)


def mock_payload(cfg: dict, topic: dict) -> dict:
    """Contenu factice hors ligne, pour tester la chaîne sans appeler l'API."""
    n_faq = int(cfg.get("faq_questions_count", 5))
    words = [w for w in slugify(topic["title"]).split("-")
             if w not in ("le", "la", "les", "un", "une", "des", "de", "du", "d", "a",
                          "au", "aux", "en", "et", "dans", "pour", "sur", "l")]
    slug = "-".join(words[:6])
    return {
        "slug": slug,
        "seo_title": topic["title"][:60],
        "title": topic["title"],
        "breadcrumb_label": " ".join(topic["title"].split()[:5]),
        "meta_description": ("%s : les repères concrets pour les professionnels "
                             "des Hautes-Pyrénées." % topic["title"])[:149],
        "category": "Réseau local",
        "excerpt": "Contenu de démonstration généré hors ligne pour valider la chaîne "
                   "de publication. Le texte définitif est produit par l'API OpenAI.",
        "cover_alt": "Entrepreneurs des Hautes-Pyrénées réunis lors d'une soirée du club Occitan Pro",
        "lead": "Ceci est un chapô de démonstration produit en mode hors ligne. Il sert "
                "uniquement à vérifier que le gabarit, les liens et les données structurées "
                "sont correctement assemblés.",
        "body_html": (
            "<h2>Section de démonstration</h2>\n"
            "<p>Texte de démonstration ancré en <strong>Hautes-Pyrénées</strong>, autour de "
            "Tarbes et de la Bigorre. Voir <a href=\"../../principe.html\">le principe du club</a> "
            "et <a href=\"../../entreprises.html\">les entrepreneurs membres</a>.</p>\n"
            "<h3>Sous-partie</h3>\n"
            "<ul>\n<li>Premier point.</li>\n<li>Deuxième point.</li>\n</ul>\n"
            "<h2>Seconde section</h2>\n"
            "<p>Le club se retrouve une fois par mois, le jeudi, dans un lieu qui change à "
            "chaque réunion.</p>"
        ),
        "faq_heading": "Questions fréquentes",
        "faq": [
            {"question": "Question de démonstration n°%d ?" % (i + 1),
             "answer": "Réponse de démonstration en texte brut, produite hors ligne pour "
                       "valider l'assemblage du bloc FAQ et du JSON-LD FAQPage."}
            for i in range(n_faq)
        ],
    }


# --------------------------------------------------------------------------- #
# 5. Validation
# --------------------------------------------------------------------------- #


REQUIRED_KEYS = ("slug", "seo_title", "title", "breadcrumb_label", "meta_description",
                 "category", "excerpt", "cover_alt", "lead", "body_html", "faq")


def validate(cfg: dict, payload: dict, slugs: set[str], lenient: bool) -> list[str]:
    """Renvoie la liste des problèmes bloquants (vide = contenu accepté)."""
    problems: list[str] = []

    for key in REQUIRED_KEYS:
        if not payload.get(key):
            problems.append("clé absente ou vide : %s" % key)
    if problems:
        return problems

    slug = payload["slug"] = slugify(str(payload["slug"]))
    if not SLUG_RE.match(slug):
        problems.append("slug invalide : %r" % slug)
    if slug in slugs:
        problems.append("le dossier /blog/%s existe déjà" % slug)
    if not 3 <= len(slug.split("-")) <= 8:
        problems.append("slug de longueur inhabituelle : %r" % slug)

    desc = payload["meta_description"].strip()
    if len(desc) >= 155:
        problems.append("meta description trop longue (%d caractères, max 154)" % len(desc))

    n_faq = int(cfg.get("faq_questions_count", 5))
    faq = payload.get("faq") or []
    if len(faq) != n_faq:
        problems.append("la FAQ contient %d questions au lieu de %d" % (len(faq), n_faq))
    for i, item in enumerate(faq, 1):
        if not isinstance(item, dict) or not item.get("question") or not item.get("answer"):
            problems.append("FAQ n°%d incomplète" % i)
            continue
        if re.search(r"<[a-zA-Z/]", str(item["answer"])):
            problems.append("FAQ n°%d : la réponse contient du HTML" % i)

    body = payload["body_html"]
    for bad in ("<h1", "<script", "<style", "<img", "<div", "<iframe", "style="):
        if bad in body.lower():
            problems.append("balise/attribut interdit dans le corps : %s" % bad)
    if "<h2" not in body.lower():
        problems.append("aucun <h2> dans le corps de l'article")

    words = word_count(body)
    if words < 1000:
        msg = "corps trop court : %d mots (minimum 1000)" % words
        if lenient:
            log("[WARN] %s — toléré en mode --mock" % msg)
        else:
            problems.append(msg)
    elif not 1200 <= words <= 1500:
        log("[WARN] corps de %d mots, hors de la fourchette 1200-1500 recommandée" % words)
    else:
        log("[INFO] corps de %d mots" % words)

    haystack = " ".join([body, payload["lead"], payload["excerpt"],
                         " ".join("%s %s" % (f.get("question", ""), f.get("answer", ""))
                                  for f in faq if isinstance(f, dict))])
    for pattern, label in FORBIDDEN_PATTERNS:
        m = re.search(pattern, haystack, re.I)
        if m:
            problems.append("règle éditoriale violée (%s) : %r" % (label, m.group(0)[:60]))

    return problems


# --------------------------------------------------------------------------- #
# 6. Rendu de l'article, à partir du GABARIT lu sur disque
# --------------------------------------------------------------------------- #


def render_faq_html(payload: dict) -> str:
    parts = []
    for item in payload["faq"]:
        parts.append(
            '            <div class="faq-item">\n'
            '              <h3>%s</h3>\n'
            '              <p>%s</p>\n'
            '            </div>' % (item["question"].strip(), item["answer"].strip()))
    return "\n".join(parts)


def render_body(payload: dict) -> str:
    lines = ['          <p class="article-lead">%s</p>' % payload["lead"].strip(), ""]
    for raw in payload["body_html"].strip().splitlines():
        stripped = raw.strip()
        lines.append("          " + stripped if stripped else "")
    lines += [
        "",
        "          <h2>%s</h2>" % payload.get("faq_heading", "Questions fréquentes").strip(),
        '          <div class="faq-list">',
        render_faq_html(payload),
        "          </div>",
        "",
    ]
    return "\n".join(lines)


def build_jsonld(cfg: dict, payload: dict, url: str, cover_url: str, today: str) -> str:
    site = cfg["site_url"]
    article = {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": payload["title"],
        "description": payload["meta_description"],
        "image": cover_url,
        "inLanguage": "fr-FR",
        "datePublished": today,
        "dateModified": today,
        "author": {"@type": "Organization", "name": cfg["author"], "url": site},
        "publisher": {
            "@type": "Organization",
            "name": cfg["site_name"],
            "url": site,
            "logo": {"@type": "ImageObject", "url": "%s/assets/logo.jpg" % site},
        },
        "mainEntityOfPage": {"@type": "WebPage", "@id": url},
        "about": payload.get("category", ""),
        "spatialCoverage": {"@type": "AdministrativeArea", "name": "Hautes-Pyrénées, France"},
    }
    crumbs = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Accueil", "item": "%s/" % site},
            {"@type": "ListItem", "position": 2, "name": "Blog", "item": "%s/blog/" % site},
            {"@type": "ListItem", "position": 3,
             "name": payload["breadcrumb_label"], "item": url},
        ],
    }
    faq = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {"@type": "Question", "name": item["question"].strip(),
             "acceptedAnswer": {"@type": "Answer", "text": item["answer"].strip()}}
            for item in payload["faq"]
        ],
    }
    blocks = []
    for obj in (article, crumbs, faq):
        body = json.dumps(obj, ensure_ascii=False, indent=2)
        body = "\n".join("  " + line for line in body.splitlines())
        blocks.append('  <script type="application/ld+json">\n%s\n  </script>\n' % body)
    return "".join(blocks)


def sub_once(pattern: str, repl: str, text: str, label: str, flags=0) -> str:
    """Remplace UNE occurrence par du texte littéral (aucune backreference n'est
    interprétée : le contenu généré peut contenir n'importe quel caractère)."""
    new, n = re.subn(pattern, lambda m: repl, text, count=1, flags=flags)
    if n != 1:
        fail("gabarit : ancre introuvable ou ambiguë (%s)" % label)
    return new


def render_article(cfg: dict, payload: dict, topic: dict, today: datetime) -> str:
    """Part du fichier de référence sur disque et n'en remplace que les zones de contenu."""
    ref_path = os.path.join(ROOT, cfg["reference_article"])
    if not os.path.exists(ref_path):
        fail("article de référence introuvable : %s" % cfg["reference_article"])
    html = read(ref_path)

    site = cfg["site_url"]
    slug = payload["slug"]
    url = "%s/blog/%s/" % (site, slug)
    cover_rel = cfg.get("cover_images", ["assets/affaires.jpg"])[
        topic["n"] % len(cfg.get("cover_images", ["assets/affaires.jpg"]))]
    cover_url = "%s/%s" % (site, cover_rel)
    iso = today.strftime("%Y-%m-%d")

    og_title = esc_attr(payload["title"].strip())
    desc = esc_attr(payload["meta_description"].strip())

    # ---- <head> ----
    html = sub_once(r"<title>.*?</title>",
                    "<title>%s – %s</title>" % (payload["seo_title"].strip(), cfg["site_name"]),
                    html, "<title>", re.S)
    html = sub_once(r'<meta name="description" content="[^"]*"',
                    '<meta name="description" content="%s"' % desc, html, "meta description")
    for prop, value in (("og:url", url), ("og:title", og_title), ("og:description", desc),
                        ("og:image", cover_url), ("article:published_time", iso)):
        html = sub_once(r'<meta property="%s" content="[^"]*"' % re.escape(prop),
                        '<meta property="%s" content="%s"' % (prop, value), html, prop)
    for name, value in (("twitter:title", og_title), ("twitter:description", desc),
                        ("twitter:image", cover_url)):
        html = sub_once(r'<meta name="%s" content="[^"]*"' % re.escape(name),
                        '<meta name="%s" content="%s"' % (name, value), html, name)
    html = sub_once(r'<link rel="canonical" href="[^"]*"',
                    '<link rel="canonical" href="%s"' % url, html, "canonical")

    # ---- données structurées : on remplace les 3 blocs d'un coup ----
    html = sub_once(r'  <script type="application/ld\+json">.*</script>\n(?=</head>)',
                    build_jsonld(cfg, payload, url, cover_url, iso),
                    html, "blocs JSON-LD", re.S)

    # ---- marqueur d'idempotence ----
    marker = "<!-- %s: %d -->" % (cfg.get("topic_marker_prefix", "topic"), topic["n"])
    html = sub_once(r"<body>\n", "<body>\n%s\n" % marker, html, "<body>")

    # ---- fil d'ariane, titre, méta, couverture ----
    html = sub_once(r'<span aria-current="page">[^<]*</span>',
                    '<span aria-current="page">%s</span>' % payload["breadcrumb_label"].strip(),
                    html, "fil d'ariane")
    html = sub_once(r"          <h1>.*?</h1>",
                    "          <h1>%s</h1>" % payload["title"].strip(),
                    html, "<h1>", re.S)
    html = sub_once(r'<time datetime="[^"]*">[^<]*</time>',
                    '<time datetime="%s">%s</time>' % (iso, date_fr(today)),
                    html, "<time>")
    html = sub_once(r'<span>Par [^<]*</span>\n            <span class="dot">•</span>\n'
                    r"            <span>[^<]*</span>",
                    '<span>Par %s</span>\n            <span class="dot">•</span>\n'
                    "            <span>%s</span>" % (cfg["author"], payload["category"].strip()),
                    html, "rubrique")
    html = sub_once(r'<div class="article-cover">\n          <img src="[^"]*" alt="[^"]*"',
                    '<div class="article-cover">\n          <img src="../../%s" alt="%s"'
                    % (cover_rel, esc_attr(payload["cover_alt"])),
                    html, "image de couverture")

    # ---- corps ----
    html = sub_once(r'<div class="article-body">\n.*?\n        </div>\n      </article>',
                    '<div class="article-body">\n%s\n        </div>\n      </article>'
                    % render_body(payload),
                    html, "corps de l'article", re.S)

    return html


# --------------------------------------------------------------------------- #
# 7. Mise à jour de l'index, du sitemap, du flux RSS et de llms.txt
# --------------------------------------------------------------------------- #


def update_blog_index(cfg: dict, payload: dict, today: datetime) -> str:
    path = os.path.join(ROOT, "blog", "index.html")
    html = read(path)
    slug = payload["slug"]
    iso = today.strftime("%Y-%m-%d")
    cover_rel = None
    m = re.search(r'<meta property="og:image" content="[^"]*/(assets/[^"]+)"', html)
    cover_rel = m.group(1) if m else "assets/affaires.jpg"

    card = """        <article class="post-card">
          <a class="post-card-photo" href="{slug}/index.html">
            <img src="../{cover}" alt="{alt}" loading="lazy" />
          </a>
          <div class="post-card-body">
            <div class="post-meta">
              <time datetime="{iso}">{human}</time>
              <span class="dot">•</span>
              <span>{cat}</span>
            </div>
            <h2><a href="{slug}/index.html">{title}</a></h2>
            <p>{excerpt}</p>
            <a class="post-link" href="{slug}/index.html">
              Lire l'article
              <svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" fill="none" viewBox="0 0 24 24" stroke-width="2.5" stroke="currentColor" aria-hidden="true">
                <path stroke-linecap="round" stroke-linejoin="round" d="M13.5 4.5 21 12m0 0-7.5 7.5M21 12H3" />
              </svg>
            </a>
          </div>
        </article>

""".format(slug=slug, cover=cover_rel, alt=esc_attr(payload["cover_alt"]), iso=iso,
           human=date_fr(today), cat=payload["category"].strip(),
           title=payload["title"].strip(), excerpt=payload["excerpt"].strip())

    anchor = '      <div class="posts-grid">\n\n'
    if anchor not in html:
        fail("blog/index.html : ancre .posts-grid introuvable")
    html = html.replace(anchor, anchor + card, 1)

    # JSON-LD Blog : on ajoute l'article en tête du tableau blogPost
    m = re.search(r'(  <script type="application/ld\+json">\n)(.*?)(\n  </script>)', html, re.S)
    if m and '"@type": "Blog"' in m.group(2):
        try:
            data = json.loads(re.sub(r"^  ", "", m.group(2), flags=re.M))
            data.setdefault("blogPost", []).insert(0, {
                "@type": "BlogPosting",
                "headline": payload["title"].strip(),
                "url": "%s/blog/%s/" % (cfg["site_url"], slug),
                "datePublished": iso,
                "author": {"@type": "Organization", "name": cfg["author"]},
            })
            body = json.dumps(data, ensure_ascii=False, indent=2)
            body = "\n".join("  " + line for line in body.splitlines())
            html = html[:m.start(2)] + body + html[m.end(2):]
        except json.JSONDecodeError as exc:
            fail("blog/index.html : JSON-LD Blog illisible (%s)" % exc)
    else:
        fail("blog/index.html : bloc JSON-LD Blog introuvable")
    return html


def update_sitemap(cfg: dict, payload: dict, today: datetime) -> str:
    path = os.path.join(ROOT, "sitemap.xml")
    xml = read(path)
    iso = today.strftime("%Y-%m-%d")
    url = "%s/blog/%s/" % (cfg["site_url"], payload["slug"])
    if url in xml:
        fail("sitemap.xml : l'URL %s est déjà présente" % url)

    xml = re.sub(r"(<loc>%s/blog/</loc>\s*\n\s*<lastmod>)[^<]*(</lastmod>)"
                 % re.escape(cfg["site_url"]),
                 lambda m: m.group(1) + iso + m.group(2), xml, count=1)

    block = ("  <url>\n"
             "    <loc>%s</loc>\n"
             "    <lastmod>%s</lastmod>\n"
             "    <changefreq>monthly</changefreq>\n"
             "    <priority>0.7</priority>\n"
             "  </url>\n\n" % (url, iso))
    if "</urlset>" not in xml:
        fail("sitemap.xml : </urlset> introuvable")
    return xml.replace("</urlset>", block + "</urlset>", 1)


def update_rss(cfg: dict, payload: dict, today: datetime) -> str:
    path = os.path.join(ROOT, "rss.xml")
    xml = read(path)
    url = "%s/blog/%s/" % (cfg["site_url"], payload["slug"])
    if url in xml:
        fail("rss.xml : l'URL %s est déjà présente" % url)
    stamp = date_rfc822(today)

    xml = re.sub(r"(<lastBuildDate>)[^<]*(</lastBuildDate>)",
                 lambda m: m.group(1) + stamp + m.group(2), xml, count=1)

    item = ("    <item>\n"
            "      <title>%s</title>\n"
            "      <link>%s</link>\n"
            "      <guid isPermaLink=\"true\">%s</guid>\n"
            "      <pubDate>%s</pubDate>\n"
            "      <description>%s</description>\n"
            "    </item>\n\n" % (esc_attr(payload["title"].strip()), url, url, stamp,
                                 esc_attr(payload["excerpt"].strip())))
    if "    <item>" not in xml:
        fail("rss.xml : aucun <item> existant pour se repérer")
    idx = xml.index("    <item>")
    return xml[:idx] + item + xml[idx:]


def update_llms(cfg: dict, payload: dict) -> str | None:
    path = os.path.join(ROOT, "llms.txt")
    if not os.path.exists(path):
        return None
    txt = read(path)
    url = "%s/blog/%s/" % (cfg["site_url"], payload["slug"])
    if url in txt:
        return None
    m = re.search(r"^## Articles du blog\s*\n\n", txt, re.M)
    if not m:
        log("[WARN] llms.txt : section « Articles du blog » introuvable, fichier laissé tel quel")
        return None
    line = "- [%s](%s) — %s\n" % (payload["title"].strip(), url, payload["excerpt"].strip())
    return txt[:m.end()] + line + txt[m.end():]


# --------------------------------------------------------------------------- #
# 8. Programme principal
# --------------------------------------------------------------------------- #


def main() -> int:
    parser = argparse.ArgumentParser(description="Génère un article de blog Occitan Pro.")
    parser.add_argument("--dry-run", action="store_true",
                        help="génère et valide, mais n'écrit aucun fichier")
    parser.add_argument("--mock", action="store_true",
                        help="contenu factice hors ligne, sans appel à l'API OpenAI")
    parser.add_argument("--topic", type=int, default=None,
                        help="force le numéro de sujet à traiter")
    args = parser.parse_args()

    log("=" * 72)
    log("Génération d'article — %s" % datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    log("=" * 72)

    cfg = load_config()
    log("[INFO] site : %s (%s)" % (cfg["site_name"], cfg["site_url"]))

    topics = parse_topics(cfg)
    log("[INFO] %d sujets listés dans %s" % (len(topics), cfg["workflow_doc"]))

    done, slugs = scan_existing(cfg)
    log("[INFO] %d article(s) déjà publié(s) — sujets traités : %s"
        % (len(slugs), sorted(done) or "aucun"))

    topic = pick_topic(topics, done, slugs, args.topic)
    if topic is None:
        log("[INFO] aucun sujet nouveau à traiter. Rien à faire.")
        log("[INFO] ajoute de nouveaux sujets dans %s pour relancer la machine."
            % cfg["workflow_doc"])
        return EXIT_NOTHING_TO_DO
    log("[INFO] sujet retenu : n°%d — %s" % (topic["n"], topic["title"]))

    system, user = build_prompt(cfg, topic)

    if args.mock:
        log("[INFO] mode --mock : aucun appel à l'API OpenAI.")
        payload = mock_payload(cfg, topic)
    else:
        log("[INFO] appel OpenAI (%s, temperature %s)…"
            % (cfg.get("openai_model"), cfg.get("openai_temperature")))
        payload = call_openai(cfg, system, user)

    problems = validate(cfg, payload, slugs, lenient=args.mock)
    if problems and not args.mock:
        log("[WARN] contenu refusé : %s" % " | ".join(problems))
        log("[INFO] nouvelle tentative avec consignes correctives…")
        payload = call_openai(cfg, system, user,
                              "Ta réponse précédente a été refusée pour ces raisons :\n- "
                              + "\n- ".join(problems)
                              + "\nRegénère l'objet JSON complet en corrigeant tout cela.")
        problems = validate(cfg, payload, slugs, lenient=False)
    if problems:
        fail("contenu invalide après nouvelle tentative : %s" % " | ".join(problems))

    today = datetime.now(timezone(timedelta(hours=2)))
    slug = payload["slug"]
    out_dir = os.path.join(ROOT, "blog", slug)
    out_file = os.path.join(out_dir, "index.html")
    if os.path.exists(out_file):
        log("[INFO] /blog/%s/index.html existe déjà : rien n'est écrasé." % slug)
        return EXIT_NOTHING_TO_DO

    article_html = render_article(cfg, payload, topic, today)
    index_html = update_blog_index(cfg, payload, today)
    sitemap_xml = update_sitemap(cfg, payload, today)
    rss_xml = update_rss(cfg, payload, today)
    llms_txt = update_llms(cfg, payload)

    # Contrôle final : les données structurées produites doivent être du JSON valide.
    for block in re.findall(r'<script type="application/ld\+json">(.*?)</script>',
                            article_html, re.S):
        try:
            json.loads(block)
        except json.JSONDecodeError as exc:
            fail("JSON-LD généré invalide : %s" % exc)

    log("-" * 72)
    log("Titre    : %s" % payload["title"])
    log("Slug     : /blog/%s/" % slug)
    log("Meta     : %s (%d caractères)"
        % (payload["meta_description"], len(payload["meta_description"])))
    log("Rubrique : %s" % payload["category"])
    log("Mots     : %d (corps) + %d questions de FAQ"
        % (word_count(payload["body_html"]), len(payload["faq"])))
    log("-" * 72)

    if args.dry_run:
        log("[DRY-RUN] aucun fichier écrit. Aperçu du début de l'article :")
        preview = strip_tags(payload["lead"] + " " + payload["body_html"])
        log("")
        log(" ".join(preview.split()[:200]))
        log("")
        log("[DRY-RUN] auraient été modifiés : blog/%s/index.html, blog/index.html, "
            "sitemap.xml, rss.xml%s" % (slug, ", llms.txt" if llms_txt else ""))
        return EXIT_OK

    os.makedirs(out_dir, exist_ok=True)
    writes = [(out_file, article_html),
              (os.path.join(ROOT, "blog", "index.html"), index_html),
              (os.path.join(ROOT, "sitemap.xml"), sitemap_xml),
              (os.path.join(ROOT, "rss.xml"), rss_xml)]
    if llms_txt:
        writes.append((os.path.join(ROOT, "llms.txt"), llms_txt))
    for path, content in writes:
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(content)
        log("[OK] écrit : %s" % os.path.relpath(path, ROOT))

    log("[OK] article publié : %s/blog/%s/" % (cfg["site_url"], slug))
    return EXIT_OK


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SystemExit:
        raise
    except Exception as exc:  # filet de sécurité : jamais de trace brute en CI
        log("[ERREUR] exception inattendue : %s: %s" % (type(exc).__name__, exc))
        sys.exit(EXIT_ERROR)
