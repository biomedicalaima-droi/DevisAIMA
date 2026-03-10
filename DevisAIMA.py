# -*- coding: utf-8 -*-
import streamlit as st
from fpdf import FPDF
from datetime import date
import os
import tempfile
import time
import io
from PIL import Image

# --- CONFIGURATION INITIALE ---
st.set_page_config(layout="wide", page_title="AIMA - Devis & Factures")

# Chemin du logo (doit être présent dans le dossier du projet)
AIMA_LOGO_PATH = "aima_logo.png" 

# --- DONNÉES ---
LOCATIONS = {
    "CAME": {"address": "409 Chemin de Gensanne, 64520 Came", "email": "lehangardaima.came@gmail.com", "phone": "05 59 31 97 53"},
    "OSSERAIN-RIVAREYTE": {"address": "1009 Route des Aügas, 64390 Osserain-Rivareyte", "email": "osserain@assoaima.org", "phone": "05 59 38 17 86"},
    "SALIES-DE-BÉARN": {"address": "154 Chemin du Haou, 64270 Salies-de-Béarn", "email": "salies@assoaima.org", "phone": "05 59 38 03 30"},
    "CASTETNAU-CAMBLONG": {"address": "11 Rue du Bourg, 64190 Castetnau-Camblong", "email": "lehangardaima.castetnau@gmail.com", "phone": "05 59 66 16 90"}
}
LIEUX_ARTICLES = ["Came", "Osserain-Rivareyte", "Salies-de-Béarn", "Castetnau-Camblong"]

data_prices = {
    "Fauteuil à roulette COMFORTO": 0.0, "Bureau": 0.0, "Armoire basse": 0.0,
    "Chaise opérateur Haworth": 0.0, "Table de réunion": 0.0, "Vestiaire Métallique": 0.0,
    "Caisson 3 Tiroirs": 0.0
}

# --- SESSION STATE ---
if 'manual_items_dict' not in st.session_state: st.session_state.manual_items_dict = []
if 'active_catalog' not in st.session_state: st.session_state.active_catalog = []

# --- CLASSE PDF ---
class AIMA_PDF(FPDF):
    def __init__(self, logo_path=None, doc_type="DEVIS"):
        super().__init__()
        self.logo_path = logo_path
        self.doc_type = doc_type

    def header(self):
        if self.logo_path and os.path.exists(self.logo_path):
            self.image(self.logo_path, 10, 10, 38)
        self.set_font('Arial', 'B', 12)
        self.set_text_color(24, 73, 115)
        self.set_xy(100, 10)
        self.cell(100, 8, f"{self.doc_type} D'EQUIPEMENT MOBILIER ET MATERIEL", 0, 1, 'R')
        self.ln(18)

    def footer(self):
        self.set_y(-25)
        self.set_font('Arial', 'I', 7.5)
        self.set_text_color(100, 100, 100)
        self.cell(0, 4, "TVA non applicable, Art. 261-7b du code général des impôts", 0, 1, 'C')
        self.cell(0, 4, "IBAN: FR90 2004 1010 0112 2207 4K02 259 | SIRET: 508 544 715 00057", 0, 1, 'C')
        self.cell(0, 4, f'Page {self.page_no()}', 0, 0, 'R')

    def draw_info_blocks(self, d_num, d_ref, d_date, c_name, c_addr, aima_info, status):
        # Badge Statut
        colors = {"En attente": (255, 193, 7), "Accepté": (40, 167, 69), "Refusé": (220, 53, 69)}
        self.set_xy(150, 25)
        self.set_font('Arial', 'B', 10)
        self.set_fill_color(*colors.get(status, (255, 193, 7)))
        self.set_text_color(255, 255, 255)
        self.cell(50, 8, f"STATUT : {status.upper()}", 0, 1, 'C', True)

        # BLOC ASSOCIATION (EXPÉDITEUR) - CENTRÉ
        y_pos = 40
        self.set_xy(10, y_pos)
        self.set_font('Arial', 'B', 9); self.set_fill_color(51, 139, 140); self.set_text_color(255, 255, 255)
        self.cell(80, 6, "Association AIMA", 1, 1, 'C', True)
        self.set_font('Arial', '', 8); self.set_text_color(0, 0, 0); self.set_x(10)
        self.multi_cell(80, 4, aima_info.encode('latin-1','replace').decode('latin-1'), 1, 'C')
        y_aima = self.get_y()
        
        # BLOC DESTINATAIRE - CENTRÉ
        self.set_xy(115, y_pos)
        self.set_font('Arial', 'B', 9); self.set_fill_color(51, 139, 140); self.set_text_color(255, 255, 255)
        self.cell(85, 6, f"DESTINATAIRE : {c_name}", 1, 1, 'C', True)
        self.set_font('Arial', '', 9); self.set_text_color(0, 0, 0); self.set_x(115)
        self.multi_cell(85, 5, c_addr.encode('latin-1','replace').decode('latin-1'), 1, 'C')
        y_client = self.get_y()
        
        # Infos Document
        self.set_xy(10, y_aima + 3)
        self.set_font('Arial', '', 8.5)
        info_doc = f"{self.doc_type} N°: {d_num}\nRéf: {d_ref}\nDate: {d_date.strftime('%d/%m/%Y')}"
        self.multi_cell(60, 4.5, info_doc, 1, 'L')
        return max(self.get_y(), y_client) + 5

# --- LOGIQUE INTERFACE ---
st.sidebar.header("📝 Paramètres")
doc_type = st.sidebar.selectbox("Document", ["DEVIS", "FACTURE"])
doc_status = st.sidebar.selectbox("Statut", ["En attente", "Accepté", "Refusé"])
selected_loc = st.sidebar.selectbox("Expéditeur", list(LOCATIONS.keys()))

loc_data = LOCATIONS[selected_loc]
aima_pdf_info = f"Le Hangar d'AIMA - {selected_loc}\n{loc_data['address']}\nTél: {loc_data['phone']}\n{loc_data['email']}"

c_name = st.sidebar.text_input("Client", value="ONG-EPSPE")
c_addr = st.sidebar.text_area("Adresse Client", value="Cotonou, Bénin")
d_num = st.sidebar.text_input("N°", value="2026-001")
d_ref = st.sidebar.text_input("Réf", value="AIMA-2026")
d_date = st.sidebar.date_input("Date", value=date.today())
include_adh = st.sidebar.checkbox("Adhésion (1€)", value=True)
liv_total = st.sidebar.number_input("Livraison", value=0.0)

st.title(f"Générateur {doc_type}")

# Gestion des articles (Simplié pour le code complet)
selected_catalog = st.multiselect("Articles", options=list(data_prices.keys()))
items_to_pdf = []
total_global = 0.0

for it in selected_catalog:
    items_to_pdf.append({"Désignation": it, "P.U.": 0.0, "Qté": 1, "Total": 0.0, "Lieu": selected_loc, "Images": []})

# --- GÉNÉRATION ---
if st.button("📄 GÉNÉRER LE PDF"):
    pdf = AIMA_PDF(logo_path=AIMA_LOGO_PATH, doc_type=doc_type)
    pdf.add_page()
    y_table = pdf.draw_info_blocks(d_num, d_ref, d_date, c_name, c_addr, aima_pdf_info, doc_status)
    
    # Configuration colonnes
    w = [50, 20, 10, 20, 60, 30] if doc_type == "DEVIS" else [110, 20, 10, 20, 0, 30]
    headers = ["Designation", "P.U.", "Qte", "Total", "Photos", "Lieu"]

    pdf.set_xy(10, y_table)
    pdf.set_font('Arial', 'B', 8); pdf.set_fill_color(230, 230, 230)
    for i, h in enumerate(headers):
        if w[i] > 0: pdf.cell(w[i], 8, h, 1, 0, 'C', True)
    pdf.ln()

    # Lignes
    pdf.set_font('Arial', '', 8)
    for row in items_to_pdf:
        txt = row['Désignation'].encode('latin-1','replace').decode('latin-1')
        h_row = 10
        curr_y = pdf.get_y()
        # Bordures fixes
        for i in range(len(w)):
            if w[i] > 0: pdf.rect(10 + sum(w[:i]), curr_y, w[i], h_row)
        # Texte
        pdf.set_xy(10, curr_y); pdf.multi_cell(w[0], h_row, txt, 0, 'L')
        pdf.set_xy(10 + w[0], curr_y); pdf.cell(w[1], h_row, "0.00", 0, 0, 'C')
        pdf.cell(w[2], h_row, "1", 0, 0, 'C')
        pdf.cell(w[3], h_row, "0.00", 0, 0, 'C')
        pdf.set_xy(10 + sum(w[:5]), curr_y); pdf.cell(w[5], h_row, row['Lieu'], 0, 1, 'C')

    # BLOC TOTAL ET SIGNATURE (ALIGNÉS)
    pdf.ln(5)
    y_fin = pdf.get_y()
    if y_fin > 220: pdf.add_page(); y_fin = pdf.get_y()
    
    # Totaux
    pdf.set_xy(10, y_fin)
    pdf.set_font('Arial', '', 9)
    pdf.cell(70, 7, f"Adhesion annuelle {d_date.year}", 1, 0, 'L')
    pdf.cell(25, 7, "1.00 EUR", 1, 1, 'R')
    pdf.set_x(10)
    pdf.cell(70, 7, "Livraison au pied du batiment", 1, 0, 'L')
    pdf.cell(25, 7, f"{liv_total:.2f} EUR", 1, 1, 'R')
    pdf.set_x(10); pdf.set_fill_color(51, 139, 140); pdf.set_text_color(255, 255, 255)
    pdf.cell(70, 10, "TOTAL NET", 1, 0, 'C', True)
    pdf.set_text_color(0, 0, 0); pdf.cell(25, 10, f"{liv_total+1:.2f} EUR", 1, 1, 'R')

    # Signature (Centrée comme sur l'image)
    pdf.set_xy(115, y_fin)
    pdf.set_font('Arial', 'B', 9)
    pdf.cell(85, 8, "Signature et cachet:", "LTR", 1, 'C') # Titre centré
    pdf.set_x(115)
    pdf.cell(85, 16, "", "LBR", 1, 'C') # Espace pour le cachet

    pdf_bytes = pdf.output(dest='S')
    st.download_button("💾 Télécharger PDF", pdf_bytes, "doc.pdf", "application/pdf")
