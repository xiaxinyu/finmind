# FinMind Architecture

## Components
- Data Dictionaries: `account/static/*.json`
- Classification: `account/analyzer/ConsumptionAnalyzer.py`
- Business Analysis: `account/analyzer/BusinessAnalyzer.py`
- DB Helpers: `account/db/SQLiteHelper.py`
- API Layer: `engine/views.py`, `engine/urls.py`
- Django Project: `finmind_site/*`

## Data Flow
1. FinSight ingests and cleans bank exports (CSV/SQLite).
2. FinMind reads cleaned rows and runs:
   - Disbursement channel resolution
   - Type-of-use resolution
   - Consumption classification
3. FinMind aggregates and produces explainable insights.
4. Frontend or scripts consume endpoints to render reports.

## Sequence (Text)
- Input rows arrive with description and amount fields.
- `BusinessAnalyzer.calculate` iterates rows:
  - Appends channel, use-type, consumption-type, keyword columns.
  - Delegates consumption classification to `ConsumptionAnalyzer`.
- `engine/views.py` endpoints:
  - `/classify`: single description + amount → consumption type
  - `/analyze`: batch rows → enriched rows
  - `/insights`: batch rows → totals and ratios by type

## Design Notes
- Rule-first, model-light: fast, deterministic, explainable.
- All data local: zero network calls; privacy by design.
- Pluggable NLP: optional enhancements when performance permits.
- Compatible with FinSight: acts as the “cognitive core”.

## Extensibility
- Add new dictionaries in `account/static` and extend analyzers.
- Insert NLP step after rule match for borderline cases.
- Extend `/insights` to compute monthly deltas, impulse scores, payday effects.

