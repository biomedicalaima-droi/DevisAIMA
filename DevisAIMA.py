# -*- coding: utf-8 -*-
import streamlit as st
from fpdf import FPDF
from datetime import date
import os
import tempfile
import time
import io

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

AIMA_LOGO_PATH = resource_path("aima_logo.png")


# Configuration de la page Streamlit
st.set_page_config(layout="wide", page_title="AIMA - Gestion de Devis")

# --- CHEMIN DU LOGO ---
#AIMA_LOGO_PATH = "C:/Users/perso/Desktop/aima_logo.png"

# --- INITIALISATION ---
if 'manual_items_dict' not in st.session_state:
    st.session_state.manual_items_dict = []
if 'active_catalog' not in st.session_state:
    st.session_state.active_catalog = []
if 'catalog_selector' not in st.session_state:
    st.session_state.catalog_selector = []

# --- CALLBACKS ---
def delete_catalog_item(item_name):
    if item_name in st.session_state.catalog_selector:
        st.session_state.catalog_selector.remove(item_name)
    st.session_state.active_catalog = [x for x in st.session_state.active_catalog if x['name'] != item_name]

def delete_manual_item(index):
    st.session_state.manual_items_dict.pop(index)

# --- LOGO SIDEBAR ---
if os.path.exists(AIMA_LOGO_PATH):
    st.sidebar.image(AIMA_LOGO_PATH, use_container_width=True)
    st.sidebar.divider()
# --- CONFIGURATION STREAMLIT ---
st.set_page_config(layout="wide", page_title="AIMA - Gestion de Devis")

# --- PARAMÈTRES ET CHEMINS ---
AIMA_LOGO_PATH = "C:/Users/perso/Desktop/aima_logo.png"

LOCATIONS = {
    "CAME": {"address": "409 Chemin de Gensanne, 64520 Came", "email": "lehangardaima.came@gmail.com", "phone": "05 59 31 97 53"},
    "OSSERAIN-RIVAREYTE": {"address": "1009 Route des Aügas, 64390 Osserain-Rivareyte", "email": "osserain@assoaima.org", "phone": "05 59 38 17 86"},
    "SALIES-DE-BÉARN": {"address": "154 Chemin du Haou, 64270 Salies-de-Béarn", "email": "salies@assoaima.org", "phone": "05 59 38 03 30"},
    "CASTETNAU-CAMBLONG": {"address": "11 Rue du Bourg, 64190 Castetnau-Camblong", "email": "lehangardaima.castetnau@gmail.com", "phone": "05 59 66 16 90"}
}
LIEUX_ARTICLES = ["Came", "Osserain-Rivareyte", "Salies-de-Béarn", "Castetnau-Camblong"]

if 'manual_items_dict' not in st.session_state: st.session_state.manual_items_dict = []
if 'active_catalog' not in st.session_state: st.session_state.active_catalog = []
if 'catalog_selector' not in st.session_state: st.session_state.catalog_selector = []

def delete_catalog_item(item_name):
    if item_name in st.session_state.catalog_selector: st.session_state.catalog_selector.remove(item_name)
    st.session_state.active_catalog = [x for x in st.session_state.active_catalog if x['name'] != item_name]

def delete_manual_item(index): st.session_state.manual_items_dict.pop(index)

data_prices = {
    "Fauteuil à roulette COMFORTO": 0.0, "Fauteuil de bureau ADDFORM": 0.0, "Fauteuil de bureau EUROSIT": 0.0,
    "Fauteuil de bureau STEELCASE": 0.0, "Fauteuil de bureau majencia": 0.0, "Fauteuil de bureau Interstuhl Hero": 0.0,
    "Bureau individuel": 0.0, "Table de réunion": 0.0, "Armoire basse": 0.0,
    "Alcôve / Isoloir / Coin Lecture": 0.0, "Alcôve de réunion 4 places": 0.0
}

class AIMA_PDF(FPDF):
    def __init__(self, logo_path=None):
        super().__init__()
        self.logo_path = logo_path

    def header(self):
        if self.logo_path and os.path.exists(self.logo_path): self.image(self.logo_path, 20, 18, 42)
        self.set_font('Arial', 'B', 14); self.set_text_color(24, 73, 115)
        self.set_xy(110, 10); self.cell(90, 8, "DEVIS D'EQUIPEMENT MOBILIER ET MATERIEL", 0, 1, 'R')
        self.ln(20)

    def footer(self):
        self.set_y(-30)
        self.set_font('Arial', 'I', 7.5); self.set_text_color(100, 100, 100)
        self.cell(0, 4, "TVA non applicable, Art. 261-7b du code général des impôts", 0, 1, 'C')
        self.cell(0, 4, "IBAN : FR90 2004 1010 0112 2207 4K02 259 BIC : PSSTFRPPBOR", 0, 1, 'C')
        self.cell(0, 4, "Association AIMA - Siege social : 1009 Route des Augas 64390 - Osserain-Rivareyte | SIRET : 508 544 715 00057", 0, 1, 'C')
        self.set_font('Arial', '', 7); self.cell(0, 4, f'Page {self.page_no()}', 0, 0, 'R')

    def draw_first_page_info(self, devis_num, ref_text, selected_date, client_name, client_address, aima_info):
        y_boxes = 40
        self.set_fill_color(51, 139, 140); self.set_text_color(255, 255, 255)
        self.set_xy(10, y_boxes); self.set_font('Arial', 'B', 9)
        self.cell(80, 7, "Association AIMA", 1, 1, 'C', True)
        self.set_text_color(0, 0, 0); self.set_font('Arial', '', 8); self.set_x(10)
        self.multi_cell(80, 4, aima_info.encode('latin-1', 'replace').decode('latin-1'), 1, 'C')
        y_left = self.get_y()
        self.set_xy(120, y_boxes); self.set_fill_color(51, 139, 140); self.set_text_color(255, 255, 255)
        self.cell(80, 7, f"DESTINATAIRE : {client_name.upper()}", 1, 1, 'C', True)
        self.set_text_color(0, 0, 0); self.set_font('Arial', '', 9); self.set_x(120)
        self.multi_cell(80, 5, client_address.encode('latin-1', 'replace').decode('latin-1'), 1, 'C')
        y_right = self.get_y()
        self.set_xy(10, y_left + 2); self.set_font('Arial', '', 8.5)
        self.multi_cell(55, 4.2, f"Devis N°: {devis_num}\nRéf: {ref_text}\nDate: {selected_date.strftime('%d/%m/%Y')}", 1, 'L')
        return max(self.get_y(), y_right) + 5

def render_item_row(label, default_price, key_suffix, is_manual=False, index=0):
    col_info, col_img = st.columns([1.8, 1])
    with col_info:
        st.write(f"### {label}")
        c1, c2, c_loc, c3 = st.columns([1, 0.7, 1.3, 1.2])
        p = c1.number_input(f"P.U. (EUR)", value=float(default_price), format="%.2f", key=f"p_{key_suffix}")
        q = c2.number_input(f"Qté", min_value=1, value=1, key=f"q_{key_suffix}")
        l = c_loc.selectbox("Lieu de stockage", options=LIEUX_ARTICLES, key=f"loc_{key_suffix}")
        imgs = c3.file_uploader(f"Photos", type=["jpg","png"], accept_multiple_files=True, key=f"img_{key_suffix}")
        if is_manual: st.button("❌ Supprimer", key=f"del_{key_suffix}", on_click=delete_manual_item, args=(index,))
        else: st.button("❌ Supprimer", key=f"del_{key_suffix}", on_click=delete_catalog_item, args=(label,))
    with col_img:
        if imgs:
            sub_cols = st.columns(3)
            for idx, img in enumerate(imgs[:3]): sub_cols[idx].image(img, use_container_width=True)
    st.divider()
    return {"Désignation": label, "P.U.": p, "Qté": q, "Total": p*q, "Lieu": l, "Images": imgs[:3] if imgs else []}, (p * q)

# --- INTERFACE ---
col_h1, col_h2 = st.columns([1, 5])
if os.path.exists(AIMA_LOGO_PATH): col_h1.image(AIMA_LOGO_PATH, width=120)
col_h2.markdown('<h1 style="color: #2c3e50; margin-top: 20px;">Plateforme de Devis AIMA</h1>', unsafe_allow_html=True)

st.sidebar.header("📝 Paramètres")
selected_loc_name = st.sidebar.selectbox("Lieu d'expédition", options=list(LOCATIONS.keys()))
loc_data = LOCATIONS[selected_loc_name]
aima_pdf_info = f"Le Hangar d'AIMA - {selected_loc_name}\n{loc_data['address']}\nTél : {loc_data['phone']}\nMail : {loc_data['email']}\nSIRET: 508 544 715 00057"

c_name = st.sidebar.text_input("Client", value="ONG- EPSPE")
c_addr = st.sidebar.text_area("Adresse Client", value="10 BP 1001 cotonou, Bénin")
d_num = st.sidebar.text_input("N° Devis", value="2026-001")
d_ref = st.sidebar.text_input("Référence", value="AIMA-2026-INT")
d_date = st.sidebar.date_input("Date", value=date.today())

st.sidebar.divider()
st.sidebar.subheader("⚙️ Frais Annexes")
include_adh = st.sidebar.checkbox(f"Cout adhésion annuelle {d_date.year} (1.00 EUR)", value=True)
include_liv = st.sidebar.checkbox("Livraison par nos soins", value=True)
liv_total = st.sidebar.number_input("Prix de la livraison (EUR)", value=78.00) if include_liv else 0.0

selected_catalog = st.multiselect("📦 Sélectionner les dispositifs :", options=sorted(list(data_prices.keys())), key="catalog_selector")
items_to_pdf = []
total_global_items = 0.0

st.session_state.active_catalog = [x for x in st.session_state.active_catalog if x['name'] in selected_catalog]
for item in selected_catalog:
    if item not in [x['name'] for x in st.session_state.active_catalog]:
        st.session_state.active_catalog.append({'name': item, 'price': data_prices[item]})

for i, item_data in enumerate(st.session_state.active_catalog):
    res, price = render_item_row(item_data['name'], item_data['price'], f"cat_{i}")
    items_to_pdf.append(res); total_global_items += price

st.subheader("➕ Article personnalisé")
m_cols = st.columns([2, 1, 1])
n_nom = m_cols[0].text_input("Désignation", key="manual_name")
n_prix = m_cols[1].number_input("Prix P.U.", min_value=0.0, format="%.2f", key="manual_price")
if m_cols[2].button("✅ Ajouter") and n_nom:
    st.session_state.manual_items_dict.append({"id": str(time.time()), "nom": n_nom, "prix": n_prix})
    st.rerun()

for i, m in enumerate(st.session_state.manual_items_dict):
    res, price = render_item_row(m['nom'], m['prix'], f"man_{m['id']}", is_manual=True, index=i)
    items_to_pdf.append(res); total_global_items += price

# --- CALCUL ET AFFICHAGE DU TOTAL SUR LA PLATEFORME ---
grand_total = total_global_items + (1.0 if include_adh else 0.0) + (liv_total if include_liv else 0.0)
st.sidebar.markdown("---")
st.sidebar.markdown(f"### **TOTAL NET : {grand_total:,.2f} EUR**")

# --- PDF ---
if items_to_pdf:
    if st.button("📄 GÉNÉRER LE DEVIS PDF"):
        pdf = AIMA_PDF(logo_path=AIMA_LOGO_PATH)
        pdf.add_page()
        y_pos = pdf.draw_first_page_info(d_num, d_ref, d_date, c_name, c_addr, aima_pdf_info)
        
        cols_w = [45, 17, 10, 18, 70, 30] 
        pdf.set_font('Arial', 'B', 8); pdf.set_fill_color(220, 220, 220); pdf.set_xy(10, y_pos)
        headers = ["Designation", "P.U.", "Qte", "Total", "Photos", "Lieu"]
        for h, w in zip(headers, cols_w): pdf.cell(w, 8, h, 1, 0, 'C', True)
        pdf.ln()

        pdf.set_font("Arial", '', 8)
        for row in items_to_pdf:
            nom_p = row['Désignation'].encode('latin-1', 'replace').decode('latin-1')
            nb_lines = len(pdf.multi_cell(cols_w[0]-2, 4, nom_p, split_only=True))
            h_row = max(nb_lines * 4 + 4, 32 if row['Images'] else 10)
            if pdf.get_y() + h_row > 240: pdf.add_page()
            y_c = pdf.get_y()
            pdf.rect(10, y_c, cols_w[0], h_row)
            pdf.set_xy(10, y_c + (h_row - (nb_lines * 4)) / 2)
            pdf.multi_cell(cols_w[0], 4, nom_p, 0, 'L')
            pdf.set_xy(10 + cols_w[0], y_c)
            pdf.cell(cols_w[1], h_row, f"{row['P.U.']:,.2f}", 1, 0, 'C')
            pdf.cell(cols_w[2], h_row, str(row['Qté']), 1, 0, 'C')
            pdf.cell(cols_w[3], h_row, f"{row['Total']:,.2f}", 1, 0, 'C')
            
            # --- PHOTO CENTERING LOGIC ---
            img_x_start = pdf.get_x()
            pdf.cell(cols_w[4], h_row, "", 1, 0) # Draw the photo cell box
            if row['Images']:
                num_imgs = len(row['Images'])
                img_display_w = 20  # Fixed width for each thumbnail
                spacing = 2
                total_imgs_w = (num_imgs * img_display_w) + ((num_imgs - 1) * spacing)
                # Calculate start offset to center thumbnails inside the 70mm cell
                start_offset = (cols_w[4] - total_imgs_w) / 2
                
                for idx, img in enumerate(row['Images']):
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
                        tmp.write(img.getvalue()); tmp.close()
                        # Place image with calculated offset
                        pdf.image(tmp.name, img_x_start + start_offset + (idx * (img_display_w + spacing)), y_c + 2, h=h_row-4)
                        os.unlink(tmp.name)
            
            pdf.cell(cols_w[5], h_row, row['Lieu'].encode('latin-1', 'replace').decode('latin-1'), 1, 1, 'C')

        # --- BLOC FINAL ---
        pdf.ln(10)
        if pdf.get_y() > 200: pdf.add_page()
        y_start = pdf.get_y()
        
        label_w = 75  
        price_box_w = 25 
        sig_box_w = 85  

        pdf.set_font("Arial", '', 9)
        pdf.set_xy(10, y_start)
        pdf.cell(label_w, 8, f"Cout adhesion annuelle {d_date.year}", 1, 0, 'L')
        pdf.cell(price_box_w, 8, "1.00 EUR" if include_adh else "0.00 EUR", 1, 1, 'R')
        
        pdf.set_x(10)
        pdf.cell(label_w, 8, "Livraison par nos soins au pied du batiment".encode('latin-1','replace').decode('latin-1'), 1, 0, 'L')
        pdf.cell(price_box_w, 8, f"{liv_total:,.2f} EUR", 1, 1, 'R')
        
        pdf.set_x(10)
        pdf.set_fill_color(51, 139, 140); pdf.set_text_color(255, 255, 255); pdf.set_font("Arial", 'B', 10)
        pdf.cell(label_w, 10, "TOTAL NET", 1, 0, 'C', True)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(price_box_w, 10, f"{grand_total:,.2f} EUR", 1, 1, 'R')

        pdf.set_xy(115, y_start) 
        pdf.set_font("Arial", 'B', 9)
        pdf.cell(sig_box_w, 8, "Signature et cachet :", 1, 1, 'L')
        pdf.set_x(115)
        pdf.cell(sig_box_w, 18, "", 1, 1)

        pdf_out = io.BytesIO()
        pdf_data = pdf.output(dest='S')
        pdf_out.write(pdf_data.encode('latin-1') if isinstance(pdf_data, str) else pdf_data)

        st.download_button("💾 Télécharger le Devis", pdf_out.getvalue(), f"Devis_{d_num}.pdf", "application/pdf")
