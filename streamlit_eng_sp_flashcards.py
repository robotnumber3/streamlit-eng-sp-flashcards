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

st.set_page_config(
    page_title="Spanish Flashcards",
    page_icon="🌿",
    layout="wide",
)

CSV_FOLDER = os.path.join(os.path.dirname(__file__), "csv")
PREFS_FILE = os.path.expanduser("~/.flashcards_prefs.json")

csv_files = [f for f in os.listdir(CSV_FOLDER) if f.endswith(".csv")]
csv_files.sort(key=str.lower)

# ------------------------------------------------------------------------
# PREFS
# ------------------------------------------------------------------------

def load_prefs():
    try:
        with open(PREFS_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return {}

def save_prefs(prefs):
    try:
        with open(PREFS_FILE, "w") as f:
            json.dump(prefs, f)
    except Exception:
        pass

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
    "selected_csv":   None,
    "cards":          [],
    "order":          [],
    "index":          0,
    "show_answer":    False,
    "direction":      ("EN_TO_ES" if prefs.get("direction_mode","random") == "en_to_es" else ("ES_TO_EN" if prefs.get("direction_mode","random") == "es_to_en" else random.choice(["EN_TO_ES", "ES_TO_EN"]))),
    "quit_requested": False,
    "final_exit":     False,
    "loaded_csv":     None,
    "direction_mode": prefs.get("direction_mode", "random"),
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

/* ---- Mobile layout (phones) ---- */
@media (max-width: 768px) {{
    .block-container {{
        padding: 0 0.6rem 1rem 0.6rem !important;
    }}
    .title-bar {{
        padding: 0.6rem 0 0.5rem 0;
        margin-bottom: 0.7rem;
    }}
    .title-bar-main {{
        font-size: 1.1rem;
    }}
    .title-bar-sub {{
        font-size: 0.65rem;
    }}
    .stats-card {{
        padding: 0.55rem 0.8rem;
        margin-bottom: 0.7rem;
        border-radius: 0.7rem;
    }}
    .stats-card .prog-label {{
        font-size: 0.62rem;
        margin-bottom: 0.3rem;
    }}
    .stats-card .stat-label {{
        font-size: 0.58rem;
    }}
    .stats-card .stat-value {{
        font-size: 0.88rem;
    }}
    .stats-card .stat-row {{
        gap: 0.9rem;
    }}
    .fc-block {{
        padding: 0.75rem 0.9rem 0.9rem 0.9rem;
        margin-bottom: 0.7rem;
        border-radius: 0.8rem;
    }}
    .fc-section-label, .fc-answer-label {{
        font-size: 0.58rem;
        margin-bottom: 0.15rem;
    }}
    .fc-word {{
        font-size: 1.75rem;
    }}
    .fc-answer {{
        font-size: 1.55rem;
    }}
    .fc-note, .fc-answer-note {{
        font-size: 0.78rem;
        margin-top: 0.2rem;
    }}
    .fc-word-placeholder {{
        font-size: 1.55rem;
        min-height: 2.0rem;
    }}
    /* Buttons */
    div[data-testid="stButton"] > button {{
        min-height: 2.4rem !important;
        font-size: 1.1rem !important;
        border-radius: 0.6rem !important;
    }}
    .st-key-showanswer_wrap div[data-testid="stButton"] > button {{
        font-size: 1.4rem !important;
    }}
    .st-key-quitnow_wrap div[data-testid="stButton"] > button,
    .st-key-newsession_wrap div[data-testid="stButton"] > button {{
        font-size: 1.0rem !important;
    }}
    .right-panel-inner {{
        padding-left: 0.7rem;
        padding-top: 0.5rem;
    }}
    .hamburger-btn {{
        font-size: 1.1rem !important;
    }}
}}
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
    padding: 0 1.5rem 2rem 1.5rem !important;
    max-width: 100% !important;
}}

/* ---- Selectbox ---- */
[data-testid="stSelectbox"] > div > div {{
    background-color: {t['bg']} !important;
    border-color: {t['border']} !important;
    color: {t['fg']} !important;
}}
/* Dropdown list portal — force theme colors */
[data-baseweb="popover"] ul,
[data-baseweb="menu"] ul,
[data-baseweb="select"] ul {{
    background-color: {t['dropdown_bg']} !important;
}}
[data-baseweb="popover"] li,
[data-baseweb="menu"] li,
[data-baseweb="select"] li {{
    background-color: {t['dropdown_bg']} !important;
    color: {t['dropdown_fg']} !important;
}}
[data-baseweb="popover"] li:hover,
[data-baseweb="menu"] li:hover {{
    background-color: {t['dropdown_hover']} !important;
}}

/* ---- Radio ---- */
[data-testid="stRadio"] label {{
    color: {t['fg']} !important;
    font-size: 0.88rem !important;
}}
[data-testid="stRadio"] {{ margin-bottom: 0 !important; }}

/* ---- Markdown ---- */
[data-testid="stMarkdownContainer"] p,
[data-testid="stMarkdownContainer"] li {{
    color: {t['fg']} !important;
    font-family: 'DM Sans', sans-serif !important;
}}

/* ---- All buttons base ---- */
div[data-testid="stButton"] > button {{
    font-family: 'DM Sans', sans-serif !important;
    width: 100% !important;
    min-height: 3.4rem !important;
    font-size: 1.5rem !important;
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

/* Hamburger ☰ */
.st-key-hamburger_wrap div[data-testid="stButton"] > button {{
    background-color: transparent !important;
    border-color: transparent !important;
    color: {t['muted']} !important;
    font-size: 1.4rem !important;
    min-height: 2.2rem !important;
    width: auto !important;
    padding: 0 0.4rem !important;
    font-weight: 400 !important;
}}
.st-key-hamburger_wrap div[data-testid="stButton"] > button:hover {{
    color: {t['fg']} !important;
    opacity: 1 !important;
}}

/* Show answer → */
.st-key-showanswer_wrap div[data-testid="stButton"] > button {{
    background-color: {t['btn_show_bg']} !important;
    border-color: {t['btn_show_bd']} !important;
    color: {t['btn_show_fg']} !important;
    font-size: 2.0rem !important;
}}
/* Correct ✓ */
.st-key-correct_wrap div[data-testid="stButton"] > button {{
    background-color: {t['accent_light']} !important;
    border-color: {t['accent']} !important;
    color: {t['accent']} !important;
}}
/* Repeat ? */
.st-key-repeat_wrap div[data-testid="stButton"] > button {{
    background-color: {t['warn_light']} !important;
    border-color: {t['warn']} !important;
    color: {t['warn']} !important;
}}
/* Quit before 🛑 */
.st-key-quitbefore_wrap div[data-testid="stButton"] > button {{
    background-color: {t['danger_light']} !important;
    border-color: {t['danger']} !important;
    color: {t['danger']} !important;
}}
/* Quit */
.st-key-quitnow_wrap div[data-testid="stButton"] > button {{
    background-color: {t['danger_light']} !important;
    border-color: {t['danger']} !important;
    color: {t['danger']} !important;
    font-size: 1.4rem !important;
}}
/* New Session */
.st-key-newsession_wrap div[data-testid="stButton"] > button {{
    background-color: {t['accent_light']} !important;
    border-color: {t['accent']} !important;
    color: {t['accent']} !important;
    font-size: 1.4rem !important;
}}
/* Change Deck */
.st-key-changedeck_wrap div[data-testid="stButton"] > button {{
    background-color: {t['bg']} !important;
    border-color: {t['border']} !important;
    color: {t['muted']} !important;
    font-size: 0.82rem !important;
    min-height: 2.2rem !important;
    font-weight: 500 !important;
}}

/* ---- Stats card ---- */
.stats-card {{
    background-color: {t['card_bg']};
    border-radius: 1rem;
    padding: 0.85rem 1.2rem;
    margin-bottom: 1.4rem;
}}
.stats-card .prog-wrap {{
    background: rgba(128,128,128,0.2);
    border-radius: 99px; height: 5px;
    margin-bottom: 0.4rem; overflow: hidden;
}}
.stats-card .prog-fill {{
    height: 5px; border-radius: 99px;
    background: {t['accent']}; transition: width 0.4s ease;
}}
.stats-card .prog-label {{
    font-size: 0.70rem; opacity: 0.55;
    margin-bottom: 0.5rem; color: {t['card_fg']};
}}
.stats-card .stat-row {{ display: flex; gap: 1.4rem; flex-wrap: wrap; }}
.stats-card .stat-item {{ display: flex; flex-direction: column; }}
.stats-card .stat-label {{
    font-size: 0.68rem; font-weight: 500;
    text-transform: uppercase; letter-spacing: 0.08em;
    opacity: 0.55; color: {t['card_fg']};
}}
.stats-card .stat-value {{
    font-size: 1.15rem; font-weight: 600; color: {t['card_fg']};
}}

/* ---- Flashcard display ---- */
.fc-block {{
    border: 1px solid {t['border']};
    border-radius: 1.2rem;
    padding: 1.4rem 1.6rem 1.6rem 1.6rem;
    margin-bottom: 1.4rem;
    background: {t['bg']};
    cursor: pointer;
    user-select: none;
    -webkit-user-select: none;
    transition: border-color 0.15s ease;
}}
.fc-block:active {{
    border-color: {t['accent']};
}}
.fc-section-label {{
    font-size: 0.72rem; font-weight: 500;
    text-transform: uppercase; letter-spacing: 0.08em;
    color: {t['muted']};
    margin-bottom: 0.3rem;
}}
.fc-word {{
    font-family: 'Fraunces', serif;
    font-size: 2.8rem; font-weight: 700;
    line-height: 1.15; color: {t['fg']};
    margin-bottom: 0;
}}
.fc-divider {{
    border: none;
    border-top: 1px solid {t['border']};
    margin: 1.1rem 0;
}}
.fc-answer-label {{
    font-size: 0.72rem; font-weight: 500;
    text-transform: uppercase; letter-spacing: 0.08em;
    color: {t['muted']};
    margin-bottom: 0.3rem;
}}
.fc-answer {{
    font-family: 'Fraunces', serif;
    font-size: 2.4rem; font-weight: 400; font-style: italic;
    line-height: 1.2; color: {t['fg']};
}}
.fc-block-empty {{
    opacity: 0.35;
}}
.fc-word-placeholder {{
    font-family: 'Fraunces', serif;
    font-size: 2.4rem;
    line-height: 1.2;
    min-height: 2.9rem;
}}
.fc-note {{
    font-family: 'DM Sans', sans-serif;
    font-size: 1.0rem;
    font-weight: 400;
    color: {t['muted']};
    margin-top: 0.3rem;
    line-height: 1.3;
}}
.fc-answer-note {{
    font-family: 'DM Sans', sans-serif;
    font-size: 1.0rem;
    font-weight: 400;
    color: {t['muted']};
    margin-top: 0.3rem;
    line-height: 1.3;
}}

/* ---- Hamburger menu dropdown ---- */
.menu-dropdown {{
    background-color: {t['menu_bg']};
    border: 1px solid {t['border']};
    border-radius: 0.75rem;
    padding: 1rem 1.2rem 0.8rem 1.2rem;
    margin-bottom: 0.8rem;
}}
.menu-dropdown .menu-section-label {{
    font-size: 0.68rem; font-weight: 600;
    text-transform: uppercase; letter-spacing: 0.1em;
    color: {t['panel_label']};
    margin-bottom: 0.5rem;
}}

/* ---- Right panel ---- */
.right-panel {{
    padding-left: 0;
    padding-top: 0;
}}
.panel-section-label {{
    font-size: 0.68rem; font-weight: 600;
    text-transform: uppercase; letter-spacing: 0.1em;
    color: {t['panel_label']};
    margin-bottom: 0.4rem;
}}
.deck-name {{
    font-family: 'Fraunces', serif;
    font-size: 1.0rem; font-weight: 600;
    color: {t['fg']};
    margin-bottom: 0.7rem;
    line-height: 1.3; word-break: break-word;
}}

/* ---- Top title bar ---- */
.title-bar {{
    display: flex;
    align-items: baseline;
    gap: 0.7rem;
    padding: 1.2rem 0 0.8rem 0;
    border-bottom: 1px solid {t['border']};
    margin-bottom: 1.4rem;
}}
.title-bar-main {{
    font-family: 'Fraunces', serif;
    font-size: 1.6rem; font-weight: 700;
    color: {t['fg']}; line-height: 1;
}}
.title-bar-sub {{
    font-size: 0.78rem; font-weight: 400;
    color: {t['muted']};
    letter-spacing: 0.05em;
    text-transform: uppercase;
}}

/* ---- Big title (deck picker) ---- */
.title-block {{ padding: 1.8rem 0 1.2rem 0; }}
.title-main {{
    font-family: 'Fraunces', serif;
    font-size: 3.0rem; font-weight: 700;
    color: {t['fg']}; line-height: 1.1;
}}
.title-sub {{
    font-size: 1.0rem; font-weight: 300;
    color: {t['muted']}; margin-top: 0.4rem;
    letter-spacing: 0.06em; text-transform: uppercase;
}}
.soft-divider {{
    border: none; border-top: 1px solid {t['border']}; margin: 1rem 0;
}}

/* ---- Summary ---- */
.summary-title {{
    font-family: 'Fraunces', serif;
    font-size: 1.8rem; font-weight: 700;
    color: {t['fg']}; margin-bottom: 1rem;
}}
.summary-grid {{
    display: grid; grid-template-columns: 1fr 1fr;
    gap: 0.55rem 1.2rem;
    background: {t['card_bg']};
    border-radius: 1rem;
    padding: 1rem 1.2rem; margin-bottom: 1.2rem;
    font-size: 0.92rem;
}}
.summary-grid .sg-label {{ font-weight: 400; opacity: 0.65; color: {t['card_fg']}; }}
.summary-grid .sg-value {{ font-weight: 600; text-align: right; color: {t['card_fg']}; }}
</style>
""", unsafe_allow_html=True)

# ------------------------------------------------------------------------
# VIEWPORT META  (must be injected via JS — Streamlit doesn't set it)
# ------------------------------------------------------------------------

st.components.v1.html("""
<script>
(function() {
    var head = window.parent.document.head;
    if (!head.querySelector('meta[name="viewport"]')) {
        var meta = window.parent.document.createElement('meta');
        meta.name = 'viewport';
        meta.content = 'width=device-width, initial-scale=1, maximum-scale=1';
        head.appendChild(meta);
    }
})();
</script>
""", height=0)

# ------------------------------------------------------------------------
# CARD LOGIC HELPERS
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
    st.session_state.index     += 1
    st.session_state.show_answer = False
    mode = st.session_state.direction_mode
    if mode == "en_to_es":
        st.session_state.direction = "EN_TO_ES"
    elif mode == "es_to_en":
        st.session_state.direction = "ES_TO_EN"
    else:
        st.session_state.direction = random.choice(["EN_TO_ES", "ES_TO_EN"])

# ------------------------------------------------------------------------
# UI COMPONENTS
# ------------------------------------------------------------------------

def stats_card_html(shown, total, correct, repeat):
    pct        = int(shown / total * 100) if total > 0 else 0
    accuracy   = int(correct / shown * 100) if shown > 0 else 0
    missed_pct = int(repeat  / shown * 100) if shown > 0 else 0
    remaining  = total - shown
    st.markdown(f"""
    <div class="stats-card">
      <div class="prog-wrap"><div class="prog-fill" style="width:{pct}%"></div></div>
      <div class="prog-label">{pct}% complete &nbsp;·&nbsp; {remaining} remaining</div>
      <div class="stat-row">
        <div class="stat-item">
          <div class="stat-label">Correct</div><div class="stat-value">{correct}</div>
        </div>
        <div class="stat-item">
          <div class="stat-label">Repeat</div><div class="stat-value">{repeat}</div>
        </div>
        <div class="stat-item">
          <div class="stat-label">Accuracy</div><div class="stat-value">{accuracy}%</div>
        </div>
        <div class="stat-item">
          <div class="stat-label">Missed</div><div class="stat-value">{missed_pct}%</div>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)


def format_word(text, word_class, note_class):
    """Split bracketed notes onto a second smaller line."""
    import re
    m = re.search(r'(\[.*?\])', text)
    if m:
        main = text[:m.start()].strip()
        note = m.group(1)
        return ('<div class="' + word_class + '">' + main + '</div>'
                '<div class="' + note_class + '">' + note + '</div>')
    return '<div class="' + word_class + '">' + text + '</div>'

def render_flashcard(prompt, solution, show_answer):
    """Always render both boxes; answer box empty until revealed."""
    q_inner = format_word(prompt, 'fc-word', 'fc-note')
    q_html  = '<div class="fc-block"><div class="fc-section-label">Translate</div>' + q_inner + '</div>'
    st.markdown(q_html, unsafe_allow_html=True)
    if show_answer:
        a_inner = format_word(solution, 'fc-answer', 'fc-answer-note')
        a_html  = '<div class="fc-block"><div class="fc-section-label">Answer</div>' + a_inner + '</div>'
    else:
        a_html  = '<div class="fc-block fc-block-empty"><div class="fc-section-label">Answer</div><div class="fc-word-placeholder">&nbsp;</div></div>'
    st.markdown(a_html, unsafe_allow_html=True)

def title_bar():
    """Thin persistent title across the top of the main column."""
    st.markdown("""
    <div class="title-bar">
      <span class="title-bar-main">Spanish Flashcards</span>
      <span class="title-bar-sub">Collett</span>
    </div>
    """, unsafe_allow_html=True)


def inject_gestures(show_answer):
    """Inject touch/click gesture handlers for flashcard interaction."""
    # Button label text we search for in the DOM to trigger clicks
    reveal_label  = "\u2192"   # →
    correct_label = "\u2713"   # ✓
    repeat_label  = "?"

    js = f"""
    <script>
    (function() {{
        var SWIPE_MIN = 50;   // px to count as a swipe
        var startX, startY, startT;
        var showAnswer = {"true" if show_answer else "false"};

        function findBtn(label) {{
            var btns = window.parent.document.querySelectorAll('button');
            for (var i = 0; i < btns.length; i++) {{
                if (btns[i].innerText.trim() === label) return btns[i];
            }}
            return null;
        }}

        function clickBtn(label) {{
            var btn = findBtn(label);
            if (btn) btn.click();
        }}

        var card = window.parent.document.querySelector('.fc-block');
        if (!card) return;

        // Tap = reveal answer (only when answer not yet shown)
        card.addEventListener('click', function(e) {{
            if (!showAnswer) {{
                clickBtn("{reveal_label}");
            }}
        }});

        // Touch swipe = correct / repeat (only when answer is shown)
        card.addEventListener('touchstart', function(e) {{
            startX = e.touches[0].clientX;
            startY = e.touches[0].clientY;
            startT = Date.now();
        }}, {{passive: true}});

        card.addEventListener('touchend', function(e) {{
            if (!showAnswer) return;
            var dx = e.changedTouches[0].clientX - startX;
            var dy = e.changedTouches[0].clientY - startY;
            var dt = Date.now() - startT;
            if (Math.abs(dx) < SWIPE_MIN || Math.abs(dy) > Math.abs(dx)) return;
            if (dt > 600) return;  // too slow
            if (dx > 0) {{
                clickBtn("{correct_label}");
            }} else {{
                clickBtn("{repeat_label}");
            }}
        }}, {{passive: true}});
    }})();
    </script>
    """
    components.html(js, height=0)

def right_panel():
    """Right column: hamburger menu (theme) at top, deck info always visible at bottom."""
    st.markdown('<div class="right-panel"><div class="right-panel-inner">', unsafe_allow_html=True)

    # --- Hamburger toggle ---
    menu_icon = "✕" if st.session_state.menu_open else "☰"
    with st.container(key="hamburger_wrap"):
        if st.button(menu_icon, key="hamburger_btn"):
            st.session_state.menu_open = not st.session_state.menu_open
            st.rerun()

    # --- Menu dropdown ---
    if st.session_state.menu_open:
        st.markdown('<div class="menu-dropdown">', unsafe_allow_html=True)
        st.markdown('<div class="menu-section-label">Theme</div>', unsafe_allow_html=True)
        new_theme = st.radio(
            "Theme",
            options=["light", "dark", "aqua"],
            index=["light", "dark", "aqua"].index(st.session_state.theme),
            label_visibility="collapsed",
            key="theme_radio",
        )
        if new_theme != st.session_state.theme:
            st.session_state.theme     = new_theme
            st.session_state.menu_open = False
            save_prefs({"theme": new_theme})
            st.rerun()

        st.markdown('<div class="menu-section-label" style="margin-top:1rem;">Direction</div>', unsafe_allow_html=True)
        dir_options = ["Random 50/50", "EN → ES only", "ES → EN only"]
        dir_keys    = ["random", "en_to_es", "es_to_en"]
        cur_idx     = dir_keys.index(st.session_state.direction_mode)
        new_dir     = st.radio(
            "Direction",
            options=dir_options,
            index=cur_idx,
            label_visibility="collapsed",
            key="dir_radio",
        )
        if dir_options.index(new_dir) != cur_idx:
            st.session_state.direction_mode = dir_keys[dir_options.index(new_dir)]
            st.session_state.menu_open      = False
            save_prefs({"theme": st.session_state.theme, "direction_mode": st.session_state.direction_mode})
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    # --- Always-visible deck info ---
    if st.session_state.selected_csv:
        st.markdown(
            f"<hr style='border:none;border-top:1px solid {t['divider']};margin:0.9rem 0;'>",
            unsafe_allow_html=True,
        )
        st.markdown('<div class="panel-section-label">Deck</div>', unsafe_allow_html=True)
        deck_name = st.session_state.selected_csv.replace("_", " ").replace(".csv", "")
        st.markdown(f'<div class="deck-name">{deck_name}</div>', unsafe_allow_html=True)
        with st.container(key="changedeck_wrap"):
            if st.button("← Change Deck", key="changedeck_btn"):
                for k in ("selected_csv", "loaded_csv"):
                    st.session_state[k] = None
                for k in ("cards", "order"):
                    st.session_state[k] = []
                st.session_state.index          = 0
                st.session_state.show_answer    = False
                st.session_state.quit_requested = False
                st.session_state.final_exit     = False
                st.session_state.menu_open      = False
                st.rerun()

    st.markdown('</div></div>', unsafe_allow_html=True)

# ========================================================================
# FINAL EXIT
# ========================================================================

if st.session_state.final_exit:
    main_col, panel_col = st.columns([3, 1])
    with main_col:
        title_bar()
        st.markdown("""
        <div class="title-block">
          <div class="title-main">¡Buen trabajo!</div>
          <div class="title-sub">Keep practicing every day</div>
        </div>""", unsafe_allow_html=True)
    with panel_col:
        right_panel()
    st.stop()

# ========================================================================
# DECK PICKER
# ========================================================================

if st.session_state.selected_csv is None:
    main_col, panel_col = st.columns([3, 1])
    with main_col:
        title_bar()
        st.markdown("<hr class='soft-divider'>", unsafe_allow_html=True)
        deck_options = ["-- Choose a deck --", *csv_files]
        selected = st.selectbox("Available decks:", deck_options, index=0)
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
    with panel_col:
        right_panel()
    st.stop()

# ========================================================================
# LOAD CSV
# ========================================================================

if st.session_state.loaded_csv != st.session_state.selected_csv or not st.session_state.cards:
    df = pd.read_csv(os.path.join(CSV_FOLDER, st.session_state.selected_csv))
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
    main_col, panel_col = st.columns([3, 1])
    with main_col:
        title_bar()
        st.markdown("<div class='summary-title'>Session Summary</div>", unsafe_allow_html=True)

        perfect_first_try = sum(
            1 for c in st.session_state.cards
            if c["shown"] and c["repeat_score"] == 0 and c["error_flag"] == 0
        )
        avg_rs = (
            sum(c["repeat_score"] for c in st.session_state.cards if c["shown"]) / shown_cards
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

        c1, c2 = st.columns(2)
        with c1:
            with st.container(key="quitnow_wrap"):
                if st.button("Quit", key="quitnow_btn"):
                    st.session_state.final_exit = True
                    st.rerun()
        with c2:
            with st.container(key="newsession_wrap"):
                if st.button("New Session", key="newsession_btn"):
                    for k in ("selected_csv", "loaded_csv"):
                        st.session_state[k] = None
                    for k in ("cards", "order"):
                        st.session_state[k] = []
                    st.session_state.index          = 0
                    st.session_state.show_answer    = False
                    st.session_state.quit_requested = False
                    st.session_state.final_exit     = False
                    st.rerun()

    with panel_col:
        right_panel()
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

# ========================================================================
# MAIN LAYOUT
# ========================================================================

main_col, panel_col = st.columns([3, 1])

with main_col:
    title_bar()
    stats_card_html(shown_cards, total_cards, correct_count, repeat_count)
    render_flashcard(prompt, solution, st.session_state.show_answer)
    inject_gestures(st.session_state.show_answer)

    if not st.session_state.show_answer:
        colA, colB, _ = st.columns([0.14, 0.14, 0.72])
        with colA:
            with st.container(key="showanswer_wrap"):
                st.button("→", key="showanswer_btn", on_click=reveal_answer)
        with colB:
            with st.container(key="quitbefore_wrap"):
                if st.button("🛑", key="quitbefore_btn"):
                    st.session_state.quit_requested = True
                    st.rerun()
    else:
        col1, col2, _ = st.columns([0.14, 0.14, 0.72])
        with col1:
            with st.container(key="correct_wrap"):
                st.button("✓", key="correct_btn", on_click=mark_correct)
        with col2:
            with st.container(key="repeat_wrap"):
                st.button("?", key="repeat_btn", on_click=mark_repeat)

with panel_col:
    right_panel()