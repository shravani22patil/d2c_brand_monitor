import os
import time
import random
import hashlib
import logging
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta

# Configure logging for imports
logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
}

def generate_hash_id(brand_name, reviewer_name, date_str):
    """Generate MD5 hash review_id from brand + reviewer + date."""
    key = f"{brand_name.strip()}|{reviewer_name.strip()}|{date_str.strip()}"
    return hashlib.md5(key.encode('utf-8')).hexdigest()

def generate_synthetic_reviews(brand_name, brand_domain, num_reviews=150):
    """Generate realistic synthetic reviews for the brand covering the last 6 months."""
    logger.info(f"Generating {num_reviews} synthetic reviews for brand {brand_name} ({brand_domain})")
    
    first_names = ["Amit", "Priya", "Rahul", "Anjali", "Siddharth", "Neha", "Rohan", "Sneha", "Karan", "Pooja", 
                   "Deepak", "Aishwarya", "Vikram", "Shalini", "Aditya", "Divya", "Sanjay", "Ritu", "Manish", "Kirti"]
    last_names = ["Sharma", "Verma", "Patel", "Gupta", "Mehta", "Singh", "Joshi", "Nair", "Rao", "Kumar", 
                  "Sen", "Das", "Reddy", "Choudhury", "Bose", "Misra", "Kapoor", "Malhotra", "Saxena", "Roy"]
    
    # Skincare keywords: 'packaging', 'moisturizer', 'fragrance', 'texture', 'breakout', 'delivery', 'ingredients', 'pump', 'consistency', 'price'
    positive_phrases = [
        "The moisturizer is incredibly lightweight and hydrating.",
        "Beautiful packaging and quick delivery! Highly recommend.",
        "The texture is so smooth and absorbs quickly into the skin.",
        "It has a very mild and pleasant fragrance.",
        "The pump dispenser is very convenient and prevents wastage.",
        "Great consistency, doesn't feel sticky at all.",
        "All the ingredients are natural and gentle on my face.",
        "Excellent price for the quality you get. Value for money.",
        "Absolutely love this serum, it did not cause any breakout.",
        "Highly impressed with the delivery speed and product packaging."
    ]
    
    neutral_phrases = [
        "The consistency is fine, but the pump mechanism is hard to press.",
        "Average moisturizer. The fragrance is a bit too strong for me.",
        "Packaging is okay, but the price seems slightly high for the size.",
        "The texture is nice, but it takes time to absorb into the skin.",
        "Decent ingredients list, though delivery took almost a week.",
        "No major breakout, but didn't see any miraculous change either.",
        "It's a good product but costly compared to competitors.",
        "The moisturizer works well, but the pump was slightly leaking.",
        "Simple packaging. The product is standard, nothing extraordinary.",
        "Texture is good but it has a strong chemical fragrance."
    ]
    
    negative_phrases = [
        "Disappointed with the packaging, it was damaged when delivered.",
        "This product gave me terrible breakouts within two days.",
        "The fragrance is way too overpowering and irritated my skin.",
        "Horrible delivery experience, took 10 days to arrive.",
        "The pump is completely broken and doesn't work at all.",
        "The consistency is too watery and feels sticky on the skin.",
        "Not worth the price. Extremely expensive for poor results.",
        "The moisturizer leaves a greasy residue and feels heavy.",
        "The ingredients list mentions harsh chemicals. Beware!",
        "Poor texture, didn't absorb and caused skin irritation."
    ]

    reviews = []
    today = datetime.now()
    
    for _ in range(num_reviews):
        # We need rating average between 3.8 and 4.3.
        # Let's assign probabilities: 5 -> 48%, 4 -> 25%, 3 -> 12%, 2 -> 9%, 1 -> 6%
        # Expected value: 5*0.48 + 4*0.25 + 3*0.12 + 2*0.09 + 1*0.06 = 2.4 + 1.0 + 0.36 + 0.18 + 0.06 = 4.0
        rating = random.choices([1, 2, 3, 4, 5], weights=[6, 9, 12, 25, 48])[0]
        
        reviewer = f"{random.choice(first_names)} {random.choice(last_names)}"
        
        # Generate random date in last 6 months (180 days)
        days_ago = random.randint(0, 180)
        review_date_obj = today - timedelta(days=days_ago)
        review_date = review_date_obj.strftime("%Y-%m-%d")
        
        # Construct review text based on rating
        if rating >= 4:
            review_title = random.choice([
                "Excellent product", "Really liked it", "Highly recommended!", "Amazing experience", 
                "Great moisturizer!", "Love the texture", "Good quality skincare", "Perfect packaging"
            ])
            text_body = " ".join(random.sample(positive_phrases, random.randint(1, 2)))
        elif rating == 3:
            review_title = random.choice([
                "Decent but average", "It is okay", "Mixed feelings", "Not bad, not great", 
                "Average quality", "Price is high", "Okay packaging"
            ])
            text_body = " ".join(random.sample(neutral_phrases, random.randint(1, 2)))
        else:
            review_title = random.choice([
                "Disappointed", "Bad experience", "Caused breakouts", "Poor quality", 
                "Worst purchase", "Not worth the money", "Broken pump / packaging"
            ])
            text_body = " ".join(random.sample(negative_phrases, random.randint(1, 2)))
        
        # Add random words sometimes to make length variable
        if len(text_body) < 20 and random.random() < 0.2:
            text_body = "Not good." if rating < 3 else "It is fine." if rating == 3 else "Loved it."
            
        verified = random.choice([True, False])
        helpful = random.choice([0, 0, 0, 1, 1, 2, 3, 5, 8])
        
        review_id = generate_hash_id(brand_name, reviewer, review_date)
        
        reviews.append({
            "review_id": review_id,
            "brand_name": brand_name,
            "reviewer_name": reviewer,
            "rating": rating,
            "review_title": review_title,
            "review_text": text_body,
            "review_date": review_date,
            "scrape_date": today.strftime("%Y-%m-%d"),
            "verified_purchase": verified,
            "helpful_votes": helpful
        })
        
    return reviews

def scrape_trustpilot_reviews(brand_name, brand_domain, max_pages=10):
    """Scrape reviews for a brand up to max_pages. If fails, returns None (caller handles fallback)."""
    logger.info(f"Starting scrape for {brand_name} ({brand_domain}) up to {max_pages} pages")
    reviews = []
    
    for page in range(1, max_pages + 1):
        url = f"https://www.trustpilot.com/review/www.{brand_domain}?page={page}"
        logger.info(f"Requesting {url}")
        
        try:
            # Random sleep between 2 to 5 seconds
            sleep_time = random.uniform(2, 5)
            time.sleep(sleep_time)
            
            response = requests.get(url, headers=HEADERS, timeout=15)
            
            if response.status_code == 403:
                logger.error(f"HTTP 403 Forbidden for {brand_name} page {page}. Scraping blocked.")
                return None
                
            if "captcha" in response.text.lower():
                logger.error(f"CAPTCHA detected for {brand_name} page {page}. Scraping blocked.")
                return None
                
            if response.status_code != 200:
                logger.error(f"HTTP status code {response.status_code} for {brand_name} page {page}.")
                # If page 1 fails, we fail. If page 2+ fails, maybe it's just out of bounds
                if page == 1:
                    return None
                else:
                    break
                    
            soup = BeautifulSoup(response.text, "html.parser")
            
            # Find review cards. In Trustpilot, these are typically '<article>' elements
            cards = soup.find_all("article")
            if not cards:
                # If page 1 has no cards, maybe structure changed or we got soft blocked
                logger.warning(f"No review cards found on page {page} for {brand_name}.")
                if page == 1:
                    return None
                else:
                    break
            
            today_str = datetime.now().strftime("%Y-%m-%d")
            
            for card in cards:
                try:
                    # 1. Reviewer Name
                    reviewer_elem = card.find(attrs={"data-consumer-name-typography": "true"})
                    if not reviewer_elem:
                        reviewer_elem = card.find(class_=lambda x: x and "consumerName" in x)
                    reviewer_name = reviewer_elem.text.strip() if reviewer_elem else "Anonymous"
                    
                    # 2. Rating
                    rating = 5  # default
                    # Trustpilot star rating image is often inside a div with class containing star-rating
                    rating_elem = card.find(class_=lambda x: x and "star-rating" in x)
                    if rating_elem:
                        img = rating_elem.find("img")
                        if img and img.get("alt"):
                            alt_text = img.get("alt") # "Rated 4 out of 5 stars"
                            rating = int(alt_text.split("out of")[0].replace("Rated", "").strip())
                    
                    # 3. Review Title
                    title_elem = card.find(attrs={"data-review-title-typography": "true"})
                    if not title_elem:
                        title_elem = card.find("h2")
                    review_title = title_elem.text.strip() if title_elem else ""
                    
                    # 4. Review Text
                    text_elem = card.find(attrs={"data-review-text-typography": "true"})
                    review_text = text_elem.text.strip() if text_elem else ""
                    
                    # 5. Review Date
                    date_str = today_str
                    time_elem = card.find("time")
                    if time_elem and time_elem.get("datetime"):
                        # Format is usually: "2024-05-12T14:30:00.000Z"
                        dt_val = time_elem.get("datetime")
                        try:
                            date_str = dt_val.split("T")[0]
                        except Exception:
                            pass
                    
                    # 6. Verified Purchase
                    verified = False
                    verified_elem = card.find(class_=lambda x: x and "verified" in x)
                    if verified_elem or card.find(text="Verified"):
                        verified = True
                    # Check in SVG or span tags
                    if not verified:
                        for span in card.find_all("span"):
                            if "verified" in span.text.lower():
                                verified = True
                                break
                    
                    # 7. Helpful Votes
                    helpful_votes = 0
                    helpful_elem = card.find(attrs={"data-helpful-count-typography": "true"})
                    if helpful_elem:
                        try:
                            helpful_votes = int(helpful_elem.text.strip())
                        except ValueError:
                            pass
                    if not helpful_elem:
                        # try looking for buttons or tags containing "helpful"
                        for btn in card.find_all(lambda tag: tag.name in ["button", "span"] and "helpful" in tag.text.lower()):
                            # Parse any digit
                            digits = [int(s) for s in btn.text.split() if s.isdigit()]
                            if digits:
                                helpful_votes = digits[0]
                                break
                    
                    review_id = generate_hash_id(brand_name, reviewer_name, date_str)
                    
                    reviews.append({
                        "review_id": review_id,
                        "brand_name": brand_name,
                        "reviewer_name": reviewer_name,
                        "rating": rating,
                        "review_title": review_title,
                        "review_text": review_text,
                        "review_date": date_str,
                        "scrape_date": today_str,
                        "verified_purchase": verified,
                        "helpful_votes": helpful_votes
                    })
                except Exception as e:
                    logger.error(f"Error parsing review card for {brand_name}: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Network error or exception during scraping {brand_name} page {page}: {e}")
            if page == 1:
                return None
            else:
                break
                
    return reviews
