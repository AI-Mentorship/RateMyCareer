# RateMyCareer - Topic Analysis & Reporting

This directory contains tools for analyzing Reddit submissions to generate career insights, categorize topics, and score sentiments using LLMs.

## Prerequisites

Ensure you have the required Python packages installed:

```bash
pip install -r requirements.txt
```

You will also need a valid Google Gemini API key set in your environment variables:
```bash
export GEMINI_API_KEY="your_api_key_here"
# or on Windows PowerShell
$env:GEMINI_API_KEY="your_api_key_here"
```

## 1. Generating the Career Report (`topic.py`)

The main script `backend/topic/topic.py` fetches submissions from the database (or a CSV), uses an LLM to categorize and score them, and outputs a CSV report.

### Usage

```bash
python backend/topic/topic.py [options]
```

### Common Options

*   `--submission-out <filename>`: Specify the output CSV filename (default: `submission_matches.csv`).
*   `--use-llm`: Enable LLM-based verification and scoring (highly recommended for accuracy).
*   `--limit <number>`: Limit the number of submissions to process (useful for testing).
*   `--csv <filename>`: Load submissions from a specific CSV file instead of the database.

### Example Command

Generate a full report named `All_Careers_Report.csv` using the LLM for all available data:

```bash
python backend/topic/topic.py --submission-out "All_Careers_Report.csv" --use-llm --limit 1000000
```

## 2. Data Cleaning (`deduplicate_report.py`)

If you suspect duplicate entries in your generated report (e.g., same snippet appearing multiple times), use this script to clean it.

### Usage

```bash
python backend/deduplicate_report.py
```

This script automatically looks for `All_Careers_Report.csv` in the root directory, removes duplicate snippets, and overwrites the file.

## 3. Analyzing Scores (`calculate_category_scores.py`)

To get a high-level summary of average scores per category for each subreddit, run this analysis script.

### Usage

```bash
python backend/calculate_category_scores.py
```

### Output

*   Prints a formatted table to the console showing average scores (1.0 - 5.0) for categories like "Job Security", "Compensation", etc., grouped by subreddit.
*   Saves the summary to `Category_Scores_Summary.csv`.

## Workflow Summary

1.  **Generate Data**: Run `topic.py` to create the raw report.
2.  **Clean Data**: Run `deduplicate_report.py` to ensure data integrity.
3.  **Analyze**: Run `calculate_category_scores.py` to see the aggregated insights.
