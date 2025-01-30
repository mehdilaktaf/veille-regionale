import os
import threading
import logging
import subprocess
import requests
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from PyPDF2 import PdfMerger
import time
from datetime import datetime
from unidecode import unidecode

logging.basicConfig(filename='app.log', level=logging.INFO)

class VeilleRegionaleApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Veille Régionale")
        self.root.geometry("400x480")

        # Centrer la fenêtre
        self.center_window()
        
        # Variables
        self.dept_var = tk.StringVar()
        self.dest_folder_var = tk.StringVar()
        self.month_var = tk.StringVar()
        self.month_var.set("Janvier")
        self.year_var = tk.StringVar()
        
        # Dictionnaire des mois 
        self.months = { "Janvier": "01", "Février": "02", "Mars": "03", 
                       "Avril": "04", "Mai": "05", "Juin": "06",
                       "Juillet": "07", "Août": "08", "Septembre": "09",
                       "Octobre": "10", "Novembre": "11", "Décembre": "12" }
        self.month_names = { "01": "janvier", "02": "février", "03": "mars", "04": "avril", "05": "mai", "06": "juin", "07": "juillet", "08": "août", "09": "septembre", "10": "octobre", "11": "novembre", "12": "décembre" }

        # Dictionary for department URLs with placeholders for the year
        self.department_urls = {
            "Maine-et-Loire": "https://www.maine-et-loire.gouv.fr/Publications/Recueil-des-Actes-Administratifs",
            "Vendée": "https://www.vendee.gouv.fr/Publications/Recueil-des-actes-administratifs/Recueils-des-Actes-Administratifs-{year}",
            "Loire-Atlantique": "https://www.loire-atlantique.gouv.fr/Publications/Recueil-des-actes-administratifs-RAA-en-Loire-Atlantique/{year}/",
            "Mayenne": "https://www.mayenne.gouv.fr/Publications/Recueil-Actes-Administratifs/Annee-{year}",
            "Sarthe": "https://www.sarthe.gouv.fr/Publications/Recueils-des-actes-administratifs",
        }
        
        # Years for OptionMenu - current year to current year - 3
        current_year = datetime.now().year
        self.years = [str(year) for year in range(current_year, current_year - 4, -1)]
        self.year_var.set(self.years[0])  # Set default to current year

        # Widgets
        # tk.Label(root, text="Lien du site régional :").pack(pady=5)
        # self.url_entry = tk.Entry(root, textvariable=self.url_var, width=50)
        # self.url_entry.pack(pady=5)
        # self.url_entry.insert(0, "https://www.maine-et-loire.gouv.fr/Publications/Recueil-des-Actes-Administratifs/Annee-20252/Annee-2025")
        tk.Label(root, text="Choisir un département :").pack(pady=5)
        self.dept_menu = tk.OptionMenu(root, self.dept_var, *self.department_urls.keys())
        self.dept_menu.pack(pady=5)
        self.dept_var.set(list(self.department_urls.keys())[-1])  # Set default to last department
        
        tk.Label(root, text="Dossier de destination :").pack(pady=5)
        self.dest_entry = tk.Entry(root, textvariable=self.dest_folder_var, width=50)
        self.dest_entry.pack(pady=5)
        self.dest_entry.insert(0, "C:/Users/camel/Documents/recueils-admins")
        tk.Button(root, text="Parcourir", command=self.browse_folder).pack(pady=5)
        
        # Year selection
        tk.Label(root, text="Choisir une année :").pack(pady=5)
        self.year_menu = tk.OptionMenu(root, self.year_var, *self.years)
        self.year_menu.pack(pady=5)

        tk.Label(root, text="Choisir un mois :").pack(pady=5) 
        self.month_menu = tk.OptionMenu(root, self.month_var, *self.months.keys()) 
        self.month_menu.pack(pady=5)

        tk.Button(root, text="Fusionner", command=self.start_thread).pack(pady=20)
        # tk.Button(root, text="Fusionner", command=self.start_process).pack(pady=20)

        # Barre de progression
        self.progress_label = tk.Label(root, text="")
        self.progress_label.pack(pady=5)
        self.progress = ttk.Progressbar(root, orient="horizontal", length=300, mode="determinate")
        self.progress.pack(pady=5)
        # Initially set progress to zero before starting
        self.progress['value'] = 0
        self.progress['maximum'] = 100
    
    def center_window(self):
        """Centre la fenêtre sur l'écran"""
        # Mettre à jour la fenêtre pour obtenir sa taille réelle
        self.root.update_idletasks()
        
        # Obtenir la largeur et la hauteur de l'écran
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        # Obtenir la largeur et la hauteur de la fenêtre
        window_width = self.root.winfo_width()
        window_height = self.root.winfo_height()
        
        # Calculer la position x et y pour centrer la fenêtre
        x = (screen_width // 2) - (window_width // 2)
        y = (screen_height // 2) - (window_height // 2)
        
        # Définir la position de la fenêtre
        self.root.geometry(f"+{x}+{y}")
        
    def browse_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.dest_folder_var.set(folder)

    def start_thread(self):
        """
        Démarre le processus dans un thread séparé.
        """
        self.progress["value"] = 0
        self.progress_label.config(text="Traitement en cours...")
        threading.Thread(target=self.run_scraping_process, daemon=True).start()

    def run_scraping_process(self):
        """
        Exécute le processus principal et met à jour l'interface utilisateur une fois terminé.
        """
        try:
            department = self.dept_var.get()
            year = self.year_var.get()
            url = self.department_urls[department].format(year=year)
            dest_folder = self.dest_folder_var.get()
            month = self.months[self.month_var.get()]
            self.scrape_and_merge(url, dest_folder, month)
            self.progress_label.config(text="Traitement terminé avec succès.")
        except Exception as e:
            self.progress_label.config(text=f"Erreur : {e}")
            messagebox.showerror("Erreur", str(e))
        
    def extraction_vendee(self, driver, month):
        """
        Extrait les liens de téléchargement des PDFs correspondant au mois donné.

        Args:
            url (str): URL du site à scraper.
            month (str): Mois cible (format : "MM").

        Returns:
            list: Liste de tuples contenant les liens des PDFs et leurs noms.
        """

        pdf_links = []
        time.sleep(10)
        try:
            # Fermer le pop-up de cookies
            cookie_deny_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.ID, "tarteaucitronAllDenied2"))
            )
            cookie_deny_button.click()
            time.sleep(1)
            cookie_deny_button.click()
        except Exception as e:
            logging.info(f"Erreur lors de la fermeture du pop-up de cookies : {e}")

        # Récupérer toutes les options du menu déroulant
        options = driver.find_elements(By.CSS_SELECTOR, '#Liste-liste-docs option')
        pdf_list_values = [
            option.get_attribute('value')
            for option in options
            if month in option.text.split("publié le")[-1].strip()
        ]

        if not pdf_list_values:
            logging.info(f"Aucune option trouvée pour le mois {month}.")
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
                logging.info(f"Erreur lors de la récupération du lien pour {option_value}: {e}")

        return pdf_links

    def extraction_sarthe(self, driver, month):
        """
        Extrait les liens de téléchargement des PDFs correspondant au mois donné.

        Args:
            url (str): URL du site à scraper.
            month (str): Mois cible (format : "MM").

        Returns:
            list: Liste de tuples contenant les liens des PDFs et leurs noms.
        """

        pdf_links = []
        time.sleep(10)
        try:
            # Fermer le pop-up de cookies
            cookie_deny_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.ID, "tarteaucitronAllDenied2"))
            )
            cookie_deny_button.click()
            time.sleep(1)
            cookie_deny_button.click()
        except Exception as e:
            logging.info(f"Erreur lors de la fermeture du pop-up de cookies : {e}")

        # Récupérer toutes les options du menu déroulant
        options = driver.find_elements(By.CSS_SELECTOR, '#Liste-liste-docs option')
        pdf_list_values = [
            option.get_attribute('value')
            for option in options
            if option.get_attribute('title') != ""
        ]

        if not pdf_list_values:
            logging.info(f"Aucune option trouvée pour le mois {month}.")
            return []

        # Récupérer les liens de téléchargement pour chaque option
        for option_value in pdf_list_values:
            select = Select(driver.find_element(By.ID, "Liste-liste-docs"))
            if "2025" in option_value:
                print(f"option_value: {option_value}")
                select.select_by_value(option_value)
                break
        driver.find_element(By.CSS_SELECTOR, "input[type='submit'][value='Valider']").click()

        try:
            download_links = driver.find_elements(By.CSS_SELECTOR, "a.fr-link.fr-link--download")
            print(f"download_links: {download_links}")
            for download_link in download_links:
                url, name = (download_link.get_attribute("href"), download_link.get_attribute("href").split("/")[-1])
                logging.info(f"url: {url}, name: {name}")
                print(f"url: {url}, name: {name}")
                if month in name:
                    logging.info(download_link.get_attribute("href"))
                    pdf_links.append((url, name))
        except Exception as e:
            logging.info(f"Erreur lors de la récupération du lien: {e}")

        return pdf_links

    def extraction_maine_et_loire(self, driver, month):
        """
        Extrait les liens de téléchargement des PDFs correspondant au mois donné.

        Args:
            url (str): URL du site à scraper.
            month (str): Mois cible (format : "MM").

        Returns:
            list: Liste de tuples contenant les liens des PDFs et leurs noms.
        """

        pdf_links = []
        year = self.year_var.get()

        try:
            # Fermer le pop-up de cookies
            cookie_deny_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.ID, "tarteaucitronAllDenied2"))
            )
            cookie_deny_button.click()
            time.sleep(1)
            cookie_deny_button.click()
            # Chercher tous les h2 avec la classe "fr-card__title"
            h2_elements = driver.find_elements(By.CSS_SELECTOR, "h2.fr-card__title")
            for h2 in h2_elements:
                a_element = h2.find_element(By.TAG_NAME, "a")
                if f"Année {year}" in a_element.text:
                    # Naviguer vers la page de l'année
                    a_element.click()
                    break
            else:
                logging.info(f"Année {year} non trouvée dans la page")
        except Exception as e:
            logging.info(f"Erreur lors de la fermeture du pop-up de cookies : {e}")

        try:
            download_div = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".fr-col-12.fr-col-md-8"))
            )
            # logging.info("download_div", download_div)
        except Exception as e:
            logging.info(f"Erreur lors de la récupération de la div: {e}")
        
        try:
            download_links = download_div.find_elements(By.CSS_SELECTOR, "a.fr-link.fr-link--download")
            logging.info("download_links", download_links)
            for download_link in download_links:
                url, name = (download_link.get_attribute("href"), download_link.get_attribute("href").split("/")[-1])
                logging.info(f"url: {url}, name: {name}")
                if self.month_names[month] in name:
                    logging.info("self.month_names[month]", self.month_names[month])
                    logging.info(download_link.get_attribute("href"))
                    pdf_links.append((url, name))
        except Exception as e:
            logging.info(f"Erreur lors de la récupération du lien: {e}")

        return pdf_links

    def extraction_mayenne(self, driver, month):
        """
        Extrait les liens de téléchargement des PDFs correspondant au mois donné.

        Args:
            url (str): URL du site à scraper.
            month (str): Mois cible (format : "MM").

        Returns:
            list: Liste de tuples contenant les liens des PDFs et leurs noms.
        """

        pdf_links = []
        year = self.year_var.get()
        month_as_text = self.month_var.get()
        try:
            # Fermer le pop-up de cookies
            cookie_deny_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.ID, "tarteaucitronAllDenied2"))
            )
            cookie_deny_button.click()
            time.sleep(1)
            cookie_deny_button.click()
        except Exception as e:
            logging.info(f"Erreur lors de la fermeture du pop-up de cookies : {e}")
            print(f"Erreur lors de la fermeture du pop-up de cookies : {e}")
        
        try:
            if int(year) < 2025:
                download_links = driver.find_elements(By.CSS_SELECTOR, "a.fr-link.fr-link--download")
                for download_link in download_links:
                    url, name = (download_link.get_attribute("href"), download_link.get_attribute("href").split("/")[-1])
                    logging.info(f"url: {url}, name: {name}")
                    print(f"url: {url}, name: {name}")
                    if self.month_names[month] in name:
                        pdf_links.append((url, name))
            else:
                # Chercher tous les h2 avec la classe "fr-card__title"
                h2_elements = driver.find_elements(By.CSS_SELECTOR, "h2.fr-card__title")
                for h2 in h2_elements:
                    a_element = h2.find_element(By.TAG_NAME, "a")
                    if f"{month_as_text} {year}" in a_element.text:
                        # Naviguer vers la page de l'année
                        a_element.click()
                        break
                    else:
                        logging.info(f"Année {year} ou mois {month_as_text} non trouvée dans la page")
                        print(f"Année {year} ou mois {month_as_text} non trouvée dans la page")
                
                download_links = driver.find_elements(By.CSS_SELECTOR, "a.fr-link.fr-link--download")
                for download_link in download_links:
                    url, name = (download_link.get_attribute("href"), download_link.text)
                    logging.info(f"url: {url}, name: {name}")
                    print(f"url: {url}, name: {name}")
                    if self.month_names[month] in name:
                        print(f"self.month_names[month]: {self.month_names[month]}")
                        pdf_links.append((url, name))
        except Exception as e:
            logging.info(f"Erreur lors de la récupération des liens: {e}")
            print(f"Erreur lors de la récupération des liens: {e}")

        return pdf_links

    def extraction_loire_atlantique(self, driver, month):
        """
        Extrait les liens de téléchargement des PDFs correspondant au mois donné.

        Args:
            url (str): URL du site à scraper.
            month (str): Mois cible (format : "MM").

        Returns:
            list: Liste de tuples contenant les liens des PDFs et leurs noms.
        """

        pdf_links = []
        year = self.year_var.get()
        try:
            # Fermer le pop-up de cookies
            cookie_deny_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.ID, "tarteaucitronAllDenied2"))
            )
            cookie_deny_button.click()
            time.sleep(1)
            cookie_deny_button.click()
        except Exception as e:
            logging.info(f"Erreur lors de la fermeture du pop-up de cookies : {e}")

        try:
            try:
                download_div = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".fr-col-12.fr-col-md-8"))
                )
            except Exception as e:
                logging.info(f"Erreur lors de la récupération de la div: {e}")
            
            nb_of_pages = 1
            try:
                # Attendre que l'élément `ul` avec la classe `fr-pagination__list` soit présent
                pagination_ul = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "ul.fr-pagination__list"))
                )

                # Obtenir tous les éléments `li` sous ce `ul`
                li_elements = pagination_ul.find_elements(By.TAG_NAME, "li")

                # Retourner le nombre d'éléments `li`
                nb_of_pages = len(li_elements) - 4 # Le "-4" est pour les liens précédent et suivant et première et dernière page 
                print(f"nb_of_pages: {nb_of_pages}")    
            except Exception as e:
                print(f"Erreur lors de la récupération des éléments de pagination : {e}")

            for i in range(nb_of_pages):
                print(f"Dowloading links of page {i+1}/{nb_of_pages}")
                download_links = driver.find_elements(By.CSS_SELECTOR, ".fr-card__link.menu-item-link")
                logging.info(f"download_links: {download_links}")
                for download_link in download_links:
                    url, name = (download_link.get_attribute("href"), download_link.get_attribute("href").split("/")[-1])
                    logging.info(f"url: {url}, name: {name}")
                    print(f"url: {url}, name: {name}")
                    if self.month_names[month] in name:
                        logging.info(f"self.month_names[month]: {self.month_names[month]}")
                        logging.info(f"download_link.get_attribute('href'): {download_link.get_attribute('href')}")
                        pdf_links.append((url, name))
                # Navigate to next page
                try:
                    next_page = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, ".fr-pagination__link.fr-pagination__link--next"))
                    )
                    next_page.click()
                except Exception as e:
                    logging.info(f"Erreur lors de la navigation vers la page suivante : {e}")
                    break
        except Exception as e:
            logging.info(f"Erreur lors de la récupération du lien: {e}")
        return pdf_links

    def get_driver(self, url):
        service = Service(ChromeDriverManager().install())
        service.creation_flags = subprocess.CREATE_NO_WINDOW
        
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        
        driver = webdriver.Chrome(service=service, options=options)
        driver.get(url)
        # time.sleep(30)

        # Initially set progress to zero before starting
        self.progress['value'] += 5
        self.root.update_idletasks()
        return driver


    def scrape_and_merge(self, url, dest_folder, month):
        # Obtenir l'année et le département sélectionnés
        year = self.year_var.get()
        department = self.dept_var.get()

        # Construire l'URL complète en fonction du département et de l'année
        url_template = self.department_urls[department]
        url = url_template.format(year=year)
        
        # Démarrer le driver et extraire les PDF
        driver = self.get_driver(url)
        pdf_links = []

        # Mois dans l'url
        month_as_text = self.month_var.get()
        # Convertir le mois en texte sans accents
        month_no_accent = unidecode(month_as_text)

        # Vérifier quel département a été choisi et extraire en conséquence
        if "vendee" in url:
            pdf_links = self.extraction_vendee(driver, month)
        elif "maine-et-loire" in url:
            pdf_links = self.extraction_maine_et_loire(driver, month)
        elif "loire-atlantique" in url:
            driver= self.get_driver(url+f"{month_no_accent}")
            pdf_links = self.extraction_loire_atlantique(driver, month)
        elif "mayenne" in url:
            pdf_links = self.extraction_mayenne(driver, month)
        elif "sarthe" in url:
            pdf_links = self.extraction_sarthe(driver, month)
        
        logging.info("Fermeture du navigateur...")
        driver.quit()

        if not pdf_links:
            if self.month_names[month]=="août":
                raise Exception(f"Aucun PDF trouvé pour le mois d'{self.month_names[month]}.")
            else:
                raise Exception(f"Aucun PDF trouvé pour le mois de {self.month_names[month]}.")

        # Initialiser la barre de progression
        total_pdfs = len(pdf_links)
        self.progress['maximum'] = total_pdfs

        merger = PdfMerger()
        for index, (pdf_url, pdf_name) in enumerate(pdf_links):
            # Télécharger et ajouter chaque PDF
            pdf_path = os.path.join(dest_folder, f"{pdf_name.split('/')[-1]}.pdf")
            headers = {"User-Agent": "Mozilla/5.0"}
            response = requests.get(pdf_url, headers=headers)
            with open(pdf_path, "wb") as f:
                f.write(response.content)
            merger.append(pdf_path)

            # Mettre à jour la barre de progression
            self.progress['value'] = index + 1
            self.root.update_idletasks()

        # Écriture du fichier PDF fusionné et fermeture du merger
        merged_pdf_path = os.path.join(dest_folder, f"RAA_fusionne_{self.month_names[month]}_{self.year_var.get()}_{department}.pdf")
        merger.write(merged_pdf_path)
        merger.close()
        
if __name__ == "__main__":
    root = tk.Tk()
    app = VeilleRegionaleApp(root)
    root.mainloop()
