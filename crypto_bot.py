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

def get_crypto_prices():
    try:
        url = "https://api.coingecko.com/api/v3/simple/price"
        params = {
            "ids": "bitcoin,ethereum",
            "vs_currencies": "usd",
            "include_24hr_change": "true",
            "include_24hr_vol": "true",
            "include_last_updated_at": "true"
        }
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        return {
            "btc_price": round(data["bitcoin"]["usd"], 2),
            "btc_change": round(data["bitcoin"]["usd_24h_change"], 2),
            "btc_volume": round(data["bitcoin"]["usd_24h_vol"], 0),
            "eth_price": round(data["ethereum"]["usd"], 2),
            "eth_change": round(data["ethereum"]["usd_24h_change"], 2),
            "eth_volume": round(data["ethereum"]["usd_24h_vol"], 0)
        }
    except Exception as e:
        print(f"שגיאה ב-CoinGecko: {e}")
        return None

def get_binance_data(symbol):
    try:
        # מחיר גבוה/נמוך
        ticker_url = f"https://api.binance.com/api/v3/ticker/24hr?symbol={symbol}"
        ticker = requests.get(ticker_url, timeout=10).json()

        # Funding Rate
        funding_url = f"https://fapi.binance.com/fapi/v1/fundingRate?symbol={symbol}&limit=1"
        funding = requests.get(funding_url, timeout=10).json()

        # Open Interest
        oi_url = f"https://fapi.binance.com/fapi/v1/openInterest?symbol={symbol}"
        oi = requests.get(oi_url, timeout=10).json()

        funding_rate = float(funding[0]["fundingRate"]) * 100

        return {
            "high": float(ticker["highPrice"]),
            "low": float(ticker["lowPrice"]),
            "funding_rate": funding_rate,
            "funding_sentiment": "שורי 🟢" if funding_rate > 0 else "דובי 🔴",
            "open_interest": float(oi["openInterest"])
        }
    except Exception as e:
        print(f"שגיאה ב-Binance {symbol}: {e}")
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

def get_review(prices, btc_data, eth_data, fear, fear_label):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {os.environ['GROQ_API_KEY']}",
        "Content-Type": "application/json"
    }

    btc_arrow = "📈" if prices["btc_change"] > 0 else "📉"
    eth_arrow = "📈" if prices["eth_change"] > 0 else "📉"
    fear_emoji = "😱" if int(fear) < 25 else "😰" if int(fear) < 50 else "😊" if int(fear) < 75 else "🤑"
    hebrew_date = get_hebrew_date()

    prompt = f"""אתה אנליסט קריפטו בכיר.
כתוב סקירת קריפטו מקצועית בעברית בלבד לסוחרים.
השתמש בפורמט Markdown של טלגרם: *מודגש* לכותרות וערכים חשובים, _נטוי_ להערות.

נתונים אמיתיים:
ביטקוין: ${prices['btc_price']:,.2f} | שינוי: {prices['btc_change']:.2f}% {btc_arrow}
BTC גבוה יומי: ${btc_data['high']:,.2f} | נמוך יומי: ${btc_data['low']:,.2f}
BTC נפח 24ש: ${prices['btc_volume']:,.0f}
BTC Funding Rate: {btc_data['funding_rate']:.4f}% — {btc_data['funding_sentiment']}
BTC Open Interest: {btc_data['open_interest']:,.0f}

איתריום: ${prices['eth_price']:,.2f} | שינוי: {prices['eth_change']:.2f}% {eth_arrow}
ETH גבוה יומי: ${eth_data['high']:,.2f} | נמוך יומי: ${eth_data['low']:,.2f}
ETH נפח 24ש: ${prices['eth_volume']:,.0f}
ETH Funding Rate: {eth_data['funding_rate']:.4f}% — {eth_data['funding_sentiment']}
ETH Open Interest: {eth_data['open_interest']:,.0f}

מדד פחד/חמדנות: {fear}/100 {fear_emoji} ({fear_label})

כתוב לפי המבנה הבא בדיוק:

🔷 *סקירת קריפטו — Live*
📅 {hebrew_date}
━━━━━━━━━━━━━━━

📊 *נתוני שוק בזמן אמת*
₿ *ביטקוין:* ${prices['btc_price']:,.2f} ({prices['btc_change']:.2f}% {btc_arrow})
📊 גבוה: *${btc_data['high']:,.2f}* | נמוך: *${btc_data['low']:,.2f}*
💰 נפח 24ש: *${prices['btc_volume']:,.0f}*
📌 Funding Rate: *{btc_data['funding_rate']:.4f}%* — {btc_data['funding_sentiment']}
📌 Open Interest: *{btc_data['open_interest']:,.0f}*

🔷 *איתריום:* ${prices['eth_price']:,.2f} ({prices['eth_change']:.2f}% {eth_arrow})
📊 גבוה: *${eth_data['high']:,.2f}* | נמוך: *${eth_data['low']:,.2f}*
💰 נפח 24ש: *${prices['eth_volume']:,.0f}*
📌 Funding Rate: *{eth_data['funding_rate']:.4f}%* — {eth_data['funding_sentiment']}
📌 Open Interest: *{eth_data['open_interest']:,.0f}*

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
    prices = get_crypto_prices()
    btc_data = get_binance_data("BTCUSDT")
    eth_data = get_binance_data("ETHUSDT")
    fear, fear_label = get_fear_greed()

    if not prices or not btc_data or not eth_data or not fear:
        print("חסרים נתונים — לא נשלח כלום")
    else:
        review = get_review(prices, btc_data, eth_data, fear, fear_label)
        send_to_telegram(review)
        print("נשלח בהצלחה!")
