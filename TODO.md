# TODO — phase d'accès limité (3 fichiers max), avant stockage historique + veille journalière

## Fait : campagnes terminées
- [x] **Grand Est (10/10)** : Aisne, Ardennes, Aube, Marne, Haute-Marne, Meurthe-et-Moselle, Meuse, Bas-Rhin, Haut-Rhin, Territoire de Belfort.
- [x] **Normandie (5/5)** : Calvados, Eure, Manche, Orne, Seine-Maritime.
- [x] **Pays de la Loire (5/5)** : Loire-Atlantique, Maine-et-Loire, Mayenne, Sarthe, Vendée.
- [x] **Outre-mer (5/5)** : Guadeloupe, Guyane, Martinique, Mayotte, Réunion.
- [x] **Auvergne-Rhône-Alpes (12/12)** : Ain, Ardèche, Cantal, Drôme, Haute-Savoie, Allier, Isère, Loire, Haute-Loire, Rhône, Savoie, Puy-de-Dôme.

## En cours : campagne Bourgogne-Franche-Comté
Pipeline (PoC Optimisé) : découverte $\rightarrow$ client ciblé (1 mois) $\rightarrow$ `run.py --max-docs 3` $\rightarrow$ CATALOGUE.md.
- [x] Côte-d'Or (21) (Terminé)
- [x] Haute-Saône (70)
- [x] Jura (39)
- [x] Nièvre (58)
- [x] Saône-et-Loire (71)
- [x] Yonne (89)
- [x] Doubs (25)

- [ ] Territoire de Belfort (90) (Déjà fait en Grand Est)

## Stratégie PoC Optimisée (Anti-WAF)
Pour minimiser l'empreinte réseau et éviter les blocages :
1. **Ciblage Année 2026 uniquement** : On valide le flux sur l'année en cours. Le backfill historique est reporté.
2. **Accès direct au mois** : Modification des clients (`MonthCardsRaaClient` et dérivés) pour ne visiter que la page du mois demandé au lieu de scanner toute l'année.
3. **Validation minimale** : Un seul mois réussi = client validé pour 2026.
4. **Arrêt précoce de la pagination** : Pour les listes chronologiques descendantes (ex. Haute-Saône), s'arrêter dès qu'un document d'un mois antérieur au mois cible est rencontré.
5. **Déport de l'extraction PDF** : Ne plus visiter la page document durant le listage. L'extraction de l'URL du PDF est déplacée dans `download()` pour éviter les GETs inutiles si le fichier est déjà présent.

## Roadmap : Campagnes restantes (Ordre Alphabétique)
Pipeline (PoC Optimisé) : découverte $\rightarrow$ client ciblé (1 mois) $\rightarrow$ `run.py --max-docs 3` $\rightarrow$ CATALOGUE.md.
- [x] Bourgogne-Franche-Comté
      - [x] Côte-d'Or, Haute-Saône, Jura, Nièvre, Saône-et-Loire, Yonne, Doubs, Territoire de Belfort
- [x] Bretagne
      - [x] Finistère, Morbihan, Côtes-d'Armor, Ille-et-Vilaine
- [x] Centre-Val de Loire
      - [x] Cher, Eure-et-Loir, Indre, Indre-et-Loire, Loiret
- [x] Corse
      - [x] Corse-du-Sud, Haute-Corse
- [x] Hauts-de-France
      - [x] Aisne (géré en Grand Est), Nord, Pas-de-Calais, Somme
- [ ] Île-de-France
      - [x] Essonne
      - [ ] Hauts-de-Seine (IGNORER pour l'instant)
      - [x] Paris
      - [x] Seine-et-Marne
      - [x] Seine-Saint-Denis
      - [x] Val-de-Marne
      - [x] Val-d'Oise (Client OK, test 3 docs OK)
      - [x] Yvelines
- [ ] Nouvelle-Aquitaine
      - [x] Gironde, Pyrénées-Atlantiques, Landes, Dordogne, Lot-et-Garonne, Creuse, Haute-Vienne, Corrèze, Charente, Deux-Sèvres
      - [ ] Charente-Maritime (Bloqué WAF - à retester)
- [ ] Occitanie
       - [x] Ariège
       - [x] Aveyron
       - [x] Lozère
       - [x] Gard
       - [x] Hérault
       - [ ] Haute-Garonne, Gers, Lot, Aude, Pyrénées-Orientales
- [ ] Provence-Alpes-Côte d'Azur
      - [ ] Alpes-Maritimes, Hautes-Alpes, Alpes-de-Haute-Provence, Var, Vaucluse

## Parking : Blocages et points d'attention
1. [ ] **Gard 2026-08** : Bloqué WAF (`RemoteDisconnected`). À reprendre plus tard.
2. [ ] **Charente-Maritime 2026-08** : Bloqué WAF (`RemoteDisconnected`). En attente de cooldown.
3. [ ] **Réunion 2017-08** : Bloqué WAF. À retenter avec `--max-wait 1800`.
4. [ ] **Mayotte 2017-08** : Bloqué WAF. À retenter avec `--max-wait 1800`.
4. [ ] **Frontière Mayenne** : Déterminer l'année de bascule entre le flow « cartes mois » et « liens directs » (tester 2020, puis 2019/2021).
5. [ ] **Archives Martinique** : Explorer la profondeur historique pour identifier le plus vieux RAAP en ligne.
6. [ ] **Mayenne début 2017** : Gérer les documents nommés `YYYYMMDD_RAA_spécial.pdf` (non datables par les regex actuelles).

## Fait
- [x] **Refactorisation structurelle** : Déplacement du code source dans `src/` et des tests dans `tests/`.
- [x] **Nettoyage des données** : Isolation des PDFs de test dans `tests/data/`.
- [x] `run.py --max-docs N` : les N plus récents du mois, liste complète en cache,
      fusion partielle `RAA_fusionne_partiel_<mois>_<année>_<dépt>.pdf` (commit `44baf48`).
- [x] CATALOGUE.md créé + campagnes documentées (flows, bandes d'années, anomalies).
- [x] Flows d'archives implémentés (commit `b4d3d7b`) : sélecteur `a.fr-link` plain,
      détection re-upload en masse (la date CMS identique sur l'ensemble est
      rejetée au profit de la source secondaire), mois sans jour (`relaxed_day_month`),
      slugs sans accents (`du_day_month` normalise `_`), guard `(?<!\d)` sur les
      dates numériques, M49 + Martinique via carte « Archives »,
      Vendée archives 1999-2019 (URL `…/Consultez-les-archives-1999-2019/YYYY/YYYY`).
- [x] **Campagne 2026-08** : Réunion 3/75 ✓ + Mayotte 3/20 ✓ (fusion partielles, caches).
- [x] **Campagne années anciennes (9/11)** :
      - Mayenne 2017-08 ✓ (liens directs, n°052-054)
      - Martinique 2017-08 ✓ (bande Archives, 2 recueils)
      - Moselle 2016-08 ✓ (legacy remonte à 2016, n°115-118)
      - Maine-et-Loire 2017-08 ✓ (via Archives RAA, re-upload 17/04/2023)
      - Sarthe 2018-08 ✓ (plus vieux year = 2018, re-upload 01/09/2023)
      - Vendée 2017-08 ✓ (flow archives 1999-2019)
      - Loire-Atlantique 2017-08 ✓ · Guadeloupe 2017-08 ✓ · Guyane 2017-08 ✓

## Plus vieilles années en ligne connues
- M49 : **2005** · Vendée : **1999** · **Haut-Rhin : 1994** (cartes) · Moselle : **2016** · Sarthe : **2018**
- GL/GY/LA/53/Martinique : 2017 OK (profondeur à explorer)
- Réunion/Mayotte : à confirmer

## En attente (après la phase d'accès)
- Complétion 2026-08 : Réunion (56 restants sur 75 → fusion complète), Mayotte (17 restants sur 20).
- Conception du mode journalier (reprise incrémentale par dépt, détection des nouveaux docs).
- Backfill historique complet (toutes les années, tous les mois) — uniquement une fois
  l'accès validé sur tous les flows. Attention aux gaps identifiés : Mayenne début 2017
  (noms YYYYMMDD non datables), mois sans jour (classés en début de mois).
- Extension au catalogue des 101 départements (structure CATALOGUE.md extensible).

## Rappel WAF (ne pas diminuer les délais)
- Seuil non publié : volume ~30–50 req sur fenêtre glissante, **par IP, tout `*.gouv.fr`
  préfecture** ; blocage = `RemoteDisconnected` (pas de 403), cooldown 30–60 min
  auto-entretenu si on continue à taper — **un polling de sonde maintient le blocage**.
- Un dépt à la fois, pas d'enchaînement ; après un blocage : arrêt total,
  attendre 30-60 min, relancer (reprise + cache de liste → relance rapide).
- La phase de liste reste le poste coûteux (Mayotte : 1 req par acte du mois ;
  Réunion : 1 req par carte RAA du mois + pagination annuelle).
