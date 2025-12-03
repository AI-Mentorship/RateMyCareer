
let cachedData = null;
let loadPromise = null;

async function loadData() {
    if (cachedData) return cachedData;
    if (loadPromise) return loadPromise;

    loadPromise = fetch('/supabase_dump.json')
        .then(res => {
            if (!res.ok) throw new Error('Failed to load local data');
            return res.json();
        })
        .then(data => {
            cachedData = data;
            return data;
        })
        .catch(err => {
            console.error("Error loading supabase_dump.json:", err);
            throw err;
        });
    
    return loadPromise;
}

// Helper to normalize career names for comparison
function normalize(name) {
    return name ? name.toLowerCase().trim() : '';
}

// Helper to find canonical career name from input
// The frontend often passes "Teachers" but DB might have "Teacher" or vice versa.
// We use the 'subreddits' table to map subreddit_id or display_name to career_name if needed,
// or just match against aggregate career_name.
function findCanonicalCareer(data, inputName) {
    if (!inputName) return null;
    const nInput = normalize(inputName);

    // Hardcoded mapping for prototype since subreddits table might be empty in dump
    const manualMap = {
        "police": "police",
        "hr": "humanresources",
        "human resources": "humanresources",
        "humanresources": "humanresources",
        "teacher": "Teachers",
        "teachers": "Teachers",
        "nurse": "nursing",
        "nursing": "nursing",
        "physical therapy": "physicaltherapy",
        "physicaltherapy": "physicaltherapy",
        "lawyer": "Lawyertalk",
        "lawyertalk": "Lawyertalk",
        "data scientist": "DataScienceJobs",
        "datasciencejobs": "DataScienceJobs",
        "data analyst": "dataanalytics",
        "dataanalytics": "dataanalytics",
        "ux designer": "UXResearch",
        "uxresearch": "UXResearch"
    };

    if (manualMap[nInput]) return manualMap[nInput];

    // 1. Check subreddits table for direct match on career_name or display_name
    if (data.subreddits && data.subreddits.length) {
        const sub = data.subreddits.find(s => 
            normalize(s.career_name) === nInput || 
            normalize(s.display_name) === nInput ||
            normalize(s.subreddit_id) === nInput
        );
        if (sub && sub.career_name) return sub.career_name;
    }

    // 2. Check aggregate table for existing career_name
    if (data.aggregate) {
        const agg = data.aggregate.find(a => normalize(a.career_name) === nInput);
        if (agg) return agg.career_name;
    }

    // 3. Try simple variations (singular/plural)
    if (data.aggregate) {
        if (nInput.endsWith('s')) {
            const singular = nInput.slice(0, -1);
            const aggS = data.aggregate.find(a => normalize(a.career_name) === singular);
            if (aggS) return aggS.career_name;
        } else {
            const plural = nInput + 's';
            const aggP = data.aggregate.find(a => normalize(a.career_name) === plural);
            if (aggP) return aggP.career_name;
        }
    }

    return inputName; // Fallback
}

// Mock quotes for prototype if DB is empty
const MOCK_QUOTES = {
    "dataanalytics": [
        "The work is intellectually stimulating but the deadlines can be brutal.",
        "I love finding insights in data, but cleaning it takes 80% of the time.",
        "Great pay and benefits, but work-life balance depends heavily on the company.",
        "Transitioning into this field was hard, but worth it for the career growth.",
        "SQL is your best friend. Python is your cool cousin."
    ],
    "Teachers": [
        "Seeing a student have that 'aha' moment makes it all worth it.",
        "The administration is out of touch, but my colleagues are amazing.",
        "Grading takes up all my weekends. I wish I had more time for lesson planning.",
        "The emotional toll is high, but the impact you have is undeniable.",
        "Summer break is necessary for sanity, not a luxury."
    ],
    "nursing": [
        "12-hour shifts are exhausting, but saving lives is incredibly rewarding.",
        "Patient ratios are unsafe in many hospitals right now.",
        "The camaraderie among nurses is the only thing getting me through.",
        "Compassion fatigue is real. Take care of yourself first.",
        "I love the flexibility of the schedule, but the work is physically demanding."
    ],
    // Add generic fallbacks for others
};

export const localData = {
    async getRankings(limit = 100) {
        const data = await loadData();
        const rows = data.aggregate || [];
        
        // Group by career_name, keep latest record_date
        const latestByCareer = {};
        rows.forEach(row => {
            const cname = row.career_name;
            if (!cname) return;
            
            if (!latestByCareer[cname] || new Date(row.record_date) > new Date(latestByCareer[cname].record_date)) {
                latestByCareer[cname] = row;
            }
        });

        // Convert to array and sort by vibe_score desc
        let sorted = Object.values(latestByCareer).sort((a, b) => {
            const va = a.vibe_score !== null ? Number(a.vibe_score) : -Infinity;
            const vb = b.vibe_score !== null ? Number(b.vibe_score) : -Infinity;
            return vb - va;
        });

        // Map subreddit_id to canonical career_name if possible (mimic API)
        // The API does a join with subreddits table.
        const subMap = {};
        (data.subreddits || []).forEach(s => {
            if (s.subreddit_id) subMap[s.subreddit_id] = s.career_name;
        });

        sorted = sorted.map(r => {
            if (r.subreddit_id && subMap[r.subreddit_id]) {
                return { ...r, career_name: subMap[r.subreddit_id] };
            }
            return r;
        });

        return { data: sorted.slice(0, limit) };
    },

    async getScores(careerName) {
        const data = await loadData();
        const canonical = findCanonicalCareer(data, careerName);
        
        const rows = (data.aggregate || [])
            .filter(r => normalize(r.career_name) === normalize(canonical))
            .sort((a, b) => new Date(b.record_date) - new Date(a.record_date));

        // Return structure matching API: { career: name, rows: [...] } or just latest row if not history?
        // The API returns { career: ..., rows: [...] } for history=true, or just { data: ... } ?
        // Actually API `scores_for_career` returns { career: ..., rows: [latest] } if history=false.
        
        return { career: canonical, rows: rows.slice(0, 100) }; // Return recent rows
    },

    async getTimeline(careerName) {
        const data = await loadData();
        const canonical = findCanonicalCareer(data, careerName);
        
        const points = [];

        // 1. Forecast
        (data.forecast || []).forEach(row => {
            if (normalize(row.career_name) === normalize(canonical)) {
                // Convert year/week to date
                // Simple approximation or use ISO week logic if needed. 
                // JS doesn't have built-in ISO week to date.
                // Let's try to match the python logic: datetime.fromisocalendar(y, w, 1)
                // We'll use a helper or just approximate since this is a prototype.
                // Actually, let's try to be accurate.
                const date = getDateFromWeek(row.year, row.week_number);
                points.push({
                    date: date.toISOString().split('T')[0],
                    source: 'forecast',
                    value: row.sentiment_average,
                    raw: row
                });
            }
        });

        // 2. Aggregate
        (data.aggregate || []).forEach(row => {
            if (normalize(row.career_name) === normalize(canonical)) {
                const val = row.forecasted_sentiment_avg !== null ? row.forecasted_sentiment_avg : row.avg_sentiment;
                points.push({
                    date: row.record_date,
                    source: 'aggregate',
                    value: val,
                    raw: row
                });
            }
        });

        // 3. Merge
        const merged = {};
        points.forEach(p => {
            if (merged[p.date]) {
                if (merged[p.date].source === 'aggregate') return; // Keep aggregate
                if (p.source === 'aggregate') merged[p.date] = p; // Overwrite with aggregate
            } else {
                merged[p.date] = p;
            }
        });

        const timeline = Object.values(merged).sort((a, b) => new Date(a.date) - new Date(b.date));
        return { career: canonical, timeline };
    },

    async getCareerSummaries(careerName) {
        const data = await loadData();
        const canonical = findCanonicalCareer(data, careerName);
        
        const rows = (data.career_summaries || [])
            .filter(r => normalize(r.career_name) === normalize(canonical))
            .sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
            
        return { career: canonical, rows };
    },

    async getQuotes(careerName, limit = 10, random = false) {
        const data = await loadData();
        const canonical = findCanonicalCareer(data, careerName);
        
        let rows = (data.quotes || [])
            .filter(r => normalize(r.career_name) === normalize(canonical));
            
        if (rows.length === 0 && MOCK_QUOTES[canonical]) {
             rows = MOCK_QUOTES[canonical].map(q => ({ quote_body: q, career_name: canonical }));
        }

        if (random) {
            // Shuffle
            rows = rows.sort(() => 0.5 - Math.random());
        }
        
        return { career: canonical, rows: rows.slice(0, limit) };
    }
};

function getDateFromWeek(year, week) {
    const simple = new Date(year, 0, 1 + (week - 1) * 7);
    const dayOfWeek = simple.getDay();
    const ISOweekStart = simple;
    if (dayOfWeek <= 4)
        ISOweekStart.setDate(simple.getDate() - simple.getDay() + 1);
    else
        ISOweekStart.setDate(simple.getDate() + 8 - simple.getDay());
    return ISOweekStart;
}
