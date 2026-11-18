import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import streamlit as st
import altair as alt
from dashboard.ui import setup_page, afficher_entete, afficher_footer
from dashboard.db_loader import charger_produits, charger_alertes

setup_page()
afficher_entete("Vue d'ensemble du stock", "Surveillez les quantités disponibles et identifiez les priorités.")

produits = charger_produits()
alertes = charger_alertes()

if produits.empty:
    st.info("Aucun produit n’est encore enregistré. Ajoutez-en depuis Administration.")
else:
    alertes_ouvertes = alertes[alertes["statut"] == "OUVERTE"] if not alertes.empty else alertes
    critiques = alertes_ouvertes[alertes_ouvertes["niveau"] == "CRITIQUE"] if not alertes.empty else alertes

    stock_total = float(produits["stock_actuel"].fillna(0).sum())
    sous_securite = produits[
        produits["stock_securite"].notna()
        & (produits["stock_actuel"] < produits["stock_securite"])
    ] if "stock_securite" in produits else produits.iloc[0:0]

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Produits suivis", len(produits))
    col2.metric("Stock cumulé", f"{stock_total:.1f}")
    col3.metric("Alertes actives", len(alertes_ouvertes))
    col4.metric("Stocks critiques", len(sous_securite))

    st.markdown("---")
    gauche, droite = st.columns([2, 1])
    with gauche:
        st.subheader("État de l'inventaire")
        categories = ["Toutes"] + sorted(produits["categorie"].dropna().astype(str).unique().tolist())
        categorie = st.selectbox("Filtrer par catégorie", categories)
        affichage = produits.copy()
        if categorie != "Toutes":
            affichage = affichage[affichage["categorie"] == categorie]

        colonnes = ["nom", "categorie", "stock_actuel", "stock_securite", "delai_fournisseur_jours"]
        df_aff = affichage[colonnes].copy()
        df_aff.columns = ["Produit", "Catégorie", "Stock actuel", "Stock sécurité", "Délai (j)"]
        st.dataframe(df_aff, use_container_width=True, hide_index=True)

    with droite:
        st.subheader("Répartition")
        compte = (
            produits["categorie"]
            .fillna("Non renseignée")
            .value_counts()
            .rename_axis("Catégorie")
            .reset_index(name="Produits")
        )

        graphique = (
            alt.Chart(compte)
            .mark_bar(cornerRadiusTopLeft=5, cornerRadiusTopRight=5, color="#176B87")
            .encode(
                x=alt.X("Catégorie:N", title="Catégorie", sort="-y"),
                y=alt.Y("Produits:Q", title="Nombre de produits"),
                tooltip=["Catégorie:N", "Produits:Q"],
            )
            .properties(height=300)
        )
        st.altair_chart(graphique, use_container_width=True)

        if len(critiques) > 0:
            st.error(f"{len(critiques)} alerte(s) critique(s)")
        else:
            st.success("Aucune alerte critique")

afficher_footer()
