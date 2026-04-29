import os
import requests
import json

def get_gold_price():
    url = "https://api.metals.live/v1/spot/gold"
    response = requests.get(url)
    data = response.json()
    return data[0]["price"]

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
            "content": f"כתוב סקירה יומית מקיפה על זהב בעברית. המחיר האמיתי של זהב היום הוא ${price} לאונקיה. כלול: מחיר נוכחי, גורמים גיאופוליטיים, ותחזית קצרה. השתמש באימוג'ים. הסקירה תהיה מקצועית וקצרה."
        }]
    }
    response = requests.post(url, headers=headers, json=data)
    result = response.json()
    return result["choices"][0]["message"]["content"]

def send_to_telegram(message):
    token = os.environ["TELEGRAM_TOKEN"]
    chat_id = os.environ["TELEGRAM_CHAT_ID"]
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    response = requests.post(url, json={
        "chat_id": chat_id,
        "text": message
    })
    print("Telegram response:", response.json())

if __name__ == "__main__":
    price = get_gold_price()
    print(f"מחיר זהב: ${price}")
    review = get_gold_review(price)
    send_to_telegram(review)
    print("נשלח בהצלחה!")
