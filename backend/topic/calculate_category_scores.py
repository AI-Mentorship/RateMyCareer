import pandas as pd
import os

def calculate_scores(file_path):
    print(f"Reading {file_path}...")
    try:
        df = pd.read_csv(file_path)
    except Exception as e:
        print(f"Error reading file: {e}")
        return

    if 'score' not in df.columns or 'category' not in df.columns or 'subreddit_id' not in df.columns:
        print("Error: Required columns (subreddit_id, category, score) not found.")
        return

    # Group by subreddit and category, then calculate mean score
    # Round to 3 decimal places for consistency
    summary = df.groupby(['subreddit_id', 'category'])['score'].mean().reset_index()
    summary['score'] = summary['score'].round(3)
    
    # Sort for better readability
    summary = summary.sort_values(by=['subreddit_id', 'score'], ascending=[True, False])

    print("\nFinal Scores per Category per Subreddit:")
    print("-" * 60)
    print(f"{'Subreddit':<20} | {'Category':<30} | {'Avg Score':<10}")
    print("-" * 60)
    
    for index, row in summary.iterrows():
        print(f"{row['subreddit_id']:<20} | {row['category']:<30} | {row['score']:<10}")

    # Also save to a file for reference
    output_path = "Category_Scores_Summary.csv"
    summary.to_csv(output_path, index=False)
    print("-" * 60)
    print(f"\nSummary saved to {output_path}")

if __name__ == "__main__":
    file_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "All_Careers_Report.csv")
    if not os.path.exists(file_path):
        file_path = "All_Careers_Report.csv"
    
    if os.path.exists(file_path):
        calculate_scores(file_path)
    else:
        print(f"File not found: {file_path}")
