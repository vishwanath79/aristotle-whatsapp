import requests
import sys
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import datetime
from pathlib import Path

senddate = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
#sys.path[0] = str(Path(sys.path[0]).parent)
from cred import news_api_key

news_api_key = news_api_key



# Function to fetch news articles
def fetch_news(skeyword):
    url = f'https://newsapi.org/v2/everything?q={skeyword}&sortBy=popularity&pageSize=5&apiKey={news_api_key}'
    response = requests.get(url)

    if response.status_code == 200:
        answer = response.json()
        
        return answer
    return "No response from the news API"

