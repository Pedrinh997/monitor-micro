# Deploy — CryptoPulse em VPS

Checklist sequencial. Rode cada bloco, confira o resultado, siga.

**Custo estimado:** ~$6/mês VPS + ~$10/ano domínio.
**Tempo:** 2-3h no total.

## Por que VPS antes de ARIMA

PC desligado -> scheduler não roda -> dados não acumulam -> ARIMA trava.
Numa VPS 24/7 o scheduler acumula sozinho. Esta fase destrava o ARIMA.

**Tamanho sugerido:** 1 vCPU / 1 GB RAM para começar. 2 GB se rodar
Prometheus + Grafana junto.

---

## Fase 1 — Provisionar VPS (você faz)

1. Escolha provedor (Hetzner CX22 recomendado, ~$5/mês)
2. Crie a VPS: Ubuntu 24.04, 2GB RAM, 1 vCPU
3. Anote o IP público
4. Registre domínio (Namecheap/Cloudflare, ~$10/ano)
5. No painel DNS do domínio, crie um A record:
   - Host: `@` (ou subdomínio, ex: `cryptopulse`)
   - Value: IP da VPS
6. Aguarde propagação (~5-30 min). Confirme com:

   nslookup SEU_DOMINIO
   # Deve retornar o IP da VPS

## Fase 2 — SSH e Docker (na VPS, como root)

    ssh root@IP_DA_VPS

    apt update && apt upgrade -y
    curl -fsSL https://get.docker.com | sh
    apt install -y docker-compose-plugin git nginx certbot python3-certbot-nginx

    docker --version && docker compose version

## Fase 3 — Clonar e configurar

    git clone https://github.com/Pedrinh997/monitor-micro.git /opt/monitor-micro
    cd /opt/monitor-micro
    cp .env.production.example .env
    nano .env

Preencha as senhas. Gere se precisar:

    openssl rand -hex 32
    # use para POSTGRES_PASSWORD e MINIO_SECRET_KEY

    python3 -c "import secrets; print(secrets.token_hex(32))"
    # use para SECRET_KEY

## Fase 4 — Subir a stack

    cd /opt/monitor-micro
    ./scripts/deploy_vps.sh

Confira:

    docker compose -f docker-compose.yml -f docker-compose.prod.yml ps
    curl http://127.0.0.1:8000/

Se as tabelas não existirem:

    docker exec monitor_micro-api-1 python create_tables.py

## Fase 5 — Nginx + HTTPS

    cp nginx/monitor-micro.conf /etc/nginx/sites-available/monitor-micro
    nano /etc/nginx/sites-available/monitor-micro
    # Troque SEU_DOMINIO pelo domínio real

    ln -s /etc/nginx/sites-available/monitor-micro /etc/nginx/sites-enabled/
    nginx -t && systemctl reload nginx

    certbot --nginx -d SEU_DOMINIO

Verifique:

    curl https://SEU_DOMINIO/api/

## Fase 6 — Firewall

    ufw allow ssh
    ufw allow 80
    ufw allow 443
    ufw --force enable
    ufw status

## Fase 7 — Deploy automático via CI

No GitHub: Settings → Secrets and variables → Actions → New repository secret.

Crie 3 secrets:

| Nome | Valor |
|------|-------|
| SERVER_HOST | IP da VPS |
| SERVER_USER | root (ou usuário deploy) |
| SSH_PRIVATE_KEY | chave privada SSH que dá acesso à VPS |

Depois, edite `.github/workflows/deploy.yml` e troque `&& false` por `&& true`.
A partir daí, todo push em `main` roda os 14 testes e, se passarem, faz deploy.

## Fase 8 — Backup diário

Na VPS, crie `/etc/cron.daily/backup-cryptopulse`:

    #!/bin/bash
    DATE=$(date +%Y%m%d)
    mkdir -p /root/backups
    docker exec monitor_micro-db-1 pg_dump -U postgres postgres | gzip > /root/backups/db-$DATE.sql.gz
    find /root/backups -mtime +7 -delete

Ative:

    chmod +x /etc/cron.daily/backup-cryptopulse

## Ajustes pós-deploy

- Remover portas expostas de db, redis, minio, grafana, worker (o overlay
  `docker-compose.prod.yml` já faz isso — confira com `docker compose config`)
- Firewall restritivo: apenas 22, 80, 443 expostos
- Confirmar que `.env` **não** foi commitado (`git status` limpo)

---

## Troubleshooting

**Deploy falhou no meio:** o `deploy_vps.sh` é idempotente. Corrija, rode de novo.

**Nginx 502:** confira que a API está de pé com `docker compose ps`. Se não, `docker logs monitor_micro-api-1`.

**certbot falhou:** DNS ainda não propagou. Espere 30 min e tente de novo.

**Ver logs:**

    docker logs monitor_micro-api-1 --tail 50
    docker logs monitor_micro-worker-1 --tail 50
    docker logs monitor_micro-frontend-1 --tail 50

**Parar tudo:**

    docker compose -f docker-compose.yml -f docker-compose.prod.yml down

**Atualizar manualmente:**

    cd /opt/monitor-micro
    ./scripts/deploy_vps.sh

---

## Próximo passo: ARIMA

Quando tiver >=20 amostras em `price_history`:

1. `pip install statsmodels` e adicionar ao `requirements.txt`
2. Trocar `_predict_baseline()` por `_predict_arima()` em `app/ml/forecast.py`
3. Manter assinatura `predict_prices(product_id, days) -> dict`
4. Endpoint e dashboard NÃO mudam
