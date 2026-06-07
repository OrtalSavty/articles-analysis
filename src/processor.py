import re
from collections import Counter

# רשימת מילות קישור ומילות "זבל" מורחבת (Stop Words)
# רשימת מילות קישור ומילות "זבל" מורחבת (Stop Words)
STOP_WORDS = {
    # מילות קישור רגילות
    "the", "and", "is", "in", "to", "of", "a", "for", "on", 
    "with", "as", "by", "it", "that", "this", "at", "from", 
    "an", "be", "are", "was", "or", "will", "has", "have", "not",
    "can", "we", "you", "your", "our", "all", "which", "their", "its",
    
    # מילות זבל כלליות
    "na", "nan", "null", "none", "http", "https", "www", "com", "companyname",
    "more", "about", "read", "new", "how","name",
    
    # שאריות קוד (JSON) שזלגו מקובץ הנתונים שלנו
    "companies","2026","name" "companyname", "companiescompanyname", "persons", "2025", "2024","2030",
    "audience", "stage", "keywords", "location", "budget", "usbudget", "million", "announced", "interested", "",
    "threelinesummary", "potentialpartners", "milestonedate", 
    "estimatedprojectendlife", "companydomain", "contract", "awarded"
}
def clean_text(text):
    if not isinstance(text, str):
        return []

    # הפיכה לאותיות קטנות
    text = text.lower()
    
    # הסרת סימני פיסוק
    text = re.sub(r'[^\w\s]', '', text)
    
    words = text.split()
    
    # סינון מילים שקיימות ברשימה השחורה, וסינון אותיות בודדות/זוגות (כמו 'n', 'a')
    cleaned_words = [
        word for word in words 
        if word not in STOP_WORDS and len(word) > 2
    ]
    
    return cleaned_words

def get_top_keywords(text_list, top_n=20):
    all_words = []
    
    for text in text_list:
        cleaned_words = clean_text(text)
        all_words.extend(cleaned_words)
    
    word_counts = Counter(all_words)
    return word_counts.most_common(top_n)