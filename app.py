import requests
from bs4 import BeautifulSoup
import spacy
from flask import Flask, request, render_template

app = Flask(__name__)

def search_google(api_key, cse_id, query, num=10):
    params = {
        'key': api_key,
        'cx': cse_id,
        'q': query,
        'num': num
    }
    try:
        response = requests.get('https://www.googleapis.com/customsearch/v1', params=params)
        response.raise_for_status()
        search_results = response.json()
        return search_results
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        return None

def extract_urls(search_results):
    urls = []
    if search_results and 'items' in search_results:
        for item in search_results['items']:
            urls.append(item['link'])
    return urls

def fetch_content(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        paragraphs = soup.find_all('p')
        content = ' '.join([p.get_text() for p in paragraphs])
        return content
    except requests.exceptions.RequestException as e:
        print(f"An error occurred while fetching {url}: {e}")
        return ""

def analyze_content(content, person_name):
    nlp = spacy.load('en_core_web_sm')
    doc = nlp(content)
    themes = []
    mentions = []
    for sent in doc.sents:
        if person_name.lower() in sent.text.lower():
            mentions.append(sent.text)
            themes.extend([token.lemma_ for token in sent if token.pos_ in ('NOUN', 'VERB')])
    return mentions, themes

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        person_name = request.form['person_name']
        api_key = request.form['api_key']
        cse_id = request.form['cse_id']
        
        query = person_name
        results = search_google(api_key, cse_id, query)
        if results:
            urls = extract_urls(results)
            all_mentions = []
            all_themes = []
            for url in urls:
                content = fetch_content(url)
                mentions, themes = analyze_content(content, person_name)
                all_mentions.extend(mentions)
                all_themes.extend(themes)
            
            return render_template('results.html', person_name=person_name, mentions=all_mentions, themes=set(all_themes))
    
    return render_template('index.html')

if __name__ == "__main__":
    app.run(debug=True)
