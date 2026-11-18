import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import streamlit as st

from dashboard.ui import setup_page, afficher_entete, afficher_footer
from dashboard.db_loader import charger_produits, charger_alertes

setup_page()

produits = charger_produits()
alertes = charger_alertes()

st.markdown(
    """
    <style>
    .smartstock-hero {
        background: linear-gradient(135deg, #0B3D5C 0%, #176B87 100%);
        border-radius: 18px;
        padding: 30px 34px;
        margin: 4px 0 22px 0;
        color: white;
        box-shadow: 0 10px 28px rgba(11, 61, 92, 0.16);
    }
    .smartstock-hero h1 {
        color: white !important;
        margin: 0 0 8px 0 !important;
        font-size: 2.25rem !important;
    }
    .smartstock-hero p {
        color: #DCEEF6;
        margin: 0;
        font-size: 1rem;
    }
    .action-card {
        min-height: 138px;
        background: white;
        border: 1px solid #E6ECF2;
        border-radius: 14px;
        padding: 18px;
        box-shadow: 0 3px 12px rgba(11, 61, 92, 0.035);
    }
    .action-card .icon {
        font-size: 1.5rem;
        margin-bottom: 8px;
    }
    .action-card strong {
        display: block;
        color: #0B3D5C;
        font-size: 1.02rem;
        margin-bottom: 5px;
    }
    .action-card span {
        color: #64748B;
        font-size: 0.88rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <section class="smartstock-hero">
        <h1>Bienvenue sur SmartStock</h1>
        <p>Votre espace central pour suivre les stocks, anticiper les ruptures et accélérer les réapprovisionnements.</p>
    </section>
    """,
    unsafe_allow_html=True,
)

alertes_ouvertes = (
    alertes[alertes["statut"] == "OUVERTE"]
    if not alertes.empty and "statut" in alertes.columns
    else alertes
)
critiques = (
    alertes_ouvertes[alertes_ouvertes["niveau"] == "CRITIQUE"]
    if not alertes_ouvertes.empty and "niveau" in alertes_ouvertes.columns
    else alertes_ouvertes.iloc[0:0]
)

col1, col2, col3, col4 = st.columns(4)
col1.metric("Produits suivis", len(produits))
col2.metric("Alertes ouvertes", len(alertes_ouvertes))
col3.metric("Alertes critiques", len(critiques))
stock_total = float(produits["stock_actuel"].fillna(0).sum()) if not produits.empty else 0.0
col4.metric("Stock cumulé", f"{stock_total:.1f}")

st.markdown("### Accès rapides")
card1, card2, card3 = st.columns(3)

with card1:
    st.markdown(
        """
        <div class="action-card">
            <div class="icon">📊</div>
            <strong>Vue d’ensemble</strong>
            <span>Suivez l’état global de l’inventaire et les catégories de produits.</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.page_link("pages/1_Vue_densemble.py", label="Ouvrir la vue d’ensemble", icon="📊", use_container_width=True)

with card2:
    st.markdown(
        """
        <div class="action-card">
            <div class="icon">🚨</div>
            <strong>Gérer les alertes</strong>
            <span>Priorisez les situations critiques et marquez les actions comme traitées.</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.page_link("pages/2_Gestion_des_alertes.py", label="Consulter les alertes", icon="🚨", use_container_width=True)

with card3:
    st.markdown(
        """
        <div class="action-card">
            <div class="icon">🔧</div>
            <strong>Administration</strong>
            <span>Ajoutez des produits, saisissez des mouvements ou corrigez les stocks.</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.page_link("pages/4_Administration.py", label="Accéder à l’administration", icon="🔧", use_container_width=True)

st.markdown("---")

if produits.empty:
    st.info("Commencez par créer un produit dans l’onglet Administration.")
elif len(critiques) > 0:
    st.error(f"{len(critiques)} alerte(s) critique(s) nécessitent votre attention.")
else:
    st.success("Aucune alerte critique active. L’inventaire ne présente aucune priorité urgente.")

afficher_footer()
