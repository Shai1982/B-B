import os
import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def get_hebrew_date():
    days = {
        0: "יום שני",
        1: "יום שלישי",
        2: "יום רביעי",
        3: "יום חמישי",
        4: "יום שישי",
        5: "יום שבת",
        6: "יום ראשון"
    }
    months = {
        1: "ינואר", 2: "פברואר", 3: "מרץ",
        4: "אפריל", 5: "מאי", 6: "יוני",
        7: "יולי", 8: "אוגוסט", 9: "ספטמבר",
        10: "אוקטובר", 11: "נובמבר", 12: "דצמבר"
    }
    now = datetime.now()
    return f"{days[now.weekday()]} | {now.day} {months[now.month]} {now.year}"

def get_gold_price():
    try:
        url = "https://query1.finance.yahoo.com/v8/finance/chart/GC=F"
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=10)
        data = response.json()
        price = data["chart"]["result"][0]["meta"]["regularMarketPrice"]
        return round(price, 2)
    except Exception as e:
        print(f"שגיאה בזהב: {e}")
        return None

def get_crypto_prices():
    try:
        url = "https://api.coingecko.com/api/v3/simple/price"
        params = {
            "ids": "bitcoin,ethereum",
            "vs_currencies": "usd",
            "include_24hr_change": "true"
        }
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        btc = round(data["bitcoin"]["usd"], 2)
        btc_change = round(data["bitcoin"]["usd_24h_change"], 2)
        eth = round(data["ethereum"]["usd"], 2)
        eth_change = round(data["ethereum"]["usd_24h_change"], 2)
        return btc, btc_change, eth, eth_change
    except Exception as e:
        print(f"שגיאה בקריפטו: {e}")
        return None, None, None, None

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

def fetch_cot_data():
    try:
        api_key = os.environ["NASDAQ_API_KEY"]
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=36*30)).strftime("%Y-%m-%d")
        url = "https://data.nasdaq.com/api/v3/datasets/CFTC/088691_FO_ALL.json"
        params = {
            "api_key": api_key,
            "start_date": start_date,
            "end_date": end_date
        }
        response = requests.get(url, params=params, timeout=30)
        data = response.json()
        columns = data["dataset"]["column_names"]
        rows = data["dataset"]["data"]
        df = pd.DataFrame(rows, columns=columns)
        df["Date"] = pd.to_datetime(df["Date"])
        df = df.sort_values("Date")
        print(f"✅ COT: {len(df)} שורות")
        return df
    except Exception as e:
        print(f"⚠️ שגיאה ב-COT: {e}")
        return None

def analyze_cot(df):
    try:
        long_col = "Money Manager Longs"
        short_col = "Money Manager Shorts"
        df["net"] = df[long_col] - df[short_col]
        df["net_pct"] = df["net"].rank(pct=True) * 100
        latest = df.iloc[-1]
        prev = df.iloc[-2]
        weekly_change = latest["net"] - prev["net"]
        change_dir = "הגדילו" if weekly_change > 0 else "הקטינו"
        df["month"] = df["Date"].dt.month
        monthly_avg = df.groupby("month")["net"].mean()
        current_month = datetime.now().month
        seasonal = "חיובית ✅" if monthly_avg[current_month] > monthly_avg.mean() else "שלילית ⚠️"
        current_pct = latest["net_pct"]
        similar = df[
            (df["net_pct"] >= current_pct - 10) &
            (df["net_pct"] <= current_pct + 10) &
            (df["Date"] < latest["Date"])
        ]
        if latest["net_pct"] >= 80:
            extreme = "EXTREME LONG 🔴 — סיכון גבוה לתיקון"
        elif latest["net_pct"] <= 20:
            extreme = "EXTREME SHORT 🟢 — הזדמנות קנייה"
        elif latest["net_pct"] >= 60:
            extreme = "לונג מעל הממוצע 🟡"
        else:
            extreme = "ניטרלי ⚪"
        report_date = latest["Date"].strftime("%d/%m/%Y")
        return f"""📋 *ניתוח COT — Smart Money*
דוח אחרון: {report_date}
פוזיציה נטו: *{int(latest['net']):,}* חוזים
אחוזון היסטורי: *{latest['net_pct']:.0f}%* — {extreme}
שינוי שבועי: {change_dir} ב־*{abs(int(weekly_change)):,}* חוזים
עונתיות חודש {current_month}: {seasonal}
מצבים דומים בעבר: *{len(similar)}* מקרים"""
    except Exception as e:
        print(f"שגיאה בניתוח COT: {e}")
        return None

def get_review(gold, btc, btc_change, eth, eth_change, fear, fear_label, cot_summary):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {os.environ['GROQ_API_KEY']}",
        "Content-Type": "application/json"
    }
    btc_arrow = "📈" if btc_change > 0 else "📉"
    eth_arrow = "📈" if eth_change > 0 else "📉"
    fear_emoji = "😱" if int(fear) < 25 else "😰" if int(fear) < 50 else "😊" if int(fear) < 75 else "🤑"
    hebrew_date = get_hebrew_date()
    cot_section = f"\nניתוח COT (36 חודשים):\n{cot_summary}\n" if cot_summary else ""

    signature = """
━━━━━━━━━━━━━━━
🏢 *קבוצת B&B*
📊 סקירה יומית מקצועית לסוחרי שוק ההון
⚠️ _האמור אינו מהווה ייעוץ השקעות_"""

    prompt = f"""אתה אנליסט פיננסי בכיר המתמחה בשוק הזהב והקריפטו.
כתוב סקירת בוקר יומית מקצועית בעברית בלבד לסוחרי שוק ההון.
השתמש בפורמט Markdown של טלגרם: *מודגש* לכותרות וערכים חשובים, _נטוי_ להערות.

נתונים אמיתיים:
זהב: ${gold:,} לאונקיה
ביטקוין: ${btc:,} — {btc_change}%
איתריום: ${eth:,} — {eth_change}%
מדד פחד/חמדנות: {fear}/100 ({fear_label})
{cot_section}

כתוב בדיוק לפי המבנה הבא:

🌅 *סקירת בוקר — שוק הזהב והקריפטו*
📅 {hebrew_date}
━━━━━━━━━━━━━━━

📊 *נתוני פתיחה*
🥇 זהב: *${gold:,}* לאונקיה
₿ ביטקוין: *${btc:,}* ({btc_change}% {btc_arrow})
🔷 איתריום: *${eth:,}* ({eth_change}% {eth_arrow})
{fear_emoji} פחד/חמדנות: *{fear}/100* — {fear_label}
━━━━━━━━━━━━━━━

{"📋 *ניתוח COT — Smart Money*" + chr(10) + "נתח לעומק את נתוני ה-COT ומשמעותם לכיוון השוק." + chr(10) + "━━━━━━━━━━━━━━━" if cot_summary else ""}

🌍 *גורמים מרכזיים היום*
פרט 3-4 גורמים ספציפיים עם השפעתם על השוק.
━━━━━━━━━━━━━━━

📈 *ניתוח טכני*
🥇 זהב: מגמה, תמיכה, התנגדות
₿ ביטקוין: מגמה, תמיכה, התנגדות
🔷 איתריום: מגמה, תמיכה, התנגדות
━━━━━━━━━━━━━━━

🔮 *תחזית יומית*
לכל נכס — כיוון צפוי עם רמות מחיר ספציפיות.
━━━━━━━━━━━━━━━

✅ *המלצה לסוחר*
לכל נכס: קנייה / המתנה / מכירה עם הסבר תמציתי.

כתוב בצורה מקצועית עם נתונים ספציפיים. השתמש ב-*מודגש* לערכי מחיר וכותרות. אל תוסיף חתימה בסוף."""

    data = {
        "model": "llama-3.3-70b-versatile",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 2000
    }
    response = requests.post(url, headers=headers, json=data, timeout=30)
    review = response.json()["choices"][0]["message"]["content"]
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
    gold = get_gold_price()
    btc, btc_change, eth, eth_change = get_crypto_prices()
    fear, fear_label = get_fear_greed()

    if not gold or not btc or not eth:
        print("חסרים נתונים — לא נשלח כלום")
    else:
        cot_df = fetch_cot_data()
        cot_summary = analyze_cot(cot_df) if cot_df is not None else None
        review = get_review(gold, btc, btc_change, eth, eth_change, fear, fear_label, cot_summary)
        send_to_telegram(review)
        print("נשלח בהצלחה!")
