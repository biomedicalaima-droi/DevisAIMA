# -*- coding: utf-8 -*-
import streamlit as st
from fpdf import FPDF
from datetime import date
import os
import tempfile
import time
import io
from PIL import Image

# --- CONFIGURATION DE LA CLASSE PDF ---
class AIMA_PDF(FPDF):
    def __init__(self, logo_path=None, doc_type="DEVIS"):
        super().__init__()
        self.logo_path = logo_path
        self.doc_type = doc_type

    def header(self):
        # Affichage du logo en haut à gauche
        if self.logo_path and os.path.exists(self.logo_path):
            try:
                self.image(self.logo_path, 10, 10, 38)
            except:
                pass
        
        self.set_font('Arial', 'B', 12)
        self.set_text_color(24, 73, 115)
        self.set_xy(100, 10)
        title = f"{self.doc_type} D'EQUIPEMENT MOBILIER ET MATERIEL"
        self.cell(100, 8, title.encode('latin-1', 'replace').decode('latin-1'), 0, 1, 'R')
        self.ln(20)

    def footer(self):
        self.set_y(-25)
        self.set_font('Arial', 'I', 7.5)
        self.set_text_color(100, 100, 100)
        footer_txt = "TVA non applicable, Art. 261-7b du code général des impôts"
        self.cell(0, 4, footer_txt.encode('latin-1', 'replace').decode('latin-1'), 0, 1, 'C')
        self.cell(0, 4, "IBAN: FR90 2004 1010 0112 2207 4K02 259 | SIRET: 508 544 715 00057", 0, 1, 'C')
        self.cell(0, 4, f'Page {self.page_no()}', 0, 0, 'R')

    def draw_info_blocks(self, d_num, d_ref, d_date, c_name, c_addr, aima_info, status):
        # Badge Statut (Rectangle Orange/Jaune en haut à droite)
        self.set_xy(150, 25)
        self.set_font('Arial', 'B', 10)
        self.set_fill_color(255, 193, 7)
        self.set_text_color(255, 255, 255)
        self.cell(50, 8, f"STATUT : {status.upper()}", 0, 1, 'C', True)

        # Blocs Adresses (Texte centré horizontalement)
        y_pos = 40
        # GAUCHE : Association AIMA
        self.set_xy(10, y_pos)
        self.set_font('Arial', 'B', 9); self.set_fill_color(51, 139, 140); self.set_text_color(255, 255, 255)
        self.cell(80, 7, "Association AIMA", 1, 1, 'C', True)
        self.set_font('Arial', '', 8); self.set_text_color(0, 0, 0); self.set_x(10)
        self.multi_cell(80, 4, aima_info.encode('latin-1', 'replace').decode('latin-1'), 1, 'C')
        y_aima = self.get_y()
        
        # DROITE : Destinataire
        self.set_xy(115, y_pos)
        self.set_font('Arial', 'B', 9); self.set_fill_color(51, 139, 140); self.set_text_color(255, 255, 255)
        self.cell(85, 7, f"DESTINATAIRE : {c_name.upper()}", 1, 1, 'C', True)
        self.set_font('Arial', '', 9); self.set_text_color(0, 0, 0); self.set_x(115)
        self.multi_cell(85, 5, c_addr.encode('latin-1', 'replace').decode('latin-1'), 1, 'C')
        y_client = self.get_y()
        
        # Bloc Infos Document (N°, Réf, Date)
        self.set_xy(10, y_aima + 3)
        self.set_font('Arial', '', 8.5)
        info_doc = f"{self.doc_type} N°: {d_num}\nRef: {d_ref}\nDate: {d_date.strftime('%d/%m/%Y')}"
        self.multi_cell(60, 4.5, info_doc.encode('latin-1', 'replace').decode('latin-1'), 1, 'L')
        return max(self.get_y(), y_client) + 5

# --- LOGIQUE STREAMLIT ---
st.set_page_config(layout="wide", page_title="AIMA - Générateur Pro")

# Données de base
LOCATIONS = {
    "CAME": {"address": "409 Chemin de Gensanne, 64520 Came", "email": "lehangardaima.came@gmail.com", "phone": "05 59 31 97 53"},
    "OSSERAIN-RIVAREYTE": {"address": "1009 Route des Aügas, 64390 Osserain-Rivareyte", "email": "osserain@assoaima.org", "phone": "05 59 38 17 86"},
}

# Initialisation Session State
if 'items' not in st.session_state:
    st.session_state.items = []

# Sidebar
st.sidebar.header("Paramètres")
doc_type = st.sidebar.selectbox("Document", ["DEVIS", "FACTURE"])
doc_status = st.sidebar.selectbox("Statut", ["En attente", "Accepté", "Refusé"])
loc_key = st.sidebar.selectbox("Lieu d'expédition", list(LOCATIONS.keys()))
c_name = st.sidebar.text_input("Client", "ONG-EPSPE")
c_addr = st.sidebar.text_area("Adresse Client", "Cotonou, Bénin")
d_num = st.sidebar.text_input("Numéro", "2026-001")
d_ref = st.sidebar.text_input("Référence", "AIMA-2026")
d_date = st.sidebar.date_input("Date", date.today())
liv_total = st.sidebar.number_input("Frais de livraison (€)", 0.0)

# Formulaire Articles
st.subheader("Ajouter des articles")
with st.form("item_form"):
    col1, col2, col3 = st.columns([3, 1, 1])
    name = col1.text_input("Désignation")
    pu = col2.number_input("P.U. (€)", min_value=0.0)
    qty = col3.number_input("Qté", min_value=1)
    if st.form_submit_button("Ajouter à la liste"):
        st.session_state.items.append({"nom": name, "pu": pu, "qty": qty, "total": pu*qty})

# Affichage des articles ajoutés
if st.session_state.items:
    st.write("### Articles sélectionnés")
    st.table(st.session_state.items)
    if st.button("Effacer la liste"):
        st.session_state.items = []

# --- GÉNÉRATION PDF ---
if st.button("📄 GÉNÉRER LE PDF"):
    if not st.session_state.items:
        st.error("Ajoutez au moins un article.")
    else:
        pdf = AIMA_PDF(logo_path="aima_logo.png", doc_type=doc_type)
        pdf.add_page()
        
        loc = LOCATIONS[loc_key]
        aima_info = f"Le Hangar d'AIMA - {loc_key}\n{loc['address']}\nTél: {loc['phone']}\n{loc['email']}"
        
        y_table = pdf.draw_info_blocks(d_num, d_ref, d_date, c_name, c_addr, aima_info, doc_status)
        
        # En-tête Tableau
        w = [110, 20, 10, 20, 30]
        headers = ["Designation", "P.U.", "Qte", "Total", "Lieu"]
        pdf.set_xy(10, y_table)
        pdf.set_font('Arial', 'B', 8); pdf.set_fill_color(230, 230, 230); pdf.set_text_color(0)
        for i, h in enumerate(headers):
            pdf.cell(w[i], 8, h, 1, 0, 'C', True)
        pdf.ln()

        # Contenu Tableau
        pdf.set_font('Arial', '', 8)
        total_items = 0
        for item in st.session_state.items:
            h_line = 8
            curr_y = pdf.get_y()
            # Bordures
            for i in range(len(w)):
                pdf.rect(10 + sum(w[:i]), curr_y, w[i], h_line)
            
            pdf.set_xy(10, curr_y)
            pdf.cell(w[0], h_line, item['nom'].encode('latin-1', 'replace').decode('latin-1'), 0, 0, 'L')
            pdf.cell(w[1], h_line, f"{item['pu']:.2f}", 0, 0, 'C')
            pdf.cell(w[2], h_line, str(item['qty']), 0, 0, 'C')
            pdf.cell(w[3], h_line, f"{item['total']:.2f}", 0, 0, 'C')
            pdf.cell(w[4], h_line, loc_key, 0, 1, 'C')
            total_items += item['total']

        # Totaux et Signature
        pdf.ln(10)
        y_fin = pdf.get_y()
        if y_fin > 230: pdf.add_page(); y_fin = pdf.get_y()
        
        # Bloc Total
        grand_total = total_items + 1.0 + liv_total # +1 pour adhésion
        pdf.set_xy(10, y_fin)
        pdf.set_font('Arial', '', 9)
        pdf.cell(70, 7, f"Adhesion annuelle {d_date.year}", 1, 0)
        pdf.cell(25, 7, "1.00 EUR", 1, 1, 'R')
        pdf.set_x(10)
        pdf.cell(70, 7, "Livraison au pied du batiment", 1, 0)
        pdf.cell(25, 7, f"{liv_total:.2f} EUR", 1, 1, 'R')
        pdf.set_x(10); pdf.set_font('Arial', 'B', 10); pdf.set_fill_color(51, 139, 140); pdf.set_text_color(255)
        pdf.cell(70, 10, "TOTAL NET", 1, 0, 'C', True)
        pdf.set_text_color(0); pdf.cell(25, 10, f"{grand_total:.2f} EUR", 1, 1, 'R')

        # Bloc Signature (CONFORME À L'IMAGE)
        pdf.set_xy(115, y_fin)
        pdf.set_font('Arial', 'B', 9)
        pdf.cell(85, 8, "Signature et cachet :", "LTR", 1, 'C') # Centré horizontalement
        pdf.set_x(115)
        pdf.cell(85, 20, "", "LBR", 1, 'C') # Espace vide pour le tampon

        # Sortie Sécurisée
        pdf_bytes = pdf.output(dest='S')
        if isinstance(pdf_bytes, str):
            pdf_bytes = pdf_bytes.encode('latin-1')
            
        st.download_button(
            label="💾 Télécharger le PDF",
            data=pdf_bytes,
            file_name=f"{doc_type}_{d_num}.pdf",
            mime="application/pdf"
        )
