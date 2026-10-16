import os
import logging
from pathlib import Path
from typing import Callable, Optional
from unidecode import unidecode
from PyPDF2 import PdfMerger
from src.clients.clients import build_client

logger = logging.getLogger(__name__)

def scrape_and_merge(
    department: str,
    year: str,
    month: str,
    dest_folder: str | Path,
    progress_cb: Optional[Callable[[int, int, str], None]] = None,
):
    """
    Récupère les PDF d'un département pour un mois donné et les fusionne.
    
    Args:
        department: Nom du département (ex: "Vendée")
        year: Année en chaîne (ex: "2026")
        month: Code mois "MM" (ex: "08")
        dest_folder: Dossier racine de destination
        progress_cb: Callback pour mettre à jour la progression (done, total, message)
    """
    dest_folder = Path(dest_folder)
    
    # 1. Construction du client
    # build_client gère la résolution de l'URL via DEPARTMENT_URLS et le formatage de l'année
    client = build_client(department, year)

    # 2. Récupération des liens
    pdf_links = client.documents_for_month(month)

    if not pdf_links:
        raise Exception(f"Aucun PDF trouvé pour le département {department} en {year}-{month}.")

    # 3. Préparation du dossier de destination
    # Structure : <dest>/<département>/<année>/<mois>/
    dept_slug = unidecode(department).lower()
    # Note: month_name est géré par le client ou needs to be provided. 
    # In app.py, it used self.month_names. Let's implement a helper or use the client.
    # Actually, raa_client.py has MONTH_NAMES_FR.
    from src.raa_client import MONTH_NAMES_FR
    month_name = MONTH_NAMES_FR.get(month, month)
    
    pdf_dir = dest_folder / dept_slug / year / month_name
    pdf_dir.mkdir(parents=True, exist_ok=True)

    # 4. Téléchargement et fusion
    total_pdfs = len(pdf_links)
    merger = PdfMerger()

    for index, (pdf_url, pdf_name) in enumerate(pdf_links):
        name = pdf_name.split("/")[-1]
        if not name.endswith(".pdf"):
            name += ".pdf"
        
        pdf_path = pdf_dir / name
        
        if progress_cb:
            progress_cb(index, total_pdfs, f"Téléchargement de {name}...")
            
        client.download(pdf_url, str(pdf_path))
        merger.append(str(pdf_path))

    # 5. Écriture du fusionné
    merged_pdf_path = dest_folder / dept_slug / f"RAA_fusionne_{month_name}_{year}_{department}.pdf"
    merger.write(str(merged_pdf_path))
    merger.close()
    
    if progress_cb:
        progress_cb(total_pdfs, total_pdfs, "Fusion terminée.")

    return str(merged_pdf_path)
