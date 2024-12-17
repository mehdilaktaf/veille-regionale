from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os, time, requests
from PyPDF2 import PdfMerger

def download_raa_pdfs(base_url, headers, target_month, download_dir):
    # Initialisation du navigateur
    driver = webdriver.Chrome("C:\\Users\\camel\\Documents\\python_projects\\veille-regionale\\chromedriver-win64\\chromedriver")  # Remplacez par votre driver
    driver.get(base_url)

    # Fermer le pop-up de cookies
    try:
        # Attendre que le bouton "Tout refuser" apparaisse
        cookie_deny_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "tarteaucitronAllDenied2"))
        )
        # Cliquer sur le bouton "Tout refuser" deux fois
        cookie_deny_button.click()
        time.sleep(1)
        cookie_deny_button.click()
        time.sleep(1)
        print("Pop-up de cookies fermé avec succès.")
    except Exception as e:
        print(f"Pop-up de cookies non trouvé ou erreur lors de la fermeture : {e}")

    try:
        # Récupérer toutes les options du menu déroulant
        options = driver.find_elements(By.CSS_SELECTOR, '#Liste-liste-docs option')
        pdf_list_values = []
        pdf_links = []

        for option in options:
            # Extraire la date au format dd/mm/yyyy à partir du texte
            option_text = option.text
            date_part = option_text.split("publié le")[-1].strip()

            # Filtrer uniquement les options contenant /11/ dans la date
            if target_month in date_part:
                # Ajouter les valeurs de la liste qui match avec le mois cible
                pdf_list_values.append(option.get_attribute('value'))

        if not pdf_list_values:
            print(f"Aucune option trouvée pour le mois {target_month}.")
            return

        # Sélectionner les PDFs correspondants au mois cible
        for option_value in pdf_list_values:
            # Sélectionner l'option dans la liste déroulante
            option = Select(driver.find_element(By.ID, "Liste-liste-docs"))
            option.select_by_value(option_value)

            # Cliquer sur le bouton "Valider"
            driver.find_element(By.CSS_SELECTOR, "input[type='submit'][value='Valider']").click()

            # Attendre que le lien de téléchargement apparaisse dans la div avec la classe 'liste_deroulante'
            try:
                download_div = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".liste_deroulante"))
                )
                # Trouver le lien de téléchargement dans la div
                download_link = download_div.find_element(By.CSS_SELECTOR, "a.fr-link--download").get_attribute("href")

                # Afficher le lien de téléchargement pour vérification
                print(f"Lien de téléchargement trouvé : {download_link}")
                # Ajouter le lien de téléchargement à la liste des liens
                pdf_links.append((download_link, option_value))

                # # Télécharger le fichier
                # response = requests.get(download_link, stream=True)
                # file_name = os.path.join(download_dir, download_link.split("/")[-1])
                # with open(file_name, "wb") as pdf_file:
                #     pdf_file.write(response.content)
                # print(f"Téléchargé : {file_name}")

            except Exception as e:
                print(f"Erreur lors de la récupération du lien de téléchargement pour {option_value}: {e}")
                continue

        # Télécharger chaque PDF
        for pdf_url, pdf_name in pdf_links:
            pdf_file_name = download_dir + "/" + f"{pdf_name.split('/')[-1]}.pdf"
            response = requests.get(pdf_url, headers=headers)

            with open(pdf_file_name, "wb") as pdf_file:
                pdf_file.write(response.content)
            print(f"Téléchargé : {pdf_file_name}")

    finally:
        driver.quit()

def merge_pdfs(pdf_dir, output_file):
    merger = PdfMerger()
    pdf_files = [f for f in os.listdir(pdf_dir) if f.endswith(".pdf")]

    for pdf_file in sorted(pdf_files):
        merger.append(os.path.join(pdf_dir, pdf_file))

    merger.write(output_file)
    merger.close()
    print(f"PDF fusionné écrit dans : {output_file}")

if __name__ == "__main__":
    TARGET_MONTHS = { "Janvier": "/1/", "Février": "/2/", "Mars": "/3/", "Avril": "/4/", "Mai": "/5/", "Juin": "/6/", "Juillet": "/7/", "Août": "/8/", "Septembre": "/9/", "Octobre": "/10/", "Novembre": "/11/", "Décembre": "/12/" }
    BASE_URL = "https://www.vendee.gouv.fr/Publications/Recueil-des-actes-administratifs/Recueils-des-Actes-Administratifs-2024"
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0 Safari/537.36"
    }
    TARGET_MONTH = TARGET_MONTHS["Novembre"]
    DOWNLOAD_DIR = "./raa_pdfs"
    OUTPUT_FILE = "./raa_pdfs/RAA_Novembre.pdf"

    os.makedirs(DOWNLOAD_DIR, exist_ok=True)

    # Étape 1 : Télécharger les PDF
    download_raa_pdfs(BASE_URL, HEADERS, TARGET_MONTH, DOWNLOAD_DIR)

    # Étape 2 : Fusionner les PDF
    merge_pdfs(DOWNLOAD_DIR, OUTPUT_FILE)