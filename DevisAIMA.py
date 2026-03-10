# -*- coding: utf-8 -*-
import streamlit as st
from fpdf import FPDF
from datetime import date
import os
import tempfile
import time
import io
import sys
from PIL import Image
import pdfplumber

# --- CONFIGURATION DU LOGO ---
# Remplacez par le chemin correct. Si vous déployez sur le web, mettez juste "aima_logo.png"
AIMA_LOGO_PATH = "C:/Users/perso/Desktop/aima_logo.png" 

def get_logo():
    if os.path.exists(AIMA_LOGO_PATH):
        return AIMA_LOGO_PATH
    return None

# --- CONFIGURATION INITIALE ---
st.set_page_config(layout="wide", page_title="AIMA - Devis & Factures")

# --- DONNÉES ET CONSTANTES ---
LOCATIONS = {
    "CAME": {"address": "409 Chemin de Gensanne, 64520 Came", "email": "lehangardaima.came@gmail.com", "phone": "05 59 31 97 53"},
    "OSSERAIN-RIVAREYTE": {"address": "1009 Route des Aügas, 64390 Osserain-Rivareyte", "email": "osserain@assoaima.org", "phone": "05 59 38 17 86"},
    "SALIES-DE-BÉARN": {"address": "154 Chemin du Haou, 64270 Salies-de-Béarn", "email": "salies@assoaima.org", "phone": "05 59 38 03 30"},
    "CASTETNAU-CAMBLONG": {"address": "11 Rue du Bourg, 64190 Castetnau-Camblong", "email": "lehangardaima.castetnau@gmail.com", "phone": "05 59 66 16 90"}
}
LIEUX_ARTICLES = ["Came", "Osserain-Rivareyte", "Salies-de-Béarn", "Castetnau-Camblong"]

# (Catalogue abrégé pour l'exemple, gardez votre liste complète dans votre fichier)
data_prices = {
    "Fauteuil à roulette COMFORTO": 0.0, "Bureau": 0.0, "Table de réunion": 0.0, "Armoire basse": 0.0,
    "Caisson 3 Tiroirs": 0.0, "Vestiaire Métallique": 0.0, "Chaise scolaire T6": 0.0
}

# --- SESSION STATE ---
if 'manual_items_dict' not in st.session_state: st.session_state.manual_items_dict = []
if 'catalog_selector' not in st.session_state: st.session_state.catalog_selector = []

# --- FONCTIONS ---
def import_items_from_pdf(uploaded_pdf):
    try:
        new_items = []
        with pdfplumber.open(uploaded_pdf) as pdf:
            for page in pdf.pages:
                table = page.extract_table()
                if table:
                    for row in table:
                        if not row or "Designation" in str(row[0]): continue
                        try:
                            nom = str(row[0]).strip()
                            prix = float(str(row[1]).replace(' ', '').replace('€', '').replace(',', '.'))
                            new_items.append({"id": str(time.time())+nom, "nom": nom, "prix": prix})
                        except: continue
        return new_items
    except Exception as e:
        st.error(f"Erreur d'importation : {e}")
        return []

# --- CLASSE PDF DESIGN OPTIMISÉ ---
class AIMA_PDF(FPDF):
    def __init__(self, logo_path=None, doc_type="DEVIS"):
        super().__init__()
        self.logo_path = logo_path
        self.doc_type = doc_type

    def header(self):
        if self.logo_path and os.path.exists(self.logo_path): 
            self.image(self.logo_path, 20, 18, 42)
        self.set_font('Arial', 'B', 14); self.set_text_color(24, 73, 115)
        self.set_xy(100, 10)
        self.cell(100, 8, f"{self.doc_type} D'EQUIPEMENT MOBILIER ET MATERIEL", 0, 1, 'R')
        self.ln(20)

    def footer(self):
        self.set_y(-30); self.set_font('Arial', 'I', 7.5); self.set_text_color(100, 100, 100)
        self.cell(0, 4, "TVA non applicable, Art. 261-7b du code général des impôts", 0, 1, 'C')
        self.cell(0, 4, "IBAN : FR90 2004 1010 0112 2207 4K02 259 | SIRET : 508 544 715 00057", 0, 1, 'C')
        self.cell(0, 4, f'Page {self.page_no()}', 0, 0, 'R')

    def draw_first_page_info(self, d_num, d_ref, d_date, c_name, c_addr, aima_info, status):
        # Statut Box
        colors = {"En attente": (255, 193, 7), "Accepté": (40, 167, 69), "Refusé": (220, 53, 69)}
        self.set_xy(150, 28); self.set_font('Arial', 'B', 10)
        self.set_fill_color(*colors.get(status, (128,128,128))); self.set_text_color(255,255,255)
        self.cell(50, 8, f"STATUT : {status.upper()}", 0, 1, 'C', True)
        
        # Infos Blocs
        y_start = 40
        self.set_fill_color(51, 139, 140); self.set_text_color(255, 255, 255)
        self.set_xy(10, y_start); self.cell(80, 7, "Association AIMA", 1, 1, 'C', True)
        self.set_text_color(0, 0, 0); self.set_font('Arial', '', 8); self.set_x(10)
        self.multi_cell(80, 4, aima_info.encode('latin-1', 'replace').decode('latin-1'), 1, 'C')
        
        self.set_xy(120, y_start); self.set_fill_color(51, 139, 140); self.set_text_color(255, 255, 255)
        self.cell(80, 7, f"DESTINATAIRE : {c_name.upper()}", 1, 1, 'C', True)
        self.set_text_color(0, 0, 0); self.set_font('Arial', '', 9); self.set_x(120)
        self.multi_cell(80, 5, c_addr.encode('latin-1', 'replace').decode('latin-1'), 1, 'C')
        
        self.set_xy(10, self.get_y() + 5); self.set_font('Arial', '', 9)
        self.multi_cell(60, 5, f"{self.doc_type} N°: {d_num}\nRéf: {d_ref}\nDate: {d_date.strftime('%d/%m/%Y')}", 1, 'L')
        return self.get_y() + 5

# --- INTERFACE STREAMLIT ---
logo_path = get_logo()
col_logo, col_titre = st.columns([1, 4])
with col_logo:
    if logo_path: st.image(logo_path, width=150)
with col_titre:
    st.title(f"Générateur AIMA - {doc_type if 'doc_type' in locals() else ''}")

# Sidebar
st.sidebar.header("📝 Paramètres")
doc_type = st.sidebar.selectbox("Type", ["DEVIS", "FACTURE"])
doc_status = st.sidebar.selectbox("État", ["En attente", "Accepté", "Refusé"])
selected_loc = st.sidebar.selectbox("Lieu d'expédition", options=list(LOCATIONS.keys()))

loc_data = LOCATIONS[selected_loc]
aima_pdf_info = f"Le Hangar d'AIMA - {selected_loc}\n{loc_data['address']}\nTél : {loc_data['phone']}\nMail : {loc_data['email']}"

c_name = st.sidebar.text_input("Client", "ONG- EPSPE")
c_addr = st.sidebar.text_area("Adresse Client", "Cotonou, Bénin")
d_num = st.sidebar.text_input("N° Document", "2026-001")
d_ref = st.sidebar.text_input("Référence", "AIMA-2026")
d_date = st.sidebar.date_input("Date", date.today())
include_adh = st.sidebar.checkbox("Adhésion (1€)", True)
liv_total = st.sidebar.number_input("Frais de livraison (€)", 0.0)

# Sélection Articles
selected_catalog = st.multiselect("📦 Catalogue :", options=sorted(data_prices.keys()), key="catalog_selector")
items_to_pdf = []
total_global = 0.0

def render_row(label, price, key):
    with st.container(border=True):
        st.markdown(f"**{label}**")
        c1, c2, c3, c4 = st.columns([1, 1, 1, 2])
        p = c1.number_input("P.U.", value=float(price), key=f"p_{key}")
        q = c2.number_input("Qté", min_value=1, key=f"q_{key}")
        l = c3.selectbox("Lieu", LIEUX_ARTICLES, key=f"l_{key}")
        imgs = c4.file_uploader("Photos (max 3)", accept_multiple_files=True, key=f"i_{key}")
        return {"Désignation": label, "P.U.": p, "Qté": q, "Total": p*q, "Lieu": l, "Images": imgs[:3] if imgs else []}

for i, item in enumerate(selected_catalog):
    res = render_row(item, data_prices.get(item, 0), f"cat_{i}")
    items_to_pdf.append(res); total_global += res['Total']

# Articles Manuels
st.subheader("➕ Articles Personnalisés")
col_m1, col_m2, col_m3 = st.columns([3, 1, 1])
m_nom = col_m1.text_input("Désignation")
m_prix = col_m2.number_input("Prix", 0.0)
if col_m3.button("Ajouter"):
    st.session_state.manual_items_dict.append({"nom": m_nom, "prix": m_prix})
    st.rerun()

for i, m in enumerate(st.session_state.manual_items_dict):
    res = render_row(m['nom'], m['prix'], f"man_{i}")
    items_to_pdf.append(res); total_global += res['Total']

# Total
grand_total = total_global + (1.0 if include_adh else 0.0) + liv_total
st.divider()
st.write(f"### TOTAL NET : {grand_total:,.2f} EUR")

# --- GÉNÉRATION PDF FINAL ---
if items_to_pdf and st.button(f"📄 GÉNÉRER LE PDF {doc_type}"):
    pdf = AIMA_PDF(logo_path=logo_path, doc_type=doc_type)
    pdf.add_page()
    y_pos = pdf.draw_first_page_info(d_num, d_ref, d_date, c_name, c_addr, aima_pdf_info, doc_status)
    
    # Configuration colonnes (Design propre)
    cols_w = [45, 17, 10, 18, 70, 30] if doc_type == "DEVIS" else [115, 17, 10, 18, 0, 30]
    headers = ["Designation", "P.U.", "Qte", "Total", "Photos", "Lieu"]

    pdf.set_font('Arial', 'B', 8); pdf.set_fill_color(220, 220, 220); pdf.set_xy(10, y_pos)
    for i, h in enumerate(headers):
        if cols_w[i] > 0: pdf.cell(cols_w[i], 8, h, 1, 0, 'C', True)
    pdf.ln()

    # Lignes d'articles
    pdf.set_font("Arial", '', 8)
    for row in items_to_pdf:
        nom_p = row['Désignation'].encode('latin-1', 'replace').decode('latin-1')
        
        # Calcul de la hauteur de ligne dynamique
        nb_lines = len(pdf.multi_cell(cols_w[0]-2, 4, nom_p, split_only=True))
        min_h = 32 if (doc_type == "DEVIS" and row['Images']) else 10
        h_row = max(nb_lines * 4 + 4, min_h)
        
        if pdf.get_y() + h_row > 240: pdf.add_page()
        y_c = pdf.get_y()
        
        # Cellule Désignation (Multi-ligne)
        pdf.rect(10, y_c, cols_w[0], h_row)
        pdf.set_xy(10, y_c + (h_row - (nb_lines * 4)) / 2)
        pdf.multi_cell(cols_w[0], 4, nom_p, 0, 'L')
        
        # Autres Cellules
        pdf.set_xy(10 + cols_w[0], y_c)
        pdf.cell(cols_w[1], h_row, f"{row['P.U.']:,.2f}", 1, 0, 'C')
        pdf.cell(cols_w[2], h_row, str(row['Qté']), 1, 0, 'C')
        pdf.cell(cols_w[3], h_row, f"{row['Total']:,.2f}", 1, 0, 'C')
        
        # Photos
        if doc_type == "DEVIS":
            img_x_start = pdf.get_x()
            pdf.cell(cols_w[4], h_row, "", 1, 0) 
            if row['Images']:
                for idx, img_file in enumerate(row['Images']):
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
                        with Image.open(img_file) as pimg:
                            if pimg.mode in ("RGBA", "P"): pimg = pimg.convert("RGB")
                            pimg.thumbnail((400, 400))
                            pimg.save(tmp.name, "JPEG")
                        pdf.image(tmp.name, img_x_start + 2 + (idx * 22), y_c + 2, w=20, h=h_row - 4)
                    if os.path.exists(tmp.name): os.remove(tmp.name)
        
        pdf.cell(cols_w[5], h_row, row['Lieu'].encode('latin-1', 'replace').decode('latin-1'), 1, 1, 'C')

    # Bloc Totaux et Signature
    pdf.ln(10)
    if pdf.get_y() > 210: pdf.add_page()
    y_final = pdf.get_y()
    
    pdf.set_font("Arial", '', 9); pdf.set_xy(10, y_final)
    pdf.cell(75, 8, f"Adhesion annuelle {d_date.year}", 1, 0, 'L')
    pdf.cell(25, 8, "1.00 EUR" if include_adh else "0.00 EUR", 1, 1, 'R')
    pdf.set_x(10)
    pdf.cell(75, 8, "Livraison au pied du batiment", 1, 0, 'L')
    pdf.cell(25, 8, f"{liv_total:,.2f} EUR", 1, 1, 'R')
    pdf.set_x(10); pdf.set_fill_color(51, 139, 140); pdf.set_text_color(255, 255, 255); pdf.set_font("Arial", 'B', 10)
    pdf.cell(75, 10, "TOTAL NET", 1, 0, 'C', True)
    pdf.set_text_color(0, 0, 0); pdf.cell(25, 10, f"{grand_total:,.2f} EUR", 1, 1, 'R')

    pdf.set_xy(115, y_final); pdf.set_font("Arial", 'B', 9)
    pdf.cell(85, 8, "Signature et cachet :", 1, 1, 'L')
    pdf.set_x(115); pdf.cell(85, 20, "", 1, 1)

    # Sortie Binaire
    pdf_data = pdf.output(dest='S')
    if isinstance(pdf_data, str): pdf_data = pdf_data.encode('latin-1')
    
    st.download_button(f"💾 Télécharger {doc_type} PDF", pdf_data, f"{doc_type}_{d_num}.pdf", "application/pdf")
