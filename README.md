# FinMind — The Intelligence Layer for FinSight

English | [简体中文](README.zh-CN.md)

Where Transactions Become Understanding.

FinMind is the specialized offline analysis engine for `https://github.com/xiaxinyu/finsight`, built to transform raw transaction data into deep, actionable insights while preserving privacy.

Unlike generic budgeting apps, FinMind combines human-readable rules, lightweight NLP, and behavioral heuristics to not only categorize spending accurately but also explain the drivers behind it.

Runs entirely offline and integrates natively with FinSight as its cognitive core.

## ✨ Core Capabilities
- Hybrid Classification Engine  
  - Rule-based matching (regex, contains, amount thresholds)  
  - Lightweight NLP (fastText / BERT-mini)  
  - Conflict resolution & priority weighting  
  - User feedback loop → auto-generate new rules
- Behavioral Profiling  
  - Tag transactions: essential, impulse, investment, luxury  
  - Detect anomalies (e.g., sudden increase in dining out)  
  - Estimate "avoidable expense" ratio
- Explainable Insights  
  - “You spent ¥1,200 on impulse buys this month — 30% above average.”  
  - “Essential spending is stable, but discretionary spiked after payday.”  
  - All insights are traceable back to specific transactions.
- Seamless FinSight Integration  
  - Reads/writes directly from FinSight’s local database (CSV/SQLite)  
  - Exposes REST-like API for FinSight frontend  
  - Can run as a background service or on-demand module

## 🛠️ Tech Stack
- Language: Python
- Core: Pandas, scikit-learn, fastText
- NLP: jieba (Chinese tokenization), HuggingFace Transformers (optional)
- Integration: Local file I/O or SQLite; optional Django
- Privacy: Zero network calls. No telemetry.

## 🌐 Relationship with FinSight
- Role  
  - FinSight: Data Platform  
  - FinMind: Intelligence Engine
- Focus  
  - FinSight: Storage, UI, Reporting  
  - FinMind: Classification, Insight, AI
- Data Flow  
  - FinSight ingests bank exports  
  - FinMind consumes FinSight’s clean data
- User Interaction  
  - FinSight: Dashboard, manual edits  
  - FinMind: Auto-suggestions, explanations

Think of it like:
- FinSight = Eyes + Hands
- FinMind = Brain

## 🧩 Project Structure
```
finmind/
├── account/                     # Rules & static dictionaries
│   ├── analyzer/                # Classification & business analysis
│   ├── cleaner/                 # Data cleaners
│   ├── db/                      # SQLite helpers
│   ├── helper/                  # Utilities
│   └── static/                  # Dictionaries & DDL
├── engine/                      # Django application layer
│   ├── views.py                 # API endpoints
│   └── urls.py
├── finmind_site/                # Django project
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── doc/                         # English documentation
│   ├── index.md
│   ├── api.md
│   └── architecture.md
└── manage.py
```

## 🔌 Django API
- `POST /api/classify`  
  - body: `{"description": "...", "money": "100.00"}`  
  - return: consumption type and matched keyword
- `POST /api/analyze`  
  - body: `{"lines": [[...], ...]}`  
  - return: batch analysis with channel, use-type, consumption, keyword
- `POST /api/insights`  
  - body: `{"lines": [[...], ...]}`  
  - return: totals and ratios by consumption type

## 🚀 Quick Start
```
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

## 🧭 Slogan
- Primary: Where Transactions Become Understanding.  
  Your transactions become understanding of yourself.
- Alternatives: The Intelligence Layer for Your Finances; Beyond Categorization — Into Insight; Your Money, Understood.

## 📚 Documentation
- English docs in `doc/`:
  - `doc/index.md` overview
  - `doc/api.md` HTTP API
  - `doc/architecture.md` architecture
- Chinese README: [README.zh-CN.md](README.zh-CN.md)

## 📜 License
GNU Affero General Public License v3.0 (AGPL-3.0)
