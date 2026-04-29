import os
import requests

def get_gold_review():
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {os.environ['GROQ_API_KEY']}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "llama3-70b-8192",
        "messages": [{
            "role": "user",
            "content": "כתוב סקירה יומית מקיפה על זהב בעברית הכוללת: מחיר נוכחי, גורמים גיאופוליטיים, ותחזית קצרה. השתמש באימוג'ים. הסקירה תהיה מקצועית וקצרה."
        }]
    }
    response = requests.post(url, headers=headers, json=data)
    return response.json()["choices"][0]["message"]["content"]

def send_to_telegram(message):
    token = os.environ["TELEGRAM_TOKEN"]
    chat_id = os.environ["TELEGRAM_CHAT_ID"]
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    requests.post(url, json={
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "HTML"
    })

if __name__ == "__main__":
    review = get_gold_review()
    send_to_telegram(review)
    print("נשלח בהצלחה!")
