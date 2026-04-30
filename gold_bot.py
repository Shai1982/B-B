import os
import requests
import pandas as pd
import numpy as np
from io import StringIO
import zipfile, io
from datetime import datetime

GOLD_MARKET_CODE = "088691"

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
    all_data = []
    current_year = datetime.now().year
    for year in range(current_year - 2, current_year + 1):
        try:
            url = f"https://www.cftc.gov/files/dea/history/fut_fin_txt_{year}.zip"
            response = requests.get(url, timeout=30)
            if response.status_code == 200:
                z = zipfile.ZipFile(io.BytesIO(response.content))
                df = pd.read_csv(z.open(z.namelist()[0]), low_memory=False)
                gold_df = df[df["CFTC_Market_Code"].astype(str).str.strip() == GOLD_MARKET_CODE]
                all_data.append(gold_df)
                print(f"✅ COT {year}: {len(gold_df)} שורות")
        except Exception as e:
            print(f"⚠️ COT {year}: {e}")
    if not all_data:
        return None
    combined = pd.concat(all_data, ignore_index=True)
    combined["Report_Date"] = pd.to_datetime(combined["As_of_Date_In_Form_YYMMDD"], format="%y%m%d")
    return combined.sort_values("Report_Date")

def analyze_cot(df):
    try:
        df = df.copy()
        df["net_large"] = df["M_Money_Positions_Long_All"] - df["M_Money_Positions_Short_All"]
        df["net_commercial"] = df["Comm_Positions_Long_All"] - df["Comm_Positions_Short_All"]
        df["large_pct"] = df["net_large"].rank(pct=True) * 100
        df["commercial_pct"] = df["net_commercial"].rank(pct=True) * 100

        latest = df.iloc[-1]
        prev = df.iloc[-2]
        weekly_change = latest["net_large"] - prev["net_large"]
        change_dir = "הגדילו" if weekly_change > 0 else "הקטינו"

        df["month"] = df["Report_Date"].dt.month
        monthly = df.groupby("month")["net_large"].mean()
        current_month = datetime.now().month
        seasonal = "חיובית" if monthly[current_month] > monthly.mean() else "שלילית"

        if latest["large_pct"] >= 80:
            extreme = "EXTREME LONG — סיכון לתיקון 🔴"
        elif latest["large_pct"] <= 20:
            extreme = "EXTREME SHORT — הזדמנות קנייה 🟢"
        elif latest["large_pct"] >= 60:
            extreme = "לונג מעל הממוצע 🟡"
        else:
            extreme = "ניטרלי ⚪"

        report_date = latest["Report_Date"].strftime("%d/%m/%Y")

        return f"""
דוח COT אחרון: {report_date}
מוסדיים נטו: {int(latest['net_large']):,} חוזים | אחוזון: {latest['large_pct']:.0f}% | {extreme}
שינוי שבועי: {change_dir} ב-{abs(int(weekly_change)):,} חוזים
מסחריים נטו: {int(latest['net_commercial']):,} חוזים | אחוזון: {latest['commercial_pct']:.0f}%
עונתיות חודש {current_month}: {seasonal} היסטורית
""".strip()
    except Exception as e:
        print(f"שגיאה בניתוח COT: {e}")
        return None

def get_review(gold, btc, btc_change, eth, eth_change, fear, fear_label, cot_summary):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {os.environ['GROQ_API_KEY']}",
        "Content-Type": "application/json"
    }
    cot_text = cot_summary if cot_summary else "נתוני COT לא זמינים היום"
    prompt = f"""אתה אנליסט פיננסי בכיר המתמחה בשוק הזהב והקריפטו.
כתוב סקירת בוקר יומית מקצועית בעברית בלבד לסוחרי שוק ההון.

נתונים אמיתיים:
זהב: ${gold} לאונקיה
ביטקוין: ${btc} (שינוי 24ש: {btc_change}%)
איתריום: ${eth} (שינוי 24ש: {eth_change}%)
מדד פחד/חמדנות: {fear}/100 ({fear_label})

ניתוח COT היסטורי:
{cot_text}

כתוב לפי המבנה הבא:

🌅 סקירת בוקר — שוק הזהב והקריפטו

📊 נתוני פתיחה
ציין את כל המחירים עם ניתוח קצר.

📋 ניתוח COT — Smart Money
נתח את נתוני ה-COT, מה המוסדיים עושים, ומה זה אומר לגבי הכיוון.

🌍 גורמים מרכזיים היום
3-4 גורמים ספציפיים המשפיעים על השווקים.

📈 ניתוח טכני
לכל נכס: מגמה, תמיכה, התנגדות.

🔮 תחזית יומית
כיוון צפוי לכל נכס עם רמות מחיר.

✅ המלצה לסוחר
קנייה / המתנה / מכירה לכל נכס עם הסבר תמציתי.

כתוב בצורה מקצועית עם נתונים ספציפיים. ללא כוכביות או markdown."""

    data = {
        "model": "llama-3.3-70b-versatile",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 2000
    }
    response = requests.post(url, headers=headers, json=data, timeout=30)
    return response.json()["choices"][0]["message"]["content"]

def send_to_telegram(message):
    token = os.environ["TELEGRAM_TOKEN"]
    chat_id = os.environ["TELEGRAM_CHAT_ID"]
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    response = requests.post(url, json={
        "chat_id": chat_id,
        "text": message
    }, timeout=10)
    print("Telegram:", response.json())

if __name__ == "__main__":
    gold = get_gold_price()
    btc, btc_change, eth, eth_change = get_crypto_prices()
    fear, fear_label = get_fear_greed()

    if not gold or not btc or not eth:
        print("חסרים נתונים — לא נשלח כלום")
    else:
        print("שואב COT...")
        cot_df = fetch_cot_data()
        cot_summary = analyze_cot(cot_df) if cot_df is not None else None
        review = get_review(gold, btc, btc_change, eth, eth_change, fear, fear_label, cot_summary)
        send_to_telegram(review)
        print("נשלח בהצלחה!")
