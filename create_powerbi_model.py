import os
import pandas as pd
from datetime import datetime

EXPORTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "exports")
REVIEWS_PATH = os.path.join(EXPORTS_DIR, "reviews.csv")
SUMMARY_PATH = os.path.join(EXPORTS_DIR, "brand_monthly_summary.csv")
KEYWORD_TRENDS_PATH = os.path.join(EXPORTS_DIR, "keyword_trends.csv")

# Brand Map (Consistent ID mapping)
BRAND_MAP = {
    "Mamaearth": 1,
    "Dot & Key": 2,
    "Plum": 3,
    "WOW Skin Science": 4
}

def create_dim_brand():
    print("Generating dim_brand.csv...")
    brands_data = [
        {"brand_id": 1, "brand_name": "Mamaearth", "category": "Skincare", "founded_year": 2016, "headquarters": "Gurugram", "brand_type": "D2C"},
        {"brand_id": 2, "brand_name": "Dot & Key", "category": "Skincare", "founded_year": 2018, "headquarters": "Bengaluru", "brand_type": "D2C"},
        {"brand_id": 3, "brand_name": "Plum", "category": "Skincare", "founded_year": 2013, "headquarters": "Mumbai", "brand_type": "D2C"},
        {"brand_id": 4, "brand_name": "WOW Skin Science", "category": "Skincare", "founded_year": 2014, "headquarters": "Bengaluru", "brand_type": "D2C"}
    ]
    df = pd.DataFrame(brands_data)
    out_path = os.path.join(EXPORTS_DIR, "dim_brand.csv")
    df.to_csv(out_path, index=False)
    print(f"Saved {len(df)} rows to {out_path}")

def create_dim_date():
    print("Generating dim_date.csv...")
    # Date dimension table covering 2024-01-01 to today
    today = datetime.now()
    date_range = pd.date_range(start="2024-01-01", end=today)
    
    df = pd.DataFrame({"date": date_range})
    df['year'] = df['date'].dt.year
    df['month'] = df['date'].dt.month
    df['month_name'] = df['date'].dt.strftime('%B')
    df['quarter'] = df['date'].dt.quarter
    df['week_number'] = df['date'].dt.isocalendar().week.astype(int)
    df['day_of_week'] = df['date'].dt.strftime('%A')
    df['is_weekend'] = df['date'].dt.dayofweek.isin([5, 6]).astype(int)
    
    # Format date as YYYY-MM-DD
    df['date'] = df['date'].dt.strftime('%Y-%m-%d')
    
    out_path = os.path.join(EXPORTS_DIR, "dim_date.csv")
    df.to_csv(out_path, index=False)
    print(f"Saved {len(df)} rows to {out_path}")

def create_fact_reviews():
    print("Generating fact_reviews.csv...")
    if not os.path.exists(REVIEWS_PATH):
        raise FileNotFoundError(f"Source file {REVIEWS_PATH} not found. Run the pipeline first.")
        
    df = pd.read_csv(REVIEWS_PATH)
    
    # Add brand_id mapping
    df['brand_id'] = df['brand_name'].map(BRAND_MAP)
    
    # Calculate review_length (character count of review_text)
    df['review_length'] = df['review_text'].fillna("").apply(len)
    
    # Keyword checks
    def has_kw(text, keywords):
        text_lower = str(text).lower() if pd.notnull(text) else ""
        return int(any(k in text_lower for k in keywords))
        
    df['has_keyword_packaging'] = df['review_text'].apply(lambda x: has_kw(x, ['packaging']))
    df['has_keyword_delivery'] = df['review_text'].apply(lambda x: has_kw(x, ['delivery']))
    df['has_keyword_fragrance'] = df['review_text'].apply(lambda x: has_kw(x, ['fragrance']))
    df['has_keyword_price'] = df['review_text'].apply(lambda x: has_kw(x, ['price', 'expensive', 'costly']))
    df['has_keyword_texture'] = df['review_text'].apply(lambda x: has_kw(x, ['texture', 'consistency']))
    
    out_path = os.path.join(EXPORTS_DIR, "fact_reviews.csv")
    df.to_csv(out_path, index=False)
    print(f"Saved {len(df)} rows to {out_path}")

def create_fact_monthly_summary():
    print("Generating fact_monthly_summary.csv...")
    if not os.path.exists(SUMMARY_PATH):
        raise FileNotFoundError(f"Source file {SUMMARY_PATH} not found. Run the pipeline first.")
        
    df = pd.read_csv(SUMMARY_PATH)
    
    # Add brand_id mapping
    df['brand_id'] = df['brand_name'].map(BRAND_MAP)
    
    # Add summary_period column formatted as "MMM YYYY" (e.g. "Jan 2024")
    # Year month is in YYYY-MM format, e.g. "2026-06"
    df['summary_period'] = pd.to_datetime(df['year_month'] + "-01").dt.strftime("%b %Y")
    
    out_path = os.path.join(EXPORTS_DIR, "fact_monthly_summary.csv")
    df.to_csv(out_path, index=False)
    print(f"Saved {len(df)} rows to {out_path}")

def create_keyword_alerts():
    print("Generating keyword_alerts.csv...")
    if not os.path.exists(KEYWORD_TRENDS_PATH):
        raise FileNotFoundError(f"Source file {KEYWORD_TRENDS_PATH} not found. Run the pipeline first.")
        
    df = pd.read_csv(KEYWORD_TRENDS_PATH)
    
    # Filter where keyword_shift > 5.0
    df_alerts = df[df['keyword_shift'] > 5.0].copy()
    
    # Add alert_severity:
    # shift > 20: "High"
    # shift > 10: "Medium"
    # shift > 5: "Low"
    def get_severity(shift):
        if shift > 20.0:
            return "High"
        elif shift > 10.0:
            return "Medium"
        else:
            return "Low"
            
    df_alerts['alert_severity'] = df_alerts['keyword_shift'].apply(get_severity)
    
    out_path = os.path.join(EXPORTS_DIR, "keyword_alerts.csv")
    df_alerts.to_csv(out_path, index=False)
    print(f"Saved {len(df_alerts)} rows to {out_path}")

def main():
    print("==================================================")
    print("       GENERATING POWER BI OPTIMIZED MODEL        ")
    print("==================================================")
    
    os.makedirs(EXPORTS_DIR, exist_ok=True)
    
    create_dim_brand()
    create_dim_date()
    create_fact_reviews()
    create_fact_monthly_summary()
    create_keyword_alerts()
    
    print("==================================================")
    print("              MODEL GENERATION COMPLETE           ")
    print("==================================================")

if __name__ == "__main__":
    main()
