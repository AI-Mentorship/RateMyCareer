#important note: This file will most likely get delete in the near future
#this is here now only for testing and progression purposes.

import os
import pandas as pd
import praw
from dotenv import load_dotenv
from transformers import pipeline

load_dotenv()

CONFIDENCE_CUTOFF = 0.4  
REGRET_KEYWORDS = [
    'regret', 'mistake', 'wish i had', 'should have', "shouldn't have",
    'wrong choice', 'bad decision', 'go back', 'if only', 'messed up'
]

user_agent = "Praw Test 1.0 by /u/Odd_Interaction5417"
reddit = praw.Reddit(
    client_id=os.getenv("PRAW_CLIENT_ID"),
    client_secret=os.getenv("PRAW_CLIENT_SECRET"),
    user_agent = user_agent
)

def analyze_text_with_chunking(text, pipeline):
    # If text is empty, return neutral
    if not text or text.isspace():
        return {'label': 0, 'confidence': 1.0}

    # Define chunking parameters
    max_chunk_length = 500  
    overlap = 50            # Overlap between chunks (very important)
    """
    Split the text into overlapping chunks (overlapping is important to prevent context loss)
    E.g: if we have the sentence "I like chicken. I like tacos. I also like matcha"
    and we split it into "I like chicken" and "I like tacos. I also like matcha" RoBERTa might loose context and 
    might give an inaccurate analysis. Instead we have "I like chicken. I like tacos" and "I like tacos. 
    I also like matcha". Sorry for the long explination.
    """
    #See project notes for how this line of code works
    chunks = [text[i:i + max_chunk_length] for i in range(0, len(text), max_chunk_length - overlap)]

    # Analyze
    results = pipeline(chunks)

    # Aggregate
    total_score = 0
    label_to_score = {'LABEL_0': -1, 'LABEL_1': 0, 'LABEL_2': 1}

    for result in results:
        score = result['score'] * label_to_score[result['label']]
        total_score += score

    average_score = total_score / len(results)

    # Determine the final sentiment
    final_label = 0
    if average_score > 0.1:
        final_label = 1
    elif average_score < -0.1:
        final_label = -1

    return {'label': final_label, 'confidence': abs(average_score)}


headlines = set()
for submission in reddit.subreddit('dataanalysis').new(limit=None):
    headlines.add(submission.title)

print("Loading RoBERTa model...")
# the "cardiffnlp/twitter-roberta-base-sentiment" model is best for sentiment analysis. I think. Probably.
sentiment_pipeline = pipeline("sentiment-analysis", model="cardiffnlp/twitter-roberta-base-sentiment")
print("Model loaded successfully.")

results = []

print("Fetching and analyzing Reddit submissions...")
for submission in reddit.subreddit('dataanalysis').new(limit=100): # Using a limit for testing
     #Post w/ no body are ignore (subject to change) 
    if not submission.selftext or submission.selftext.isspace():
        continue

    # Combine the title and the body (selftext) of the post
    combined_text = submission.title + " " + submission.selftext

    # Analyze the combined text
    sentiment_result = analyze_text_with_chunking(combined_text, sentiment_pipeline)

     #Post w/ low confidence are cut :(
    if sentiment_result['confidence'] < CONFIDENCE_CUTOFF:
        continue

    total_regret_count = 0
    text_to_search = combined_text.lower()
    for keyword in REGRET_KEYWORDS:
        total_regret_count += text_to_search.count(keyword)

    # Append the result 
    results.append({
        'headlines': submission.title,
        'label': sentiment_result['label'],
        'confidence': sentiment_result['confidence'],
        'regret_keyword_count': total_regret_count
    })

df = pd.DataFrame(results)

print(df.head())

#df.to_csv('DataAnalysis.csv', encoding='utf-8', index=False)