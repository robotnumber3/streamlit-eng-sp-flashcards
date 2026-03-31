# REV 30
# streamlit_eng_sp_flashcards.py

import streamlit as st
import random
import os
import sys
import json
import pandas as pd
import streamlit.components.v1 as components
from streamlit.runtime.scriptrunner import get_script_run_ctx

if get_script_run_ctx() is None:
    print("Run this app with: streamlit run streamlit_eng_sp_flashcards.py")
    sys.exit(1)

# ------------------------------------------------------------------------
# CONFIG
# ------------------------------------------------------------------------

st.set_page_config(page_title="Spanish Flashcards", page_icon="🌿", layout="wide")

CSV_FOLDER = os.path.join(os.path.dirname(__file__), "csv")
PREFS_FILE = os.path.expanduser("~/.flashcards_prefs.json")

csv_files = [f for f in os.listdir(CSV_FOLDER) if f.endswith(".csv")]
csv_files.sort(key=str.lower)


def csv_data_row_count(filename):
    file_path = os.path.join(CSV_FOLDER, filename)
    try:
        with open(file_path, encoding="utf-8", errors="ignore") as handle:
            return max(sum(1 for _ in handle) - 1, 0)
    except Exception:
        return 0


csv_row_counts = {filename: csv_data_row_count(filename) for filename in csv_files}


def display_deck_name(filename):
    base_name, extension = os.path.splitext(filename)
    if extension.lower() == ".csv":
        return f"{base_name} [{csv_row_counts.get(filename, 0)}]"
    return base_name

# ------------------------------------------------------------------------
# PREFS
# ------------------------------------------------------------------------

def load_prefs():
    try:
        with open(PREFS_FILE) as f:
            return json.load(f)
    except Exception:
        return {}

def save_prefs(prefs):
    try:
        with open(PREFS_FILE, "w") as f:
            json.dump(prefs, f)
    except Exception:
        pass


def current_prefs():
    return {
        "theme": st.session_state.theme,
        "direction_mode": st.session_state.direction_mode,
        "speech_speed": st.session_state.speech_speed,
    }

# ------------------------------------------------------------------------
# THEMES
# ------------------------------------------------------------------------

THEMES = {
    "light": {
        "bg":            "#f5f0e8",
        "fg":            "#1a1a1a",
        "card_bg":       "#1e1e1e",
        "card_fg":       "#f0ece4",
        "accent":        "#2e8b57",
        "accent_light":  "#c8f0d8",
        "info":          "#2f6fdf",
        "info_light":    "#d7e5ff",
        "warn":          "#b8860b",
        "warn_light":    "#fdf0c0",
        "danger":        "#a01818",
        "danger_light":  "#f8d8d8",
        "border":        "#c0b8a8",
        "divider":       "#c0b8a8",
        "muted":         "#5a5450",
        "btn_show_bg":   "#c8f0d8",
        "btn_show_fg":   "#1a6b38",
        "btn_show_bd":   "#2e8b57",
        "panel_label":   "#5a5450",
        "menu_bg":       "#ede8e0",
        "dropdown_bg":   "#ede8e0",
        "dropdown_fg":   "#1a1a1a",
        "dropdown_hover":"#d8d0c4",
    },
    "dark": {
        "bg":            "#0f1117",
        "fg":            "#e8e4dc",
        "card_bg":       "#1e2130",
        "card_fg":       "#e8e4dc",
        "accent":        "#3dba70",
        "accent_light":  "#1a3d2a",
        "info":          "#63a4ff",
        "info_light":    "#11294d",
        "warn":          "#f0b429",
        "warn_light":    "#3d2e00",
        "danger":        "#e05252",
        "danger_light":  "#3d1010",
        "border":        "#2a2d35",
        "divider":       "#2a2d35",
        "muted":         "#888480",
        "btn_show_bg":   "#1a3d2a",
        "btn_show_fg":   "#3dba70",
        "btn_show_bd":   "#3dba70",
        "panel_label":   "#666c7a",
        "menu_bg":       "#1a1d26",
        "dropdown_bg":   "#1a1d26",
        "dropdown_fg":   "#e8e4dc",
        "dropdown_hover":"#252836",
    },
    "aqua": {
        "bg":            "#0a1f1f",
        "fg":            "#d4f0ee",
        "card_bg":       "#0f3535",
        "card_fg":       "#d4f0ee",
        "accent":        "#1a9e92",
        "accent_light":  "#0d2e2e",
        "info":          "#4ea3ff",
        "info_light":    "#0d2742",
        "warn":          "#c48a0a",
        "warn_light":    "#2a1e00",
        "danger":        "#c04040",
        "danger_light":  "#2a0d0d",
        "border":        "#1a3d3d",
        "divider":       "#1a3d3d",
        "muted":         "#4a8e88",
        "btn_show_bg":   "#0d2e2e",
        "btn_show_fg":   "#1a9e92",
        "btn_show_bd":   "#1a9e92",
        "panel_label":   "#3a7a75",
        "menu_bg":       "#0d2a2a",
        "dropdown_bg":   "#0d2a2a",
        "dropdown_fg":   "#d4f0ee",
        "dropdown_hover":"#143535",
    },
}

# ------------------------------------------------------------------------
# SESSION STATE
# ------------------------------------------------------------------------

prefs = load_prefs()

defaults = {
    "theme":          prefs.get("theme", "dark"),
    "menu_open":      False,
    "direction_mode": prefs.get("direction_mode", "random"),
    "speech_speed":   prefs.get("speech_speed", 5),
    "selected_csv":   None,
    "cards":          [],
    "order":          [],
    "index":          0,
    "show_answer":    False,
    "direction":      ("EN_TO_ES" if prefs.get("direction_mode","random") == "en_to_es"
                       else ("ES_TO_EN" if prefs.get("direction_mode","random") == "es_to_en"
                       else random.choice(["EN_TO_ES", "ES_TO_EN"]))),
    "quit_requested": False,
    "final_exit":     False,
    "loaded_csv":     None,
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

t = THEMES[st.session_state.theme]

# ------------------------------------------------------------------------
# HIDE NATIVE SIDEBAR
# ------------------------------------------------------------------------

st.markdown("""
<style>
[data-testid="stSidebar"]        { display: none !important; }
[data-testid="collapsedControl"] { display: none !important; }
</style>
""", unsafe_allow_html=True)

# ------------------------------------------------------------------------
# GLOBAL CSS
# ------------------------------------------------------------------------

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Fraunces:ital,wght@0,300;0,400;0,700;1,300;1,400&family=DM+Sans:wght@300;400;500;600&display=swap');

html, body,
[data-testid="stAppViewContainer"],
[data-testid="stApp"],
[data-testid="stMain"],
[data-testid="stMainBlockContainer"] {{
    background-color: {t['bg']} !important;
    color: {t['fg']} !important;
    max-width: 100% !important;
}}
[data-testid="stHeader"] {{ background-color: {t['bg']} !important; }}
#MainMenu, footer, header {{ visibility: hidden; }}
html, body, p, div, span, label, [class*="st-"] {{
    font-family: 'DM Sans', sans-serif !important;
    color: {t['fg']};
}}
.block-container {{
    padding: 0 1rem 2rem 1rem !important;
    max-width: 600px !important;
    margin: 0 auto !important;
    position: relative !important;
}}
/* Reduce default Streamlit element gaps */
[data-testid="stVerticalBlock"] > * {{
    margin-bottom: 0 !important;
}}

/* Selectbox */
[data-testid="stSelectbox"] > div > div {{
    background-color: {t['bg']} !important;
    border-color: {t['border']} !important;
    color: {t['fg']} !important;
}}
[data-baseweb="popover"] ul, [data-baseweb="menu"] ul {{
    background-color: {t['dropdown_bg']} !important;
}}
[data-baseweb="popover"] li, [data-baseweb="menu"] li {{
    background-color: {t['dropdown_bg']} !important;
    color: {t['dropdown_fg']} !important;
}}
[data-baseweb="popover"] li:hover {{ background-color: {t['dropdown_hover']} !important; }}

/* Radio */
[data-testid="stRadio"] label {{ color: {t['fg']} !important; font-size: 0.9rem !important; }}
[data-testid="stRadio"] {{ margin-bottom: 0 !important; }}

/* Markdown */
[data-testid="stMarkdownContainer"] p,
[data-testid="stMarkdownContainer"] li {{
    color: {t['fg']} !important;
    font-family: 'DM Sans', sans-serif !important;
}}

/* ---- All buttons base ---- */
div[data-testid="stButton"] > button {{
    font-family: 'DM Sans', sans-serif !important;
    width: 100% !important;
    min-height: 3.0rem !important;
    font-size: 1.2rem !important;
    font-weight: 600 !important;
    border-radius: 0.75rem !important;
    border-width: 2px !important;
    transition: opacity 0.15s ease !important;
    cursor: pointer !important;
    background-color: {t['bg']} !important;
    color: {t['fg']} !important;
    border-color: {t['border']} !important;
}}
div[data-testid="stButton"] > button:hover {{ opacity: 0.82 !important; }}

/* ---- Hamburger ---- */
.st-key-hamburger_wrap {{
    min-width: 2.5rem !important;
}}
.st-key-hamburger_wrap div[data-testid="stButton"] {{
    display: flex !important;
    justify-content: flex-end !important;
}}
.st-key-hamburger_wrap div[data-testid="stButton"] > button {{
    background: transparent !important;
    border: none !important;
    color: {t['fg']} !important;
    font-size: 1.3rem !important;
    min-height: 1.8rem !important;
    width: auto !important;
    padding: 0 0.3rem !important;
    font-weight: 400 !important;
    border-width: 0px !important;
}}

/* ---- Show answer → ---- */
.st-key-showanswer_wrap div[data-testid="stButton"] > button {{
    background-color: {t['btn_show_bg']} !important;
    border-color: {t['btn_show_bd']} !important;
    color: {t['btn_show_fg']} !important;
    font-size: 1.5rem !important;
}}
/* ---- Correct ✓ ---- */
.st-key-correct_wrap div[data-testid="stButton"] > button {{
    background-color: {t['accent_light']} !important;
    border-color: {t['accent']} !important;
    color: {t['accent']} !important;
}}
/* ---- Repeat ? ---- */
.st-key-repeat_wrap div[data-testid="stButton"] > button {{
    background-color: {t['warn_light']} !important;
    border-color: {t['warn']} !important;
    color: {t['warn']} !important;
}}
/* ---- Quit before 🛑 ---- */
.st-key-quitbefore_wrap div[data-testid="stButton"] > button {{
    background-color: {t['danger_light']} !important;
    border-color: {t['danger']} !important;
    color: {t['danger']} !important;
}}
/* ---- Quit ---- */
.st-key-quitnow_wrap div[data-testid="stButton"] > button {{
    background-color: {t['danger_light']} !important;
    border-color: {t['danger']} !important;
    color: {t['danger']} !important;
}}
/* ---- New Session ---- */
.st-key-newsession_wrap div[data-testid="stButton"] > button {{
    background-color: {t['accent_light']} !important;
    border-color: {t['accent']} !important;
    color: {t['accent']} !important;
}}
/* ---- Mistakes Only ---- */
.st-key-mistakesonly_wrap div[data-testid="stButton"] > button {{
    background-color: {t['info_light']} !important;
    border-color: {t['info']} !important;
    color: {t['info']} !important;
}}
.st-key-speaker_wrap div[data-testid="stButton"] > button {{
    background-color: {t['info_light']} !important;
    border-color: {t['info']} !important;
    color: {t['info']} !important;
}}
.st-key-mistakesonly_wrap div[data-testid="stButton"] > button:disabled {{
    background-color: rgba(128, 128, 128, 0.14) !important;
    border-color: rgba(128, 128, 128, 0.32) !important;
    color: rgba(180, 180, 180, 0.55) !important;
    opacity: 1 !important;
    cursor: default !important;
}}
/* ---- Change Deck ---- */
.st-key-changedeck_wrap div[data-testid="stButton"] > button {{
    background-color: {t['bg']} !important;
    border-color: {t['border']} !important;
    color: {t['muted']} !important;
    font-size: 0.82rem !important;
    min-height: 2.2rem !important;
    font-weight: 500 !important;
}}

/* ---- Button pair row ---- */
.st-key-btn_row_wrap [data-testid="stHorizontalBlock"] {{
    display: flex !important;
    flex-direction: row !important;
    flex-wrap: nowrap !important;
    gap: 0.45rem !important;
    justify-content: center !important;
    width: 100% !important;
}}
.st-key-btn_row_wrap [data-testid="stColumn"] {{
    flex: 1 1 0 !important;
    width: calc(50% - 0.225rem) !important;
    min-width: 0 !important;
    max-width: none !important;
}}
.st-key-btn_row_wrap [data-testid="stColumn"] > div {{
    width: 100% !important;
}}
.st-key-btn_row_wrap div[data-testid="stButton"] {{
    width: 100% !important;
}}
.st-key-btn_row_wrap div[data-testid="stButton"] > div {{
    width: 100% !important;
}}
.st-key-btn_row_wrap div[data-testid="stButton"] > button {{
    width: 100% !important;
    min-height: 3.2rem !important;
    font-size: 1.3rem !important;
}}

/* ---- Small centered icon button row ---- */
.st-key-icon_btn_row_wrap [data-testid="stHorizontalBlock"] {{
    display: flex !important;
    flex-direction: row !important;
    flex-wrap: nowrap !important;
    justify-content: center !important;
    gap: 0.8rem !important;
    width: fit-content !important;
    margin: 0 auto !important;
}}
.st-key-icon_btn_row_wrap [data-testid="stColumn"] {{
    flex: 0 0 auto !important;
    width: auto !important;
    min-width: 0 !important;
    max-width: none !important;
}}
.st-key-icon_btn_row_wrap [data-testid="stColumn"] > div,
.st-key-icon_btn_row_wrap div[data-testid="stButton"],
.st-key-icon_btn_row_wrap div[data-testid="stButton"] > div {{
    width: auto !important;
}}
.st-key-icon_btn_row_wrap div[data-testid="stButton"] > button {{
    width: 5.4rem !important;
    min-height: 3.2rem !important;
    font-size: 1.3rem !important;
}}

/* ---- Revealed answer action row ---- */
.st-key-answer_action_row_wrap [data-testid="stHorizontalBlock"] {{
    display: flex !important;
    flex-direction: row !important;
    flex-wrap: nowrap !important;
    justify-content: center !important;
    align-items: center !important;
    gap: 0.35rem !important;
    width: fit-content !important;
    margin: 0 auto !important;
}}
.st-key-answer_action_row_wrap [data-testid="stColumn"] {{
    display: contents !important;
}}
.st-key-answer_action_row_wrap [data-testid="stColumn"] > div,
.st-key-answer_action_row_wrap div[data-testid="stButton"],
.st-key-answer_action_row_wrap div[data-testid="stButton"] > div {{
    width: auto !important;
}}
.st-key-answer_action_row_wrap .st-key-speaker_wrap,
.st-key-answer_action_row_wrap .st-key-speaker_wrap > div,
.st-key-answer_action_row_wrap .st-key-speaker_wrap [data-testid="stElementContainer"] {{
    width: auto !important;
    min-width: 0 !important;
}}
.st-key-answer_action_row_wrap .st-key-speaker_wrap iframe {{
    width: 4.3rem !important;
    min-width: 4.3rem !important;
    max-width: 4.3rem !important;
    display: block !important;
    margin: 0.12rem 0 0 0 !important;
}}
.st-key-answer_action_row_wrap div[data-testid="stButton"] > button {{
    width: 4.3rem !important;
    min-height: 3.2rem !important;
    font-size: 1.3rem !important;
}}

/* ---- Centered summary button row ---- */
.st-key-summary_btn_row_wrap [data-testid="stHorizontalBlock"] {{
    display: flex !important;
    flex-direction: row !important;
    flex-wrap: nowrap !important;
    justify-content: center !important;
    gap: 0.25rem !important;
    width: fit-content !important;
    margin: 0 auto !important;
}}
.st-key-summary_btn_row_wrap [data-testid="stColumn"] {{
    flex: 0 0 auto !important;
    width: auto !important;
    min-width: 0 !important;
    max-width: none !important;
}}
.st-key-summary_btn_row_wrap [data-testid="stColumn"] > div,
.st-key-summary_btn_row_wrap div[data-testid="stButton"],
.st-key-summary_btn_row_wrap div[data-testid="stButton"] > div {{
    width: auto !important;
}}
.st-key-summary_btn_row_wrap div[data-testid="stButton"] > button {{
    min-width: 0 !important;
    min-height: 2.8rem !important;
    font-size: 0.92rem !important;
    padding-left: 0.55rem !important;
    padding-right: 0.55rem !important;
}}
.st-key-quitnow_wrap div[data-testid="stButton"] > button {{
    width: 4.0rem !important;
}}
.st-key-newsession_wrap div[data-testid="stButton"] > button {{
    width: 6.8rem !important;
}}
.st-key-mistakesonly_wrap div[data-testid="stButton"] > button {{
    width: 5.8rem !important;
}}

/* ---- Header row ---- */
.st-key-header_row_wrap [data-testid="stHorizontalBlock"] {{
    display: flex !important;
    flex-direction: row !important;
    flex-wrap: nowrap !important;
    align-items: center !important;
    gap: 0.5rem !important;
    width: 100% !important;
}}
.st-key-header_row_wrap [data-testid="stColumn"] {{
    min-width: 0 !important;
}}
.st-key-header_row_wrap [data-testid="stColumn"]:first-child {{
    flex: 1 1 auto !important;
    width: auto !important;
}}
.st-key-header_row_wrap [data-testid="stColumn"]:last-child {{
    flex: 0 0 auto !important;
    width: auto !important;
    max-width: none !important;
}}

/* ---- Title row ---- */
.title-row {{
    display: flex;
    align-items: center;
    gap: 0.5rem;
    flex-wrap: nowrap;
    padding: 0.5rem 0 0.3rem 0;
    width: 100%;
    min-width: 0;
}}
.title-row-spacer {{
    flex: 1;
}}
.title-main {{
    font-family: 'Fraunces', serif;
    font-size: 1.4rem;
    font-weight: 600;
    color: {t['fg']};
    line-height: 1;
    white-space: nowrap;
}}
.title-sub {{
    font-size: 0.8rem;
    font-weight: 400;
    color: {t['muted']};
    white-space: nowrap;
}}

/* ---- Menu dropdown ---- */
.menu-dropdown {{
    background-color: {t['menu_bg']};
    border: 1px solid {t['border']};
    border-radius: 0.75rem;
    padding: 0.9rem 1.1rem 0.7rem 1.1rem;
    margin-bottom: 0.7rem;
}}
.menu-section-label {{
    font-size: 0.68rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: {t['panel_label']};
    margin-bottom: 0.4rem;
}}

/* ---- Deck strip ---- */
.deck-strip {{
    display: flex;
    align-items: center;
    gap: 0.6rem;
    margin-bottom: 0.4rem;
    flex-wrap: wrap;
}}
.deck-strip-label {{
    font-size: 0.65rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: {t['muted']};
}}
.deck-strip-name {{
    font-family: 'Fraunces', serif;
    font-size: 0.9rem;
    font-weight: 600;
    color: {t['fg']};
}}

/* ---- Stats card ---- */
.stats-card {{
    background-color: {t['card_bg']};
    border-radius: 0.8rem;
    padding: 0.5rem 0.9rem;
    margin-bottom: 0.6rem;
}}
.stats-card .prog-wrap {{
    background: rgba(128,128,128,0.2);
    border-radius: 99px; height: 4px;
    margin-bottom: 0.35rem; overflow: hidden;
}}
.stats-card .prog-fill {{
    height: 4px; border-radius: 99px;
    background: {t['accent']}; transition: width 0.4s ease;
}}
.stats-card .prog-label {{
    font-size: 0.78rem; opacity: 0.62;
    margin-bottom: 0.4rem; color: {t['card_fg']};
}}
.stats-card .stat-row {{ display: flex; gap: 1.1rem; flex-wrap: wrap; }}
.stats-card .stat-item {{ display: flex; flex-direction: column; }}
.stats-card .stat-label {{
    font-size: 0.70rem; font-weight: 500;
    text-transform: uppercase; letter-spacing: 0.07em;
    opacity: 0.55; color: {t['card_fg']};
}}
.stats-card .stat-value {{
    font-size: 1.10rem; font-weight: 600; color: {t['card_fg']};
}}

/* ---- Flashcard boxes ---- */
.fc-block {{
    border: 1px solid {t['border']};
    border-radius: 1rem;
    padding: 0.6rem 0.9rem;
    margin-bottom: 0.5rem;
    background: {t['bg']};
    cursor: pointer;
    user-select: none;
    -webkit-user-select: none;
    transition: border-color 0.15s ease;
}}
.fc-block:active {{ border-color: {t['accent']}; }}
.fc-block-empty {{ opacity: 0.35; }}
.fc-section-label {{
    font-size: 0.60rem; font-weight: 500;
    text-transform: uppercase; letter-spacing: 0.08em;
    color: {t['muted']}; margin-bottom: 0.2rem;
}}
.fc-word {{
    font-family: 'Fraunces', serif;
    font-size: 1.2rem; font-weight: 700;
    line-height: 1.2; color: {t['fg']};
}}
.fc-answer {{
    font-family: 'Fraunces', serif;
    font-size: 1.1rem; font-weight: 400; font-style: italic;
    line-height: 1.2; color: {t['fg']};
}}
.fc-word-placeholder {{
    font-size: 1.1rem; line-height: 1.2; min-height: 1.4rem;
}}
.fc-note, .fc-answer-note {{
    font-size: 1.0rem; font-weight: 400;
    color: {t['muted']}; margin-top: 0.2rem; line-height: 1.3;
}}

/* ---- Summary ---- */
.summary-title {{
    font-family: 'Fraunces', serif;
    font-size: 1.5rem; font-weight: 700;
    color: {t['fg']}; margin-bottom: 0.8rem;
}}
.summary-grid {{
    display: grid; grid-template-columns: 1fr 1fr;
    gap: 0.5rem 1rem;
    background: {t['card_bg']};
    border-radius: 0.9rem;
    padding: 0.9rem 1.1rem; margin-bottom: 1rem;
    font-size: 0.9rem;
}}
.summary-grid .sg-label {{ font-weight: 400; opacity: 0.65; color: {t['card_fg']}; }}
.summary-grid .sg-value {{ font-weight: 600; text-align: right; color: {t['card_fg']}; }}

/* ---- Big title (deck picker) ---- */
.title-block {{ padding: 1.2rem 0 0.8rem 0; }}
.title-big {{
    font-family: 'Fraunces', serif;
    font-size: 2.0rem; font-weight: 700;
    color: {t['fg']}; line-height: 1.1;
}}
.title-big-sub {{
    font-size: 0.85rem; font-weight: 300;
    color: {t['muted']}; margin-top: 0.3rem;
    letter-spacing: 0.06em; text-transform: uppercase;
}}
.soft-divider {{
    border: none; border-top: 1px solid {t['border']}; margin: 0.6rem 0;
}}

/* ---- Responsive deck picker ---- */
.st-key-mobile_deck_picker_wrap {{
    display: none;
}}
@media (max-width: 767px) {{
    .st-key-desktop_deck_picker_wrap {{
        display: none !important;
    }}
    .st-key-mobile_deck_picker_wrap {{
        display: block !important;
    }}
    .st-key-mobile_deck_picker_wrap [data-testid="stButton"] {{
        margin-bottom: 0.05rem !important;
    }}
    .st-key-mobile_deck_picker_wrap [data-testid="stButton"] > button {{
        display: flex !important;
        align-items: center !important;
        min-height: 1.75rem !important;
        padding: 0.05rem 0.45rem !important;
        font-size: 0.82rem !important;
        font-weight: 500 !important;
        line-height: 1.0 !important;
        justify-content: flex-start !important;
        text-align: left !important;
        border-radius: 0 !important;
        border: none !important;
        box-shadow: none !important;
    }}
    .st-key-mobile_deck_picker_wrap [data-testid="stButton"] > button > div,
    .st-key-mobile_deck_picker_wrap [data-testid="stButton"] > button p {{
        width: 100% !important;
        margin: 0 !important;
        text-align: left !important;
        justify-content: flex-start !important;
    }}
    .st-key-mobile_deck_picker_wrap [data-testid="stVerticalBlock"] > * {{
        margin-bottom: 0 !important;
    }}
}}
</style>
""", unsafe_allow_html=True)

# ------------------------------------------------------------------------
# VIEWPORT META
# ------------------------------------------------------------------------

components.html("""
<script>
(function() {
    var doc = window.parent.document;
    var head = doc.head;
    var existing = head.querySelector('meta[name="viewport"]');
    if (existing) {
        existing.content = 'width=device-width, initial-scale=1, maximum-scale=1';
    } else {
        var meta = doc.createElement('meta');
        meta.name = 'viewport';
        meta.content = 'width=device-width, initial-scale=1, maximum-scale=1';
        head.appendChild(meta);
    }
})();
</script>
""", height=0)

# ------------------------------------------------------------------------
# CARD LOGIC
# ------------------------------------------------------------------------

def current_card_index():
    return st.session_state.order[st.session_state.index]

def reveal_answer():
    st.session_state.show_answer = True

def mark_correct():
    card = st.session_state.cards[current_card_index()]
    card["repeat_score"] = max(card["repeat_score"] - 1, 0)
    advance_card()

def mark_repeat():
    card = st.session_state.cards[current_card_index()]
    card["repeat_score"] = 2
    card["error_flag"] = 1
    advance_card()

def schedule_repeat(card_index, repeat_score):
    next_position = st.session_state.index + 1
    remaining = len(st.session_state.order) - next_position
    if remaining <= 0:
        st.session_state.order.append(card_index)
        return
    if repeat_score >= 2:
        midpoint_offset = max(1, remaining // 2)
        window_size = max(1, remaining // 6)
        lower = max(next_position, next_position + midpoint_offset - window_size)
        upper = min(len(st.session_state.order), next_position + midpoint_offset + window_size)
        insert_at = random.randint(lower, upper)
    else:
        insert_at = random.randint(next_position, len(st.session_state.order))
    st.session_state.order.insert(min(insert_at, len(st.session_state.order)), card_index)

def advance_card():
    idx  = current_card_index()
    card = st.session_state.cards[idx]
    card["shown"] = True
    if card["repeat_score"] > 0:
        schedule_repeat(idx, card["repeat_score"])
    st.session_state.index      += 1
    st.session_state.show_answer = False
    mode = st.session_state.direction_mode
    if mode == "en_to_es":
        st.session_state.direction = "EN_TO_ES"
    elif mode == "es_to_en":
        st.session_state.direction = "ES_TO_EN"
    else:
        st.session_state.direction = random.choice(["EN_TO_ES", "ES_TO_EN"])

# ------------------------------------------------------------------------
# UI HELPERS
# ------------------------------------------------------------------------

def format_word(text, word_class, note_class):
    import re
    m = re.search(r'(\[.*?\])', text)
    if m:
        main = text[:m.start()].strip()
        note = m.group(1)
        return ('<div class="' + word_class + '">' + main + '</div>'
                '<div class="' + note_class + '">' + note + '</div>')
    return '<div class="' + word_class + '">' + text + '</div>'


def strip_spoken_text(text):
    import re

    spoken_text = re.sub(r'\[.*?\]|\(.*?\)', '', text)
    spoken_text = re.sub(r'\s+', ' ', spoken_text)
    return spoken_text.strip()


def render_flashcard(prompt, solution, show_answer):
    q_inner = format_word(prompt, 'fc-word', 'fc-note')
    q_html  = '<div class="fc-block"><div class="fc-section-label">Translate</div>' + q_inner + '</div>'
    st.markdown(q_html, unsafe_allow_html=True)
    if show_answer:
        a_inner = format_word(solution, 'fc-answer', 'fc-answer-note')
        a_html  = '<div class="fc-block"><div class="fc-section-label">Answer</div>' + a_inner + '</div>'
    else:
        a_html  = '<div class="fc-block fc-block-empty"><div class="fc-section-label">Answer</div><div class="fc-word-placeholder">&nbsp;</div></div>'
    st.markdown(a_html, unsafe_allow_html=True)


def inject_tap_reveal(show_answer):
    show_str = "true" if show_answer else "false"
    components.html("""
    <script>
    (function() {
        var showAnswer = """ + show_str + """;
        function clickBtn(label) {
            var btns = window.parent.document.querySelectorAll('button');
            for (var i = 0; i < btns.length; i++) {
                if (btns[i].innerText.trim() === label) {
                    btns[i].dispatchEvent(new MouseEvent('click', {bubbles:true}));
                    return;
                }
            }
        }
        function attach() {
            var doc = window.parent.document;
            var cards = doc.querySelectorAll('.fc-block');
            if (!cards.length) return false;
            if (doc._fcHandler) doc.body.removeEventListener('click', doc._fcHandler);
            doc._fcHandler = function(e) {
                if (!e.target.closest('.fc-block')) return;
                if (!showAnswer) clickBtn('\u2192');
            };
            doc.body.addEventListener('click', doc._fcHandler);
            return true;
        }
        var n = 0;
        function tryAttach() {
            if (attach()) return;
            if (++n < 20) setTimeout(tryAttach, 150);
        }
        tryAttach();
    })();
    </script>
    """, height=0)


def speech_rate_value():
    speech_rate_map = {
        1: 0.20,
        2: 0.40,
        3: 0.60,
        4: 0.80,
        5: 1.00,
    }
    return speech_rate_map.get(st.session_state.speech_speed, 1.00)


def render_speaker_button(text):
    speech_text = strip_spoken_text(text)
    speech_rate = speech_rate_value()
    components.html(
        f"""
        <style>
        body {{
            margin: 0;
            background: transparent;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 3.2rem;
        }}
        #speak-btn {{
            width: 4.3rem;
            min-height: 3.2rem;
            font-size: 1.3rem;
            font-weight: 600;
            border-radius: 0.75rem;
            border: 2px solid {t['info']};
            background-color: {t['info_light']};
            color: {t['info']};
            cursor: pointer;
            font-family: 'DM Sans', sans-serif;
            margin-top: 0.12rem;
        }}
        </style>
        <button id="speak-btn" type="button">🔊</button>
        <script>
        (function() {{
            var speechText = {json.dumps(speech_text)};
            var speechRate = {speech_rate};
            var synth = window.speechSynthesis;
            var button = document.getElementById('speak-btn');

            if (!button || !synth || !speechText) return;

            function pickVoice(voices) {{
                return voices.find(function(voice) {{ return voice.lang === 'es-ES'; }})
                    || voices.find(function(voice) {{ return voice.lang === 'es-MX'; }})
                    || voices.find(function(voice) {{ return voice.lang && voice.lang.toLowerCase().startsWith('es'); }})
                    || null;
            }}

            function speakNow() {{
                var utterance = new SpeechSynthesisUtterance(speechText);
                var voices = synth.getVoices ? synth.getVoices() : [];
                var voice = pickVoice(voices);

                utterance.lang = voice ? voice.lang : 'es-ES';
                utterance.rate = speechRate;
                if (voice) utterance.voice = voice;

                synth.cancel();
                synth.speak(utterance);
            }}

            function speakFromTap(event) {{
                if (event) event.preventDefault();
                if (synth.getVoices && synth.getVoices().length) {{
                    speakNow();
                    return;
                }}

                var handled = false;
                function handleVoicesChanged() {{
                    if (handled) return;
                    handled = true;
                    speakNow();
                }}

                if (typeof synth.addEventListener === 'function') {{
                    synth.addEventListener('voiceschanged', handleVoicesChanged, {{ once: true }});
                }} else {{
                    synth.onvoiceschanged = handleVoicesChanged;
                }}

                setTimeout(handleVoicesChanged, 250);
            }}

            button.addEventListener('click', speakFromTap);
            button.addEventListener('touchend', speakFromTap);
        }})();
        </script>
        """,
        height=60,
    )


def stats_card_html(shown, total, correct, repeat):
    pct        = int(shown / total * 100) if total > 0 else 0
    accuracy   = int(correct / shown * 100) if shown > 0 else 0
    missed_pct = int(repeat  / shown * 100) if shown > 0 else 0
    remaining  = total - shown
    st.markdown(f"""
    <div class="stats-card">
      <div class="prog-wrap"><div class="prog-fill" style="width:{pct}%"></div></div>
      <div class="prog-label">{pct}% complete &nbsp;&middot;&nbsp; {remaining} remaining</div>
      <div class="stat-row">
        <div class="stat-item"><div class="stat-label">Correct</div><div class="stat-value">{correct}</div></div>
        <div class="stat-item"><div class="stat-label">Repeat</div><div class="stat-value">{repeat}</div></div>
        <div class="stat-item"><div class="stat-label">Accuracy</div><div class="stat-value">{accuracy}%</div></div>
        <div class="stat-item"><div class="stat-label">Missed</div><div class="stat-value">{missed_pct}%</div></div>
      </div>
    </div>
    """, unsafe_allow_html=True)


def render_header():
    menu_icon = "✕" if st.session_state.menu_open else "☰"
    with st.container(key="header_row_wrap"):
        title_col, ham_col = st.columns([1, 0.14], gap="small")
        with title_col:
            st.markdown(
                "<div class='title-row'>"
                "<span class='title-main'>Spanish Flashcards</span>"
                "</div>",
                unsafe_allow_html=True,
            )
        with ham_col:
            with st.container(key="hamburger_wrap"):
                if st.button(menu_icon, key="hamburger_btn"):
                    st.session_state.menu_open = not st.session_state.menu_open
                    st.rerun()
    st.markdown(
        f"<hr style='border:none;border-top:1px solid {t['border']};margin:0 0 0.7rem 0;'>",
        unsafe_allow_html=True,
    )


def render_menu():
    if not st.session_state.menu_open:
        return
    st.markdown('<div class="menu-dropdown">', unsafe_allow_html=True)
    st.markdown('<div class="menu-section-label">Theme</div>', unsafe_allow_html=True)
    new_theme = st.radio("Theme", options=["light", "dark", "aqua"],
                         index=["light","dark","aqua"].index(st.session_state.theme),
                         label_visibility="collapsed", key="theme_radio")
    if new_theme != st.session_state.theme:
        st.session_state.theme     = new_theme
        st.session_state.menu_open = False
        save_prefs(current_prefs())
        st.rerun()
    st.markdown('<div class="menu-section-label" style="margin-top:0.9rem;">Direction</div>',
                unsafe_allow_html=True)
    dir_options = ["Random 50/50", "EN → ES only", "ES → EN only"]
    dir_keys    = ["random", "en_to_es", "es_to_en"]
    cur_idx     = dir_keys.index(st.session_state.direction_mode)
    new_dir     = st.radio("Direction", options=dir_options, index=cur_idx,
                           label_visibility="collapsed", key="dir_radio")
    if dir_options.index(new_dir) != cur_idx:
        st.session_state.direction_mode = dir_keys[dir_options.index(new_dir)]
        st.session_state.menu_open      = False
        save_prefs(current_prefs())
        st.rerun()
    st.markdown('<div class="menu-section-label" style="margin-top:0.9rem;">Speech Speed</div>',
                unsafe_allow_html=True)
    speed_options = [1, 2, 3, 4, 5]
    speed_labels = {
        1: "Very Slow",
        2: "Slow",
        3: "Medium",
        4: "Fast",
        5: "Very Fast",
    }
    new_speed = st.radio(
        "Speech Speed",
        options=speed_options,
        index=speed_options.index(st.session_state.speech_speed),
        format_func=lambda value: speed_labels[value],
        horizontal=True,
        label_visibility="collapsed",
        key="speech_speed_radio",
    )
    if new_speed != st.session_state.speech_speed:
        st.session_state.speech_speed = new_speed
        st.session_state.menu_open = False
        save_prefs(current_prefs())
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)


def render_deck_strip():
    if not st.session_state.selected_csv:
        return
    deck_name = display_deck_name(st.session_state.selected_csv)
    st.markdown(
        '<div class="deck-strip">'
        '<span class="deck-strip-label">Deck</span>'
        '<span class="deck-strip-name">' + deck_name + '</span>'
        '</div>', unsafe_allow_html=True)


def render_buttons(show_answer, spanish_audio_text):
    if not show_answer:
        with st.container(key="icon_btn_row_wrap"):
            col1, col2 = st.columns(2)
            with col1:
                with st.container(key="showanswer_wrap"):
                    st.button("→", key="showanswer_btn", on_click=reveal_answer)
            with col2:
                with st.container(key="quitbefore_wrap"):
                    if st.button("🛑", key="quitbefore_btn"):
                        st.session_state.quit_requested = True
                        st.rerun()
        return

    with st.container(key="answer_action_row_wrap"):
        col1, col2, col3 = st.columns(3, gap="small")
        with col1:
            with st.container(key="correct_wrap"):
                st.button("✓", key="correct_btn", on_click=mark_correct)
        with col2:
            with st.container(key="repeat_wrap"):
                st.button("?", key="repeat_btn", on_click=mark_repeat)
        with col3:
            with st.container(key="speaker_wrap"):
                render_speaker_button(spanish_audio_text)


def restart_mistakes_only():
    mistake_cards = [
        {
            "word": card["word"],
            "answer": card["answer"],
            "shown": False,
            "repeat_score": 1,
            "error_flag": 0,
        }
        for card in st.session_state.cards
        if card["error_flag"] == 1
    ]
    if not mistake_cards:
        return
    st.session_state.cards = mistake_cards
    st.session_state.order = list(range(len(mistake_cards)))
    random.shuffle(st.session_state.order)
    st.session_state.index = 0
    st.session_state.show_answer = False
    st.session_state.quit_requested = False
    st.session_state.final_exit = False
    st.session_state.menu_open = False
    st.rerun()

# ========================================================================
# FINAL EXIT
# ========================================================================

if st.session_state.final_exit:
    render_header()
    render_menu()
    st.markdown(
        "<div class='title-block'>"
        "<div class='title-big'>Buen trabajo!</div>"
        "<div class='title-big-sub'>Keep practicing every day</div>"
        "</div>",
        unsafe_allow_html=True,
    )
    st.stop()

# ========================================================================
# DECK PICKER
# ========================================================================

if st.session_state.selected_csv is None:
    render_header()
    render_menu()
    st.markdown("<hr class='soft-divider'>", unsafe_allow_html=True)
    deck_options = ["-- Choose a deck --", *csv_files]
    with st.container(key="mobile_deck_picker_wrap"):
        st.markdown("<div style='font-size: 0.95rem; color: " + t['fg'] + ";'>Available decks:</div>", unsafe_allow_html=True)
        deck_container = st.container(height=250)
        with deck_container:
            for csv_file in csv_files:
                deck_display = display_deck_name(csv_file)
                if st.button(deck_display, key=f"deck_btn_{csv_file}", use_container_width=True):
                    st.session_state.selected_csv   = csv_file
                    st.session_state.cards          = []
                    st.session_state.order          = []
                    st.session_state.index          = 0
                    st.session_state.show_answer    = False
                    st.session_state.quit_requested = False
                    st.session_state.final_exit     = False
                    st.session_state.loaded_csv     = None
                    st.rerun()

    with st.container(key="desktop_deck_picker_wrap"):
        selected = st.selectbox(
            "Available decks:",
            deck_options,
            index=0,
            format_func=lambda value: value if value == "-- Choose a deck --" else display_deck_name(value),
        )
        if selected != deck_options[0]:
            st.session_state.selected_csv   = selected
            st.session_state.cards          = []
            st.session_state.order          = []
            st.session_state.index          = 0
            st.session_state.show_answer    = False
            st.session_state.quit_requested = False
            st.session_state.final_exit     = False
            st.session_state.loaded_csv     = None
            st.rerun()
    st.stop()

# ========================================================================
# LOAD CSV
# ========================================================================

if st.session_state.loaded_csv != st.session_state.selected_csv or not st.session_state.cards:
    # Auto-detect delimiter (some files use ; others use ,)
    csv_path = os.path.join(CSV_FOLDER, st.session_state.selected_csv)
    with open(csv_path, 'r', encoding='utf-8') as _f:
        _first = _f.readline()
    _sep = ';' if ';' in _first else ','
    df = pd.read_csv(csv_path, sep=_sep)
    # Normalize column names (strip whitespace)
    df.columns = [c.strip() for c in df.columns]
    st.session_state.cards = [
        {"word": row["word"], "answer": row["answer"],
         "shown": False, "repeat_score": 1, "error_flag": 0}
        for _, row in df.iterrows()
    ]
    st.session_state.order = list(range(len(st.session_state.cards)))
    random.shuffle(st.session_state.order)
    st.session_state.index = 0
    st.session_state.loaded_csv = st.session_state.selected_csv

# ========================================================================
# STATS
# ========================================================================

total_cards   = len(st.session_state.cards)
shown_cards   = sum(1 for c in st.session_state.cards if c["shown"])
correct_count = sum(1 for c in st.session_state.cards if c["repeat_score"] == 0 and c["shown"])
repeat_count  = sum(1 for c in st.session_state.cards if c["error_flag"] == 1)

# ========================================================================
# QUIT / SUMMARY
# ========================================================================

if st.session_state.quit_requested:
    render_header()
    render_menu()
    st.markdown("<div class='summary-title'>Session Summary</div>", unsafe_allow_html=True)

    perfect_first_try = sum(1 for c in st.session_state.cards
                            if c["shown"] and c["repeat_score"] == 0 and c["error_flag"] == 0)
    avg_rs = (sum(c["repeat_score"] for c in st.session_state.cards if c["shown"]) / shown_cards
              ) if shown_cards > 0 else 0
    accuracy   = int(correct_count / shown_cards * 100) if shown_cards > 0 else 0
    missed_pct = int(repeat_count  / shown_cards * 100) if shown_cards > 0 else 0

    st.markdown(f"""
    <div class="summary-grid">
      <div class="sg-label">Cards Shown</div>      <div class="sg-value">{shown_cards}</div>
      <div class="sg-label">Correct</div>           <div class="sg-value">{correct_count}</div>
      <div class="sg-label">Repeat Needed</div>     <div class="sg-value">{repeat_count}</div>
      <div class="sg-label">Perfect First Try</div> <div class="sg-value">{perfect_first_try}</div>
      <div class="sg-label">Avg Repeat Score</div>  <div class="sg-value">{avg_rs:.2f}</div>
      <div class="sg-label">Accuracy</div>          <div class="sg-value">{accuracy}%</div>
      <div class="sg-label">Missed</div>            <div class="sg-value">{missed_pct}%</div>
    </div>
    """, unsafe_allow_html=True)

    mistakes_only_disabled = repeat_count == 0

    with st.container(key="summary_btn_row_wrap"):
        c1, c2, c3 = st.columns(3)
        with c1:
            with st.container(key="mistakesonly_wrap"):
                st.button(
                    "Mistakes",
                    key="mistakesonly_btn",
                    on_click=restart_mistakes_only,
                    disabled=mistakes_only_disabled,
                )
        with c2:
            with st.container(key="newsession_wrap"):
                if st.button("New", key="newsession_btn"):
                    for k in ("selected_csv", "loaded_csv"):
                        st.session_state[k] = None
                    for k in ("cards", "order"):
                        st.session_state[k] = []
                    st.session_state.index          = 0
                    st.session_state.show_answer    = False
                    st.session_state.quit_requested = False
                    st.session_state.final_exit     = False
                    st.rerun()
        with c3:
            with st.container(key="quitnow_wrap"):
                if st.button("Quit", key="quitnow_btn"):
                    st.session_state.final_exit = True
                    st.rerun()
    st.stop()

# ========================================================================
# END OF DECK
# ========================================================================

if st.session_state.cards and st.session_state.order:
    if st.session_state.index >= len(st.session_state.order):
        st.session_state.quit_requested = True
        st.rerun()

if not st.session_state.order:
    st.stop()

# ========================================================================
# CURRENT CARD
# ========================================================================

card = st.session_state.cards[current_card_index()]
if st.session_state.direction == "EN_TO_ES":
    prompt, solution = card["word"], card["answer"]
else:
    prompt, solution = card["answer"], card["word"]

spanish_text = solution if st.session_state.direction == "EN_TO_ES" else prompt

# ========================================================================
# MAIN LAYOUT
# ========================================================================

render_header()
render_menu()
render_deck_strip()
stats_card_html(shown_cards, total_cards, correct_count, repeat_count)
render_flashcard(prompt, solution, st.session_state.show_answer)
inject_tap_reveal(st.session_state.show_answer)
render_buttons(st.session_state.show_answer, spanish_text)