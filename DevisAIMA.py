# -*- coding: utf-8 -*-
import streamlit as st
from fpdf import FPDF
from datetime import date
import os
import tempfile
import time
import json
from PIL import Image

# --- CONFIGURATION INITIALE ---
st.set_page_config(layout="wide", page_title="AIMA - Devis & Factures")

TARGET_FOLDER = r"C:\Usrs\perso\Desktop\Devis-Facture"
COUNTER_FILE = os.path.join(TARGET_FOLDER, "counter.json")
AIMA_LOGO_PATH = "C:/Users/perso/Desktop/aima_logo.png"

if not os.path.exists(TARGET_FOLDER):
    os.makedirs(TARGET_FOLDER)


AIMA_LOGO_PATH = "C:/Users/perso/Desktop/aima_logo.png"

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

st.set_page_config(layout="wide", page_title="AIMA - Devis & Factures")
# --- GESTION DU COMPTEUR ---
def load_counters():
    if os.path.exists(COUNTER_FILE):
        try:
            with open(COUNTER_FILE, "r") as f:
                return json.load(f)
        except:
            pass
    return {"DEVIS": 0, "FACTURE": 0}

def save_counters(counters):
    with open(COUNTER_FILE, "w") as f:
        json.dump(counters, f)

def get_next_number(doc_type):
    counters = load_counters()
    next_val = counters.get(doc_type, 0) + 1
    prefix = "FAC" if doc_type == "FACTURE" else "DEV"
    return f"{date.today().year}-{prefix}-{next_val:03d}"

def increment_counter(doc_type):
    counters = load_counters()
    counters[doc_type] = counters.get(doc_type, 0) + 1
    save_counters(counters)

# --- INITIALISATION SESSION STATE ---
if 'manual_items_dict' not in st.session_state:
    st.session_state.manual_items_dict = []
if 'active_catalog' not in st.session_state:
    st.session_state.active_catalog = []
if 'catalog_selector' not in st.session_state:
    st.session_state.catalog_selector = []

# --- DONNÉES ---
LOCATIONS = {
    "CAME": {"address": "409 Chemin de Gensanne, 64520 Came", "email": "lehangardaima.came@gmail.com", "phone": "05 59 31 97 53"},
    "OSSERAIN-RIVAREYTE": {"address": "1009 Route des Aügas, 64390 Osserain-Rivareyte", "email": "osserain@assoaima.org", "phone": "05 59 38 17 86"},
    "SALIES-DE-BÉARN": {"address": "154 Chemin du Haou, 64270 Salies-de-Béarn", "email": "salies@assoaima.org", "phone": "05 59 38 03 30"},
    "CASTETNAU-CAMBLONG": {"address": "11 Rue du Bourg, 64190 Castetnau-Camblong", "email": "lehangardaima.castetnau@gmail.com", "phone": "05 59 66 16 90"}
}
LIEUX_ARTICLES = ["Came", "Osserain-Rivareyte", "Salies-de-Béarn", "Castetnau-Camblong"]
MODES_PAIEMENT = ["Virement", "Chèque", "Espèces", "Carte Bleue"]

data_prices = {
    "Fauteuil à roulette COMFORTO": 0.0, "Fauteuil de bureau ADDFORM": 0.0, "Fauteuil de bureau EUROSIT": 0.0,
    "Fauteuil de bureau STEELCASE": 0.0, "Fauteuil de bureau majencia": 0.0, "Fauteuil de bureau Interstuhl Hero": 0.0,
    "Fauteuil de bureau GIRSBERGER": 0.0, "Chaise opérateur Haworth": 0.0, "Fauteuil ergonomique Addform": 0.0,
    "Fauteuil Horma Teknion": 0.0, "Fauteuil dessinateur Forma 5": 0.0, "Chaise opérateur Viasit Drumback gris": 0.0,
    "Fauteuil Savera Teknion": 0.0, "Fauteuil Bejot Eleven Blanc": 0.0, "Fauteuil opérateur REXITT": 0.0,
    "Fauteuil Steelcase sans accoudoirs": 0.0, "Fauteuil Aresline Trendy": 0.0, "Fauteuil System 55 Haworth": 0.0,
    "Siège Cobi Steelcase": 0.0, "Fauteuil Comforto": 0.0, "CHAISE PLASTISQUE PIED ALU": 0.0, "Chaises empilables": 0.0,
    "Chaise scolaire T6": 0.0, "Chaise 4 pieds bicolore": 0.0, "Lot chaises d’école Rondo": 0.0,
    "Bureau": 0.0, "Bureau 70 x 122 cm": 0.0, "Bureau avec retour": 0.0, "Bureau FrameOne Steelcase": 0.0,
    "Bureau individuel": 0.0, "Bureau sur roulettes": 0.0, "Grand bureau individuel": 0.0, "Table pliante sans marque": 0.0,
    "Bureau haut": 0.0, "Bureau Frameone Steelcase": 0.0, "Bureau individuel ou bench de 2 ou 4 postes de travail": 0.0,
    "Bureau Majencia": 0.0, "Bureau d’angle SteelCase": 0.0, "Bureau individuel 4 pieds": 0.0, "Bench 2 places Sedus en 120 cm": 0.0,
    "Bench 2.0 Platten Steelcase": 0.0, "Bench Majencia 120×160 cm": 0.0, "Bench Steelcase Frame One": 0.0,
    "Benchs 2 places Sedus en 160 cm (3 modèles)": 0.0, "Table carrée 160×160": 0.0, "Table de réunion": 0.0,
    "Table de réunion carrée 140×140": 0.0, "Bench 4 postes": 0.0, "Bench 4 postes réglables": 0.0,
    "Bureau électrique Teknion": 0.0, "Table ronde Strafor": 0.0, "Table de réunion 12 personnes": 0.0,
    "Table de réunion en trapèze": 0.0, "Table de réunion Sedus": 0.0, "Table ovale Steelcase": 0.0,
    "Table de réunion haute Steelcase": 0.0, "Console": 0.0, "Table de réunion haute Ahrend": 0.0,
    "Table pliante Wiesner-Hager": 0.0, "Tabla basse sokoa": 0.0, "Table basse ronde": 0.0,
    "Table de restauration – 4 pers": 0.0, "Table bois massif": 0.0, "Table de Jardin": 0.0,
    "Table bistrot carrée": 0.0, "Table scolaire bicolore T6": 0.0, "Table scolaire T6": 0.0,
    "Table rectangulaire COMPO": 0.0, "Table de café/thé": 0.0,
    "Armoire basse": 0.0, "Armoire internat": 0.0, "Armoire mi-haute blanche": 0.0, "Armoires plateau tournant à rideaux": 0.0,
    "Vitrine sur roulettes": 0.0, "Armoire haute vitrée": 0.0, "Armoire basse portes battantes": 0.0,
    "Armoire basse portes coulissantes": 0.0, "Armoire haute portes battantes": 0.0, "Armoire haute portes battantes NowyStyl": 0.0,
    "Armoire métallique blanche rideaux coulissants": 0.0, "Caisson 3 Tiroirs": 0.0, "Caisson blanc": 0.0,
    "Caisson de bureau 2 tiroirs Majencia (réf : Abidos)": 0.0, "Caisson de bureau 3 tiroirs": 0.0,
    "Caisson de bureau Dior 3 tiroirs": 0.0, "Caisson de bureau Kinnarp’s": 0.0, "Caisson de bureau Sedus": 0.0,
    "Caisson haut de bureau (réf : Abidos)": 0.0, "Coussins d’assise pour caisson": 0.0,
    "Caisson de rangement “tower” Steelcase": 0.0, "Tour latérale de bureau bicolore": 0.0,
    "Tour latérale de bureau blanche": 0.0, "Crédence de bureau Haworth": 0.0, "Vestiaire 3 portes": 0.0,
    "Vestiaire Métallique": 0.0, "Vestiaire métallique gris": 0.0, "Vestiaire, casier multicases à code": 0.0,
    "Vestiaire 4 “Porte Z”": 0.0, "Vestiaire 6 “Porte Z”": 0.0, "Rayonnage Professionnel": 0.0,
    "Alcôve / Isoloir / Coin Lecture": 0.0, "Alcôve de réunion 4 places": 0.0, "Alcôve Manufacture du Design": 0.0,
    "Espace de travail individuel Ahrend": 0.0, "Banque D’Accueil": 0.0, "Caisse garde meuble 8m3": 0.0,
    "claustra de restauration": 0.0, "Claustra perforé": 0.0, "Accueil grande taille": 0.0,
    "Lit simple Souvignet": 0.0, "Lit Mathou": 0.0, "Lit SoftLock Mathou": 0.0, "Lit CatLock Mathou": 0.0, "Lit métal": 0.0,
    "Distributeur de gel hydroalcoolique": 0.0, "Pétrin mélangeur": 0.0, "Mixeur turbo broyeur": 0.0,
    "Imprimante PRO SHARP MX 5112N": 0.0, "Liseuse LED": 0.0, "Tour PC HP Windows 10": 0.0,
    "our PC LENOVO": 0.0, "Multiprises – 3 prises avec interrupteur et ports USB-A et USB-C": 0.0,
    "Carrelage": 0.0, "Dalle de faux plafond acoustique": 0.0, "Dalle de faux plafond Artic 20mm": 0.0,
    "Dalle de faux plafond Blanka": 0.0, "Dalle de plafond acoustique Tonga bords A cobalt": 0.0,
    "Dalle de plafond Armstrong Metal": 0.0, "Dalle de plafond Artic": 0.0, "Dalle de plafond Rockfon Blanka": 0.0,
    "Dalle faux plafond All Cork": 0.0, "Porte pleine sans cadre": 0.0, "Profilés métalliques": 0.0,
    "Systèmes à galandage + châssis pour porte coulissante": 0.0,
    "Poubelle Tri Sélectif Rubbermaid": 0.0, "Classeurs 2 anneaux": 0.0, "Chevet": 0.0, "Commode": 0.0,
    "Couette 140 x 200 cm": 0.0, "Oreiller 55 x 55 cm": 0.0, "Rideau Occultant": 0.0, "Miroir rond": 0.0,
    "Pupitre de conférence": 0.0, "Triporteur": 0.0, "Porte manteau": 0.0, "Panetière": 0.0,
}

# --- CLASSE PDF ---
class AIMA_PDF(FPDF):
    def __init__(self, logo_path=None, doc_type="DEVIS"):
        super().__init__()
        self.logo_path = logo_path
        self.doc_type = doc_type

    def header(self):
        if self.logo_path and os.path.exists(self.logo_path): 
            self.image(self.logo_path, 20, 18, 42)
        self.set_font('Arial', 'B', 18)
        self.set_text_color(24, 73, 115)
        self.set_y(10)
        self.cell(0, 10, self.doc_type, 0, 1, 'C')
        self.ln(15)

    def footer(self):
        self.set_y(-30)
        self.set_font('Arial', 'I', 7.5); self.set_text_color(100, 100, 100)
        self.cell(0, 4, "TVA non applicable, Art. 261-7b du code général des impôts", 0, 1, 'C')
        self.cell(0, 4, "IBAN : FR90 2004 1010 0112 2207 4K02 259 BIC : PSSTFRPPBOR", 0, 1, 'C')
        self.cell(0, 4, "Association AIMA - Siege social : 1009 Route des Augas 64390 - Osserain-Rivareyte | SIRET : 508 544 715 00057", 0, 1, 'C')
        self.set_font('Arial', '', 7); self.cell(0, 4, f'Page {self.page_no()}', 0, 0, 'R')

    def draw_first_page_info(self, doc_num, ref_text, selected_date, client_name, client_address, aima_info, status, pay_mode):
        status_colors = {"En attente": (255, 193, 7), "Accepté": (40, 167, 69), "Refusé": (220, 53, 69)}
        color = status_colors.get(status, (128, 128, 128))
        self.set_xy(150, 28)
        self.set_font('Arial', 'B', 10); self.set_fill_color(*color); self.set_text_color(255, 255, 255)
        self.cell(50, 8, f"STATUT : {status.upper()}", 0, 1, 'C', True)

        y_boxes = 40
        self.set_fill_color(51, 139, 140); self.set_text_color(255, 255, 255); self.set_xy(10, y_boxes)
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
        # Ajout du mode de paiement dans le bloc d'informations
        info_text = f"{self.doc_type} N°: {doc_num}\nRéf: {ref_text}\nDate: {selected_date.strftime('%d/%m/%Y')}\nMode de paiement: {pay_mode}"
        self.multi_cell(65, 4.2, info_text, 1, 'L')
        return max(self.get_y(), y_right) + 5

# --- HELPERS ---
def delete_catalog_item(item_name):
    if item_name in st.session_state.catalog_selector: 
        st.session_state.catalog_selector.remove(item_name)
    st.session_state.active_catalog = [x for x in st.session_state.active_catalog if x['name'] != item_name]

def delete_manual_item(index): 
    st.session_state.manual_items_dict.pop(index)

def render_item_row(label, default_price, key_suffix, is_manual=False, index=0, mode="DEVIS"):
    col_info, col_img = st.columns([2, 1])
    with col_info:
        st.write(f"### {label}")
        c1, c2, c_extra, c3 = st.columns([1, 0.7, 1.3, 1.2])
        p = c1.number_input(f"P.U. (EUR)", value=float(default_price), format="%.2f", key=f"p_{key_suffix}")
        q = c2.number_input(f"Qté", min_value=1, value=1, key=f"q_{key_suffix}")
        
        extra_val = ""
        remise_amount = 0.0
        if mode == "DEVIS":
            extra_val = c_extra.selectbox("Lieu de stockage", options=LIEUX_ARTICLES, key=f"loc_{key_suffix}")
        else:
            extra_val = c_extra.number_input("Remise (%)", min_value=0, max_value=100, value=0, key=f"rem_{key_suffix}")
            remise_amount = (p * q) * (extra_val / 100)
            
        imgs = c3.file_uploader(f"Photos", type=["jpg","png"], accept_multiple_files=True, key=f"img_{key_suffix}")
        if is_manual: st.button("❌ Supprimer", key=f"del_{key_suffix}", on_click=delete_manual_item, args=(index,))
        else: st.button("❌ Supprimer", key=f"del_{key_suffix}", on_click=delete_catalog_item, args=(label,))
            
    with col_img:
        if imgs:
            sub_cols = st.columns(3)
            for idx, img in enumerate(imgs[:3]): sub_cols[idx].image(img, use_container_width=True)
    st.divider()
    
    row_total = (p * q) - remise_amount
        
    return {"Désignation": label, "P.U.": p, "Qté": q, "Total": row_total, "Extra": extra_val, "RemiseVal": remise_amount, "Images": imgs[:3] if imgs else []}, row_total

def reset_all():
    st.session_state.manual_items_dict = []
    st.session_state.active_catalog = []
    st.session_state.catalog_selector = []
    st.rerun()

# --- SIDEBAR ---
st.sidebar.header("📝 Paramètres")
doc_type = st.sidebar.selectbox("Type de document", ["DEVIS", "FACTURE"])
doc_status = st.sidebar.selectbox("État du suivi", ["En attente", "Accepté", "Refusé"])
# Ajout du choix du mode de paiement
pay_mode = st.sidebar.selectbox("Mode de paiement", options=MODES_PAIEMENT)

if st.sidebar.button("🔄 Réinitialiser tout"):
    reset_all()

suggested_num = get_next_number(doc_type)
d_num = st.sidebar.text_input(f"N° {doc_type}", value=suggested_num)

selected_loc_name = st.sidebar.selectbox("Lieu d'expédition", options=list(LOCATIONS.keys()))
loc_data = LOCATIONS[selected_loc_name]
aima_pdf_info = f"Le Hangar d'AIMA - {selected_loc_name}\n{loc_data['address']}\nTél : {loc_data['phone']}\nMail : {loc_data['email']}\nSIRET: 508 544 715 00057"

c_name = st.sidebar.text_input("Client", value="ONG- EPSPE")
c_addr = st.sidebar.text_area("Adresse Client", value="10 BP 1001 cotonou, Bénin")
d_ref = st.sidebar.text_input("Référence", value="AIMA-2026-INT")
d_date = st.sidebar.date_input("Date", value=date.today())

st.sidebar.divider()
include_adh = st.sidebar.checkbox(f"Cout adhesion annuelle {d_date.year} (1.00 EUR)", value=True)
include_liv = st.sidebar.checkbox("Livraison par nos soins", value=True)
liv_total = st.sidebar.number_input("Prix de la livraison (EUR)", value=0.0) if include_liv else 0.0

include_remise = st.sidebar.checkbox("Remise (Remboursement Avarie)", value=False)
montant_remise_avarie = st.sidebar.number_input("Montant de la remise / remboursement (EUR)", value=0.0) if include_remise else 0.0

st.markdown(f'<h1 style="color: #2c3e50;">AIMA - Générateur de {doc_type.capitalize()}</h1>', unsafe_allow_html=True)

# --- ARTICLES ---
selected_catalog = st.multiselect("📦 Sélectionner les dispositifs :", options=sorted(list(data_prices.keys())), key="catalog_selector")
items_to_pdf = []
total_global_items = 0.0
total_remise_articles = 0.0

st.session_state.active_catalog = [x for x in st.session_state.active_catalog if x['name'] in selected_catalog]
for item in selected_catalog:
    if item not in [x['name'] for x in st.session_state.active_catalog]:
        st.session_state.active_catalog.append({'name': item, 'price': data_prices.get(item, 0.0)})

for i, item_data in enumerate(st.session_state.active_catalog):
    res, price = render_item_row(item_data['name'], item_data['price'], f"cat_{i}", mode=doc_type)
    items_to_pdf.append(res)
    total_global_items += price
    total_remise_articles += res['RemiseVal']

st.subheader("➕ Article personnalisé")
m_cols = st.columns([2, 1, 1])
n_nom = m_cols[0].text_input("Désignation", key="manual_name")
n_prix = m_cols[1].number_input("Prix P.U.", min_value=0.0, format="%.2f", key="manual_price")
if m_cols[2].button("✅ Ajouter") and n_nom:
    st.session_state.manual_items_dict.append({"id": str(time.time()), "nom": n_nom, "prix": n_prix})
    st.rerun()

for i, m in enumerate(st.session_state.manual_items_dict):
    res, price = render_item_row(m['nom'], m['prix'], f"man_{m['id']}", is_manual=True, index=i, mode=doc_type)
    items_to_pdf.append(res)
    total_global_items += price
    total_remise_articles += res['RemiseVal']

grand_total = total_global_items + (1.0 if include_adh else 0.0) + (liv_total if include_liv else 0.0) - montant_remise_avarie
st.sidebar.markdown(f"### **TOTAL NET : {grand_total:,.2f} EUR**")

# --- GENERATION ---
if items_to_pdf:
    if st.button(f"📄 GÉNÉRER {doc_type} PDF"):
        pdf = AIMA_PDF(logo_path=AIMA_LOGO_PATH, doc_type=doc_type)
        pdf.add_page()
        # On passe pay_mode à la fonction de dessin
        y_pos = pdf.draw_first_page_info(d_num, d_ref, d_date, c_name, c_addr, aima_pdf_info, doc_status, pay_mode)
        
        if doc_type == "DEVIS":
            cols_w = [45, 17, 10, 18, 70, 30] 
            headers = ["Designation", "P.U.", "Qte", "Total", "Photos", "Lieu"]
        else:
            cols_w = [115, 17, 10, 18, 0, 30] 
            headers = ["Designation", "P.U.", "Qte", "Total", "", "Remise"]

        pdf.set_font('Arial', 'B', 8); pdf.set_fill_color(220, 220, 220); pdf.set_xy(10, y_pos)
        for i, h in enumerate(headers):
            if cols_w[i] > 0: pdf.cell(cols_w[i], 8, h, 1, 0, 'C', True)
        pdf.ln()

        pdf.set_font("Arial", '', 8)
        for row in items_to_pdf:
            nom_p = row['Désignation'].encode('latin-1', 'replace').decode('latin-1')
            nb_lines = len(pdf.multi_cell(cols_w[0]-2, 4, nom_p, split_only=True))
            h_row = max(nb_lines * 4 + 4, 32 if (doc_type == "DEVIS" and row['Images']) else 10)
            
            if pdf.get_y() + h_row > 240: pdf.add_page()
            y_c = pdf.get_y()
            pdf.rect(10, y_c, cols_w[0], h_row)
            pdf.set_xy(10, y_c + (h_row - (nb_lines * 4)) / 2)
            pdf.multi_cell(cols_w[0], 4, nom_p, 0, 'L')
            
            pdf.set_xy(10 + cols_w[0], y_c)
            pdf.cell(cols_w[1], h_row, f"{row['P.U.']:,.2f}", 1, 0, 'C')
            pdf.cell(cols_w[2], h_row, str(row['Qté']), 1, 0, 'C')
            pdf.cell(cols_w[3], h_row, f"{row['Total']:,.2f}", 1, 0, 'C')
            
            if doc_type == "DEVIS":
                img_x = pdf.get_x()
                pdf.cell(cols_w[4], h_row, "", 1, 0)
                if row['Images']:
                    for idx, img_file in enumerate(row['Images']):
                        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
                        with Image.open(img_file) as pimg:
                            if pimg.mode in ("RGBA", "P"): pimg = pimg.convert("RGB")
                            pimg.thumbnail((400, 400)); pimg.save(tmp.name, "JPEG")
                        pdf.image(tmp.name, img_x + 2 + (idx * 22), y_c + 2, w=20, h=h_row - 4)
                        os.remove(tmp.name)
                pdf.cell(cols_w[5], h_row, str(row['Extra']).encode('latin-1', 'replace').decode('latin-1'), 1, 1, 'C')
            else:
                rem_display = "" if row['Extra'] == 0 else f"{row['Extra']}%"
                pdf.cell(cols_w[5], h_row, rem_display, 1, 1, 'C')

        # --- FINAL BLOCK LAYOUT ---
        pdf.ln(5)
        if pdf.get_y() > 220: pdf.add_page()
        y_final = pdf.get_y()

        if doc_type == "FACTURE":
            x_offset = 120
            col_label_width = 50
            col_price_width = 30
        else:
            x_offset = 10
            col_label_width = 72
            col_price_width = 18

        pdf.set_font("Arial", '', 9)
        
        # Ligne Adhésion
        pdf.set_xy(x_offset, y_final)
        pdf.cell(col_label_width, 6, f"Cout adhesion annuelle {d_date.year}", 1, 0, 'L')
        pdf.cell(col_price_width, 6, "1.00 EUR" if include_adh else "0.00 EUR", 1, 1, 'R')

        # Ligne Livraison
        pdf.set_x(x_offset)
        pdf.cell(col_label_width, 6, "Livraison par nos soins", 1, 0, 'L')
        pdf.cell(col_price_width, 6, f"{liv_total:,.2f} EUR", 1, 1, 'R')

        # Ligne Remise (Articles + Remboursement Avarie)
        total_remise_a_afficher = total_remise_articles + montant_remise_avarie
        pdf.set_x(x_offset)
        pdf.cell(col_label_width, 6, "Remise", 1, 0, 'L')
        pdf.cell(col_price_width, 6, f"- {total_remise_a_afficher:,.2f} EUR" if total_remise_a_afficher > 0 else "0.00 EUR", 1, 1, 'R')

        # Ligne TOTAL NET
        pdf.set_x(x_offset)
        pdf.set_fill_color(51, 139, 140); pdf.set_text_color(255, 255, 255); pdf.set_font("Arial", 'B', 10)
        pdf.cell(col_label_width, 8, "TOTAL NET", 1, 0, 'C', True)
        pdf.set_text_color(0, 0, 0); pdf.cell(col_price_width, 8, f"{grand_total:,.2f} EUR", 1, 1, 'R')

        # --- SIGNATURE BOX (ONLY FOR DEVIS) ---
        if doc_type == "DEVIS":
            pdf.set_xy(115, y_final) 
            pdf.set_font("Arial", 'B', 8)
            pdf.cell(85, 6, "Signature et cachet :", 1, 1, 'L')
            pdf.set_x(115)
            pdf.cell(85, 20, "", 1, 1)
            
        full_path = os.path.join(TARGET_FOLDER, f"{doc_type}_{d_num}.pdf")
        pdf.output(full_path)
        increment_counter(doc_type)
        st.success(f"✅ Sauvegardé : {full_path}")
        st.download_button(f"💾 Télécharger {doc_type}", open(full_path, "rb"), f"{doc_type}_{d_num}.pdf")
