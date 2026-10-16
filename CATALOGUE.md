# Catalogue d'accès — sites RAA des départements

Objectif : un état des lieux par département de l'accès HTTP aux RAA —
structure des pages (flow), source de date faisant foi, bandes d'années à
flow différent, plus vieille année en ligne — pour dimensionner ensuite le
stockage historique et la veille journalière (101 départements à terme).

Mode de test : `run.py --max-docs 3` (3 fichiers les plus récents du mois,
fusion partielle `RAA_fusionne_partiel_...`). Un dépt à la fois, pas
d'enchaînement (WAF par IP, seuil ~30–50 req sur fenêtre glissante).

Légende statut : ✓ OK · ⚠ partiel/anomalie · ✗ non testé · en attente = à refaire

| Dépt | Site | Flow (structure des pages) | Date faisant foi | Bandes d'années (flow différent) | Plus vieux year en ligne | Test année ancienne | 2026-08 |
|---|---|---|---|---|---|---|---|
| Haute-Corse | haute-corse.gouv.fr | 3 niveaux : section $\rightarrow$ page annuelle $\rightarrow$ pages mensuelles $\rightarrow$ PDF | span CMS | 1 | 2005 | ✗ non testé | ✓ test 3/16 OK, full en attente |
| Corse-du-Sud | corse-du-sud.gouv.fr | 2 niveaux : section $\rightarrow$ page annuelle $\rightarrow$ PDF directs | span CMS | 1 | 2004 | ✗ non testé | ✓ test 3/14 OK, full en attente |
| Nord | nord.gouv.fr | 3 niveaux : section $\rightarrow$ page annuelle $\rightarrow$ pages mensuelles $\rightarrow$ PDF | span CMS | 1 | à confirmer | ✗ non testé | ✓ test 3/31 OK, full en attente |
| Pas-de-Calais | pas-de-calais.gouv.fr | 2 niveaux : section $\rightarrow$ page annuelle $\rightarrow$ PDF directs | span CMS | 1 | à confirmer | ✗ non testé | ✓ test 3/32 OK, full en attente |
| Somme | somme.gouv.fr | 2 niveaux : section $\rightarrow$ page annuelle $\rightarrow$ PDF directs | texte du lien (pas de span CMS) | 1 | à confirmer | ✗ non testé | ✓ test 3/33 OK, full en attente |
| Oise | oise.gouv.fr | 2 niveaux : section $\rightarrow$ page annuelle paginée $\rightarrow$ PDF directs | span CMS | 1 | à confirmer | ✗ non testé | ⚠ implémenté, blocage WAF au test |
| Seine-et-Marne | seine-et-marne.gouv.fr | page annuelle $\rightarrow$ select `Liste-liste-docs` $\rightarrow$ POST $\rightarrow$ panneau de téléchargement | span CMS (panneau POST) | 1 | 2017 | ✗ non testé | ✓ test 3/39 OK (sept), full en attente |
| Aisne | aisne.gouv.fr | cartes « RAA Année YYYY » (2026→2010) → cartes docs paginées par 10 (`(offset)/N`, ~17 pages) → page doc (1 lien + span) | span CMS (noms de fichier sans date) | 1 (à confirmer sur 2010-2019) | 2010 (cartes) | ✗ non testé | ✓ test 3/21 OK, full en attente |
| Allier | allier.gouv.fr | cartes « Recueil des actes administratifs de l'année YYYY » → page annuelle de liens directs (span CMS) | span CMS (100 %) | 1 | à confirmer | ✗ non testé | ✓ test 3/21 OK, full en attente |
| Isère | isere.gouv.fr | page annuelle : **select** → POST → panneau de téléchargement (span CMS) | span CMS (100 %) | 1 | à confirmer | ✗ non testé | ✓ test 3/21 OK, full en attente |
| Aube | aube.gouv.fr | cartes « RAA YYYY » (2024→2026, pas de carte archives) → cartes docs paginées par 10, **liens directs vers le PDF** (pas de page doc) | attribut `title` de la carte (CMS, pattern LA) ; texte « RAA n°207 du 31 août 2026 » en contrôle | 1 (2024 même flow, à confirmer) | 2024 (seule bande visible) | ✗ non testé | — |
| Marne | marne.gouv.fr | 2025-2026 : **1 select par mois** (pas de global ; 1er select en tête de page à double tiret) → POST de l'option (pattern Vendée) ; 2013-2024 : cartes (groupes « Années A à B ») → page annuelle tableau → pages docs | 2025+ : span CMS du panneau POST (noms sans date) ; 2013-2024 : span CMS page doc ; libellé « du … » en pré-filtre/contrôle | **2** : menu (2025-2026) / pages docs (2013-2024) | 2013 (carte groupe) | ✗ non testé | — |
| Ardennes | ardennes.gouv.fr | carte « l'année YYYY » (courante) ou « années antérieures » → cartes années (2025→2017 + commune « 2015 & 2016 ») → page annuelle de liens directs (≈ 288/an, sans pagination) | span CMS (100 %) ; nom de fichier « RAA 8-2026-144 du 31 aout 2026.pdf » en contrôle | **2** : carte directe (année en cours) / carte « années antérieures » ; **page commune 2015 & 2016** (mois ≠ année, à gérer au backfill) | 2015 & 2016 (carte commune) | ✗ non testé | ✓ test 3/19 OK, full en attente |
| Haute-Marne | haute-marne.gouv.fr | cartes « Année YYYY » (2026→2017, pas d'archives visible) → page annuelle de liens directs (sans pagination) ; 2026 : `a.fr-link` plain (URL absolue), années anciennes : `a.fr-link--download` + span | 2026 : **nom de fichier/libellé** (coquilles tolérées : année 2 chiffres « 05-02-26 », tiret final « 2026-.pdf ») ; anciennes : span CMS | **2** : 2026 sans span CMS (date dans le nom) / anciennes avec span CMS | 2017 (carte, à confirmer) | ✗ non testé | — |
| Meurthe-et-Moselle | meurthe-et-moselle.gouv.fr | cartes « Recueils des actes administratifs année YYYY » (2026→2017) → page annuelle : select « Liste-liste-docs » (110 options 2026) → POST → panneau (pattern Vendée) | span CMS du panneau POST (100 %) ; libellé « Numéro N du D mois YYYY » (ancré « du ») en pré-filtre/contrôle | 1 (2017 à confirmer) | 2017 (carte, à confirmer) | ✗ non testé | — |
| Meuse | meuse.gouv.fr | section : **select d'années** « Liste-des-recueils-liste-docs » (2026→2006, pas de cartes) → page annuelle de liens directs (sans pagination) | span CMS (100 %) ; nom de fichier « RAA n°26 du 27 février 2026.pdf » en contrôle | 1 (2006 à confirmer) | 2006 (select, à confirmer) | ✗ non testé | — |
| Bas-Rhin | bas-rhin.gouv.fr | section sous « Publications officielles » : cartes « RAA ANNEE YYYY » (majuscules sans accent, 2026→2017) → page annuelle : **1 select par mois**, tous « Liste-liste-docs » → POST → panneau (pattern Marne/Vendée) | span CMS du panneau POST (100 %) ; mois du dossier mensuel de la value (« Media/Files/22.-RAA/2026/Fevrier/... ») en pré-filtre, libellé « RAA N° X du D mois YYYY » en contrôle | 1 (2017 à confirmer) | 2017 (carte, à confirmer) | ✗ non testé | — |
| Haut-Rhin | haut-rhin.gouv.fr | cartes d'années à **texte exact « YYYY »** (2026→**1994**, archive très profonde) → page annuelle : cartes docs paginées par 10, **liens directs vers le PDF** (pattern Aube/LA) | attribut `title` de la carte (CMS, « format pdf - 1,02 Mb - 31/08/2026 ») ; texte « Recueil n°100 du 31 août 2026 » en contrôle | 1 (à confirmer sur 1994-2025) | **1994** (cartes) | ✗ non testé | — |
| Territoire de Belfort | territoire-de-belfort.gouv.fr | section : liens `a.fr-link` plain « Année YYYY » (2026→2015 + 2010, 2011-2014 absents, **coquille : 2021 → page 2022**) → page annuelle de liens directs (sans pagination) | span CMS (100 %) ; nom « recueil-90-2026-014- publié le 02-02-2026.pdf » en contrôle (ancré « publié le », pas « du ») | 1 (slugs longs 2023+ / courts 2015-2022) | 2010 (lien, à confirmer) | ✗ non testé | — |
| Haute-Saône | haute-saone.gouv.fr | page section (liste paginée par 10) $\rightarrow$ page doc (1 lien + span CMS) | span CMS (100 %) | 1 (à confirmer) | à confirmer | ✗ non testé | ✓ test 3/9 OK, full en attente |
| Jura | jura.gouv.fr | page section $\rightarrow$ page annuelle paginée $\rightarrow$ liens directs PDF | attribut `title` du lien (CMS) | 1 (à confirmer) | à confirmer | ✗ non testé | ✓ test 3/17 OK, full en attente |
| Nièvre | nievre.gouv.fr | page section $\rightarrow$ page annuelle paginée $\rightarrow$ page doc $\rightarrow$ PDF (sélecteur `a[href$='.pdf']`) | span CMS (100 %) | 1 (à confirmer) | à confirmer | ✗ non testé | ✓ test 3/28 OK, full en attente |
| Saône-et-Loire | saone-et-loire.gouv.fr | page section $\rightarrow$ page annuelle paginée $\rightarrow$ page doc $\rightarrow$ PDF | span CMS (100 %) | 1 (à confirmer) | à confirmer | ✗ non testé | ✓ test 3/28 OK, full en attente |
| Doubs | doubs.gouv.fr | page section $\rightarrow$ page annuelle paginée $\rightarrow$ page doc $\rightarrow$ PDF | span CMS (100 %) | 1 (à confirmer) | à confirmer | ✗ non testé | ✓ test 3/X OK, full en attente |
| Rhône | rhone.gouv.fr | section $\rightarrow$ page annuelle : **1 select par mois** $\rightarrow$ pages mensuelles $\rightarrow$ liens directs `a.fr-link--download` | texte du lien (date présente dans le libellé « Télécharger ... - DD/MM/YYYY ») | 1 | à confirmer | ✗ non testé | ✓ test 3/X OK |
| Savoie | savoie.gouv.fr | section $\rightarrow$ pages annuelles (peuvent être divisées, ex: « 2026 - 1 », « 2026 - 2 ») $\rightarrow$ liens directs `a[href$='.pdf']` | texte du lien (date présente dans le libellé « Télécharger ... - DD/MM/YYYY ») | 1 | à confirmer | ✗ non testé | ✓ test 3/X OK |
| Puy-de-Dôme | puy-de-dome.gouv.fr | section $\rightarrow$ page département $\rightarrow$ page annuelle $\rightarrow$ liens directs `a[href$='.pdf']` | texte du lien (date présente dans le libellé « Télécharger ... - DD/MM/YYYY ») | 1 | à confirmer | ✗ non testé | ✓ test 3/18 OK |
| Calvados | calvados.gouv.fr | 2 niveaux : section → carte « RAA départemental » (et « régional ») → cartes années texte exact « YYYY » (2026→2018) + carte « Archives » → page annuelle de liens directs (≈ 350/an, sans pagination) | span CMS (100 %) ; noms de fichier sans date (« recueil-14-2026-369-... ») | 1 (2018 à confirmer ; « Archives » au-delà) | 2018 (cartes, à confirmer) | ✗ non testé | — |
| Seine-Maritime | seine-maritime.gouv.fr | 3 niveaux : annuelle $\rightarrow$ mensuelle $\rightarrow$ PDF. Les liens mensuels sont dans des `h2` sur la page annuelle ; les PDF sont des liens `a` simples sur la page mensuelle | texte du lien (date présente dans le libellé « Télécharger ... - DD/MM/YYYY ») | 1 | 2018 (à confirmer) | ✗ non testé | ✓ test 3/27 OK, full en attente |\n| Eure | eure.gouv.fr | cartes « RAA YYYY » (2026→2015, pas d'archives visible) → page annuelle : cartes docs paginées par 10 (≈ 25 pages, « Recueil spécial N°27-2026-261 du 01 septembre 2026 ») → page doc (1 lien + span) | span CMS (100 %) ; mois de la carte (ancré « du ») en pré-filtre — typos du site (« oaût », « febvrier ») → cartes visitées au balayeur | 1 (2015 à confirmer) | 2015 (cartes, à confirmer) | ✗ non testé | ✓ test 3/29 OK, full en attente |
| Manche | manche.gouv.fr | cartes années texte exact « YYYY » (2026→2016, coquilles de slug 2021→/20212, 2020→/20202) → page annuelle : cartes mois « N. <Mois> » paginées par 10 (préfixe numérique non fiable) + cartes non-mois (« 2. Délégations de signatures ») → page de carte : liens `a.fr-link` plain (sans span en 2026), date de publication dans le texte | **la carte mois fait foi** (le mensuel du mois M est publié le M+1 — la date de publication ne fait pas foi) ; cartes non-mois : date de publication (balayeur) | 1 (2016 à confirmer) | 2016 (cartes, à confirmer) | ✗ non testé | ✓ test 3/18 OK, full en attente |
| Orne | orne.gouv.fr | section → carte « (RAA) » → années (2026→2017) dans le **menu latéral** `a.fr-sidemenu__link` (les cartes h2 de la page RAA ont un href cassé vers la page elle-même) → page annuelle : cartes mois à nom seul (Janvier…Décembre) + carte thématique « Spéciaux du mois de juillet » → page de carte : liens aux **classes corrompues par le CMS** (`a[href$='.pdf']`), span intact | span CMS (100 %, annexes comprises) ; nom « du <jour> D <mois> YYYY » en contrôle (double espaces, « du <mois> » sans jour, annexes sans date) | 1 (2017 à confirmer) | 2017 (menu, à confirmer) | ✗ non testé | ✓ test 3/26 OK, full en attente |
| Maine-et-Loire | maine-et-loire.gouv.fr | cartes « Année YYYY » → page annuelle de liens | span CMS (années récentes) ; **noms de fichier** (archives : re-upload) | **2** : 2022+ page publications / 2005-2021 carte « Archives RAA » | **2005** | ✓ 2017-08 (3/9) | ✓ full run |
| Vendée | vendee.gouv.fr | 2020+ : menu `select#Liste-liste-docs` + POST ; 1999-2019 : page archives à liens directs | 2020+ : span CMS du panneau ; 1999-2019 : libellé « publié le » (span = re-upload) | **2** : 2020+ menu/POST / 1999-2019 « Consultez-les-archives-1999-2019/YYYY/YYYY » (150 liens/an) | **1999** | ✓ 2017-08 (3/10) | ✓ full run |
| Loire-Atlantique | loire-atlantique.gouv.fr | page mensuelle `/YYYY/<slug>/`, cartes paginées par 10 | attribut `title` de la carte (CMS) | 1 (2017 même flow) | 2017 (testé) | ✓ 2017-08 (3/12) | ✓ full run |
| Mayenne | mayenne.gouv.fr | 2026 : cartes mois → pages mensuelles ; 2017 : liens directs `a.fr-link` plain (sans `--download`, sans span) | span CMS (récent) ; texte du lien ancré « du » (2017) | **2** : cartes / liens directs — frontière entre 2018 et 2026 (à affiner) | 2017 (testé) | ✓ 2017-08 (3/10) | ✓ full run |
| Sarthe | sarthe.gouv.fr | cartes « RAA - Sarthe - YYYY » → page annuelle de liens | span CMS (récent) ; noms de fichier (2018 : re-upload, mois seul) | 1 (pas de carte archives) | **2018** | ✓ 2018-08 (3/11) | ✓ full run |
| Guadeloupe | guadeloupe.gouv.fr | cartes « Mois YYYY » → pages de liens | span CMS | 1 (2017 même flow) | 2017 (testé) | ✓ 2017-08 (3/9) | ✓ full run |
| Martinique | martinique.gouv.fr | « RAA YYYY » (courante) ou « Archives » → « RAAP YYYY » → sous-cartes RAA + spéciales | span CMS | **2** : carte directe / Archives (RAAP) | à explorer sous Archives | ✓ 2017-08 (2 docs) | ✓ full run |
| Guyane | guyane.gouv.fr | cartes « Mois YYYY » → pages de liens | span CMS | 1 (2017 même flow) | 2017 (testé) | ✓ 2017-08 (3/24) | ✓ full run |
| Réunion | reunion.gouv.fr | page annuelle paginée : séparateurs mois + cartes RAA → actes individuels | span CMS | 1 (à confirmer sur 2017) | à confirmer | en attente (bloqué WAF) | ⚠ test 3/75 OK, full en attente |
| Mayotte | mayotte.gouv.fr | 3 niveaux : cartes mois → cartes docs paginées par 10 → page doc (1 lien + span) | span CMS | 1 (à confirmer sur 2017) | à confirmer | en attente (après cooldown WAF) | ⚠ test 3/20 OK, full en attente |
| Moselle | mc.moselle.gouv.fr (legacy) | recherche POST par date, `table.table_list` paginée, md5id | « Date de publication » du tableau | 1, **remonte à 2016** | **2016** (testé) | ✓ 2016-08 (3/14, n°115-118) | ✓ full run |
| Landes | landes.gouv.fr | 3 niveaux : section $\rightarrow$ page annuelle (paginée) $\rightarrow$ pages documents $\rightarrow$ PDF | texte du lien (page annuelle) | 1 | à confirmer | ✗ non testé | ✓ test 3/39 OK, full en attente |
| Gironde | gironde.gouv.fr | 3 niveaux : section $\rightarrow$ pages annuelles $\rightarrow$ pages mensuelles $\rightarrow$ PDF | span CMS / texte du lien | 1 | à confirmer | ✗ non testé | ✓ test 3/42 OK, full en attente |
| Pyrénées-Atlantiques | pyrenees-atlantiques.gouv.fr | 3 niveaux : section $\rightarrow$ pages annuelles $\rightarrow$ pages mensuelles (paginées) $\rightarrow$ PDF | span CMS / texte du lien | 1 | à confirmer | ✗ non testé | ✓ test 3/53 OK, full en attente |
| Dordogne | dordogne.gouv.fr | 3 niveaux : section $\rightarrow$ page annuelle $\rightarrow$ pages mensuelles (paginées) $\rightarrow$ PDF | span CMS / texte du lien | 1 | à confirmer | ✗ non testé | ✓ test 3/12 OK, full en attente |
| Lot-et-Garonne | lot-et-garonne.gouv.fr | 3 niveaux : section $\rightarrow$ page annuelle $\rightarrow$ pages mensuelles $\rightarrow$ PDF | texte du lien (inclut date CMS) | 1 | à confirmer | ✗ non testé | ✓ test 3/16 OK, full en attente |
| Deux-Sèvres | deux-sevres.gouv.fr | 3 niveaux : section $\rightarrow$ page annuelle $\rightarrow$ pages mensuelles $\rightarrow$ PDF | texte du lien | 1 | à confirmer | ✗ non testé | ✓ test 3/33 OK, full en attente |

## Anomalies de données découvertes (années anciennes)

- **Re-upload en masse des archives** : les spans CMS des pages d'archives
  portent la **date de re-publication** (identique pour tous les liens), pas
  la date de publication : M49 2017 → 17/04/2023 sur 101 liens ; Sarthe 2018 →
  01/09/2023 sur 104 liens ; Vendée 1999-2019 → idem. Géré par
  `_bulk_reupload_inversion` (raa_client.py) : si une même date CMS couvre la
  majorité des docs et est contredite par la source secondaire → celle-ci
  fait foi (warning dans les logs).
- **Noms de fichier en slug sans accents** (archives) : `101-raa_secial_du_29_decembre_2017.pdf`
  (très souvent la seule source de date) → `du_day_month` normalise les
  tirets bas ; variante tronquée `decembe` ajoutée à MONTHS_FR.
- **Mois sans jour** : `raa_mensuel_no_89_-decembe_2018.pdf` (Sarthe) →
  `relaxed_day_month` retourne (None, mois) ; le doc est classé en début de
  mois avec un warning « jour inconnu ».
- **Faux positif date** : « 2017-01 » (année-mois) lu comme 17/01 → guard
  `(?<!\d)` ajoutée sur `_DATE_NUM`.
- **Libellé Vendée archives** : le texte du lien inclut le span (« PDF -
  5,0 Mb - 05/08/2023 ») qui fausse le parsing du libellé → retiré avant
  parsing dans `_archive_documents`.
- **Mayenne** : documents de début 2017 nommés `20170113_RAA_spécial.pdf`
  (YYYYMMDD, sans « du ») → non datables actuellement (gap de backfill,
  pas d'impact accès).
- **Ardennes** : le préfixe du nom de fichier (`RAA 8-2026-033`, le 8 supposé
  mois) peut diverger de la date : un doc nommé « RAA 8-2026-033 du 19 janvier
  2026.pdf » porte une date CMS de **février** 2026 — les trois sources
  divergent ; le mois CMS fait foi (warning généré, exclu d'août comme il se
  doit). Le préfixe ne sert donc à rien : ni clé de mois, ni contrôle fiable.
- **Territoire de Belfort** : le span CMS (date de dépôt du fichier) peut
  diverger du nom de fichier (« publié le ») sur plusieurs docs de 2026 :
  n°009 nom 21/01 / CMS juillet, n°095 nom 08/08 / CMS 07, n°126 nom 27/08 /
  CMS 09. Règle du projet : le mois CMS fait foi (warnings dans les logs) —
  à creuser au backfill (re-postage probable).

## Résultats de campagne (2026-09-01)

### Phase Grand Est (mode test 3 fichiers)
- **Aisne 2026-08** ✓ : 3/21 docs (n°169-171, dont 1 spécial), ~31 req.
  Anomalie de slug : la carte 2018 pointe sur `RAA-Annee-20182` (coquille du
  site) et 2012 sur « RAA année 2012 » en minuscule — géré par
  `find_annual_href` (insensible à la casse, match sur le texte de la carte).
- **Ardennes 2026-08** ✓ : 3/19 docs (n°142-144), ~8 req (run bon marché :
  1 page annuelle de 288 liens). Warning de divergence CMS/nom sur
  « RAA 8-2026-033 du 19 janvier 2026 » (CMS = février) → anomalie documentée.
- *Bascule du mois de test : 2026-08 → 2026-02 à partir de l'Aube
  (mois aux problèmes plus communs).*
- **Aube 2026-02** ✓ : 3/26 docs (n°47-49), ~25 req. Coquilles CMS dans les
  noms (« RAA  n°47 » double espace, « RAAn°049 » sans espace) — sans impact
  (title CMS fait foi).
- **Marne 2026-02** ✓ : 3/20 docs (n°038-040), ~25 req (1 GET section +
  1 GET annuelle + 20 POST + 3 dl). Bug initial (0 doc) : le select « global »
  supposé n'existe pas — un select **par mois** (8 selects sur 2026, le
  premier en tête de page à double tiret) ; le client prend l'union des
  options de tous les selects, champ POST = nom du dernier select.
- **Haute-Marne 2026-02** ✓ : 3/10 docs (n°18-20), ≈5 req (1 GET section +
  1 GET annuelle + 3 dl, run bon marché). La page 2026 n'a **aucun span CMS**
  (liens `a.fr-link` plain) : la date vient du nom de fichier, coquilles
  tolérées (« RAA n° 19 du 05-02-26 » année sur 2 chiffres,
  « RAA n° 21 du 02-03-2026-.pdf » tiret final) → `du_day_month(name)` essayé
  avant `relaxed_day_month` dans la base `AnnualPageRaaClient`.
- **Meurthe-et-Moselle 2026-02** ✓ : 3/7 docs (n°15-17), ≈13 req (1 GET
  section + 1 GET annuelle + 7 POST + 3 dl). Pattern Vendée : select
  « Liste-liste-docs » (1 option par doc, libellés « Numéro N du D mois
  YYYY » ancrés « du » → pré-filtre fiable, 0 option sans date sur 2026) ;
  le POST génère le panneau (span CMS faisant foi), noms de fichier propres
  (« Numéro 15 du 18 février 2026.pdf »).
- **Meuse 2026-02** ✓ : 3/11 docs (n°24-26), ≈11 req au total (dont 4
  retentatives 404 du bug ci-dessous). La section ne porte **pas de cartes**
  mais un select d'années ; les values des options sont **relatives à la
  racine du site** (sans barre initiale) — un `urljoin` naïf avec la page
  section dupliquait le préfixe (`/Publications/Publications/...` → 404) :
  barre initiale ajoutée avant `urljoin`. Coquille de casse 2020 :
  « RAA Année 2020 » (comparaison insensible à la casse).
- **Bas-Rhin 2026-02** ✓ : 3/8 docs (n° spéc. 25/02, 26/02 + n°08 du 27/02),
  ≈13 req (1 GET section + 1 GET annuelle + 8 POST + 3 dl). Page annuelle :
  **1 select par mois** (9 selects, tous nommés « Liste-liste-docs » — sans
  la coquille double tiret de la Marne). Cartes section en majuscules sans
  accent (« RAA ANNEE 2026 ») → `find_annual_href` rendu insensible aux
  accents (unidecode des deux côtés, bug réel détecté au test).
- **Haut-Rhin 2026-02** ✓ : 3/10 docs (n°18-20), ≈15 req (1 GET section +
  10 GET de pagination annuelle + 3 dl). Cartes d'années à texte exact
  « YYYY » (jamais de préfixe « RAA ») → navigation par match exact (pas de
  partiel). La section porte un lien PDF égaré dans une carte (« Reccueil
  n°77 du 10 juillet 2026 » — coquille du site) : ignoré (texte ≠ année).
  Archive la plus profonde vue en Grand Est : **1994**.
- **Territoire de Belfort 2026-02** ✓ : 3/10 docs (n°021-023), ≈9 req
  (1 GET section + 1 GET annuelle + 3 dl). Domaine `territoire-de-belfort.gouv.fr`
  (pas `belfort.gouv.fr`, qui ne résout pas). Warnings de divergence
  CMS/nom sur d'autres mois (n°009 nom 21/01 CMS juil., n°095 nom 08/08
  CMS 07, n°126 nom 27/08 CMS 09) — le mois CMS fait foi (règle du
  projet) ; à creuser au backfill (re-postage probable). **Grand Est 10/10.**

### Phase Normandie (mode test 3 fichiers, mois 2026-02)
- **Calvados 2026-02** ✓ : 3/34 docs (spéciaux n°092-094), ≈6 req (1 sonde +
  1 GET page départementale + 1 GET annuelle + 3 dl). Navigation à 2 niveaux :
  la section porte les cartes « départemental »/« régional » ; la page
  départementale les cartes années texte exact « YYYY » (2026→2018) + carte
  « Archives ». Page annuelle : 350 liens directs sans pagination, span CMS
  100 %, noms sans date (« recueil-14-2026-369-recueil-des-actes-
  administratifs.pdf »). Un AP non-RAA (`202607_AP_abrogation_...pdf`) est
  posté sur la page annuelle : inclus seulement si sa date CMS tombe dans le
  mois cible (règle M49).
- **Eure 2026-02** ✓ : 3/29 docs (spéciaux n°062-064, 109 pages fusionnées).
  Pattern Aisne (3 niveaux) : cartes « RAA YYYY » (2026→2015) → page annuelle
  de cartes docs paginées par 10 (≈ 25 pages) → page doc (1 lien + span CMS
  faisant foi). Le mois de la carte (ancré « du ») pré-filtre avant le GET de
  la page document ; le site porte des typos de mois (« du 14 oaût 2026 »,
  « du 28 febvrier 2026 ») : cartes à mois non détectable visitées au
  balayeur, CMS faisant foi. La section porte des cartes documents parasites
  (« Recueil spécial n°27-2026-217 du 10 juillet 2026 », slug coquille
  « ...20262 ») : `find_annual_href` ne matche que « RAA YYYY » exact.
  Phase de liste coûteuse (1 GET section + ≈ 25 pages + 1 GET doc par carte du
  mois + balayeur) → cache `.raa_list/` ; relance 04/09 bon marché
  (1 sonde + 1 dl n°064 + fusion partielle, reprise des 2 PDF du 02/09).
- **Manche 2026-02** ✓ : 3/18 docs (spéciaux n°044-046, 90 pages fusionnées),
  ≈ 8 req (1 sonde + 1 GET section + 2 GET annuelle + 1 GET carte mois +
  1 GET carte « Délégations » + 3 dl) — run bon marché (pré-filtre sur les
  cartes). La page annuelle organise en **cartes mois** (« 3. Février »,
  paginées par 10 — le préfixe numérique n'est pas fiable : « 10. » manquant,
  « 11. Septembre » ; matching par le nom de mois) + cartes non-mois
  (« 2. Délégations de signatures du Préfet de la Manche ») qui portent des
  RAA **absents des cartes mois** (le n°013 du 12/01 n'existe que là).
  Page de carte : liens `a.fr-link` plain (**sans span** en 2026), date de
  publication dans le texte (« PDF - 0,11 Mb - 05/02/2026 »), noms sans jour.
  **La carte mois fait foi** (dérogation à la règle CMS) : le « RAA mensuel
  <Mois> » du mois M est publié le M+1 (mensuel de janvier → 05/02,
  mensuel de février → 05/03) — classé en début du mois de la carte avec
  warning. Cartes non-mois balayées (publication faisant foi), dédoublonnage
  par nom (n°038 présent sur les deux).
- **Orne 2026-02** ✓ : 3/26 docs (n°20, n°21 + annexe « Récapitulatif des
  candidatures », 596 pages fusionnées), ≈ 8 req (1 sonde + 2 GET navigation
  + 1 GET annuelle + 1 GET carte + 3 dl). Trois niveaux : section → carte
  « (RAA) » → années dans le **menu latéral** `a.fr-sidemenu__link` (« Le
  Recueil des Actes Administratifs 2026 » majuscules, autres minuscules) —
  les cartes h2 de la page RAA portent le même texte mais un **href cassé
  (renvoi vers la page elle-même)** : navigation par le menu latéral. Page
  annuelle : **cartes mois à nom seul** (Janvier…Décembre, sans pagination)
  + carte « Spéciaux du mois de juillet » (nom de mois dans le titre →
  traitée comme carte de juillet, dédoublonnage par nom). Pages de carte :
  ancres aux **classes corrompues par le CMS** (« <a
  fr-link--download="" id='class="fr-link'… » — le sélecteur
  `a.fr-link--download` ne matche pas → `a[href$='.pdf']`), le
  span.fr-link__detail est en revanche **intact (100 %, annexes sans date
  comprise)** et fait foi. Noms datés « du <jour de la semaine> D <mois>
  YYYY » (double espaces, « du <mois> » sans jour) en contrôle. Pas de
  mensuel : le « fusionné » = spécialités + annexes du mois. Anomalies
  numérotation (n°15 avant n°14, n°17 « du 24 » posté le 25/02) : le CMS
  fait foi.

### Phase 2026-08 (mode test 3 fichiers)
- **Réunion** ✓ : 3/75 actes (les plus récents), 16 repris, cache créé, ~17 req.
- **Mayotte** ✓ : 3/20 actes (n°159-161), layout 3 niveaux confirmé, ~27 req.

### Phase années anciennes (départ 2017-08, repli par dépt)
- **Mayenne 2017-08** ✓ : layout « liens directs » confirmé (125 liens/an,
  sans pagination) ; 3 recueils n°052-054.
- **Martinique 2017-08** ✓ : bande Archives fonctionnelle (2 recueils).
- **Moselle 2016-08** ✓ : site legacy remonte bien à 2016 (n°115-118).
- **Maine-et-Loire 2017-08** ✓ : via carte « Archives RAA » (2005-2021) ;
  inversion re-upload déclenchée (spans 17/04/2023), noms slug.
- **Sarthe 2018-08** ✓ : plus vieux year en ligne = 2018 (pas de 2017) ;
  inversion re-upload (spans 01/09/2023), mois seul dans les noms.
- **Vendée 2017-08** ✓ : flow archives découverts + implémentés (URL
  double `/2017/2017`, 150 liens, libellé « publié le »).
- **Loire-Atlantique 2017-08** ✓ : même flow mensuel qu'en 2026.
- **Guadeloupe 2017-08** ✓ : même flow cartes mois.
- **Guyane 2017-08** ✓ : même flow cartes mois.
- **Réunion 2017-08** : **bloqué WAF** au lancement (30 min d'attente
  infructueuse) → à refaire après cooldown.
- **Mayotte 2017-08** : en attente (même blocage).

### À faire après le cooldown WAF
1. `python run.py Réunion 2017 08 raa_pdfs --max-docs 3 --max-wait 1800`
2. `python run.py Mayotte 2017 08 raa_pdfs --max-docs 3 --max-wait 1800`
3. Affiner la frontière Mayenne (cartes vs liens directs) : tester 2020,
   puis 2019/2021 selon le résultat (runs bon marché : 1 GET + 3 dl).
4. Explorer la profondeur des Archives Martinique (quel est le plus vieux RAAP ?).
