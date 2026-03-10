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

# --- CONFIGURATION INITIALE ---
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# Remplacez par le chemin réel de votre logo
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

# Catalogue simplifié pour l'exemple (à compléter selon vos besoins)
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
    "Pupitre de conférence": 0.0, "Triporteur": 0.0, "Porte manteau": 0.0, "Panetière": 0.0
}

# --- SESSION STATE ---
if 'manual_items_dict' not in st.session_state: st.session_state.manual_items_dict = []
if 'active_catalog' not in st.session_state: st.session_state.active_catalog = []
if 'catalog_selector' not in st.session_state: st.session_state.catalog_selector = []

# --- FONCTION IMPORT PDF (REVERSE) ---
def import_items_from_pdf(uploaded_pdf):
    try:
        new_items = []
        with pdfplumber.open(uploaded_pdf) as pdf:
            for page in pdf.pages:
                table = page.extract_table()
                if table:
                    for row in table:
                        if not row or "Designation" in str(row[0]) or "TOTAL" in str(row[0]):
                            continue
                        try:
                            nom = str(row[0]).strip().replace('\n', ' ')
                            prix_str = str(row[1]).replace(' ', '').replace('€', '').replace(',', '.')
                            prix = float(prix_str)
                            new_items.append({"id": str(time.time())+nom, "nom": nom, "prix": prix})
                        except:
                            continue
        return new_items
    except Exception as e:
        st.error(f"Erreur d'importation : {e}")
        return []

# --- CALLBACKS ---
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
            self.image(self.logo_path, 10, 10, 38)
        self.set_font('Arial', 'B', 12); self.set_text_color(24, 73, 115)
        self.set_xy(100, 10)
        title = f"{self.doc_type} D'EQUIPEMENT MOBILIER ET MATERIEL"
        self.cell(100, 8, title.encode('latin-1', 'replace').decode('latin-1'), 0, 1, 'R')
        self.ln(20)

    def footer(self):
        self.set_y(-25)
        self.set_font('Arial', 'I', 7.5); self.set_text_color(100, 100, 100)
        self.cell(0, 4, "TVA non applicable, Art. 261-7b du code général des impôts".encode('latin-1', 'replace').decode('latin-1'), 0, 1, 'C')
        self.cell(0, 4, "IBAN: FR90 2004 1010 0112 2207 4K02 259 | SIRET: 508 544 715 00057", 0, 1, 'C')
        self.cell(0, 4, f'Page {self.page_no()}', 0, 0, 'R')

    def draw_info_blocks(self, doc_num, ref_text, selected_date, client_name, client_address, aima_info, status):
        # Badge Statut
        self.set_xy(150, 25); self.set_font('Arial', 'B', 10)
        self.set_fill_color(255, 193, 7); self.set_text_color(255, 255, 255)
        self.cell(50, 8, f"STATUT : {status.upper()}", 0, 1, 'C', True)

        # Blocs Adresses
        y_pos = 40
        self.set_xy(10, y_pos); self.set_font('Arial', 'B', 9); self.set_fill_color(51, 139, 140); self.set_text_color(255, 255, 255)
        self.cell(80, 7, "Association AIMA", 1, 1, 'C', True)
        self.set_font('Arial', '', 8); self.set_text_color(0, 0, 0); self.set_x(10)
        self.multi_cell(80, 4, aima_info.encode('latin-1', 'replace').decode('latin-1'), 1, 'C')
        y_aima = self.get_y()
        
        self.set_xy(115, y_pos); self.set_fill_color(51, 139, 140); self.set_text_color(255, 255, 255)
        self.cell(85, 7, f"DESTINATAIRE : {client_name.upper()}", 1, 1, 'C', True)
        self.set_font('Arial', '', 9); self.set_text_color(0, 0, 0); self.set_x(115)
        self.multi_cell(85, 5, client_address.encode('latin-1', 'replace').decode('latin-1'), 1, 'C')
        y_client = self.get_y()
        
        self.set_xy(10, y_aima + 3); self.set_font('Arial', '', 8.5)
        info_doc = f"{self.doc_type} N°: {doc_num}\nRef: {ref_text}\nDate: {selected_date.strftime('%d/%m/%Y')}"
        self.multi_cell(60, 4.5, info_doc.encode('latin-1', 'replace').decode('latin-1'), 1, 'L')
        return max(self.get_y(), y_client) + 5

# --- INTERFACE DE LIGNE D'ARTICLE ---
def render_item_row(label, default_price, key_suffix, is_manual=False, index=0):
    col_info, col_img = st.columns([2, 1])
    with col_info:
        st.markdown(f"**{label}**")
        c1, c2, c3, c4 = st.columns([1, 0.6, 1, 1])
        p = c1.number_input(f"P.U. (€)", value=float(default_price), key=f"p_{key_suffix}")
        q = c2.number_input(f"Qté", min_value=1, value=1, key=f"q_{key_suffix}")
        l = c3.selectbox("Lieu", options=LIEUX_ARTICLES, key=f"loc_{key_suffix}")
        if is_manual: 
            st.button("🗑️", key=f"del_{key_suffix}", on_click=delete_manual_item, args=(index,))
        else: 
            st.button("🗑️", key=f"del_{key_suffix}", on_click=delete_catalog_item, args=(label,))
    with col_img:
        imgs = st.file_uploader(f"Photos", type=["jpg","png"], accept_multiple_files=True, key=f"img_{key_suffix}")
        if imgs: st.image(imgs[0], width=100)
    st.divider()
    return {"Désignation": label, "P.U.": p, "Qté": q, "Total": p*q, "Lieu": l, "Images": imgs[:3] if imgs else []}, (p * q)

# --- STREAMLIT UI ---
st.sidebar.header("📝 Paramètres")
doc_type = st.sidebar.selectbox("Document", ["DEVIS", "FACTURE"])
doc_status = st.sidebar.selectbox("Statut", ["En attente", "Accepté", "Refusé"])
selected_loc_name = st.sidebar.selectbox("Lieu d'expédition", options=list(LOCATIONS.keys()))
loc_data = LOCATIONS[selected_loc_name]

aima_pdf_info = f"Le Hangar d'AIMA - {selected_loc_name}\n{loc_data['address']}\nTél : {loc_data['phone']}\nMail : {loc_data['email']}"

c_name = st.sidebar.text_input("Client", value="ONG-EPSPE")
c_addr = st.sidebar.text_area("Adresse Client", value="Cotonou, Bénin")
d_num = st.sidebar.text_input("N° Document", value="2026-001")
d_ref = st.sidebar.text_input("Référence", value="AIMA-2026")
d_date = st.sidebar.date_input("Date", value=date.today())

st.sidebar.divider()
include_adh = st.sidebar.checkbox("Adhésion (1€)", value=True)
liv_total = st.sidebar.number_input("Frais livraison (€)", value=0.0)

# Import PDF
st.markdown("### 📥 Importer un PDF")
up_file = st.file_uploader("Charger articles depuis un ancien PDF", type="pdf")
if up_file and st.button("Extraire Articles"):
    items = import_items_from_pdf(up_file)
    st.session_state.manual_items_dict.extend(items)
    st.rerun()

# Sélection Catalogue
selected_catalog = st.multiselect("📦 Catalogue :", options=sorted(list(data_prices.keys())), key="catalog_selector")
items_to_pdf = []
total_items = 0.0

# Construction de la liste active
st.session_state.active_catalog = [{"name": n, "price": data_prices[n]} for n in selected_catalog]

for i, item in enumerate(st.session_state.active_catalog):
    res, price = render_item_row(item['name'], item['price'], f"cat_{i}")
    items_to_pdf.append(res); total_items += price

st.subheader("➕ Article Personnalisé")
col_n, col_p, col_b = st.columns([2,1,1])
n_nom = col_n.text_input("Nom de l'article")
n_prix = col_p.number_input("Prix", min_value=0.0)
if col_b.button("Ajouter") and n_nom:
    st.session_state.manual_items_dict.append({"id": str(time.time()), "nom": n_nom, "prix": n_prix})
    st.rerun()

for i, m in enumerate(st.session_state.manual_items_dict):
    res, price = render_item_row(m['nom'], m['prix'], f"man_{i}", is_manual=True, index=i)
    items_to_pdf.append(res); total_items += price

# --- GÉNÉRATION ---
grand_total = total_items + (1.0 if include_adh else 0.0) + liv_total
st.sidebar.markdown(f"## TOTAL : {grand_total:.2f} €")

if items_to_pdf and st.button(f"📄 GÉNÉRER LE PDF"):
    pdf = AIMA_PDF(logo_path=AIMA_LOGO_PATH, doc_type=doc_type)
    pdf.add_page()
    y_table = pdf.draw_info_blocks(d_num, d_ref, d_date, c_name, c_addr, aima_pdf_info, doc_status)
    
    # Header Tableau
    w = [100, 18, 10, 18, 44] if doc_type == "DEVIS" else [115, 20, 10, 20, 30]
    headers = ["Designation", "P.U.", "Qte", "Total", "Photos/Lieu"]
    pdf.set_xy(10, y_table); pdf.set_font('Arial', 'B', 8); pdf.set_fill_color(230, 230, 230)
    for i, h in enumerate(headers): pdf.cell(w[i], 8, h, 1, 0, 'C', True)
    pdf.ln()

    # Lignes
    pdf.set_font('Arial', '', 8)
    for row in items_to_pdf:
        h_row = 25 if (doc_type == "DEVIS" and row['Images']) else 10
        if pdf.get_y() + h_row > 260: pdf.add_page()
        
        curr_y = pdf.get_y()
        pdf.rect(10, curr_y, w[0], h_row)
        pdf.set_xy(10, curr_y); pdf.multi_cell(w[0], 5, row['Désignation'].encode('latin-1','replace').decode('latin-1'), 0, 'L')
        
        pdf.set_xy(10+w[0], curr_y)
        pdf.cell(w[1], h_row, f"{row['P.U.']:.2f}", 1, 0, 'C')
        pdf.cell(w[2], h_row, str(row['Qté']), 1, 0, 'C')
        pdf.cell(w[3], h_row, f"{row['Total']:.2f}", 1, 0, 'C')
        
        # Images et Lieu
        img_x = pdf.get_x()
        pdf.cell(w[4], h_row, "", 1, 1)
        if row['Images'] and doc_type == "DEVIS":
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
            with Image.open(row['Images'][0]) as img:
                img.convert("RGB").save(tmp.name)
            pdf.image(tmp.name, img_x + 2, curr_y + 2, h=h_row-4)
            os.remove(tmp.name)

    # Totaux et Signature
    pdf.ln(5)
    y_f = pdf.get_y()
    if y_f > 220: pdf.add_page(); y_f = pdf.get_y()
    
    pdf.set_xy(10, y_f); pdf.cell(70, 7, f"Adhesion {d_date.year}", 1, 0); pdf.cell(25, 7, "1.00", 1, 1, 'R')
    pdf.set_x(10); pdf.cell(70, 7, "Livraison", 1, 0); pdf.cell(25, 7, f"{liv_total:.2f}", 1, 1, 'R')
    pdf.set_x(10); pdf.set_fill_color(51, 139, 140); pdf.set_text_color(255)
    pdf.cell(70, 10, "TOTAL NET", 1, 0, 'C', True); pdf.set_text_color(0); pdf.cell(25, 10, f"{grand_total:.2f} EUR", 1, 0, 'R')
    
    pdf.set_xy(115, y_f); pdf.set_font('Arial', 'B', 9); pdf.cell(85, 8, "Signature et cachet :", "LTR", 1, 'C')
    pdf.set_x(115); pdf.cell(85, 20, "", "LBR", 1)

    # Sortie Binaire
    res_pdf = pdf.output(dest='S')
    st.download_button("💾 Télécharger PDF", res_pdf.encode('latin-1') if isinstance(res_pdf, str) else res_pdf, f"{d_num}.pdf", "application/pdf")

