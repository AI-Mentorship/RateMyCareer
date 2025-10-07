#important note: This file will most likely get delete in the near future
# this is here now only for testing and progression purposes.
#The "chopped_chin" csv file is an test.

import os
import pandas as pd
import numpy as np
import praw
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer as SIA
from dotenv import load_dotenv

load_dotenv()

user_agent = "Praw Test 1.0 by /u/Odd_Interaction5417"
reddit = praw.Reddit(
    client_id=os.getenv("CLIENT_ID"),
    client_secret=os.getenv("CLIENT_SECRET"),
    user_agent = user_agent
)

headlines = set()
for submission in reddit.subreddit('cscareerquestions').new(limit=None):
    headlines.add(submission.title)

df = pd.DataFrame(headlines)


nltk.download('vader_lexicon')
sia = SIA()
result = []

for line in headlines:
    pol_score = sia.polarity_scores(line)
    pol_score['headlines'] = line
    result.append(pol_score)

df = pd.DataFrame.from_records(result)


df['label'] = 0
df.loc[df['compound'] > 0.2, 'label'] = 1
df.loc[df['compound'] < -0.2, 'label'] = -1
df.head()

df2 = df[['headlines', 'label']]
#df2.to_csv('chopped_chin.csv', encoding='utf-8', index=False)