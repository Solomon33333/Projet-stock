set -euo pipefail

echo "[$(date '+%Y-%m-%d %H:%M:%S')] === n8n a déclenché le pipeline ===" >> /project/logs/pipeline.log

# Appel du pipeline (Python embarqué dans l'image n8n)
python3 /project/run_pipeline.py >> /project/logs/pipeline.log 2>&1 || true

echo "[$(date '+%Y-%m-%d %H:%M:%S')] === Fin ===" >> /project/logs/pipeline.log

# Compte les alertes critiques du jour
CRITIQUES=$(python3 - <<'PYEOF'
import sqlite3
conn = sqlite3.connect("/project/data/stock.db")
n = conn.execute(
    "SELECT COUNT(*) FROM alertes WHERE niveau='CRITIQUE' AND statut='OUVERTE' AND date(date_generation)=date('now')"
).fetchone()[0]
conn.close()
print(n)
PYEOF
)

echo "{\"critiques\": $CRITIQUES, \"timestamp\": \"$(date -Iseconds)\"}"
