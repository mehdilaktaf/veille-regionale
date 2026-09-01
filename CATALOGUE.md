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
| Aisne | aisne.gouv.fr | cartes « RAA Année YYYY » (2026→2010) → cartes docs paginées par 10 (`(offset)/N`, ~17 pages) → page doc (1 lien + span) | span CMS (noms de fichier sans date) | 1 (à confirmer sur 2010-2019) | 2010 (cartes) | ✗ non testé | ✓ test 3/21 OK, full en attente |
| Aube | aube.gouv.fr | cartes « RAA YYYY » (2024→2026, pas de carte archives) → cartes docs paginées par 10, **liens directs vers le PDF** (pas de page doc) | attribut `title` de la carte (CMS, pattern LA) ; texte « RAA n°207 du 31 août 2026 » en contrôle | 1 (2024 même flow, à confirmer) | 2024 (seule bande visible) | ✗ non testé | — |
| Marne | marne.gouv.fr | 2025-2026 : **1 select par mois** (pas de global ; 1er select en tête de page à double tiret) → POST de l'option (pattern Vendée) ; 2013-2024 : cartes (groupes « Années A à B ») → page annuelle tableau → pages docs | 2025+ : span CMS du panneau POST (noms sans date) ; 2013-2024 : span CMS page doc ; libellé « du … » en pré-filtre/contrôle | **2** : menu (2025-2026) / pages docs (2013-2024) | 2013 (carte groupe) | ✗ non testé | — |
| Ardennes | ardennes.gouv.fr | carte « l'année YYYY » (courante) ou « années antérieures » → cartes années (2025→2017 + commune « 2015 & 2016 ») → page annuelle de liens directs (≈ 288/an, sans pagination) | span CMS (100 %) ; nom de fichier « RAA 8-2026-144 du 31 aout 2026.pdf » en contrôle | **2** : carte directe (année en cours) / carte « années antérieures » ; **page commune 2015 & 2016** (mois ≠ année, à gérer au backfill) | 2015 & 2016 (carte commune) | ✗ non testé | ✓ test 3/19 OK, full en attente |
| Haute-Marne | haute-marne.gouv.fr | cartes « Année YYYY » (2026→2017, pas d'archives visible) → page annuelle de liens directs (sans pagination) ; 2026 : `a.fr-link` plain (URL absolue), années anciennes : `a.fr-link--download` + span | 2026 : **nom de fichier/libellé** (coquilles tolérées : année 2 chiffres « 05-02-26 », tiret final « 2026-.pdf ») ; anciennes : span CMS | **2** : 2026 sans span CMS (date dans le nom) / anciennes avec span CMS | 2017 (carte, à confirmer) | ✗ non testé | — |
| Meurthe-et-Moselle | meurthe-et-moselle.gouv.fr | cartes « Recueils des actes administratifs année YYYY » (2026→2017) → page annuelle : select « Liste-liste-docs » (110 options 2026) → POST → panneau (pattern Vendée) | span CMS du panneau POST (100 %) ; libellé « Numéro N du D mois YYYY » (ancré « du ») en pré-filtre/contrôle | 1 (2017 à confirmer) | 2017 (carte, à confirmer) | ✗ non testé | — |
| Meuse | meuse.gouv.fr | section : **select d'années** « Liste-des-recueils-liste-docs » (2026→2006, pas de cartes) → page annuelle de liens directs (sans pagination) | span CMS (100 %) ; nom de fichier « RAA n°26 du 27 février 2026.pdf » en contrôle | 1 (2006 à confirmer) | 2006 (select, à confirmer) | ✗ non testé | — |
| Bas-Rhin | bas-rhin.gouv.fr | section sous « Publications officielles » : cartes « RAA ANNEE YYYY » (majuscules sans accent, 2026→2017) → page annuelle : **1 select par mois**, tous « Liste-liste-docs » → POST → panneau (pattern Marne/Vendée) | span CMS du panneau POST (100 %) ; mois du dossier mensuel de la value (« Media/Files/22.-RAA/2026/Fevrier/... ») en pré-filtre, libellé « RAA N° X du D mois YYYY » en contrôle | 1 (2017 à confirmer) | 2017 (carte, à confirmer) | ✗ non testé | — |
| Haut-Rhin | haut-rhin.gouv.fr | cartes d'années à **texte exact « YYYY »** (2026→**1994**, archive très profonde) → page annuelle : cartes docs paginées par 10, **liens directs vers le PDF** (pattern Aube/LA) | attribut `title` de la carte (CMS, « format pdf - 1,02 Mb - 31/08/2026 ») ; texte « Recueil n°100 du 31 août 2026 » en contrôle | 1 (à confirmer sur 1994-2025) | **1994** (cartes) | ✗ non testé | — |
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
