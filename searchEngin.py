"""
Indian Dance Search — Gradio front-end
========================================
This UI no longer holds the dance data itself — it calls the
Flask API in dance_api.py over HTTP and renders whatever comes back.

Run (two terminals):
    Terminal 1:  python dance_api.py            # starts API on :5000
    Terminal 2:  python dance_search_app.py      # starts UI on :7860

Or just run this file directly — it will try to start the API
automatically in the background if it isn't already running
(see AUTO_START_API below).
"""

import os

os.environ["GRADIO_ANALYTICS_ENABLED"] = "False"  # skip the startup phone-home call

import subprocess
import sys
import time

import requests
import gradio as gr

API_BASE = "http://127.0.0.1:5000"
AUTO_START_API = True  # set False if you're running dance_api.py yourself


# ---------------------------------------------------------------------------
# 0. (OPTIONAL) auto-start the API so `python dance_search_app.py` just works
# ---------------------------------------------------------------------------
def ensure_api_running():
    try:
        requests.get(f"{API_BASE}/api/health", timeout=1)
        print("[searchEngin] dance_api.py already running.")
        return  # already running
    except requests.exceptions.RequestException:
        pass

    if not AUTO_START_API:
        print("[searchEngin] AUTO_START_API is False and no API was found running.")
        return

    # Build an ABSOLUTE path to dance_api.py, next to this file, so this
    # works no matter what directory Python was launched from.
    script_dir = os.path.dirname(os.path.abspath(__file__))
    api_path = os.path.join(script_dir, "dance_api.py")

    if not os.path.exists(api_path):
        print(f"[searchEngin] ERROR: couldn't find dance_api.py at {api_path}")
        print("[searchEngin] Make sure dance_api.py is in the same folder as this file.")
        return

    print(f"[searchEngin] Starting API: {api_path}")
    subprocess.Popen([sys.executable, api_path])  # don't hide stdout/stderr — let errors show

    for _ in range(30):  # wait up to ~6s for it to come up
        try:
            requests.get(f"{API_BASE}/api/health", timeout=0.5)
            print("[searchEngin] API is up.")
            return
        except requests.exceptions.RequestException:
            time.sleep(0.2)

    print("[searchEngin] WARNING: API did not respond after 6s. Check the API window/output above for errors.")


# ---------------------------------------------------------------------------
# 1. API CLIENT
# ---------------------------------------------------------------------------
def api_search(query: str):
    try:
        resp = requests.get(f"{API_BASE}/api/search", params={"q": query}, timeout=5)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.RequestException as e:
        return {"type": "error", "message": str(e)}


# ---------------------------------------------------------------------------
# 2. RENDERING (pure presentation — all data/search logic lives in the API)
# ---------------------------------------------------------------------------
def render(result: dict) -> str:
    box = "border:1px solid #e5e5e5;border-radius:10px;padding:16px 20px;margin-bottom:10px;background:#fff;"

    if result["type"] == "empty":
        return "<div style='padding:2rem;text-align:center;color:#888;'>Type a dance name or a state name to search.</div>"

    if result["type"] == "error":
        return f"""<div style='{box}'>
            <b style='color:#000;'>Couldn't reach the dance API</b> at {API_BASE}.<br>
            Make sure <code>dance_api.py</code> is running.<br>
            <span style='color:#000;font-size:0.85rem;'>{result['message']}</span>
        </div>"""

    if result["type"] == "none":
        return f"<div style='{box}'><span style='color:#000;'>No match found for <b style='color:#000;'>{result['query']}</b>. Try a dance name (e.g. 'Bhangra') or a state name (e.g. 'Punjab').</span></div>"

    if result["type"] == "suggestions":
        items = "".join(f"<li style='color:#000;'>{d}</li>" for d in result["dances"][:10])
        states = "".join(f"<li style='color:#000;'>{s}</li>" for s in result["states"][:10])
        html = f"<div style='{box}'><b style='color:#000;'>No exact match — did you mean:</b>"
        if items:
            html += f"<div style='margin-top:8px;color:#000;'>Dances:</div><ul>{items}</ul>"
        if states:
            html += f"<div style='margin-top:8px;color:#000;'>States:</div><ul>{states}</ul>"
        html += "</div>"
        return html

    if result["type"] == "classical_list":
        items = "".join(
            f"<li style='color:#000;'><b style='color:#000;'>{d['dance']}</b> "
            f"<span style='color:#000;'>({d['state']})</span></li>"
            for d in result["dances"]
        )
        return f"""
        <div style="{box}">
            <div style="font-size:0.8rem;color:#8a5a00;background:#fff3cd;display:inline-block;
                        padding:2px 8px;border-radius:6px;margin-bottom:8px;">ALL 8 CLASSICAL DANCES</div>
            <ul>{items}</ul>
        </div>
        """

    if result["type"] == "folk_list":
        items = "".join(
            f"<li style='color:#000;'><b style='color:#000;'>{d['dance']}</b> "
            f"<span style='color:#000;'>({d['state']})</span> "
            f"<span style='color:#666;font-size:0.8rem;'>[{d.get('category', '')}]</span></li>"
            for d in result["dances"]
        )
        label = result.get("label", "Folk / Tribal")
        return f"""
        <div style="{box}">
            <div style="font-size:0.8rem;color:#0a5;background:#e6f7ee;display:inline-block;
                        padding:2px 8px;border-radius:6px;margin-bottom:8px;">A SAMPLE OF {label.upper()} DANCES</div>
            <ul>{items}</ul>
        </div>
        """

    if result["type"] == "dance":
        if result["category"] == "Classical":
            state = result["states"][0]["state"]
            return f"""
            <div style="{box}">
                <div style="font-size:0.8rem;color:#8a5a00;background:#fff3cd;display:inline-block;
                            padding:2px 8px;border-radius:6px;margin-bottom:8px;">CLASSICAL DANCE</div>
                <h3 style="margin:4px 0;color:#000;">{result['dance']}</h3>
                <div style="color:#000;">Belongs to: <b style="color:#000;">{state}</b></div>
            </div>
            """
        else:
            rows = "".join(
                f"<li style='color:#000;'><b style='color:#000;'>{s['state']}</b> <span style='color:#000;'>({s['region']})</span></li>"
                for s in result["states"]
            )
            return f"""
            <div style="{box}">
                <div style="font-size:0.8rem;color:#0a5;background:#e6f7ee;display:inline-block;
                            padding:2px 8px;border-radius:6px;margin-bottom:8px;">FOLK / TRIBAL DANCE</div>
                <h3 style="margin:4px 0;color:#000;">{result['dance']}</h3>
                <div style="color:#000;">Found in:</div>
                <ul>{rows}</ul>
            </div>
            """

    if result["type"] == "state":
        html = f"<div style='{box}'><h3 style='margin:4px 0 12px 0;color:#000;'>{result['state']}</h3>"
        if result["classical"]:
            classical_items = "".join(f"<li style='color:#000;'>{d}</li>" for d in result["classical"])
            html += f"""
            <div style="font-size:0.8rem;color:#8a5a00;background:#fff3cd;display:inline-block;
                        padding:2px 8px;border-radius:6px;margin-bottom:6px;">CLASSICAL DANCE</div>
            <ul style="margin-top:0;">{classical_items}</ul>
            """
        else:
            html += "<div style='color:#000;margin-bottom:10px;'>No classical dance associated with this state.</div>"

        if result["folk"]:
            folk_items = "".join(
                f"<li style='color:#000;'><span style='color:#000;'>{r['dance']}</span> <span style='color:#000;'>({r['region']})</span></li>"
                for r in result["folk"]
            )
            html += f"""
            <div style="font-size:0.8rem;color:#0a5;background:#e6f7ee;display:inline-block;
                        padding:2px 8px;border-radius:6px;margin:10px 0 6px 0;">FOLK / TRIBAL DANCES</div>
            <ul style="margin-top:0;">{folk_items}</ul>
            """
        html += "</div>"
        return html

    return "<div>Something went wrong.</div>"


def run_search(query):
    return render(api_search(query))


# ---------------------------------------------------------------------------
# 3. UI
# ---------------------------------------------------------------------------
HIDE_FOOTER_CSS = """
footer {display: none !important;}
"""

with gr.Blocks(title="Indian Dance Search", theme=gr.themes.Soft(), css=HIDE_FOOTER_CSS) as demo:
    gr.Markdown(
        f"""
        # 💃 Indian Classical & Folk Dance Search
        Search by **dance name** to see which state it's from,
        or search by **state name** to see its classical dance (if any)
        followed by its folk/tribal dances.

        <span style='font-size:0.8rem;color:#999;'>Data served from API at {API_BASE}</span>
        """
    )

    with gr.Row():
        query_box = gr.Textbox(
            label="",
            placeholder="Try 'Bharatanatyam', 'Bhangra', or 'Kerala'...",
            scale=6,
            autofocus=True,
        )
        search_btn = gr.Button("Search", variant="primary", scale=1)

    results_html = gr.HTML(render({"type": "empty"}))

    search_btn.click(fn=run_search, inputs=query_box, outputs=results_html)
    query_box.submit(fn=run_search, inputs=query_box, outputs=results_html)

if __name__ == "__main__":
    ensure_api_running()
    demo.launch(show_api=False)