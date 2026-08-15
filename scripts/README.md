# Génération automatique d'articles de blog

Un article de blog est généré et publié automatiquement **chaque lundi à 9h UTC**
(11h en France l'été, 10h l'hiver) par le workflow `.github/workflows/blog-auto.yml`.

## 1. Clé API OpenAI (à faire une seule fois)

Sur GitHub : dépôt `cazacomm/occitanpro` → **Settings** → **Secrets and variables** →
**Actions** → **New repository secret**

| Champ | Valeur |
|---|---|
| Name | `OPENAI_API_KEY` |
| Secret | la clé `sk-…` du compte OpenAI |

La clé se crée sur https://platform.openai.com/api-keys.
Sans ce secret, le workflow échoue avec un message clair et **ne publie rien**.

Vérifier aussi que les Actions ont le droit d'écrire :
**Settings** → **Actions** → **General** → *Workflow permissions* → **Read and write permissions**.

## 2. Lancer manuellement

**Depuis GitHub** : onglet **Actions** → *Blog auto* → **Run workflow**.
Deux options facultatives : `dry_run` (simulation, n'écrit rien) et `topic` (forcer un numéro de sujet).

**En local** :

```bash
pip install openai
export OPENAI_API_KEY="sk-..."

python3 scripts/generate-article.py --dry-run   # simulation, aucun fichier écrit
python3 scripts/generate-article.py             # génère et écrit vraiment
python3 scripts/generate-article.py --topic 5   # force le sujet n°5
python3 scripts/generate-article.py --mock      # hors ligne, contenu factice (test de la chaîne)
```

Codes de sortie : `0` article généré · `78` aucun sujet nouveau (normal, pas une erreur) · `1` erreur.

## 3. Ce que fait le script

1. lit `blog-config.json` ;
2. extrait les sujets de la section « sujets d'articles suggérés » de `BLOG_WORKFLOW.md` ;
3. regarde quels sujets sont déjà traités grâce au marqueur `<!-- occitanpro-topic: N -->`
   présent dans chaque article généré, et prend **le premier sujet non traité** ;
4. demande le contenu à OpenAI (`gpt-4o-mini`, temperature `0.7`) au format JSON ;
5. **valide** : longueur du corps, meta description < 155 caractères, 5 questions de FAQ,
   balises autorisées, et surtout les interdits éditoriaux de `BLOG_WORKFLOW.md`
   (prix, pourcentages, dates de fondation, références réglementaires). En cas de refus,
   une seconde tentative est faite avec les corrections ; si elle échoue aussi, le script
   s'arrête **sans rien écrire** ;
6. relit le **gabarit** depuis l'article existant indiqué par `reference_article`
   (aucun template n'est dupliqué dans le script : le HTML reste la source de vérité) ;
7. écrit `blog/<slug>/index.html`, ajoute la carte dans `blog/index.html`, met à jour
   `sitemap.xml`, `rss.xml` et `llms.txt`.

Toutes les écritures ont lieu **à la fin**, une fois tout généré et validé : un échec
laisse le dépôt strictement intact. Rejouer le workflow ne réécrit jamais un article
existant (le sujet est marqué comme traité, et un dossier déjà présent n'est jamais écrasé).

## 4. Ajouter des sujets

Quand les 12 sujets sont épuisés, le workflow sort en code `78` sans rien publier.
Il suffit d'ajouter des lignes à la liste numérotée de `BLOG_WORKFLOW.md`, au même format :

```markdown
13. **Titre du nouveau sujet** — angle attendu, en une phrase.
```

## 5. Coût estimé

Avec `gpt-4o-mini` (~0,15 $ / M tokens en entrée, ~0,60 $ / M en sortie) :

| | Tokens | Coût |
|---|---|---|
| Prompt | ~1 200 | ~0,0002 $ |
| Article généré (~1 300 mots + FAQ) | ~2 800 | ~0,0017 $ |
| **Par article** | | **~0,002 $** (moins d'un demi-centime) |
| **Par an** (52 articles) | | **~0,10 $** |

Une seconde tentative éventuelle double le coût de l'exécution concernée — l'ordre de
grandeur reste négligeable. Les minutes GitHub Actions sont gratuites sur dépôt public.
