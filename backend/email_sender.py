import smtplib
from email.mime.text import MIMEText
import os
import math

SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = os.getenv("SMTP_PORT")
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASS")

def send_code(email: str, code: str):
    try:
        msg = MIMEText(f"Код для подтверждения регистрации: {code}")
        msg["Subject"] = "Подтверждение регистрации"
        msg["From"] = SMTP_USER
        msg["To"] = email

        with smtplib.SMTP_SSL(SMTP_SERVER, int(SMTP_PORT), timeout=30) as server:
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)
    except Exception as e:
        print(f"Не удалось отправить письмо с кодом: {e}")