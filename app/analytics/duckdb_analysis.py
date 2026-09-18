"""Análise de preços históricos via DuckDB lendo Parquets do MinIO."""
import os
import tempfile
from pathlib import Path
import boto3
import duckdb

BUCKET = "price-history"


def _s3():
    return boto3.client(
        "s3",
        endpoint_url=f"http://{os.getenv('MINIO_ENDPOINT', 'minio:9000')}",
        aws_access_key_id=os.getenv("MINIO_ACCESS_KEY", "minioadmin"),
        aws_secret_access_key=os.getenv("MINIO_SECRET_KEY", "minioadmin"),
        region_name="us-east-1",
    )


def _download_parquets(dest: str) -> int:
    """Baixa todos os .parquet do bucket para dest/. Retorna contagem."""
    s3 = _s3()
    n = 0
    try:
        objs = s3.list_objects_v2(Bucket=BUCKET)
    except Exception:
        return 0
    for obj in objs.get("Contents", []):
        key = obj["Key"]
        if not key.endswith(".parquet"):
            continue
        data = s3.get_object(Bucket=BUCKET, Key=key)["Body"].read()
        (Path(dest) / Path(key).name).write_bytes(data)
        n += 1
    return n


def _load_view(con, parquet_dir: str):
    pattern = str(Path(parquet_dir) / "*.parquet")
    con.execute(
        f"CREATE OR REPLACE VIEW prices AS "
        f"SELECT * FROM read_parquet('{pattern}')"
    )


def get_price_stats(product_id: int | None = None) -> dict:
    """Preço médio, mínimo, máximo e contagem para um produto (ou todos)."""
    with tempfile.TemporaryDirectory() as tmp:
        n = _download_parquets(tmp)
        if n == 0:
            return {"error": "sem parquets no bucket", "count": 0}
        con = duckdb.connect()
        _load_view(con, tmp)
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
    with tempfile.TemporaryDirectory() as tmp:
        n = _download_parquets(tmp)
        if n == 0:
            return {"error": "sem parquets no bucket"}
        con = duckdb.connect()
        _load_view(con, tmp)
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
