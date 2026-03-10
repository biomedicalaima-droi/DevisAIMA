# -*- coding: utf-8 -*-
import streamlit as st
from fpdf import FPDF
from datetime import date
import os
import tempfile
import time
import io
from PIL import Image
import pdfplumber

# --- CONFIGURATION DU LOGO ---
# Assurez-vous que le fichier est bien à la racine de votre projet Streamlit
AIMA_LOGO_PATH = "aima_logo.png" 

# --- CONFIGURATION INITIALE ---
st.set_page_config(layout="wide", page_title="AIMA - Devis & Factures")

# --- DONNÉES ---
LOCATIONS = {
    "CAME": {"address": "409 Chemin de Gensanne, 64520 Came", "email": "lehangardaima.came@gmail.com", "phone": "05 59 31 97 53"},
    "OSSERAIN-RIVAREYTE": {"address": "1009 Route des Aügas, 64390 Osserain-Rivareyte", "email": "osserain@assoaima.org", "phone": "05 59 38 17 86"},
    "SALIES-DE-BÉARN": {"address": "154 Chemin du Haou, 64270 Salies-de-Béarn", "email": "salies@assoaima.org", "phone": "05 59 38 03 30"},
    "CASTETNAU-CAMBLONG": {"address": "11 Rue du Bourg, 64190 Castetnau-Camblong", "email": "lehangardaima.castetnau@gmail.com", "phone": "05 59 66 16 90"}
}
LIEUX_ARTICLES = ["Came", "Osserain-Rivareyte", "Salies-de-Béarn", "Castetnau-Camblong"]

# --- CLASSE PDF (LOGIQUE DE TABLEAU FIXE) ---
class AIMA_PDF(FPDF):
    def __init__(self, logo_path=None, doc_type="DEVIS"):
        super().__init__()
        self.logo_path = logo_path
        self.doc_type = doc_type

    def header(self):
        if self.logo_path and os.path.exists(self.logo_path):
            self.image(self.logo_path, 10, 10, 35)
        self.set_font('Arial', 'B', 12)
        self.set_text_color(24, 73, 115)
        self.set_xy(100, 10)
        self.cell(100, 8, f"{self.doc_type} D'EQUIPEMENT MOBILIER ET MATERIEL", 0, 1, 'R')
        self.ln(15)

    def footer(self):
        self.set_y(-25)
        self.set_font('Arial', 'I', 7)
        self.set_text_color(100, 100, 100)
        self.cell(0, 4, "TVA non applicable, Art. 261-7b du code général des impôts", 0, 1, 'C')
        self.cell(0, 4, "IBAN: FR90 2004 1010 0112 2207 4K02 259 | SIRET: 508 544 715 00057", 0, 1, 'C')
        self.cell(0, 4, f'Page {self.page_no()}', 0, 0, 'R')

    def draw_info_blocks(self, d_num, d_ref, d_date, c_name, c_addr, aima_info, status):
        # Statut
        colors = {"En attente": (255, 193, 7), "Accepté": (40, 167, 69), "Refusé": (220, 53, 69)}
        self.set_xy(150, 25)
        self.set_font('Arial', 'B', 10)
        self.set_fill_color(*colors.get(status, (128,128,128)))
        self.set_text_color(255, 255, 255)
        self.cell(50, 8, f"STATUT : {status.upper()}", 0, 1, 'C', True)

        # Blocs Expéditeur / Destinataire
        self.set_text_color(0, 0, 0)
        y_pos = 40
        # AIMA
        self.set_xy(10, y_pos)
        self.set_font('Arial', 'B', 9); self.set_fill_color(51, 139, 140); self.set_text_color(255,255,255)
        self.cell(80, 6, "Association AIMA", 1, 1, 'L', True)
        self.set_font('Arial', '', 8); self.set_text_color(0,0,0)
        self.set_x(10); self.multi_cell(80, 4, aima_info.encode('latin-1','replace').decode('latin-1'), 1, 'L')
        
        # CLIENT
        self.set_xy(110, y_pos)
        self.set_font('Arial', 'B', 9); self.set_fill_color(51, 139, 140); self.set_text_color(255,255,255)
        self.cell(90, 6, f"DESTINATAIRE : {c_name}", 1, 1, 'L', True)
        self.set_font('Arial', '', 9); self.set_text_color(0,0,0)
        self.set_x(110); self.multi_cell(90, 5, c_addr.encode('latin-1','replace').decode('latin-1'), 1, 'L')
        
        # Infos Document
        curr_y = self.get_y() + 5
        self.set_xy(10, curr_y)
        self.set_font('Arial', '', 9)
        info_doc = f"{self.doc_type} N°: {d_num}\nRéf: {d_ref}\nDate: {d_date.strftime('%d/%m/%Y')}"
        self.multi_cell(60, 5, info_doc, 1, 'L')
        return self.get_y() + 5

# --- INTERFACE ---
st.sidebar.header("⚙️ Paramètres")
doc_type = st.sidebar.selectbox("Document", ["DEVIS", "FACTURE"])
doc_status = st.sidebar.selectbox("Statut", ["En attente", "Accepté", "Refusé"])
selected_loc = st.sidebar.selectbox("Expéditeur", list(LOCATIONS.keys()))

# Affichage du logo sur Streamlit
if os.path.exists(AIMA_LOGO_PATH):
    st.image(AIMA_LOGO_PATH, width=150)
else:
    st.warning("⚠️ Fichier 'aima_logo.png' non trouvé à la racine.")

# ... (Ici gardez votre logique de saisie client et sélection d'articles habituelle) ...

# --- LOGIQUE DE GÉNÉRATION (TABLEAU SANS MÉLANGE) ---
if st.button(f"📄 GÉNÉRER LE PDF"):
    pdf = AIMA_PDF(logo_path=AIMA_LOGO_PATH, doc_type=doc_type)
    pdf.add_page()
    
    # Entête
    y_table = pdf.draw_info_blocks(d_num, d_ref, d_date, c_name, c_addr, aima_info, doc_status)
    
    # Colonnes : Largeurs fixes
    # [Designation(1), PU(2), Qte(3), Total(4), Photos(5), Lieu(6)]
    if doc_type == "DEVIS":
        w = [50, 20, 10, 20, 60, 30]
        headers = ["Désignation", "P.U.", "Qté", "Total", "Photos", "Lieu"]
    else:
        w = [110, 20, 10, 20, 0, 30] # Pas de colonne photos pour facture
        headers = ["Désignation", "P.U.", "Qté", "Total", "", "Lieu"]

    # Header du tableau
    pdf.set_xy(10, y_table)
    pdf.set_font('Arial', 'B', 8); pdf.set_fill_color(230, 230, 230)
    for i, h in enumerate(headers):
        if w[i] > 0: pdf.cell(w[i], 8, h, 1, 0, 'C', True)
    pdf.ln()

    # Corps du tableau
    pdf.set_font('Arial', '', 8)
    for row in items_to_pdf:
        # 1. Calculer la hauteur nécessaire pour cette ligne
        text = row['Désignation'].encode('latin-1','replace').decode('latin-1')
        nb_lines = len(pdf.multi_cell(w[0], 5, text, split_only=True))
        h_row = max(nb_lines * 5, 30 if (doc_type == "DEVIS" and row['Images']) else 10)
        
        # Saut de page si besoin
        if pdf.get_y() + h_row > 260:
            pdf.add_page()
            # Redessiner le header sur la nouvelle page
            pdf.set_font('Arial', 'B', 8); pdf.set_fill_color(230, 230, 230)
            for i, h in enumerate(headers):
                if w[i] > 0: pdf.cell(w[i], 8, h, 1, 0, 'C', True)
            pdf.ln()

        start_x = 10
        start_y = pdf.get_y()

        # Dessiner les bordures de la ligne (rectangles) pour éviter les trous
        for i in range(len(w)):
            if w[i] > 0:
                pdf.rect(start_x + sum(w[:i]), start_y, w[i], h_row)

        # Remplir les données
        # Col 1: Désignation
        pdf.set_xy(start_x, start_y)
        pdf.multi_cell(w[0], 5, text, 0, 'L')

        # Col 2, 3, 4: Prix, Qté, Total
        pdf.set_xy(start_x + w[0], start_y)
        pdf.cell(w[1], h_row, f"{row['P.U.']:.2f}", 0, 0, 'C')
        pdf.cell(w[2], h_row, str(row['Qté']), 0, 0, 'C')
        pdf.cell(w[3], h_row, f"{row['Total']:.2f}", 0, 0, 'C')

        # Col 5: Photos (Uniquement Devis)
        if doc_type == "DEVIS" and w[4] > 0:
            img_x = pdf.get_x()
            if row['Images']:
                for idx, img in enumerate(row['Images'][:3]):
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
                        with Image.open(img) as pimg:
                            pimg.convert("RGB").save(tmp.name, "JPEG")
                        pdf.image(tmp.name, img_x + 2 + (idx * 19), start_y + 2, h=h_row - 4)
                    os.unlink(tmp.name)

        # Col 6: Lieu
        pdf.set_xy(start_x + sum(w[:5]), start_y)
        pdf.cell(w[5], h_row, row['Lieu'], 0, 1, 'C')

    # --- TOTAUX ET SIGNATURE ---
    pdf.ln(5)
    if pdf.get_y() > 220: pdf.add_page()
    
    final_y = pdf.get_y()
    pdf.set_font('Arial', 'B', 9)
    pdf.set_xy(10, final_y)
    pdf.cell(70, 7, f"Adhésion annuelle: {'1.00' if include_adh else '0.00'} EUR", 1, 1)
    pdf.cell(70, 7, f"Livraison: {liv_total:.2f} EUR", 1, 1)
    pdf.set_fill_color(51, 139, 140); pdf.set_text_color(255, 255, 255)
    pdf.cell(70, 10, f"TOTAL NET: {grand_total:.2f} EUR", 1, 0, 'C', True)
    
    # Signature
    pdf.set_xy(110, final_y)
    pdf.set_text_color(0,0,0)
    pdf.cell(90, 24, "Signature et cachet:", 1, 0, 'L')

    # Sortie
    pdf_bytes = pdf.output(dest='S')
    if isinstance(pdf_bytes, str): pdf_bytes = pdf_bytes.encode('latin-1')
    
    st.download_button("💾 Télécharger le PDF", pdf_bytes, f"{doc_type}_{d_num}.pdf", "application/pdf")
