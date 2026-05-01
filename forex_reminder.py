import os
import requests
import json
from datetime import datetime, timedelta

def load_events():
    try:
        with open("forex_events.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"שגיאה בטעינת אירועים: {e}")
        return None

def get_todays_events(events):
    today = datetime.now().date()
    todays = []
    for event in events:
        try:
            event_date = datetime.strptime(event["date"], "%Y-%m-%dT%H:%M:%S%z").replace(tzinfo=None)
            if event_date.date() == today:
                todays.append({
                    "name": event.get("title", ""),
                    "country": event.get("country", ""),
                    "time": event_date,
                    "forecast": event.get("forecast", "אין"),
                    "previous": event.get("previous", "אין"),
                    "impact": event.get("impact", "")
                })
        except:
            continue
    return sorted(todays, key=lambda x: x["time"])

def get_upcoming_events(events):
    now = datetime.now()
    reminder_time = now + timedelta(minutes=30)
    upcoming = []
    for event in events:
        event_time = event["time"]
        if now <= event_time <= reminder_time + timedelta(minutes=5):
            upcoming.append(event)
    return upcoming

def analyze_reminder(events, all_today):
    if not events:
        return None

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {os.environ['GROQ_API_KEY']}",
        "Content-Type": "application/json"
    }

    is_most_important = len(all_today) > 1
    events_text = json.dumps([{
        "name": e["name"],
        "country": e["country"],
        "time": e["time"].strftime("%H:%M"),
        "forecast": e["forecast"],
        "previous": e["previous"]
    } for e in events], ensure_ascii=False)

    prompt = f"""אתה אנליסט פורקס בכיר.
עוד 30 דקות יתפרסמו האירועים הכלכליים הבאים.
כתוב תזכורת קצרה ומקצועית בעברית בלבד.

האירועים:
{events_text}

{"יש היום מספר אירועים — סמן אם זה הכי חשוב." if is_most_important else ""}

כתוב לפי המבנה:

⚡ תזכורת — עוד 30 דקות
━━━━━━━━━━━━━━━

עבור כל אירוע:
🕐 [שעה]
📌 [שם האירוע] — [מדינה]
📊 צפי: [ערך צפוי] | קודם: [ערך קודם]
📝 [הסבר קצר מה זה]
📈 נתון גבוה: [השפעה על דולר/יורו/זהב]
📉 נתון נמוך: [השפעה על דולר/יורו/זהב]
➡️ ללא שינוי: [השפעה על דולר/יורו/זהב]
{"⭐ זהו האירוע הכי חשוב של היום!" if is_most_important else ""}

כתוב בעברית בלבד. ללא כוכביות או markdown. קצר וקולע."""

    data = {
        "model": "llama-3.3-70b-versatile",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 1000
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
    print("Telegram:", response.json().get("ok"))

if __name__ == "__main__":
    print("בודק אירועים קרובים...")
    events = load_events()

    if not events:
        print("אין אירועים שמורים")
    else:
        todays_events = get_todays_events(events)

        if not todays_events:
            print("אין אירועים להיום")
        else:
            upcoming = get_upcoming_events(todays_events)

            if not upcoming:
                print("אין אירועים בעוד 30 דקות")
            else:
                print(f"נמצאו {len(upcoming)} אירועים קרובים")
                reminder = analyze_reminder(upcoming, todays_events)

                if reminder:
                    signature = """
━━━━━━━━━━━━━━━
🏢 קבוצת B&B
⚠️ האמור אינו מהווה ייעוץ השקעות"""
                    send_to_telegram(reminder + signature)
                    print("תזכורת נשלחה!")
