import os
import requests

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def send_telegram_alert(product_title, current_price, target_price):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("⚠️ Telegram não configurado.")
        return False
    message = f"🔔 *Alerta de Preço!*\n\nProduto: {product_title}\nPreço atual: R$ {current_price:.2f}\nPreço alvo: R$ {target_price:.2f}\n\nAcesse o sistema para mais detalhes."
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        resp = requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"})
        if resp.status_code == 200:
            print("✅ Mensagem enviada para o Telegram")
            return True
        else:
            print(f"❌ Erro: {resp.text}")
            return False
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False
