import pandas as pd
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from collections import Counter
import logging

logger = logging.getLogger(__name__)

def extract_keywords_df(df):
    """
    Extract keywords from negative and neutral reviews only.
    Returns a DataFrame with one row per brand-month-keyword.
    """
    if df.empty:
        return pd.DataFrame(columns=['brand_name', 'year_month', 'keyword', 'frequency', 'pct_of_negative_reviews', 'keyword_shift'])

    # Ensure nltk resources are downloaded
    try:
        stop_words = set(stopwords.words('english'))
    except LookupError:
        nltk.download('stopwords', quiet=True)
        stop_words = set(stopwords.words('english'))
        
    try:
        # Check tokenization
        word_tokenize("test sentence")
    except LookupError:
        nltk.download('punkt', quiet=True)

    # Filter for negative and neutral reviews only
    neg_neut_df = df[df['sentiment_label'].isin(['Negative', 'Neutral'])].copy()
    
    # Custom stopwords
    custom_stopwords = {
        'product', 'skin', 'use', 'using', 'used', 'brand', 'one', 'get', 'got', 
        'really', 'just', 'very', 'also', 'would', 'could', 'still', 'even', 
        'cream', 'serum', 'face', 'hair'
    }
    all_stop_words = stop_words.union(custom_stopwords)

    records = []
    
    # Group by brand and month
    grouped = neg_neut_df.groupby(['brand_name', 'year_month'])
    
    for (brand, yyyy_mm), group in grouped:
        total_reviews = len(group)
        if total_reviews == 0:
            continue
            
        all_words = []
        review_word_sets = []
        
        for idx, row in group.iterrows():
            title = str(row.get('review_title', ''))
            text = str(row.get('review_text', ''))
            combined = f"{title} {text}".lower()
            
            # Tokenize words, filtering for alphabetic characters and length > 1
            try:
                tokens = [w for w in word_tokenize(combined) if w.isalpha() and len(w) > 1]
            except Exception:
                tokens = [w for w in combined.split() if w.isalpha() and len(w) > 1]
                
            filtered = [w for w in tokens if w not in all_stop_words]
            all_words.extend(filtered)
            review_word_sets.append(set(filtered))
            
        # Count frequencies
        word_counts = Counter(all_words)
        
        # Get top 30 keywords
        top_30 = word_counts.most_common(30)
        
        for keyword, freq in top_30:
            # Count how many reviews contain this keyword
            reviews_with_keyword = sum(1 for w_set in review_word_sets if keyword in w_set)
            pct = (reviews_with_keyword / total_reviews) * 100.0
            
            records.append({
                "brand_name": brand,
                "year_month": yyyy_mm,
                "keyword": keyword,
                "frequency": freq,
                "pct_of_negative_reviews": pct,
                "keyword_shift": 0.0 # Will compute in next step
            })
            
    keyword_df = pd.DataFrame(records)
    if keyword_df.empty:
        return keyword_df

    # Compute keyword_shift: Compare current month pct to previous month pct
    # Sort chronologically to make sure we process correctly
    keyword_df = keyword_df.sort_values(by=['brand_name', 'year_month'])
    
    # Map for easy lookup of previous month pct: (brand, previous_month, keyword) -> pct
    # To do this, let's group by brand, get unique months sorted
    brands = keyword_df['brand_name'].unique()
    for brand in brands:
        brand_mask = keyword_df['brand_name'] == brand
        brand_df = keyword_df[brand_mask]
        sorted_months = sorted(brand_df['year_month'].unique())
        
        # Create map of (month, keyword) -> pct
        pct_map = {}
        for idx, row in brand_df.iterrows():
            pct_map[(row['year_month'], row['keyword'])] = row['pct_of_negative_reviews']
            
        # Compute shift for each row of this brand
        for idx, row in brand_df.iterrows():
            curr_month = row['year_month']
            kw = row['keyword']
            curr_pct = row['pct_of_negative_reviews']
            
            curr_idx = sorted_months.index(curr_month)
            if curr_idx > 0:
                prev_month = sorted_months[curr_idx - 1]
                prev_pct = pct_map.get((prev_month, kw), 0.0)
                shift = curr_pct - prev_pct
            else:
                shift = 0.0
                
            keyword_df.at[idx, 'keyword_shift'] = shift
            
    return keyword_df
