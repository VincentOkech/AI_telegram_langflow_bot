TELEGRAM_TOKEN = "7867905932:AJSjZ548"
import requests
url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getMe"
response = requests.get(url)
print(response.json())
