# RETOMADA — LEIA ISTO PRIMEIRO

Quando voltar, rode:

    monitor-up
    cd /mnt/d/monitor_micro
    cat DEPLOY_VPS.md

Depois siga a secao 3 abaixo.

AVISO: scheduler so roda com PC ligado. Se ficou dias desligado,
price_history e Parquets NAO acumularam. Esperado — Fase 4 resolve.

---

# Deploy VPS — Monitor Micro

Preparado em 2026-09-21. Proxima fase: 4 — VPS + Nginx + HTTPS.

## 0. Estado do projeto no dia do preparo

- Repo: github.com/Pedrinh997/monitor-micro
- Ultimo commit: 3139df2
- Parquets no MinIO: 8
- Amostras em price_history: 3
- Fases concluidas: 0, 1, 2, 3, A, C

## 1. Por que VPS antes de ARIMA

PC desligado -> scheduler nao roda -> dados nao acumulam -> ARIMA trava.
Numa VPS 24/7 o scheduler acumula sozinho. Fase 4 destrava o ARIMA.

## 2. Pre-requisitos

- VPS Ubuntu 22.04 ou 24.04 (DigitalOcean, Linode, Hetzner)
- Dominio com A record apontando para o IP
- SSH como root
- Repositorio no GitHub (ja tem)

Sugestao: 1 vCPU / 1 GB RAM para comecar. 2 GB se rodar Prometheus + Grafana.

## 3. Provisionamento

### 3.1 — Conectar

    ssh root@SEU_IP

### 3.2 — Atualizar

    apt update && apt upgrade -y

### 3.3 — Docker

    curl -fsSL https://get.docker.com | sh
    apt install -y docker-compose-plugin
    docker --version && docker compose version

### 3.4 — Usuario deploy (opcional)

    adduser deploy
    usermod -aG docker deploy
    su - deploy

### 3.5 — Clonar

    git clone https://github.com/Pedrinh997/monitor-micro.git
    cd monitor-micro

### 3.6 — .env de producao

    nano .env

Variaveis obrigatorias: POSTGRES_PASSWORD, MINIO_ROOT_PASSWORD,
SECRET_KEY, API_URL=http://api:8000.

Gere SECRET_KEY:

    python3 -c "import secrets; print(secrets.token_hex(32))"

### 3.7 — Subir

    docker compose up -d
    docker compose ps
    curl http://localhost:8000/

### 3.8 — Criar tabelas (uma vez)

    docker exec monitor_micro-api-1 python create_tables.py

## 4. Nginx + HTTPS

### 4.1 — Instalar

    apt install -y nginx certbot python3-certbot-nginx

### 4.2 — Configurar /etc/nginx/sites-available/monitor-micro

    server {
        server_name seudominio.com;

        location /api/ {
            proxy_pass http://127.0.0.1:8000/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }

        location / {
            proxy_pass http://127.0.0.1:8501/;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_set_header Host $host;
        }

        listen 80;
    }

Ativar:

    ln -s /etc/nginx/sites-available/monitor-micro /etc/nginx/sites-enabled/
    nginx -t && systemctl reload nginx

### 4.3 — HTTPS

    certbot --nginx -d seudominio.com

### 4.4 — Verificar

    curl https://seudominio.com/api/

## 5. Ajustes pos-deploy

- Remover portas expostas de db, redis, minio, grafana, worker
- Firewall: ufw allow ssh && ufw allow 80 && ufw allow 443 && ufw enable
- Backup: docker exec monitor_micro-db-1 pg_dump -U postgres postgres | gzip > /root/backup-DATA.sql.gz

## 6. Proximo passo: ARIMA

Quando tiver >=20 amostras:

1. pip install statsmodels no requirements.txt
2. Trocar _predict_baseline() por _predict_arima() em app/ml/forecast.py
3. Manter assinatura predict_prices(product_id, days) -> dict
4. Endpoint e dashboard NAO mudam
