# Veille Régionale

Ce projet permet d'automatiser la veille sur les Recueils des Actes Administratifs (RAA) des départements de la région Pays de la Loire. Il automatise la récupération des PDFs, leur fusion et l'analyse de leur contenu pour identifier des mots-clés spécifiques.

## 🚀 Fonctionnalités

- **Interface Streamlit (Nouvel)** : Carte interactive pour sélectionner les départements et lancer des imports/fusions en masse.
- **Automatisation du Scraping** : Récupération automatique des PDFs de RAA depuis les portails gouvernementaux (Maine-et-Loire, Vendée, Loire-Atlantique, Mayenne, Sarthe).
- **Fusion de Documents** : Fusion des PDFs téléchargés pour un mois et un département donnés en un seul fichier.
- **Analyse Intelligente** : Extraction du texte en **gras** des PDFs pour identifier des arrêtés administratifs basés sur une liste de mots-clés (ex: ZFE, sécheresse, bruit, etc.).
- **Export Excel** : Sauvegarde des résultats de l'analyse dans un fichier Excel.

## 🛠️ Installation

### Prérequis
- Python 3.x
- Navigateur Google Chrome installé

### Configuration
1. Clonez le dépôt.
2. Installez les dépendances :
   ```bash
   pip install -r requirements.txt
   ```

## 💻 Utilisation

### 1. Application Streamlit (Interactive)
L'interface web permet de sélectionner des départements sur une carte et de lancer des imports ou des fusions de documents.
```bash
.venv/bin/python -m streamlit run streamlit_app.py
```

### 2. Application Graphique (GUI)
L'interface classique permet de sélectionner un département, une année et un mois.
```bash
python app.py
```

### 2. Analyse des Documents
Le script d'analyse recherche des mots-clés dans le texte en gras d'un PDF fusionné.
```bash
# Utilisation avec le chemin par défaut
python analyse.py

# Utilisation avec un chemin spécifique
python analyse.py "chemin/vers/votre/document.pdf"
```

### 3. Script de Récupération Standalone
Pour récupérer et fusionner les PDFs sans passer par l'interface graphique :
```bash
python fetch_and_merge_pdf.py
```

## 📁 Structure du Projet

- `streamlit_app.py` : Interface interactive avec carte (Streamlit).
- `run.py` : CLI headless pour récupérer et fusionner les RAA d'un département/mois.
- `app.py` : Point d'entrée principal (Interface GUI Tkinter).
- `analyse.py` : Logique d'extraction et de recherche de mots-clés.
- `src/` : Cœur de l'application.
    - `raa_client.py` : Base partagée des clients HTTP.
    - `raa_core.py` : Logique métier commune.
    - `clients/` : Implémentations spécifiques par département.
- `tests/` : Suite de tests unitaires et d'intégration.
- `requirements.txt` : Liste des dépendances Python.
- `raa_pdfs/` : Dossier de stockage temporaire pour les PDFs téléchargés.
