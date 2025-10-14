# Data Processor Usage Guide

This guide explains how to use the data processor script to scrape and filter Reddit posts.

## 1. Files and Folders:

Your project folder needs to contain these items:
- finetunetest.py (your main script)
- .env (for API keys)
- subreddits.csv (list of subreddits to scrape)
- copypastas_combined.txt (list of known spam posts)
- anti_flair.csv (list of flairs to penalize for each subreddit)
- sarcasm-model/ (the folder containing your sarcasm model files)

## 2. What the Script Does:

The script performs a two-step process on each Reddit post to decide where to save it:
1. Classification: It uses an AI model to determine the post's topic (Job Experience, Self-Promotion, Technical Question, etc.).
2. Scoring: It calculates a "spam/low-quality" score for the post.

## 3. Where the Data Goes:

Based on the two steps above, posts are sorted into three files:
- job_sentiment_data.csv: This is your main dataset. It contains high-quality posts classified as Job Experience that have a low spam score.
- filtered_job_posts.csv: This is your review file. It contains job posts that were flagged with a high spam score, which may be sarcastic or spammy job listings.
- non_job_posts.csv: This contains all posts that were not about job experiences, such as self-promotion or technical questions. This is useful for future AI model training.

## 4. How to Run the Script:

Use the command line to run the script.
- To save to CSV files:
  python finetunetest.py --output csv --limit 250
- To save to a Supabase database:
  python finetunetest.py --output supabase --limit 100