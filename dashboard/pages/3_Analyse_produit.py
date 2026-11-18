import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import streamlit as st
import pandas as pd
import altair as alt
from dashboard.ui import setup_page, afficher_entete, afficher_footer
from dashboard.db_loader import charger_produits, charger_mouvements
from src import prevision as P

setup_page()
afficher_entete("Analyse produit", "Étudiez la consommation et les seuils de réapprovisionnement.")

produits = charger_produits()
mouvements = charger_mouvements()

if produits.empty:
    st.info("Aucun produit n’est encore enregistré. Ajoutez-en depuis Administration.")
else:
    nom = st.selectbox("Sélectionner un produit", produits["nom"].tolist())
    p = produits[produits["nom"] == nom].iloc[0].to_dict()
    serie = P.conso_journaliere(mouvements, int(p["id"]))

    if serie.empty:
        st.info("Aucune sortie n'est enregistrée pour ce produit : le graphique de consommation sera disponible après un premier mouvement de sortie.")
    else:
        serie.index = pd.to_datetime(serie.index).tz_localize(None)

        cm = P.moyenne_mobile(serie, 7)
        pc = P.point_de_commande(serie, int(p["delai_fournisseur_jours"]), 7, 1.65)

        c1, c2, c3 = st.columns(3)
        c1.metric("Stock Actuel", f"{float(p['stock_actuel']):.1f}")
        c2.metric("Point de commande", f"{pc:.1f}")
        c3.metric("Prévision 7j", f"{P.prevision_moyenne_mobile(serie, 7, 7):.1f}")

        st.markdown("---")
        st.subheader("Consommation quotidienne")

        df_chart = pd.DataFrame({
            "Date": serie.tail(30).index,
            "Consommation": serie.tail(30).values,
        })

        graphique = (
            alt.Chart(df_chart)
            .mark_line(point=True, strokeWidth=3, color="#176B87")
            .encode(
                x=alt.X("Date:T", title="Date"),
                y=alt.Y("Consommation:Q", title="Quantité consommée", scale=alt.Scale(zero=True)),
                tooltip=[
                    alt.Tooltip("Date:T", title="Date", format="%d/%m/%Y"),
                    alt.Tooltip("Consommation:Q", title="Consommation", format=".1f"),
                ],
            )
            .properties(height=360)
            .interactive()
        )

        st.altair_chart(graphique, use_container_width=True)

afficher_footer()
