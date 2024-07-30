import json
from bs4 import BeautifulSoup
import requests
from transformers import pipeline
import threading

try:
    summarizer = pipeline("summarization", model="facebook/bart-large-cnn")
except RuntimeError as e:
    print(f"Failed to initialize the summarizer: {e}")
    exit(1)

urls = []

def split_text(text, max_length=512):
    sentences = text.split('. ')
    chunks = []
    current_chunk = []
    current_length = 0
    
    for sentence in sentences:
        sentence_length = len(sentence.split())
        if current_length + sentence_length <= max_length:
            current_chunk.append(sentence)
            current_length += sentence_length
        else:
            chunks.append('. '.join(current_chunk))
            current_chunk = [sentence]
            current_length = sentence_length
    
    if current_chunk:
        chunks.append('. '.join(current_chunk))
    
    return chunks

def summarize_text(text):
    chunks = split_text(text)
    summaries = []
    
    def summarize_chunk(chunk):
        try:
            summary = summarizer(chunk, max_length=130, min_length=30, do_sample=False)
            summaries.append(summary[0]['summary_text'])
        except Exception as e:
            print(f"Error summarizing chunk: {e}")
    
    threads = []
    for chunk in chunks:
        thread = threading.Thread(target=summarize_chunk, args=(chunk,))
        threads.append(thread)
        thread.start()
    
    for thread in threads:
        thread.join()
    
    return ' '.join(summaries)

def toi_scrap():
    result = {}
    for url in urls:
        res = requests.get(url)
        sp = BeautifulSoup(res.text, "html.parser")
        script_tags = sp.find_all("script", type="application/ld+json")

        article_data = {}
        for i, script in enumerate(script_tags):
            script_content = script.get_text()
            try:
                json_data = json.loads(script_content)
                if json_data.get("@type") == "NewsArticle":
                    name = json_data.get("name")
                    article_body = json_data.get("articleBody")
                    if name and article_body:
                        article_data["name"] = name
                        article_data["articleBody"] = article_body
                        article_data["articleSummary"] = summarize_text(article_body)
                    elif name:
                        article_data["name"] = name
                    elif article_body:
                        article_data["articleBody"] = article_body
                        article_data["articleSummary"] = summarize_text(article_body)
                else:
                    name = json_data.get("name")
                    article_body = json_data.get("articleBody")
                    if name:
                        article_data["name"] = name
                    if article_body:
                        article_data["articleBody"] = article_body
                        article_data["articleSummary"] = summarize_text(article_body)
            except json.JSONDecodeError as e:
                print(f"Error decoding JSON in script {i} from {url}: {e}")
                continue

        result[url] = article_data

    with open("scraped_data.json", "w") as f:
        json.dump(result, f, indent=2)

    print("JSON data saved successfully to scraped_data.json")

def retrieve_data():
    with open('scrap_main_text.json') as f:
        data = json.load(f)
    for i in data:
        urls.append(i.get('link'))

if __name__ == "__main__":
    retrieve_data()
    toi_scrap()
