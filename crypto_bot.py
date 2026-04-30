import os
import requests
import json
from datetime import datetime

def get_hebrew_date():
    days = {
        0: "יום שני", 1: "יום שלישי", 2: "יום רביעי",
        3: "יום חמישי", 4: "יום שישי", 5: "יום שבת", 6: "יום ראשון"
    }
    months = {
        1: "ינואר", 2: "פברואר", 3: "מרץ", 4: "אפריל",
        5: "מאי", 6: "יוני", 7: "יולי", 8: "אוגוסט",
        9: "ספטמבר", 10: "אוקטובר", 11: "נובמבר", 12: "דצמבר"
    }
    now = datetime.now()
    return f"{days[now.weekday()]} | {now.day} {months[now.month]} {now.year}"

def get_crypto_data():
    try:
        url = "https://api.coingecko.com/api/v3/coins/markets"
        params = {
            "vs_currency": "usd",
            "ids": "bitcoin,ethereum",
            "order": "market_cap_desc",
            "sparkline": "false",
            "price_change_percentage": "24h"
        }
        response = requests.get(url, params=params, timeout=15)
        data = response.json()
        
        btc = next(x for x in data if x["id"] == "bitcoin")
        eth = next(x for x in data if x["id"] == "ethereum")
        
        return {
            "btc_price": round(btc["current_price"], 2),
            "btc_change": round(btc["price_change_percentage_24h"], 2),
            "btc_high": round(btc["high_24h"], 2),
            "btc_low": round(btc["low_24h"], 2),
            "btc_volume": round(btc["total_volume"], 0),
            "btc_market_cap": round(btc["market_cap"], 0),
            "eth_price": round(eth["current_price"], 2),
            "eth_change": round(eth["price_change_percentage_24h"], 2),
            "eth_high": round(eth["high_24h"], 2),
            "eth_low": round(eth["low_24h"], 2),
            "eth_volume": round(eth["total_volume"], 0),
            "eth_market_cap": round(eth["market_cap"], 0)
        }
    except Exception as e:
        print(f"שגיאה ב-CoinGecko: {e}")
        return None

def get_fear_greed():
    try:
        url = "https://api.alternative.me/fng/"
        response = requests.get(url, timeout=10)
        data = response.json()
        value = data["data"][0]["value"]
        label = data["data"][0]["value_classification"]
        return value, label
    except:
        return None, None

def get_review(d, fear, fear_label):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {os.environ['GROQ_API_KEY']}",
        "Content-Type": "application/json"
    }

    btc_arrow = "📈" if d["btc_change"] > 0 else "📉"
    eth_arrow = "📈" if d["eth_change"] > 0 else "📉"
    fear_emoji = "😱" if int(fear) < 25 else "😰" if int(fear) < 50 else "😊" if int(fear) < 75 else "🤑"
    hebrew_date = get_hebrew_date()

    prompt = f"""אתה אנליסט קריפטו בכיר.
כתוב סקירת קריפטו מקצועית בעברית בלבד לסוחרים.
השתמש בפורמט Markdown של טלגרם: *מודגש* לכותרות וערכים חשובים, _נטוי_ להערות.

נתונים אמיתיים:
ביטקוין: ${d['btc_price']:,.2f} | שינוי: {d['btc_change']:.2f}% {btc_arrow}
BTC גבוה יומי: ${d['btc_high']:,.2f} | נמוך יומי: ${d['btc_low']:,.2f}
BTC נפח 24ש: ${d['btc_volume']:,.0f}
BTC שווי שוק: ${d['btc_market_cap']:,.0f}

איתריום: ${d['eth_price']:,.2f} | שינוי: {d['eth_change']:.2f}% {eth_arrow}
ETH גבוה יומי: ${d['eth_high']:,.2f} | נמוך יומי: ${d['eth_low']:,.2f}
ETH נפח 24ש: ${d['eth_volume']:,.0f}
ETH שווי שוק: ${d['eth_market_cap']:,.0f}

מדד פחד/חמדנות: {fear}/100 {fear_emoji} ({fear_label})

כתוב לפי המבנה הבא בדיוק:

🔷 *סקירת קריפטו — Live*
📅 {hebrew_date}
━━━━━━━━━━━━━━━

📊 *נתוני שוק בזמן אמת*
₿ *ביטקוין:* ${d['btc_price']:,.2f} ({d['btc_change']:.2f}% {btc_arrow})
📊 גבוה: *${d['btc_high']:,.2f}* | נמוך: *${d['btc_low']:,.2f}*
💰 נפח 24ש: *${d['btc_volume']:,.0f}*
🏦 שווי שוק: *${d['btc_market_cap']:,.0f}*

🔷 *איתריום:* ${d['eth_price']:,.2f} ({d['eth_change']:.2f}% {eth_arrow})
📊 גבוה: *${d['eth_high']:,.2f}* | נמוך: *${d['eth_low']:,.2f}*
💰 נפח 24ש: *${d['eth_volume']:,.0f}*
🏦 שווי שוק: *${d['eth_market_cap']:,.0f}*

{fear_emoji} *פחד/חמדנות:* {fear}/100 — {fear_label}
━━━━━━━━━━━━━━━

🌍 *ניתוח סנטימנט*
נתח את מדד הפחד/חמדנות ונפחי המסחר ומה הם מסמנים.
━━━━━━━━━━━━━━━

📈 *ניתוח טכני*
₿ ביטקוין: מגמה, תמיכה, התנגדות
🔷 איתריום: מגמה, תמיכה, התנגדות
━━━━━━━━━━━━━━━

🔮 *תחזית*
כיוון צפוי לכל נכס עם רמות מחיר ספציפיות.
━━━━━━━━━━━━━━━

✅ *המלצה לסוחר*
קנייה / המתנה / מכירה לכל נכס עם הסבר תמציתי.

כתוב בצורה מקצועית עם נתונים ספציפיים. אל תוסיף חתימה בסוף."""

    data = {
        "model": "llama-3.3-70b-versatile",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 2000
    }
    response = requests.post(url, headers=headers, json=data, timeout=30)
    review = response.json()["choices"][0]["message"]["content"]

    signature = """
━━━━━━━━━━━━━━━
🏢 *קבוצת B&B*
📊 סקירת קריפטו יומית מקצועית
⚠️ _האמור אינו מהווה ייעוץ השקעות_"""

    return review + signature

def send_to_telegram(message):
    token = os.environ["TELEGRAM_TOKEN"]
    chat_id = os.environ["TELEGRAM_CHAT_ID"]
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    response = requests.post(url, json={
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "Markdown"
    }, timeout=10)
    print("Telegram:", response.json())

if __name__ == "__main__":
    d = get_crypto_data()
    fear, fear_label = get_fear_greed()

    if not d or not fear:
        print("חסרים נתונים — לא נשלח כלום")
    else:
        review = get_review(d, fear, fear_label)
        send_to_telegram(review)
        print("נשלח בהצלחה!")
