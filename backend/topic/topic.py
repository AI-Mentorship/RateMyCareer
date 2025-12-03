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
import time
from typing import List, Dict, Any
from collections import defaultdict, Counter
from statistics import mean

# --- Topic Categories (Grouped Keywords)
TOPIC_CATEGORIES = {
    'Compensation & Benefits': [
        'salary', 'pay', 'wage', 'income', 'compensation', 'bonus', 'raise', 'commission', 
        'equity', 'stock options', 'rsu', '401k', 'pension', 'benefits', 'insurance', 
        'health', 'dental', 'vision', 'pto', 'vacation', 'sick leave', 'parental leave', 
        'maternity leave', 'paternity leave', 'severance', 'reimbursement', 'stipend',
        'union', 'dues', 'paycheck', 'unpaid'
    ],
    'Management & Leadership': [
        'boss', 'manager', 'supervisor', 'lead', 'director', 'executive', 'ceo', 'cto', 
        'cfo', 'vp', 'leadership', 'management', 'micromanagement', 'micromanager', 
        'owner', 'founder', 'admin', 'administration', 'upper management',
        'principal', 'superintendent', 'district', 'school board', 'board of', 'board member', 'head of', 'chief'
    ],
    'Work Culture & Environment': [
        'culture', 'environment', 'atmosphere', 'vibe', 'toxic', 'toxicity', 'stress', 
        'burnout', 'pressure', 'politics', 'drama', 'harassment', 'discrimination', 
        'racism', 'sexism', 'diversity', 'inclusion', 'remote', 'wfh', 'hybrid', 
        'office', 'flexible', 'flexibility', 'work-life balance', 'balance', 'morale',
        'respect', 'disrespect', 'valued', 'appreciated', 'bullying', 'safety', 'safe', 'unsafe', 'support', 'unsupported'
    ],
    'Career Growth & Development': [
        'promotion', 'promote', 'growth', 'career path', 'ladder', 'advancement', 
        'training', 'learning', 'development', 'mentor', 'mentorship', 'skill', 
        'upskill', 'certification', 'review', 'performance', 'feedback', 'goal', 'objective',
        'exam', 'test', 'licensing', 'license', 'exams', 'tests'
    ],
    'Hiring & Onboarding': [
        'interview', 'recruiter', 'hr', 'human resources', 'hiring', 'application', 
        'apply', 'resume', 'cv', 'offer', 'negotiation', 'onboarding', 'orientation', 
        'background check', 'referral', 'candidate', 'process', 'job description',
        'hired', 'job offer', 'job hunt', 'job search', 'rejection', 'accepted', 'start date', 
        'new job', 'leaving', 'quit', 'resigned', 'resignation', 'notice'
    ],
    'Workload & Operations': [
        'workload', 'hours', 'overtime', 'shift', 'schedule', 'deadline', 'meeting', 
        'project', 'task', 'bandwidth', 'capacity', 'busy', 'slow', 'crunch', 'sprint', 
        'agile', 'scrum', 'process', 'workflow', 'tools', 'software', 'hardware', 'equipment',
        'paperwork', 'email', 'emails', 'admin work', 'duties', 'responsibilities', 
        'teaching', 'grading', 'planning', 'lesson', 'curriculum', 'classroom', 
        'rounds', 'patient', 'client', 'customer', 'student', 'parent',
        'students', 'parents', 'patients', 'clients', 'customers', 'classes', 'schools', 'teach'
    ],
    'Job Security & Stability': [
        'layoff', 'laid off', 'firing', 'fired', 'termination', 'let go', 'redundancy', 
        'restructure', 'reorganization', 'stable', 'stability', 'secure', 'security', 
        'contract', 'temp', 'freelance', 'gig', 'unemployed', 'unemployment'
    ],
    'Team & Colleagues': [
        'team', 'coworker', 'colleague', 'peer', 'partner', 'staff', 'employee', 
        'people', 'social', 'collaboration', 'collaborative', 'support', 'supportive', 'clique',
        'nurse', 'nurses', 'doctor', 'doctors', 'teacher', 'teachers'
    ]
}

# --- LLM Verification Logic
def verify_with_llm(snippets: List[str], api_key: str) -> Dict[str, Dict[str, Any]]:
    """
    Sends a batch of snippets to Gemini to verify relevance, sentiment, and category.
    Returns a dict mapping snippet -> {category, score, relevant}
    """
    import google.generativeai as genai
    
    if not api_key:
        logger.error("No GEMINI_API_KEY provided.")
        return {}

    genai.configure(api_key=api_key)
    # Use gemini-2.0-flash as verified from list_models
    try:
        model = genai.GenerativeModel('gemini-2.0-flash')
    except Exception:
        # Fallback
        model = genai.GenerativeModel('gemini-flash-latest')

    # Prepare the prompt
    categories_str = ", ".join(TOPIC_CATEGORIES.keys())
    
    verified_data = {}
    
    # Process in batches of 10 to avoid token limits/timeouts
    batch_size = 10
    for i in range(0, len(snippets), batch_size):
        batch = snippets[i:i+batch_size]
        
        prompt = f"""
        You are a data analyst verifying career reviews.
        I will provide a list of text snippets. For each snippet:
        1. Determine if it is RELEVANT to a career discussion (ignore spam, politics, or unrelated chatter).
        2. Identify the PRIMARY category from this list: [{categories_str}]. If none fit, use "Other".
        3. Assign a sentiment score from 1 (Negative) to 5 (Positive).
        
        Format your response as a JSON list of objects with keys: "snippet_index", "relevant" (bool), "category", "score" (1-5).
        
        Snippets:
        """
        
        for idx, s in enumerate(batch):
            prompt += f"\n{idx}. {s}"
            
        try:
            response = model.generate_content(prompt)
            # Simple parsing of the JSON response
            # We expect the model to return a code block with JSON
            text = response.text
            # Extract JSON part
            json_match = re.search(r'```json\s*(.*?)\s*```', text, re.DOTALL)
            if not json_match:
                json_match = re.search(r'\[.*\]', text, re.DOTALL)
            
            if json_match:
                import json
                data = json.loads(json_match.group(1) if json_match.group(1) else json_match.group(0))
                
                for item in data:
                    idx = item.get('snippet_index')
                    if idx is not None and 0 <= idx < len(batch):
                        original_snippet = batch[idx]
                        verified_data[original_snippet] = {
                            'relevant': item.get('relevant', False),
                            'category': item.get('category', 'Other'),
                            'score': item.get('score', 3)
                        }
            else:
                logger.warning(f"Could not parse JSON from LLM response for batch {i}")
                
        except Exception as e:
            logger.error(f"LLM Error on batch {i}: {e}")
            if "429" in str(e) or "Quota exceeded" in str(e):
                logger.info("Hit rate limit. Sleeping for 60 seconds...")
                time.sleep(60)
            else:
                time.sleep(2) # Backoff
            
        time.sleep(4) # Rate limit niceness (15 RPM limit = 1 req / 4 sec)

    return verified_data

# --- Advanced Logic Constraints
# Define rules to reduce false positives
KEYWORD_CONSTRAINTS = {
    'let go': {
        # Must be preceded by passive voice indicators to mean "fired"
        # e.g. "was let go", "got let go", "be let go"
        'required_regex': r'\b(was|were|been|be|get|got|getting)\s+let\s+go\b'
    },
    'maternity leave': {
        # Exclude if talking about covering for someone else
        'excluded_words': ['sub', 'substitute', 'cover', 'covering', 'replacement', 'fill', 'filling']
    },
    'paternity leave': {
        'excluded_words': ['sub', 'substitute', 'cover', 'covering', 'replacement', 'fill', 'filling']
    },
    'sick leave': {
        'excluded_words': ['sub', 'substitute', 'cover', 'covering']
    },
    'boss': {
        'excluded_words': ['final', 'level', 'game']
    },
    'vacation': {
        'excluded_words': ['student', 'students', 'kid', 'kids', 'child', 'children']
    }
}



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


def check_constraints(text: str, keyword: str) -> bool:
    """Check if a keyword match in text satisfies defined constraints."""
    constraints = KEYWORD_CONSTRAINTS.get(keyword)
    if not constraints:
        return True
        
    # Check excluded words (simple substring check in the surrounding window or whole sentence)
    # For simplicity, we check the whole sentence 'text'
    if 'excluded_words' in constraints:
        for bad_word in constraints['excluded_words']:
            # Check if bad_word appears in the text
            # Use word boundary to avoid partial matches if needed, but simple check is often enough
            if re.search(r'\b' + re.escape(bad_word) + r'\b', text):
                return False
                
    # Check required regex
    if 'required_regex' in constraints:
        pattern = constraints['required_regex']
        if not re.search(pattern, text):
            return False
            
    return True


def apply_llm_verification(results: List[Dict[str, Any]], verified_data: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Updates the results structure using the verified data from the LLM.
    Re-calculates topic averages and filters out irrelevant snippets.
    """
    updated_results = []
    
    for r in results:
        subreddit_id = r['subreddit_id']
        new_matches = []
        
        # Group scores by category to recalculate averages
        category_scores = defaultdict(list)
        
        for m in r.get('submission_matches', []):
            snippet = m.get('snippet')
            if snippet in verified_data:
                v = verified_data[snippet]
                if v.get('relevant'):
                    # Update the match with LLM data
                    # We replace 'matched_keywords' with the LLM category for consistency in CSV output
                    cat = v.get('category')
                    score = v.get('score')
                    
                    # Update the match object
                    m['matched_keywords'] = [cat] # Treat category as the "keyword"
                    m['submission_score'] = score
                    new_matches.append(m)
                    
                    # Add to aggregation
                    category_scores[cat].append(score)
            else:
                # If not verified (maybe LLM failed?), keep original or discard?
                # Let's keep original to be safe, or discard if we want strict LLM filtering.
                # For now, let's keep it but maybe mark it? 
                # Actually, if we requested verification and didn't get it, it's safer to keep it 
                # but we might have mixed data. Let's assume verified_data covers everything we sent.
                new_matches.append(m)
                # We need to re-add its original contribution to averages if we keep it
                # But we don't have the original category easily accessible here without re-parsing.
                # So let's just skip re-aggregating unverified items to keep stats clean.
                pass

        # Re-build topics list
        new_topics = []
        for cat, scores in category_scores.items():
            new_topics.append({
                'topic': cat,
                'avg_score': mean(scores),
                'mentions': len(scores),
                'examples': [] # We could populate this if we wanted
            })
            
        updated_results.append({
            'subreddit_id': subreddit_id,
            'topics': new_topics,
            'submission_matches': new_matches
        })
        
    return updated_results


def analyze_subreddit_by_keywords(subreddit_id: str,
                                  texts: List[str],
                                  nlp,
                                  sentiment_pipeline,
                                  tokenizer,
                                  categories: Dict[str, List[str]],
                                  min_mentions: int = 1) -> Dict[str, Any]:
    """Analyze texts for a subreddit by scanning sentences for manual keywords.

    For each keyword found, attributes the sentiment score to its parent category.
    Returns averaged results per category.
    """
    logger.info(f'Analyzing subreddit by keywords: {subreddit_id} ({len(texts)} submissions)')
    
    # Flatten categories to keywords and map back
    kw_map = {} # keyword -> category
    all_keywords = []
    for cat, kws in categories.items():
        for kw in kws:
            k = kw.lower().strip()
            if k:
                kw_map[k] = cat
                all_keywords.append(k)

    # prepare keyword regex patterns (word-boundary where appropriate)
    kw_patterns = []
    for k in all_keywords:
        # use word boundaries for alphanumeric keywords; allow phrases as simple substring
        if re.match(r"^[a-z0-9_]+$", k):
            pat = re.compile(r"\b" + re.escape(k) + r"\b")
        else:
            pat = re.compile(re.escape(k))
        kw_patterns.append((k, pat))

    category_sentiments = defaultdict(list) # category -> list of (score, snippet)
    # per-submission matches: list of dicts {submission_id, matched_keywords, submission_score, snippet}
    submission_matches = []
    rejected_submissions = []

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
        snippets = []
        
        for sent in doc.sents:
            s = sent.text.strip()
            if not s:
                continue
            low = s.lower()
            
            # Check for matches in this sentence
            sent_matches = []
            for k, pat in kw_patterns:
                if pat.search(low):
                    # Apply constraints (context check)
                    if check_constraints(low, k):
                        sent_matches.append(k)
            
            if sent_matches:
                # Question Detection: If it's a question, we might want to skip scoring or flag it.
                # For now, let's skip scoring questions to avoid skewing sentiment with uncertainty.
                if '?' in s:
                    continue

                # Calculate sentiment for the sentence once
                try:
                    max_len = getattr(tokenizer, 'model_max_length', 512)
                    text_piece = s[:max_len]
                    result = sentiment_pipeline(text_piece)
                    score = convert_sentiment_to_score(result)
                    
                    submission_scores.append(score)
                    snippets.append(s)
                    
                    # Attribute score to all matched categories
                    for k in sent_matches:
                        matched.add(k)
                        cat = kw_map[k]
                        category_sentiments[cat].append((score, s))
                        
                except Exception as e:
                    logger.debug(f' sentiment error: {e}')
                    continue

        # record per-submission match if any keywords matched
        if matched:
            # join unique snippets
            unique_snippets = list(set(snippets))
            snippet_text = " ... ".join(unique_snippets)
            submission_matches.append({
                'submission_id': sid, 
                'matched_keywords': sorted(matched), 
                'submission_score': (mean(submission_scores) if submission_scores else None),
                'snippet': snippet_text
            })
        else:
            rejected_submissions.append({
                'submission_id': sid,
                'content': content
            })

    topics_out = []
    for cat, items in category_sentiments.items():
        scores = [x[0] for x in items]
        
        # Sort by score to find min (lowest) and max (highest)
        sorted_items = sorted(items, key=lambda x: x[0])
        examples = []
        if sorted_items:
            # Add lowest score snippet
            low = sorted_items[0]
            examples.append({'snippet': low[1], 'score': low[0], 'type': 'lowest'})
            # Add highest score snippet if we have more than one item
            if len(sorted_items) > 1:
                high = sorted_items[-1]
                examples.append({'snippet': high[1], 'score': high[0], 'type': 'highest'})
        
        if len(scores) >= min_mentions:
            topics_out.append({'topic': cat, 'avg_score': mean(scores), 'mentions': len(scores), 'examples': examples})
        else:
            # include even if below min_mentions but mark None (keeps behavior consistent)
            topics_out.append({'topic': cat, 'avg_score': (mean(scores) if scores else None), 'mentions': len(scores), 'examples': examples})

    # filter out zero-mention keywords to reduce output size
    topics_out = [t for t in topics_out if t['mentions'] > 0]
    return {'subreddit_id': subreddit_id, 'topics': topics_out, 'submission_matches': submission_matches, 'rejected_submissions': rejected_submissions}


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
    # We want to pivot this: instead of one row per submission, we want one row per (submission + category)
    # But the current structure is per-submission.
    # Let's flatten it: Subreddit | Category | Score | Snippet | Submission_ID
    
    fieldnames = ['subreddit_id', 'category', 'score', 'snippet', 'submission_id']
    
    # We need to reconstruct the category mapping to look up which category a keyword belongs to
    # (This is a bit inefficient to rebuild, but safer than passing it around everywhere)
    kw_map = {}
    for cat, kws in TOPIC_CATEGORIES.items():
        for kw in kws:
            k = kw.lower().strip()
            if k:
                kw_map[k] = cat

    with open(out_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for r in results:
            sid = r.get('subreddit_id')
            for s in r.get('submission_matches', []):
                # s has 'matched_keywords' list. We need to group these by category.
                # A single submission might have matches for multiple categories.
                
                # Group snippets/scores by category for this specific submission
                # Note: The current 'submission_score' is an average of ALL keywords. 
                # Ideally we'd have per-category scores for the submission, but we only stored the aggregate.
                # For now, we will use the aggregate submission score for all categories found in it,
                # OR we can just list the category and the snippet.
                
                # Let's group the keywords found in this submission by category
                found_cats = defaultdict(list)
                for k in s.get('matched_keywords', []):
                    # Check if k is already a known category (from LLM) or a keyword (from Regex)
                    if k in TOPIC_CATEGORIES:
                        found_cats[k].append(k)
                    elif k in kw_map:
                        found_cats[kw_map[k]].append(k)
                
                # Write one row per category found in this submission
                for cat, kws in found_cats.items():
                    writer.writerow({
                        'subreddit_id': sid,
                        'category': cat,
                        'score': (f"{s.get('submission_score'):.3f}" if s.get('submission_score') is not None else ''),
                        'snippet': s.get('snippet', ''),
                        'submission_id': s.get('submission_id')
                    })


def write_rejected_submissions_csv(out_path: str, results: List[Dict[str, Any]]):
    fieldnames = ['subreddit_id', 'submission_id', 'content']
    with open(out_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in results:
            sid = r.get('subreddit_id')
            for rej in r.get('rejected_submissions', []):
                writer.writerow({
                    'subreddit_id': sid,
                    'submission_id': rej.get('submission_id'),
                    'content': rej.get('content')
                })


def write_samples_csv(out_path: str, results: List[Dict[str, Any]]):
    fieldnames = ['subreddit_id', 'topic', 'type', 'score', 'snippet']
    with open(out_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in results:
            sid = r.get('subreddit_id')
            for t in r.get('topics', []):
                for ex in t.get('examples', []):
                    writer.writerow({
                        'subreddit_id': sid,
                        'topic': t['topic'],
                        'type': ex.get('type', 'sample'),
                        'score': ex.get('score', ''),
                        'snippet': ex.get('snippet', '')
                    })


def main():
    parser = argparse.ArgumentParser(description='Topic + per-topic sentiment analysis grouped by subreddit')
    parser.add_argument('--subreddit', help='(optional) subreddit_id to limit to')
    parser.add_argument('--top-k', type=int, default=6, help='Top K topics to extract per subreddit')
    parser.add_argument('--min-mentions', type=int, default=1, help='Minimum mentions to report a topic')
    parser.add_argument('--mode', choices=['keywords', 'noun'], default='keywords', help='Analysis mode: use manual keywords or noun-chunk topics')
    parser.add_argument('--keywords-file', help='Optional newline-delimited file with extra keywords to include (one per line)')
    parser.add_argument('--out', help='Optional CSV output path')
    parser.add_argument('--submission-out', help='Optional CSV path to write per-submission matched keywords')
    parser.add_argument('--rejected-out', help='Optional CSV path to write rejected submissions')
    parser.add_argument('--samples-out', help='Optional CSV path to write highest/lowest sample posts')
    parser.add_argument('--limit', type=int, default=20000, help='Limit number of submissions fetched')
    parser.add_argument('--use-llm', action='store_true', help='Use Gemini LLM to verify and refine results (requires GEMINI_API_KEY)')
    args = parser.parse_args()

    supabase = load_supabase_client()
    if not supabase:
        logger.error('Could not initialize Supabase client; exiting')
        return

    # Check for API key if LLM requested
    gemini_key = os.getenv('GEMINI_API_KEY')
    if args.use_llm and not gemini_key:
        logger.error("Error: --use-llm requested but GEMINI_API_KEY not found in environment.")
        return

    import spacy
    from transformers import pipeline, AutoTokenizer

    logger.info('Loading spaCy model...')
    nlp = spacy.load('en_core_web_sm')

    logger.info('Loading sentiment model (this may take a while)...')
    model_name = 'nlptown/bert-base-multilingual-uncased-sentiment'
    sentiment_pipeline = pipeline('sentiment-analysis', model=model_name)
    tokenizer = AutoTokenizer.from_pretrained(model_name)

    # prepare categories if requested
    categories = TOPIC_CATEGORIES.copy()
    if args.mode == 'keywords' and args.keywords_file:
        extra_kws = load_keywords_from_file(args.keywords_file)
        if extra_kws:
            # Add extra keywords to a "Custom" category
            if 'Custom' not in categories:
                categories['Custom'] = []
            categories['Custom'].extend(extra_kws)

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
            res = analyze_subreddit_by_keywords(sid, texts, nlp, sentiment_pipeline, tokenizer, categories, min_mentions=args.min_mentions)
        else:
            res = analyze_subreddit(sid, texts, nlp, sentiment_pipeline, tokenizer, top_k=args.top_k, min_mentions=args.min_mentions)
        results.append(res)

    # --- LLM Verification Step ---
    if args.use_llm:
        logger.info("Starting LLM verification...")
        # Collect all snippets
        all_snippets = []
        for r in results:
            for m in r.get('submission_matches', []):
                if m.get('snippet'):
                    all_snippets.append(m['snippet'])
        
        # Remove duplicates
        all_snippets = list(set(all_snippets))
        logger.info(f"Verifying {len(all_snippets)} unique snippets with Gemini...")
        
        verified_data = verify_with_llm(all_snippets, gemini_key)
        results = apply_llm_verification(results, verified_data)
        logger.info("LLM verification complete.")

    for r in results:
        print('\n=== Subreddit:', r['subreddit_id'], '===')
        for t in r['topics']:
            if t['avg_score'] is not None:
                print(f"- {t['topic']}: avg={t['avg_score']:.2f} stars ({t['mentions']} mentions)")
                # Print sample snippets if available
                if t.get('examples'):
                    for ex_obj in t['examples']:
                        # ex_obj is now a dict {'snippet', 'score', 'type'}
                        label = ex_obj.get('type', 'sample').capitalize()
                        score = ex_obj.get('score', '?')
                        text = ex_obj.get('snippet', '')
                        
                        clean_ex = text.replace('\n', ' ')
                        if len(clean_ex) > 100: clean_ex = clean_ex[:100] + "..."
                        print(f"  {label} ({score}): \"{clean_ex}\"")
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

    if args.rejected_out:
        logger.info(f'Writing rejected submissions CSV to {args.rejected_out}')
        write_rejected_submissions_csv(args.rejected_out, results)

    if args.samples_out:
        logger.info(f'Writing samples CSV to {args.samples_out}')
        write_samples_csv(args.samples_out, results)


if __name__ == '__main__':
    main()
