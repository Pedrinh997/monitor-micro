from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
from datetime import datetime, timedelta
import requests
import json
import os
import boto3
from io import StringIO
import pandas as pd

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2026, 9, 8),
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    'scrape_all_products',
    default_args=default_args,
    description='Scraping todos os produtos e salvando no MinIO',
    schedule_interval='0 */6 * * *',  # a cada 6 horas (já ajustado)
    catchup=False,
)

def scrape_and_save(**context):
    # 1. Busca produtos do banco (via PostgresHook)
    pg_hook = PostgresHook(postgres_conn_id='monitor_db')
    conn = pg_hook.get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT id, url FROM products")
    products = cursor.fetchall()
    cursor.close()
    conn.close()
    
    # 2. Para cada produto, faz scraping (simulado) e coleta dados
    # Aqui você pode chamar seu scraper real ou apenas simular com preço aleatório
    import random
    results = []
    for prod_id, url in products:
        # Chama sua API de scraping (ou função local)
        # Vamos simular:
        price = round(random.uniform(50, 200), 2)
        results.append({
            'product_id': prod_id,
            'price': price,
            'currency': 'BRL',
            'scraped_at': datetime.now().isoformat()
        })
    
    # 3. Converte para DataFrame e salva em Parquet no MinIO
    df = pd.DataFrame(results)
    buffer = StringIO()
    df.to_parquet(buffer, index=False)
    
    # 4. Conecta ao MinIO (S3)
    s3 = boto3.client(
        's3',
        endpoint_url='http://minio:9000',
        aws_access_key_id='minioadmin',
        aws_secret_access_key='minioadmin',
        region_name='us-east-1'
    )
    # Cria bucket se não existir
    try:
        s3.head_bucket(Bucket='price-history')
    except:
        s3.create_bucket(Bucket='price-history')
    
    # Salva o arquivo com timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    s3.put_object(
        Bucket='price-history',
        Key=f'scrapes/{timestamp}.parquet',
        Body=buffer.getvalue()
    )
    
    print(f"✅ Salvos {len(results)} registros no MinIO")

with dag:
    scrape_task = PythonOperator(
        task_id='scrape_and_save_to_minio',
        python_callable=scrape_and_save,
        provide_context=True,
    )
