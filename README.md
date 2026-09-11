# Indian Dance Search

## Files
- `dance_api.py` — Flask API serving the classical + folk/tribal dance data and search logic
- `searchEngin.py` — Gradio UI that calls the API and renders results
- `requirements.txt` — Python dependencies
- `.gitignore` — keeps the venv and cache files out of version control

## Setup
```
python -m venv .venv
.venv\Scripts\activate        # Windows
source .venv/bin/activate     # Mac/Linux

pip install -r requirements.txt
```

## Run
Just run the UI file — it auto-starts `dance_api.py` in the background if it isn't already running:
```
python searchEngin.py
```

Then open the local URL Gradio prints (usually http://127.0.0.1:7860).

To run the API on its own (e.g. to test endpoints directly with curl/Postman):
```
python dance_api.py
```
It serves on http://127.0.0.1:5000.