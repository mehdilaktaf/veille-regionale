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

class VeilleRegionaleApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Veille Régionale")
        self.root.geometry("400x300")

        # Variables
        self.url_var = tk.StringVar()
        self.dest_folder_var = tk.StringVar()
        self.month_var = tk.StringVar()
        
        # Dictionnaire des mois 
        self.months = { "Janvier": "01", "Février": "02", "Mars": "03", 
                       "Avril": "04", "Mai": "05", "Juin": "06",
                       "Juillet": "07", "Août": "08", "Septembre": "09",
                       "Octobre": "10", "Novembre": "11", "Décembre": "12" }

        # Widgets
        tk.Label(root, text="Lien du site régional :").pack(pady=5)
        self.url_entry = tk.Entry(root, textvariable=self.url_var, width=50)
        self.url_entry.pack(pady=5)

        tk.Label(root, text="Dossier de destination :").pack(pady=5)
        self.dest_entry = tk.Entry(root, textvariable=self.dest_folder_var, width=50)
        self.dest_entry.pack(pady=5)
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
        month = self.month_var.get()

        if not url or not dest_folder or not month:
            messagebox.showerror("Erreur", "Veuillez remplir tous les champs !")
            return

        try:
            self.scrape_and_merge(url, dest_folder, month)
            messagebox.showinfo("Succès", "Les PDFs ont été fusionnés avec succès !")
        except Exception as e:
            messagebox.showerror("Erreur", f"Une erreur s'est produite : {e}")

    def scrape_and_merge(self, url, dest_folder, month):
        # Setup WebDriver
        # driver = webdriver.Chrome(ChromeDriverManager().install())
        # Configure the WebDriver
        service = Service(ChromeDriverManager().install())
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        driver = webdriver.Chrome(service=service, options=options)
        driver.get(url)

        # Liste des fichiers PDF
        pdf_links = []

        # Attendre que la liste déroulante soit chargée
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "Liste-liste-docs")))
        options = driver.find_elements(By.TAG_NAME, "option")

        for option in options:
            if f"/{month}/" in option.text:
                option_value = option.get_attribute("value")
                select = Select(driver.find_element(By.ID, "Liste-liste-docs"))
                select.select_by_value(option_value)

                # Cliquer sur le bouton "Valider"
                driver.find_element(By.CSS_SELECTOR, "input[type='submit']").click()

                # Attendre le lien de téléchargement
                download_link = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "a.fr-link--download"))
                )
                pdf_links.append(download_link.get_attribute("href"))

                # Revenir à la page précédente
                driver.back()

        driver.quit()

        # Télécharger et fusionner les PDFs
        merger = PdfMerger()
        for link in pdf_links:
            pdf_path = os.path.join(dest_folder, os.path.basename(link))
            response = requests.get(link)
            with open(pdf_path, "wb") as f:
                f.write(response.content)
            merger.append(pdf_path)

        # Sauvegarder le fichier fusionné
        merged_pdf_path = os.path.join(dest_folder, "RAA_fusionne_"+str(month)+".pdf")
        merger.write(merged_pdf_path)
        merger.close()

if __name__ == "__main__":
    root = tk.Tk()
    app = VeilleRegionaleApp(root)
    root.mainloop()
