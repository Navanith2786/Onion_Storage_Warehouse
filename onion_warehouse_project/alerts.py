import os
import requests
import time
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def send_telegram_alert(message):
    if not BOT_TOKEN or not CHAT_ID:
        print("Telegram configuration missing!")
        return
    
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": f"🚨 Onion Warehouse Alert! 🚨\n\n{message}",
        "parse_mode": "Markdown"
    }
    
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        print("Telegram alert sent successfully")
    except Exception as e:
        print(f"Failed to send telegram alert: {e}")



# Cooldown: only send alerts once every 10 minutes
last_alert_time = 0
ALERT_COOLDOWN = 600  # 10 minutes in seconds

def check_thresholds(reading):
    global last_alert_time
    
    # Thresholds: 8-10°C, 65-70% RH
    temp = reading.get('temp')
    hum = reading.get('hum')
    
    if temp is None or hum is None:
        return
    
    alerts = []
    if temp > 10:
        alerts.append(f"🌡️ High Temperature: {temp}°C (Safe range: 8-10°C)")
    elif temp < 8:
        alerts.append(f"🌡️ Low Temperature: {temp}°C (Safe range: 8-10°C)")
        
    if hum > 70:
        alerts.append(f"💧 High Humidity: {hum}% (Safe range: 65-70%)")
    elif hum < 65:
        alerts.append(f"💧 Low Humidity: {hum}% (Safe range: 65-70%)")
        
    if alerts and (time.time() - last_alert_time) > ALERT_COOLDOWN:
        send_telegram_alert("\n".join(alerts))
        last_alert_time = time.time()
