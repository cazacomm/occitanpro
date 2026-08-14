# Workflow blog — Occitan Pro

Procédure pour publier un nouvel article sur https://occitanpro.com/blog/.
Le site est statique (HTML/CSS, GitHub Pages) : aucun CMS, tout se fait par fichiers.

---

## 1. Structure des fichiers

```
/blog/
  index.html                     ← liste des articles
  <slug-de-l-article>/
    index.html                   ← l'article
/assets/
  blog.css                       ← styles du blog (base du site + composants blog)
/sitemap.xml                     ← à mettre à jour à chaque publication
/rss.xml                         ← à mettre à jour à chaque publication
/robots.txt                      ← ne change pas
/llms.txt                        ← à mettre à jour à chaque publication
```

URL finale d'un article : `https://occitanpro.com/blog/<slug>/`
(GitHub Pages sert automatiquement le `index.html` du dossier.)

---

## 2. Publier un nouvel article — checklist

1. **Créer le dossier** `/blog/<slug>/` et y copier le fichier `index.html` d'un article existant comme gabarit.
   Le slug : minuscules, tirets, sans accents, 3 à 6 mots, contenant le mot-clé principal + l'ancrage local
   (ex. `devis-travaux-tarbes-que-verifier`).

2. **Mettre à jour le `<head>`** :
   - `<title>` : 55-60 caractères, mot-clé + `– Occitan Pro`
   - `<meta name="description">` : **moins de 155 caractères**, une phrase, avec l'ancrage local
   - `og:url`, `og:title`, `og:description`, `og:image`, `article:published_time`
   - `twitter:title`, `twitter:description`, `twitter:image`
   - `<link rel="canonical">` → `https://occitanpro.com/blog/<slug>/` (**toujours en non-www**, voir §5)

3. **Mettre à jour les 3 blocs JSON-LD** de l'article :
   - `Article` : `headline`, `description`, `image`, `datePublished`, `dateModified`, `mainEntityOfPage`
   - `BreadcrumbList` : le 3ᵉ élément (nom + URL de l'article)
   - `FAQPage` : les 5 questions/réponses, **identiques mot pour mot** au HTML visible de la section FAQ

4. **Écrire le contenu** (voir §3 pour les règles rédactionnelles).

5. **Ajouter la carte** dans `/blog/index.html` (bloc `<article class="post-card">`, le plus récent en premier)
   et l'ajouter au tableau `blogPost` du JSON-LD `Blog` en haut du fichier.

6. **Mettre à jour** :
   - `sitemap.xml` : ajouter un bloc `<url>` pour l'article + passer le `<lastmod>` de `/blog/` à la date du jour
   - `rss.xml` : ajouter un `<item>` en haut de la liste + mettre à jour `<lastBuildDate>`
   - `llms.txt` : ajouter une ligne dans la section « Articles du blog »

7. **Vérifier** :
   - liens relatifs corrects depuis `/blog/<slug>/` : `../../index.html`, `../../assets/…`, `../../favicon/…`, `../index.html`
   - l'image de couverture existe bien dans `/assets/`
   - la page s'affiche correctement en mobile (menu burger fonctionnel)

8. **Commit + push** sur `main`. GitHub Pages déploie automatiquement (1 à 2 minutes).

---

## 3. Règles rédactionnelles

**Format**
- 1200 à 1500 mots hors FAQ.
- Un seul `<h1>` (le titre de l'article), puis des `<h2>` et `<h3>` structurés.
- Un chapô (`.article-lead`) de 3 à 5 lignes qui répond immédiatement à la question posée par le titre.
- Une section FAQ de **5 questions**, en fin d'article, dupliquée en JSON-LD `FAQPage`.
- Au moins 2 liens internes (vers `principe.html`, `entreprises.html`, `contact.html`, `salon.html` ou un autre article).
- Un CTA de fin (`.article-cta`) avec téléphone + lien contact.

**Ancrage local (SEO/GEO)**
- Citer explicitement les Hautes-Pyrénées / le 65 / la Bigorre / Tarbes et environs.
- Parler des réalités locales : TPE, artisans, prestataires, saisonnalité, distances courtes.

**Interdits absolus**
- ❌ Inventer des **prix**, montants de cotisation, tarifs ou fourchettes.
- ❌ Inventer des **chiffres précis** (statistiques, pourcentages, nombre de recommandations, CA généré).
- ❌ Inventer des **noms de clients**, témoignages ou citations.
- ❌ Inventer des **réglementations**, obligations légales ou références de textes.
- ❌ Inventer une **date de fondation** du club ou des dates d'événements non confirmées.

En cas de doute sur un chiffre : le reformuler qualitativement (« une vingtaine de membres », « plusieurs secteurs »)
plutôt que de l'inventer.

**Sources internes fiables** (déjà publiées sur le site, réutilisables)
- Une vingtaine de membres actifs, plusieurs secteurs d'activité.
- Réunion une fois par mois, le jeudi, lieu tournant.
- Déroulé : accueil → présentation d'un membre → échanges → convivialité.
- Valeurs : convivialité, confiance, croissance.
- En principe un membre par secteur, avec souplesse.
- Salon : samedi 19 septembre 2026, 10h-18h, Château d'Orleix, entrée gratuite.
- Contact : 06 76 67 37 72 — occitanpro@gmail.com

---

## 4. NAP (à garder identique partout)

| Champ | Valeur |
|---|---|
| Nom | Occitan Pro |
| Téléphone | 06 76 67 37 72 / `tel:0676673772` / `+33676673772` |
| Email | occitanpro@gmail.com |
| Zone | Hautes-Pyrénées (65), Occitanie, France |
| Site | https://occitanpro.com |

L'adresse postale du siège n'est pas publiée : **ne pas en inventer une**, y compris dans les JSON-LD.

---

## 5. www vs non-www

Le fichier `CNAME` contient `occitanpro.com` : la forme canonique du site est **non-www**.
Tous les `<link rel="canonical">`, `og:url`, URLs du `sitemap.xml`, du `rss.xml` et du `llms.txt`
doivent utiliser `https://occitanpro.com/…` sans `www.`.

---

## 6. 12 sujets d'articles suggérés

Tous ancrés local (Hautes-Pyrénées / Tarbes / Bigorre) et rédigeables **sans inventer aucun chiffre**.

1. **Comment choisir un artisan de confiance dans les Hautes-Pyrénées** — les signaux qui rassurent, les questions à poser, pourquoi la recommandation reste le meilleur filtre.
2. **Rejoindre un club d'entrepreneurs à Tarbes : à quoi s'attendre les 6 premiers mois** — le rythme réel, ce qui se passe avant les premiers résultats.
3. **Travaux de rénovation en Bigorre : dans quel ordre faire intervenir les corps de métier** — coordination entre électricien, plombier, plaquiste, peintre.
4. **Être indépendant dans le 65 : comment sortir de l'isolement professionnel** — entraide, relecture de devis, dépannage entre confrères.
5. **Préparer un salon professionnel local quand on est une TPE** — objectifs réalistes, stand, suivi des contacts (à publier avant le Salon du 19 septembre 2026).
6. **Recommander sans se griller : le guide de la mise en relation entre pros** — quand recommander, comment le formuler, quoi faire si ça se passe mal.
7. **Se présenter en 2 minutes : l'exercice qui change tout en réunion de réseau** — parler besoin client plutôt qu'intitulé de métier.
8. **Entretenir sa maison dans les Hautes-Pyrénées : le calendrier saison par saison** — quel professionnel appeler à quel moment de l'année.
9. **Pourquoi les entreprises locales se recommandent entre elles plutôt que de se concurrencer** — complémentarité, un membre par secteur, cibles différentes.
10. **Le premier rendez-vous client : ce que les artisans du club font systématiquement** — écoute, cadrage du besoin, transparence sur ce qu'on ne fait pas.
11. **Développer son activité sans budget publicitaire : les canaux qui marchent en zone rurale** — réseau, visibilité locale, avis, présence terrain.
12. **Portrait de membre : le format « entrepreneur du mois »** — gabarit récurrent pour mettre en avant un membre du club (à valider avec la personne concernée avant publication).

---

## 7. Après publication

- Vérifier l'URL en ligne (délai GitHub Pages : 1 à 2 min).
- Tester les données structurées : https://search.google.com/test/rich-results
- Soumettre le sitemap dans la Google Search Console si ce n'est pas déjà fait.
- Partager le lien sur les canaux du club.
