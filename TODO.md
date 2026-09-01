# En attente : runs live Réunion + Mayotte (WAF par IP, cooldown long)

## Correctif du blocage — implémenté + testé (84/84 unittest)
Le blocage n'est plus géré à la main : `raa_client.py` (`RaaHttpClient`) a
- **pacing** : délai min `request_delay` (2 s) entre deux requêtes réseau (`_throttle` dans `_get`/`_post`/`download`) ;
- **retry 4 / cooldown 90 s** sur coupure (`ConnectionError`/`Timeout`) et refus/indispo (HTTP 403-429-502-503-504) — traverse un à-coup ;
- **reprise** : `download` saute un PDF déjà **complet** (`%PDF-` + `%%EOF`), re-télécharge les tronqués.
`VendeeRaaClient._post` aligné. `run.py` ajoute la **cache de liste**
(`<dest>/.raa_list/<dépt>_<année>_<mois>.json`, `--refresh` pour forcer),
`--max-wait` (sonde 1 GET/min jusqu'au déblocage, sans insister), `--probe`
(statut + en-têtes WAF/CDN + robots.txt, 1 GET).

## État des runs aout 2026
- ✓ PDL (5) + Guadeloupe + Guyane + Moselle : fusions OK
- ✓ **Martinique** : 34 docs (n°217–273), fusion 949 p (concordance), reprise des 10 déjà là
- ⚠ **Réunion** : ~16/~40 actes téléchargés (reprise), **pas encore de fusion ni de cache de liste**
- ✗ **Mayotte** : non lancée

## Nettoyage Vendée — fait
- `2026/aout/` → `2026/août/` ; `RAA_Aout_2026.pdf` →
  `RAA_fusionne_août_2026_Vendée.pdf` (re-fusion 12 docs, 633 p).

## À propos du WAF (recherche faite)
- Limite **non publiée** : c'est une règle privée du WAF de chaque site préfecture,
  pas de « N req/heure » documenté. Le seuil est un **volume sur fenêtre glissante**
  (~30–50 req), pas un simple débit → le pacing protège dans un run, pas entre runs.
- Blocage **par IP, couvre tout `*.gouv.fr` préfecture** (même plateforme CMS).
  `data.gouv.fr` (infra DINUM) n'est pas affecté. Pas de dataset RAA sur data.gouv.fr
  (pas d'API officielle de contournement).
- Symptôme `RemoteDisconnected` = drop de connexion au niveau WAF (pas de 403).
  `--probe` : pas d'en-tête WAF identifiable, pas de robots.txt → rien à référencer.
- Le cooldown est **long (30–60 min) et s'auto-entretient** si on continue à taper.

## Reprise express (quand l'IP est « froide », aucun run depuis ~1 h)
1 run complet par dépt, contre un WAF reposé (chaque dépt ~40–50 req tient dans une
fenêtre fraîche) ; `--max-wait` attend le déblocage si besoin :
```
python run.py Réunion 2026 08 raa_pdfs --max-wait 1800     # liste→cache→tous les actes→fusion
python run.py Mayotte 2026 08 raa_pdfs --max-wait 1800     # 1re exécution
```
La reprise saute les PDF complets et la liste est en cache : une relance est rapide.
Vérifier ensuite : nb de docs, pages des fusions, ordre chronologique.

## Rappel
- Un dépt à la fois, pas d'enchaînement, pas de polling dense sur un site bloqué
  (AGENTS.md, section Timing).
