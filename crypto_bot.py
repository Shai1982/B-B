
import os
import requests
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

def get_bybit_data(symbol):
    try:
        url = "https://api.bybit.com/v5/market/tickers"
        params = {"category": "linear", "symbol": symbol}
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        ticker = data["result"]["list"][0]
        return {
            "price": float(ticker["lastPrice"]),
            "change": float(ticker["price24hPcnt"]) * 100,
            "high": float(ticker["highPrice24h"]),
            "low": float(ticker["lowPrice24h"]),
            "volume": float(ticker["volume24h"]),
            "funding_rate": float(ticker["fundingRate"]) * 100,
            "open_interest": float(ticker["openInterest"])
        }
    except Exception as e:
        print(f"שגיאה ב-Bybit {symbol}: {e}")
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

def get_review(btc, eth, fear, fear_label):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {os.environ['GROQ_API_KEY']}",
        "Content-Type": "application/json"
    }

    btc_arrow = "📈" if btc["change"] > 0 else "📉"
    eth_arrow = "📈" if eth["change"] > 0 else "📉"
    fear_emoji = "😱" if int(fear) < 25 else "😰" if int(fear) < 50 else "😊" if int(fear) < 75 else "🤑"
    btc_funding = "שורי 🟢" if btc["funding_rate"] > 0 else "דובי 🔴"
    eth_funding = "שורי 🟢" if eth["funding_rate"] > 0 else "דובי 🔴"
    hebrew_date = get_hebrew_date()

    prompt = f"""אתה אנליסט קריפטו בכיר.
כתוב סקירת קריפטו מקצועית בעברית בלבד לסוחרים.
השתמש בפורמט Markdown של טלגרם: *מודגש* לכותרות וערכים חשובים, _נטוי_ להערות.

נתונים אמיתיים מ-Bybit:
ביטקוין: ${btc['price']:,.2f} | שינוי: {btc['change']:.2f}% {btc_arrow}
BTC גבוה יומי: ${btc['high']:,.2f} | נמוך יומי: ${btc['low']:,.2f}
BTC נפח 24ש: {btc['volume']:,.0f} | Open Interest: {btc['open_interest']:,.0f}
BTC Funding Rate: {btc['funding_rate']:.4f}% — {btc_funding}

איתריום: ${eth['price']:,.2f} | שינוי: {eth['change']:.2f}% {eth_arrow}
ETH גבוה יומי: ${eth['high']:,.2f} | נמוך יומי: ${eth['low']:,.2f}
ETH נפח 24ש: {eth['volume']:,.0f} | Open Interest: {eth['open_interest']:,.0f}
ETH Funding Rate: {eth['funding_rate']:.4f}% — {eth_funding}

מדד פחד/חמדנות: {fear}/100 {fear_emoji} ({fear_label})

כתוב לפי המבנה הבא בדיוק:

🔷 *סקירת קריפטו — Bybit Live*
📅 {hebrew_date}
━━━━━━━━━━━━━━━

📊 *נתוני שוק בזמן אמת*
₿ *ביטקוין:* ${btc['price']:,.2f} ({btc['change']:.2f}% {btc_arrow})
📊 גבוה: *${btc['high']:,.2f}* | נמוך: *${btc['low']:,.2f}*
💰 נפח 24ש: *{btc['volume']:,.0f}*
📌 Funding Rate: *{btc['funding_rate']:.4f}%* — {btc_funding}
📌 Open Interest: *{btc['open_interest']:,.0f}*

🔷 *איתריום:* ${eth['price']:,.2f} ({eth['change']:.2f}% {eth_arrow})
📊 גבוה: *${eth['high']:,.2f}* | נמוך: *${eth['low']:,.2f}*
💰 נפח 24ש: *{eth['volume']:,.0f}*
📌 Funding Rate: *{eth['funding_rate']:.4f}%* — {eth_funding}
📌 Open Interest: *{eth['open_interest']:,.0f}*

{fear_emoji} *פחד/חמדנות:* {fear}/100 — {fear_label}
━━━━━━━━━━━━━━━

🌍 *ניתוח סנטימנט*
נתח את ה-Funding Rate וה-Open Interest ומה הם מסמנים לגבי כיוון השוק.
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
    btc = get_bybit_data("BTCUSDT")
    eth = get_bybit_data("ETHUSDT")
    fear, fear_label = get_fear_greed()

    if not btc or not eth or not fear:
        print("חסרים נתונים — לא נשלח כלום")
    else:
        review = get_review(btc, eth, fear, fear_label)
        send_to_telegram(review)
        print("נשלח בהצלחה!")
