import os
import requests
import json
from datetime import datetime
import pandas as pd
import numpy as np

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

def fetch_cot_data(dataset_code, name):
    try:
        api_key = os.environ["NASDAQ_API_KEY"]
        url = f"https://data.nasdaq.com/api/v3/datasets/CFTC/{dataset_code}.json"
        params = {
            "api_key": api_key,
            "rows": 52
        }
        response = requests.get(url, params=params, timeout=30)
        data = response.json()
        columns = data["dataset"]["column_names"]
        rows = data["dataset"]["data"]
        df = pd.DataFrame(rows, columns=columns)
        df["Date"] = pd.to_datetime(df["Date"])
        df = df.sort_values("Date")
        print(f"✅ {name}: {len(df)} שורות")
        return df
    except Exception as e:
        print(f"⚠️ שגיאה ב-{name}: {e}")
        return None

def analyze_cot(gold_df, dollar_df, euro_df):
    results = {}

    for name, df, long_col, short_col in [
        ("זהב", gold_df, "Money Manager Longs", "Money Manager Shorts"),
        ("דולר", dollar_df, "Money Manager Longs", "Money Manager Shorts"),
        ("יורו", euro_df, "Money Manager Longs", "Money Manager Shorts"),
    ]:
        try:
            df = df.copy()

            # מוסדיים (Non-Commercial)
            df["mm_net"] = df[long_col] - df[short_col]
            df["mm_pct"] = df["mm_net"].rank(pct=True) * 100

            # מסחריים (Commercial)
            df["comm_net"] = df["Comm Positions-Long (All)"] - df["Comm Positions-Short (All)"]
            df["comm_pct"] = df["comm_net"].rank(pct=True) * 100

            # קטנים (Non-Reportable)
            df["small_net"] = df["Nonrept. Positions-Long (All)"] - df["Nonrept. Positions-Short (All)"]

            latest = df.iloc[-1]
            prev = df.iloc[-2]

            mm_change = latest["mm_net"] - prev["mm_net"]
            comm_change = latest["comm_net"] - prev["comm_net"]

            results[name] = {
                "date": latest["Date"].strftime("%d/%m/%Y"),
                "mm_net": int(latest["mm_net"]),
                "mm_pct": round(latest["mm_pct"], 1),
                "mm_change": int(mm_change),
                "comm_net": int(latest["comm_net"]),
                "comm_pct": round(latest["comm_pct"], 1),
                "comm_change": int(comm_change),
                "small_net": int(latest["small_net"])
            }
        except Exception as e:
            print(f"שגיאה בניתוח {name}: {e}")

    return results

def get_ai_analysis(results):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {os.environ['GROQ_API_KEY']}",
        "Content-Type": "application/json"
    }

    results_text = json.dumps(results, ensure_ascii=False, indent=2)

    prompt = f"""אתה אנליסט פורקס וסחורות בכיר המתמחה בדוחות COT.
קיבלת נתוני COT עבור זהב, דולר ויורו.
כתוב ניתוח מקצועי מפורט בעברית בלבד.

הנתונים:
{results_text}

כתוב לפי המבנה הבא בדיוק:

דוח COT שבועי
תאריך דוח: {results.get('זהב', {}).get('date', '')}
━━━━━━━━━━━━━━━

🥇 זהב

👥 ספקולנטים גדולים (Non-Commercial):
פוזיציה נטו: [ערך] חוזים
אחוזון היסטורי: [ערך]% מתוך 52 שבועות
שינוי שבועי: [עלה/ירד] ב-[ערך] חוזים
משמעות: [הסבר קצר מה זה אומר]
על מה להסתכל: [טיפ מקצועי]

🏭 מסחריים (Commercial/Hedgers):
פוזיציה נטו: [ערך] חוזים
אחוזון היסטורי: [ערך]%
שינוי שבועי: [עלה/ירד] ב-[ערך] חוזים
משמעות: [הסבר קצר]

👤 סוחרים קטנים (Non-Reportable):
פוזיציה נטו: [ערך] חוזים
משמעות: [הסבר קצר]

📊 סיכום זהב:
[ניתוח מה הדוח אומר על כיוון הזהב — שורי/דובי/ניטרלי ולמה]
━━━━━━━━━━━━━━━

💵 דולר אמריקאי

[אותו מבנה כמו זהב]

📊 סיכום דולר:
[ניתוח מה הדוח אומר על כיוון הדולר]
━━━━━━━━━━━━━━━

💶 יורו

[אותו מבנה כמו זהב]

📊 סיכום יורו:
[ניתוח מה הדוח אומר על כיוון היורו]
━━━━━━━━━━━━━━━

🔍 מסקנה כללית:
[ניתוח של הקשר בין שלושת הנכסים ומה זה אומר על השוק]

כתוב בעברית בלבד. ללא כוכביות או markdown. מקצועי וקולע."""

    data = {
        "model": "llama-3.3-70b-versatile",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 3000
    }
    response = requests.post(url, headers=headers, json=data, timeout=30)
    return response.json()["choices"][0]["message"]["content"]

def send_to_telegram(message):
    token = os.environ["TELEGRAM_TOKEN"]
    chat_id = os.environ["TELEGRAM_CHAT_ID"]
    url = f"https://api.telegram.org/bot{token}/sendMessage"

    max_length = 4000
    parts = [message[i:i+max_length] for i in range(0, len(message), max_length)]

    for i, part in enumerate(parts):
        if i > 0:
            part = "המשך...\n\n" + part
        response = requests.post(url, json={
            "chat_id": chat_id,
            "text": part
        }, timeout=10)
        print(f"Telegram חלק {i+1}:", response.json().get("ok"))

if __name__ == "__main__":
    print("שואב נתוני COT...")

    # קודי Nasdaq לכל נכס
    gold_df = fetch_cot_data("088691_FO_ALL", "זהב")
    dollar_df = fetch_cot_data("098662_FO_ALL", "דולר")
    euro_df = fetch_cot_data("099741_FO_ALL", "יורו")

    if gold_df is None and dollar_df is None and euro_df is None:
        print("לא ניתן לשאוב נתונים — לא נשלח כלום")
    else:
        results = analyze_cot(gold_df, dollar_df, euro_df)
        analysis = get_ai_analysis(results)

        header = f"""📊 דוח COT שבועי
📅 {get_hebrew_date()}
━━━━━━━━━━━━━━━

"""
        signature = """

━━━━━━━━━━━━━━━
🏢 קבוצת B&B
📚 למטרות לימוד בלבד
⚠️ האמור אינו מהווה ייעוץ השקעות"""

        send_to_telegram(header + analysis + signature)
        print("נשלח בהצלחה!")
