import os
import re
import csv
import praw
import time
import logging
import argparse
import prawcore
import torch
import torch.nn.functional as F
from dotenv import load_dotenv
from supabase import create_client, Client
from datetime import datetime, timezone
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline

# --- 1. SETUP AND CONFIGURATION ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
load_dotenv()

# --- Helper Functions ---
def load_copypastas_from_file(filepath: str):
    if not os.path.exists(filepath):
        logging.warning(f"Copypasta file '{filepath}' not found.")
        return []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return [line.strip() for line in f if line.strip()]
    except Exception as e:
        logging.error(f"Error loading copypasta file: {e}")
        return []

def load_hf_model(model_path, tokenizer_name="roberta-base"):
    if not os.path.exists(model_path):
        logging.error(f"Model directory '{model_path}' not found.")
        return None, None, None
    try:
        tokenizer = AutoTokenizer.from_pretrained(tokenizer_name)
        model = AutoModelForSequenceClassification.from_pretrained(model_path)
        device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
        model.to(device)
        logging.info(f"✅ Model '{model_path}' loaded onto device: {device}")
        return model, tokenizer, device
    except Exception as e:
        logging.error(f"Could not load model '{model_path}': {e}")
        return None, None, None

# --- CONSTANTS AND MODEL SETUP ---
script_dir = os.path.dirname(os.path.abspath(__file__))
COPASTAS_FILE = os.path.join(script_dir, 'copypastas_combined.txt')
FILTERED_JOB_POSTS_FILE = os.path.join(script_dir, 'filtered_job_posts.csv')
SENTIMENT_DATA_FILE = os.path.join(script_dir, 'job_sentiment_data.csv')
NON_JOB_POSTS_FILE = os.path.join(script_dir, 'non_job_posts.csv')
SARCASM_MODEL_PATH = "sarcasm-model"

KNOWN_COPYPASTAS = load_copypastas_from_file(COPASTAS_FILE)
sarcasm_model, sarcasm_tokenizer, ml_device = load_hf_model(SARCASM_MODEL_PATH)

try:
    logging.info("Loading zero-shot classification model...")
    classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli", device=0 if torch.cuda.is_available() else -1)
    logging.info("✅ Zero-shot classification model loaded.")
except Exception as e:
    logging.error(f"Could not load zero-shot model: {e}")
    classifier = None

CANDIDATE_LABELS = [
    'job experience and career advice', 'self-promotion or portfolio sharing', 
    'technical question or software help', 'spam or advertisement', 'general discussion'
]
SPAM_KEYWORDS_GENERAL = [
    "crypto", "giveaway", "free money", "cash prize", "investment", "forex", "dropshipping", "onlyfans", 
    "subscribe", "my new app", "check out my site", "join my discord", "i built a tool", "my youtube channel"
]
SPAM_DOMAINS = ["bit.ly", "tinyurl.com", "linktr.ee", "t.co"]
SCORING_WEIGHTS = {
    "SPAM_DOMAIN": 11, "CONTAINS_LINK": 5, "SPAM_KEYWORD": 11, "COPYPASTA": 15,
    "SHORT_TEXT": 4, "EXCESSIVE_PUNCTUATION": 2, "ML_SARCASM_MAX": 8
}
FLAG_THRESHOLD = 10

if KNOWN_COPYPASTAS:
    vectorizer = TfidfVectorizer().fit(KNOWN_COPYPASTAS)
    vectors_copastas = vectorizer.transform(KNOWN_COPYPASTAS)
else:
    vectorizer, vectors_copastas = None, None

# --- 2. ANALYSIS LOGIC ---
def classify_submission_with_model(text: str) -> str:
    if not classifier: return "GENERAL_CONTENT"
    result = classifier(text[:1024], CANDIDATE_LABELS, multi_label=False)
    top_label = result['labels'][0]
    label_map = {
        'job experience and career advice': "JOB_EXPERIENCE",
        'self-promotion or portfolio sharing': "SELF_PROMOTION",
        'technical question or software help': "TECHNICAL_QUESTION",
        'spam or advertisement': "SPAM"
    }
    return label_map.get(top_label, "GENERAL_CONTENT")

def predict_with_hf_model(model, tokenizer, text):
    if not model or not tokenizer: return "N/A", 0.0
    try:
        inputs = tokenizer(text, padding=True, truncation=True, max_length=256, return_tensors="pt").to(ml_device)
        model.eval()
        with torch.no_grad():
            outputs = model(**inputs)
            probs = F.softmax(outputs.logits, dim=-1)
            confidence, preds = torch.max(probs, dim=1)
            label = model.config.id2label[preds.item()]
            return label, confidence.item()
    except Exception as e:
        logging.error(f"Prediction failed: {e}")
        return "ERROR", 0.0

def get_content_score(submission: praw.models.Submission) -> dict:
    submission_text = f"{submission.title} {submission.selftext}"
    text_lower = submission_text.lower()
    scores = {"l1_keyword_score": 0, "l2_structure_score": 0, "ml_sarcasm_score": 0}
    
    if any(domain in text_lower for domain in SPAM_DOMAINS): scores["l1_keyword_score"] += SCORING_WEIGHTS["SPAM_DOMAIN"]
    if re.search(r'https?://\S+', text_lower): scores["l1_keyword_score"] += SCORING_WEIGHTS["CONTAINS_LINK"]
    if any(keyword in text_lower for keyword in SPAM_KEYWORDS_GENERAL): scores["l1_keyword_score"] += SCORING_WEIGHTS["SPAM_KEYWORD"]
    if KNOWN_COPYPASTAS and vectorizer is not None:
        try:
            sim = cosine_similarity(vectorizer.transform([text_lower]), vectors_copastas).flatten()
            if len(sim) > 0 and max(sim) > 0.95: scores["l1_keyword_score"] += SCORING_WEIGHTS["COPYPASTA"]
        except Exception as e:
            logging.warning(f"TF-IDF similarity check failed: {e}")

    if len(submission.selftext.split()) < 10: scores["l2_structure_score"] += SCORING_WEIGHTS["SHORT_TEXT"]
    if text_lower.count('!') > 3 or text_lower.count('?') > 3 or submission.title.isupper(): scores["l2_structure_score"] += SCORING_WEIGHTS["EXCESSIVE_PUNCTUATION"]
    
    sarcasm_pred, sarcasm_conf = predict_with_hf_model(sarcasm_model, sarcasm_tokenizer, submission_text)
    if sarcasm_pred == "SARCASTIC":
        scores["ml_sarcasm_score"] += int(SCORING_WEIGHTS["ML_SARCASM_MAX"] * sarcasm_conf)

    scores["total_score"] = sum(scores.values())
    return scores

# --- 3. MAIN SCRAPING AND PROCESSING LOGIC ---
def process_subreddit(reddit: praw.Reddit, supabase: Client, subreddit_name: str, limit: int, output_mode: str):
    try:
        logging.info(f"--- Processing subreddit: r/{subreddit_name} ---")
        subreddit = reddit.subreddit(subreddit_name)
        sentiment_submissions_to_save, filtered_submissions_data, non_job_submissions_to_save = [], [], []

        logging.info(f"Fetching {limit} 'hot' submissions...")
        for submission in subreddit.hot(limit=limit):
            try:
                if submission.stickied or submission.author is None:
                    continue
                
                submission_text = f"Title: {submission.title}\n\n{submission.selftext}"
                category = classify_submission_with_model(submission_text)

                if category == "JOB_EXPERIENCE":
                    scores_dict = get_content_score(submission)
                    logging.info(f"Processing [JOB_EXPERIENCE] '{submission.title[:40]}...': Score=[{scores_dict['total_score']}]")

                    if scores_dict['total_score'] > FLAG_THRESHOLD:
                        logging.info("-> High score. Routing to FILTERED.")
                        filtered_row = {"submission_id": submission.id, "title": submission.title}
                        filtered_row.update(scores_dict)
                        filtered_submissions_data.append(filtered_row)
                    else:
                        logging.info("-> Low score. Routing to SENTIMENT DATA.")
                        sentiment_submissions_to_save.append({
                            "submission_id": submission.id, "content": submission_text, "upvotes": submission.score,
                            "num_comments": submission.num_comments,
                            "created_utc": datetime.fromtimestamp(submission.created_utc, timezone.utc).isoformat()
                        })
                else:
                    logging.info(f"-> Routing to NON-JOB DATA [{category}]: '{submission.title[:40]}...'")
                    non_job_submissions_to_save.append({
                        "submission_id": submission.id,
                        "content": submission_text,
                        "category": category,
                        "created_utc": datetime.fromtimestamp(submission.created_utc, timezone.utc).isoformat()
                    })

            except Exception as e:
                logging.error(f"Error processing submission {submission.id}: {e}", exc_info=True)
        
        # --- Save the collected data ---
        if output_mode == 'supabase' and supabase:
            if sentiment_submissions_to_save:
                logging.info(f"Saving {len(sentiment_submissions_to_save)} submissions to Supabase 'sentiment_submissions' table...")
                supabase.table("sentiment_submissions").upsert(sentiment_submissions_to_save).execute()
            if non_job_submissions_to_save:
                logging.info(f"Saving {len(non_job_submissions_to_save)} submissions to Supabase 'non_job_submissions' table...")
                supabase.table("non_job_submissions").upsert(non_job_submissions_to_save).execute()

        elif output_mode == 'csv':
            if sentiment_submissions_to_save:
                logging.info(f"Saving {len(sentiment_submissions_to_save)} submissions to '{SENTIMENT_DATA_FILE}'...")
                file_exists = os.path.exists(SENTIMENT_DATA_FILE) and os.path.getsize(SENTIMENT_DATA_FILE) > 0
                with open(SENTIMENT_DATA_FILE, 'a', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=sentiment_submissions_to_save[0].keys())
                    if not file_exists: writer.writeheader()
                    writer.writerows(sentiment_submissions_to_save)
            
            if non_job_submissions_to_save:
                logging.info(f"Saving {len(non_job_submissions_to_save)} non-job submissions to '{NON_JOB_POSTS_FILE}'...")
                file_exists = os.path.exists(NON_JOB_POSTS_FILE) and os.path.getsize(NON_JOB_POSTS_FILE) > 0
                with open(NON_JOB_POSTS_FILE, 'a', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=non_job_submissions_to_save[0].keys())
                    if not file_exists: writer.writeheader()
                    writer.writerows(non_job_submissions_to_save)
        
        if filtered_submissions_data:
            logging.info(f"Writing {len(filtered_submissions_data)} filtered job posts to '{FILTERED_JOB_POSTS_FILE}'...")
            file_exists = os.path.exists(FILTERED_JOB_POSTS_FILE) and os.path.getsize(FILTERED_JOB_POSTS_FILE) > 0
            with open(FILTERED_JOB_POSTS_FILE, 'a', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=filtered_submissions_data[0].keys())
                if not file_exists: writer.writeheader()
                writer.writerows(filtered_submissions_data)

        logging.info(f"✅ Successfully finished processing r/{subreddit_name}")
    except Exception as e:
        logging.error(f"An unexpected error occurred for r/{subreddit_name}: {e}", exc_info=True)


# --- 4. SCRIPT EXECUTION ---
def main():
    parser = argparse.ArgumentParser(description="Scrape and process Reddit submissions.")
    parser.add_argument("--output", choices=['supabase', 'csv'], required=True, help="The destination for the processed data.")
    parser.add_argument("--limit", type=int, default=250, help="The number of posts to fetch per subreddit.")
    args = parser.parse_args()

    supabase_client = None
    if args.output == 'supabase':
        try:
            supabase_url = os.getenv("SUPABASE_URL")
            supabase_key = os.getenv("SUPABASE_KEY")
            if not supabase_url or not supabase_key: raise ValueError("Supabase URL/Key missing.")
            supabase_client: Client = create_client(supabase_url, supabase_key)
        except Exception as e:
            logging.error(f"Failed to initialize Supabase client: {e}")
            return
            
    try:
        reddit_client = praw.Reddit(
            client_id=os.getenv("REDDIT_CLIENT_ID"),
            client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
            user_agent=os.getenv("REDDIT_USER_AGENT"),
            username=os.getenv("REDDIT_USERNAME"),
            password=os.getenv("REDDIT_PASSWORD"),
        )
        logging.info(f"PRAW initialized for user: {reddit_client.user.me()}")
    except Exception as e:
        logging.error(f"Failed to initialize PRAW client: {e}")
        return

    try:
        csv_path = os.path.join(script_dir, "subreddits.csv")
        with open(csv_path, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            subreddit_names = [row['subreddit_name'].strip() for row in reader if row.get('subreddit_name')]
        
        for subreddit_name in subreddit_names:
            process_subreddit(reddit_client, supabase_client, subreddit_name, args.limit, args.output)
        
        logging.info("--- All subreddits have been processed. ---")
    except Exception as e:
        logging.error(f"An error occurred: {e}", exc_info=True)

if __name__ == "__main__":
    main()