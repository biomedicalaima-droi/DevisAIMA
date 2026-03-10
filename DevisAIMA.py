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

# Chemin du logo - Assurez-vous que ce fichier existe
AIMA_LOGO_PATH = "aima_logo.png" 

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
    "Fauteuil à roulette COMFORTO": 0.0, "Bureau": 0.0, "Armoire basse": 0.0,
    "Chaise opérateur Haworth": 0.0, "Table de réunion": 0.0, "Vestiaire Métallique": 0.0,
    "Caisson 3 Tiroirs": 0.0
}

# --- SESSION STATE ---
if 'manual_items_dict' not in st.session_state: st.session_state.manual_items_dict = []
if 'active_catalog' not in st.session_state: st.session_state.active_catalog = []
if 'catalog_selector' not in st.session_state: st.session_state.catalog_selector = []

# --- CALLBACKS ---
def delete_catalog_item(item_name):
    if item_name in st.session_state.catalog_selector: st.session_state.catalog_selector.remove(item_name)
    st.session_state.active_catalog = [x for x in st.session_state.active_catalog if x['name'] != item_name]

def delete_manual_item(index): st.session_state.manual_items_dict.pop(index)

# --- CLASSE PDF (LOGIQUE D'AFFICHAGE CORRIGÉE) ---
class AIMA_PDF(FPDF):
    def __init__(self, logo_path=None, doc_type="DEVIS"):
        super().__init__()
        self.logo_path = logo_path
        self.doc_type = doc_type

    def header(self):
        if self.logo_path and os.path.exists(self.logo_path): 
            self.image(self.logo_path, 10, 10, 38)
        self.set_font('Arial', 'B', 12); self.set_text_color(24, 73, 115)
        self.set_xy(100, 10)
        self.cell(100, 8, f"{self.doc_type} D'EQUIPEMENT MOBILIER ET MATERIEL", 0, 1, 'R')
        self.ln(20)

    def footer(self):
        self.set_y(-25)
        self.set_font('Arial', 'I', 7.5); self.set_text_color(100, 100, 100)
        self.cell(0, 4, "TVA non applicable, Art. 261-7b du code général des impôts", 0, 1, 'C')
        self.cell(0, 4, "IBAN : FR90 2004 1010 0112 2207 4K02 259 | SIRET : 508 544 715 00057", 0, 1, 'C')
        self.cell(0, 4, f'Page {self.page_no()}', 0, 0, 'R')

    def draw_info_blocks(self, doc_num, ref_text, selected_date, client_name, client_address, aima_info, status):
        # --- STATUT ---
        self.set_xy(150, 25)
        self.set_font('Arial', 'B', 10)
        self.set_fill_color(255, 193, 7) # Jaune/Orange comme sur la photo
        self.set_text_color(255, 255, 255)
        self.cell(50, 8, f"STATUT : {status.upper()}", 0, 1, 'C', True)

        # --- BLOCS ADRESSES CENTRÉS ---
        y_pos = 40
        # GAUCHE : Association AIMA
        self.set_xy(10, y_pos); self.set_font('Arial', 'B', 9)
        self.set_fill_color(51, 139, 140); self.set_text_color(255, 255, 255)
        self.cell(80, 7, "Association AIMA", 1, 1, 'C', True)
        self.set_text_color(0, 0, 0); self.set_font('Arial', '', 8); self.set_x(10)
        self.multi_cell(80, 4, aima_info.encode('latin-1', 'replace').decode('latin-1'), 1, 'C')
        y_left = self.get_y()
        
        # DROITE : Destinataire
        self.set_xy(115, y_pos); self.set_fill_color(51, 139, 140); self.set_text_color(255, 255, 255)
        self.cell(85, 7, f"DESTINATAIRE : {client_name.upper()}", 1, 1, 'C', True)
        self.set_text_color(0, 0, 0); self.set_font('Arial', '', 9); self.set_x(115)
        self.multi_cell(85, 5, client_address.encode('latin-1', 'replace').decode('latin-1'), 1, 'C')
        y_right = self.get_y()
        
        # Infos Document (N°, Réf, Date)
        self.set_xy(10, y_left + 3); self.set_font('Arial', '', 8.5)
        info = f"{self.doc_type} N°: {doc_num}\nRéf: {ref_text}\nDate: {selected_date.strftime('%d/%m/%Y')}"
        self.multi_cell(60, 4.5, info, 1, 'L')
        return max(self.get_y(), y_right) + 5

# --- FONCTION RENDER ROW (UI) ---
def render_item_row(label, default_price, key_suffix, is_manual=False, index=0):
    col_info, col_img = st.columns([2, 1])
    with col_info:
        st.write(f"**{label}**")
        c1, c2, c_loc, c3 = st.columns([1, 0.6, 1.2, 1])
        p = c1.number_input(f"P.U.", value=float(default_price), key=f"p_{key_suffix}")
        q = c2.number_input(f"Qté", min_value=1, value=1, key=f"q_{key_suffix}")
        l = c_loc.selectbox("Stock", options=LIEUX_ARTICLES, key=f"loc_{key_suffix}")
        imgs = c3.file_uploader(f"Photos", type=["jpg","png"], accept_multiple_files=True, key=f"img_{key_suffix}")
        if is_manual: st.button("Supprimer", key=f"del_{key_suffix}", on_click=delete_manual_item, args=(index,))
        else: st.button("Supprimer", key=f"del_{key_suffix}", on_click=delete_catalog_item, args=(label,))
    with col_img:
        if imgs:
            sc = st.columns(3)
            for idx, img in enumerate(imgs[:3]): sc[idx].image(img, use_container_width=True)
    st.divider()
    return {"Désignation": label, "P.U.": p, "Qté": q, "Total": p*q, "Lieu": l, "Images": imgs[:3] if imgs else []}, (p * q)

# --- INTERFACE ---
st.sidebar.header("📝 Paramètres")
doc_type = st.sidebar.selectbox("Document", ["DEVIS", "FACTURE"])
doc_status = st.sidebar.selectbox("Statut", ["En attente", "Accepté", "Refusé"])
selected_loc_name = st.sidebar.selectbox("Lieu d'expédition", options=list(LOCATIONS.keys()))

loc_data = LOCATIONS[selected_loc_name]
aima_pdf_info = f"Le Hangar d'AIMA - {selected_loc_name}\n{loc_data['address']}\nTél : {loc_data['phone']}\n{loc_data['email']}"

c_name = st.sidebar.text_input("Client", value="ONG- EPSPE")
c_addr = st.sidebar.text_area("Adresse Client", value="10 BP 1001 cotonou, Bénin")
d_num = st.sidebar.text_input("N° Document", value="2026-001")
d_ref = st.sidebar.text_input("Référence", value="AIMA-2026-INT")
d_date = st.sidebar.date_input("Date", value=date.today())
include_adh = st.sidebar.checkbox("Adhésion annuelle (1.00€)", value=True)
liv_total = st.sidebar.number_input("Frais de livraison", value=0.0)

st.title(f"Générateur de {doc_type}")

# Articles
selected_catalog = st.multiselect("📦 Catalogue", options=sorted(list(data_prices.keys())), key="catalog_selector")
items_to_pdf = []
total_global = 0.0

st.session_state.active_catalog = [x for x in st.session_state.active_catalog if x['name'] in selected_catalog]
for item in selected_catalog:
    if item not in [x['name'] for x in st.session_state.active_catalog]:
        st.session_state.active_catalog.append({'name': item, 'price': data_prices.get(item, 0.0)})

for i, it in enumerate(st.session_state.active_catalog):
    res, price = render_item_row(it['name'], it['price'], f"cat_{i}")
    items_to_pdf.append(res); total_global += price

# Article Manuel
st.subheader("➕ Ajouter un article")
m1, m2, m3 = st.columns([2, 1, 1])
n_nom = m1.text_input("Nom de l'objet")
n_prix = m2.number_input("Prix U.", min_value=0.0)
if m3.button("Ajouter") and n_nom:
    st.session_state.manual_items_dict.append({"id": str(time.time()), "nom": n_nom, "prix": n_prix})
    st.rerun()

for i, m in enumerate(st.session_state.manual_items_dict):
    res, price = render_item_row(m['nom'], m['prix'], f"man_{m['id']}", is_manual=True, index=i)
    items_to_pdf.append(res); total_global += price

grand_total = total_global + (1.0 if include_adh else 0.0) + liv_total

# --- GÉNÉRATION PDF ---
if st.button(f"📄 GÉNÉRER LE PDF"):
    pdf = AIMA_PDF(logo_path=AIMA_LOGO_PATH, doc_type=doc_type)
    pdf.add_page()
    y_table = pdf.draw_info_blocks(d_num, d_ref, d_date, c_name, c_addr, aima_pdf_info, doc_status)
    
    # Colonnes
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
        nb_lines = len(pdf.multi_cell(w[0], 5, txt, split_only=True))
        h_row = max(nb_lines * 5, 30 if (doc_type == "DEVIS" and row['Images']) else 10)
        
        if pdf.get_y() + h_row > 260: pdf.add_page()
        
        curr_y = pdf.get_y()
        # Bordures
        for i in range(len(w)):
            if w[i] > 0: pdf.rect(10 + sum(w[:i]), curr_y, w[i], h_row)
        
        # Contenu
        pdf.set_xy(10, curr_y); pdf.multi_cell(w[0], 5, txt, 0, 'L')
        pdf.set_xy(10 + w[0], curr_y); pdf.cell(w[1], h_row, f"{row['P.U.']:.2f}", 0, 0, 'C')
        pdf.cell(w[2], h_row, str(row['Qté']), 0, 0, 'C')
        pdf.cell(w[3], h_row, f"{row['Total']:.2f}", 0, 0, 'C')
        
        # Photos
        if doc_type == "DEVIS" and row['Images']:
            img_x = 10 + sum(w[:4])
            for idx, img in enumerate(row['Images'][:3]):
                with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
                    pimg = Image.open(img)
                    if pimg.mode in ("RGBA", "P"): pimg = pimg.convert("RGB")
                    pimg.save(tmp.name, "JPEG")
                    pdf.image(tmp.name, img_x + 2 + (idx * 19), curr_y + 2, h=h_row - 4)
                os.unlink(tmp.name)
        
        pdf.set_xy(10 + sum(w[:5]), curr_y)
        pdf.cell(w[5], h_row, row['Lieu'], 0, 1, 'C')

    # --- TOTAUX ET SIGNATURE (ALIGNÉS IMAGE) ---
    pdf.ln(5)
    if pdf.get_y() > 220: pdf.add_page()
    y_fin = pdf.get_y()

    # Totaux à gauche
    pdf.set_font('Arial', '', 9); pdf.set_xy(10, y_fin)
    pdf.cell(70, 7, f"Adhesion annuelle {d_date.year}", 1, 0)
    pdf.cell(25, 7, f"{'1.00' if include_adh else '0.00'} EUR", 1, 1, 'R')
    pdf.set_x(10)
    pdf.cell(70, 7, "Livraison au pied du batiment", 1, 0)
    pdf.cell(25, 7, f"{liv_total:.2f} EUR", 1, 1, 'R')
    pdf.set_x(10); pdf.set_font('Arial', 'B', 10); pdf.set_fill_color(51, 139, 140); pdf.set_text_color(255, 255, 255)
    pdf.cell(70, 10, "TOTAL NET", 1, 0, 'C', True)
    pdf.set_text_color(0, 0, 0); pdf.cell(25, 10, f"{grand_total:.2f} EUR", 1, 1, 'R')

    # Bloc Signature à droite (Centré)
    pdf.set_xy(115, y_fin)
    pdf.set_font('Arial', 'B', 9)
    pdf.cell(85, 8, "Signature et cachet :", "LTR", 1, 'C') # Centré
    pdf.set_x(115)
    pdf.cell(85, 24, "", "LBR", 1, 'C') # Espace pour le tampon

    # Sortie
    pdf_bytes = pdf.output(dest='S')
    st.download_button("💾 Télécharger le PDF", pdf_bytes, f"{doc_type}_{d_num}.pdf", "application/pdf")
