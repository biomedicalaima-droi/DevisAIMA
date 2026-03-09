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
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

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
    "Fauteuil à roulette COMFORTO": 0.0, "Fauteuil de bureau ADDFORM": 0.0, "Fauteuil de bureau STEELCASE": 0.0,
    "Bureau": 0.0, "Bureau avec retour": 0.0, "Table de réunion": 0.0, "Armoire basse": 0.0,
    "Caisson 3 Tiroirs": 0.0, "Vestiaire Métallique": 0.0, "Lit simple Souvignet": 0.0,
    "Chaise scolaire T6": 0.0, "Table pliante": 0.0, "Rayonnage Pro": 0.0
}

# --- SESSION STATE ---
if 'manual_items_dict' not in st.session_state: st.session_state.manual_items_dict = []
if 'active_catalog' not in st.session_state: st.session_state.active_catalog = []
if 'catalog_selector' not in st.session_state: st.session_state.catalog_selector = []

# --- FONCTIONS UTILITAIRES ---
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

def delete_catalog_item(item_name):
    if item_name in st.session_state.catalog_selector: st.session_state.catalog_selector.remove(item_name)
    st.session_state.active_catalog = [x for x in st.session_state.active_catalog if x['name'] != item_name]

def delete_manual_item(index): 
    st.session_state.manual_items_dict.pop(index)

# --- CLASSE PDF ---
class AIMA_PDF(FPDF):
    def __init__(self, logo_path=None, doc_type="DEVIS"):
        super().__init__()
        self.logo_path = logo_path
        self.doc_type = doc_type

    def header(self):
        if self.logo_path and os.path.exists(self.logo_path): 
            try: self.image(self.logo_path, 20, 18, 42)
            except: pass
        self.set_font('Arial', 'B', 14); self.set_text_color(24, 73, 115)
        self.set_xy(100, 10)
        self.cell(100, 8, f"{self.doc_type} D'EQUIPEMENT MOBILIER ET MATERIEL", 0, 1, 'R')
        self.ln(20)

    def footer(self):
        self.set_y(-30); self.set_font('Arial', 'I', 7.5); self.set_text_color(100, 100, 100)
        self.cell(0, 4, "TVA non applicable, Art. 261-7b du code général des impôts", 0, 1, 'C')
        self.cell(0, 4, "IBAN : FR90 2004 1010 0112 2207 4K02 259 | SIRET : 508 544 715 00057", 0, 1, 'C')
        self.cell(0, 4, f'Page {self.page_no()}', 0, 0, 'R')

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
loc_data = LOCATIONS[selected_loc_name]
aima_pdf_info = f"AIMA - {selected_loc_name}\n{loc_data['address']}\nTél : {loc_data['phone']}\nSIRET: 508 544 715 00057"

c_name = st.sidebar.text_input("Client", "ONG- EPSPE")
c_addr = st.sidebar.text_area("Adresse", "Cotonou, Bénin")
d_num = st.sidebar.text_input("N°", f"2026-001")
d_ref = st.sidebar.text_input("Référence", "AIMA-2026")
d_date = st.sidebar.date_input("Date", date.today())
include_adh = st.sidebar.checkbox("Adhésion (1€)", True)
liv_total = st.sidebar.number_input("Livraison (€)", 0.0)

st.title(f"Générateur de {doc_type}")

# Import PDF
up_file = st.file_uploader("📥 Importer un ancien PDF", type="pdf")
if up_file and st.button("Scanner le PDF"):
    st.session_state.manual_items_dict.extend(import_items_from_pdf(up_file))
    st.rerun()

# Sélection Catalogue
selected_catalog = st.multiselect("📦 Catalogue :", options=sorted(list(data_prices.keys())), key="catalog_selector")
items_to_pdf = []
total_items = 0.0

def render_row(label, price, key):
    with st.container(border=True):
        st.write(f"**{label}**")
        c1, c2, c3, c4 = st.columns([1, 1, 1, 2])
        p = c1.number_input("P.U.", value=float(price), key=f"p_{key}")
        q = c2.number_input("Qté", min_value=1, key=f"q_{key}")
        l = c3.selectbox("Lieu", LIEUX_ARTICLES, key=f"l_{key}")
        imgs = c4.file_uploader("Photos", accept_multiple_files=True, key=f"i_{key}")
        return {"Désignation": label, "P.U.": p, "Qté": q, "Total": p*q, "Lieu": l, "Images": imgs[:3] if imgs else []}

for i, item in enumerate(selected_catalog):
    res = render_row(item, data_prices.get(item, 0), f"cat_{i}")
    items_to_pdf.append(res); total_items += res['Total']

st.subheader("➕ Article Manuel")
col_m1, col_m2 = st.columns([3, 1])
m_nom = col_m1.text_input("Nom de l'article")
m_prix = col_m2.number_input("Prix", 0.0)
if st.button("Ajouter l'article"):
    st.session_state.manual_items_dict.append({"nom": m_nom, "prix": m_prix})
    st.rerun()

for i, m in enumerate(st.session_state.manual_items_dict):
    res = render_row(m['nom'], m['prix'], f"man_{i}")
    items_to_pdf.append(res); total_items += res['Total']

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
        nom_p = row['Désignation'].encode('latin-1', 'replace').decode('latin-1')
        h_row = max(10, 32 if (doc_type == "DEVIS" and row['Images']) else 10)
        if pdf.get_y() + h_row > 250: pdf.add_page()
        
        y_c = pdf.get_y()
        pdf.cell(cols_w[0], h_row, nom_p[:25], 1)
        pdf.cell(cols_w[1], h_row, f"{row['P.U.']:.2f}", 1, 0, 'C')
        pdf.cell(cols_w[2], h_row, str(row['Qté']), 1, 0, 'C')
        pdf.cell(cols_w[3], h_row, f"{row['Total']:.2f}", 1, 0, 'C')
        
        if doc_type == "DEVIS":
            pdf.cell(cols_w[4], h_row, "", 1)
            for idx, img in enumerate(row['Images']):
                with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
                    pimg = Image.open(img).convert("RGB")
                    pimg.save(tmp.name)
                    pdf.image(tmp.name, pdf.get_x()-70 + (idx*22), y_c+2, h=h_row-4)
                if os.path.exists(tmp.name): os.remove(tmp.name)
        
        pdf.cell(cols_w[5], h_row, row['Lieu'], 1, 1, 'C')

    # Bloc Signature & Totaux
    pdf.ln(5)
    y_end = pdf.get_y()
    pdf.set_font("Arial", 'B', 9)
    pdf.cell(70, 8, f"Adhesion: {'1.00' if include_adh else '0.00'} EUR", 1, 1)
    pdf.cell(70, 8, f"Livraison: {liv_total:.2f} EUR", 1, 1)
    pdf.set_fill_color(51, 139, 140); pdf.set_text_color(255, 255, 255)
    pdf.cell(70, 10, f"TOTAL NET: {grand_total:.2f} EUR", 1, 0, 'C', True)
    
    # Signature
    pdf.set_xy(120, y_end); pdf.set_text_color(0, 0, 0)
    pdf.cell(80, 26, "Signature et Cachet", 1, 0, 'C')

    # FIX DU PDF VIDE (Conversion Bytes)
    pdf_output = pdf.output(dest='S')
    if isinstance(pdf_output, str):
        pdf_output = pdf_output.encode('latin-1')

    st.download_button("💾 Télécharger le PDF", pdf_output, f"{doc_type}_{d_num}.pdf", "application/pdf")

