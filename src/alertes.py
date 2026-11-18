"""Génération des alertes à partir de l'état du stock + prévisions."""
import pandas as pd
from src import prevision as P


def evaluer_produit(produit: dict, serie: pd.Series, z: float = 1.65) -> list[dict]:
    alertes = []
    delai = produit["delai_fournisseur_jours"]
    stock = produit["stock_actuel"]

    cm = P.moyenne_mobile(serie, 7)
    ss = P.stock_securite(serie, delai, z)
    pc = P.point_de_commande(serie, delai, 7, z)
    prev_7j = P.prevision_moyenne_mobile(serie, 7, 7)

    # Une absence de consommation ne permet pas de déduire un risque réel.
    if cm <= 0:
        return alertes

    if stock <= pc:
        niveau = "CRITIQUE" if stock <= ss else "WARNING"
        q_sugg = max(0.0, round(cm * delai + ss - stock, 1))
        unite = produit.get("unite", "unité")

        if stock == 0:
            situation = "Le stock est épuisé"
        elif stock < ss:
            situation = "Le stock est inférieur au stock de sécurité"
        else:
            situation = "Le stock a atteint le point de commande"

        alertes.append({
            "type": "SEUIL", "niveau": niveau,
            "message": (
                f"{situation} ({stock:.1f} {unite}). "
                f"Le réapprovisionnement doit être déclenché au seuil de {pc:.1f} {unite}. "
                f"Consommation moyenne : {cm:.2f} {unite}/jour sur 7 jours; "
                f"stock de sécurité : {ss:.1f} {unite}."
            ),
            "quantite_suggeree": q_sugg,
        })

    if prev_7j > stock and stock > 0 and stock > pc:
        alertes.append({
            "type": "PREVISION", "niveau": "WARNING",
            "message": (f"Consommation prévue sur 7j ({prev_7j:.1f}) "
                        f"dépasse le stock actuel ({stock:.1f})"),
            "quantite_suggeree": round(prev_7j - stock, 1),
        })

    recent_idx = serie.tail(7).index
    anom = P.detecter_anomalies(serie, k=3.5)
    anom_recentes = anom[anom.index.isin(recent_idx)]
    if len(anom_recentes) > 0:
        alertes.append({
            "type": "ANOMALIE", "niveau": "INFO",
            "message": (f"{len(anom_recentes)} jour(s) de consommation anormale "
                        f"sur les 7 derniers jours"),
            "quantite_suggeree": 0.0,
        })

    return alertes
