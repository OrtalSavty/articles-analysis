import os
import sqlite3
import json
import re
from datetime import datetime
from collections import Counter
from urllib.parse import urlparse

from flask import Flask, jsonify, render_template, request

from processor import get_top_keywords
from load_data import ensure_database_ready

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.abspath(os.path.join(BASE_DIR, '..', 'db', 'my_database.db'))
TODAY = datetime.now().strftime('%Y-%m-%d')

ensure_database_ready(db_path=DB_PATH)

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def parse_to_standard_date(val):
    if val is None: return None
    s = str(val).strip()
    if not s or s == '\\N' or 'N/A' in s.upper() or 'NAN' in s.upper() or s.startswith('0000'):
        return None
    m1 = re.search(r'(\d{4})[-/](\d{1,2})[-/](\d{1,2})', s)
    if m1:
        y, m, d = map(int, m1.groups())
        if 2000 <= y <= 2030 and 1 <= m <= 12 and 1 <= d <= 31:
            return f"{y}-{m:02d}-{d:02d}"
    return None

@app.route('/')
def dashboard():
    conn = get_db_connection()
    all_rows = conn.execute('SELECT summary, location, keywords, link, creation_time, actionDate FROM articles').fetchall()
    conn.close()

    total_articles = len(all_rows)
    
    summaries = []
    garbage_keys = ["persons", "companies", "audience", "stage", "keywords", "milestoneDate", "estimatedProjectEndLife", "location", "USBudget", "threeLineSummary", "potentialpartners", "budget", "companyDomain", "N/A", "null"]
    for row in all_rows:
        raw_summary = row['summary']
        if raw_summary and isinstance(raw_summary, str):
            clean_text = raw_summary
            if clean_text.strip().startswith('{'):
                for key in garbage_keys:
                    clean_text = re.sub(r'"?' + key + r'"?\s*:?', ' ', clean_text, flags=re.IGNORECASE)
                clean_text = re.sub(r'\[|\]|\{|\}', ' ', clean_text)
            summaries.append(clean_text)
    top_words = get_top_keywords(summaries, top_n=25)

    days_counter = Counter()
    months_counter = Counter()
    sources_counter = Counter()
    cat_counter = Counter()
    lang_counter = Counter()
    all_dates = []

    for row in all_rows:
        for d_field in [row['actionDate'], row['creation_time']]:
            clean_d = parse_to_standard_date(d_field)
            if clean_d and clean_d <= TODAY:
                all_dates.append(clean_d)
                days_counter[datetime.strptime(clean_d, '%Y-%m-%d').strftime('%A')] += 1
                months_counter[clean_d[:7]] += 1
                break
        
        link = row['link']
        if link and isinstance(link, str) and link.startswith('http'):
            try: sources_counter[urlparse(link).netloc.replace('www.', '')] += 1
            except: sources_counter['מקור כללי'] += 1
        else: sources_counter['מקור כללי'] += 1
        
        kw = row['keywords']
        if kw and isinstance(kw, str) and kw != 'N/A' and kw.strip() != '':
            if kw.startswith('['):
                try:
                    for k in json.loads(kw): cat_counter[k] += 1
                except: pass
            else: cat_counter[kw] += 1
            
        loc = row['location']
        if loc and isinstance(loc, str) and loc != 'N/A' and loc.strip() != '':
            lang_counter[loc] += 1

    day_order = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
    all_dates.sort()

    # כאן התיקון - מיון כרונולוגי של כל החודשים ללא חיתוך
    sorted_months = sorted(months_counter.items())

    return render_template(
        'dashboard.html',
        top_words=top_words,
        total_articles=int(total_articles),
        dates_labels=day_order,
        dates_values=[int(days_counter.get(day, 0)) for day in day_order],
        trends_labels=[m[0] for m in sorted_months],
        trends_values=[int(m[1]) for m in sorted_months],
        sources_labels=[s[0] for s in sources_counter.most_common(5)],
        sources_values=[s[1] for s in sources_counter.most_common(5)],
        cat_labels=[c[0] for c in cat_counter.most_common(5)],
        cat_values=[c[1] for c in cat_counter.most_common(5)],
        lang_labels=[l[0] for l in lang_counter.most_common(5)],
        lang_values=[l[1] for l in lang_counter.most_common(5)],
        unique_sources=len([s for s in sources_counter if s != 'מקור כללי']),
        date_min=all_dates[0] if all_dates else 'לא זמין',
        date_max=all_dates[-1] if all_dates else 'לא זמין'
    )

@app.route('/ask', methods=['POST'])
def ask():
    data = request.get_json(silent=True) or {}
    question = (data.get('question') or '').strip()
    if not question: return jsonify({'error': 'לא סופקה שאלה'}), 400
    try:
        import mindsdb_sdk
        server = mindsdb_sdk.connect(os.getenv('MINDSDB_URL', 'http://127.0.0.1:47334'))
        safe_q = question.replace("'", "''")
        result = server.query(f"SELECT answer FROM {os.getenv('MINDSDB_AGENT_NAME', 'articles_agent')} WHERE question = '{safe_q}';").fetch()
        return jsonify({'answer': str(result['answer'].iloc[0]) if result is not None and not result.empty else 'לא התקבלה תשובה'})
    except Exception as exc: return jsonify({'error': str(exc)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)