from flask import Flask, jsonify, request
import openai
import json
import logging
from string import Template
import requests
import yaml
from copy import deepcopy
from langdetect import detect, lang_detect_exception
import time

with open("./config.yml", "r") as f:
    config = yaml.safe_load(f)

openai.api_key = config["OPENAI_API_KEY"]
HEADERS = {
    'X-AYLIEN-NewsAPI-Application-ID': config["NEWSAPI_APP_ID"], 
    'X-AYLIEN-NewsAPI-Application-Key': config["NEWSAPI_APP_KEY"],
}

app = Flask(__name__)
STORIES_ENDPOINT = 'https://api.aylien.com/news/stories'
history = []
openai_model = "gpt-3.5-turbo-0613"


@app.route("/api/text2aql")
def text2aql():
    text = request.args.get("text")
    if not text:
        return jsonify({"error": "Parameter 'text' is required."}), 400
    
    aql = convert_text2aql_chatgpt(text)
    response = jsonify({"aql": aql})
    response.headers.add("Access-Control-Allow-Origin", "*")
    return response

@app.route("/api/summarize", methods=['GET'])
def summarize():
    # Get the parameters from the request
    headlines = request.args.get('headlines')
    num_sentences = request.args.get('num_sentences')

    if not headlines:
        return jsonify({'error': 'Headlines are required for summarization.'}), 400
    if not num_sentences:
        num_sentences = 3
    else:
        try:
            num_sentences = int(num_sentences)
        except ValueError:
            return jsonify({'error': 'num_sentences parameter should be a number.'}), 400
    all_headlines = "\n".join(headlines.split(','))
    prompt = f"The following headlines were reported:\n{all_headlines}\n\nSummarize this information in {num_sentences} sentences:"

    try:
        # Make a request to the OpenAI API
        response = openai.Completion.create(
            engine=openai_model,
            prompt=prompt,
            temperature=0.5,
            max_tokens=150
        )

        # Get the model's response
        summary = response['choices'][0]['text'].strip()

        # Return the model's summary
        return jsonify({'summary': summary})

    except Exception as e:
        return jsonify({'error': f"An error occurred: {str(e)}"}), 500

@app.route("/api/fetchnews")
def fetchnews():
    aql = request.args.get("aql")
    text = request.args.get("text")
    
    if not aql:
        return jsonify({"error": "Parameter 'aql' is required."}), 400
    
    try:
        params = json.loads(request.args.get("params"))
    except:
        params = {}
        
    num_articles = request.args.get("num_articles", 10)
    
    try:
        lang = detect(text) if text else 'en'
    except lang_detect_exception.LangDetectException:
        lang = 'en'  # Default to English
    
    if lang == 'zh':
        stories = retrieve_stories({"aql": aql, "language": "zh-cn", **params, **{"per_page": num_articles}})
    else:
        stories = retrieve_stories({"aql": aql, "language": "en", **params, **{"per_page": num_articles}})
    response = jsonify({"stories": stories})
    response.headers.add("Access-Control-Allow-Origin", "*")
    return response

def convert_text2aql_chatgpt(text):
    settings_text = "You are a helpful assistant that answers natural language queries into Aylien Query Language (AQL)."
    append_history(settings_text, "system", len(history) == 0)
    append_history(text, "user")
    
    try:
        aql = openai.ChatCompletion.create(
            model=openai_model,
            messages=history
        )
        if aql['choices'] and len(aql['choices']) > 0:
            append_history(aql['choices'][0]['message']['content'], "assistant")
            return aql['choices'][0]['message']['content']
        return "No compute"
    except Exception as e:
        logging.error(f"OpenAI API error: {e}")
        return "OpenAI API error"

def append_history(text, role, condition=True):
    if condition and text:
        history.append({"role": role, "content": text})

def retrieve_stories(params, n_pages=1, headers=HEADERS, endpoint=STORIES_ENDPOINT, sleep=None):
    params = deepcopy(params)
    stories = []
    cursor = '*'
    for i in range(n_pages):
        params['cursor'] = cursor
        try:
            response = requests.get(
                endpoint,
                params,
                headers=headers
            )
            response.raise_for_status()  # Raises stored HTTPError, if one occurred.
            
            data = json.loads(response.text)
            stories += data['stories']
            if data.get('next_page_cursor', '*') != cursor:
                cursor = data['next_page_cursor']
                if sleep is not None:
                    time.sleep(sleep)
            else:
                break
        except requests.exceptions.HTTPError as err:
            logging.error(f"HTTP Error occurred: {err}")
            break
        except Exception as e:
            logging.error(f"An Error occurred: {e}")
            break
    return stories

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0')
