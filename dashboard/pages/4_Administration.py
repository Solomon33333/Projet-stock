import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import streamlit as st

from dashboard.ui import setup_page, afficher_entete, afficher_footer
from dashboard.db_loader import charger_produits
from src.db import (
    ajouter_mouvement,
    ajouter_produit,
    modifier_stock_produit,
    supprimer_produit,
)

# --- IMPORT DU MOTEUR D'ALERTES ---
try:
    from run_pipeline import executer as lancer_pipeline
except ImportError:
    lancer_pipeline = None

setup_page()
afficher_entete("Administration", "Gérez le catalogue, les mouvements et les stocks depuis un seul espace.")

produits = charger_produits()

st.markdown("<style>.admin-card { background:#fff; border:1px solid #E6ECF2; border-radius:13px; padding:16px 18px; }</style>", unsafe_allow_html=True)

m1, m2, m3 = st.columns(3)
m1.metric("Produits", len(produits))
m2.metric("Stock cumulé", f"{float(produits['stock_actuel'].fillna(0).sum()):.1f}" if not produits.empty else "0.0")
m3.metric("Catégories", produits["categorie"].nunique() if not produits.empty else 0)

st.markdown("---")
tab_mvt, tab_prod, tab_gestion = st.tabs([
    "📥 Mouvement",
    "➕ Nouveau produit",
    "✏️ Stock & suppression",
])

with tab_mvt:
    st.subheader("Enregistrer un mouvement")
    if produits.empty:
        st.warning("Créez d’abord un produit avant d’enregistrer un mouvement.")
    else:
        col_select, col_info = st.columns([1.6, 1])
        with col_select:
            nom = st.selectbox("Produit", produits["nom"].tolist(), key="mvt_nom")
            produit = produits[produits["nom"] == nom].iloc[0]
            p_id = int(produit["id"])
        with col_info:
            unite = str(produit["unite"]).strip() or "unité"
            col_info.metric(
                "Stock disponible",
                f"{float(produit['stock_actuel']):.1f} {unite}",
            )

        with st.form("form_mvt", clear_on_submit=True):
            c1, c2 = st.columns(2)
            type_mvt = c1.selectbox(
                "Type de mouvement",
                ["ENTREE", "SORTIE", "CORRECTION"],
                help="ENTREE: ajouter, SORTIE: retirer, CORRECTION: remplacer le stock.",
            )
            qte = c2.number_input("Quantité", min_value=0.0, step=1.0, format="%.1f")
            motif = st.text_input("Motif", value="Saisie manuelle", max_chars=120)

            if st.form_submit_button("Enregistrer le mouvement", use_container_width=True):
                if qte <= 0:
                    st.error("La quantité doit être strictement supérieure à zéro.")
                else:
                    try:
                        ajouter_mouvement(p_id, type_mvt, qte, motif.strip() or "Saisie manuelle")
                        
                        # --- DECLENCHEUR AUTOMATIQUE ---
                        if lancer_pipeline:
                            try:
                                nb_alertes = lancer_pipeline()
                                st.success(f"Mouvement enregistré. {nb_alertes} alerte(s) recalculée(s) automatiquement.")
                            except Exception as e:
                                st.warning(f"Mouvement enregistré, mais le recalcul des alertes a échoué : {e}")
                        else:
                            st.success(f"Mouvement enregistré pour **{nom}**.")
                            
                        st.cache_data.clear()
                        st.rerun()
                    except ValueError as exc:
                        st.error(str(exc))
                    except Exception:
                        st.error("Impossible d’enregistrer le mouvement. Vérifiez la base de données.")

with tab_prod:
    st.subheader("Ajouter un produit")
    st.caption("Définissez les informations essentielles du nouvel article.")

    with st.form("form_prod", clear_on_submit=True):
        nom_p = st.text_input("Nom du produit", placeholder="Ex. Papier A4")

        c1, c2 = st.columns(2)
        cat = c1.selectbox("Catégorie", ["Consommables", "Pièces", "Fournitures", "Réactifs", "Autre"])
        unite = c2.selectbox("Unité", ["pièce", "kg", "L", "boîte", "paquet"])

        c3, c4 = st.columns(2)
        delai = c3.number_input("Délai fournisseur (jours)", min_value=1, max_value=365, value=7, step=1)
        seuil = c4.number_input("Seuil fixe", min_value=0.0, value=10.0, step=1.0, format="%.1f")

        if st.form_submit_button("Créer le produit", use_container_width=True):
            nom_normalise = nom_p.strip()
            if not nom_normalise:
                st.error("Le nom du produit est obligatoire.")
            else:
                try:
                    ajouter_produit(nom_normalise, cat, unite, int(delai), seuil)
                    st.cache_data.clear()
                    st.success(f"Produit **{nom_normalise}** créé avec succès.")
                    st.rerun()
                except Exception as exc:
                    message = str(exc)
                    if "UNIQUE constraint" in message:
                        st.error("Un produit portant ce nom existe déjà.")
                    else:
                        st.error("Impossible de créer le produit.")

with tab_gestion:
    st.subheader("Modifier ou supprimer un produit")

    if produits.empty:
        st.info("Aucun produit disponible pour modification.")
    else:
        nom_modif = st.selectbox(
            "Sélectionner un produit",
            produits["nom"].tolist(),
            key="sel_modif",
        )
        p_modif = produits[produits["nom"] == nom_modif].iloc[0].to_dict()
        p_id = int(p_modif["id"])
        stock_actuel = float(p_modif["stock_actuel"])

        col_modif, col_suppr = st.columns(2)

        @st.dialog("Modifier le stock")
        def modifier_stock_dialog(produit_id: int, nom: str, stock_initial: float):
            nouveau_stock = st.number_input(
                "Nouveau stock",
                min_value=0.0,
                value=stock_initial,
                step=1.0,
                format="%.1f",
                key=f"nouveau_stock_{produit_id}",
                help="Cette modification remplace directement la quantité enregistrée.",
            )

            col_annuler, col_confirmer = st.columns(2)
            if col_annuler.button("Annuler", use_container_width=True, key=f"annuler_modif_{produit_id}"):
                st.rerun()

            if col_confirmer.button("Confirmer la modification", use_container_width=True, type="primary", key=f"confirmer_modif_{produit_id}"):
                try:
                    modifier_stock_produit(produit_id, nouveau_stock)

                    if lancer_pipeline:
                        try:
                            nb_alertes = lancer_pipeline()
                            st.success(f"Stock mis à jour. {nb_alertes} alerte(s) recalculée(s) automatiquement.")
                        except Exception as e:
                            st.warning(f"Stock mis à jour, mais le recalcul des alertes a échoué : {e}")
                    else:
                        st.success(f"Stock de **{nom}** mis à jour : {nouveau_stock:.1f}.")

                    st.cache_data.clear()
                    st.rerun()
                except ValueError as exc:
                    st.error(str(exc))

        @st.dialog("Supprimer le produit")
        def supprimer_produit_dialog(produit_id: int, nom: str):
            st.warning(
                f"Voulez-vous vraiment supprimer « {nom} » ?",
                icon="⚠️",
            )
            st.caption("Cette action supprimera aussi les mouvements et alertes liés.")

            col_annuler, col_supprimer = st.columns(2)
            if col_annuler.button("Annuler", use_container_width=True, key=f"annuler_suppr_{produit_id}"):
                st.rerun()

            if col_supprimer.button("Supprimer", use_container_width=True, type="primary", key=f"confirmer_suppr_{produit_id}"):
                try:
                    supprimer_produit(produit_id)
                    st.cache_data.clear()
                    st.success(f"Produit **{nom}** supprimé.")
                    st.rerun()
                except ValueError as exc:
                    st.error(str(exc))

        with col_modif:
            st.markdown("### ✏️ Corriger le stock")
            st.caption("Ouvrez une boîte de dialogue pour saisir la nouvelle quantité.")
            if st.button("Modifier le stock", use_container_width=True, key=f"ouvrir_modif_{p_id}"):
                modifier_stock_dialog(p_id, nom_modif, stock_actuel)

        with col_suppr:
            st.markdown("### 🗑️ Supprimer")
            st.warning("Cette action supprimera aussi les mouvements et alertes liés.", icon="⚠️")
            if st.button(
                "Supprimer définitivement",
                use_container_width=True,
                type="secondary",
                key=f"ouvrir_suppr_{p_id}",
            ):
                supprimer_produit_dialog(p_id, nom_modif)

afficher_footer()