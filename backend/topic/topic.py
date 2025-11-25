"""Topic extraction + per-topic sentiment analysis grouped by subreddit.

This script fetches submissions from the Supabase `submissions` table,
groups content by `subreddit_id`, extracts top noun-chunk topics using spaCy,
then scores sentences mentioning each topic with a review-trained Transformer
sentiment model (1-5 stars) and reports averaged scores per topic per subreddit.

Usage:
    python backend/topic.py --help

Dependencies:
    pip install spacy transformers torch supabase
    python -m spacy download en_core_web_sm

Notes:
 - The script reads SUPABASE_URL and SUPABASE_KEY from the repository root .env
   (it will also fall back to environment variables).
 - Results are printed and optionally written to CSV (--out path).
"""

import os
import csv
import logging
import argparse
import re

# --- Manual keyword list (user-provided expanded workplace keywords)
MANUAL_KEYWORDS = [
    # Roles & People
    'boss','manager','supervisor','employee','coworker','colleague','team','teammate','intern','internship','executive','director','client','customer','hr','human resources','recruiter',
    # Hiring Process
    'job','career','role','position','profession','occupation','interview','application','apply','resume','cv','cover letter','offer','hiring','onboarding','referral','background check',
    # Compensation & Benefits
    'salary','pay','wage','income','compensation','bonus','raise','promotion','perk','benefit','insurance','401k','pto','vacation','sick leave','parental leave','stock options',
    # Work Structure & Environment
    'company','workplace','office','corporate','startup','agency','firm','business','remote','wfh','hybrid','freelance','contract','contractor','part-time','full-time','shift','overtime',
    # Performance & Growth
    'review','performance','feedback','goal','training','development','promotion','mentor','mentorship','career path','career ladder','skill','certification',
    # Common Topics
    'workload','burnout','stress','toxic','culture','policy','meeting','project','deadline','layoff','severance','quit','resign','resignation','fired','termination'
]


def load_keywords_from_file(path: str):
    kws = []
    try:
        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                t = line.strip()
                if t:
                    kws.append(t.lower())
    except Exception:
        logger.warning(f'Could not load keywords file: {path}')
    return kws


from collections import defaultdict, Counter
from statistics import mean
from typing import List, Dict, Any

try:
    from dotenv import load_dotenv
    from supabase import create_client
except Exception:
    load_dotenv = None
    create_client = None

import warnings
warnings.filterwarnings("ignore")

logger = logging.getLogger("topic")
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def load_supabase_client():
    # Try multiple .env locations: backend/.env then repository root .env
    backend_root = os.path.dirname(os.path.dirname(__file__))
    repo_root = os.path.dirname(backend_root)
    candidate_envs = [os.path.join(backend_root, '.env'), os.path.join(repo_root, '.env')]

    loaded = False
    if load_dotenv:
        for p in candidate_envs:
            try:
                if os.path.exists(p):
                    load_dotenv(p)
                    logger.info(f'Loaded environment from {p}')
                    loaded = True
                    break
            except Exception:
                # non-fatal; try next
                continue

    # allow environment variables to be set externally as well
    url = os.getenv('SUPABASE_URL')
    key = os.getenv('SUPABASE_KEY')
    if not url or not key:
        logger.error('SUPABASE_URL or SUPABASE_KEY not found in environment or .env (checked backend/.env and repo root .env)')
        return None
    if not create_client:
        logger.error('supabase package not installed. pip install supabase')
        return None
    return create_client(url, key)


def resolve_subreddit_identifier(supabase, filter_str: str):
    """Try to resolve a subreddit name (like 'Teachers') to the internal subreddit_id by
    querying a `subreddits` table if present. Returns the matching id or None.
    """
    if not filter_str:
        return None
    try:
        # attempt to fetch candidate rows from a subreddits table
        res = supabase.table('subreddits').select('*').limit(1000).execute()
        rows = res.data if (res and getattr(res, 'data', None) is not None) else []
    except Exception:
        return None

    fs = str(filter_str).lower()
    for r in rows:
        # check common column names (include display_name used in your DB)
        for key in ('subreddit_id', 'id', 'name', 'subreddit_name', 'display_name'):
            val = r.get(key)
            if not val:
                continue
            if str(val).lower() == fs or fs in str(val).lower():
                # prefer subreddit_id field if present
                return r.get('subreddit_id') or r.get('id') or None
    return None


def convert_sentiment_to_score(sentiment_result: List[Dict[str, Any]]) -> int:
    # sentiment_result is a list-of-dicts returned by the pipeline
    if not sentiment_result:
        return 3
    label = sentiment_result[0].get('label', '')
    # Map common labels like '1 star' ... '5 stars'
    if isinstance(label, str):
        if '1' in label: return 1
        if '2' in label: return 2
        if '3' in label: return 3
        if '4' in label: return 4
        if '5' in label: return 5
    return 3


def extract_top_topics(nlp, texts, top_k: int = 5) -> List[str]:
    """Extract top noun-chunk topics from either a single string or an iterable of texts.

    To avoid exceeding spaCy's `nlp.max_length`, prefer passing a list of individual
    submission strings. The function will process each item separately and aggregate
    noun-chunk counts across items.
    """
    counts = Counter()

    # Helper to process a single text safely (truncate if necessary)
    def _process_text(t: str):
        if not t:
            return
        # ensure it's a string
        txt = str(t).lower()
        max_len = getattr(nlp, 'max_length', None) or 1000000
        if len(txt) > max_len:
            txt = txt[:max_len]
        try:
            doc = nlp(txt)
        except Exception as e:
            logger.debug(f"spaCy failed on a text chunk (len={len(txt)}): {e}")
            return
        for chunk in doc.noun_chunks:
            topic = chunk.text.strip()
            if len(topic) > 2 and topic not in nlp.Defaults.stop_words:
                counts[topic] += 1

    # If a single string was provided, process in chunks up to max_length
    if isinstance(texts, str):
        max_len = getattr(nlp, 'max_length', 1000000)
        # process in slices if the text is longer than max_len
        if len(texts) <= max_len:
            _process_text(texts)
        else:
            for i in range(0, len(texts), max_len):
                _process_text(texts[i:i+max_len])
    else:
        # assume iterable of texts or dict-like items
        for item in texts:
            if isinstance(item, dict):
                txt = item.get('content') or item.get('text') or ''
            else:
                txt = item
            _process_text(txt)

    return [t for t, _ in counts.most_common(top_k)]


# --- relevance filtering: keep career/workplace-related words and time/abstract concepts
# You can tweak these lists to broaden/narrow what counts as career-related.
CAREER_KEYWORDS = {
    'job', 'jobs', 'career', 'careers', 'work', 'works', 'office', 'offices', 'position', 'positions',
    'role', 'roles', 'company', 'companies', 'employer', 'employers', 'employee', 'employees',
    'manager', 'managers', 'boss', 'bosses', 'interview', 'interviews', 'resume', 'cv', 'hiring', 'hire',
    'salary', 'pay', 'wage', 'compensation', 'benefits', 'promotion', 'promotions', 'fired', 'firing',
    'client', 'clients', 'customer', 'customers', 'industry', 'industries', 'position', 'role', 'internship',
    'intern', 'interns', 'shift', 'commute', 'commuting', 'remote', 'office', 'workplace', 'work-life', 'culture',
    'team', 'teams', 'engineering', 'nursing', 'doctor', 'teacher', 'education', 'school', 'exam', 'test'
}

# allow some abstract/time concepts (user requested these be kept)
ABSTRACT_KEYWORDS = {
    'time', 'times', 'day', 'days', 'week', 'weeks', 'month', 'months', 'year', 'years', 'hour', 'hours',
    'experience', 'stress', 'burnout', 'growth', 'impact', 'later', 'now', 'soon', 'laterality'
}


def clean_topic_text(t: str) -> str:
    # remove stray parentheses and surrounding punctuation
    tt = t.strip()
    if tt.startswith('(') and tt.endswith(')'):
        tt = tt[1:-1].strip()
    # strip leading/trailing punctuation
    return tt.strip(" \"'.,:;()[]{}")


def normalize_topic_text(topic: str, nlp) -> str:
    """Normalize a topic string:
    - lowercase
    - remove surrounding punctuation and parentheses
    - strip leading articles and possessives (a, an, the, my, your, his, her, their, our)
    - remove extra internal whitespace
    - return the cleaned phrase
    """
    if not topic:
        return topic
    t = clean_topic_text(topic.lower())
    # remove leading articles/possessives
    prefixes = ('a ', 'an ', 'the ', 'my ', 'your ', 'his ', 'her ', 'their ', 'our ')
    for p in prefixes:
        if t.startswith(p):
            t = t[len(p):].strip()
            break

    # remove leading possessive markers like "john's " -> remove trailing 's on first token
    parts = t.split()
    if parts:
        first = parts[0]
        if first.endswith("'s"):
            parts[0] = first[:-2]
    t = ' '.join(parts)

    # Use spaCy lemmatization to merge plurals and normalize tokens.
    # Keep contentful tokens (nouns, proper nouns, adjectives, verbs) and drop determiners/pronouns.
    doc = nlp(t)
    kept = []
    for tok in doc:
        if tok.pos_ in ('DET', 'PRON', 'PART', 'PUNCT', 'SPACE'):
            continue
        lemma = tok.lemma_.lower().strip()
        if not lemma:
            continue
        # drop stray punctuation-only lemmas
        if all(ch in "'\".,:;()[]{}-" for ch in lemma):
            continue
        kept.append(lemma)

    t = ' '.join(kept)
    # final cleanup
    t = t.strip(" \"'.,:;()[]{}")
    t = ' '.join(t.split())
    return t


def is_relevant_topic(topic: str, nlp) -> bool:
    """Return True if topic looks career/workplace related or is allowed abstract/time concept.

    Heuristic checks:
    - any token lemma in CAREER_KEYWORDS or ABSTRACT_KEYWORDS
    - topic contains substrings commonly mentioning careers (school, exam, interview, manager, boss, data)
    - otherwise False
    """
    t = clean_topic_text(topic.lower())
    if not t:
        return False

    # exclude clearly personal / conversational fragments we don't want
    EXCLUDE_PATTERNS = {
        'friend', 'wife', 'husband', 'kids', 'kid', 'daughter', 'son', 'belt',
        'thanks', 'thank', 'advice', 'any thoughts', 'anyone', 'anyone else',
        'my friend', 'my wife', 'these kids', 'any thoughts?'
    }
    for ex in EXCLUDE_PATTERNS:
        if ex in t:
            return False

    # quick substring checks that strongly indicate career/workplace topics
    substr_allow = ('school', 'exam', 'test', 'interview', 'manager', 'boss', 'company', 'data', 'science', 'law', 'client', 'clinic', 'nurse', 'doctor', 'salary', 'pay', 'wage', 'promotion', 'hiring', 'remote', 'office', 'workplace')
    for s in substr_allow:
        if s in t:
            return True

    doc = nlp(t)
    # token lemma checks - require explicit career or abstract lemma
    for token in doc:
        lemma = token.lemma_.lower()
        if lemma in CAREER_KEYWORDS:
            return True
        if lemma in ABSTRACT_KEYWORDS:
            return True

    # If none of the above matched, do not allow generic nouns (this avoids 'my friend', 'my wife', etc.)
    return False


def filter_topics(topics: List[str], nlp, keep_time_and_abstract: bool = True) -> List[str]:
    out = []
    for t in topics:
        cleaned = clean_topic_text(t)
        if not cleaned:
            continue
        if is_relevant_topic(cleaned, nlp):
            out.append(cleaned)
        else:
            # keep time/abstract if requested
            if keep_time_and_abstract:
                # check if any abstract keyword appears
                low = cleaned.lower()
                if any(a in low for a in ABSTRACT_KEYWORDS):
                    out.append(cleaned)
    return out


def analyze_subreddit(subreddit_id: str,
                      texts: List[str],
                      nlp,
                      sentiment_pipeline,
                      tokenizer,
                      top_k: int = 5,
                      min_mentions: int = 1) -> Dict[str, Any]:
    """Analyze a list of submission texts for a single subreddit.

    Returns a dict with top topics and per-topic average score and counts.
    """
    # normalize texts: accept list of strings or list of dicts with 'content'
    normalized_texts = []
    for item in texts:
        if isinstance(item, dict):
            content = item.get('content') or ''
        elif isinstance(item, (list, tuple)) and len(item) >= 2:
            # (submission_id, content)
            content = item[1] or ''
        else:
            content = item or ''
        if content and str(content).strip():
            normalized_texts.append(str(content))

    logger.info(f'Analyzing subreddit: {subreddit_id} ({len(normalized_texts)} submissions)')
    corpus = " \n ".join(normalized_texts)
    if not corpus.strip():
        return {'subreddit_id': subreddit_id, 'topics': []}

    # Avoid passing a massive concatenated string to spaCy; process per-submission texts
    top_topics = extract_top_topics(nlp, normalized_texts, top_k=top_k)
    filtered_topics = filter_topics(top_topics, nlp, keep_time_and_abstract=True)
    logger.info(f'  Top topics: {top_topics} -> filtered: {filtered_topics}')

    docs = [nlp(t) for t in normalized_texts]

    topic_sentiments = {topic: [] for topic in filtered_topics}

    for topic in top_topics:
        for doc in docs:
            for sent in doc.sents:
                if topic in sent.text.lower():
                    max_len = getattr(tokenizer, 'model_max_length', 512)
                    text_piece = sent.text[:max_len]
                    try:
                        result = sentiment_pipeline(text_piece)
                        score = convert_sentiment_to_score(result)
                        topic_sentiments[topic].append(score)
                    except Exception as e:
                        logger.debug(f'  sentiment pipeline error for topic {topic}: {e}')
                        continue

    # --- normalize and merge near-duplicate topics (strip articles/possessives, dedupe)
    aggregated = defaultdict(list)
    for topic, scores in topic_sentiments.items():
        norm = normalize_topic_text(topic, nlp)
        if not norm:
            continue
        aggregated[norm].extend(scores)

    topics_out = []
    for norm_topic, scores in aggregated.items():
        if len(scores) >= min_mentions:
            avg = mean(scores)
            topics_out.append({'topic': norm_topic, 'avg_score': avg, 'mentions': len(scores)})
        else:
            topics_out.append({'topic': norm_topic, 'avg_score': None, 'mentions': len(scores)})

    return {'subreddit_id': subreddit_id, 'topics': topics_out}


def analyze_subreddit_by_keywords(subreddit_id: str,
                                  texts: List[str],
                                  nlp,
                                  sentiment_pipeline,
                                  tokenizer,
                                  keywords: List[str],
                                  min_mentions: int = 1) -> Dict[str, Any]:
    """Analyze texts for a subreddit by scanning sentences for manual keywords.

    For each keyword, collects sentence-level sentiment scores and returns averaged results.
    """
    logger.info(f'Analyzing subreddit by keywords: {subreddit_id} ({len(texts)} submissions)')
    # prepare keyword regex patterns (word-boundary where appropriate)
    kw_patterns = []
    for kw in keywords:
        k = kw.lower().strip()
        if not k:
            continue
        # use word boundaries for alphanumeric keywords; allow phrases as simple substring
        if re.match(r"^[a-z0-9_]+$", k):
            pat = re.compile(r"\\b" + re.escape(k) + r"\\b")
        else:
            pat = re.compile(re.escape(k))
        kw_patterns.append((k, pat))

    keyword_sentiments = {k: [] for k, _ in kw_patterns}
    # per-submission matches: list of dicts {submission_id, matched_keywords, submission_score}
    submission_matches = []

    # We need submission ids; texts may be tuples (submission_id, content) or strings.
    # Normalize inputs: allow texts to be list of dicts with 'submission_id' and 'content'
    normalized_texts = []
    for item in texts:
        if isinstance(item, dict):
            sid = item.get('submission_id')
            content = item.get('content', '')
        elif isinstance(item, (list, tuple)) and len(item) >= 2:
            sid, content = item[0], item[1]
        else:
            sid = None
            content = item
        normalized_texts.append({'submission_id': sid, 'content': content})

    for item in normalized_texts:
        sid = item.get('submission_id')
        content = item.get('content') or ''
        doc = nlp(content)
        submission_scores = []
        matched = set()
        for sent in doc.sents:
            s = sent.text.strip()
            if not s:
                continue
            low = s.lower()
            for k, pat in kw_patterns:
                if pat.search(low):
                    matched.add(k)
                    try:
                        max_len = getattr(tokenizer, 'model_max_length', 512)
                        text_piece = s[:max_len]
                        result = sentiment_pipeline(text_piece)
                        score = convert_sentiment_to_score(result)
                        keyword_sentiments[k].append(score)
                        submission_scores.append(score)
                    except Exception as e:
                        logger.debug(f' sentiment error for kw {k}: {e}')
                        continue

        # record per-submission match if any keywords matched
        if matched:
            submission_matches.append({'submission_id': sid, 'matched_keywords': sorted(matched), 'submission_score': (mean(submission_scores) if submission_scores else None)})

    topics_out = []
    for k, scores in keyword_sentiments.items():
        if len(scores) >= min_mentions:
            topics_out.append({'topic': k, 'avg_score': mean(scores), 'mentions': len(scores)})
        else:
            # include even if below min_mentions but mark None (keeps behavior consistent)
            topics_out.append({'topic': k, 'avg_score': (mean(scores) if scores else None), 'mentions': len(scores)})

    # filter out zero-mention keywords to reduce output size
    topics_out = [t for t in topics_out if t['mentions'] > 0]
    return {'subreddit_id': subreddit_id, 'topics': topics_out, 'submission_matches': submission_matches}


def fetch_submissions_grouped(supabase, filter_subreddit: str = None, limit: int = 10000):
    try:
        # Supabase has paging limits on single requests; fetch in pages to cover up to `limit` rows
        rows = []
        page_size = 1000
        fetched = 0
        start = 0

        # Try including subreddit_name if present in DB; if query fails due to missing column,
        # fall back to a safer column list without subreddit_name.
        include_subreddit_name = True
        attempted_with_name = False

        while fetched < limit:
            end = min(start + page_size - 1, limit - 1)
            cols = 'submission_id,content,subreddit_id,subreddit_name,created_utc' if include_subreddit_name else 'submission_id,content,subreddit_id,created_utc'
            try:
                q = supabase.table('submissions').select(cols).range(start, end)
                res = q.execute()
                # if the client returns an error payload, raise to be handled below
                if isinstance(res, dict) and res.get('code'):
                    raise Exception(res)
                page = res.data if (res and getattr(res, 'data', None) is not None) else []
            except Exception as e:
                # If we haven't yet tried without subreddit_name and the error suggests missing column, retry without it
                err_str = str(e)
                if include_subreddit_name and (('subreddit_name' in err_str) or (isinstance(e, dict) and e.get('code') == '42703')):
                    logger.info('subreddit_name column not present; retrying submissions query without that column')
                    include_subreddit_name = False
                    attempted_with_name = True
                    # restart pagination from beginning using the narrower column set
                    rows = []
                    fetched = 0
                    start = 0
                    continue
                logger.error(f'Error querying submissions: {e}')
                return {}

            if not page:
                break
            rows.extend(page)
            fetched += len(page)
            if len(page) < page_size:
                break
            start += page_size
    except Exception as e:
        logger.error(f'Error querying submissions: {e}')
        return {}

    by_sub = defaultdict(list)
    for r in rows:
        content = r.get('content') or ''
        sid = r.get('subreddit_id') or r.get('subreddit_name') or 'unknown'
        sname = r.get('subreddit_name') or ''
        if not content or not content.strip():
            continue
        # If filter_subreddit provided, only include rows that match id or name (case-insensitive)
        if filter_subreddit:
            fs = str(filter_subreddit).lower()
            if not (str(sid).lower() == fs or str(sname).lower() == fs):
                continue
        # store dicts so downstream can access submission_id
        by_sub[sid].append({'submission_id': r.get('submission_id'), 'content': content.strip()})
    return by_sub


def write_results_csv(out_path: str, results: List[Dict[str, Any]]):
    fieldnames = ['subreddit_id', 'topic', 'avg_score', 'mentions']
    with open(out_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in results:
            sid = r.get('subreddit_id')
            for t in r.get('topics', []):
                writer.writerow({'subreddit_id': sid, 'topic': t.get('topic'), 'avg_score': (f"{t.get('avg_score'):.3f}" if t.get('avg_score') is not None else ''), 'mentions': t.get('mentions')})


def write_submission_matches_csv(out_path: str, results: List[Dict[str, Any]]):
    fieldnames = ['subreddit_id', 'submission_id', 'matched_keywords', 'submission_score']
    with open(out_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in results:
            sid = r.get('subreddit_id')
            for s in r.get('submission_matches', []):
                writer.writerow({'subreddit_id': sid, 'submission_id': s.get('submission_id'), 'matched_keywords': ';'.join(s.get('matched_keywords', [])), 'submission_score': (f"{s.get('submission_score'):.3f}" if s.get('submission_score') is not None else '')})


def main():
    parser = argparse.ArgumentParser(description='Topic + per-topic sentiment analysis grouped by subreddit')
    parser.add_argument('--subreddit', help='(optional) subreddit_id to limit to')
    parser.add_argument('--top-k', type=int, default=6, help='Top K topics to extract per subreddit')
    parser.add_argument('--min-mentions', type=int, default=1, help='Minimum mentions to report a topic')
    parser.add_argument('--mode', choices=['keywords', 'noun'], default='keywords', help='Analysis mode: use manual keywords or noun-chunk topics')
    parser.add_argument('--keywords-file', help='Optional newline-delimited file with extra keywords to include (one per line)')
    parser.add_argument('--out', help='Optional CSV output path')
    parser.add_argument('--submission-out', help='Optional CSV path to write per-submission matched keywords')
    parser.add_argument('--limit', type=int, default=20000, help='Limit number of submissions fetched')
    args = parser.parse_args()

    supabase = load_supabase_client()
    if not supabase:
        logger.error('Could not initialize Supabase client; exiting')
        return

    import spacy
    from transformers import pipeline, AutoTokenizer

    logger.info('Loading spaCy model...')
    nlp = spacy.load('en_core_web_sm')

    logger.info('Loading sentiment model (this may take a while)...')
    model_name = 'nlptown/bert-base-multilingual-uncased-sentiment'
    sentiment_pipeline = pipeline('sentiment-analysis', model=model_name)
    tokenizer = AutoTokenizer.from_pretrained(model_name)

    # prepare keywords if requested
    keywords = []
    if args.mode == 'keywords':
        keywords = [k.lower() for k in MANUAL_KEYWORDS]
        if args.keywords_file:
            keywords += load_keywords_from_file(args.keywords_file)

    # try to resolve subreddit name to id via subreddits table (if available)
    filter_id = None
    if args.subreddit:
        filter_id = resolve_subreddit_identifier(supabase, args.subreddit)
        if not filter_id:
            # fall back to using the argument directly (it may already be an id)
            filter_id = args.subreddit
        logger.info(f"Resolved subreddit filter '{args.subreddit}' -> '{filter_id}'")

    by_sub = fetch_submissions_grouped(supabase, filter_subreddit=filter_id, limit=args.limit)
    if not by_sub:
        logger.warning('No submissions found to analyze')
        return

    results = []
    for sid, texts in by_sub.items():
        if args.mode == 'keywords':
            res = analyze_subreddit_by_keywords(sid, texts, nlp, sentiment_pipeline, tokenizer, keywords, min_mentions=args.min_mentions)
        else:
            res = analyze_subreddit(sid, texts, nlp, sentiment_pipeline, tokenizer, top_k=args.top_k, min_mentions=args.min_mentions)
        results.append(res)

    for r in results:
        print('\n=== Subreddit:', r['subreddit_id'], '===')
        for t in r['topics']:
            if t['avg_score'] is not None:
                print(f"- {t['topic']}: avg={t['avg_score']:.2f} stars ({t['mentions']} mentions)")
            else:
                print(f"- {t['topic']}: no mentions found in sentences ({t['mentions']})")

    if args.out:
        logger.info(f'Writing CSV to {args.out}')
        write_results_csv(args.out, results)
    # optionally write per-submission matches
    if args.submission_out:
        logger.info(f'Writing submission matches CSV to {args.submission_out}')
        write_submission_matches_csv(args.submission_out, results)
    elif args.out:
        # default submission-out next to main out if requested
        sub_out = args.out + '.submissions.csv'
        logger.info(f'Writing submission matches CSV to {sub_out}')
        write_submission_matches_csv(sub_out, results)


if __name__ == '__main__':
    main()
