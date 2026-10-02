"""Análise de preços históricos via DuckDB lendo Parquets do MinIO.

Cache:
- Parquets ficam em CACHE_DIR (persistente durante a vida do container).
- ETags do bucket são salvos em .etags.json para detectar mudanças.
- Cache hit => zero downloads. Cache miss => sincroniza só o necessário.
"""
import json
import os
import tempfile
from pathlib import Path

import boto3
import duckdb

BUCKET = "price-history"
CACHE_DIR = Path(os.getenv("ANALYTICS_CACHE_DIR", tempfile.gettempdir())) / "duckdb_parquet_cache"
ETAGS_FILE = CACHE_DIR / ".etags.json"


def _s3():
    return boto3.client(
        "s3",
        endpoint_url=f"http://{os.getenv('MINIO_ENDPOINT', 'minio:9000')}",
        aws_access_key_id=os.getenv("MINIO_ACCESS_KEY", "minioadmin"),
        aws_secret_access_key=os.getenv("MINIO_SECRET_KEY", "minioadmin"),
        region_name="us-east-1",
    )


def _list_parquets(s3) -> list[dict]:
    try:
        objs = s3.list_objects_v2(Bucket=BUCKET)
    except Exception:
        return []
    return [o for o in objs.get("Contents", []) if o["Key"].endswith(".parquet")]


def _load_cached_etags() -> dict | None:
    try:
        return json.loads(ETAGS_FILE.read_text())
    except Exception:
        return None


def _save_etags(etags: dict) -> None:
    try:
        ETAGS_FILE.write_text(json.dumps(etags))
    except Exception:
        pass


def _sync_parquets() -> int:
    """Garante cache atualizado. Retorna número de parquets ÚNICOS.

    Deduplica por ETag: dois keys com o mesmo conteúdo contam como um só.
    Sem isso, read_parquet('*.parquet') soma as mesmas linhas N vezes,
    inflando count e avg_price.
    """
    s3 = _s3()
    all_parquets = _list_parquets(s3)
    if not all_parquets:
        return 0

    seen_etags: set[str] = set()
    unique: list[dict] = []
    for o in all_parquets:
        if o["ETag"] in seen_etags:
            continue
        seen_etags.add(o["ETag"])
        unique.append(o)

    current = {o["Key"]: o["ETag"] for o in unique}
    cached = _load_cached_etags()
    if cached == current and CACHE_DIR.exists():
        return len(unique)

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    wanted = {Path(o["Key"]).name for o in unique}
    for f in CACHE_DIR.glob("*.parquet"):
        if f.name not in wanted:
            f.unlink()

    for o in unique:
        data = s3.get_object(Bucket=BUCKET, Key=o["Key"])["Body"].read()
        (CACHE_DIR / Path(o["Key"]).name).write_bytes(data)

    _save_etags(current)
    return len(unique)


def _load_view(con, parquet_dir: Path):
    """Cria view `prices` deduplicada.

    O bucket mistura snapshots cumulativos antigos (dump completo do
    histórico) com deltas novos (só o range novo). read_parquet('*')
    soma as mesmas medições N vezes — count e avg_price inflados.

    Dedup por (product_id, scraped_at, price): com timestamp em
    microssegundos, colisão legítima é praticamente nula.
    """
    pattern = str(parquet_dir / "*.parquet")
    con.execute(f"""
        CREATE OR REPLACE VIEW prices AS
        SELECT DISTINCT product_id, scraped_at, price, currency
        FROM read_parquet('{pattern}')
    """)


def get_price_stats(product_id: int | None = None) -> dict:
    """Preço médio, mínimo, máximo e contagem para um produto (ou todos)."""
    n = _sync_parquets()
    if n == 0:
        return {"error": "sem parquets no bucket", "count": 0}

    con = duckdb.connect()
    _load_view(con, CACHE_DIR)
    where = f"WHERE product_id = {product_id}" if product_id else ""
    row = con.execute(f"""
        SELECT
            COUNT(*)      AS n,
            AVG(price)    AS avg_price,
            MIN(price)    AS min_price,
            MAX(price)    AS max_price,
            MAX(currency) AS currency
        FROM prices
        {where}
    """).fetchone()
    con.close()
    return {
        "count":     int(row[0]),
        "avg_price": float(row[1]) if row[1] is not None else None,
        "min_price": float(row[2]) if row[2] is not None else None,
        "max_price": float(row[3]) if row[3] is not None else None,
        "currency":  row[4],
    }


def get_price_variation(product_id: int) -> dict:
    """Variação absoluta e percentual entre os 2 últimos preços do produto."""
    n = _sync_parquets()
    if n == 0:
        return {"error": "sem parquets no bucket"}

    con = duckdb.connect()
    _load_view(con, CACHE_DIR)
    rows = con.execute(f"""
        SELECT price, scraped_at
        FROM prices
        WHERE product_id = {product_id}
        ORDER BY scraped_at DESC
        LIMIT 2
    """).fetchall()
    con.close()

    if len(rows) < 2:
        return {
            "product_id": product_id,
            "message": "histórico insuficiente (< 2 amostras)",
        }

    current, _ = rows[0]
    previous, _ = rows[1]
    diff = current - previous
    pct = (diff / previous * 100) if previous else None
    return {
        "product_id": product_id,
        "current":    float(current),
        "previous":   float(previous),
        "diff":       float(diff),
        "pct_change": round(float(pct), 2) if pct is not None else None,
    }
