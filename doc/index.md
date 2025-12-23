# FinMind — The Intelligence Layer for FinSight

Where Transactions Become Understanding.

FinMind is the specialized offline analysis engine designed to transform raw transactions into deep, actionable insights. It integrates natively with the FinSight data platform while keeping everything private and local.

## Vision
Move beyond bookkeeping into financial self-awareness. FinMind explains not just "how much you spent" but "why you spent it".

## Core Capabilities
- Hybrid Classification Engine
  - Rule matching (regex, contains, amount thresholds)
  - Lightweight NLP (fastText / BERT-mini) for semantics
  - Conflict resolution with priorities
  - User feedback loop → auto-learn new rules
- Behavioral Profiling
  - Tag transactions: essential, impulse, investment, luxury
  - Detect anomalies (e.g., sudden spike in dining)
  - Estimate avoidable expense ratio
- Explainable Insights
  - “Impulse spending ¥1,200 this month — 30% above your average”
  - “Essential spending is stable, discretionary spikes post-payday”
  - Every insight is traceable to specific transactions
- Seamless Integration
  - Read/write local CSV/SQLite from FinSight
  - REST-style API for frontends
  - Run as background service or on-demand module

## Tech Stack
- Language: Python
- Core: Pandas, scikit-learn, fastText
- NLP: jieba, HuggingFace Transformers (optional)
- Integration: Local file I/O or SQLite; optional Django
- Privacy: Zero network calls. No telemetry.

## Relationship with FinSight
- Role
  - FinSight: Data Platform
  - FinMind: Intelligence Engine
- Focus
  - FinSight: Storage, UI, Reporting
  - FinMind: Classification, Insight, AI
- Data Flow
  - FinSight ingests and cleans bank exports
  - FinMind consumes cleaned data for intelligence
- Metaphor
  - FinSight = Eyes + Hands
  - FinMind = Brain

## Project Structure
```
finmind/
├── account/                     # Rules, dictionaries, cleaners, DB helpers
│   ├── analyzer/                # Classification and business analysis
│   ├── cleaner/
│   ├── db/
│   ├── helper/
│   └── static/
├── engine/                      # Django application (API layer)
│   ├── views.py
│   └── urls.py
├── finmind_site/                # Django project
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── doc/                         # Documentation (this folder)
│   ├── index.md                 # Overview
│   ├── api.md                   # HTTP API
│   └── architecture.md          # System architecture
├── manage.py
├── README.md
└── requirements.txt
```

## Quick Start
```
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

## Privacy
- No cloud usage. All data stays on your machine.
- No hidden telemetry. FinMind processes locally via files or SQLite.

## License
Apache-2.0. See `README.md`.

