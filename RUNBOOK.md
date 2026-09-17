# Runbook — Monitor Micro (WSL2)

## Subir ambiente

    monitor-up       # sobe dockerd + compose + espera Postgres+API
    monitor-status   # docker compose ps
    monitor-logs     # logs da API
    monitor-api      # curl /

Se a API reclamar de tabela inexistente após `docker compose down -v`:

    sudo docker exec monitor_micro-api-1 python create_tables.py

## Banco

    sudo docker exec monitor_micro-db-1 psql -U postgres -d postgres -c "\dt"
    sudo docker exec monitor_micro-db-1 psql -U postgres -d postgres -c "SELECT * FROM users;"

Reset:

    sudo docker exec monitor_micro-db-1 psql -U postgres -d postgres -c \
      "TRUNCATE price_history, products, users RESTART IDENTITY CASCADE;"

## Endpoints

    curl http://127.0.0.1:8000/

    curl -X POST http://127.0.0.1:8000/auth/register \
      -H "Content-Type: application/json" \
      -d '{"username":"teste","email":"teste@teste.com","password":"123456"}'

    TOKEN=$(curl -sS -X POST http://127.0.0.1:8000/auth/token \
      -H "Content-Type: application/x-www-form-urlencoded" \
      -d "username=teste&password=123456" | jq -r .access_token)

    curl http://127.0.0.1:8000/products/ -H "Authorization: Bearer $TOKEN"

## Se docker não responde

    sudo nohup dockerd > /tmp/docker.log 2>&1 &
    sleep 8
    sudo docker compose up -d

Ou simplesmente: `monitor-up`
