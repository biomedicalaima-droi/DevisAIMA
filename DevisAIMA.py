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

# --- CONFIGURATION INITIALE ---
AIMA_LOGO_PATH = "aima_logo.png" # Placez l'image dans le même dossier sur GitHub

st.set_page_config(layout="wide", page_title="AIMA - Devis & Factures")

# --- DONNÉES ET CONSTANTES ---
LOCATIONS = {
    "CAME": {"address": "409 Chemin de Gensanne, 64520 Came", "email": "lehangardaima.came@gmail.com", "phone": "05 59 31 97 53"},
    "OSSERAIN-RIVAREYTE": {"address": "1009 Route des Aügas, 64390 Osserain-Rivareyte", "email": "osserain@assoaima.org", "phone": "05 59 38 17 86"},
    "SALIES-DE-BÉARN": {"address": "154 Chemin du Haou, 64270 Salies-de-Béarn", "email": "salies@assoaima.org", "phone": "05 59 38 03 30"},
    "CASTETNAU-CAMBLONG": {"address": "11 Rue du Bourg, 64190 Castetnau-Camblong", "email": "lehangardaima.castetnau@gmail.com", "phone": "05 59 66 16 90"}
}
LIEUX_ARTICLES = ["Came", "Osserain-Rivareyte", "Salies-de-Béarn", "Castetnau-Camblong"]

data_prices = {
    "Bureau droit (120x80cm)": 40.0, "Bureau d'angle": 60.0, "Chaise de bureau à roulettes": 25.0,
    "Fauteuil de direction": 45.0, "Armoire métallique haute": 50.0, "Armoire métallique basse": 30.0,
    "Caisson de bureau (3 tiroirs)": 15.0, "Table de réunion (6 pers.)": 80.0, "Étagère de stockage": 20.0,
    "Lot de chaises empilables (x4)": 40.0, "Canapé d'accueil (2 places)": 70.0, "Tableau blanc / Paperboard": 10.0
}

# --- SESSION STATE ---
if 'manual_items_dict' not in st.session_state: st.session_state.manual_items_dict = []
if 'active_catalog' not in st.session_state: st.session_state.active_catalog = []

# --- FONCTION IMPORT PDF ---
def import_items_from_pdf(uploaded_pdf):
    try:
        new_items = []
        with pdfplumber.open(uploaded_pdf) as pdf:
            for page in pdf.pages:
                table = page.extract_table()
                if table:
                    for row in table:
                        if not row or "Designation" in str(row[0]) or "TOTAL" in str(row[0]): continue
                        try:
                            nom = str(row[0]).strip()
                            prix_str = str(row[1]).replace(' ', '').replace('€', '').replace(',', '.')
                            new_items.append({"id": str(time.time())+nom, "nom": nom, "prix": float(prix_str)})
                        except: continue
        return new_items
    except Exception as e:
        st.error(f"Erreur d'importation : {e}")
        return []

# --- CLASSE PDF ---
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
        self.cell(0, 4, "Association AIMA - SIRET : 508 544 715 00057", 0, 1, 'C')
        self.set_font('Arial', '', 7); self.cell(0, 4, f'Page {self.page_no()}', 0, 0, 'R')

    def draw_first_page_info(self, doc_num, ref_text, selected_date, client_name, client_address, aima_info, status):
        status_colors = {"En attente": (255, 193, 7), "Accepté": (40, 167, 69), "Refusé": (220, 53, 69)}
        c = status_colors.get(status, (128, 128, 128))
        self.set_xy(150, 28); self.set_font('Arial', 'B', 10); self.set_fill_color(*c); self.set_text_color(255, 255, 255)
        self.cell(50, 8, f"STATUT : {status.upper()}", 0, 1, 'C', True)
        
        self.set_xy(10, 40); self.set_fill_color(51, 139, 140); self.set_text_color(255, 255, 255)
        self.cell(80, 7, "Association AIMA", 1, 1, 'C', True)
        self.set_text_color(0, 0, 0); self.set_font('Arial', '', 8); self.set_x(10)
        self.multi_cell(80, 4, aima_info.encode('latin-1', 'replace').decode('latin-1'), 1, 'C')
        
        self.set_xy(120, 40); self.set_fill_color(51, 139, 140); self.set_text_color(255, 255, 255)
        self.cell(80, 7, f"DESTINATAIRE : {client_name.upper()}", 1, 1, 'C', True)
        self.set_text_color(0, 0, 0); self.set_font('Arial', '', 9); self.set_x(120)
        self.multi_cell(80, 5, client_address.encode('latin-1', 'replace').decode('latin-1'), 1, 'C')
        
        self.set_xy(10, self.get_y() + 2); self.set_font('Arial', '', 8.5)
        self.multi_cell(55, 4.2, f"{self.doc_type} N°: {doc_num}\nRéf: {ref_text}\nDate: {selected_date.strftime('%d/%m/%Y')}", 1, 'L')
        return self.get_y() + 5

# --- INTERFACE ---
st.sidebar.header("📝 Paramètres")
doc_type = st.sidebar.selectbox("Type", ["DEVIS", "FACTURE"])
doc_status = st.sidebar.selectbox("État", ["En attente", "Accepté", "Refusé"])
selected_loc_name = st.sidebar.selectbox("Expéditeur", options=list(LOCATIONS.keys()))

# Import
up_file = st.file_uploader("📥 Importer un ancien PDF AIMA", type="pdf")
if up_file and st.button("Scanner le PDF"):
    st.session_state.manual_items_dict.extend(import_items_from_pdf(up_file))
    st.success("Articles ajoutés !")

# Devis Builder
st.title(f"Générateur de {doc_type}")
loc_data = LOCATIONS[selected_loc_name]
aima_pdf_info = f"AIMA - {selected_loc_name}\n{loc_data['address']}\nTél : {loc_data['phone']}\nSIRET: 508 544 715 00057"

c_name = st.sidebar.text_input("Client", "ONG- EPSPE")
c_addr = st.sidebar.text_area("Adresse", "Cotonou, Bénin")
d_num = st.sidebar.text_input("N°", f"2026-FAC-001")
d_ref = st.sidebar.text_input("Référence", "AIMA-2026")
d_date = st.sidebar.date_input("Date", date.today())
include_adh = st.sidebar.checkbox("Adhésion (1€)", True)
liv_total = st.sidebar.number_input("Livraison (€)", 0.0)

selected_catalog = st.multiselect("📦 Catalogue :", options=sorted(list(data_prices.keys())))

items_to_pdf = []
total_items = 0.0

# Affichage Articles
for name in selected_catalog:
    with st.container(border=True):
        st.write(f"**{name}**")
        c1, c2, c3, c4 = st.columns([1, 1, 1, 2])
        p = c1.number_input("P.U.", value=float(data_prices.get(name,0)), key=f"p_{name}")
        q = c2.number_input("Qté", min_value=1, key=f"q_{name}")
        l = c3.selectbox("Lieu", LIEUX_ARTICLES, key=f"l_{name}")
        imgs = c4.file_uploader("Photos", accept_multiple_files=True, key=f"i_{name}")
        items_to_pdf.append({"Désignation": name, "P.U.": p, "Qté": q, "Total": p*q, "Lieu": l, "Images": imgs[:3] if imgs else []})
        total_items += p*q

for i, m in enumerate(st.session_state.manual_items_dict):
    with st.container(border=True):
        st.write(f"**{m['nom']}** (Manuel)")
        c1, c2, c3, c4 = st.columns([1, 1, 1, 2])
        p = c1.number_input("P.U.", value=float(m['prix']), key=f"pm_{i}")
        q = c2.number_input("Qté", min_value=1, key=f"qm_{i}")
        l = c3.selectbox("Lieu", LIEUX_ARTICLES, key=f"lm_{i}")
        imgs = c4.file_uploader("Photos", accept_multiple_files=True, key=f"im_{i}")
        items_to_pdf.append({"Désignation": m['nom'], "P.U.": p, "Qté": q, "Total": p*q, "Lieu": l, "Images": imgs[:3] if imgs else []})
        total_items += p*q

grand_total = total_items + (1.0 if include_adh else 0.0) + liv_total
st.write(f"### TOTAL : {grand_total:,.2f} EUR")

# --- GÉNÉRATION PDF ---
if items_to_pdf and st.button("📄 GÉNÉRER LE PDF"):
    pdf = AIMA_PDF(logo_path=AIMA_LOGO_PATH, doc_type=doc_type)
    pdf.add_page()
    y_pos = pdf.draw_first_page_info(d_num, d_ref, d_date, c_name, c_addr, aima_pdf_info, doc_status)
    
    cols_w = [45, 17, 10, 18, 70, 30] if doc_type == "DEVIS" else [115, 17, 10, 18, 0, 30]
    pdf.set_font('Arial', 'B', 8); pdf.set_fill_color(220, 220, 220); pdf.set_xy(10, y_pos)
    headers = ["Designation", "P.U.", "Qte", "Total", "Photos", "Lieu"]
    for i, h in enumerate(headers):
        if cols_w[i] > 0: pdf.cell(cols_w[i], 8, h, 1, 0, 'C', True)
    pdf.ln()

    pdf.set_font("Arial", '', 8)
    for row in items_to_pdf:
        h_row = max(10, 32 if (doc_type == "DEVIS" and row['Images']) else 10)
        if pdf.get_y() + h_row > 250: pdf.add_page()
        y_c = pdf.get_y()
        pdf.cell(cols_w[0], h_row, row['Désignation'][:25].encode('latin-1','replace').decode('latin-1'), 1)
        pdf.cell(cols_w[1], h_row, f"{row['P.U.']:.2f}", 1, 0, 'C')
        pdf.cell(cols_w[2], h_row, str(row['Qté']), 1, 0, 'C')
        pdf.cell(cols_w[3], h_row, f"{row['Total']:.2f}", 1, 0, 'C')
        if doc_type == "DEVIS":
            pdf.cell(cols_w[4], h_row, "", 1)
            for idx, img in enumerate(row['Images']):
                with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
                    Image.open(img).convert("RGB").save(tmp.name)
                    pdf.image(tmp.name, pdf.get_x()-70 + (idx*22), y_c+2, h=h_row-4)
        pdf.cell(cols_w[5], h_row, row['Lieu'], 1, 1, 'C')

    pdf.ln(5); pdf.set_fill_color(51, 139, 140); pdf.set_text_color(255, 255, 255)
    pdf.cell(75, 10, "TOTAL NET", 1, 0, 'C', True)
    pdf.set_text_color(0, 0, 0); pdf.cell(25, 10, f"{grand_total:.2f} EUR", 1, 1, 'R')
    
    pdf_bytes = pdf.output(dest='S').encode('latin-1', 'replace')
    st.download_button("💾 Télécharger", pdf_bytes, f"{d_num}.pdf")
