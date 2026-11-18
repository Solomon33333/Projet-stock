"""Pipeline complet : lit la base, calcule, écrit les alertes."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import pandas as pd  # noqa: E402

from src.db import get_conn, init_db  # noqa: E402
from src import prevision as P  # noqa: E402
from src.alertes import evaluer_produit  # noqa: E402


def charger_donnees(conn):
    produits = pd.read_sql("SELECT * FROM produits", conn).to_dict("records")
    mouvements = pd.read_sql("SELECT * FROM mouvements", conn)
    return produits, mouvements


def executer(z: float = 1.65) -> int:
    if z < 0:
        raise ValueError("Le facteur z doit être positif ou nul")

    init_db()
    conn = get_conn()
    nb_alertes = 0
    try:
        produits, mouvements = charger_donnees(conn)
        for p in produits:
            serie = P.conso_journaliere(mouvements, p["id"])
            if serie.empty:
                continue

            ss = P.stock_securite(serie, p["delai_fournisseur_jours"], z)
            conn.execute(
                "UPDATE produits SET stock_securite = ? WHERE id = ?",
                (round(float(ss), 2), p["id"]),
            )

            alertes_actuelles = evaluer_produit(p, serie, z=z)

            types_actuels = {alerte["type"] for alerte in alertes_actuelles}

            # Une alerte ouverte n’est conservée que si sa cause existe toujours.
            if types_actuels:
                placeholders = ",".join("?" for _ in types_actuels)
                conn.execute(
                    f"""UPDATE alertes SET statut = 'TRAITEE'
                        WHERE produit_id = ? AND statut = 'OUVERTE'
                          AND type_alerte NOT IN ({placeholders})""",
                    (p["id"], *sorted(types_actuels)),
                )
            else:
                conn.execute(
                    """UPDATE alertes SET statut = 'TRAITEE'
                       WHERE produit_id = ? AND statut = 'OUVERTE'""",
                    (p["id"],),
                )

            for alerte in alertes_actuelles:
                deja_presente = conn.execute(
                    """SELECT id FROM alertes
                       WHERE produit_id = ? AND type_alerte = ? AND statut = 'OUVERTE'
                       LIMIT 1""",
                    (p["id"], alerte["type"]),
                ).fetchone()

                if deja_presente:
                    conn.execute(
                        """UPDATE alertes
                           SET niveau = ?, message = ?, quantite_suggeree = ?,
                               date_generation = CURRENT_TIMESTAMP
                           WHERE id = ?""",
                        (alerte["niveau"], alerte["message"],
                         alerte["quantite_suggeree"], deja_presente["id"]),
                    )
                else:
                    conn.execute(
                        """INSERT INTO alertes(produit_id, type_alerte, niveau,
                                               message, quantite_suggeree)
                           VALUES (?,?,?,?,?)""",
                        (p["id"], alerte["type"], alerte["niveau"], alerte["message"],
                         alerte["quantite_suggeree"]),
                    )
                    nb_alertes += 1

        conn.commit()
        return nb_alertes
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    n = executer()
    print(f"Pipeline OK — {n} alerte(s) générée(s).")
