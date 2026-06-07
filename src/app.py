import os
import sqlite3

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
    # מאפשר גישה לעמודות לפי שם
    conn.row_factory = sqlite3.Row
    return conn


@app.route('/')
def dashboard():
    # התחברות לבסיס הנתונים
    conn = get_db_connection()

    # שליפת תקצירים עבור ענן תגיות
    articles_for_cloud = conn.execute('SELECT summary FROM articles WHERE summary IS NOT NULL').fetchall()
    summaries = [row['summary'] for row in articles_for_cloud]

    # חישוב מילות מפתח שכיחות
    top_words = get_top_keywords(summaries, top_n=25)

    # ספירת מאמרים לפי מקור
    source_query = '''
        SELECT source, COUNT(*) as count 
        FROM articles 
        WHERE source IS NOT NULL AND source != '\\N'
        GROUP BY source 
        ORDER BY count DESC 
        LIMIT 5
    '''
    source_rows = conn.execute(source_query).fetchall()

    # ספירת מאמרים לפי יום
    date_query = '''
        SELECT actionDate, COUNT(*) as count 
        FROM articles 
        WHERE actionDate IS NOT NULL AND actionDate != 'N/A' AND actionDate != '\\N'
        GROUP BY actionDate 
        ORDER BY actionDate ASC 
        LIMIT 10
    '''
    date_rows = conn.execute(date_query).fetchall()

    # עיבוד הנתונים לרשימות
    sources_labels = [row['source'] for row in source_rows]
    sources_values = [row['count'] for row in source_rows]

    dates_labels = [row['actionDate'] for row in date_rows]
    dates_values = [row['count'] for row in date_rows]

    cat_query = '''
        SELECT keywords as category, COUNT(*) as count 
        FROM articles 
        WHERE keywords IS NOT NULL AND keywords != 'N/A' 
        GROUP BY keywords 
        ORDER BY count DESC 
        LIMIT 5
    '''
    cat_rows = conn.execute(cat_query).fetchall()
    cat_labels = [row['category'] for row in cat_rows]
    cat_values = [row['count'] for row in cat_rows]

    lang_query = '''
        SELECT location as language, COUNT(*) as count 
        FROM articles 
        WHERE location IS NOT NULL AND location != 'N/A' 
        GROUP BY location 
        ORDER BY count DESC 
        LIMIT 5
    '''
    lang_rows = conn.execute(lang_query).fetchall()
    lang_labels = [row['language'] for row in lang_rows]
    lang_values = [row['count'] for row in lang_rows]

    trends_query = '''
        SELECT substr(actionDate, 1, 7) as month, COUNT(*) as count 
        FROM articles 
        WHERE actionDate IS NOT NULL AND actionDate != 'N/A' AND actionDate != '\\N'
        GROUP BY month 
        ORDER BY month ASC 
        LIMIT 10
    '''
    trends_rows = conn.execute(trends_query).fetchall()
    trends_labels = [row['month'] for row in trends_rows]
    trends_values = [row['count'] for row in trends_rows]

    # נתוני סיכום לסרגל הסטטיסטיקות
    total_articles = conn.execute('SELECT COUNT(*) as n FROM articles').fetchone()['n']
    unique_sources = conn.execute(
        "SELECT COUNT(DISTINCT source) as n FROM articles WHERE source IS NOT NULL AND source != '\\N'"
    ).fetchone()['n']
    date_range = conn.execute(
        "SELECT MIN(actionDate) as dmin, MAX(actionDate) as dmax FROM articles "
        "WHERE actionDate IS NOT NULL AND actionDate != 'N/A' AND actionDate != '\\N'"
    ).fetchone()
    date_min = date_range['dmin'] or ''
    date_max = date_range['dmax'] or ''

    # סגירת החיבור
    conn.close()

    # שליחת הנתונים לתבנית
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
    # העברת שאלת המשתמש ל-Agent של MindsDB
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

        # יצירת Agent חדשה נשענת על data=files.opps, לכן שולחים רק question
        result = server.query(f"""
            SELECT answer FROM {agent_name}
            WHERE question = '{safe_q}';
        """).fetch()

        if result is not None and not result.empty:
            answer = result['answer'].iloc[0]
        else:
            answer = 'לא התקבלה תשובה מהסוכן.'

        return jsonify({'answer': str(answer)})

    except Exception as exc:
        return jsonify({'error': str(exc)}), 500


if __name__ == '__main__':
    # הרצת השרת
    app.run(debug=True, host='0.0.0.0', port=5000)