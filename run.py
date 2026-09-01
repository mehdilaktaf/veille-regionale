"""CLI headless de récupération + fusion des RAA d'un département/mois.

Usage :
    python run.py <département> <année> <mois> <dossier_destination> [--delay S]

Le <mois> accepte un code « MM » (08) ou un nom (« Août », « aout »).
Le <département> est insensible à la casse/aux accents (« reunion »,
« Réunion »).

Reprise : les PDF déjà complets sur disque ne sont pas retéléchargés
(voir RaaHttpClient.download) ; la fusion n'est écrite qu'après le
téléchargement complet du mois.

Mode test : --max-docs N ne récupère que les N documents les plus
récents du mois (la liste complète reste mise en cache) et écrit une
fusion partielle nommée « RAA_fusionne_partiel_... ».
"""

import argparse
import json
import logging
import os
import time
from urllib.parse import urljoin

import requests
from PyPDF2 import PdfMerger
from unidecode import unidecode

from clients import DEPARTMENT_URLS, build_client
from raa_client import MONTH_NAMES_FR, RaaError

# En-têtes révélateurs du WAF/CDN qui protège le site.
_WAF_HEADERS = (
    "server", "cf-ray", "cf-cache-status", "x-cache", "x-served-by",
    "via", "x-azure-ref", "x-powered-by", "x-akamai-transaction-id",
    "x-amz-cf-id", "report-to",
)

# Nom de mois (libellé) -> code « MM ».
MONTHS_BY_NAME = {
    "janvier": "01", "février": "02", "fevrier": "02", "mars": "03",
    "avril": "04", "mai": "05", "juin": "06", "juillet": "07",
    "août": "08", "aout": "08", "septembre": "09", "octobre": "10",
    "novembre": "11", "décembre": "12", "decembre": "12",
}


def resolve_month(month_arg):
    """Retourne le code « MM » du mois (accepte « 08 », « Août », « aout »)."""
    m = month_arg.strip()
    if m.isdigit() and len(m) == 2 and 1 <= int(m) <= 12:
        return m
    code = MONTHS_BY_NAME.get(m.lower())
    if code is None:
        raise SystemExit(f"Mois inconnu : {month_arg!r}")
    return code


def resolve_department(name):
    """Retourne le nom exact du département (insensible à la casse/accents)."""
    if name in DEPARTMENT_URLS:
        return name
    target = unidecode(name).lower()
    for dept in DEPARTMENT_URLS:
        if unidecode(dept).lower() == target:
            return dept
    raise SystemExit(
        f"Département inconnu : {name!r} "
        f"(choix : {', '.join(sorted(DEPARTMENT_URLS))})"
    )


def wait_until_reachable(client, max_wait, interval=60):
    """Attend que le site devienne joignable (blocage WAF) sans insister :
    1 GET « sonde » toutes les ``interval`` secondes, jusqu'à ``max_wait``.
    Retourne True si le site répond, False si le délai d'attente est dépassé."""
    if max_wait <= 0:
        return True
    deadline = time.monotonic() + max_wait
    print(
        f"Site bloqué ? Attente du déblocage "
        f"(1 sonde GET / {interval:g} s, max {max_wait:g} s)…"
    )
    while True:
        try:
            client.session.get(client.base_url, timeout=20)
            print("Site joignable : lancement du run.")
            return True
        except requests.RequestException as exc:
            if time.monotonic() + interval > deadline:
                print(
                    f"Site encore bloqué après {max_wait:g} s ({type(exc).__name__})."
                )
                return False
            print(f"Bloqué ({type(exc).__name__}) — nouvelle sonde dans {interval:g} s.")
            time.sleep(interval)


def probe(department, year="2026"):
    """Diagnostique la protection d'un site sans tester agressivement :
    1 GET sur la page de base (statut + en-têtes WAF/CDN) puis robots.txt
    (éventuel Crawl-delay). Sert à identifier le WAF et sa politesse, pas à
    contourner le blocage."""
    client = build_client(department, year)
    url = client.base_url
    print(f"== Sonde {department} : {url}")
    try:
        r = client.session.get(url, timeout=20)
    except requests.RequestException as exc:
        print(f"BLOQUE : {type(exc).__name__} : {exc}")
        print("(Le site coupe la connexion sans réponse : blocage WAF par IP.)")
        return
    print(f"HTTP {r.status_code}  ({len(r.content)} o)")
    for header in _WAF_HEADERS:
        value = r.headers.get(header)
        if value:
            print(f"  {header}: {value}")
    robots = client.session
    try:
        rr = robots.get(urljoin(url, "/robots.txt"), timeout=20)
        if rr.status_code == 200:
            crawl = [
                line.strip()
                for line in rr.text.splitlines()
                if line.lower().startswith("crawl-delay")
            ]
            suffix = f"  -> {crawl[0]}" if crawl else "  (pas de Crawl-delay)"
            print(f"robots.txt : HTTP 200{suffix}")
        else:
            print(f"robots.txt : HTTP {rr.status_code}")
    except requests.RequestException as exc:
        print(f"robots.txt : {type(exc).__name__}")


def cache_path(dest_folder, department, year, month):
    """Chemin du cache de liste : <dest>/.raa_list/<dept>_<année>_<mois>.json.

    La liste des documents d'un mois est stable (les RAA du mois ne changent
    pas) ; la mettre en cache permet de la calculer une seule fois (phase de
    liste coûteuse en requêtes, non reprenable) et de n'en faire qu'à la
    reprise (téléchargements) lors des relances après blocage WAF.
    """
    return os.path.join(
        dest_folder, ".raa_list",
        f"{unidecode(department).lower()}_{year}_{month}.json",
    )


def limit_to_recent(pdf_links, max_docs):
    """Retourne les ``max_docs`` documents les plus récents (la liste est
    triée en ordre chronologique croissant). Inchangé si ``max_docs`` est
    nul ou supérieur à la taille de la liste."""
    if not max_docs or len(pdf_links) <= max_docs:
        return pdf_links
    return pdf_links[-max_docs:]


def merged_filename(month_name, year, department, partial=False):
    """Nom du PDF fusionné ; « partiel » si mode --max-docs."""
    kind = "fusionne_partiel" if partial else "fusionne"
    return f"RAA_{kind}_{month_name}_{year}_{department}.pdf"


def load_or_list(client, month, cache_file, refresh=False):
    """Retourne la liste des PDF du mois, depuis le cache s'il est présent,
    sinon en interrogeant le site (et en écrivant le cache)."""
    if not refresh and os.path.isfile(cache_file):
        with open(cache_file, encoding="utf-8") as f:
            pdf_links = [tuple(item) for item in json.load(f)]
        print(f"Liste en cache ({len(pdf_links)} docs) : {cache_file}")
        return pdf_links
    pdf_links = client.documents_for_month(month)
    os.makedirs(os.path.dirname(cache_file), exist_ok=True)
    with open(cache_file, "w", encoding="utf-8") as f:
        json.dump([list(item) for item in pdf_links], f, ensure_ascii=False)
    print(f"Liste actualisée puis mise en cache ({len(pdf_links)} docs).")
    return pdf_links


def run(
    department, year, month, dest_folder,
    request_delay=2.0, max_wait=0, wait_interval=60, refresh=False,
    max_docs=0,
):
    """Récupère puis fusionne le mois : retourne le chemin du PDF fusionné.

    Si un téléchargement échoue (blocage WAF), les PDF déjà complets sont
    conservés : relancer la même commande reprend où s'est arrêté le run.

    Avec ``max_docs`` (mode test), seuls les N documents les plus récents
    du mois sont récupérés et la fusion partielle porte le nom
    « RAA_fusionne_partiel_... ».
    """
    client = build_client(department, year)
    if request_delay is not None:
        client.request_delay = request_delay

    if not wait_until_reachable(client, max_wait, wait_interval):
        raise SystemExit(
            "Blocage WAF non levé avant la fin de l'attente ; relancer plus tard "
            "(les PDF déjà téléchargés sont repris)."
        )

    all_links = load_or_list(
        client, month, cache_path(dest_folder, department, year, month), refresh
    )
    pdf_links = limit_to_recent(all_links, max_docs)
    if not pdf_links:
        raise SystemExit(
            f"Aucun PDF trouvé pour {department} {month}/{year}."
        )
    if max_docs and len(pdf_links) < len(all_links):
        print(
            f"Mode test : {len(pdf_links)} derniers document(s) sur "
            f"{len(all_links)} (fusion partielle)."
        )

    month_name = MONTH_NAMES_FR[month]
    dept_dir = os.path.join(dest_folder, unidecode(department).lower())
    pdf_dir = os.path.join(dept_dir, year, month_name)
    os.makedirs(pdf_dir, exist_ok=True)

    def local_name(pdf_name):
        name = pdf_name.split("/")[-1]
        if not name.endswith(".pdf"):
            name += ".pdf"
        return name

    def local_path(pdf_name):
        return os.path.join(pdf_dir, local_name(pdf_name))

    done = [n for _, n in pdf_links if client._is_complete_pdf(local_path(n))]
    print(
        f"{department} {month_name}/{year} : {len(pdf_links)} document(s), "
        f"{len(done)} déjà téléchargé(s) (reprise)."
    )

    # 1. Téléchargements (reprise : les fichiers complets sont ignorés).
    for pdf_url, pdf_name in pdf_links:
        client.download(pdf_url, local_path(pdf_name))

    # 2. Fusion dans l'ordre chronologique renvoyé par le client.
    merged = os.path.join(
        dept_dir,
        merged_filename(month_name, year, department, partial=bool(max_docs)),
    )
    merger = PdfMerger()
    for pdf_url, pdf_name in pdf_links:
        merger.append(local_path(pdf_name))
    merger.write(merged)
    merger.close()
    print(f"Fusion écrite : {merged}")
    return merged


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Récupérer et fusionner les RAA d'un département/mois."
    )
    parser.add_argument("department", help="Département (ex. Martinique, reunion)")
    parser.add_argument("year", nargs="?", help="Année (ex. 2026)")
    parser.add_argument("month", nargs="?", help="Mois : code MM (08) ou nom (Août)")
    parser.add_argument("dest", nargs="?", help="Dossier de destination (ex. ./raa_pdfs)")
    parser.add_argument(
        "--probe", action="store_true",
        help="Sonde le site (statut + en-têtes WAF/CDN + robots.txt) sans lancer",
    )
    parser.add_argument(
        "--delay", type=float, default=2.0,
        help="Délai minimum entre deux requêtes réseau, en s (défaut 2.0)",
    )
    parser.add_argument(
        "--max-wait", type=float, default=0,
        help="Attente max (s) du déblocage WAF avant le run (0 = pas d'attente)",
    )
    parser.add_argument(
        "--wait-interval", type=float, default=60,
        help="Intervalle (s) entre les sondes de déblocage (défaut 60)",
    )
    parser.add_argument(
        "--refresh", action="store_true",
        help="Re-calculer la liste du mois (ignore le cache)",
    )
    parser.add_argument(
        "--max-docs", type=int, default=0,
        help="Mode test : ne récupérer que les N documents les plus récents "
        "du mois (fusion partielle « RAA_fusionne_partiel_... ») ; 0 = tout",
    )
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="Journaux au niveau DEBUG")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )

    department = resolve_department(args.department)

    if args.probe:
        probe(department, (args.year or "2026").strip())
        return

    if not (args.year and args.month and args.dest):
        raise SystemExit("Il faut <année>, <mois> et <dossier> (ou --probe).")
    year = args.year.strip()
    if not (year.isdigit() and len(year) == 4):
        raise SystemExit(f"Année invalide : {args.year!r}")
    month = resolve_month(args.month)
    if args.max_docs is not None and args.max_docs < 0:
        raise SystemExit("--max-docs doit être un entier positif ou nul.")
    try:
        run(
            department, year, month, args.dest,
            request_delay=args.delay, max_wait=args.max_wait,
            wait_interval=args.wait_interval, refresh=args.refresh,
            max_docs=args.max_docs,
        )
    except RaaError as exc:
        print(f"\nArrêt sur blocage WAF : {exc}")
        print(
            "Relancer la même commande pour reprendre : la liste est en cache et "
            "les PDF déjà complets ne sont pas retéléchargés."
        )
        raise SystemExit(1)


if __name__ == "__main__":
    main()
