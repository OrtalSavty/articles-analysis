# בסיס המערכת
FROM python:3.9-slim

# תיקיית עבודה במכולה
WORKDIR /app

# העתקת קובץ הדרישות והתקנתן
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# העתקת כל שאר הקבצים של הפרויקט לתוך המכולה
COPY . .

# הפעלת Flask ישירות
CMD ["python", "src/app.py"]