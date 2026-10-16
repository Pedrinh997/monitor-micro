# Runbook — Monitor Micro (WSL2)

Guia operacional do dia a dia. Para deploy em VPS, ver `DEPLOY.md`.

## Ligar após PC desligado

PC desligado -> Docker parou -> containers pararam -> scheduler NÃO rodou.
Tudo esperado. Nada quebrou.

Abra o terminal Ubuntu e rode:

    cd /mnt/d/monitor_micro && ./scripts/fixup.sh

Esse script: sobe dockerd, desliga serviços nativos (postgres/redis),
sobe o compose, espera API e Prometheus, e roda o healthcheck.
Tempo: ~1 min.

## Verificar

    cd /mnt/d/monitor_micro

    docker compose ps --format "table {{.Name}}\t{{.Status}}"
    curl -sS http://127.0.0.1:8000/ && echo

    docker exec monitor_micro-api-1 python -c "
    from app.scheduler import start_scheduler
    s = start_scheduler()
    for j in s.get_jobs(): print(f'  {j.id:25}  proximo: {j.next_run_time}')
    s.shutdown(wait=False)
    "

    git status --short && git log --oneline -3

Esperado: 9 containers Up, API OK, 2 jobs armados, git limpo.

## Dados (comparar com antes de desligar)

    docker exec monitor_micro-db-1 psql -U postgres -d postgres -c \
      "SELECT COUNT(*) FROM price_history;"

    docker exec monitor_micro-api-1 python -c "
    import boto3, os
    s3 = boto3.client('s3', endpoint_url='http://'+os.getenv('MINIO_ENDPOINT','minio:9000'),
        aws_access_key_id=os.getenv('MINIO_ACCESS_KEY','minioadmin'),
        aws_secret_access_key=os.getenv('MINIO_SECRET_KEY','minioadmin'),
        region_name='us-east-1')
    print('Parquets:', len(s3.list_objects_v2(Bucket='price-history').get('Contents', [])))
    "

Se iguais ao anotado: esperado. Se maiores: PC ficou ligado. Nenhum é erro.

## Banco

    docker exec monitor_micro-db-1 psql -U postgres -d postgres -c "\dt"
    docker exec monitor_micro-db-1 psql -U postgres -d postgres -c "SELECT * FROM users;"

Reset:

    docker exec monitor_micro-db-1 psql -U postgres -d postgres -c \
      "TRUNCATE price_history, products, users RESTART IDENTITY CASCADE;"

Se a API reclamar de tabela inexistente após `docker compose down -v`:

    docker exec monitor_micro-api-1 python create_tables.py

## Endpoints

    curl http://127.0.0.1:8000/

    curl -X POST http://127.0.0.1:8000/auth/register \
      -H "Content-Type: application/json" \
      -d '{"username":"teste","email":"teste@teste.com","password":"123456"}'

    TOKEN=$(curl -sS -X POST http://127.0.0.1:8000/auth/token \
      -H "Content-Type: application/x-www-form-urlencoded" \
      -d "username=teste&password=123456" | jq -r .access_token)

    curl http://127.0.0.1:8000/products/ -H "Authorization: Bearer $TOKEN"

## Comandos rápidos

    ./scripts/fixup.sh                       # sobe tudo e valida
    ./scripts/healthcheck.sh                 # só verifica
    docker compose ps                        # status dos containers
    docker logs monitor_micro-api-1 --tail 50
    docker compose down                      # para tudo (NÃO use -v, apaga volumes)
    docker compose up -d                     # sobe sem passar pelo fixup

## Troubleshooting

**API não responde:**

    docker logs monitor_micro-api-1 --tail 50

**Container em restart:**

    docker logs monitor_micro-<nome>-1 --tail 50

**Docker não sobe:**

    sudo systemctl start docker
    # ou, se systemd não estiver ativo:
    sudo nohup dockerd > /tmp/docker.log 2>&1 &
    sleep 8

**Postgres não responde em 40s:**

    docker logs monitor_micro-db-1 --tail 30

**Tudo travado:**

    cd /mnt/d/monitor_micro && ./scripts/fixup.sh
    # ou, se o próprio fixup falhar:
    docker compose down && docker compose up -d

NÃO use `-v` no `down` (apaga volumes).

## Próximo passo

Para deploy em VPS, ver `DEPLOY.md`.
