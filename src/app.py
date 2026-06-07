import os
import sqlite3
import json
import re
from collections import Counter
from urllib.parse import urlparse

from flask import Flask, jsonify, render_template, request

from processor import get_top_keywords
from load_data import ensure_database_ready

app = Flask(__name__)

# הגדרת נתיב דינמי לקובץ בסיס הנתונים
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.abspath(os.path.join(BASE_DIR, '..', 'db', 'my_database.db'))

# אתחול בסיס הנתונים לטעינת CSV בריצה ראשונה
ensure_database_ready(db_path=DB_PATH)


def get_db_connection():
    """יצירת חיבור ל-SQLite"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def parse_to_standard_date(val):
    """פונקציית עזר לחילוץ ונרמול תאריכים מכל פורמט אפשרי"""
    if val is None:
        return None
    s = str(val).strip()
    
    # סינון ערכי זבל נפוצים
    if not s or s == '\\N' or 'N/A' in s.upper() or 'NAN' in s.upper() or s.startswith('0000'):
        return None
        
    # אפשרות 1: מבנה ISO סטנדרטי (YYYY-MM-DD או YYYY/MM/DD)
    m1 = re.search(r'(\d{4})[-/](\d{1,2})[-/](\d{1,2})', s)
    if m1:
        y, m, d = map(int, m1.groups())
        if 2000 <= y <= 2030 and 1 <= m <= 12 and 1 <= d <= 31:
            return f"{y}-{m:02d}-{d:02d}"
            
    # אפשרות 2: מבנה אירופאי/ישראלי (DD/MM/YYYY או DD-MM-YYYY)
    m2 = re.search(r'(\d{1,2})[-/](\d{1,2})[-/](\d{4})', s)
    if m2:
        d, m, y = map(int, m2.groups())
        if 2000 <= y <= 2030 and 1 <= m <= 12 and 1 <= d <= 31:
            return f"{y}-{m:02d}-{d:02d}"
            
    # אפשרות 3: תמיכה במבנה של מספר סידורי / Timestamp (אם קיים בקובץ)
    if s.isdigit() and 9 <= len(s) <= 11:
        try:
            import datetime
            dt = datetime.date.fromtimestamp(int(s))
            if 2000 <= dt.year <= 2030:
                return dt.isoformat()
        except Exception:
            pass
            
    return None


@app.route('/')
def dashboard():
    # התחברות לבסיס הנתונים ושליפת הנתונים הגולמיים
    conn = get_db_connection()
    all_rows = conn.execute('SELECT summary, location, keywords, link, creation_time, actionDate FROM articles').fetchall()
    conn.close()

    total_articles = len(all_rows)

    # 1. עיבוד תקצירים לענן מילים
    summaries = []
    garbage_keys = [
        "persons", "companies", "audience", "stage", "keywords", 
        "milestoneDate", "estimatedProjectEndLife", "location", 
        "USBudget", "threeLineSummary", "potentialpartners", "budget", 
        "companyDomain", "N/A", "null"
    ]

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

    # 2. חילוץ מקורות חכם מתוך עמודת ה-link
    sources_counter = Counter()
    for row in all_rows:
        link = row['link']
        if link and isinstance(link, str) and link.startswith('http'):
            try:
                domain = urlparse(link).netloc
                domain = domain.replace('www.', '')
                if domain:
                    sources_counter[domain] += 1
                    continue
            except Exception:
                pass
        sources_counter['מקור כללי'] += 1

    top_sources = sources_counter.most_common(5)
    sources_labels = [s[0] for s in top_sources]
    sources_values = [s[1] for s in top_sources]
    
    unique_sources = len([s for s in sources_counter if s != 'מקור כללי'])
    if unique_sources == 0 and len(sources_counter) > 0:
        unique_sources = len(sources_counter)

    # 3. חילוץ ונרמול תאריכים ומגמות בצורה מוגנת
    dates_counter = Counter()
    months_counter = Counter()
    
    for row in all_rows:
        # בדיקה של שני שדות התאריך האפשריים לכל שורה
        for date_field in [row['actionDate'], row['creation_time']]:
            clean_d = parse_to_standard_date(date_field)
            if clean_d:
                dates_counter[clean_d] += 1
                months_counter[clean_d[:7]] += 1
                break

    # מיון כרונולוגי מדויק של כל התאריכים התקינים שנמצאו במערכת
    all_sorted_dates = sorted(dates_counter.keys())
    date_min = all_sorted_dates[0] if all_sorted_dates else 'לא זמין'
    date_max = all_sorted_dates[-1] if all_sorted_dates else 'לא זמין'

    # הכנת נתונים עבור גרפי התאריכים והמגמות (מציג את 10 הימים/חודשים הראשונים)
    sorted_dates_for_chart = sorted(dates_counter.items())[:10]
    dates_labels = [d[0] for d in sorted_dates_for_chart]
    dates_values = [d[1] for d in sorted_dates_for_chart]

    sorted_months_for_chart = sorted(months_counter.items())[:10]
    trends_labels = [m[0] for m in sorted_months_for_chart]
    trends_values = [m[1] for m in sorted_months_for_chart]

    # 4. התפלגות לפי קטגוריה (keywords)
    cat_counter = Counter()
    for row in all_rows:
        kw = row['keywords']
        if kw and isinstance(kw, str) and kw != 'N/A' and kw.strip() != '':
            if kw.startswith('['):
                try:
                    kw_list = json.loads(kw)
                    for k in kw_list:
                        cat_counter[k] += 1
                    continue
                except Exception:
                    pass
            cat_counter[kw] += 1

    top_cats = cat_counter.most_common(5)
    cat_labels = [c[0] for c in top_cats]
    cat_values = [c[1] for c in top_cats]

    # 5. מאמרים לפי שפה / מיקום (location)
    lang_counter = Counter()
    for row in all_rows:
        loc = row['location']
        if loc and isinstance(loc, str) and loc != 'N/A' and loc.strip() != '':
            lang_counter[loc] += 1

    top_langs = lang_counter.most_common(5)
    lang_labels = [l[0] for l in top_langs]
    lang_values = [l[1] for l in top_langs]

    return render_template(
        'dashboard.html',
        top_words=top_words,
        dates_labels=dates_labels,
        dates_values=dates_values,
        sources_labels=sources_labels,
        sources_values=sources_values,
        cat_labels=cat_labels,
        cat_values=cat_values,
        lang_labels=lang_labels,
        lang_values=lang_values,
        trends_labels=trends_labels,
        trends_values=trends_values,
        total_articles=total_articles,
        unique_sources=unique_sources,
        date_min=date_min,
        date_max=date_max,
    )


@app.route('/ask', methods=['POST'])
def ask():
    data = request.get_json(silent=True) or {}
    question = (data.get('question') or '').strip()
    if not question:
        return jsonify({'error': 'לא סופקה שאלה'}), 400

    mindsdb_url = os.getenv('MINDSDB_URL', 'http://127.0.0.1:47334')
    agent_name = os.getenv('MINDSDB_AGENT_NAME', 'articles_agent')

    try:
        import mindsdb_sdk
        server = mindsdb_sdk.connect(mindsdb_url)
        safe_q = question.replace("'", "''")
        result = server.query(f"SELECT answer FROM {agent_name} WHERE question = '{safe_q}';").fetch()

        if result is not None and not result.empty:
            answer = result['answer'].iloc[0]
        else:
            answer = 'לא התקבלה תשובה מהסוכן.'
        return jsonify({'answer': str(answer)})
    except Exception as exc:
        return jsonify({'error': str(exc)}), 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)