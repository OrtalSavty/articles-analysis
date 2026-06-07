import re
from collections import Counter

# רשימה בסיסית של מילות קישור באנגלית (Stop Words)
STOP_WORDS = {
    "the", "and", "is", "in", "to", "of", "a", "for", "on", 
    "with", "as", "by", "it", "that", "this", "at", "from", 
    "an", "be", "are", "was", "or"
}

def clean_text(text):
    # (CSV למקרה שיש ערכים חסרים ב) וידאו שהטקסט הוא אכן מחרוזת 
    if not isinstance(text, str):
        return []

    #  נירמול: הפיכת הטקסט לאותיות קטנות
    text = text.lower()
    
    #  הסרת סימני פיסוק - משאירים רק אותיות, מספרים ורווחים
    text = re.sub(r'[^\w\s]', '', text)
    
    # פיצול למילים
    words = text.split()
    
    # Stop Words סינון- שמירת המילים שאינן ברשימת ה
    cleaned_words = [word for word in words if word not in STOP_WORDS]
    
    return cleaned_words


def get_top_keywords(text_list, top_n=20):
    all_words = []
    
    # מעבר על כל הטקסטים ברשימה
    for text in text_list:
        # ניקוי הטקסט בעזרת הפונקציה הקודמת
        cleaned_words = clean_text(text)
        # הוספת המילים הנקיות לרשימה הכללית
        all_words.extend(cleaned_words)
    
    # חישוב השכיחות של כל מילה
    word_counts = Counter(all_words)
    
    #   המילים הנפוצות ביותר יחד עם מספר הפעמים שהן הופיעו
    return word_counts.most_common(top_n)