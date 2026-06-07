# קובץ טעינת הנתונים

import os
import sqlite3

import pandas as pd


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_CSV_PATH = os.path.abspath(os.path.join(BASE_DIR, '..', 'data', 'opps.csv'))
DEFAULT_DB_PATH = os.path.abspath(os.path.join(BASE_DIR, '..', 'db', 'my_database.db'))


def load_csv_to_db(csv_path=DEFAULT_CSV_PATH, db_path=DEFAULT_DB_PATH):
    # CSV טעינת ה
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"CSV file not found: {csv_path}")

    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    df = pd.read_csv(csv_path)

    # חיבור לבסיס הנתונים
    with sqlite3.connect(db_path) as conn:
        # 'articles'  שמירת הנתונים בטבלה בשם
        df.to_sql('articles', conn, if_exists='replace', index=False)

    print(f"Data loaded successfully into {db_path}")


def database_has_articles_table(db_path=DEFAULT_DB_PATH):
    if not os.path.exists(db_path):
        return False

    with sqlite3.connect(db_path) as conn:
        row = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='articles'"
        ).fetchone()
        return row is not None


def ensure_database_ready(csv_path=DEFAULT_CSV_PATH, db_path=DEFAULT_DB_PATH):
    # טוען נתונים רק בריצה ראשונה או כשחסרה טבלת articles
    if not database_has_articles_table(db_path):
        load_csv_to_db(csv_path=csv_path, db_path=db_path)


# הרצה
if __name__ == "__main__":
    ensure_database_ready()

