# -*- coding: utf-8 -*-
import streamlit as st
from fpdf import FPDF
from datetime import date
import os
import tempfile
import time
import sys
from PIL import Image

# --- CONFIGURATION INITIALE ---
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

AIMA_LOGO_PATH = resource_path("aima_logo.png")
#AIMA_LOGO_PATH = "C:/Users/perso/Desktop/aima_logo.png"

st.set_page_config(layout="wide", page_title="AIMA - Gestion de Devis")

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



# Chemin du logo (à adapter selon votre PC)
if os.path.exists("aima_logo.png"):
    AIMA_LOGO_PATH = "aima_logo.png"
else:
    AIMA_LOGO_PATH = "C:/Users/perso/Desktop/aima_logo.png" 

st.set_page_config(layout="wide", page_title="AIMA - Gestion Médicale")

# --- DICTIONNAIRE DE TRADUCTION ---
LANG = {
    "FR": {
        "title": "AIMA - Gestion de Devis & Factures Médicales",
        "settings": "📝 Paramètres",
        "type": "Type de document",
        "status": "STATUT",
        "payment": "Paiement",
        "reset": "Réinitialiser tout",
        "date": "Date du document",
        "by": "Réalisé par",
        "loc": "Lieu d'expédition",
        "client": "Client",
        "address": "Adresse",
        "doc_num": "N° Document",
        "ref": "Référence",
        "select_items": "📦 Sélectionner dispositifs :",
        "add_custom": "➕ Ajouter un article personnalisé",
        "designation": "Désignation",
        "price": "Prix (EUR)",
        "pu": "P.U. (EUR)",
        "qty": "Qté",
        "total": "Total",
        "total_net": "TOTAL NET",
        "generate": "📄 GÉNÉRER",
        "download": "💾 Télécharger",
        "photos": "Photos",
        "import_title": "📥 Importer et Modifier un PDF existant",
        "import_help": "Glissez un ancien PDF AIMA ici",
        "footer_tva": "TVA non applicable, Art. 261-7b du code général des impôts",
        "dest": "DESTINATAIRE"
    },
    "EN": {
        "title": "AIMA - Medical Quote & Invoice Management",
        "settings": "📝 Settings",
        "type": "Document Type",
        "status": "STATUS",
        "payment": "Payment",
        "reset": "Reset All",
        "date": "Document Date",
        "by": "Prepared by",
        "loc": "Shipping Location",
        "client": "Client",
        "address": "Address",
        "doc_num": "Document No.",
        "ref": "Reference",
        "select_items": "📦 Select equipment:",
        "add_custom": "➕ Add custom item",
        "designation": "Description",
        "price": "Price (EUR)",
        "pu": "U.P. (EUR)",
        "qty": "Qty",
        "total": "Total",
        "total_net": "TOTAL NET",
        "generate": "GENERATE",
        "download": "💾 Download",
        "photos": "Photos",
        "import_title": "📥 Import and Edit existing PDF",
        "import_help": "Drop an old AIMA PDF here",
        "footer_tva": "VAT not applicable, Art. 261-7b of the General Tax Code",
        "dest": "BILL TO"
    }
}

# --- INITIALISATION SESSION STATE ---
if 'manual_items_dict' not in st.session_state:
    st.session_state.manual_items_dict = []
if 'active_catalog' not in st.session_state:
    st.session_state.active_catalog = []
if 'catalog_selector' not in st.session_state:
    st.session_state.catalog_selector = []

# --- CALLBACKS ---
def reset_app():
    st.session_state.manual_items_dict = []
    st.session_state.active_catalog = []
    st.session_state.catalog_selector = []
    st.rerun()

def delete_catalog_item(item_name):
    if item_name in st.session_state.catalog_selector:
        st.session_state.catalog_selector.remove(item_name)
    st.session_state.active_catalog = [x for x in st.session_state.active_catalog if x['name'] != item_name]

def delete_manual_item(index):
    st.session_state.manual_items_dict.pop(index)

# --- DONNÉES MÉDICALES ---
data_prices = {
    "Abaisse-langue": [0, 1.5], "Anuscope": [0, 5], "Appareil de photothérapie": [45, 400],
    "Aspirateur à mucosités": [30, 150], "Aspirateur chirurgical": [30, 200], "Bain thermostaté": [30, 50],
    "Baquet roulant": [0, 5], "Béquille - Canne": [0, 5], "Berceau": [0, 30],
    "Bistouri électrique": [90, 300], "Boîte à instruments - Boîte de stérilisation": [0, 60],
    "Brancard simple": [0, 25], "Brancard sur chariot roulant": [0, 150], "Centrifugeuse": [60, 300],
    "Capnographe": [45, 80], "Cardiotocographe": [45, 400], "Chaise percée - Chaise pot": [0, 10],
    "Chambre d'inhalation": [0, 7.5], "Chariot médical": [0, 25], "Colposcope": [15, 500],
    "Concentrateur d’oxygène": [30, 250], "Consommable à usage unique": [0, 0.5],
    "Conteneur - Tambour de stérilisation": [0, 12.5], "Cupule": [0, 1.5],
    "Cuve-Bac à ultrasons pour nettoyage d'instruments": [15, 150], "Déambulateur": [0, 5],
    "Défibrillateur manuel": [60, 350], "Défibrillateur semi-automatique": [30, 250],
    "Dispositif d'immobilisation, d'ergothérapie (ex : attelle)": [0, 5], "Doppler": [30, 25],
    "Échographe": [120, 1500], "Échographe de type bladder scan": [30, 300],
    "Éclairage opératoire - Scialytique": [60, 500], "Électrocardiographe": [60, 250],
    "Étuve": [30, 50], "Fauteuil de dialyse": [0, 50], "Fauteuil de prélèvement": [0, 50],
    "Fauteuil roulant": [0, 50], "Garrot": [0, 5], "Garrot électrique": [30, 150],
    "Glucomètre": [0, 2.5], "Haricot": [0, 5], "Incubateur de néonatalogie fermé - Couveuse": [120, 400],
    "Incubateur de néonatalogie ouvert - Table de réanimation": [120, 400],
    "Instrumentation (Chirurgie/Gynéco/ORL/Ortho/etc.)": [0, 4], "Insufflateur manuel": [0, 25],
    "Lampe d’examen": [15, 50], "Laryngoscope": [15, 37.5], "Littérature médicale": [0, 0],
    "Lève-malade - Sangle lève-personne": [15, 17.5], "Lunettes - Montures": [0, 2.5],
    "Marteau à réflexes": [0, 5], "Masque facial pour ventilation-insufflation": [0, 5],
    "Microscope de paillasse": [30, 150], "Microscope opératoire": [60, 1100],
    "Mobilier hospitalier": [0, 25], "Moniteur 3 paramètres (ECG, SpO2, PNI)": [90, 350],
    "Moniteur 2 paramètres (SpO2, PNI)": [60, 250], "Moteur orthopédique": [30, 1000],
    "Nébuliseur": [30, 20], "Négatoscope": [15, 25], "Otoscope": [15, 15],
    "Oxymètre de pouls - Saturo-mètre": [30, 80], "Panier à instruments / stérilisation": [0, 5],
    "Paravent": [0, 20], "Pèse-bébé (manuel ou électronique)": [15, 20], "Pèse-personne": [0, 10],
    "Pied à sérum - Potence": [0, 12.5], "Pissette": [0, 2.5], "Plateau à instruments": [0, 2.5],
    "Poire à lavement": [0, 2.5], "Pompe d’auto-analgésie": [45, 100], "Pompe à nutrition entérale": [45, 75],
    "Pompe à perfusion": [45, 120], "Pompe à pousse-seringue": [45, 100], "Rampe chauffante": [30, 120],
    "Rampe de photothérapie": [30, 200], "Rehausseur WC / Siège de bain": [0, 5],
    "Spéculum gynécologique": [0, 4], "Spiromètre": [0, 10], "Stérilisateur à chaleur humide - Autoclave": [90, 600],
    "Stérilisateur à chaleur sèche - Poupinel": [45, 50], "Stéthoscope": [0, 5],
    "Table d'accouchement": [0, 200], "Table d'opération (manuelle/électrique)": [45, 1250],
    "Table de réanimation néonatale": [90, 90], "Table - Divan - Lit d'examen": [0, 175],
    "Tensiomètre automatique - Moniteur PNI": [30, 200], "Tensiomètre manuel - Sphygmomanomètre": [0, 5],
    "Tenues de soins et de bloc opératoire": [0, 5], "Thermo-soudeuse": [30, 50],
    "Tire-lait électrique": [15, 5], "Urinal - Bassin de lit": [0, 1.5],
    "Ventilateur d’anesthésie (sans halogénés)": [120, 1500], "Ventilateur d’anesthésie (avec cuve halogénés)": [120, 2000],
    "Ventilateur de réanimation / Artificielle": [120, 1200], "Ventilateur de soins intensifs": [120, 1200],
    "Ventilateur d’urgence": [60, 750], "Verticalisateur": [15, 175]
}

LOCATIONS = {
    "SALIES-DE-BÉARN": {
        "name": "Association AIMA",
        "sub_name": "Le Hangar d'AIMA Humanitaire et Medical",
        "address": "10 avenue des Salines, 64270 Salies-de-Bearn",
        "phone": "+33 6 09 93 97 25",
        "email": "international@assoaima.org",
        "SIRET": "508 544 715 00057"
    },
}

# --- SIDEBAR ---
st.sidebar.header("🌍 Language / Langue")
lang_choice = st.sidebar.radio("Select Language", ["FR", "EN"], horizontal=True)
T = LANG[lang_choice]

st.sidebar.header(T['settings'])
doc_type = st.sidebar.selectbox(T['type'], ["DEVIS", "FACTURE"])

# État du suivi avec options traduites
status_options = ["EN ATTENTE", "ACCEPTÉ", "LIVRÉ", "PAYÉ", "ANNULÉ"] if lang_choice == "FR" else ["PENDING", "ACCEPTED", "SHIPPED", "PAID", "CANCELLED"]
doc_status = st.sidebar.selectbox(T['status'], status_options)

realized_by = st.sidebar.text_input(T['by'], value="Equipe AIMA")

payment_options = ["Virement Bancaire", "Espèces", "Chèque"] if lang_choice == "FR" else ["Bank Transfer", "Cash", "Check", ]
payment_method = st.sidebar.selectbox(T['payment'], payment_options)

if st.sidebar.button(f"🔄 {T['reset']}", use_container_width=True):
    reset_app()

st.sidebar.divider()
doc_date = st.sidebar.date_input(T['date'], value=date.today())
selected_loc = st.sidebar.selectbox(T['loc'], options=list(LOCATIONS.keys()))
loc_data = LOCATIONS[selected_loc]

c_name = st.sidebar.text_input(T['client'], value="")
c_addr = st.sidebar.text_area(T['address'], value="")
default_d_num = f"2026-MED-0331" if doc_type == "FACTURE" else f"2026-MED-001"
d_num = st.sidebar.text_input(T['doc_num'], value=default_d_num)
d_ref = st.sidebar.text_input(T['ref'], value="AIMA-2026-INT")

# --- PDF ENGINE ---
class AIMA_PDF(FPDF):
    def __init__(self, logo_path=None, doc_type="DEVIS", lang_dict=None):
        super().__init__()
        self.logo_path = logo_path
        self.doc_type = doc_type
        self.T = lang_dict

    def header(self):
        if self.logo_path and os.path.exists(self.logo_path): 
            self.image(self.logo_path, 20, 18, 42)
        self.set_font('Arial', 'B', 18); self.set_text_color(24, 73, 115)
        self.set_y(10); 
        label = "QUOTE" if (self.doc_type == "DEVIS" and self.T == LANG["EN"]) else ("INVOICE" if (self.doc_type == "FACTURE" and self.T == LANG["EN"]) else self.doc_type)
        self.cell(0, 10, label, 0, 1, 'C')
        self.ln(25 if self.page_no() == 1 else 35)

    def footer(self):
        self.set_y(-30)
        self.set_font('Arial', 'I', 7.5); self.set_text_color(100, 100, 100)
        self.cell(0, 4, self.T['footer_tva'], 0, 1, 'C')
        self.cell(0, 4, "IBAN : FR90 2004 1010 0112 2207 4K02 259 BIC : PSSTFRPPBOR", 0, 1, 'C')
        self.cell(0, 4, "Association AIMA - Siege social : 1009 Route des Augas 64390 - Osserain-Rivareyte | SIRET : 508 544 715 00057", 0, 1, 'C')
        self.set_font('Arial', '', 7); self.cell(0, 4, f'Page {self.page_no()}', 0, 0, 'R')

    def draw_info_blocks(self, doc_num, ref_text, selected_date, client_name, client_address, aima_info, realized_by, payment, status):
        # --- CODE COULEUR DU STATUT ---
        status_colors = {
            "ACCEPTÉ": (40, 167, 69), "ACCEPTED": (40, 167, 69),
            "PAYÉ": (0, 123, 255), "PAID": (0, 123, 255),
            "ANNULÉ": (220, 53, 69), "CANCELLED": (220, 53, 69),
            "EN ATTENTE": (255, 193, 7), "PENDING": (255, 193, 7),
            "LIVRÉ": (23, 162, 184), "SHIPPED": (23, 162, 184)
        }
        bg_color = status_colors.get(status.upper(), (108, 117, 125))

        # --- DESSIN DU STATUT (COIN SUPÉRIEUR DROIT) ---
        self.set_xy(140, 12)
        self.set_font('Arial', 'B', 11)
        self.set_fill_color(*bg_color)
        self.set_text_color(255, 255, 255)
        self.cell(60, 8, f"{self.T['status']} : {status.upper()}", 0, 0, 'C', True)
        self.set_text_color(0, 0, 0) # Reset

        y_boxes = 38
        # Bloc Fournisseur
        self.set_xy(10, y_boxes)
        self.set_fill_color(51, 139, 140); self.set_text_color(255, 255, 255)
        self.set_font('Arial', 'B', 9); self.cell(80, 7, "Association AIMA", 1, 1, 'C', True)
        self.set_text_color(0, 0, 0); self.set_font('Arial', '', 8); self.set_x(10)
        self.rect(10, y_boxes + 7, 80, 20)
        self.multi_cell(80, 4, aima_info.encode('latin-1', 'replace').decode('latin-1'), 0, 'C')
        
        # Bloc Destinataire
        self.set_xy(120, y_boxes)
        self.set_fill_color(51, 139, 140); self.set_text_color(255, 255, 255)
        self.rect(120, y_boxes, 80, 7)
        self.cell(80, 7, f"{self.T['dest']} : {client_name.upper()}".encode('latin-1', 'replace').decode('latin-1'), 0, 1, 'C', True)
        self.set_text_color(0, 0, 0); self.set_font('Arial', '', 9); self.set_x(120)
        self.rect(120, y_boxes + 7, 80, 15)
        self.multi_cell(80, 5, client_address.encode('latin-1', 'replace').decode('latin-1'), 0, 'C')
        
        # Bloc Métadonnées
        y_meta = y_boxes + 30
        self.set_xy(10, y_meta)
        self.set_font('Arial', '', 8.5)
        type_label = "QUOTE" if (self.doc_type == "DEVIS" and self.T == LANG["EN"]) else ("INVOICE" if (self.doc_type == "FACTURE" and self.T == LANG["EN"]) else self.doc_type)
        by_label = "Prepared by" if self.T == LANG["EN"] else "Réalisé par"
        
        info_text = (f"{type_label} N°: {doc_num}\n"
                    f"Ref: {ref_text}\n"
                    f"Date: {selected_date.strftime('%d/%m/%Y')}\n"
                    f"{by_label}: {realized_by}\n"
                    f"{self.T['payment']}: {payment}")
        
        self.rect(10, y_meta, 75, 22)
        self.multi_cell(75, 4.2, info_text.encode('latin-1', 'replace').decode('latin-1'), 0, 'L')
        return self.get_y() + 5

# --- FONCTION RENDU LIGNE ARTICLE ---
def render_item_row(label, default_price_list, key_suffix, T_dict, is_manual=False, index=0, mode="DEVIS"):
    initial_p = float(sum(default_price_list)) if isinstance(default_price_list, list) else float(default_price_list)
    col_info, col_img, col_preview = st.columns([2.2, 0.6, 1.2])
    
    with col_info:
        st.markdown(f"#### {label}")
        c_price, c_qty, c_extra = st.columns([1, 0.6, 1.5])
        p = c_price.number_input(T_dict['pu'], value=initial_p, min_value=0.0, step=1.0, key=f"p_{key_suffix}")
        q = c_qty.number_input(T_dict['qty'], min_value=1, value=1, key=f"q_{key_suffix}")
        imgs = None
        if mode == "DEVIS":
            imgs = c_extra.file_uploader(T_dict['photos'], type=["jpg","png"], accept_multiple_files=True, key=f"i_{key_suffix}")
        if is_manual: 
            st.button("🗑️", key=f"del_{key_suffix}", on_click=delete_manual_item, args=(index,))
        else: 
            st.button("🗑️", key=f"del_{key_suffix}", on_click=delete_catalog_item, args=(label,))
    
    total_net = p * q
    with col_img:
        st.markdown(f"<p style='font-size: 14px; margin-bottom: 0;'>{T_dict['total']}</p>", unsafe_allow_html=True)
        st.subheader(f"{total_net:,.2f}")
        st.caption("EUR")
    
    with col_preview:
        if mode == "DEVIS" and imgs:
            thumb_cols = st.columns(3)
            for idx, img_file in enumerate(imgs[:3]):
                with thumb_cols[idx]: st.image(img_file, use_container_width=True) 
    
    st.divider()
    return {"Désignation": label, "P.U.": p, "Qté": q, "Total": total_net, "Images": imgs[:3] if imgs else []}, total_net

# --- INTERFACE PRINCIPALE ---
st.markdown(f'<h1 style="color: #244973;">{T["title"]}</h1>', unsafe_allow_html=True)

# Expander Import PDF
with st.expander(f"### {T['import_title']}"):
    uploaded_pdf = st.file_uploader(T['import_help'], type=["pdf"], key="pdf_importer")
    if uploaded_pdf is not None:
        try:
            import pdfplumber
            with pdfplumber.open(uploaded_pdf) as pdf_file:
                table = pdf_file.pages[0].extract_table()
                if table:
                    st.session_state.active_catalog, st.session_state.manual_items_dict, st.session_state.catalog_selector = [], [], []
                    for row in table[1:]:
                        if row and row[0]:
                            name = row[0].split('\n')[0].strip()
                            try:
                                raw_p = row[1].replace('EUR', '').replace(',', '').strip()
                                price = float(raw_p)
                                qty = int(row[2])
                            except: price, qty = 0.0, 1
                            if name in data_prices:
                                st.session_state.catalog_selector.append(name)
                                st.session_state.active_catalog.append({'name': name, 'price': [0, price]})
                            else:
                                st.session_state.manual_items_dict.append({"id": time.time(), "nom": name, "prix": [0, price]})
                    st.success("✅ Import réussi !")
        except Exception as e: st.error(f"Erreur : {e}")

# Sélection articles catalogue
selected_catalog = st.multiselect(T['select_items'], options=sorted(list(data_prices.keys())), key="catalog_selector")

# Ajout article personnalisé
with st.expander(T['add_custom']):
    cx1, cx2, cx3 = st.columns([3, 1, 1])
    new_n = cx1.text_input(T['designation'])
    new_p = cx2.number_input(T['price'], min_value=0.0)
    if cx3.button("Ajouter"):
        if new_n:
            st.session_state.manual_items_dict.append({"id": time.time(), "nom": new_n, "prix": [0, new_p]})
            st.rerun()

# --- CALCUL ET RENDU DES ARTICLES ---
items_to_pdf = []
total_items = 0.0

# Mise à jour du catalogue actif
st.session_state.active_catalog = [x for x in st.session_state.active_catalog if x['name'] in selected_catalog]
for item in selected_catalog:
    if item not in [x['name'] for x in st.session_state.active_catalog]:
        st.session_state.active_catalog.append({'name': item, 'price': data_prices.get(item, [0, 0])})

# Rendu Catalogue
for i, item_data in enumerate(st.session_state.active_catalog):
    res, price = render_item_row(item_data['name'], item_data['price'], f"cat_{i}", T, mode=doc_type)
    items_to_pdf.append(res); total_items += price

# Rendu Manuel
for i, m in enumerate(st.session_state.manual_items_dict):
    res, price = render_item_row(m['nom'], m['prix'], f"man_{m['id']}", T, is_manual=True, index=i, mode=doc_type)
    items_to_pdf.append(res); total_items += price

grand_total = total_items
st.sidebar.markdown(f"## {T['total_net']} : {grand_total:,.2f} EUR")

# --- BOUTON GÉNÉRATION PDF ---
if items_to_pdf and st.button(f"{T['generate']} {doc_type} PDF"):
    pdf = AIMA_PDF(logo_path=AIMA_LOGO_PATH, doc_type=doc_type, lang_dict=T)
    pdf.add_page()
    aima_info = f"{loc_data['sub_name']}\n{loc_data['address']}\nTel: {loc_data['phone']}\nMail: {loc_data['email']}\nSIRET: {loc_data['SIRET']}"
    
    # Dessin des blocs d'entête (Statut inclus)
    y_pos = pdf.draw_info_blocks(d_num, d_ref, doc_date, c_name, c_addr, aima_info, realized_by, payment_method, doc_status)
    
    # Headers du tableau
    if doc_type == "FACTURE":
        cols_w = [115, 30, 15, 30] 
        headers = [T['designation'], T['pu'], T['qty'], T['total'] + " EUR"]
    else: 
        cols_w = [65, 20, 10, 23, 72] 
        headers = [T['designation'], T['pu'], T['qty'], T['total'] + " EUR", T['photos']]

    pdf.set_font('Arial', 'B', 9); pdf.set_fill_color(220, 220, 220); pdf.set_xy(10, y_pos)
    for i, h in enumerate(headers): pdf.cell(cols_w[i], 8, h.encode('latin-1', 'replace').decode('latin-1'), 1, 0, 'C', True)
    pdf.ln()

    # Contenu du tableau
    pdf.set_font("Arial", '', 9)
    for row in items_to_pdf:
        h_row = 8 if doc_type == "FACTURE" else (32 if row['Images'] else 12)
        if pdf.get_y() + h_row > 260: pdf.add_page()
        y_start = pdf.get_y()
        
        pdf.set_xy(10, y_start + 2)
        pdf.multi_cell(cols_w[0], 4, row['Désignation'].encode('latin-1','replace').decode('latin-1'), 0, 'L')
        
        pdf.set_xy(10 + cols_w[0], y_start)
        pdf.cell(cols_w[1], 8, f"{row['P.U.']:,.2f}", 0, 0, 'C')
        pdf.cell(cols_w[2], 8, str(row['Qté']), 0, 0, 'C')
        pdf.cell(cols_w[3], 8, f"{row['Total']:,.2f}", 0, 0, 'C')
        
        if doc_type == "DEVIS" and row['Images']:
            img_x = 10 + sum(cols_w[:4])
            for idx, img_f in enumerate(row['Images'][:3]):
                with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
                    with Image.open(img_f) as pimg:
                        if pimg.mode != "RGB": pimg = pimg.convert("RGB")
                        pimg.save(tmp.name, "JPEG")
                    pdf.image(tmp.name, img_x + 2 + (idx*22), y_start + 2, h=h_row-4)
                os.remove(tmp.name)

        # Dessin des bordures
        cx = 10
        for w in cols_w:
            pdf.rect(cx, y_start, w, h_row)
            cx += w
        pdf.set_y(y_start + h_row)

    # Résumé Total
    pdf.ln(5); summary_x = 10 + sum(cols_w) - 85; pdf.set_xy(summary_x, pdf.get_y())
    pdf.set_fill_color(51, 139, 140); pdf.set_text_color(255, 255, 255); pdf.set_font("Arial", 'B', 10)
    pdf.cell(60, 10, T['total_net'], 1, 0, 'C', True)
    pdf.set_text_color(0, 0, 0); pdf.cell(25, 10, f"{grand_total:,.2f} EUR", 1, 1, 'C')

    # Sortie PDF
    pdf_bytes = pdf.output(dest='S').encode('latin-1', 'replace')
    st.download_button(f"{T['download']} {doc_type}", pdf_bytes, f"{d_num}.pdf", "application/pdf")
