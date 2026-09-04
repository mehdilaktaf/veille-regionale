# TODO — phase d'accès limité (3 fichiers max), avant stockage historique + veille journalière

## Fait : campagne Grand Est (10/10, Moselle déjà fait avant)
Un dépt à la fois, pipeline : découverte (2-4 GET) → client (sous-classe
existante) → clients.py + tests → `run.py <Dépt> 2026 02 raa_pdfs
--max-docs 3 --max-wait 1800` (repli 2026-03 si février vide) → CATALOGUE.md +
AGENTS.md + commit par dépt. Mois de test : **2026-02** (décision du 01/09 à
partir de l'Aube, mois aux problèmes plus communs) ; Aisne et Ardennes
déjà testés en 2026-08 avant la bascule.
- [x] Aisne (02) — 2026-08 ✓ 3/21 (cartes années → cartes docs paginées → page doc, span CMS)
- [x] Ardennes (08) — 2026-08 ✓ 3/19 (page annuelle de liens directs, span CMS 100 %)
- [x] Aube (10) — 2026-02 ✓ 3/26 (cartes « RAA YYYY » → cartes docs paginées, liens PDF directs, title CMS)
- [x] Marne (51) — 2026-02 ✓ 3/20 (flow menu 1 select/mois + POST ; flow pages docs 2013-2024)
- [x] Haute-Marne (52) — 2026-02 ✓ 3/10 (page annuelle de liens directs, 2026 sans span CMS → date du nom de fichier)
- [x] Meurthe-et-Moselle (54) — 2026-02 ✓ 3/7 (select « Liste-liste-docs » + POST, pattern Vendée, libellés « Numéro N du D mois YYYY »)
- [x] Meuse (55) — 2026-02 ✓ 3/11 (select d'années sur la section → page annuelle de liens directs, span CMS 100 %)
- [x] Bas-Rhin (67) — 2026-02 ✓ 3/8 (cartes « RAA ANNEE YYYY » sans accent → page annuelle : 1 select/mois « Liste-liste-docs » + POST, pattern Marne)
- [x] Haut-Rhin (68) — 2026-02 ✓ 3/10 (cartes années texte exact « YYYY » (2026→1994) → cartes docs paginées, liens PDF directs, title CMS)
- [x] Territoire de Belfort (90) — 2026-02 ✓ 3/10 (domaine territoire-de-belfort.gouv.fr, liens « Année YYYY » → page annuelle de liens directs, span CMS 100 %)
Règle WAF : 1 dépt à la fois, espacement, arrêt total si blocage (pas de
polling), ~4-5 dépts par session.

## En cours : campagne Normandie (2/5)
Même pipeline que le Grand Est : découverte (2-4 GET) → client (sous-classe
existante) → clients.py + tests → `run.py <Dépt> 2026 02 raa_pdfs
--max-docs 3 --max-wait 1800` (repli 2026-03 si février vide) → CATALOGUE.md +
AGENTS.md + commit par dépt.
- [x] Calvados (14) — 2026-02 ✓ 3/34 (2 niveaux : carte « départemental » → cartes années, page annuelle liens directs ≈ 350, span CMS 100 %)
- [x] Eure (27) — 2026-02 ✓ 3/29 (cartes « RAA YYYY » → cartes docs paginées → page doc span CMS ; typos de mois « oaût »/« febvrier » au balayeur)
- [ ] Manche (50)
- [ ] Orne (61)
- [ ] Seine-Maritime (76)

## Parking : années anciennes (reprendre après le Grand Est)
1. [ ] `python run.py Réunion 2017 08 raa_pdfs --max-docs 3 --max-wait 1800` (bloqué le 01/09)
2. [ ] `python run.py Mayotte 2017 08 raa_pdfs --max-docs 3 --max-wait 1800`
3. [ ] Frontière Mayenne (cartes vs liens directs) : tester 2020, puis 2019/2021
4. [ ] Profondeur des Archives Martinique (plus vieux RAAP)

## Fait
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
