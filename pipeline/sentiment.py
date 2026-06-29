from textblob import TextBlob
import pandas as pd

def analyze_sentiment(df):
    """
    Run sentiment analysis using TextBlob:
    - Combine title + " " + review_text as input
    - Compute polarity and subjectivity
    - Map polarity to sentiment_label
    - Add columns: polarity, subjectivity, sentiment_label
    - Return the DataFrame
    """
    if df.empty:
        return df
        
    polarities = []
    subjectivities = []
    labels = []
    
    for idx, row in df.iterrows():
        title = row.get('review_title', '')
        text = row.get('review_text', '')
        
        # Combine title and text
        combined = f"{title} {text}".strip()
        
        if not combined:
            pol = 0.0
            sub = 0.0
        else:
            blob = TextBlob(combined)
            pol = blob.sentiment.polarity
            sub = blob.sentiment.subjectivity
            
        # Map polarity to label
        if pol > 0.1:
            label = "Positive"
        elif pol < -0.1:
            label = "Negative"
        else:
            label = "Neutral"
            
        polarities.append(pol)
        subjectivities.append(sub)
        labels.append(label)
        
    df['polarity'] = polarities
    df['subjectivity'] = subjectivities
    df['sentiment_label'] = labels
    
    return df
