# --------------------------------------
# Step 1: Imports
# --------------------------------------
import os
import json
import time
import requests # Use requests for robust REST API calls
from getpass import getpass
from dotenv import load_dotenv
from supabase import create_client, Client

# --------------------------------------
# Step 2: Connect to Supabase & Gemini
# --------------------------------------
# Load environment variables from .env file
load_dotenv() 

print("Connecting to Supabase...")
SUPABASE_URL = os.environ.get("SUPABASE_URL") or getpass("Enter your Supabase URL: ")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY") or getpass("Enter your Supabase Key: ")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
print("✅ Connected to Supabase.")

print("Configuring Gemini...")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY") or getpass("Enter your Gemini API key: ")
# Use the REST API endpoint
GEMINI_API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-09-2025:generateContent?key={GEMINI_API_KEY}"
print("✅ Gemini configured.")

# --------------------------------------
# Step 3: Helper Functions (Supabase)
# --------------------------------------
def get_all_careers():
    """Fetches a unique list of career names from the subreddits table."""
    try:
        response = supabase.table("subreddits").select("career_name").execute()
        careers_with_duplicates = [r["career_name"] for r in response.data if r.get("career_name")]
        return list(set(careers_with_duplicates))
    except Exception as e:
        print(f"Error fetching careers: {e}")
        return []

def get_subreddit_ids_for_career(career_name):
    """Gets all subreddit_ids associated with a single career name."""
    try:
        response = supabase.table("subreddits") \
            .select("subreddit_id") \
            .eq("career_name", career_name) \
            .execute()
        return [r["subreddit_id"] for r in response.data]
    except Exception as e:
        print(f"Error fetching subreddit IDs for {career_name}: {e}")
        return []

def get_all_posts_for_subreddit_ids(subreddit_ids):
    """
    --- THIS IS THE UPGRADED FUNCTION ---
    Fetches the TOP 10 posts for a list of subreddit_ids, ordered by upvotes.
    """
    if not subreddit_ids:
        return []

    print(f"   Fetching top 10 posts for {len(subreddit_ids)} subreddit(s)...")
    
    try:
        # --- THIS IS THE NEW QUERY ---
        # Select content and upvotes
        # Order by upvotes in descending order
        # Limit to the top 5 (changed from 10)
        response = supabase.table("submissions") \
            .select("content, upvotes") \
            .in_("subreddit_id", subreddit_ids) \
            .not_.is_("content", None) \
            .order("upvotes", desc=True) \
            .limit(5) \
            .execute()
        
        all_posts = [p["content"] for p in response.data if p.get("content")]
        print(f"   Found {len(all_posts)} top posts.")
        return all_posts

    except Exception as e:
        print(f"Error during post pagination: {e}")
        return []
            
# --------------------------------------
# Step 4: Summarization with Gemini (REST API)
# --------------------------------------
def summarize_career(career_name, posts_list):
    """
    --- THIS IS THE UPGRADED FUNCTION ---
    Generates a summary using the Gemini REST API with error handling.
    """
    if not posts_list:
        return "No posts found for this career yet."

    # Combine all posts into one large text block
    posts_text = "\n\n".join(posts_list)

    # The prompt from your teammate's code (it's a good prompt)
    prompt = f"""
Summarize the career '{career_name}' based on the following Reddit posts.
Your summary should be well-structured and answer these questions:
- What are the common day-to-day responsibilities?
- What are the most common challenges and complaints?
- What are the most common positive aspects and rewards?
- What is the overall sentiment (e.g., positive, negative, mixed)?

Make under 100 words. Non-negotiable.

Posts:
{posts_text}
"""

    # Construct the API payload
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.5,
            "maxOutputTokens": 1500 # Increased from 500
        }
    }
    
    # API call with exponential backoff (as per guidelines)
    max_retries = 5
    backoff_time = 1
    for i in range(max_retries):
        try:
            response = requests.post(
                GEMINI_API_URL, 
                headers={"Content-Type": "application/json"}, 
                data=json.dumps(payload)
            )
            response.raise_for_status() # Raise an exception for bad status codes
            
            # Safely parse the JSON response
            result = response.json()
            
            # Use .get() for safe nested dictionary access
            candidates = result.get('candidates', [])
            if candidates:
                content = candidates[0].get('content', {})
                parts = content.get('parts', [])
                if parts:
                    return parts[0].get('text', "No summary could be generated.").strip()

            print(f"   Warning: Received an empty response from API: {result}")
            return "No summary could be generated (empty response)."

        except requests.exceptions.RequestException as e:
            print(f"   API Error: {e}. Retrying in {backoff_time}s...")
            time.sleep(backoff_time)
            backoff_time *= 2 # Exponential backoff
        except Exception as e:
            print(f"   An unexpected error occurred: {e}")
            return f"Summary generation failed: {e}"
            
    return "Summary generation failed after multiple retries."

# --------------------------------------
# Step 5: Generate summaries for all careers
# --------------------------------------
def main():
    careers = get_all_careers()
    if not careers:
        print("No careers found in 'subreddits' table. Exiting.")
        return

    print(f"\nFound {len(careers)} unique careers to process.\n")

    for career in careers:
        print(f"--- Processing career: {career} ---")
        
        subreddit_ids = get_subreddit_ids_for_career(career)
        if not subreddit_ids:
            print(f"   No subreddit IDs found for {career}. Skipping.")
            continue
            
        posts_list = get_all_posts_for_subreddit_ids(subreddit_ids)
        if not posts_list:
            print(f"   No posts found for {career}. Skipping.")
            continue
        
        print(f"   Generating summary for {career}...")
        summary = summarize_career(career, posts_list)
        
        print(f"   Summary generated. Saving to Supabase...")
        
        try:
            # Save to Supabase (using schema table 'career_summaries')
            # The 'on_conflict' matches your teammate's code and your schema
            supabase.table("career_summaries").upsert({
                "career_name": career,
                "summary": summary
            }, on_conflict="career_name").execute()
            print(f"   ✅ Successfully saved summary for {career}.")
        
        except Exception as e:
            print(f"   ❌ Error saving summary for {career}: {e}")

    print("\n🎉 All career summaries generated and saved successfully!")

if __name__ == "__main__":
    main()