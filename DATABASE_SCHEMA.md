# Database Schema

הטבלה המרכזית במסד הנתונים `my_database.db` היא **articles**.

## מבנה טבלת `articles`

| שם עמודה | טיפוס | תיאור |
| :--- | :--- | :--- |
| `id` | INTEGER | מפתח ראשי (Primary Key) |
| `summary` | TEXT | תקציר המאמר |
| `location` | TEXT | מיקום גיאוגרפי או שפה |
| `keywords` | TEXT | מילות מפתח (בפורמט JSON) |
| `link` | TEXT | קישור למקור המאמר |
| `creation_time` | TEXT | תאריך יצירה |
| `actionDate` | TEXT | תאריך איסוף |

המערכת טוענת את הנתונים מקובץ `opps.csv` בעזרת `load_data.py` בכל עלייה של הקונטיינר.