import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import streamlit as st
import pandas as pd

from dashboard.db_loader import charger_alertes, marquer_traitee
from dashboard.ui import afficher_entete, afficher_footer, setup_page


setup_page()
afficher_entete(
    "Gestion des alertes",
    "Priorisez les risques de rupture, consultez les recommandations et clôturez les alertes traitées.",
)

alertes = charger_alertes()

if alertes.empty:
    st.info("Aucune alerte n’a encore été générée. Lancez le pipeline depuis l’administration ou après un mouvement de stock.")
else:
    for colonne in ("niveau", "statut", "type_alerte", "categorie"):
        if colonne not in alertes.columns:
            alertes[colonne] = ""

    alertes["niveau"] = alertes["niveau"].fillna("INFO").astype(str)
    alertes["statut"] = alertes["statut"].fillna("OUVERTE").astype(str)

    ouvertes = alertes[alertes["statut"] == "OUVERTE"]
    traitees = alertes[alertes["statut"] == "TRAITEE"]

    critiques = ouvertes[ouvertes["niveau"] == "CRITIQUE"]
    warnings = ouvertes[ouvertes["niveau"] == "WARNING"]
    informations = ouvertes[ouvertes["niveau"] == "INFO"]

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Alertes ouvertes", len(ouvertes))
    c2.metric("Critiques", len(critiques), delta="Action urgente", delta_color="inverse")
    c3.metric("Avertissements", len(warnings))
    c4.metric("Traitées", len(traitees))

    st.markdown("### Comment lire les niveaux")
    n1, n2, n3 = st.columns(3)
    n1.info("🔴 **CRITIQUE** : stock au-dessous ou proche du stock de sécurité.")
    n2.warning("🟡 **WARNING** : risque de rupture ou consommation supérieure au stock disponible.")
    n3.caption("🔵 **INFO** : consommation inhabituelle détectée, à surveiller.")

    onglet_ouvertes, onglet_historique = st.tabs([
        f"🔔 Alertes ouvertes ({len(ouvertes)})",
        f"✅ Historique ({len(traitees)})",
    ])

    with onglet_ouvertes:
        if ouvertes.empty:
            st.success("Toutes les alertes ont été traitées. L’inventaire ne contient aucune alerte active.")
        else:
            f1, f2, f3 = st.columns([1.4, 1, 1.4])

            niveaux = ["Tous"] + [niveau for niveau in ["CRITIQUE", "WARNING", "INFO"] if niveau in ouvertes["niveau"].values]
            categories = ["Toutes"] + sorted(ouvertes["categorie"].dropna().astype(str).unique().tolist())

            niveau_filtre = f1.selectbox("Priorité", niveaux)
            categorie_filtre = f2.selectbox("Catégorie", categories)
            recherche = f3.text_input("Rechercher un produit", placeholder="Nom du produit")

            alertes_filtrees = ouvertes.copy()
            if niveau_filtre != "Tous":
                alertes_filtrees = alertes_filtrees[alertes_filtrees["niveau"] == niveau_filtre]
            if categorie_filtre != "Toutes":
                alertes_filtrees = alertes_filtrees[alertes_filtrees["categorie"] == categorie_filtre]
            if recherche.strip():
                alertes_filtrees = alertes_filtrees[
                    alertes_filtrees["produit_nom"].str.contains(recherche.strip(), case=False, na=False)
                ]

            niveau_ordre = {"CRITIQUE": 0, "WARNING": 1, "INFO": 2}
            alertes_filtrees["priorite"] = alertes_filtrees["niveau"].map(niveau_ordre).fillna(3)
            alertes_filtrees = alertes_filtrees.sort_values(["priorite", "date_generation"], ascending=[True, False])

            if alertes_filtrees.empty:
                st.info("Aucune alerte ne correspond aux filtres sélectionnés.")

            for _, row in alertes_filtrees.iterrows():
                niveau = row["niveau"]
                icon = "🔴" if niveau == "CRITIQUE" else "🟡" if niveau == "WARNING" else "🔵"

                with st.container(border=True):
                    gauche, droite = st.columns([4.5, 1.5])

                    with gauche:
                        st.markdown(f"### {icon} {row['produit_nom']}")
                        st.markdown(f"**{niveau}** — {row['type_alerte']}")
                        st.write(row["message"] or "Aucun détail supplémentaire.")

                        quantite = row.get("quantite_suggeree")
                        unite = row.get("unite") if "unite" in row.index else None
                        if pd.notna(quantite) and float(quantite) > 0:
                            unite_affichee = unite if pd.notna(unite) and str(unite).strip() else "unité(s)"
                            st.success(
                                f"**Action recommandée : commander {float(quantite):.1f} {unite_affichee}.**"
                            )

                    with droite:
                        date_generation = row.get("date_generation")
                        if pd.notna(date_generation):
                            st.caption(f"Générée le : {date_generation}")

                        confirmation_key = f"confirmer_{int(row['id'])}"
                        confirmer = st.checkbox(
                            "Action effectuée",
                            key=confirmation_key,
                            help="Cochez cette case avant de clôturer l’alerte.",
                        )

                        if st.button(
                            "Clôturer l’alerte",
                            key=f"btn_{int(row['id'])}",
                            use_container_width=True,
                            disabled=not confirmer,
                        ):
                            marquer_traitee(int(row["id"]))
                            st.success(f"Alerte de **{row['produit_nom']}** clôturée.")
                            st.rerun()

    with onglet_historique:
        if traitees.empty:
            st.info("Aucune alerte n’a encore été traitée.")
        else:
            colonnes = {
                "date_generation": "Date",
                "produit_nom": "Produit",
                "niveau": "Niveau",
                "type_alerte": "Type",
                "message": "Détail",
            }
            historique = traitees[list(colonnes.keys())].copy()
            historique = historique.rename(columns=colonnes)
            st.dataframe(historique, use_container_width=True, hide_index=True)

st.markdown("---")
col1, col2 = st.columns(2)
if col1.button("Actualiser les données", use_container_width=True):
    st.cache_data.clear()
    st.rerun()
col2.caption("Les données sont mises à jour automatiquement toutes les 30 secondes.")

afficher_footer()
