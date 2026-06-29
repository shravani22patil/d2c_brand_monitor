import os
import pandas as pd
import numpy as np

EXPORTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "exports")
REVIEWS_PATH = os.path.join(EXPORTS_DIR, "reviews.csv")
KEYWORD_TRENDS_PATH = os.path.join(EXPORTS_DIR, "keyword_trends.csv")
SUMMARY_PATH = os.path.join(EXPORTS_DIR, "brand_monthly_summary.csv")

def validate_reviews():
    print("--- Validating reviews.csv ---")
    if not os.path.exists(REVIEWS_PATH):
        print("FAIL: reviews.csv does not exist.")
        return False
        
    df = pd.read_csv(REVIEWS_PATH)
    total_rows = len(df)
    print(f"Total reviews loaded: {total_rows}")
    
    passed = True
    
    # 1. No null review_ids
    null_ids = df['review_id'].isnull().sum()
    if null_ids == 0:
        print(f"  [PASS] No null review_ids (0/{total_rows})")
    else:
        print(f"  [FAIL] Found {null_ids} null review_ids!")
        passed = False
        
    # 2. Rating always 1-5
    invalid_ratings = df[(df['rating'] < 1) | (df['rating'] > 5)]
    if len(invalid_ratings) == 0:
        print(f"  [PASS] Rating always between 1-5 (min={df['rating'].min()}, max={df['rating'].max()})")
    else:
        print(f"  [FAIL] Found {len(invalid_ratings)} ratings outside 1-5!")
        passed = False
        
    # 3. review_date is a valid date
    try:
        parsed_dates = pd.to_datetime(df['review_date'], errors='coerce')
        invalid_dates = parsed_dates.isnull().sum()
        if invalid_dates == 0:
            print(f"  [PASS] All review_dates are valid (min={df['review_date'].min()}, max={df['review_date'].max()})")
        else:
            print(f"  [FAIL] Found {invalid_dates} invalid or unparseable review_dates!")
            passed = False
    except Exception as e:
        print(f"  [FAIL] Error parsing review_date: {e}")
        passed = False
        
    # 4. sentiment_label is always one of Positive/Negative/Neutral
    valid_labels = {'Positive', 'Negative', 'Neutral'}
    actual_labels = set(df['sentiment_label'].unique())
    invalid_labels = actual_labels - valid_labels
    if not invalid_labels:
        print(f"  [PASS] sentiment_label values are valid (Labels found: {actual_labels})")
    else:
        print(f"  [FAIL] Found invalid sentiment_labels: {invalid_labels}!")
        passed = False
        
    # 5. All 4 brands present
    expected_brands = {"Mamaearth", "Dot & Key", "Plum", "WOW Skin Science"}
    actual_brands = set(df['brand_name'].unique())
    missing_brands = expected_brands - actual_brands
    if not missing_brands:
        print(f"  [PASS] All 4 target brands are present in reviews.csv: {actual_brands}")
    else:
        print(f"  [FAIL] Missing target brands: {missing_brands}!")
        passed = False
        
    return passed

def validate_keywords():
    print("\n--- Validating keyword_trends.csv ---")
    if not os.path.exists(KEYWORD_TRENDS_PATH):
        print("FAIL: keyword_trends.csv does not exist.")
        return False
        
    df = pd.read_csv(KEYWORD_TRENDS_PATH)
    total_rows = len(df)
    print(f"Total keyword trends loaded: {total_rows}")
    
    passed = True
    
    # 1. keyword_shift is never null
    null_shifts = df['keyword_shift'].isnull().sum()
    if null_shifts == 0:
        print(f"  [PASS] keyword_shift is never null (0/{total_rows})")
    else:
        print(f"  [FAIL] Found {null_shifts} null keyword_shift values!")
        passed = False
        
    # 2. pct_of_negative_reviews is between 0 and 100
    invalid_pcts = df[(df['pct_of_negative_reviews'] < 0.0) | (df['pct_of_negative_reviews'] > 100.0)]
    if len(invalid_pcts) == 0:
        print(f"  [PASS] pct_of_negative_reviews is between 0 and 100 (min={df['pct_of_negative_reviews'].min():.2f}%, max={df['pct_of_negative_reviews'].max():.2f}%)")
    else:
        print(f"  [FAIL] Found {len(invalid_pcts)} pct_of_negative_reviews values outside [0, 100]!")
        passed = False
        
    return passed

def validate_summaries():
    print("\n--- Validating brand_monthly_summary.csv ---")
    if not os.path.exists(SUMMARY_PATH):
        print("FAIL: brand_monthly_summary.csv does not exist.")
        return False
        
    df = pd.read_csv(SUMMARY_PATH)
    total_rows = len(df)
    print(f"Total summary rows loaded: {total_rows}")
    
    passed = True
    
    # 1. positive_pct + negative_pct + neutral_pct sums to approximately 100
    sums = df['positive_pct'] + df['negative_pct'] + df['neutral_pct']
    # Check if any sum is more than 0.1 away from 100.0
    violations = df[np.abs(sums - 100.0) > 0.1]
    if len(violations) == 0:
        print(f"  [PASS] Sentiment percentages sum to approximately 100% (min sum={sums.min():.4f}%, max sum={sums.max():.4f}%)")
    else:
        print(f"  [FAIL] Found {len(violations)} rows where sentiment percentages do not sum to 100%!")
        for idx, row in violations.iterrows():
            total = row['positive_pct'] + row['negative_pct'] + row['neutral_pct']
            print(f"    - Brand: {row['brand_name']}, Month: {row['year_month']}, Sum: {total:.4f}% (Pos: {row['positive_pct']:.2f}%, Neg: {row['negative_pct']:.2f}%, Neut: {row['neutral_pct']:.2f}%)")
        passed = False
        
    # 2. avg_rating is between 1 and 5
    invalid_ratings = df[(df['avg_rating'] < 1.0) | (df['avg_rating'] > 5.0)]
    if len(invalid_ratings) == 0:
        print(f"  [PASS] Average rating is between 1 and 5 (min={df['avg_rating'].min():.2f}, max={df['avg_rating'].max():.2f})")
    else:
        print(f"  [FAIL] Found {len(invalid_ratings)} average ratings outside [1, 5]!")
        passed = False
        
    return passed

def main():
    print("==================================================")
    print("             DATA VALIDATION REPORT               ")
    print("==================================================")
    
    rev_ok = validate_reviews()
    kw_ok = validate_keywords()
    sum_ok = validate_summaries()
    
    print("\n" + "="*50)
    if rev_ok and kw_ok and sum_ok:
        print("          STATUS: ALL CHECKS PASSED (PASS)")
    else:
        print("          STATUS: SOME CHECKS FAILED (FAIL)")
    print("="*50)

if __name__ == "__main__":
    main()
