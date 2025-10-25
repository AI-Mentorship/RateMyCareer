import os
from dotenv import load_dotenv
from transformers import pipeline
from supabase import create_client, Client

load_dotenv()

# tunable parameter for the neutral score range
NEUTRAL_RANGE = 0.05
REGRET_KEYWORDS = [
    'regret', 'mistake', 'wish i had', 'should have', "shouldn't have",
    'wrong choice', 'bad decision', 'go back', 'if only', 'messed up',
    'burnout', 'quit', 'unhappy', 'miserable', 'overwhelmed'
]

# Pagination settings
# We'll fetch and process rows in batches of 500
BATCH_SIZE = 500

url: str = os.getenv("SUPABASE_URL")
key: str = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(url, key)
print("✅ Successfully connected to Supabase.")


def analyze_text_with_chunking(text, pipeline):
    max_chunk_length = 500
    overlap = 50
    
    chunks = [text[i:i + max_chunk_length] for i in range(0, len(text), max_chunk_length - overlap)]

    results = pipeline(chunks)

    # Check if chunking or pipeline returned no results
    if not results:
        return {'sentiment_score': 0.0}

    total_score = 0
    for result in results:
        if result['label'] == 'LABEL_2':
            score = result['score']
        elif result['label'] == 'LABEL_0':
            score = -result['score']
        else: # 'LABEL_1'
            score = (result['score'] * 2 - 1) * NEUTRAL_RANGE
        
        total_score += score
        
    average_score = total_score / len(results)
    return {'sentiment_score': average_score}

def check_for_regret(text, keywords):
    text_to_search = text.lower()
    for keyword in keywords:
        if keyword in text_to_search:
            return True
    return False

print("🧠 Loading RoBERTa model...")
sentiment_pipeline = pipeline("sentiment-analysis", model="cardiffnlp/twitter-roberta-base-sentiment")
print("🤖 Model loaded successfully.")

# Main processing loop with pagination
page = 0
total_processed = 0

while True:
    # Calculate the row range for the current page
    start_row = page * BATCH_SIZE
    end_row = start_row + BATCH_SIZE - 1

    print(f"\n🔍 Fetching batch {page + 1} (rows {start_row} to {end_row})...")
    
    # Fetch a 'page' of un-analyzed submissions
    response = supabase.table('submissions') \
                       .select('submission_id, content') \
                       .eq('analyzed', False) \
                       .range(start_row, end_row) \
                       .execute()

    submissions_to_analyze = response.data

    # --- This is the exit condition for the loop ---
    if not submissions_to_analyze:
        print("🎉 No new submissions to analyze. All caught up!")
        break  # Exit the while loop
    
    print(f"🔬 Found {len(submissions_to_analyze)} submissions in this batch.")

    for submission in submissions_to_analyze:
        submission_id = submission['submission_id']
        content = submission['content']

        # Added a try/except block for safety, just in case one row fails
        try:
            sentiment_result = analyze_text_with_chunking(content, sentiment_pipeline)
            score = sentiment_result['sentiment_score']
            has_regret_result = check_for_regret(content, REGRET_KEYWORDS)

            update_data = {
                'sentiment_score': score,
                'has_regret': has_regret_result,
                'analyzed': True
            }

            supabase.table('submissions').update(update_data).eq('submission_id', submission_id).execute()
            print(f"   -> Processed and updated submission_id: {submission_id}")
            total_processed += 1

        except Exception as e:
            print(f"   ❌ ERROR processing submission {submission_id}: {e}")
            # Mark as analyzed anyway to avoid getting stuck on a bad row
            supabase.table('submissions').update({'analyzed': True, 'sentiment_score': None}).eq('submission_id', submission_id).execute()

    # Move to the next page for the next loop iteration
    page += 1

print(f"\n🚀 Analysis complete. Total submissions processed: {total_processed}")
