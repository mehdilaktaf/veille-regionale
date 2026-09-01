# Plan — Transport Playwright (fallback opt-in)

Statut : **spécification validée en attente d'implémentation** (décision du
01/09/2026). Rien n'est branché : tout reste en HTTP direct (`requests`).
Implémenter uniquement quand un département rencontrera un rendu JS pur
(voir §5, critères de bascule).

## Contexte / problème

Contrainte n°1 du projet : le WAF des sites préfecture bloque **par IP sur
volume de requêtes glissant (~30–50 req)** — les runs sont donc dosés
(pacing 2 s, 1 dépt à la fois, cache de liste). Un navigateur classique
consommerait ×5–10 de requêtes par page (CSS/JS/images/polices) → blocage
immédiat. Le browser n'est donc justifié que si le contenu est inatteignable
en HTTP direct, et il doit alors être **strictement dosé** (abort des
assets non fonctionnels).

Sur les 14 dépts vérifiés, aucun n'est rendu en JS pur (listes et liens de
téléchargement présents dans le HTML source ; les POST Marne/Vendée
renvoient le lien en HTML serveur).

## 1. Principe : remplacer `self.session`, rien d'autre

Aucun client n'est modifié. `RaaHttpClient.__init__` fait
`self.session = requests.Session()` et **tous** les accès réseau passent par
cet attribut (base `_get`/`_post`, le `_post` custom de Vendée, les POST
Moselle, `download()` en stream). Le transport Playwright est donc un
**objet de type session** :

```python
class PlaywrightSession:          # substitut de requests.Session
    def get(self, url, timeout=None, stream=False, **kw)   # → ResponseLike
    def post(self, url, data=None, timeout=None, **kw)     # → ResponseLike
    def close(self)
    headers = {...}               # compatibilité (non fonctionnel en browser mode)
```

ResponseLike : `.text`, `.status_code`, `.content`, `.raise_for_status()`,
`.iter_content(chunk_size)` (seulement en mode stream).

Points clés :

- **`stream=True` (téléchargement binaire des PDF) → bypass vers une session
  `requests` interne** : le PDF est une URL directe, le navigateur n'apporte
  rien et gère mal le binaire. Reprise (`_is_complete_pdf`) et contrôle
  d'entête inchangés.
- **Cartographie d'erreurs** : échec navigateur (`net::ERR_CONNECTION_RESET`,
  `ERR_EMPTY_RESPONSE` — signature du WAF) → `requests.exceptions.ConnectionError`
  ; HTTP 4xx/5xx → `requests.exceptions.HTTPError` avec `response.status_code`.
  Conséquence : la mécanique **retry 4 / cooldown 90 s / `_retry_delay`** est
  réutilisée à 0 changement, de même que la cache de liste, la reprise et
  `--max-wait` de `run.py`.
- **Pacing conservé** : `_throttle()` (2 s) est appelé par `_get`/`_post`
  *avant* `self.session.*` → le browser mode reste espacé de 2 s entre pages.

## 2. `PlaywrightSession` — comportement

| Aspect | Règle |
|---|---|
| Cycle de vie | 1 `Browser` + 1 `Context` + 1 `Page` (sync API), démarrage paresseux au 1er GET, `close()` en fin de run (1 dépt = 1 process `run.py` → 1 navigateur par run) |
| Headless | `headless=True` par défaut (new headless), flag debug `--headed` en dev |
| **Route policy** (contrôle WAF) | `"minimal"` : autorise `document` + `script` + `xhr`, **abort** image/font/media/stylesheet — sites rendus en JS (coût ~1,5–3× l'HTTP direct, jamais ×20) ; `"document"` : abort de tout sauf `document` — si le browser ne sert qu'à son fingerprint TLS/headers (coût ≈ HTTP direct) |
| Attendu de rendu | `goto(wait_until="domcontentloaded")` + `render_wait` optionnel par dépt (sélecteur à attendre, ex. un `select` ou le 1er lien), timeout 30 s |
| **POST** | `post_mode="direct"` (défaut) : POST `requests` via la session interne persistante (c'est exactement ce qui est validé pour Marne/Vendée/Moselle — réponses en HTML serveur) ; `post_mode="fetch"` : `page.evaluate(fetch(...))` same-origin dans le contexte navigateur — requis si token JS ou réponse rendue en JS |
| Cookies | `post_mode="direct"` : jar de cookies = session interne (consistant entre POSTs directs + downloads). **Contrainte connue** : un dépt avec dépendance POST→GET en session (Moselle : critères en session) doit prendre `post_mode="fetch"` (tout dans le contexte browser), sinon rester en HTTP |
| Compteur WAF | `page.on("request")` → total de requêtes réelles, log en fin de run (`Budget requêtes : N (browser)`) — suivi du seuil glissant |

## 3. Branchement (3 fichiers, zéro client modifié)

- `clients.py` : config par dépt + choix du transport, source de vérité
  GUI/CLI :

  ```python
  DEPARTMENT_TRANSPORT = {  # défaut "http" ; seul un dépt justifié passe en browser
      # "Marne": {"transport": "browser", "route_policy": "minimal", "post_mode": "direct"},
  }

  def build_client(department, year, transport=None):
      client = <instanciation actuelle>
      cfg = transport or DEPARTMENT_TRANSPORT.get(department, {}).get("transport", "http")
      if cfg == "browser":
          client.session = PlaywrightSession(**DEPARTMENT_TRANSPORT[department])
      return client
  ```

  Le swap post-construction est volontairement localisé dans `build_client`
  (pas de changement de signature sur les 14 constructeurs).
- `run.py` : flag `--transport {http,browser}` (prioritaire sur la config)
  pour expérimenter sans éditer `clients.py`.
- `requirements-browser.txt` (optionnel, séparé) : `playwright==<version
  pinnée>` + note `playwright install chromium` dans AGENTS.md. Le
  `requirements.txt` principal reste léger : un run HTTP n'installe rien de
  plus.
- `app.py` (GUI) : rien à changer (passe par `build_client` ; browser headless
  dans le même process).

## 4. Garanties zéro impact

- Les **143 tests unitaires passent sans modification** (fake au niveau
  `_get`/`_post`, sous la session).
- Aucun dépt ne change de comportement tant que `DEPARTMENT_TRANSPORT` est
  vide (tout reste `http`).
- Smoke test de régression : après toute mise à jour Playwright/Chromium,
  1 run bon marché (Ardennes : ~2 req) en browser mode vs HTTP.

## 5. Critères de bascule d'un dépt en browser (règle à documenter AGENTS.md)

Bascule **uniquement** si :

1. la liste des documents est absente du HTML source (montage JS, données en
   XHR) — HTTP direct structurellement bloqué ; **ou**
2. le lien de téléchargement exige un token généré en JS (POST direct
   inopérant) ; **ou**
3. le WAF fingerprinte les clients non-navigateurs (blocage systématique en
   HTTP simple qui passe en browser).

Sinon : rester en HTTP (meilleur budget WAF). C'est la règle par défaut, pas
l'exception.

## 6. Tests du transport

`test_browser_transport.py` avec un `PageLike` factice (protocol :
`goto(url)` → `(status, html)`, `evaluate` → dictionnaire) :

- `get` → `.text` correct, `raise_for_status` sur 503 ;
- erreur `net::ERR_*` → `ConnectionError` → `_retry_delay` = 90 s (réutilise
  le test existant de cooldown) ;
- `post_mode` direct vs fetch ;
- `stream=True` → session interne (aucun appel navigateur) ;
- route policy : les `route` attendus sont enregistrés ;
- compteur de requêtes.

## 7. Risques / mitigations

| Risque | Mitigation |
|---|---|
| Consommation WAF en browser (scripts chargés) | route policy `minimal` obligatoire ; compteur de requêtes loggé ; `--max-docs 3` pour toute validation live |
| Dérive de version Playwright/Chromium | version pinnée + smoke test Ardennes après upgrade |
| Cookies partagés POST→GET (cas Moselle) | `post_mode="fetch"` ou rester HTTP ; documenté |
| Poids de la dépendance (~300 Mo Chromium) | requirements séparé optionnel ; install une fois |

## 8. Plan d'implémentation (quand on le décide — 4 étapes)

1. `browser_transport.py` + `test_browser_transport.py` (aucun site live) →
   suite complète verte.
2. `clients.py` (config vide) + `run.py --transport` → comportement identique
   par défaut, testé.
3. Validation live instrumentée sur 1 dépt HTTP-friendly (compte des
   requêtes browser vs HTTP, même page) pour mesurer le surcoût WAF réel.
4. Bascule du 1er dépt réellement rendu en JS (lorsqu'il arrivera dans les
   87 restants) + entrée CATALOGUE.md.

## 9. Fichiers touchés (à l'implémentation)

- `browser_transport.py` (nouveau) : `PlaywrightSession`, route policies,
  mapping d'erreurs, compteur.
- `clients.py` : `DEPARTMENT_TRANSPORT` + param `transport` de `build_client`.
- `run.py` : flag `--transport`.
- `requirements-browser.txt` (nouveau, optionnel).
- `AGENTS.md` : critères de bascule, note install, quirks.
- `test_browser_transport.py` (nouveau).

## 10. Points ouverts (tranchés à l'implémentation)

- Le flag `--transport` est-il nécessaire maintenant, ou la config
  `clients.py` suffit-elle ?
- Pinner Playwright dès maintenant dans `requirements-browser.txt` ou
  attendre l'étape 1 ?
- Ajouter le compteur de requêtes en mode HTTP aussi (hook `session.get/post`,
  ~10 lignes) — utile pour le budget WAF quel que soit le transport ?
