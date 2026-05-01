import os
import requests
import json
from datetime import datetime, timedelta
from xml.etree import ElementTree as ET

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

def fetch_forex_events():
    try:
        url = "https://nfs.faireconomy.media/ff_calendar_nextweek.json"
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=15)
        data = response.json()
        
        # סנן רק אירועים עם השפעה גבוהה
        high_impact = [e for e in data if e.get("impact", "") == "High"]
        print(f"נמצאו {len(high_impact)} אירועים בעלי השפעה גבוהה")
        return high_impact
    except Exception as e:
        print(f"שגיאה בשליפת אירועים: {e}")
        return None

def get_next_week_events(events):
    # מציאת ימי השבוע הבא (ראשון-שישי)
    today = datetime.now()
    days_until_sunday = (6 - today.weekday()) % 7
    if days_until_sunday == 0:
        days_until_sunday = 7
    next_sunday = today + timedelta(days=days_until_sunday)
    next_friday = next_sunday + timedelta(days=5)
    
    week_events = []
    for event in events:
        try:
            event_date = datetime.strptime(event["date"], "%Y-%m-%dT%H:%M:%S%z").replace(tzinfo=None)
            if next_sunday.date() <= event_date.date() <= next_friday.date():
                week_events.append(event)
        except:
            continue
    
    return week_events, next_sunday, next_friday

def analyze_events(events):
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
עבור כל אירוע כתוב ניתוח קצר ומקצועי.

האירועים:
{events_text}

כתוב את הניתוח לפי המבנה הבא — חלק לפי ימים:

עבור כל יום שיש בו אירועים כתוב:
[שם היום ותאריך]
━━━━━━━━━━━━━━━
עבור כל אירוע באותו יום:
🕐 [שעה בשעון ישראל UTC+3]
📌 [שם האירוע] — [מדינה/מטבע]
📊 נוכחי: [ערך נוכחי] | צפי: [ערך צפוי]
📝 [הסבר קצר מה זה האירוע]
📈 נתון גבוה מהצפי: [השפעה על דולר/יורו/זהב]
📉 נתון נמוך מהצפי: [השפעה על דולר/יורו/זהב]
➡️ ללא שינוי: [השפעה על דולר/יורו/זהב]
⭐ חשיבות: [אם זה האירוע הכי חשוב של היום — ציין זאת]

כתוב בעברית בלבד. ללא כוכביות או markdown. קצר וקולע."""

    data = {
        "model": "llama-3.3-70b-versatile",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 3000
    }
    response = requests.post(url, headers=headers, json=data, timeout=30)
    return response.json()["choices"][0]["message"]["content"]

def save_events_for_reminders(events):
    try:
        with open("forex_events.json", "w", encoding="utf-8") as f:
            json.dump(events, f, ensure_ascii=False, indent=2)
        print("אירועים נשמרו לתזכורות")
    except Exception as e:
        print(f"שגיאה בשמירה: {e}")

def send_to_telegram(message):
    token = os.environ["TELEGRAM_TOKEN"]
    chat_id = os.environ["TELEGRAM_CHAT_ID"]
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    
    # שלח בחלקים אם ההודעה ארוכה מדי
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
    print("סורק אירועים כלכליים...")
    events = fetch_forex_events()
    
    if not events:
        print("לא נמצאו אירועים")
    else:
        week_events, next_sunday, next_friday = get_next_week_events(events)
        
        if not week_events:
            print("אין אירועים גבוהי השפעה לשבוע הבא")
        else:
            print(f"נמצאו {len(week_events)} אירועים לשבוע הבא")
            save_events_for_reminders(week_events)
            
            header = f"""📅 אירועים כלכליים חשובים
שבוע {get_hebrew_date(next_sunday)} עד {get_hebrew_date(next_friday)}
🔴 השפעה גבוהה בלבד
━━━━━━━━━━━━━━━

"""
            analysis = analyze_events(week_events)
            
            signature = """

━━━━━━━━━━━━━━━
🏢 קבוצת B&B
📊 ניתוח אירועים כלכליים שבועי
⚠️ האמור אינו מהווה ייעוץ השקעות"""
            
            full_message = header + analysis + signature
            send_to_telegram(full_message)
            print("נשלח בהצלחה!")
