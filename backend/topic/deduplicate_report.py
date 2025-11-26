import pandas as pd
import os

def deduplicate_csv(file_path):
    print(f"Reading {file_path}...")
    try:
        df = pd.read_csv(file_path)
    except Exception as e:
        print(f"Error reading file: {e}")
        return

    original_count = len(df)
    print(f"Original row count: {original_count}")

    # Deduplicate based on 'snippet' column, keeping the first occurrence
    if 'snippet' in df.columns:
        df_cleaned = df.drop_duplicates(subset=['snippet'], keep='first')
        cleaned_count = len(df_cleaned)
        removed_count = original_count - cleaned_count
        
        print(f"Cleaned row count: {cleaned_count}")
        print(f"Removed {removed_count} duplicate rows.")

        if removed_count > 0:
            df_cleaned.to_csv(file_path, index=False)
            print(f"Successfully overwrote {file_path} with cleaned data.")
        else:
            print("No duplicates found. File unchanged.")
    else:
        print("Error: 'snippet' column not found in CSV.")

if __name__ == "__main__":
    # Adjust path as needed, assuming script is run from root or backend
    # The file is in the root D:\Ratemycareer\All_Careers_Report.csv
    file_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "All_Careers_Report.csv")
    
    if not os.path.exists(file_path):
        # Try relative path if running from root
        file_path = "All_Careers_Report.csv"
    
    if os.path.exists(file_path):
        deduplicate_csv(file_path)
    else:
        print(f"File not found: {file_path}")
