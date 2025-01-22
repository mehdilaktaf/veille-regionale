import os
import requests
import tkinter as tk
from tkinter import filedialog, messagebox
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from PyPDF2 import PdfMerger
import time

class VeilleRegionaleApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Veille Régionale")
        self.root.geometry("400x300")

        # Variables
        self.url_var = tk.StringVar()
        self.dest_folder_var = tk.StringVar()
        self.month_var = tk.StringVar()
        self.month_var.set("Janvier")
        
        # Dictionnaire des mois 
        self.months = { "Janvier": "01", "Février": "02", "Mars": "03", 
                       "Avril": "04", "Mai": "05", "Juin": "06",
                       "Juillet": "07", "Août": "08", "Septembre": "09",
                       "Octobre": "10", "Novembre": "11", "Décembre": "12" }

        # Widgets
        tk.Label(root, text="Lien du site régional :").pack(pady=5)
        self.url_entry = tk.Entry(root, textvariable=self.url_var, width=50)
        self.url_entry.pack(pady=5)
        self.url_entry.insert(0, "https://www.maine-et-loire.gouv.fr/Publications/Recueil-des-Actes-Administratifs/Annee-20252/Annee-2025")

        tk.Label(root, text="Dossier de destination :").pack(pady=5)
        self.dest_entry = tk.Entry(root, textvariable=self.dest_folder_var, width=50)
        self.dest_entry.pack(pady=5)
        self.dest_entry.insert(0, "C:/Users/camel/Documents/recueils-admins")
        tk.Button(root, text="Parcourir", command=self.browse_folder).pack(pady=5)

        tk.Label(root, text="Choisir un mois :").pack(pady=5) 
        self.month_menu = tk.OptionMenu(root, self.month_var, *self.months.keys()) 
        self.month_menu.pack(pady=5)

        tk.Button(root, text="Fusionner", command=self.start_process).pack(pady=20)

    def browse_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.dest_folder_var.set(folder)

    def start_process(self):
        url = self.url_var.get()
        dest_folder = self.dest_folder_var.get()
        selected_month_text = self.month_var.get()
        selected_month_value = self.months[selected_month_text]
        month = selected_month_value

        if not url or not dest_folder or not month:
            messagebox.showerror("Erreur", "Veuillez remplir tous les champs !")
            return

        try:
            self.scrape_and_merge(url, dest_folder, month)
            messagebox.showinfo("Succès", "Les PDFs ont été fusionnés avec succès !")
        except Exception as e:
            messagebox.showerror("Erreur", f"Une erreur s'est produite : {e}")

    def extraction_vendee(self, url, month):
        """
        Extrait les liens de téléchargement des PDFs correspondant au mois donné.

        Args:
            url (str): URL du site à scraper.
            month (str): Mois cible (format : "MM").

        Returns:
            list: Liste de tuples contenant les liens des PDFs et leurs noms.
        """
        service = Service(ChromeDriverManager().install())
        options = webdriver.ChromeOptions()
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        
        driver = webdriver.Chrome(service=service, options=options)
        driver.get(url)
        pdf_links = []

        try:
            # Fermer le pop-up de cookies
            cookie_deny_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.ID, "tarteaucitronAllDenied2"))
            )
            cookie_deny_button.click()
            time.sleep(1)
            cookie_deny_button.click()
        except Exception as e:
            print(f"Erreur lors de la fermeture du pop-up de cookies : {e}")

        try:
            # Récupérer toutes les options du menu déroulant
            options = driver.find_elements(By.CSS_SELECTOR, '#Liste-liste-docs option')
            pdf_list_values = [
                option.get_attribute('value')
                for option in options
                if month in option.text.split("publié le")[-1].strip()
            ]

            if not pdf_list_values:
                print(f"Aucune option trouvée pour le mois {month}.")
                return []

            # Récupérer les liens de téléchargement pour chaque option
            for option_value in pdf_list_values:
                select = Select(driver.find_element(By.ID, "Liste-liste-docs"))
                select.select_by_value(option_value)

                driver.find_element(By.CSS_SELECTOR, "input[type='submit'][value='Valider']").click()

                try:
                    download_div = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, ".liste_deroulante"))
                    )
                    download_link = download_div.find_element(By.CSS_SELECTOR, "a.fr-link--download").get_attribute("href")
                    pdf_links.append((download_link, option_value))
                except Exception as e:
                    print(f"Erreur lors de la récupération du lien pour {option_value}: {e}")

        finally:
            print("Fermeture du navigateur...")
            driver.quit()

        return pdf_links

    def extraction_maine_et_loire(self, url, month):
        """
        Extrait les liens de téléchargement des PDFs correspondant au mois donné.

        Args:
            url (str): URL du site à scraper.
            month (str): Mois cible (format : "MM").

        Returns:
            list: Liste de tuples contenant les liens des PDFs et leurs noms.
        """
        service = Service(ChromeDriverManager().install())
        options = webdriver.ChromeOptions()
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        
        driver = webdriver.Chrome(service=service, options=options)
        driver.get(url)
        pdf_links = []

        try:
            # Fermer le pop-up de cookies
            cookie_deny_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.ID, "tarteaucitronAllDenied2"))
            )
            cookie_deny_button.click()
            time.sleep(1)
            cookie_deny_button.click()
        except Exception as e:
            print(f"Erreur lors de la fermeture du pop-up de cookies : {e}")

        try:
            download_div = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".fr-col-12.fr-col-md-8"))
            )
            print("download_div", download_div)
        except Exception as e:
            print(f"Erreur lors de la récupération de la div: {e}")
        
        try:
            download_links = download_div.find_elements(By.CSS_SELECTOR, "a.fr-link.fr-link--download")
            print("download_links", download_links)
            for download_link in download_links:
                print(download_link.get_attribute("href"))
                pdf_links.append((download_link.get_attribute("href"), download_link.get_attribute("href").split("/")[-1]))
        except Exception as e:
            print(f"Erreur lors de la récupération du lien: {e}")

        print("Fermeture du navigateur...")
        driver.quit()

        return pdf_links


    def scrape_and_merge(self, url, dest_folder, month):
        """
        Télécharge et fusionne les PDFs d'un mois donné à partir d'une URL.

        Args:
            url (str): URL du site à scraper.
            dest_folder (str): Dossier où sauvegarder les PDFs.
            month (str): Mois cible (format : "MM").
        """
        if url.startswith("https://www.vendee.gouv.fr"):
            pdf_links = self.extraction_vendee(url, month)
        elif url.startswith("https://www.maine-et-loire.gouv.fr/"):
            pdf_links = self.extraction_maine_et_loire(url, month)
        print(f"Liens trouvés pour le mois {month} : {pdf_links}")

        if not pdf_links:
            print(f"Aucun PDF à télécharger pour le mois {month}.")
            return

        # Télécharger et fusionner les PDFs
        merger = PdfMerger()
        for pdf_url, pdf_name in pdf_links:
            print(f"Téléchargement du PDF : {pdf_url}")
            pdf_path = dest_folder + f"{pdf_name.split('/')[-1]}.pdf"
            print(f"Sauvegarde du PDF : {pdf_path}")
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0 Safari/537.36"
            }
            response = requests.get(pdf_url, headers=headers)   
            with open(pdf_path, "wb") as f:
                f.write(response.content)
            merger.append(pdf_path)

        # Sauvegarder le fichier fusionné
        merged_pdf_path = os.path.join(dest_folder, f"RAA_fusionne_{month}.pdf")
        merger.write(merged_pdf_path)
        merger.close()

        print(f"Fichier fusionné sauvegardé sous : {merged_pdf_path}")

if __name__ == "__main__":
    root = tk.Tk()
    app = VeilleRegionaleApp(root)
    root.mainloop()
