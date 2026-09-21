# BOOT — Ligar Monitor Micro apos PC desligado

## O que acontece

PC desligado -> Docker parou -> containers pararam -> scheduler NAO rodou.
Tudo esperado. Nada quebrou.

## 1. Abrir WSL

Abre o terminal Ubuntu.

## 2. Subir tudo

    monitor-up

Faz: sobe daemon, docker compose up -d, espera Postgres e API, mostra status.
Tempo: 30-60s.

Se aparecer "API nao responde", aguarde 10s e teste:

    curl -sS http://127.0.0.1:8000/

## 3. Verificar

    cd /mnt/d/monitor_micro

    sudo docker compose ps --format "table {{.Name}}\t{{.Status}}"
    curl -sS http://127.0.0.1:8000/ && echo

    sudo docker exec monitor_micro-api-1 python -c "
    from app.scheduler import start_scheduler
    s = start_scheduler()
    for j in s.get_jobs(): print(f'  {j.id:25}  proximo: {j.next_run_time}')
    s.shutdown(wait=False)
    "

    git status --short && git log --oneline -3

Esperado: 7 containers Up, API OK, 2 jobs armados, git limpo.

## 4. Dados (comparar com antes de desligar)

    sudo docker exec monitor_micro-db-1 psql -U postgres -d postgres -c \
      "SELECT COUNT(*) FROM price_history;"

    sudo docker exec monitor_micro-api-1 python -c "
    import boto3, os
    s3 = boto3.client('s3', endpoint_url='http://'+os.getenv('MINIO_ENDPOINT','minio:9000'),
        aws_access_key_id=os.getenv('MINIO_ACCESS_KEY','minioadmin'),
        aws_secret_access_key=os.getenv('MINIO_SECRET_KEY','minioadmin'),
        region_name='us-east-1')
    print('Parquets:', len(s3.list_objects_v2(Bucket='price-history').get('Contents', [])))
    "

Se iguais ao anotado: esperado. Se maiores: PC ficou ligado. Nenhum e erro.

## 5. Proximo passo

Ver DEPLOY_VPS.md -> Fase 4.

## 6. Se algo der errado

API nao responde:

    sudo docker logs monitor_micro-api-1 --tail 50

Container em restart:

    sudo docker logs monitor_micro-<nome>-1 --tail 50

Docker nao sobe:

    sudo nohup dockerd > /tmp/docker.log 2>&1 &
    sleep 8 && sudo docker ps

Permission denied no monitor-up:

    chmod +x ~/up_monitor.sh

Postgres nao responde em 40s:

    sudo docker logs monitor_micro-db-1 --tail 30

Tudo travado:

    sudo docker compose down && sudo docker compose up -d

NAO use -v (apaga volumes).
