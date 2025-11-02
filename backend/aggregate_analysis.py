import os
from dotenv import load_dotenv
from supabase import create_client, Client
import pandas as pd
from datetime import datetime
from sklearn.linear_model import LinearRegression

# --- Setup and Connection ---
load_dotenv()
url: str = os.getenv("SUPABASE_URL")
key: str = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(url, key)
print("✅ Successfully connected to Supabase.")

# --- Pagination settings ---
BATCH_SIZE = 500

try:
    # --- 1. Fetch Analyzed Submissions (with Pagination) ---
    print("🚚 Fetching analyzed data from the 'submissions' table...")
    
    all_submissions_data = []
    page = 0
    
    while True:
        start_row = page * BATCH_SIZE
        end_row = start_row + BATCH_SIZE - 1
        
        print(f"   -> Fetching batch {page + 1} (rows {start_row} to {end_row})...")
        
        submissions_response = supabase.table('submissions').select(
            'subreddit_id, sentiment_score, has_regret, created_utc'
        ).not_.is_('sentiment_score', None).range(start_row, end_row).execute()
        
        if not submissions_response.data:
            print("   -> No more data found.")
            break # Exit the loop
        
        all_submissions_data.extend(submissions_response.data)
        page += 1

    if not all_submissions_data:
        print("🟡 No analyzed submissions found to aggregate. Exiting.")
        exit()

    submissions_df = pd.DataFrame(all_submissions_data)
    print(f"📊 Found a total of {len(submissions_df)} analyzed submissions to process.")

    # --- 2. Fetch Subreddit Info for Career Names ---
    print("🚚 Fetching career names from the 'subreddits' table...")
    subreddits_response = supabase.table('subreddits').select('subreddit_id, display_name').execute()
    subreddits_df = pd.DataFrame(subreddits_response.data)

    # --- 3. Perform Aggregation (Summary) ---
    print("⚙️  Calculating aggregate summary metrics...")
    grouped = submissions_df.groupby('subreddit_id')

    def calculate_regret_ratio(series):
        if len(series) == 0:
            return 0
        return series.sum() / len(series)

    aggregated_data = grouped.agg(
        avg_sentiment=('sentiment_score', 'mean'),
        sentiment_volatility=('sentiment_score', 'std'),
        regret_ratio=('has_regret', calculate_regret_ratio)
    ).reset_index()

    aggregated_data['sentiment_volatility'] = aggregated_data['sentiment_volatility'].fillna(0)
    
    # --- 4. Merge Data to Add Career Names ---
    # We do this merge *before* the regression so we can loop by 'career_name'
    submissions_with_names_df = pd.merge(submissions_df, subreddits_df, on='subreddit_id', how='left')
    submissions_with_names_df = submissions_with_names_df.dropna(subset=['display_name'])

    # --- 5. NEW: Train Linear Regression Models ---
    print("🧠 Training Linear Regression models for forecasting...")
    
    submissions_with_names_df['created_utc'] = pd.to_datetime(submissions_with_names_df['created_utc'])
    min_date = submissions_with_names_df['created_utc'].min()
    
    # 'days_elapsed' will be our X-axis (e.g., 0, 1, 7, 14, 21, etc.)
    submissions_with_names_df['days_elapsed'] = (submissions_with_names_df['created_utc'] - min_date).dt.total_seconds() / (24 * 60 * 60)
    
    forecast_results = []
    
    # Loop through each unique career
    for career_name in submissions_with_names_df['display_name'].unique():
        career_df = submissions_with_names_df[submissions_with_names_df['display_name'] == career_name]
        
        # catch case for lin reg (can be removed later)
        if len(career_df) < 2:
            print(f"   -> Skipping {career_name} (not enough data)")
            continue
            
        # Prepare data for scikit-learn
        X = career_df[['days_elapsed']] # X (features) must be a 2D array
        y = career_df['sentiment_score'] # y (target) is a 1D array
        
        # Train the model
        model = LinearRegression()
        model.fit(X, y)
        
        # Create a forecast 30 days from the *last post*
        last_day = X['days_elapsed'].max()
        future_day = last_day + 30
        
        future_day_df = pd.DataFrame([[future_day]], columns=['days_elapsed'])
        forecasted_score = model.predict(future_day_df)[0]
        
        # Get the subreddit_id for this career to merge later
        subreddit_id = career_df['subreddit_id'].iloc[0]
        
        forecast_results.append({
            'subreddit_id': subreddit_id,
            'forecasted_sentiment_avg': forecasted_score
        })
        print(f"   -> Forecast for {career_name}: {forecasted_score:.4f}")

    # Convert forecast results to a DataFrame
    forecast_df = pd.DataFrame(forecast_results)

    # --- 6. Combine All Results ---
    print("🤝 Merging summary data with forecast data...")
    # Merge the summary (avg_sentiment, etc.) with the new forecast
    final_df = pd.merge(aggregated_data, forecast_df, on='subreddit_id', how='left')
    # Merge in the career names
    final_df = pd.merge(final_df, subreddits_df.rename(columns={'display_name':'career_name'}), on='subreddit_id', how='left')


    # --- 7. Prepare Data for Insertion ---
    print("📝 Preparing final data for Supabase table...")
    final_df['record_date'] = datetime.now().isoformat()  
    final_df['vibe_score'] = None

    final_df = final_df[[
        'career_name', 'subreddit_id', 'record_date', 'avg_sentiment', 
        'sentiment_volatility', 'regret_ratio', 'forecasted_sentiment_avg', 'vibe_score'
    ]]

    final_df = final_df.dropna(subset=['career_name'])
    
    data_to_insert = final_df.to_dict(orient='records')

    # --- 8. Insert Data into the Aggregate Table ---
    if not data_to_insert:
        print("🟡 No data to insert after merging and filtering. Exiting.")
        exit()
        
    print(f" Inserting {len(data_to_insert)} new snapshot records into 'aggregate' table...")
    insert_response = supabase.table('aggregate').insert(data_to_insert).execute()
    
    print("✅ Aggregation complete! New snapshot has been successfully inserted.")

except Exception as e:
    print(f"❌ An error occurred: {e}")

