-----

# Reddit Scraper Usage Guide

This guide explains how to use the script to scrape, filter, and save Reddit posts.

-----

## Required Files

Your project folder needs to contain these items:

  * `reddit_scraper.py` (your main script)
  * `.env` (for API keys)
  * `subreddits.csv` (list of subreddits to scrape)
  * `copypastas_combined.txt` (list of known spam posts)
  * `sarcasm-model/` (the folder containing your sarcasm model files)

-----

## Configuration

You can control the script's output by changing settings in two places:

### 1\. Toggle Auxiliary CSV Files

At the top of the `reddit_scraper.py` script, you can find the `SAVE_AUXILIARY_DATA_TO_CSV` flag.

  * `SAVE_AUXILIARY_DATA_TO_CSV = True`
      * When running in **CSV mode**, this will save **all three** output files: the main sentiment data, the filtered posts, and the non-job posts.
  * `SAVE_AUXILIARY_DATA_TO_CSV = False`
      * When running in **CSV mode**, this will **only** save the main `job_sentiment_data.csv` file.

**Note:** This flag has no effect on Supabase mode.

### 2\. Choose Output Destination (CSV vs. Supabase)

You choose where to save the data using a command-line argument when you run the script. See the "How to Run" section for examples.

-----

## How the Filtering Works

The script uses a sophisticated two-stage pipeline to process each Reddit post:

1.  **Stage 1: Binary Classification**
    The script first uses an AI model to make a simple, high-level decision: is this post about "Workplace experiences and career development" or is it "Unrelated"?

2.  **Stage 2: Scoring & Sorting**
    If a post is identified as a "Workplace Post," it's then passed to a scoring function. This function calculates a score based on keywords to determine if the post is a **job advertisement** or a **genuine discussion**.

-----

## Understanding the Output

The script's output behavior depends on the mode you select.

### CSV Mode (`--output csv`)

  * `job_sentiment_data.csv`: This is your primary dataset. It contains genuine discussions and personal stories about workplace experiences.
  * `filtered_job_posts.csv`: This file contains posts that were flagged with a high score, which are primarily **job advertisements**.
  * `non_job_posts.csv`: This contains all posts that were classified as "Unrelated to work or careers."

*Note: The `filtered_job_posts.csv` and `non_job_posts.csv` files are only created if `SAVE_AUXILIARY_DATA_TO_CSV` is set to `True`.*

### Supabase Mode (`--output supabase`)

This mode is streamlined and **only saves the main, high-quality data**.

  * The script will save subreddit information to your `subreddits` table.
  * It will then save the genuine discussions (the same data that goes into `job_sentiment_data.csv`) to your `submissions` table.
  * **All filtered job ads and non-job posts are discarded in this mode.**

-----

## How to Run the Script

Use the command line to run the script. The `--limit` argument controls how many posts to fetch from each subreddit.

  * **To save to CSV files:**
    ```bash
    python reddit_scraper.py --output csv --limit 250
    ```
  * **To save to your Supabase database:**
    ```bash
    python reddit_scraper.py --output supabase --limit 100
    ```