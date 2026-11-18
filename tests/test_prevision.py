import pandas as pd
import pytest

from src import prevision as P


def test_moyenne_mobile():
    s = pd.Series([1, 1, 1, 1, 1, 1, 2])
    assert P.moyenne_mobile(s, 7) == pytest.approx(1 + 1 / 7)


def test_moyenne_mobile_serie_vide():
    assert P.moyenne_mobile(pd.Series(dtype=float)) == 0.0


def test_stock_securite_positif():
    s = pd.Series([5, 6, 4, 5, 7, 5, 6])
    assert P.stock_securite(s, delai=5) > 0


def test_parametres_invalides():
    with pytest.raises(ValueError):
        P.moyenne_mobile(pd.Series([1]), fenetre=0)
    with pytest.raises(ValueError):
        P.stock_securite(pd.Series([1, 2]), delai=-1)


def test_anomalie_detectee_serie_bruitee():
    # Série réaliste : consommation autour de 5 avec du bruit + un pic
    s = pd.Series([5.0, 4.8, 5.2, 4.9, 5.1, 4.7, 5.3, 5.0, 4.9, 5.1,
                   5.2, 4.8, 5.0, 4.9, 5.1, 5.0, 4.8, 5.2, 4.9, 5.1,
                   50.0])
    anom = P.detecter_anomalies(s, k=3.5)          # <-- k=3.5
    assert len(anom) == 1
    assert anom.iloc[0] == 50.0


def test_serie_ultra_plate_mad_zero():
    # Limite connue de la MAD : si > 50% des valeurs sont identiques,
    # MAD = 0 et aucune anomalie n'est détectée. Comportement documenté.
    s = pd.Series([5.0] * 20 + [50.0])
    assert len(P.detecter_anomalies(s)) == 0


def test_pas_anomalie_serie_stable():
    s = pd.Series([5.0, 5.1, 4.9, 5.0, 5.1, 4.9, 5.0, 5.1, 4.9, 5.0])
    assert len(P.detecter_anomalies(s)) == 0


def test_conso_journaliere_reindexe():
    df = pd.DataFrame({
        "produit_id": [1, 1],
        "date": ["2026-01-01", "2026-01-05"],
        "type": ["SORTIE", "SORTIE"],
        "quantite": [4.0, 6.0],
    })
    s = P.conso_journaliere(df, 1)
    assert len(s) == 5
    assert s.sum() == 10.0
    assert s.iloc[0] == 4.0
    assert s.iloc[-1] == 6.0


def test_conso_ignore_entrees():
    df = pd.DataFrame({
        "produit_id": [1, 1],
        "date": ["2026-01-01", "2026-01-02"],
        "type": ["ENTREE", "SORTIE"],
        "quantite": [100.0, 3.0],
    })
    s = P.conso_journaliere(df, 1)
    assert s.sum() == 3.0


def test_mae_dimensions_invalides():
    with pytest.raises(ValueError):
        P.mae([1, 2], [1])
