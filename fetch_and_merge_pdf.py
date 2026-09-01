import os
import logging

from PyPDF2 import PdfMerger

from vendee_client import VendeeRaaClient


def download_raa_pdfs(base_url, target_month, download_dir):
    client = VendeeRaaClient(base_url)
    pdf_links = client.documents_for_month(target_month)

    downloaded = []
    for pdf_url, pdf_name in pdf_links:
        pdf_file_name = os.path.join(download_dir, pdf_name)
        client.download(pdf_url, pdf_file_name)
        print(f"Téléchargé : {pdf_file_name}")
        downloaded.append(pdf_name)
    return downloaded


def merge_pdfs(pdf_dir, output_file, pdf_files):
    merger = PdfMerger()

    for pdf_file in sorted(pdf_files):
        merger.append(os.path.join(pdf_dir, pdf_file))

    merger.write(output_file)
    merger.close()
    print(f"PDF fusionné écrit dans : {output_file}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    TARGET_MONTHS = { "Janvier": "01", "Février": "02", "Mars": "03", "Avril": "04", "Mai": "05", "Juin": "06", "Juillet": "07", "Août": "08", "Septembre": "09", "Octobre": "10", "Novembre": "11", "Décembre": "12" }
    BASE_URL = "https://www.vendee.gouv.fr/Publications/Recueil-des-actes-administratifs/Recueils-des-Actes-Administratifs-2024"
    TARGET_MONTH = TARGET_MONTHS["Novembre"]
    DOWNLOAD_DIR = "./raa_pdfs/vendee/2024/novembre"
    OUTPUT_FILE = "./raa_pdfs/vendee/RAA_Novembre.pdf"

    os.makedirs(DOWNLOAD_DIR, exist_ok=True)

    # Étape 1 : Télécharger les PDF
    downloaded = download_raa_pdfs(BASE_URL, TARGET_MONTH, DOWNLOAD_DIR)
    print(f"{len(downloaded)} document(s) du mois {TARGET_MONTH} téléchargé(s).")

    # Étape 2 : Fusionner les PDF du run courant uniquement
    merge_pdfs(DOWNLOAD_DIR, OUTPUT_FILE, downloaded)
