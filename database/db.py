import sqlite3
import os
import pandas as pd
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# Default DB Path is in the parent folder of database/ (the project root)
DEFAULT_DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "d2c_monitor.db")
DEFAULT_EXPORTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "exports")

def get_connection(db_path=DEFAULT_DB_PATH):
    return sqlite3.connect(db_path)

def init_db(db_path=DEFAULT_DB_PATH):
    """Create all tables if they don't exist."""
    logger.info(f"Initializing database at: {db_path}")
    conn = get_connection(db_path)
    cursor = conn.cursor()
    
    # Table 1: reviews
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS reviews (
        review_id TEXT PRIMARY KEY,
        brand_name TEXT,
        reviewer_name TEXT,
        rating INTEGER,
        review_title TEXT,
        review_text TEXT,
        review_date DATE,
        scrape_date DATE,
        verified_purchase BOOLEAN,
        helpful_votes INTEGER,
        week_number INTEGER,
        year_month TEXT,
        rating_category TEXT,
        short_review BOOLEAN,
        polarity REAL,
        subjectivity REAL,
        sentiment_label TEXT
    )
    """)
    
    # Table 2: keyword_trends
    # Unique constraint on brand_name, year_month, keyword to support replace
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS keyword_trends (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        brand_name TEXT,
        year_month TEXT,
        keyword TEXT,
        frequency INTEGER,
        pct_of_negative_reviews REAL,
        keyword_shift REAL,
        extracted_date DATE,
        UNIQUE(brand_name, year_month, keyword)
    )
    """)
    
    # Table 3: brand_monthly_summary
    # Unique constraint on brand_name, year_month to support upsert
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS brand_monthly_summary (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        brand_name TEXT,
        year_month TEXT,
        total_reviews INTEGER,
        avg_rating REAL,
        positive_pct REAL,
        negative_pct REAL,
        neutral_pct REAL,
        avg_polarity REAL,
        rating_trend REAL,
        review_velocity REAL,
        computed_date DATE,
        UNIQUE(brand_name, year_month)
    )
    """)
    
    conn.commit()
    conn.close()
    logger.info("Database tables initialized successfully.")

def insert_reviews(df, db_path=DEFAULT_DB_PATH):
    """Insert reviews, ignore duplicates on review_id."""
    if df.empty:
        logger.info("No reviews to insert.")
        return
        
    logger.info(f"Inserting {len(df)} reviews into database.")
    conn = get_connection(db_path)
    
    # Prepare dataframe (convert dates to string representations for SQLite)
    df_db = df.copy()
    if 'review_date' in df_db.columns:
        df_db['review_date'] = df_db['review_date'].dt.strftime('%Y-%m-%d')
    if 'scrape_date' in df_db.columns:
        # If it's a datetime object, convert to string
        if hasattr(df_db['scrape_date'], 'dt'):
            df_db['scrape_date'] = df_db['scrape_date'].dt.strftime('%Y-%m-%d')
            
    # Convert booleans to int for SQLite compatibility
    for col in ['verified_purchase', 'short_review']:
        if col in df_db.columns:
            df_db[col] = df_db[col].astype(int)
            
    # We want to perform "INSERT OR IGNORE"
    columns = [
        'review_id', 'brand_name', 'reviewer_name', 'rating', 'review_title', 
        'review_text', 'review_date', 'scrape_date', 'verified_purchase', 
        'helpful_votes', 'week_number', 'year_month', 'rating_category', 
        'short_review', 'polarity', 'subjectivity', 'sentiment_label'
    ]
    
    # Keep only relevant columns
    df_db = df_db[[c for c in columns if c in df_db.columns]]
    
    placeholders = ", ".join(["?"] * len(df_db.columns))
    col_names = ", ".join(df_db.columns)
    sql = f"INSERT OR IGNORE INTO reviews ({col_names}) VALUES ({placeholders})"
    
    cursor = conn.cursor()
    cursor.executemany(sql, df_db.values.tolist())
    conn.commit()
    conn.close()
    logger.info("Reviews inserted successfully.")

def insert_keywords(df, db_path=DEFAULT_DB_PATH):
    """Insert keyword trends, replace if same brand+month+keyword exists."""
    if df.empty:
        logger.info("No keywords to insert.")
        return
        
    logger.info(f"Inserting {len(df)} keyword trends into database.")
    conn = get_connection(db_path)
    
    df_db = df.copy()
    df_db['extracted_date'] = datetime.now().strftime('%Y-%m-%d')
    
    columns = [
        'brand_name', 'year_month', 'keyword', 'frequency', 
        'pct_of_negative_reviews', 'keyword_shift', 'extracted_date'
    ]
    
    df_db = df_db[columns]
    
    placeholders = ", ".join(["?"] * len(columns))
    col_names = ", ".join(columns)
    sql = f"INSERT OR REPLACE INTO keyword_trends ({col_names}) VALUES ({placeholders})"
    
    cursor = conn.cursor()
    cursor.executemany(sql, df_db.values.tolist())
    conn.commit()
    conn.close()
    logger.info("Keyword trends inserted successfully.")

def update_monthly_summary(db_path=DEFAULT_DB_PATH):
    """Recomputes and upserts brand_monthly_summary for all brand-month combinations in reviews."""
    logger.info("Recomputing brand monthly summaries...")
    conn = get_connection(db_path)
    
    # Load all reviews
    df_reviews = pd.read_sql_query("SELECT * FROM reviews", conn)
    if df_reviews.empty:
        logger.warning("No reviews found to compute monthly summaries.")
        conn.close()
        return
        
    df_reviews['review_date'] = pd.to_datetime(df_reviews['review_date'])
    
    # Get distinct brand and month
    brands = df_reviews['brand_name'].unique()
    
    summaries = []
    today_str = datetime.now().strftime('%Y-%m-%d')
    
    for brand in brands:
        brand_reviews = df_reviews[df_reviews['brand_name'] == brand]
        months = sorted(brand_reviews['year_month'].unique())
        
        # We need to compute metrics for each month
        # And keep track of previous month metrics for trend/velocity calculations
        prev_avg_rating = None
        prev_total_reviews = None
        
        for yyyy_mm in months:
            month_reviews = brand_reviews[brand_reviews['year_month'] == yyyy_mm]
            total_reviews = len(month_reviews)
            
            avg_rating = float(month_reviews['rating'].mean())
            avg_polarity = float(month_reviews['polarity'].mean())
            
            # Sentiment counts
            sent_counts = month_reviews['sentiment_label'].value_counts()
            pos_pct = float((sent_counts.get('Positive', 0) / total_reviews) * 100.0)
            neg_pct = float((sent_counts.get('Negative', 0) / total_reviews) * 100.0)
            neut_pct = float((sent_counts.get('Neutral', 0) / total_reviews) * 100.0)
            
            # Compute trends
            if prev_avg_rating is not None:
                rating_trend = avg_rating - prev_avg_rating
            else:
                rating_trend = 0.0
                
            if prev_total_reviews is not None and prev_total_reviews > 0:
                review_velocity = ((total_reviews - prev_total_reviews) / prev_total_reviews) * 100.0
            else:
                review_velocity = 0.0
                
            summaries.append({
                "brand_name": brand,
                "year_month": yyyy_mm,
                "total_reviews": total_reviews,
                "avg_rating": avg_rating,
                "positive_pct": pos_pct,
                "negative_pct": neg_pct,
                "neutral_pct": neut_pct,
                "avg_polarity": avg_polarity,
                "rating_trend": rating_trend,
                "review_velocity": review_velocity,
                "computed_date": today_str
            })
            
            # Set previous values for next iteration
            prev_avg_rating = avg_rating
            prev_total_reviews = total_reviews
            
    # Insert or replace in database
    if summaries:
        df_summary = pd.DataFrame(summaries)
        columns = [
            'brand_name', 'year_month', 'total_reviews', 'avg_rating', 
            'positive_pct', 'negative_pct', 'neutral_pct', 'avg_polarity', 
            'rating_trend', 'review_velocity', 'computed_date'
        ]
        df_summary = df_summary[columns]
        
        placeholders = ", ".join(["?"] * len(columns))
        col_names = ", ".join(columns)
        sql = f"INSERT OR REPLACE INTO brand_monthly_summary ({col_names}) VALUES ({placeholders})"
        
        cursor = conn.cursor()
        cursor.executemany(sql, df_summary.values.tolist())
        conn.commit()
        logger.info(f"Upserted {len(summaries)} rows into brand_monthly_summary.")
        
    conn.close()

def export_to_csv(db_path=DEFAULT_DB_PATH, exports_dir=DEFAULT_EXPORTS_DIR):
    """Export all three tables to separate CSV files in exports/ folder."""
    os.makedirs(exports_dir, exist_ok=True)
    logger.info(f"Exporting database tables to CSV in: {exports_dir}")
    
    conn = get_connection(db_path)
    
    tables = ['reviews', 'keyword_trends', 'brand_monthly_summary']
    for table in tables:
        df = pd.read_sql_query(f"SELECT * FROM {table}", conn)
        # Drop the autoincrement ID from summary and keyword_trends if we want clean csv exports,
        # but let's keep them or match the format. Let's keep them as is.
        csv_path = os.path.join(exports_dir, f"{table}.csv")
        df.to_csv(csv_path, index=False)
        logger.info(f"Exported {table} to {csv_path} ({len(df)} rows)")
        
    conn.close()
