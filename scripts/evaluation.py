"""Évaluations pour le rapport — protocole v3 (Exp.3 vérité terrain stricte)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
import pandas as pd

from src.db import get_conn
from src import prevision as P

RESULTATS = Path(__file__).resolve().parent.parent / "resultats"
RESULTATS.mkdir(exist_ok=True)


def charger():
    conn = get_conn()
    produits = pd.read_sql("SELECT * FROM produits", conn).to_dict("records")
    mouvements = pd.read_sql("SELECT * FROM mouvements", conn)
    conn.close()
    return produits, mouvements


def simuler_produit(serie, delai, stock_init, politique, params):
    stock = stock_init
    commandes_en_cours = []
    ruptures = 0
    nb_commandes = 0
    test = serie.values

    for jour in range(len(test)):
        livrees = [q for (j, q) in commandes_en_cours if j == jour]
        stock += sum(livrees)
        commandes_en_cours = [(j, q) for (j, q) in commandes_en_cours if j > jour]

        if politique == "seuil_fixe":
            seuil = params["seuil_fixe"]
            if stock <= seuil:
                q = max(params["cm_hist"] * 30, 1.0)
                commandes_en_cours.append((jour + delai, q))
                nb_commandes += 1
        else:
            pc = params["pc_calc"]
            ss = params["ss_calc"]
            cm = params["cm_hist"]
            if stock <= pc:
                q = max(pc + cm * 30 - stock, ss)
                commandes_en_cours.append((jour + delai, q))
                nb_commandes += 1

        conso = test[jour]
        if stock < conso:
            ruptures += 1
            stock = 0.0
        else:
            stock -= conso

    return ruptures, nb_commandes, stock


def exp1_seuil_vs_point_commande(produits, mouvements, horizon_test=30):
    lignes = []
    for p in produits:
        serie = P.conso_journaliere(mouvements, p["id"])
        if len(serie) < horizon_test + 14:
            continue
        test = serie.tail(horizon_test)
        hist = serie.iloc[:-horizon_test]

        cm_hist = P.moyenne_mobile(hist, 7)
        delai = p["delai_fournisseur_jours"]
        ss_calc = P.stock_securite(hist, delai, z=1.65)
        pc_calc = cm_hist * delai + ss_calc
        stock_init = pc_calc

        r_fixe, c_fixe, _ = simuler_produit(
            test, delai, stock_init, "seuil_fixe",
            {"seuil_fixe": p["seuil_fixe"], "cm_hist": cm_hist},
        )
        r_pc, c_pc, _ = simuler_produit(
            test, delai, stock_init, "point_de_commande",
            {"pc_calc": pc_calc, "ss_calc": ss_calc, "cm_hist": cm_hist},
        )

        lignes.append({
            "produit_id": p["id"], "produit": p["nom"],
            "ruptures_seuil_fixe": r_fixe,
            "ruptures_point_commande": r_pc,
            "commandes_seuil_fixe": c_fixe,
            "commandes_point_commande": c_pc,
        })

    df = pd.DataFrame(lignes)
    df.to_csv(RESULTATS / "exp1_seuil.csv", index=False)
    resume = pd.DataFrame([
        {"methode": "seuil_fixe",
         "ruptures_total": int(df["ruptures_seuil_fixe"].sum()),
         "commandes_total": int(df["commandes_seuil_fixe"].sum())},
        {"methode": "point_de_commande",
         "ruptures_total": int(df["ruptures_point_commande"].sum()),
         "commandes_total": int(df["commandes_point_commande"].sum())},
    ])
    resume.to_csv(RESULTATS / "exp1_resume.csv", index=False)
    return resume, df


def exp2_prevision(produits, mouvements, fenetre=7, horizon=7):
    lignes = []
    for p in produits:
        serie = P.conso_journaliere(mouvements, p["id"])
        if len(serie) < horizon + fenetre:
            continue
        hist = serie.iloc[:-horizon]
        reel = serie.tail(horizon)

        pred_naive = float(hist.mean())
        mae_naive = P.mae(reel.values, np.full(horizon, pred_naive))
        rmse_naive = float(np.sqrt(np.mean((reel.values - pred_naive) ** 2)))

        pred_mm = P.moyenne_mobile(hist, fenetre)
        mae_mm = P.mae(reel.values, np.full(horizon, pred_mm))
        rmse_mm = float(np.sqrt(np.mean((reel.values - pred_mm) ** 2)))

        lignes.append({
            "produit_id": p["id"], "produit": p["nom"],
            "mae_baseline_naive": round(mae_naive, 3),
            "mae_moyenne_mobile": round(mae_mm, 3),
            "rmse_baseline_naive": round(rmse_naive, 3),
            "rmse_moyenne_mobile": round(rmse_mm, 3),
            "gain_mae_pct": round(100 * (mae_naive - mae_mm) / mae_naive, 2)
                            if mae_naive > 0 else 0.0,
        })

    df = pd.DataFrame(lignes)
    df.to_csv(RESULTATS / "exp2_prevision.csv", index=False)
    resume = pd.DataFrame([
        {"methode": "baseline_naive",
         "mae_moyenne": round(df["mae_baseline_naive"].mean(), 3),
         "rmse_moyen": round(df["rmse_baseline_naive"].mean(), 3)},
        {"methode": "moyenne_mobile",
         "mae_moyenne": round(df["mae_moyenne_mobile"].mean(), 3),
         "rmse_moyen": round(df["rmse_moyenne_mobile"].mean(), 3)},
    ])
    resume.to_csv(RESULTATS / "exp2_resume.csv", index=False)
    return resume, df


def exp3_alertes(produits, mouvements, horizon_test=90):
    """
    V4 : stock initial = pc + 15j de conso (état normal, pas de surstock),
    horizon de test = 90 jours (3 cycles de réappro),
    lead time fournisseur respecté.

    Vérité terrain = sans commande, le stock tombe à 0 sous 7 jours.
    Prédiction    = alerte SEUIL émise ce jour-là.
    """
    tp = fp = fn = tn = 0
    for p in produits:
        serie = P.conso_journaliere(mouvements, p["id"])
        if len(serie) < horizon_test + 14:
            continue
        test = serie.tail(horizon_test)
        hist = serie.iloc[:-horizon_test]

        cm = P.moyenne_mobile(hist, 7)
        delai = p["delai_fournisseur_jours"]
        ss = P.stock_securite(hist, delai, z=1.65)
        pc = cm * delai + ss

        # Stock initial : pc + 15 jours de conso (pas de surstock)
        stock = pc + cm * 15
        commandes_en_cours = []

        for i, conso in enumerate(test.values):
            # Livraisons du jour
            livrees = [q for (j, q) in commandes_en_cours if j == i]
            stock += sum(livrees)
            commandes_en_cours = [(j, q) for (j, q) in commandes_en_cours if j > i]

            # Vérité terrain : sans commande, le stock tombe-t-il à 0 sous 7j ?
            conso_cumul = 0.0
            rupture_imminente = False
            for j in range(i, min(i + 7, len(test))):
                conso_cumul += test.iloc[j]
                if stock - conso_cumul < 0:
                    rupture_imminente = True
                    break
            verite = rupture_imminente
            pred = stock <= pc

            if pred and verite:
                tp += 1
            elif pred and not verite:
                fp += 1
            elif not pred and verite:
                fn += 1
            else:
                tn += 1

            # Commande si alerte, livrée après le lead time
            if pred:
                q = max(pc + cm * 30 - stock, ss)
                commandes_en_cours.append((i + delai, q))

            # Consommation du jour
            stock = max(0.0, stock - conso)

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    rappel = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * precision * rappel / (precision + rappel) if (precision + rappel) > 0 else 0.0

    df = pd.DataFrame([
        {"metrique": "TP", "valeur": tp},
        {"metrique": "FP", "valeur": fp},
        {"metrique": "FN", "valeur": fn},
        {"metrique": "TN", "valeur": tn},
        {"metrique": "precision", "valeur": round(precision, 3)},
        {"metrique": "rappel", "valeur": round(rappel, 3)},
        {"metrique": "f1", "valeur": round(f1, 3)},
    ])
    df.to_csv(RESULTATS / "exp3_alertes.csv", index=False)
    return df


def main():
    print("Chargement des données…")
    produits, mouvements = charger()
    print(f"  {len(produits)} produits, {len(mouvements)} mouvements\n")

    print("=== Exp. 1 — Seuil fixe vs point de commande ===")
    r1, _ = exp1_seuil_vs_point_commande(produits, mouvements)
    print(r1.to_string(index=False)); print()

    print("=== Exp. 2 — Prévision : baseline naïve vs moyenne mobile ===")
    r2, _ = exp2_prevision(produits, mouvements)
    print(r2.to_string(index=False)); print()

    print("=== Exp. 3 — V3-STRICTE ===")
    r3 = exp3_alertes(produits, mouvements)
    print(r3.to_string(index=False)); print()

    print(f"✅ CSV générés dans : {RESULTATS}")


if __name__ == "__main__":
    main()
