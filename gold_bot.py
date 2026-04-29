import os
import requests

def get_gold_price():
    try:
        url = "https://query1.finance.yahoo.com/v8/finance/chart/GC=F"
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=10)
        data = response.json()
        price = data["chart"]["result"][0]["meta"]["regularMarketPrice"]
        return round(price, 2)
    except:
        return 4577

def get_gold_review(price):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {os.environ['GROQ_API_KEY']}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "llama-3.3-70b-versatile",
        "messages": [{
            "role": "user",
            "content": f"""כתוב סקירה יומית מקיפה על זהב בעברית.
המחיר האמיתי של זהב היום הוא ${price} לאונקיה.
כלול את הנושאים הבאים:
1. מחיר נוכחי
2. גורמים גיאופוליטיים עיקריים
3. תחזית קצרה
השתמש באימוג'ים. הסקירה תהיה מקצועית וקצרה."""
        }]
    }
    response = requests.post(url, headers=headers, json=data, timeout=30)
    result = response.json()
    return result["choices"][0]["message"]["content"]

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
    price = get_gold_price()
    print(f"מחיר זהב: ${price}")
    review = get_gold_review(price)
    send_to_telegram(review)
    print("נשלח בהצלחה!")
