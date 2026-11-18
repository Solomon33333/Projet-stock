"""Génère un jeu de données réaliste et reproductible."""
import random
from datetime import date, timedelta
from pathlib import Path
import sys

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.db import get_conn, init_db  # noqa: E402

SEED = 42
NB_PRODUITS = 25
NB_JOURS = 120
DATE_DEBUT = date.today() - timedelta(days=NB_JOURS)

CATEGORIES = ["Consommables", "Pièces", "Fournitures", "Réactifs"]


def generer_produits(rng):
    produits = []
    for i in range(1, NB_PRODUITS + 1):
        conso_moy = rng.uniform(2, 20)
        delai = rng.choice([3, 5, 7, 10, 14])
        produits.append({
            "id": i,
            "nom": f"Produit_{i:02d}",
            "categorie": rng.choice(CATEGORIES),
            "unite": rng.choice(["pièce", "kg", "L"]),
            "delai_fournisseur_jours": delai,
            "stock_actuel": 0,
            "seuil_fixe": round(conso_moy * delai * 1.5, 1),
            "stock_securite": None,
            "conso_moy": conso_moy,
        })
    return produits


def serie_conso(produit, rng):
    base = produit["conso_moy"]
    tendance = rng.uniform(-0.02, 0.05)
    serie = []
    for j in range(NB_JOURS):
        saison = 1.4 if (j % 7) in (0, 1) else 0.9
        bruit = rng.gauss(1, 0.15)
        val = base * (1 + tendance * j / 30) * saison * bruit
        val = max(0.0, val)
        if rng.random() < 0.02:
            val *= rng.uniform(2.5, 4.0)
        serie.append(val)
    return serie


def main():
    random.seed(SEED)
    np.random.seed(SEED)
    rng = random.Random(SEED)

    init_db()
    conn = get_conn()
    conn.executescript(
        "DELETE FROM alertes; DELETE FROM mouvements; DELETE FROM produits;"
    )

    produits = generer_produits(rng)
    for p in produits:
        conn.execute(
            """INSERT INTO produits(id, nom, categorie, unite,
                                    delai_fournisseur_jours, stock_actuel, seuil_fixe)
               VALUES (?,?,?,?,?,?,?)""",
            (p["id"], p["nom"], p["categorie"], p["unite"],
             p["delai_fournisseur_jours"], 0, p["seuil_fixe"]),
        )

    total_mvts = 0
    for p in produits:
        serie = serie_conso(p, rng)
        for j, conso in enumerate(serie):
            d = DATE_DEBUT + timedelta(days=j)
            q = round(conso, 2)
            if q <= 0:
                continue
            conn.execute(
                """INSERT INTO mouvements(produit_id, date, type, quantite, motif)
                   VALUES (?,?,?,?,?)""",
                (p["id"], d.isoformat(), "SORTIE", q, "consommation"),
            )
            total_mvts += 1

    for p in produits:
        stock_init = round(p["conso_moy"] * 30, 1)
        conn.execute(
            "UPDATE produits SET stock_actuel = ? WHERE id = ?",
            (stock_init, p["id"]),
        )
        conn.execute(
            """INSERT INTO mouvements(produit_id, date, type, quantite, motif)
               VALUES (?,?,?,?,?)""",
            (p["id"], (DATE_DEBUT - timedelta(days=1)).isoformat(),
             "ENTREE", stock_init, "stock_initial"),
        )

    conn.commit()
    conn.close()
    print(f"OK — {NB_PRODUITS} produits, {total_mvts + NB_PRODUITS} mouvements, "
          f"{NB_JOURS} jours.")


if __name__ == "__main__":
    main()
