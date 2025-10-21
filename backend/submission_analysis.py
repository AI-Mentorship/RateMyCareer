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

url: str = os.getenv("SUPABASE_URL")
key: str = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(url, key)
print("✅ Successfully connected to Supabase.")


def analyze_text_with_chunking(text, pipeline):

    max_chunk_length = 500
    overlap = 50
    
    chunks = [text[i:i + max_chunk_length] for i in range(0, len(text), max_chunk_length - overlap)]

    results = pipeline(chunks)

    total_score = 0

    for result in results:
        if result['label'] == 'LABEL_2':
            score = result['score']
        elif result['label'] == 'LABEL_0':
            score = -result['score']
        # For neutral labels, we map the confidence to a small range around zero
        else: # 'LABEL_1'
            # (result['score'] * 2 - 1) maps the [0, 1] confidence to [-1, 1]
            # We then scale it by our small NEUTRAL_RANGE
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

print("🔍 Fetching un-analyzed submissions from the 'submissions' table...")
response = supabase.table('submissions').select('submission_id, content').eq('analyzed', False).execute()
submissions_to_analyze = response.data

if not submissions_to_analyze:
    print("🎉 No new submissions to analyze. All caught up!")
else:
    print(f"🔬 Found {len(submissions_to_analyze)} submissions to analyze.")

    for submission in submissions_to_analyze:
        submission_id = submission['submission_id']
        content = submission['content']

        sentiment_result = analyze_text_with_chunking(content, sentiment_pipeline)

        score = sentiment_result['sentiment_score']

        has_regret_result = check_for_regret(content, REGRET_KEYWORDS)

        # Prepare the result for Supabase using the float score
        update_data = {
            'sentiment_score': score,
            'has_regret': has_regret_result,
            'analyzed': True
        }

        supabase.table('submissions').update(update_data).eq('submission_id', submission_id).execute()
        print(f"   -> Processed and updated submission_id: {submission_id}")

    print("🚀 Analysis complete. All new submissions have been updated in Supabase.")
