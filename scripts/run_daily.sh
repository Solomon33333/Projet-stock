#!/usr/bin/env bash
set -euo pipefail

# NOUVEAU CHEMIN ICI
PROJECT_DIR="/mnt/DATA/Mes Projets/projet-stock"
LOG_FILE="$PROJECT_DIR/logs/pipeline.log"
PYTHON="$PROJECT_DIR/.venv/bin/python"
STATUS_FILE="$PROJECT_DIR/logs/status.json"

cd "$PROJECT_DIR"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] === Démarrage pipeline ===" >> "$LOG_FILE"
"$PYTHON" "$PROJECT_DIR/run_pipeline.py" >> "$LOG_FILE" 2>&1
echo "[$(date '+%Y-%m-%d %H:%M:%S')] === Fin pipeline ===" >> "$LOG_FILE"

# Calcul du nombre d'alertes critiques
CRITIQUES=$("$PYTHON" - <<'PYEOF'
import sqlite3
from pathlib import Path
db = Path("/mnt/DATA/Mes Projets/projet-stock/data/stock.db")
conn = sqlite3.connect(db)
n = conn.execute("SELECT COUNT(*) FROM alertes WHERE niveau='CRITIQUE' AND statut='OUVERTE' AND date(date_generation)=date('now')").fetchone()[0]
conn.close()
print(n)
PYEOF
)

# Écriture du fichier JSON pour n8n
echo "{\"critiques\": $CRITIQUES, \"timestamp\": \"$(date -Iseconds)\"}" > "$STATUS_FILE"

if [ "$CRITIQUES" -gt 0 ]; then
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] === Alerte: $CRITIQUES alertes critiques détectées ===" >> "$LOG_FILE"
  # Ici, vous pouvez ajouter d'autres actions, comme l'envoi d'une notification
fi
