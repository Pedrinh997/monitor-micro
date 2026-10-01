import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
EMAIL_FROM = os.getenv("EMAIL_FROM", SMTP_USER)

def send_price_alert(product_title: str, current_price: float, target_price: float, user_email: str):
    """Envia alerta de preço.

    - Se SMTP_USER/SMTP_PASSWORD definidos: usa STARTTLS + login (produção).
    - Se vazios: envia sem auth/TLS (Mailpit em dev).
    """
    subject = f"🔔 Alerta de Preço: {product_title}"
    body = f"""
Olá!

O produto '{product_title}' atingiu o preço alvo!

- Preço atual: US$ {current_price:.2f}
- Preço alvo:  US$ {target_price:.2f}

Acesse o sistema para mais detalhes.
"""

    msg = MIMEMultipart()
    msg['From'] = EMAIL_FROM or 'alerts@monitor.micro'
    msg['To'] = user_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain', 'utf-8'))

    try:
        if SMTP_USER and SMTP_PASSWORD:
            # Modo produção: TLS + auth
            server = smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=15)
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
        else:
            # Modo dev: Mailpit aceita SMTP puro sem auth
            server = smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=15)

        server.send_message(msg)
        server.quit()
        print(f"✅ Email enviado para {user_email}")
        return True
    except Exception as e:
        print(f"❌ Erro ao enviar email: {type(e).__name__}: {e}")
        return False
