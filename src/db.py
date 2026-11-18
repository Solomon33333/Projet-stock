"""Accès SQLite. Une seule source de vérité pour le schéma."""
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "stock.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS produits (
    id                      INTEGER PRIMARY KEY,
    nom                     TEXT NOT NULL UNIQUE,
    categorie               TEXT,
    unite                   TEXT,
    delai_fournisseur_jours INTEGER NOT NULL CHECK(delai_fournisseur_jours > 0),
    stock_actuel            REAL NOT NULL DEFAULT 0 CHECK(stock_actuel >= 0),
    seuil_fixe              REAL CHECK(seuil_fixe >= 0),
    stock_securite          REAL CHECK(stock_securite >= 0)
);

CREATE TABLE IF NOT EXISTS mouvements (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    produit_id  INTEGER NOT NULL REFERENCES produits(id) ON DELETE CASCADE,
    date        DATE NOT NULL,
    type        TEXT NOT NULL CHECK(type IN ('ENTREE','SORTIE','CORRECTION')),
    quantite    REAL NOT NULL CHECK(quantite >= 0),
    motif       TEXT
);

CREATE TABLE IF NOT EXISTS alertes (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    produit_id        INTEGER NOT NULL REFERENCES produits(id) ON DELETE CASCADE,
    date_generation   DATETIME DEFAULT CURRENT_TIMESTAMP,
    type_alerte       TEXT NOT NULL,
    niveau            TEXT,
    message           TEXT,
    quantite_suggeree REAL CHECK(quantite_suggeree >= 0),
    statut            TEXT DEFAULT 'OUVERTE' CHECK(statut IN ('OUVERTE','TRAITEE')),
    UNIQUE(produit_id, date_generation, type_alerte)
);

CREATE INDEX IF NOT EXISTS idx_mvt_produit_date ON mouvements(produit_id, date);
CREATE INDEX IF NOT EXISTS idx_alertes_statut ON alertes(statut, date_generation);
"""


def get_conn() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA busy_timeout = 5000")
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with get_conn() as conn:
        conn.executescript(SCHEMA)


if __name__ == "__main__":
    init_db()
    print(f"Base initialisée : {DB_PATH}")


def ajouter_produit(nom: str, categorie: str, unite: str, delai: int, seuil_fixe: float):
    nom = nom.strip()
    if not nom:
        raise ValueError("Le nom du produit est obligatoire")
    if delai <= 0:
        raise ValueError("Le délai fournisseur doit être positif")
    if seuil_fixe is None or seuil_fixe < 0:
        raise ValueError("Le seuil fixe doit être positif ou nul")
    with get_conn() as conn:
        conn.execute(
            """INSERT INTO produits (nom, categorie, unite, delai_fournisseur_jours, stock_actuel, seuil_fixe)
               VALUES (?, ?, ?, ?, 0, ?)""",
            (nom, categorie, unite, delai, seuil_fixe),
        )


def ajouter_mouvement(produit_id: int, type_mvt: str, quantite: float, motif: str):
    if type_mvt not in {"ENTREE", "SORTIE", "CORRECTION"}:
        raise ValueError("Type de mouvement invalide")
    if quantite < 0:
        raise ValueError("La quantité doit être positive ou nulle")

    with get_conn() as conn:
        produit = conn.execute("SELECT stock_actuel FROM produits WHERE id = ?", (produit_id,)).fetchone()
        if produit is None:
            raise ValueError("Produit introuvable")

        nouveau_stock = float(produit["stock_actuel"])
        if type_mvt == "ENTREE":
            nouveau_stock += quantite
        elif type_mvt == "SORTIE":
            nouveau_stock -= quantite
            if nouveau_stock < 0:
                raise ValueError("Stock insuffisant pour ce mouvement")
        else:
            nouveau_stock = quantite

        conn.execute(
            """INSERT INTO mouvements (produit_id, date, type, quantite, motif)
               VALUES (?, date('now'), ?, ?, ?)""",
            (produit_id, type_mvt, quantite, motif),
        )
        conn.execute("UPDATE produits SET stock_actuel = ? WHERE id = ?", (nouveau_stock, produit_id))


def modifier_stock_produit(produit_id: int, nouveau_stock: float):
    if nouveau_stock < 0:
        raise ValueError("Le stock ne peut pas être négatif")
    with get_conn() as conn:
        cur = conn.execute("UPDATE produits SET stock_actuel = ? WHERE id = ?", (nouveau_stock, produit_id))
        if cur.rowcount == 0:
            raise ValueError("Produit introuvable")


def supprimer_produit(produit_id: int):
    with get_conn() as conn:
        cur = conn.execute("DELETE FROM produits WHERE id = ?", (produit_id,))
        if cur.rowcount == 0:
            raise ValueError("Produit introuvable")