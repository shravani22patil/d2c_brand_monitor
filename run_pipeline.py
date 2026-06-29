import os
import logging
import pandas as pd
from scraper.trustpilot_scraper import scrape_trustpilot_reviews, generate_synthetic_reviews
from pipeline.cleaner import clean_reviews
from pipeline.sentiment import analyze_sentiment
from pipeline.keyword_extractor import extract_keywords_df
from database.db import init_db, insert_reviews, insert_keywords, update_monthly_summary, export_to_csv, DEFAULT_DB_PATH
import sqlite3

# Set up logging to console and file
log_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pipeline.log")
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.FileHandler(log_file, mode='a', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("run_pipeline")

BRANDS = [
    {"name": "Mamaearth", "domain": "mamaearth.in"},
    {"name": "Dot & Key", "domain": "dotandkey.com"},
    {"name": "Plum", "domain": "plumgoodness.com"},
    {"name": "WOW Skin Science", "domain": "buywow.in"}
]

def main():
    logger.info("==================================================")
    logger.info("Starting D2C Brand Monitor Data Pipeline")
    logger.info("==================================================")
    
    # Step 1: Initialize Database
    init_db()
    
    all_reviews = []
    scrape_counts = {}
    
    # Step 2: Scrape Reviews (with fallback)
    for brand in BRANDS:
        brand_name = brand["name"]
        brand_domain = brand["domain"]
        
        logger.info(f"Processing brand: {brand_name}")
        reviews = scrape_trustpilot_reviews(brand_name, brand_domain, max_pages=10)
        
        # Fallback to synthetic data if scraping is blocked (e.g. 403 or CAPTCHA or empty)
        if not reviews:
            logger.warning(f"Scraping failed or was blocked for {brand_name}. Falling back to synthetic data.")
            reviews = generate_synthetic_reviews(brand_name, brand_domain)
            
        scrape_counts[brand_name] = len(reviews)
        all_reviews.extend(reviews)
        
    logger.info(f"Total reviews collected across all brands: {len(all_reviews)}")
    
    if not all_reviews:
        logger.error("No reviews collected. Pipeline cannot proceed.")
        return
        
    # Step 3: Clean Data
    logger.info("Running Cleaner...")
    df_clean = clean_reviews(all_reviews)
    logger.info(f"Cleaned DataFrame size: {df_clean.shape}")
    
    # Step 4: Run Sentiment Analysis
    logger.info("Running Sentiment Analysis...")
    df_sentiment = analyze_sentiment(df_clean)
    logger.info("Sentiment analysis completed.")
    
    # Step 5: Extract Keywords
    logger.info("Running Keyword Extraction...")
    df_keywords = extract_keywords_df(df_sentiment)
    logger.info(f"Extracted {len(df_keywords)} keyword trend rows.")
    
    # Step 6: Database Insertion
    logger.info("Inserting reviews into Database...")
    insert_reviews(df_sentiment)
    
    logger.info("Inserting keyword trends into Database...")
    insert_keywords(df_keywords)
    
    # Step 7: Update Monthly Summary Table
    logger.info("Updating monthly brand summaries in Database...")
    update_monthly_summary()
    
    # Step 8: Export tables to CSV
    logger.info("Exporting database tables to CSV...")
    export_to_csv()
    
    logger.info("Pipeline executed successfully.")
    
    # Step 9: Print Summary Report
    print_summary_report(scrape_counts)

def print_summary_report(scrape_counts):
    """Print the final summary report to console."""
    conn = sqlite3.connect(DEFAULT_DB_PATH)
    
    print("\n" + "="*50)
    print("           D2C BRAND MONITOR PIPELINE SUMMARY       ")
    print("="*50)
    
    # 1. How many reviews scraped per brand (this run)
    print("\n1. REVIEWS SCRAPED THIS RUN:")
    for brand, count in scrape_counts.items():
        print(f"   - {brand}: {count} reviews")
        
    # 2. Current avg rating per brand (from all reviews in DB)
    print("\n2. OVERALL AVERAGE RATING PER BRAND (DATABASE):")
    df_avg = pd.read_sql_query("SELECT brand_name, AVG(rating) as avg_rating, COUNT(*) as total_count FROM reviews GROUP BY brand_name", conn)
    for idx, row in df_avg.iterrows():
        print(f"   - {row['brand_name']}: {row['avg_rating']:.2f} ({row['total_count']} total reviews in DB)")
        
    # 3. Top 3 rising keywords per brand (highest keyword_shift in the latest month available)
    print("\n3. TOP 3 RISING KEYWORDS PER BRAND (LATEST MONTH):")
    try:
        df_kw = pd.read_sql_query("SELECT * FROM keyword_trends", conn)
        if not df_kw.empty:
            for brand in scrape_counts.keys():
                brand_kw = df_kw[df_kw['brand_name'] == brand]
                if not brand_kw.empty:
                    latest_month = brand_kw['year_month'].max()
                    latest_brand_kw = brand_kw[brand_kw['year_month'] == latest_month]
                    # Sort by keyword_shift descending
                    top_rising = latest_brand_kw.sort_values(by='keyword_shift', ascending=False).head(3)
                    print(f"   * {brand} ({latest_month}):")
                    if not top_rising.empty:
                        for _, r in top_rising.iterrows():
                            print(f"     - '{r['keyword']}': shift = {r['keyword_shift']:+.2f}% (frequency = {r['frequency']})")
                    else:
                        print("     - No keyword data available.")
                else:
                    print(f"   * {brand}: No keyword data available.")
        else:
            print("   - No keyword data in database.")
    except Exception as e:
        print(f"   - Error retrieving rising keywords: {e}")
        
    # 4. Any brands whose rating dropped more than 0.2 points vs last month
    print("\n4. ALERTS: RATING DROPS (> 0.2 points vs last month):")
    try:
        df_summary = pd.read_sql_query("SELECT * FROM brand_monthly_summary", conn)
        if not df_summary.empty:
            alerts_found = False
            for brand in scrape_counts.keys():
                brand_summary = df_summary[df_summary['brand_name'] == brand]
                if not brand_summary.empty:
                    latest_month = brand_summary['year_month'].max()
                    latest_row = brand_summary[brand_summary['year_month'] == latest_month].iloc[0]
                    # Check rating_trend
                    trend = latest_row['rating_trend']
                    if trend < -0.2:
                        alerts_found = True
                        print(f"   [ALERT] {brand} rating dropped by {abs(trend):.2f} points in {latest_month} (New Avg: {latest_row['avg_rating']:.2f})")
            if not alerts_found:
                print("   - No brand experienced a rating drop > 0.2 points in the latest month.")
        else:
            print("   - No summary data available to check for drops.")
    except Exception as e:
        print(f"   - Error checking rating drops: {e}")
        
    print("="*50 + "\n")
    conn.close()

if __name__ == "__main__":
    main()
