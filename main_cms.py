import json
from bs4 import BeautifulSoup
import requests

url = "https://timesofindia.indiatimes.com/rssfeedstopstories.cms"

res = requests.get(url)
sp = BeautifulSoup(res.text, "xml")

items = sp.find_all("item")
json_data_list = []
for i, item in enumerate(items):
    try:
        title = item.find("title").get_text()
        link = item.find("link").get_text()
        description = item.find("description").get_text()
        pubDate = item.find("pubDate").get_text()
        
        json_data = {
            "title": title,
            "link": link,
            "description": description,
            "pubDate": pubDate
        }
        json_data_list.append(json_data)
    except AttributeError as e:
        print(f"Error processing item {i}: {e}")
        continue

with open("scrap_main_text.json", "w") as f:
    json.dump(json_data_list, f, indent=2)
