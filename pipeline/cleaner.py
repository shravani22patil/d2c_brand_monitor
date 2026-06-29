import pandas as pd

def clean_reviews(reviews_list):
    """
    Clean the scraped reviews:
    - Remove duplicate review_ids
    - Strip whitespace from all text fields
    - Convert review_date strings to datetime objects
    - Add a week_number column (ISO week number from review_date)
    - Add a year_month column (YYYY-MM format)
    - Add a rating_category column (Excellent, Good, Neutral, Poor, Critical)
    - Flag reviews under 20 characters as short_review = True
    - Return a cleaned pandas DataFrame
    """
    if not reviews_list:
        return pd.DataFrame()
        
    df = pd.DataFrame(reviews_list)
    
    # 1. Remove duplicate review_ids
    df = df.drop_duplicates(subset=['review_id'])
    
    # 2. Strip whitespace from all text/string fields
    # Ensure they are strings first to avoid issues
    string_cols = ['brand_name', 'reviewer_name', 'review_title', 'review_text']
    for col in string_cols:
        if col in df.columns:
            df[col] = df[col].fillna("").astype(str).str.strip()
            
    # 3. Convert review_date strings to datetime objects
    df['review_date'] = pd.to_datetime(df['review_date'])
    
    # 4. Add a week_number column (ISO week number from review_date)
    df['week_number'] = df['review_date'].dt.isocalendar().week.astype(int)
    
    # 5. Add a year_month column (YYYY-MM format)
    df['year_month'] = df['review_date'].dt.strftime('%Y-%m')
    
    # 6. Add a rating_category column
    rating_map = {
        5: "Excellent",
        4: "Good",
        3: "Neutral",
        2: "Poor",
        1: "Critical"
    }
    df['rating_category'] = df['rating'].map(rating_map).fillna("Neutral")
    
    # 7. Flag reviews under 20 characters as short_review = True
    df['short_review'] = df['review_text'].apply(lambda x: len(x) < 20)
    
    return df
