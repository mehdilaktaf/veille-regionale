import os
import threading
import logging
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
from PyPDF2 import PdfMerger
from datetime import datetime
from unidecode import unidecode
from src.clients.clients import DEPARTMENT_URLS, build_client
from src.raa_core import scrape_and_merge as core_scrape_and_merge

logging.basicConfig(filename='app.log', level=logging.INFO)

class VeilleRegionaleApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Veille Régionale")
        self.root.geometry("400x480")

        # Centrer la fenêtre
        self.center_window()
        
        # Variables
        self.http_client = None
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

        # URLs de base par département ({year} : placeholder année).
        # Source de vérité : clients.py (partagée avec le CLI run.py).
        self.department_urls = DEPARTMENT_URLS
        
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
            dest_folder = self.dest_folder_var.get()
            month = self.months[self.month_var.get()]
            
            def progress_callback(done, total, message):
                self.progress['value'] = (done / total * 100) if total > 0 else 0
                self.progress_label.config(text=message)
                self.root.update_idletasks()

            core_scrape_and_merge(
                department=department,
                year=year,
                month=month,
                dest_folder=dest_folder,
                progress_cb=progress_callback
            )
            self.progress_label.config(text="Traitement terminé avec succès.")
        except Exception as e:
            self.progress_label.config(text=f"Erreur : {e}")
            messagebox.showerror("Erreur", str(e))
        
    if __name__ == "__main__":
        root = tk.Tk()
        app = VeilleRegionaleApp(root)
        root.mainloop()
