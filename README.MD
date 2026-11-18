# SmartStock — Gestion intelligente des stocks

SmartStock est une application Python permettant de suivre un inventaire, analyser la consommation, anticiper les ruptures et gérer les alertes de réapprovisionnement. Elle combine une interface Streamlit, une base SQLite et une automatisation avec n8n.

## Fonctionnalités

- tableau de bord des stocks et des alertes critiques;
- analyse de consommation et prévision à court terme;
- calcul du stock de sécurité à partir du délai fournisseur et de la demande;
- création, consultation et suppression de produits;
- saisie des entrées, sorties et corrections de stock;
- génération d’alertes évitant les doublons ouverts;
- pipeline quotidien journalisé et automatisable avec Cron;
- lecture du statut dans un workflow n8n.

## Architecture

```text
projet-stock/
├── dashboard/                 Interface Streamlit
│   ├── app.py                 Page d’accueil
│   ├── db_loader.py           Chargement des données
│   └── pages/                 Vues fonctionnelles
├── src/                       Logique métier
│   ├── db.py                  Schéma SQLite et opérations
│   ├── prevision.py           Prévisions et statistiques
│   └── alertes.py             Évaluation des alertes
├── data/                      Données et générateur
├── scripts/                   Scripts Cron/n8n
├── tests/                     Tests Pytest
├── n8n/workflow_stock.json    Workflow n8n exporté
├── run_pipeline.py            Exécution du pipeline
└── docker-compose.yml         Environnement n8n
```

## Prérequis

- Python 3.11 ou supérieur;
- Docker et Docker Compose pour lancer n8n;
- Git pour cloner le dépôt;
- Linux, macOS ou Windows avec un terminal compatible Bash.

Les principales dépendances sont Pandas, NumPy, Streamlit et Pytest.

## Installation

Depuis la racine du projet :

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python src/db.py
```

Sous Windows, activez l’environnement avec :

```powershell
.venv\Scripts\Activate.ps1
```

## Initialiser les données

Pour repartir d’une base propre contenant 25 produits fictifs reproductibles :

```bash
python data/generer_donnees.py
python run_pipeline.py
```

> Attention : ce script supprime les produits, mouvements et alertes existants.

Vous pouvez aussi démarrer avec une base vide :

```bash
python src/db.py
```

Puis créez les produits depuis l’onglet **Administration** de l’application.

## Démarrer l’interface

```bash
streamlit run dashboard/app.py
```

Ouvrez ensuite l’adresse affichée dans le terminal, généralement `http://localhost:8501`.

## Exécuter le pipeline

Le pipeline initialise la base, calcule les consommations et stocks de sécurité, puis crée les nouvelles alertes :

```bash
python run_pipeline.py
```

Il est également possible d’exécuter le script bash prévu pour Cron :

```bash
bash scripts/run_daily.sh
```

Avant utilisation, adaptez dans `scripts/run_daily.sh` les chemins absolus du projet, de l’environnement virtuel et du journal.

## Automatiser avec n8n

Démarrez n8n avec Docker Compose :

```bash
docker compose up -d
```

L’interface est accessible sur `http://localhost:5678`. Importez ensuite `n8n/workflow_stock.json` depuis l’interface n8n.

Le workflow lit `logs/status.json`, produit par `scripts/run_daily.sh`, puis journalise les alertes critiques détectées.

Pour arrêter n8n :

```bash
docker compose down
```

## Automatisation avec Cron

Un exemple Linux peut exécuter le pipeline chaque jour à 6 h :

```cron
0 6 * * * cd /chemin/vers/projet-stock && bash scripts/run_daily.sh
```

Remplacez `/chemin/vers/projet-stock` par le chemin réel du dépôt.

## Tests

Lancer toute la suite :

```bash
pytest
```

Lancer un fichier ou un test précis :

```bash
pytest tests/test_prevision.py
pytest tests/test_prevision.py::test_stock_securite_positif
```

## Données et fichiers générés

- `data/stock.db` : base SQLite locale;
- `logs/pipeline.log` : journal du pipeline créé au premier lancement bash;
- `logs/status.json` : statut utilisé par n8n;
- `logs/notifications.log` : journaux écrits par le workflow n8n;
- `resultats/` : fichiers CSV d’expérimentation.

Ne placez pas de données sensibles dans les fichiers générés sans chiffrement ou contrôle d’accès adapté.

## Dépannage

### Streamlit affiche une base vide

Initialisez les données puis relancez l’application :

```bash
python data/generer_donnees.py
streamlit run dashboard/app.py
```

### Le pipeline n’est pas trouvé depuis n8n

Vérifiez que les volumes Docker sont montés depuis la racine du projet, puis contrôlez que `docker-compose.yml` autorise l’accès aux dossiers `scripts`, `data` et `logs`.

### `run_daily.sh` échoue

Vérifiez :

```bash
chmod +x scripts/run_daily.sh
bash -n scripts/run_daily.sh
bash scripts/run_daily.sh
```

Corrigez ensuite `PROJECT_DIR`, `PYTHON` et `STATUS_FILE` dans le script si nécessaire.

## Technologies

- Python 3.11+;
- Streamlit;
- Pandas et NumPy;
- SQLite;
- Pytest;
- Docker Compose;
- n8n;
- Cron.