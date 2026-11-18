"""Algorithmes de prévision et de dimensionnement. Pur, testable, sans I/O."""
import numpy as np
import pandas as pd


def conso_journaliere(df_mouvements: pd.DataFrame, produit_id: int) -> pd.Series:
    """Retourne la consommation quotidienne réelle d’un produit.

    Seules les sorties sont consommées. Les entrées, corrections et types
    inconnus sont ignorés. Les jours sans mouvement restent présents à zéro.
    """
    colonnes = {"produit_id", "date", "type", "quantite"}
    if df_mouvements is None or df_mouvements.empty:
        return pd.Series(dtype=float)

    manquantes = colonnes.difference(df_mouvements.columns)
    if manquantes:
        raise ValueError(f"Colonnes mouvements manquantes: {', '.join(sorted(manquantes))}")

    df = df_mouvements[df_mouvements["produit_id"] == produit_id].copy()
    if df.empty:
        return pd.Series(dtype=float)

    df["date"] = pd.to_datetime(df["date"], errors="coerce", utc=True)
    df = df[df["date"].notna() & (df["type"] == "SORTIE")].copy()
    if df.empty:
        return pd.Series(dtype=float)

    df["quantite"] = pd.to_numeric(df["quantite"], errors="coerce").fillna(0.0)
    df["consommation"] = df["quantite"].clip(lower=0)

    serie = df.groupby(df["date"].dt.normalize())["consommation"].sum().sort_index()
    serie.index = serie.index.tz_localize(None)
    full_idx = pd.date_range(serie.index.min(), serie.index.max(), freq="D")
    return serie.reindex(full_idx, fill_value=0.0)


def _valider_parametre(valeur: int | float, nom: str, minimum: float = 1.0) -> None:
    if not np.isfinite(valeur) or valeur < minimum:
        raise ValueError(f"{nom} doit être >= {minimum}")


def moyenne_mobile(serie: pd.Series, fenetre: int = 7) -> float:
    _valider_parametre(fenetre, "fenetre")
    if serie is None or serie.empty:
        return 0.0
    valeurs = pd.Series(serie, dtype=float).dropna()
    valeurs = valeurs[np.isfinite(valeurs)]
    if valeurs.empty:
        return 0.0
    return float(valeurs.tail(int(fenetre)).mean())


def stock_securite(serie: pd.Series, delai: int, z: float = 1.65) -> float:
    _valider_parametre(delai, "delai")
    _valider_parametre(z, "z", minimum=0.0)
    if serie is None or serie.empty:
        return 0.0

    valeurs = pd.Series(serie, dtype=float).dropna()
    valeurs = valeurs[np.isfinite(valeurs)]
    if len(valeurs) < 2:
        return 0.0

    sigma = float(valeurs.std(ddof=1))
    if not np.isfinite(sigma):
        return 0.0
    return max(0.0, z * sigma * np.sqrt(delai))


def point_de_commande(serie: pd.Series, delai: int,
                      fenetre: int = 7, z: float = 1.65) -> float:
    cm = moyenne_mobile(serie, fenetre)
    ss = stock_securite(serie, delai, z)
    return max(0.0, cm * delai + ss)


def prevision_moyenne_mobile(serie: pd.Series, fenetre: int = 7,
                             horizon: int = 7) -> float:
    _valider_parametre(horizon, "horizon")
    return moyenne_mobile(serie, fenetre) * int(horizon)


def mae(y_true, y_pred) -> float:
    y_true = np.asarray(y_true, dtype=float).reshape(-1)
    y_pred = np.asarray(y_pred, dtype=float).reshape(-1)
    if y_true.size == 0 or y_true.shape != y_pred.shape:
        raise ValueError("y_true et y_pred doivent être des tableaux non vides de mêmes dimensions")
    if not np.isfinite(y_true).all() or not np.isfinite(y_pred).all():
        raise ValueError("Les valeurs de prévision doivent être finies")
    return float(np.mean(np.abs(y_true - y_pred)))


def detecter_anomalies(serie: pd.Series, k: float = 2.5) -> pd.Series:
    _valider_parametre(k, "k", minimum=0.0)
    if serie is None or serie.empty:
        return pd.Series(dtype=float)

    valeurs = pd.Series(serie, dtype=float).dropna()
    valeurs = valeurs[np.isfinite(valeurs)]
    if valeurs.empty:
        return valeurs

    med = valeurs.median()
    ecarts_absolus = (valeurs - med).abs()
    mad = ecarts_absolus.median()
    if mad == 0:
        return valeurs.iloc[0:0]

    resultat = valeurs[ecarts_absolus > k * 1.4826 * mad]
    return resultat
