import sys
from pathlib import Path
import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.db import get_conn

@st.cache_data(ttl=30)
def charger_produits() -> pd.DataFrame:
    conn = get_conn()
    try: return pd.read_sql("SELECT * FROM produits ORDER BY nom", conn)
    finally: conn.close()

@st.cache_data(ttl=30)
def charger_alertes() -> pd.DataFrame:
    conn = get_conn()
    try:
        return pd.read_sql("SELECT a.*, p.nom AS produit_nom, p.categorie, p.unite FROM alertes a JOIN produits p ON p.id = a.produit_id ORDER BY a.date_generation DESC", conn)
    finally: conn.close()

@st.cache_data(ttl=30)
def charger_mouvements() -> pd.DataFrame:
    conn = get_conn()
    try: return pd.read_sql("SELECT * FROM mouvements", conn)
    finally: conn.close()

def marquer_traitee(alerte_id: int):
    conn = get_conn()
    try:
        conn.execute("UPDATE alertes SET statut = 'TRAITEE' WHERE id = ?", (alerte_id,))
        conn.commit()
    finally: conn.close()
    st.cache_data.clear()
