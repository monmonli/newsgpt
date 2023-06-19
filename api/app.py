from flask import Flask, jsonify, request
import openai
import json
from string import Template
import requests
import yaml
from copy import deepcopy
from langdetect import detect

with open("./config.yml", "r") as f:
    config = yaml.safe_load(f)

openai.api_key = config["OPENAI_API_KEY"]
HEADERS = {
    'X-AYLIEN-NewsAPI-Application-ID': config["NEWSAPI_APP_ID"], 
    'X-AYLIEN-NewsAPI-Application-Key': config["NEWSAPI_APP_KEY"],
}

app = Flask(__name__)
prompt_aql = {
    "Show me all the articles about Aylien, an AI company based in Ireland, that were written in the last 24 hours": 
    'entities:({{surface_forms.text:"aylien" AND overall_prominence:>=0.65 AND sort:"relevance"}})\n{"published_at.start": "NOW-100DAYS", "published_at.end": "NOW",}',
}


@app.route("/api/text2aql")
def text2aql():
    text = request.args.get("text")
    if not text:
        return jsonify({"error": "Parameter 'text' is required."}), 400
    
    aql = convert_text2aql_chatgpt(text)
    response = jsonify({"aql": aql})
    response.headers.add("Access-Control-Allow-Origin", "*")
    return response

def convert_text2aql_chatgpt(text):
    try:
       
        aql = openai.ChatCompletion.create(
            model="gpt-3.5-turbo-0613",
            messages=[
                {"role": "user", "content": prompt_aql.substitute({'prompt': text})},
            ]
        )
        if aql['choices'] and len(aql['choices']) > 0:
            return aql['choices'][0]['message']['content']
        return "No compute"
    except:
        return "OpenAI API error"


def detect_language(text):
    try:
        return detect(text)
    except:
        return 'en'  # Default to English


STORIES_ENDPOINT = 'https://api.aylien.com/news/stories'

@app.route("/api/fetchnews")
def fetchnews(text):
    aql = request.args.get("aql")
    
    if not aql:
        return jsonify({"error": "Parameter 'aql' is required."}), 400
    
    try:
        params = json.loads(request.args.get("params"))
    except:
        params = {}
        
    num_articles = request.args.get("num_articles", 10)
    lang = detect_language(text)
    if lang == 'zh':
        stories = retrieve_stories({"aql": aql, "language": "zh-cn", **params, **{"per_page": num_articles}})
    else:
        stories = retrieve_stories({"aql": aql, "language": "en", **params, **{"per_page": num_articles}})
    response = jsonify({"stories": stories})
    response.headers.add("Access-Control-Allow-Origin", "*")
    return response

def retrieve_stories(params,
                     n_pages=1,
                     headers=HEADERS,
                     endpoint=STORIES_ENDPOINT,
                     sleep=None):
    params = deepcopy(params)
    stories = []
    cursor = '*'
    for i in range(n_pages):
        params['cursor'] = cursor
        response = requests.get(
            endpoint,
            params,
            headers=headers
        )

        data = json.loads(response.text)
        if response.status_code != 200:
            return []
        
        stories += data['stories']
        if data.get('next_page_cursor', '*') != cursor:
            cursor = data['next_page_cursor']
            if sleep is not None:
                time.sleep(sleep)
        else:
            break
    return stories

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0')
