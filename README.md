# BharatStandards AI — SIH26108 Complete Functional Prototype

## What is functional
- Search procurement requirements and rank applicable standards.
- Upload PDF, DOCX or TXT tenders and extract text.
- Explainable relevance scoring with keyword/phrase/synonym expansion.
- Compliance gap detector and heuristic coverage score.
- Standard details, requirements, certification signals and related-standard links.
- Relevance graph view.
- Editable tender specification generator.
- Download generated specification and Markdown analysis report.
- Hindi/Hinglish starter normalization for common procurement terms.
- Runs locally without an API key.

## Run on Windows
Double-click `run_windows.bat`.

Or:
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run app.py
```

## Demo queries
- 100W LED street light, IP66, surge protection
- 33kV HT XLPE underground armoured cable
- 540Wp Mono PERC solar PV module
- Single Phase Smart Electricity Meter IS 16444
- 10 kVA double conversion UPS with VRLA battery
- Stainless steel pipes for water supply
- Fe500 TMT reinforcement bars for RCC

## Architecture
Input -> PDF/DOCX/TXT extraction -> normalization -> explainable retrieval -> standard details -> gap detector -> relationship graph -> specification editor -> report export.

## Important
`data/standards.json` is a **prototype demonstration index**, not a complete or authoritative BIS catalogue. Verify current BIS standards, amendments, QCOs and certification routes against authoritative sources before real procurement.

## Production/SIH upgrade path
Replace the local index with a licensed/authoritative BIS corpus; add embeddings/hybrid vector search, source-clause citations, version history, official QCO connectors, audit logs, multilingual Indic NLP and retrieval evaluation.
