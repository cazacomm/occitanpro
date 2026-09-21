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
- Salon : samedi 19 septembre 2026, 10h-18h, au 35e RAP (quartier Soult, place de la Courte Boule, 65000 Tarbes), entrée gratuite.
- Contact : 06 76 67 37 72 — occitanpro@gmail.com

### ⚠️ Incohérences à trancher avec le client (non corrigées à ce jour)

Deux informations diffèrent d'une page à l'autre du site. **Ne pas les corriger sans validation du
client** : en attendant l'arbitrage, utiliser dans les articles la formulation prudente indiquée
en 3ᵉ colonne.

| Information | Ce que disent les pages | Formulation à utiliser en attendant |
|---|---|---|
| Fréquence des réunions | `index.html` : « une fois par mois, le jeudi » — `principe.html` : « le dernier jeudi de chaque mois » | « une fois par mois, le jeudi » |
| Nombre de membres | `entreprises.html` et le JSON-LD de `index.html` : 20 — `principe.html` : « ~25 membres actifs » | « une vingtaine d'entrepreneurs » |

Une fois l'arbitrage rendu, harmoniser les pages concernées **et** les contenus du blog déjà publiés
(`/blog/<slug>/index.html`, section FAQ visible **et** JSON-LD `FAQPage`, qui doivent rester identiques
mot pour mot), ainsi que `llms.txt`.

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

## 6. Sujets d'articles suggérés

Tous ancrés local (Hautes-Pyrénées / Tarbes / Bigorre) et rédigeables **sans inventer aucun chiffre**.
La liste se recharge toute seule : voir `scripts/README.md`, § « Réserve de sujets ».

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
13. **Les avantages de rejoindre un réseau d'affaires à Orleix** — Découvrir les bénéfices concrets pour les entrepreneurs locaux.
14. **Comment organiser un événement professionnel à Tarbes** — Conseils pratiques pour réussir l'organisation d'événements d'affaires.
15. **Les erreurs courantes des entrepreneurs débutants en Bigorre** — Identifier et éviter les pièges fréquents pour les nouveaux entrepreneurs.
16. **Le rôle des clubs d'entrepreneurs dans la vallée de l'Adour** — Comprendre l'impact des clubs sur le développement des affaires locales.
17. **Comment optimiser son réseau professionnel dans les Hautes-Pyrénées** — Stratégies pour étendre efficacement son réseau local.
18. **Les atouts d'une TPE artisanale dans le 65** — Analyser les forces spécifiques des petites entreprises artisanales locales.
19. **Développer une stratégie de recommandation en Occitanie** — Méthodes pour créer un système de recommandations efficace.
20. **Les métiers d'artisanat florissants dans les Hautes-Pyrénées** — Explorer les métiers artisanaux en plein essor dans la région.
21. **Comment choisir un partenaire d'affaires local à Tarbes** — Critères pour sélectionner des partenaires commerciaux solides.
22. **Valoriser son savoir-faire artisanal dans le réseau local** — Techniques pour mettre en avant ses compétences artisanales.
23. **Pourquoi intégrer un club d'entrepreneurs dans le 65000** — Découvrir les raisons et avantages d'adhérer à un club local.
24. **Créer des synergies professionnelles en vallée de l'Adour** — Identifier des opportunités de collaboration entre entrepreneurs.
25. **L'impact du bouche-à-oreille pour les TPE de Tarbes** — Analyse de l'importance du bouche-à-oreille pour les petites entreprises.
26. **Organiser un atelier collaboratif dans les Hautes-Pyrénées** — Étapes pour mettre en place un atelier efficace et participatif.
27. **Les spécificités du marché local pour les artisans du 65** — Comprendre les particularités du marché des artisans locaux.
28. **Le guide pour réseauter efficacement à Orleix** — Conseils pour optimiser ses rencontres professionnelles.
29. **Comment développer sa visibilité en Bigorre** — Stratégies pour accroître la notoriété de son entreprise localement.
30. **Les avantages des réunions de réseau dans les Hautes-Pyrénées** — Découvrir les bénéfices des rencontres régulières entre entrepreneurs.
31. **La dynamique des clubs d'entrepreneurs en Occitanie** — Analyse de l'évolution des clubs et leur influence sur le tissu économique.
32. **Comment fidéliser sa clientèle dans le 65** — Techniques pour maintenir et renforcer la relation avec ses clients.
33. **Les secteurs d'activité porteurs en vallée de l'Adour** — Explorer les domaines économiques en croissance dans la région.
34. **Les bonnes pratiques pour un pitch efficace à Tarbes** — Techniques pour réussir sa présentation en milieu professionnel.
35. **Créer un réseau d'entraide entre artisans de Bigorre** — Mettre en place un système de soutien mutuel entre professionnels.
36. **Les clés pour réussir une collaboration inter-entreprises à Orleix** — Éléments essentiels pour une coopération fructueuse entre entreprises.
37. **Comment utiliser le digital pour développer son réseau à Tarbes** — Astuces pour tirer parti des outils numériques dans le réseautage.
38. **Les initiatives locales qui boostent l'entrepreneuriat en Hautes-Pyrénées** — Découverte des programmes et soutiens locaux pour entrepreneurs.
39. **Développer une stratégie de communication locale en Occitanie** — Élaborer un plan de communication adapté au territoire.
40. **Les avantages de l'économie circulaire pour les TPE de Bigorre** — Comprendre les bénéfices de l'économie circulaire pour les petites entreprises locales.
41. **Comment gérer sa croissance en tant qu'artisan dans le 65** — Stratégies pour un développement maîtrisé de son activité artisanale.
42. **Les tendances entrepreneuriales à surveiller en vallée de l'Adour** — Identifier les courants émergents dans le monde des affaires local.
43. **Comment valoriser son entreprise lors d'un événement à Tarbes** — Techniques pour maximiser la visibilité de sa marque lors d'événements.
44. **Les ressources locales pour les entrepreneurs débutants en Hautes-Pyrénées** — Découverte des aides et accompagnements disponibles pour les novices.
45. **Les étapes pour réussir une transition numérique à Orleix** — Guide pour intégrer efficacement le numérique dans son entreprise.
46. **Comment adapter son offre aux besoins locaux en Bigorre** — Stratégies pour ajuster ses produits ou services aux attentes régionales.
47. **La gestion du temps pour les entrepreneurs de Tarbes** — Techniques pour optimiser son emploi du temps et gagner en efficacité.
48. **Comment renforcer la solidarité entre entrepreneurs en 65000** — Initiatives pour favoriser l'entraide au sein du réseau local.
49. **Les bénéfices de la formation continue pour les artisans du 65** — Importance de l'apprentissage permanent pour maintenir sa compétitivité.
50. **Comment structurer son business plan pour le marché local** — Éléments clés pour adapter son plan d'affaires au contexte régional.
51. **Les opportunités d'expansion pour les TPE dans les Hautes-Pyrénées** — Exploration des possibilités de croissance pour les petites entreprises locales.
52. **Les défis de la reconversion professionnelle à Tarbes** — Astuces pour réussir sa transition vers un nouveau métier dans la région.

---

## 7. Après publication

- Vérifier l'URL en ligne (délai GitHub Pages : 1 à 2 min).
- Tester les données structurées : https://search.google.com/test/rich-results
- Soumettre le sitemap dans la Google Search Console si ce n'est pas déjà fait.
- Partager le lien sur les canaux du club.
