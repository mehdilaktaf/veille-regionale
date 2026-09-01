# Catalogue d'accès — sites RAA des départements

Objectif : un état des lieux par département de l'accès HTTP aux RAA —
structure des pages (flow), source de date faisant foi, bandes d'années à
flow différent, plus vieille année en ligne — pour dimensionner ensuite le
stockage historique et la veille journalière (101 départements à terme).

Mode de test en cours : `run.py --max-docs 3` (3 fichiers les plus récents
du mois, fusion partielle `RAA_fusionne_partiel_...`). Un run à la fois,
pas d'enchaînement (WAF par IP, seuil ~30–50 req sur fenêtre glissante).

Légende statut : ✓ OK · ⚠ partiel/anomalie · ✗ non testé · — pas encore de run

| Dépt | Site | Flow (structure des pages) | Date faisant foi | Bandes d'années (flow différent) | Vieille année testée | 2026-08 |
|---|---|---|---|---|---|---|
| Maine-et-Loire | maine-et-loire.gouv.fr | publications → carte « Année YYYY » → page annuelle de liens `a.fr-link--download` | span `fr-link__detail` CMS (100 % des liens) | 1 seule (à confirmer) | ✗ | ✓ full run, fusion OK |
| Vendée | vendee.gouv.fr | page annuelle `…/Recueils-des-Actes-Administratifs-YYYY` : menu `select#Liste-liste-docs`, lien de téléchargement généré par POST (même URL) | span CMS du panneau de téléchargement (les libellés du menu sont fautifs) | 1 seule (à confirmer) | ✗ | ✓ full run, fusion OK |
| Loire-Atlantique | loire-atlantique.gouv.fr | page mensuelle `/YYYY/<slug-mois>/`, cartes `a.fr-card__link.menu-item-link`, paginées par 10 | attribut `title` de la carte (CMS) | 1 seule (à confirmer) | ✗ | ✓ full run, fusion OK |
| Mayenne | mayenne.gouv.fr | `…/Annee-YYYY` : cartes « Mois YYYY » → page mensuelle **ou** liens directs sur la page annuelle (années anciennes) | span CMS (partiel), sinon texte du lien ancré sur « du » | 2 bandes : cartes (récent) / liens directs (ancien) — frontière inconnue | ✗ (cible) | ✓ full run, fusion OK |
| Sarthe | sarthe.gouv.fr | publications → carte « RAA - Sarthe - YYYY » → page annuelle de liens (~186/an) | span CMS (100 %) | 1 seule (à confirmer) | ✗ | ✓ full run, fusion OK |
| Guadeloupe | guadeloupe.gouv.fr | `…/YYYY` : cartes « Mois YYYY » → pages de liens | span CMS (100 %) | 1 seule (à confirmer) | ✗ | ✓ full run, fusion OK |
| Martinique | martinique.gouv.fr | publications → carte « RAA YYYY » (année courante) **ou** carte « Archives » → « RAAP YYYY » / « R.A.A.P YYYY » (années antérieures) → page annuelle de sous-cartes (RAA + spéciales) → pages de liens | span CMS (100 %) | 2 bandes : carte directe / Archives — frontière inconnue | ✗ (cible) | ✓ full run, fusion OK |
| Guyane | guyane.gouv.fr | `…/Annee-YYYY` : cartes « Mois YYYY » → pages de liens | span CMS (100 %) | 1 seule (à confirmer) | ✗ | ✓ full run, fusion OK |
| Réunion | reunion.gouv.fr | page annuelle paginée par 10 : séparateurs de mois (sans date) + cartes RAA → page des actes individuels (pas de recueil composé) | span CMS (100 %) | 1 seule (à confirmer) | ✗ | ⚠ test 3/75 OK, full run en attente |
| Mayotte | mayotte.gouv.fr | 3 niveaux : `…/RAA-YYYY` → cartes « MOIS YYYY » (majuscules, année parfois absente) → cartes documents paginées par 10 → page document (1 lien + span CMS) | span CMS (100 %) | 1 seule (à confirmer) | ✗ | ⚠ test 3/20 OK, full run en attente |
| Moselle | mc.moselle.gouv.fr (site legacy) | recherche POST par date (`exec_search_rec`), tableau `table.table_list` paginé (« > »), téléchargement par `docfile_md5id` | « Date de publication » du tableau | 1 seule, « toutes les années » (à confirmer depuis 2016) | ✗ (cible 2016) | ✓ full run, fusion OK |

## Résultats de campagne (à compléter au fil des runs)

<!-- Après chaque run : date, commande, nb req, layout observé, anomalies -->

### Réunion 2026-08 — mode test 3 fichiers
- Commande : `python run.py Réunion 2026 08 raa_pdfs --max-docs 3 --max-wait 1800`
- Statut : ✓ OK (2026-09-01)
- Liste : 75 actes en août 2026, mise en cache (`.raa_list/reunion_2026_08.json`)
- Layout observé : page annuelle paginée par 10 (séparateurs de mois sans date +
  cartes RAA) → page d'actes individuels, span CMS 100 % — conforme 2026
- Téléchargés : 3 derniers (arrêtés délégation/désignation, 1er août), complets
- Repris : les 16 actes déjà sur disque non retéléchargés
- Anomalies : aucune ; ~17 req totales (sonde incluse), aucun blocage

### Mayotte 2026-08 — mode test 3 fichiers
- Commande : `python run.py Mayotte 2026 08 raa_pdfs --max-docs 3 --max-wait 1800`
- Statut : ✓ OK (2026-09-01)
- Liste : 20 actes en août 2026, mise en cache (`.raa_list/mayotte_2026_08.json`)
- Layout observé : 3 niveaux confirmés — cartes « AOÛT 2026 » → cartes documents
  paginées par 10 → page document (1 lien `fr-link--download` + span CMS 100 %)
- Téléchargés : recueils n°159–161 (les 3 plus récents), complets
- Anomalies : aucune ; noms de fichier sans date (`recueil-r06-2026-NNN-...`),
  mois fait foi du span CMS (conforme) ; ~27 req totales (sonde incluse), aucun blocage
