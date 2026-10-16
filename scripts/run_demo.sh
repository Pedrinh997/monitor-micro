#!/bin/bash
source venv/bin/activate

# Define o host do Redis para localhost (já que estamos rodando fora do Docker Compose)
export REDIS_HOST=localhost
export REDIS_URL="redis://localhost:6379/0"

uvicorn app.main:app --host 0.0.0.0 --port 8000 &
python -m app.worker &
sleep 3
ngrok http 8000 --log=stdout > ngrok.log 2>&1 &
echo "✅ Serviços iniciados!"
echo "🔗 Link público: execute 'curl -s http://localhost:4040/api/tunnels | jq -r \".tunnels[0].public_url\"'"
wait
