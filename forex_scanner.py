import os
import requests
import json
from datetime import datetime, timedelta

def get_hebrew_date(date):
    days = {
        0: "יום שני", 1: "יום שלישי", 2: "יום רביעי",
        3: "יום חמישי", 4: "יום שישי", 5: "יום שבת", 6: "יום ראשון"
    }
    months = {
        1: "ינואר", 2: "פברואר", 3: "מרץ", 4: "אפריל",
        5: "מאי", 6: "יוני", 7: "יולי", 8: "אוגוסט",
        9: "ספטמבר", 10: "אוקטובר", 11: "נובמבר", 12: "דצמבר"
    }
    return f"{days[date.weekday()]} | {date.day} {months[date.month]} {date.year}"

def fetch_events(week="thisweek"):
    try:
        url = f"https://nfs.faireconomy.media/ff_calendar_{week}.json"
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code == 200 and response.text.strip():
            data = response.json()
            high_impact = [e for e in data if e.get("impact", "") == "High"]
            print(f"✅ {week}: {len(high_impact)} אירועים גבוהים")
            return high_impact
        return []
    except Exception as e:
        print(f"⚠️ {week}: {e}")
        return []

def parse_date(date_str):
    try:
        return datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S%z").replace(tzinfo=None)
    except:
        return None

def get_week_events():
    today = datetime.now()
    # שבת — שאוב thisweek + nextweek וסנן לשבוע הבא
    next_sunday = today + timedelta(days=1)
    next_friday = next_sunday + timedelta(days=5)

    all_events = fetch_events("thisweek") + fetch_events("nextweek")

    week_events = []
    for event in all_events:
        event_date = parse_date(event["date"])
        if event_date and next_sunday.date() <= event_date.date() <= next_friday.date():
            week_events.append(event)

    return week_events, next_sunday, next_friday

def analyze_week_events(events):
    if not events:
        return None

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {os.environ['GROQ_API_KEY']}",
        "Content-Type": "application/json"
    }

    events_text = json.dumps(events, ensure_ascii=False, indent=2)

    prompt = f"""אתה אנליסט פורקס בכיר.
קיבלת רשימת אירועים כלכליים לשבוע הבא.
כתוב ניתוח מקצועי בעברית בלבד.

האירועים:
{events_text}

חלק לפי ימים. עבור כל יום:
[שם היום ותאריך]
━━━━━━━━━━━━━━━
עבור כל אירוע:
🕐 [שעה בשעון ישראל UTC+3]
📌 [שם האירוע] — [מדינה/מטבע]
📊 נוכחי: [ערך נוכחי] | צפי: [ערך צפוי]
📝 [הסבר קצר מה זה]
📈 גבוה מהצפי: [השפעה על דולר/יורו/זהב]
📉 נמוך מהצפי: [השפעה על דולר/יורו/זהב]
➡️ ללא שינוי: [השפעה על דולר/יורו/זהב]
⭐ [אם זה הכי חשוב של היום — ציין]

ללא כוכביות או markdown. קצר וקולע."""

    data = {
        "model": "llama-3.3-70b-versatile",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 3000
    }
    response = requests.post(url, headers=headers, json=data, timeout=30)
    return response.json()["choices"][0]["message"]["content"]

def save_events(events):
    try:
        with open("forex_events.json", "w", encoding="utf-8") as f:
            json.dump(events, f, ensure_ascii=False, indent=2)
        print("✅ אירועים נשמרו")
    except Exception as e:
        print(f"שגיאה בשמירה: {e}")

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
    today = datetime.now()
    print(f"היום: {today.strftime('%A')} | weekday: {today.weekday()}")

    # שבת = weekday 5
    if today.weekday() == 5:
        print("מצב שבת — שואב אירועים לשבוע הבא...")
        week_events, next_sunday, next_friday = get_week_events()

        if not week_events:
            print("אין אירועים גבוהי השפעה לשבוע הבא")
        else:
            print(f"נמצאו {len(week_events)} אירועים")
            save_events(week_events)

            header = f"""📅 אירועים כלכליים חשובים
שבוע {get_hebrew_date(next_sunday)} עד {get_hebrew_date(next_friday)}
🔴 השפעה גבוהה בלבד
━━━━━━━━━━━━━━━

"""
            analysis = analyze_week_events(week_events)
            signature = """

━━━━━━━━━━━━━━━
🏢 קבוצת B&B
📊 ניתוח אירועים כלכליים שבועי
⚠️ האמור אינו מהווה ייעוץ השקעות"""

            send_to_telegram(header + analysis + signature)
            print("נשלח בהצלחה!")
    else:
        print("לא שבת — הקובץ הזה רץ רק בשבת")
        print("התזכורות מנוהלות על ידי forex_reminder.py")
