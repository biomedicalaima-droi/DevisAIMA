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

# --- CONFIGURATION INITIALE ---
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

AIMA_LOGO_PATH = "aima_logo.png" # Modifiez le chemin si nécessaire

st.set_page_config(layout="wide", page_title="AIMA - Gestionnaire Pro", page_icon="📄")

# --- STYLE CSS PERSONNALISÉ ---
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; background-color: #338b8c; color: white; }
    .stMetaData { color: #184973; }
    .item-box { border: 1px solid #e6e9ef; padding: 15px; border-radius: 10px; background-color: white; margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- DONNÉES ---
LOCATIONS = {
    "CAME": {"address": "409 Chemin de Gensanne, 64520 Came", "email": "lehangardaima.came@gmail.com", "phone": "05 59 31 97 53"},
    "OSSERAIN-RIVAREYTE": {"address": "1009 Route des Aügas, 64390 Osserain-Rivareyte", "email": "osserain@assoaima.org", "phone": "05 59 38 17 86"},
    "SALIES-DE-BÉARN": {"address": "154 Chemin du Haou, 64270 Salies-de-Béarn", "email": "salies@assoaima.org", "phone": "05 59 38 03 30"},
    "CASTETNAU-CAMBLONG": {"address": "11 Rue du Bourg, 64190 Castetnau-Camblong", "email": "lehangardaima.castetnau@gmail.com", "phone": "05 59 66 16 90"}
}
LIEUX_ARTICLES = list(LOCATIONS.keys())
data_prices = {"Bureau": 0.0, "Chaise": 0.0, "Armoire": 0.0, "Table": 0.0, "Fauteuil": 0.0}

# --- SESSION STATE ---
if 'manual_items' not in st.session_state: st.session_state.manual_items = []
if 'catalog_selection' not in st.session_state: st.session_state.catalog_selection = []

# --- PDF CLASS ---
class AIMA_PDF(FPDF):
    def __init__(self, doc_type="DEVIS"):
        super().__init__()
        self.doc_type = doc_type

    def header(self):
        if os.path.exists(AIMA_LOGO_PATH):
            self.image(AIMA_LOGO_PATH, 10, 10, 40)
        self.set_font('Arial', 'B', 15)
        self.set_text_color(24, 73, 115)
        self.set_xy(100, 10)
        title = f"{self.doc_type} D'EQUIPEMENT MOBILIER ET MATERIEL"
        self.cell(100, 10, title.encode('latin-1', 'replace').decode('latin-1'), 0, 1, 'R')
        self.ln(20)

    def footer(self):
        self.set_y(-30)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(100, 100, 100)
        # --- PHRASES LÉGALES CONSERVÉES ---
        self.cell(0, 4, "TVA non applicable, Art. 261-7b du code général des impôts".encode('latin-1', 'replace').decode('latin-1'), 0, 1, 'C')
        self.cell(0, 4, "IBAN : FR90 2004 1010 0112 2207 4K02 259 BIC : PSSTFRPPBOR", 0, 1, 'C')
        self.cell(0, 4, "Association AIMA - Siege social : 1009 Route des Augas 64390 - Osserain-Rivareyte | SIRET : 508 544 715 00057", 0, 1, 'C')
        self.set_font('Arial', '', 7)
        self.cell(0, 4, f'Page {self.page_no()}', 0, 0, 'R')

    def draw_info_blocks(self, doc_num, ref, date_obj, c_name, c_addr, aima_info, status):
        # Badge Statut
        colors = {"En attente": (255, 193, 7), "Accepté": (40, 167, 69), "Refusé": (220, 53, 69)}
        bg = colors.get(status, (128, 128, 128))
        self.set_xy(155, 25)
        self.set_font('Arial', 'B', 10); self.set_fill_color(*bg); self.set_text_color(255, 255, 255)
        self.cell(45, 8, f"STATUT : {status.upper()}", 0, 1, 'C', True)

        # Blocs Adresses
        self.set_xy(10, 40)
        self.set_font('Arial', 'B', 9); self.set_fill_color(51, 139, 140); self.set_text_color(255, 255, 255)
        self.cell(85, 7, "EXPÉDITEUR : Association AIMA", 1, 1, 'C', True)
        self.set_text_color(0); self.set_font('Arial', '', 8); self.set_x(10)
        self.multi_cell(85, 4, aima_info.encode('latin-1', 'replace').decode('latin-1'), 1, 'C')
        y_left = self.get_y()

        self.set_xy(110, 40); self.set_text_color(255, 255, 255)
        self.cell(90, 7, f"DESTINATAIRE : {c_name.upper()}", 1, 1, 'C', True)
        self.set_text_color(0); self.set_font('Arial', '', 9); self.set_x(110)
        self.multi_cell(90, 5, c_addr.encode('latin-1', 'replace').decode('latin-1'), 1, 'C')
        
        self.set_xy(10, y_left + 2); self.set_font('Arial', 'B', 9)
        self.cell(60, 5, f"{self.doc_type} N°: {doc_num}", 0, 1)
        self.set_font('Arial', '', 9); self.cell(60, 5, f"Réf: {ref}", 0, 1)
        self.cell(60, 5, f"Date: {date_obj.strftime('%d/%m/%Y')}", 0, 1)
        return max(self.get_y(), self.get_y()) + 5

# --- FONCTION D'AFFICHAGE LIGNE ARTICLE ---
def item_interface(label, key):
    with st.expander(f"📦 {label}", expanded=True):
        col1, col2, col3, col4 = st.columns([2, 1, 1, 2])
        p = col1.number_input("Prix Unitaire (€)", min_value=0.0, key=f"p_{key}")
        q = col2.number_input("Quantité", min_value=1, key=f"q_{key}")
        l = col3.selectbox("Lieu", LIEUX_ARTICLES, key=f"l_{key}")
        imgs = col4.file_uploader("3 Photos max", type=["jpg", "png"], accept_multiple_files=True, key=f"i_{key}")
        
        if imgs:
            cols = st.columns(3)
            for idx, img in enumerate(imgs[:3]):
                cols[idx].image(img, use_container_width=True)
                
    return {"nom": label, "pu": p, "qty": q, "lieu": l, "images": imgs[:3]}

# --- UI STREAMLIT ---
st.sidebar.image(AIMA_LOGO_PATH, width=150) if os.path.exists(AIMA_LOGO_PATH) else st.sidebar.title("AIMA")
doc_type = st.sidebar.selectbox("Document", ["DEVIS", "FACTURE"])
status = st.sidebar.selectbox("Statut", ["En attente", "Accepté", "Refusé"])
loc = st.sidebar.selectbox("Lieu AIMA", list(LOCATIONS.keys()))

st.sidebar.divider()
c_name = st.sidebar.text_input("Client", "ONG-EPSPE")
c_addr = st.sidebar.text_area("Adresse Client", "Cotonou, Bénin")
d_num = st.sidebar.text_input("Numéro", "2026-001")
d_ref = st.sidebar.text_input("Référence", "AIMA-2026")
d_date = st.sidebar.date_input("Date", date.today())

st.sidebar.divider()
include_adh = st.sidebar.checkbox("Adhésion (1.00€)", True)
liv_price = st.sidebar.number_input("Livraison (€)", 0.0)

# --- CORPS PRINCIPAL ---
st.title(f"📄 Générateur de {doc_type}")

tab1, tab2 = st.tabs(["🛒 Articles", "⚙️ Paramètres Avancés"])

items_data = []
with tab1:
    catalog = st.multiselect("Choisir dans le catalogue", list(data_prices.keys()))
    for i, name in enumerate(catalog):
        items_data.append(item_interface(name, f"cat_{i}"))

    st.divider()
    if st.button("➕ Ajouter un article personnalisé"):
        st.session_state.manual_items.append(f"Article {len(st.session_state.manual_items)+1}")
    
    for i, name in enumerate(st.session_state.manual_items):
        items_data.append(item_interface(name, f"man_{i}"))

# --- GÉNÉRATION PDF ---
if st.button(f"🚀 GÉNÉRER LE {doc_type} MAINTENANT"):
    pdf = AIMA_PDF(doc_type=doc_type)
    pdf.add_page()
    
    aima_txt = f"Lieu: {loc}\n{LOCATIONS[loc]['address']}\nTél: {LOCATIONS[loc]['phone']}\n{LOCATIONS[loc]['email']}"
    y_start = pdf.draw_info_blocks(d_num, d_ref, d_date, c_name, c_addr, aima_txt, status)
    
    # Header Tableau
    w = [40, 15, 10, 15, 85, 25] # Designations, PU, Qte, Total, Photos (Large), Lieu
    pdf.set_xy(10, y_start)
    pdf.set_font('Arial', 'B', 8); pdf.set_fill_color(230, 230, 230)
    headers = ["Désignation", "P.U.", "Qté", "Total", "Photos (Toutes)", "Lieu"]
    for i, h in enumerate(headers): pdf.cell(w[i], 8, h, 1, 0, 'C', True)
    pdf.ln()

    # Lignes
    pdf.set_font('Arial', '', 8)
    total_ht = 0
    for item in items_data:
        h_row = 35 if item['images'] else 10
        if pdf.get_y() + h_row > 260: pdf.add_page()
        
        curr_y = pdf.get_y()
        total_row = item['pu'] * item['qty']
        total_ht += total_row
        
        pdf.cell(w[0], h_row, item['nom'][:25].encode('latin-1','replace').decode('latin-1'), 1, 0, 'L')
        pdf.cell(w[1], h_row, f"{item['pu']:.2f}", 1, 0, 'C')
        pdf.cell(w[2], h_row, str(item['qty']), 1, 0, 'C')
        pdf.cell(w[3], h_row, f"{total_row:.2f}", 1, 0, 'C')
        
        # --- LOGIQUE D'AFFICHAGE DES 3 PHOTOS ---
        img_cell_x = pdf.get_x()
        pdf.cell(w[4], h_row, "", 1, 0) # Cellule vide pour les images
        if item['images']:
            img_w = 25 # Largeur d'une image
            for idx, img_file in enumerate(item['images'][:3]):
                with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
                    img_pil = Image.open(img_file)
                    img_pil.convert("RGB").save(tmp.name)
                    # On place les images côte à côte avec un petit décalage
                    pdf.image(tmp.name, img_cell_x + 2 + (idx * 27), curr_y + 2, h=h_row - 4)
                    os.unlink(tmp.name)

        pdf.cell(w[5], h_row, item['lieu'].encode('latin-1','replace').decode('latin-1'), 1, 1, 'C')

    # Total
    grand_total = total_ht + (1.0 if include_adh else 0.0) + liv_price
    pdf.ln(5)
    y_final = pdf.get_y()
    if y_final > 220: pdf.add_page(); y_final = pdf.get_y()
    
    pdf.set_xy(10, y_final)
    pdf.cell(70, 7, f"Adhesion annuelle {d_date.year}", 1, 0); pdf.cell(25, 7, "1.00" if include_adh else "0.00", 1, 1, 'R')
    pdf.set_x(10); pdf.cell(70, 7, "Livraison", 1, 0); pdf.cell(25, 7, f"{liv_price:.2f}", 1, 1, 'R')
    pdf.set_x(10); pdf.set_fill_color(51, 139, 140); pdf.set_text_color(255); pdf.set_font('Arial', 'B', 10)
    pdf.cell(70, 10, "TOTAL NET", 1, 0, 'C', True); pdf.set_text_color(0); pdf.cell(25, 10, f"{grand_total:.2f} EUR", 1, 0, 'R')

    # Signature
    pdf.set_xy(115, y_final)
    pdf.set_font('Arial', 'B', 9); pdf.cell(85, 8, "Signature et cachet :", "LTR", 1, 'L')
    pdf.set_x(115); pdf.cell(85, 20, "", "LBR", 1)

    # Export
    stream = io.BytesIO()
    pdf_out = pdf.output(dest='S')
    stream.write(pdf_out.encode('latin-1') if isinstance(pdf_out, str) else pdf_out)
    st.download_button("💾 Télécharger le PDF", stream.getvalue(), f"{doc_type}_{d_num}.pdf", "application/pdf")

