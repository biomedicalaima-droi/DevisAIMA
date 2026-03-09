# -*- coding: utf-8 -*-
import streamlit as st
from streamlit_gsheets import GSheetsConnection
from fpdf import FPDF
from datetime import date
import os
import tempfile
import time
import io
import pandas as pd
from PIL import Image
import pdfplumber

# --- CONFIGURATION INITIALE ---
st.set_page_config(layout="wide", page_title="AIMA - Cloud Manager")

# Remplacez par un chemin accessible sur le serveur ou une URL
AIMA_LOGO_PATH = "aima_logo.png" 

# --- CONNEXION GOOGLE SHEETS ---
# Note: Configurez l'URL dans les "Secrets" de Streamlit Cloud
conn = st.connection("gsheets", type=GSheetsConnection)

def get_cloud_articles():
    return conn.read(worksheet="Articles", ttl="5m")

def get_cloud_history():
    return conn.read(worksheet="Documents", ttl="1m")

def save_doc_to_cloud(numero, client, montant, type_doc):
    try:
        df_history = get_cloud_history()
        new_doc = pd.DataFrame([{
            "numero": numero,
            "date": date.today().strftime("%d/%m/%Y"),
            "client": client,
            "montant": montant,
            "type": type_doc
        }])
        updated_df = pd.concat([df_history, new_doc], ignore_index=True)
        conn.update(worksheet="Documents", data=updated_df)
    except:
        st.warning("Impossible de sauvegarder dans l'historique Cloud (Vérifiez les permissions).")

# --- DONNÉES FIXES ---
LOCATIONS = {
    "CAME": {"address": "409 Chemin de Gensanne, 64520 Came", "email": "lehangardaima.came@gmail.com", "phone": "05 59 31 97 53"},
    "OSSERAIN-RIVAREYTE": {"address": "1009 Route des Aügas, 64390 Osserain-Rivareyte", "email": "osserain@assoaima.org", "phone": "05 59 38 17 86"},
    "SALIES-DE-BÉARN": {"address": "154 Chemin du Haou, 64270 Salies-de-Béarn", "email": "salies@assoaima.org", "phone": "05 59 38 03 30"},
    "CASTETNAU-CAMBLONG": {"address": "11 Rue du Bourg, 64190 Castetnau-Camblong", "email": "lehangardaima.castetnau@gmail.com", "phone": "05 59 66 16 90"}
}
LIEUX_ARTICLES = ["Came", "Osserain-Rivareyte", "Salies-de-Béarn", "Castetnau-Camblong"]

# --- SESSION STATE ---
if 'manual_items_dict' not in st.session_state: st.session_state.manual_items_dict = []

# --- LOGIQUE REVERSE PDF ---
def import_items_from_pdf(uploaded_pdf):
    try:
        new_items = []
        with pdfplumber.open(uploaded_pdf) as pdf:
            for page in pdf.pages:
                table = page.extract_table()
                if not table: continue
                for row in table:
                    if not row or any(x in str(row[0]) for x in ["Designation", "TOTAL", "Adhésion"]): continue
                    try:
                        nom = str(row[0]).strip()
                        prix_str = str(row[1]).replace(' ', '').replace('€', '').replace(',', '.')
                        new_items.append({"id": f"{time.time()}_{nom}", "nom": nom, "prix": float(prix_str)})
                    except: continue
        return new_items
    except Exception as e:
        st.error(f"Erreur d'import : {e}")
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
        
        self.set_xy(10, 40); self.set_fill_color(51, 139, 140); self.set_text_color(255, 255, 255); self.cell(80, 7, "Association AIMA", 1, 1, 'C', True)
        self.set_text_color(0, 0, 0); self.set_font('Arial', '', 8); self.set_x(10); self.multi_cell(80, 4, aima_info.encode('latin-1', 'replace').decode('latin-1'), 1, 'C')
        
        self.set_xy(120, 40); self.set_fill_color(51, 139, 140); self.set_text_color(255, 255, 255); self.cell(80, 7, f"DESTINATAIRE : {client_name.upper()}", 1, 1, 'C', True)
        self.set_text_color(0, 0, 0); self.set_font('Arial', '', 9); self.set_x(120); self.multi_cell(80, 5, client_address.encode('latin-1', 'replace').decode('latin-1'), 1, 'C')
        return self.get_y() + 5

# --- INTERFACE ---
tab_doc, tab_stock, tab_history = st.tabs(["📄 Créer Document", "📦 Catalogue Cloud", "📜 Historique"])

# Chargement catalogue Cloud
try:
    df_cloud = get_cloud_articles()
    data_prices_cloud = dict(zip(df_cloud['designation'], df_cloud['prix']))
except:
    data_prices_cloud = {"Erreur Cloud": 0.0}

with tab_stock:
    st.subheader("Gérer les articles sur Google Sheets")
    st.dataframe(df_cloud, use_container_width=True)
    with st.form("add_art"):
        n_n = st.text_input("Désignation")
        n_p = st.number_input("Prix (€)", min_value=0.0)
        if st.form_submit_button("Ajouter au catalogue Cloud"):
            new_row = pd.DataFrame([{"designation": n_n, "prix": n_p}])
            updated_df = pd.concat([df_cloud, new_row], ignore_index=True)
            conn.update(worksheet="Articles", data=updated_df)
            st.success("Synchronisé !")
            st.rerun()

with tab_history:
    st.subheader("Historique des documents générés")
    df_h = get_cloud_history()
    st.dataframe(df_h, use_container_width=True)

with tab_doc:
    with st.sidebar:
        st.header("📝 Paramètres")
        doc_type = st.selectbox("Type", ["DEVIS", "FACTURE"])
        doc_status = st.selectbox("Suivi", ["En attente", "Accepté", "Refusé"])
        selected_loc = st.selectbox("Lieu d'expédition", list(LOCATIONS.keys()))
        c_name = st.text_input("Client", "ONG- EPSPE")
        c_addr = st.text_area("Adresse Client", "Cotonou, Bénin")
        d_num = st.text_input("N° Document", f"2026-FAC-001")
        d_date = st.date_input("Date", date.today())
        include_adh = st.checkbox("Adhésion (1€)", True)
        liv_total = st.number_input("Frais Livraison (€)", 0.0)

    # Zone Import
    up_file = st.file_uploader("Importer un ancien PDF AIMA", type="pdf")
    if up_file and st.button("Charger articles du PDF"):
        st.session_state.manual_items_dict.extend(import_items_from_pdf(up_file))
        st.rerun()

    # Sélection catalogue
    sel_cat = st.multiselect("📦 Articles du catalogue :", options=sorted(list(data_prices_cloud.keys())))
    
    items_to_pdf = []
    total_items = 0.0

    # Rendu lignes
    for name in sel_cat:
        with st.container(border=True):
            st.write(f"**{name}**")
            col1, col2, col3, col4 = st.columns([1, 1, 1, 2])
            p = col1.number_input("Prix", value=float(data_prices_cloud.get(name,0)), key=f"p_{name}")
            q = col2.number_input("Qté", min_value=1, key=f"q_{name}")
            l = col3.selectbox("Lieu", LIEUX_ARTICLES, key=f"l_{name}")
            imgs = col4.file_uploader("Photos", accept_multiple_files=True, key=f"i_{name}")
            items_to_pdf.append({"Désignation": name, "P.U.": p, "Qté": q, "Total": p*q, "Lieu": l, "Images": imgs[:3] if imgs else []})
            total_items += p*q

    # Rendu Manuels
    for i, m in enumerate(st.session_state.manual_items_dict):
        with st.container(border=True):
            st.write(f"**{m['nom']}** (Manuel)")
            col1, col2, col3, col4 = st.columns([1, 1, 1, 2])
            p = col1.number_input("Prix", value=float(m['prix']), key=f"pm_{i}")
            q = col2.number_input("Qté", min_value=1, key=f"qm_{i}")
            l = col3.selectbox("Lieu", LIEUX_ARTICLES, key=f"lm_{i}")
            imgs = col4.file_uploader("Photos", accept_multiple_files=True, key=f"im_{i}")
            items_to_pdf.append({"Désignation": m['nom'], "P.U.": p, "Qté": q, "Total": p*q, "Lieu": l, "Images": imgs[:3] if imgs else []})
            total_items += p*q

    grand_total = total_items + (1.0 if include_adh else 0.0) + liv_total
    st.subheader(f"TOTAL NET : {grand_total:,.2f} EUR")

    if items_to_pdf and st.button(f"📄 GÉNÉRER PDF & SAUVEGARDER CLOUD"):
        pdf = AIMA_PDF(logo_path=AIMA_LOGO_PATH, doc_type=doc_type)
        pdf.add_page()
        # Logique PDF identique à votre original...
        # [Ajoutez ici votre boucle de dessin PDF de votre code original]
        
        # Sauvegarde Cloud
        save_doc_to_cloud(d_num, c_name, grand_total, doc_type)
        
        # Sortie
        pdf_bytes = pdf.output(dest='S').encode('latin-1', 'replace')
        st.download_button("💾 Télécharger", pdf_bytes, f"{d_num}.pdf")
