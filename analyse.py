import pdfplumber
import pandas as pd
import sys

# Path to the uploaded PDF file
pdf_path = sys.argv[1] if len(sys.argv) > 1 else "C:/Users/camel/Documents/recueils-admins/RAA_fusionne_janvier_2025_Loire-Atlantique.pdf"

# Reading the PDF and extracting bold text
pdf_text = []
with pdfplumber.open(pdf_path) as pdf:
    for page_number, page in enumerate(pdf.pages, start=1):
        print(f"Extracting bold text from page {page_number}...")
        
        # Extraire les caractéristiques du texte
        words = page.extract_words(extra_attrs=['fontname', 'size'])
        
        # Identifier le texte en gras (recherche des polices contenant 'Bold' ou 'bold')
        bold_text = ' '.join([
            word['text'] 
            for word in words 
            if 'Bold' in word['fontname'] or 'bold' in word['fontname']
        ])
        
        if bold_text.strip():  # Si du texte en gras a été trouvé
            pdf_text.append((page_number, bold_text))

# Prepare to identify relevant arrêtés
keywords = [
    "Zones à faibles émissions mobilité", "ZFE-m", "Pic de pollution",
    "Plan Protection Atmosphère", "PPA", "Plan local pour l’amélioration de la qualité de l’air",
    "Plan régional pour la qualité de l'air", "PRQA", "Plan Climat Air-Énergie Territorial",
    "PCAET", "lutte/destruction de certaines espèces", "chardon", "ambroisie",
    "protection de géotope", "protection des habitats naturels", "APHN", "APPHN",
    "protection du biotope", "APB", "APPB", "Natura 2000", "bonnes conditions agro-environnementales",
    "bruit", "réglementation des bruits de voisinage", "SRADDET", "sécheresse",
    "produits phytopharmaceutiques", "Déclaration d'Utilité Publique", "DUP",
    "enquête publique", "aires d'alimentation du captage", "efficacité énergétique", "PREE",
    "risque naturel ou technologique prévisible", "Plan de Prévention du Risques",
    "emploi du feu", "Dossier départemental des risques majeurs", "DDRM", "PPRI",
    "Plan Départemental de Protection des Forêts Contre les Incendies", "PDPFCI",
    "Plan Particulier d'Intervention", "PPI", "Plans de prévention des risques naturels",
    "PPRN", "Plans de prévention des risques technologiques", "PPRT",
    "Schéma Départemental d'Analyse et de Couverture des Risques", "SDACR",
    "Schéma Directeur de Prévision des Crues", "SDPC", "Plan de prévention des risques d’incendies de forêts",
    "PPRIF", "débroussaillement", "OLD", "Stratégie locale du risque Inondation",
    "Règlement sanitaire départemental", "feux en plein air", "usage de l'eau", "limitations d'usage de l'eau"
]

# Search for relevant arrêtés (maintenant uniquement dans le texte en gras)
results = []
for page_number, bold_text in pdf_text:
    for keyword in keywords:
        print(f"Searching for keyword '{keyword}' in bold text of page {page_number}...")
        if keyword.lower() in bold_text.lower():
            results.append({
                "Page Number": page_number,
                "Matched Keyword": keyword,
                "Bold Text": bold_text[:500]  # Limit text to 500 chars for readability
            })

# Convert results to DataFrame and export
results_df = pd.DataFrame(results)

if not results_df.empty:
    print(results_df)
    excel_path = pdf_path.replace('.pdf', '_resultats_bold.xlsx')
    results_df.to_excel(excel_path, index=False, engine='openpyxl')
    print(f"\nLes résultats ont été sauvegardés dans : {excel_path}")
else:
    print("No relevant arrêtés found in bold text.")

# # Script de traitement de donnéesfrom PyPDF2 import PdfReader
# import pandas as pd
# from PyPDF2 import PdfReader
# # Path to the uploaded PDF file
# pdf_path = "C:/Users/camel/Documents/recueils-admins/RAA_fusionne_janvier_2025_Loire-Atlantique.pdf"
 
# # Reading the PDF
# reader = PdfReader(pdf_path)

# # Extract text from each page
# pdf_text = []
# for page_number, page in enumerate(reader.pages, start=1):
#     print(f"Extracting text from page {page_number}...")
#     text = page.extract_text()
#     pdf_text.append((page_number, text))
 
# # Prepare to identify relevant arrêtés
# keywords = [
#     "Zones à faibles émissions mobilité", "ZFE-m", "Pic de pollution",
#     "Plan Protection Atmosphère", "PPA", "Plan local pour l’amélioration de la qualité de l’air",
#     "Plan régional pour la qualité de l'air", "PRQA", "Plan Climat Air-Énergie Territorial",
#     "PCAET", "lutte/destruction de certaines espèces", "chardon", "ambroisie",
#     "protection de géotope", "protection des habitats naturels", "APHN", "APPHN",
#     "protection du biotope", "APB", "APPB", "Natura 2000", "bonnes conditions agro-environnementales",
#     "bruit", "réglementation des bruits de voisinage", "SRADDET", "sécheresse",
#     "produits phytopharmaceutiques", "Déclaration d'Utilité Publique", "DUP",
#     "enquête publique", "aires d'alimentation du captage", "efficacité énergétique", "PREE",
#     "risque naturel ou technologique prévisible", "Plan de Prévention du Risques",
#     "emploi du feu", "Dossier départemental des risques majeurs", "DDRM", "PPRI",
#     "Plan Départemental de Protection des Forêts Contre les Incendies", "PDPFCI",
#     "Plan Particulier d'Intervention", "PPI", "Plans de prévention des risques naturels",
#     "PPRN", "Plans de prévention des risques technologiques", "PPRT",
#     "Schéma Départemental d'Analyse et de Couverture des Risques", "SDACR",
#     "Schéma Directeur de Prévision des Crues", "SDPC", "Plan de prévention des risques d’incendies de forêts",
#     "PPRIF", "débroussaillement", "OLD", "Stratégie locale du risque Inondation",
#     "Règlement sanitaire départemental", "feux en plein air", "usage de l'eau", "limitations d'usage de l'eau"
# ]
 
# # Search for relevant arrêtés
# results = []
# for page_number, text in pdf_text:
#     for keyword in keywords:
#         print(f"Searching for keyword '{keyword}' in page {page_number}...")
#         if keyword.lower() in text.lower():
#             results.append({
#                 "Page Number": page_number,
#                 "Matched Keyword": keyword,
#                 "Extracted Text": text[:500]  # Limit text to 500 chars for readability
#             })
 
# # Convert results to DataFrame for better structuring
# results_df = pd.DataFrame(results)
 
# # Display results to user if any relevant data is found
# if not results_df.empty:
#     print(results_df)
#     # Créer le nom du fichier Excel basé sur le nom du PDF
#     excel_path = pdf_path.replace('.pdf', '_resultats.xlsx')
#     # Exporter en Excel
#     results_df.to_excel(excel_path, index=False, engine='openpyxl')
#     print(f"\nLes résultats ont été sauvegardés dans : {excel_path}")
# else:
#     results_df = "No relevant arrêtés found in the document."