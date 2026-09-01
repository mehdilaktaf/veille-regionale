# TODO — phase d'accès limité (3 fichiers max), avant stockage historique + veille journalière

## En cours
- [ ] Mettre à jour CATALOGUE.md + ce fichier après chaque run.

## Fait
- [x] `run.py --max-docs N` : les N plus récents du mois, liste complète en cache,
      fusion partielle `RAA_fusionne_partiel_<mois>_<année>_<dépt>.pdf` (commit `44baf48`).
- [x] CATALOGUE.md créé (flows des 11 dépts, bandes d'années, statuts).
- [x] **Réunion 2026-08 — mode test** : 3/75 actes téléchargés (les plus récents),
      16 déjà repris, cache `.raa_list/reunion_2026_08.json` créé, ~17 req, pas de blocage.
- [x] **Mayotte 2026-08 — mode test** : 3/20 actes téléchargés (recueils n°159–161),
      layout 3 niveaux confirmé, cache `.raa_list/mayotte_2026_08.json` créé,
      ~27 req, pas de blocage.

## Campagne « année ancienne » (1 run/dépt, départ 2017-08, repli 2016-08)
But : valider l'accès sur chaque flow **et** cartographier les bandes d'années
à flow différent + la plus vieille année en ligne (voir CATALOGUE.md).
Cibles prioritaires :
- [ ] **Mayenne** : trouver la frontière cartes mois / liens directs (2017 probablement
      liens directs ; sinon tester 2016, puis remonter)
- [ ] **Martinique** : vérifier la bande Archives (« RAAP YYYY ») sur 2017
- [ ] **Moselle** : le site legacy remonte-t-il à 2016 (recherche POST 01/08/2016–31/08/2016) ?
- [ ] Maine-et-Loire, Vendée, Loire-Atlantique, Sarthe, Guadeloupe, Guyane,
      Réunion, Mayotte : confirmer flow unique sur 2017 (1 run de 3 fichiers chacun)
Règle : si l'année n'existe pas en ligne (404 / liste vide), remonter d'une année
et noter « plus vieille année en ligne = YYYY » dans le catalogue.

## En attente (après la phase d'accès)
- Complétion 2026-08 : Réunion (56 actes restants sur 75 → fusion complète), Mayotte (17 restants sur 20).
- Conception du mode journalier (reprise incrémentale par dépt, détection des nouveaux docs).
- Backfill historique complet (toutes les années, tous les mois) — uniquement une fois
  l'accès validé sur tous les flows.
- Extension au catalogue des 101 départements (structure CATALOGUE.md extensible).

## Rappel WAF (ne pas diminuer les délais)
- Seuil non publié : volume ~30–50 req sur fenêtre glissante, **par IP, tout `*.gouv.fr`
  préfecture** ; blocage = `RemoteDisconnected` (pas de 403), cooldown 30–60 min
  auto-entretenu si on continue à taper.
- Un dépt à la fois, pas d'enchaînement, espacement 5–15 min entre runs ;
  si blocage : attendre, puis relancer (reprise + cache de liste → relance rapide).
- La phase de liste reste le poste coûteux (ex. Réunion : ~11 req ; Mayotte : 1 req par
  acte du mois) ; `--max-docs` limite les téléchargements, pas la liste.
