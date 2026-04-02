# REV 57
# streamlit_eng_sp_flashcards.py

import streamlit as st
import random
import os
import sys
import json
import html
import re
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
REVIEWS_FILE = os.path.expanduser("~/.flashcards_reviews.json")

PERSON_LABELS = {
    "miguel": "Miguel",
    "david": "David",
}
REVIEW_DECK_VALUES = {
    person: f"__review_{person}__"
    for person in PERSON_LABELS
}
REVIEW_DECK_ORDER = [REVIEW_DECK_VALUES["miguel"], REVIEW_DECK_VALUES["david"]]

BUTTON_COLORS = {
    "green": {"bg": "#c8f0d8", "border": "#2e8b57", "fg": "#0f4f29"},
    "yellow": {"bg": "#fdf0c0", "border": "#b8860b", "fg": "#6a4b00"},
    "blue": {"bg": "#d7e5ff", "border": "#2f6fdf", "fg": "#17479a"},
    "red": {"bg": "#f8d8d8", "border": "#c23b22", "fg": "#7f1717"},
}

csv_files = [f for f in os.listdir(CSV_FOLDER) if f.endswith(".csv")]
csv_files.sort(key=str.lower)


def review_item_key(word, answer):
    return json.dumps([word, answer], ensure_ascii=False, separators=(",", ":"))


def is_review_deck(deck_value):
    return deck_value in REVIEW_DECK_VALUES.values()


def review_deck_person(deck_value):
    for person, review_value in REVIEW_DECK_VALUES.items():
        if review_value == deck_value:
            return person
    return None


def review_deck_label(person):
    return f"REVIEW - {PERSON_LABELS[person]}"


def csv_data_row_count(filename):
    file_path = os.path.join(CSV_FOLDER, filename)
    try:
        with open(file_path, encoding="utf-8", errors="ignore") as handle:
            return max(sum(1 for _ in handle) - 1, 0)
    except Exception:
        return 0


csv_row_counts = {filename: csv_data_row_count(filename) for filename in csv_files}


def display_deck_name(filename):
    if is_review_deck(filename):
        return review_deck_label(review_deck_person(filename))
    base_name, extension = os.path.splitext(filename)
    if extension.lower() == ".csv":
        return f"{base_name} [{csv_row_counts.get(filename, 0)}]"
    return base_name


def is_forced_en_es_deck(filename):
    return bool(filename) and not is_review_deck(filename) and "EN_ES" in os.path.basename(filename)

# ------------------------------------------------------------------------
# PREFS
# ------------------------------------------------------------------------

DEFAULT_THEME = "dark"
DEFAULT_DIRECTION_MODE = "random"
DEFAULT_SPEECH_SPEED = 5
DEFAULT_SHOW_HINTS = True


def default_person_prefs():
    return {
        "theme": DEFAULT_THEME,
        "direction_mode": DEFAULT_DIRECTION_MODE,
        "speech_speed": DEFAULT_SPEECH_SPEED,
        "show_hints": DEFAULT_SHOW_HINTS,
    }


def sanitize_person_prefs(pref_data, fallback=None):
    fallback = fallback or default_person_prefs()
    theme = pref_data.get("theme", fallback["theme"])
    if theme not in THEMES:
        theme = fallback["theme"]
    direction_mode = pref_data.get("direction_mode", fallback["direction_mode"])
    if direction_mode not in {"random", "en_to_es", "es_to_en"}:
        direction_mode = fallback["direction_mode"]
    speech_speed = pref_data.get("speech_speed", fallback["speech_speed"])
    if speech_speed not in {1, 2, 3, 4, 5}:
        speech_speed = fallback["speech_speed"]
    show_hints = pref_data.get("show_hints", fallback["show_hints"])
    if not isinstance(show_hints, bool):
        show_hints = fallback["show_hints"]
    return {
        "theme": theme,
        "direction_mode": direction_mode,
        "speech_speed": speech_speed,
        "show_hints": show_hints,
    }


def normalize_prefs(pref_data):
    pref_data = pref_data if isinstance(pref_data, dict) else {}
    shared_defaults = sanitize_person_prefs(pref_data, default_person_prefs())
    raw_person_settings = pref_data.get("person_settings", {})
    if not isinstance(raw_person_settings, dict):
        raw_person_settings = {}

    person_settings = {}
    for person in PERSON_LABELS:
        person_settings[person] = sanitize_person_prefs(
            raw_person_settings.get(person, {}),
            shared_defaults,
        )

    active_person = pref_data.get("active_person", "miguel")
    if active_person not in PERSON_LABELS:
        active_person = "miguel"

    return {
        "active_person": active_person,
        "person_settings": person_settings,
    }


def direction_for_mode(direction_mode):
    if direction_mode == "en_to_es":
        return "EN_TO_ES"
    if direction_mode == "es_to_en":
        return "ES_TO_EN"
    return random.choice(["EN_TO_ES", "ES_TO_EN"])


def effective_direction(deck_value=None):
    deck_value = st.session_state.selected_csv if deck_value is None else deck_value
    if is_forced_en_es_deck(deck_value):
        return "EN_TO_ES"
    return direction_for_mode(st.session_state.direction_mode)

def load_prefs():
    try:
        with open(PREFS_FILE, encoding="utf-8") as f:
            return normalize_prefs(json.load(f))
    except Exception:
        return normalize_prefs({})


def save_prefs(pref_data):
    try:
        with open(PREFS_FILE, "w", encoding="utf-8") as f:
            json.dump(normalize_prefs(pref_data), f, ensure_ascii=False)
    except Exception:
        pass


def load_review_data():
    empty = {person: {} for person in PERSON_LABELS}
    try:
        with open(REVIEWS_FILE, encoding="utf-8") as f:
            raw = json.load(f)
    except Exception:
        return empty

    review_data = {person: {} for person in PERSON_LABELS}
    for person in PERSON_LABELS:
        person_entries = raw.get(person, [])
        if isinstance(person_entries, dict):
            person_entries = person_entries.values()
        if not isinstance(person_entries, list) and not hasattr(person_entries, "__iter__"):
            continue
        for entry in person_entries:
            if not isinstance(entry, dict):
                continue
            word = str(entry.get("word", "")).strip()
            answer = str(entry.get("answer", "")).strip()
            try:
                count = int(entry.get("count", 0))
            except (TypeError, ValueError):
                count = 0
            if word and answer and count > 0:
                review_data[person][review_item_key(word, answer)] = {
                    "word": word,
                    "answer": answer,
                    "count": count,
                }
    return review_data


def save_review_data(review_data):
    try:
        with open(REVIEWS_FILE, "w", encoding="utf-8") as f:
            serializable = {
                person: list(review_data.get(person, {}).values())
                for person in PERSON_LABELS
            }
            json.dump(serializable, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def current_prefs():
    current_person = st.session_state.active_person
    person_settings = {
        person: dict(st.session_state.person_settings.get(person, default_person_prefs()))
        for person in PERSON_LABELS
    }
    person_settings[current_person] = {
        "theme": st.session_state.theme,
        "direction_mode": st.session_state.direction_mode,
        "speech_speed": st.session_state.speech_speed,
        "show_hints": st.session_state.show_hints,
    }
    return {
        "active_person": st.session_state.active_person,
        "person_settings": person_settings,
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
        "review":        "#7c3aed",
        "review_light":  "#efe4ff",
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
        "review":        "#c084fc",
        "review_light":  "#2b1642",
        "menu_bg":       "#1a1d26",
        "dropdown_bg":   "#1a1d26",
        "dropdown_fg":   "#e8e4dc",
        "dropdown_hover":"#252836",
    },
    "aqua": {
        "bg":            "#071a20",
        "fg":            "#d9f4fb",
        "card_bg":       "#0b2a33",
        "card_fg":       "#d9f4fb",
        "accent":        "#008ead",
        "accent_light":  "#0b3c49",
        "info":          "#44b5d4",
        "info_light":    "#0d3140",
        "warn":          "#c48a0a",
        "warn_light":    "#2a1e00",
        "danger":        "#cf5b5b",
        "danger_light":  "#321315",
        "border":        "#006e85",
        "divider":       "#006e85",
        "muted":         "#79b8c6",
        "btn_show_bg":   "#005a6b",
        "btn_show_fg":   "#b9f0fb",
        "btn_show_bd":   "#008ead",
        "panel_label":   "#66aab9",
        "review":        "#d28cff",
        "review_light":  "#311447",
        "menu_bg":       "#09232b",
        "dropdown_bg":   "#09232b",
        "dropdown_fg":   "#d9f4fb",
        "dropdown_hover":"#0d3440",
    },
    "amber": {
        "bg":            "#241506",
        "fg":            "#ffe39a",
        "card_bg":       "#362006",
        "card_fg":       "#fff0c8",
        "accent":        "#cd9b00",
        "accent_light":  "#5c3205",
        "info":          "#f5b900",
        "info_light":    "#52350a",
        "warn":          "#f5b900",
        "warn_light":    "#5b430c",
        "danger":        "#ff7a45",
        "danger_light":  "#3d1710",
        "border":        "#cd9b00",
        "divider":       "#b77800",
        "muted":         "#efc15a",
        "btn_show_bg":   "#5a3204",
        "btn_show_fg":   "#ffdc8a",
        "btn_show_bd":   "#f5b900",
        "panel_label":   "#e5b84e",
        "review":        "#ffb85c",
        "review_light":  "#4a2806",
        "menu_bg":       "#2f1b06",
        "dropdown_bg":   "#2f1b06",
        "dropdown_fg":   "#fff0c8",
        "dropdown_hover":"#4a2b08",
    },
}

# ------------------------------------------------------------------------
# SESSION STATE
# ------------------------------------------------------------------------

prefs = load_prefs()
review_data = load_review_data()
active_person = prefs["active_person"]
active_person_prefs = prefs["person_settings"][active_person]

defaults = {
    "theme":          active_person_prefs["theme"],
    "menu_open":      False,
    "direction_mode": active_person_prefs["direction_mode"],
    "speech_speed":   active_person_prefs["speech_speed"],
    "show_hints":     active_person_prefs["show_hints"],
    "active_person":  active_person,
    "person_radio":   active_person,
    "person_settings": prefs["person_settings"],
    "review_data":    review_data,
    "selected_csv":   None,
    "cards":          [],
    "order":          [],
    "index":          0,
    "show_answer":    False,
    "direction":      direction_for_mode(active_person_prefs["direction_mode"]),
    "quit_requested": False,
    "final_exit":     False,
    "loaded_csv":     None,
    "erase_review_confirm": False,
    "delete_review_confirm_key": None,
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

t = THEMES[st.session_state.theme]


def sync_menu_widget_state():
    direction_labels = {
        "random": "Random 50/50",
        "en_to_es": "EN → ES only",
        "es_to_en": "ES → EN only",
    }
    st.session_state.theme_radio = st.session_state.theme
    st.session_state.dir_radio = direction_labels[st.session_state.direction_mode]
    st.session_state.speech_speed_radio = st.session_state.speech_speed
    st.session_state.hints_radio = "Hints ON" if st.session_state.show_hints else "Hints OFF"


def store_active_person_prefs():
    st.session_state.person_settings[st.session_state.active_person] = {
        "theme": st.session_state.theme,
        "direction_mode": st.session_state.direction_mode,
        "speech_speed": st.session_state.speech_speed,
        "show_hints": st.session_state.show_hints,
    }


def close_menu_and_save():
    store_active_person_prefs()
    save_prefs(current_prefs())
    st.session_state.menu_open = False
    st.session_state.erase_review_confirm = False


def render_menu_backdrop_close_handler():
    components.html(
        """
        <script>
        (function() {
            var doc = window.parent.document;
            var backdrop = doc.querySelector('.menu-backdrop');
            var closeButton = doc.querySelector('.st-key-close_menu_backdrop_wrap button');

            if (!backdrop || !closeButton) {
                return;
            }

            if (doc._menuBackdropHandler && doc._menuBackdropElement) {
                doc._menuBackdropElement.removeEventListener('click', doc._menuBackdropHandler);
            }

            doc._menuBackdropElement = backdrop;
            doc._menuBackdropHandler = function() {
                closeButton.dispatchEvent(new MouseEvent('click', { bubbles: true }));
            };

            backdrop.addEventListener('click', doc._menuBackdropHandler);
        })();
        </script>
        """,
        height=0,
    )


def apply_person_prefs(person):
    person_prefs = sanitize_person_prefs(
        st.session_state.person_settings.get(person, {}),
        default_person_prefs(),
    )
    st.session_state.person_settings[person] = person_prefs
    st.session_state.theme = person_prefs["theme"]
    st.session_state.direction_mode = person_prefs["direction_mode"]
    st.session_state.speech_speed = person_prefs["speech_speed"]
    st.session_state.show_hints = person_prefs["show_hints"]
    st.session_state.direction = direction_for_mode(person_prefs["direction_mode"])
    sync_menu_widget_state()


def review_count_for(person):
    return len(st.session_state.review_data.get(person, {}))


def review_deck_selectable(deck_value):
    if not is_review_deck(deck_value):
        return True
    person = review_deck_person(deck_value)
    return person == st.session_state.active_person and review_count_for(person) > 0


def visible_review_deck_values():
    active_review_value = REVIEW_DECK_VALUES[st.session_state.active_person]
    if review_count_for(st.session_state.active_person) > 0:
        return [active_review_value]
    return []


def reset_study_state(reset_selected=True):
    if reset_selected:
        st.session_state.selected_csv = None
    st.session_state.loaded_csv = None
    st.session_state.cards = []
    st.session_state.order = []
    st.session_state.index = 0
    st.session_state.show_answer = False
    st.session_state.quit_requested = False
    st.session_state.final_exit = False
    st.session_state.delete_review_confirm_key = None


def activate_deck(deck_value):
    reset_study_state(reset_selected=False)
    st.session_state.selected_csv = deck_value
    st.session_state.direction = effective_direction(deck_value)


def current_review_person():
    if is_review_deck(st.session_state.selected_csv):
        return review_deck_person(st.session_state.selected_csv)
    return st.session_state.active_person


def current_review_card_key(card):
    return review_item_key(card["word"], card["answer"])


def upsert_review_item(person, word, answer, count=5):
    key = review_item_key(word, answer)
    st.session_state.review_data.setdefault(person, {})[key] = {
        "word": word,
        "answer": answer,
        "count": count,
    }
    save_review_data(st.session_state.review_data)


def decrement_review_item(person, word, answer):
    key = review_item_key(word, answer)
    entry = st.session_state.review_data.get(person, {}).get(key)
    if not entry:
        return False
    entry["count"] -= 1
    removed = entry["count"] <= 0
    if removed:
        del st.session_state.review_data[person][key]
    save_review_data(st.session_state.review_data)
    return removed


def delete_review_item(person, word, answer):
    key = review_item_key(word, answer)
    if key not in st.session_state.review_data.get(person, {}):
        return False
    del st.session_state.review_data[person][key]
    save_review_data(st.session_state.review_data)
    return True


def purge_remaining_occurrences(card_index, current_position=None):
    if current_position is None:
        current_position = st.session_state.index
    st.session_state.order = (
        st.session_state.order[: current_position + 1]
        + [idx for idx in st.session_state.order[current_position + 1:] if idx != card_index]
    )


def erase_review_deck(person):
    st.session_state.review_data[person] = {}
    save_review_data(st.session_state.review_data)
    st.session_state.erase_review_confirm = False
    st.session_state.menu_open = False
    if st.session_state.selected_csv == REVIEW_DECK_VALUES[person]:
        reset_study_state(reset_selected=True)

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
.st-key-person_radio_wrap {{
    margin: 0.05rem 0 0.5rem 0 !important;
}}
.st-key-person_radio_wrap [data-testid="stRadio"] > div {{
    flex-direction: row !important;
    justify-content: flex-start !important;
    gap: 1.3rem !important;
}}
.st-key-person_radio_wrap label p {{
    font-size: 0.95rem !important;
}}

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
div[data-testid="stButton"] > button > div,
div[data-testid="stButton"] > button p,
div[data-testid="stButton"] > button span {{
    color: inherit !important;
}}
div[data-testid="stButton"] > button [data-testid="stMarkdownContainer"],
div[data-testid="stButton"] > button [data-testid="stMarkdownContainer"] p,
div[data-testid="stButton"] > button [data-testid="stMarkdownContainer"] span,
div[data-testid="stButton"] > button [data-testid="stMarkdownContainer"] div {{
    color: inherit !important;
    -webkit-text-fill-color: currentColor !important;
    opacity: 1 !important;
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
    background-color: {BUTTON_COLORS['green']['bg']} !important;
    border-color: {BUTTON_COLORS['green']['border']} !important;
    color: {BUTTON_COLORS['green']['fg']} !important;
    font-size: 1.42rem !important;
    font-weight: 600 !important;
}}
.st-key-showanswer_wrap div[data-testid="stButton"] > button [data-testid="stMarkdownContainer"],
.st-key-showanswer_wrap div[data-testid="stButton"] > button [data-testid="stMarkdownContainer"] p,
.st-key-showanswer_wrap div[data-testid="stButton"] > button [data-testid="stMarkdownContainer"] span,
.st-key-showanswer_wrap div[data-testid="stButton"] > button [data-testid="stMarkdownContainer"] div {{
    font-size: 1.45rem !important;
    font-weight: 600 !important;
    line-height: 1 !important;
}}
/* ---- Correct ✓ ---- */
.st-key-correct_wrap div[data-testid="stButton"] > button {{
    background-color: {BUTTON_COLORS['green']['bg']} !important;
    border-color: {BUTTON_COLORS['green']['border']} !important;
    color: {BUTTON_COLORS['green']['fg']} !important;
}}
/* ---- Repeat ? ---- */
.st-key-repeat_wrap div[data-testid="stButton"] > button {{
    background-color: {BUTTON_COLORS['yellow']['bg']} !important;
    border-color: {BUTTON_COLORS['yellow']['border']} !important;
    color: {BUTTON_COLORS['yellow']['fg']} !important;
}}
/* ---- Quit before 🛑 ---- */
.st-key-quitbefore_wrap div[data-testid="stButton"] > button {{
    background-color: {BUTTON_COLORS['red']['bg']} !important;
    border-color: {BUTTON_COLORS['red']['border']} !important;
    color: {BUTTON_COLORS['red']['fg']} !important;
}}
/* ---- Quit ---- */
.st-key-quitnow_wrap div[data-testid="stButton"] > button {{
    background-color: {BUTTON_COLORS['red']['bg']} !important;
    border-color: {BUTTON_COLORS['red']['border']} !important;
    color: {BUTTON_COLORS['red']['fg']} !important;
}}
/* ---- New Session ---- */
.st-key-newsession_wrap div[data-testid="stButton"] > button {{
    background-color: {BUTTON_COLORS['green']['bg']} !important;
    border-color: {BUTTON_COLORS['green']['border']} !important;
    color: {BUTTON_COLORS['green']['fg']} !important;
}}
/* ---- Mistakes Only ---- */
.st-key-mistakesonly_wrap div[data-testid="stButton"] > button {{
    background-color: {BUTTON_COLORS['blue']['bg']} !important;
    border-color: {BUTTON_COLORS['blue']['border']} !important;
    color: {BUTTON_COLORS['blue']['fg']} !important;
}}
.st-key-speaker_wrap div[data-testid="stButton"] > button {{
    background-color: {BUTTON_COLORS['blue']['bg']} !important;
    border-color: {BUTTON_COLORS['blue']['border']} !important;
    color: {BUTTON_COLORS['blue']['fg']} !important;
}}
.st-key-del_active_wrap div[data-testid="stButton"] > button {{
    background-color: {t['review_light']} !important;
    border-color: {t['review']} !important;
    color: {t['review']} !important;
}}
.st-key-del_confirm_wrap div[data-testid="stButton"] > button {{
    background-color: {t['danger']} !important;
    border-color: {t['danger']} !important;
    color: white !important;
}}
.st-key-del_wrap div[data-testid="stButton"] > button,
.st-key-del_active_wrap div[data-testid="stButton"] > button,
.st-key-del_confirm_wrap div[data-testid="stButton"] > button {{
    width: 3.6rem !important;
}}
.st-key-clear_delete_confirm_wrap {{
    display: none !important;
}}
.st-key-del_wrap div[data-testid="stButton"] > button:disabled {{
    background-color: rgba(128, 128, 128, 0.14) !important;
    border-color: rgba(128, 128, 128, 0.30) !important;
    color: rgba(180, 180, 180, 0.55) !important;
    opacity: 1 !important;
    cursor: default !important;
}}
.st-key-review_miguel_active_wrap div[data-testid="stButton"] > button,
.st-key-review_david_active_wrap div[data-testid="stButton"] > button {{
    background-color: {t['review_light']} !important;
    color: {t['review']} !important;
    font-weight: 700 !important;
}}
.st-key-review_miguel_inactive_wrap div[data-testid="stButton"] > button,
.st-key-review_david_inactive_wrap div[data-testid="stButton"] > button {{
    background-color: rgba(128, 128, 128, 0.10) !important;
    color: {t['muted']} !important;
    opacity: 1 !important;
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
    flex: 0 0 4.8rem !important;
    width: 4.8rem !important;
    min-width: 4.8rem !important;
    max-width: 4.8rem !important;
}}
.st-key-icon_btn_row_wrap [data-testid="stColumn"] > div,
.st-key-icon_btn_row_wrap div[data-testid="stButton"],
.st-key-icon_btn_row_wrap div[data-testid="stButton"] > div {{
    width: 100% !important;
}}
.st-key-icon_btn_row_wrap div[data-testid="stButton"] > button {{
    width: 100% !important;
    min-height: 3.2rem !important;
    font-size: 1.55rem !important;
    font-weight: 700 !important;
}}
.st-key-icon_btn_row_wrap div[data-testid="stButton"] > button [data-testid="stMarkdownContainer"],
.st-key-icon_btn_row_wrap div[data-testid="stButton"] > button [data-testid="stMarkdownContainer"] p,
.st-key-icon_btn_row_wrap div[data-testid="stButton"] > button [data-testid="stMarkdownContainer"] span,
.st-key-icon_btn_row_wrap div[data-testid="stButton"] > button [data-testid="stMarkdownContainer"] div {{
    font-size: 1.55rem !important;
    font-weight: 700 !important;
    line-height: 1 !important;
}}

/* ---- Revealed answer action row ---- */
.st-key-answer_action_row_wrap [data-testid="stHorizontalBlock"] {{
    display: flex !important;
    flex-direction: row !important;
    flex-wrap: nowrap !important;
    justify-content: center !important;
    align-items: center !important;
    gap: 0.26rem !important;
    width: fit-content !important;
    margin: 0 auto !important;
}}
.st-key-answer_action_row_wrap [data-testid="stColumn"] {{
    flex: 0 0 3.6rem !important;
    width: 3.6rem !important;
    min-width: 3.6rem !important;
    max-width: 3.6rem !important;
}}
.st-key-answer_action_row_wrap [data-testid="stColumn"] > div,
.st-key-answer_action_row_wrap div[data-testid="stButton"],
.st-key-answer_action_row_wrap div[data-testid="stButton"] > div {{
    width: 100% !important;
}}
.st-key-answer_action_row_wrap .st-key-speaker_wrap,
.st-key-answer_action_row_wrap .st-key-speaker_wrap > div,
.st-key-answer_action_row_wrap .st-key-speaker_wrap [data-testid="stElementContainer"] {{
    width: 100% !important;
    min-width: 100% !important;
}}
.st-key-answer_action_row_wrap .st-key-speaker_wrap iframe {{
    width: 100% !important;
    min-width: 100% !important;
    max-width: 100% !important;
    display: block !important;
    margin: 0.12rem 0 0 0 !important;
}}
.st-key-answer_action_row_wrap div[data-testid="stButton"] > button {{
    width: 3.6rem !important;
    min-height: 3.2rem !important;
    font-size: 1.55rem !important;
    font-weight: 700 !important;
}}
.st-key-answer_action_row_wrap div[data-testid="stButton"] > button [data-testid="stMarkdownContainer"],
.st-key-answer_action_row_wrap div[data-testid="stButton"] > button [data-testid="stMarkdownContainer"] p,
.st-key-answer_action_row_wrap div[data-testid="stButton"] > button [data-testid="stMarkdownContainer"] span,
.st-key-answer_action_row_wrap div[data-testid="stButton"] > button [data-testid="stMarkdownContainer"] div {{
    font-size: 1.55rem !important;
    font-weight: 700 !important;
    line-height: 1 !important;
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
    font-weight: 700 !important;
    padding-left: 0.55rem !important;
    padding-right: 0.55rem !important;
}}
.st-key-summary_btn_row_wrap div[data-testid="stButton"] > button [data-testid="stMarkdownContainer"],
.st-key-summary_btn_row_wrap div[data-testid="stButton"] > button [data-testid="stMarkdownContainer"] p,
.st-key-summary_btn_row_wrap div[data-testid="stButton"] > button [data-testid="stMarkdownContainer"] span,
.st-key-summary_btn_row_wrap div[data-testid="stButton"] > button [data-testid="stMarkdownContainer"] div {{
    font-size: 0.92rem !important;
    font-weight: 700 !important;
    line-height: 1.05 !important;
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
.menu-backdrop {{
    position: fixed;
    inset: 0;
    background: rgba(0, 0, 0, 0.38);
    z-index: 998;
    pointer-events: auto;
}}
.st-key-menu_modal_wrap {{
    position: relative;
    z-index: 999;
}}
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
.st-key-erase_review_wrap,
.st-key-erase_review_confirm_wrap {{
    margin-top: 0.95rem !important;
}}
.st-key-clear_erase_review_confirm_wrap {{
    display: none !important;
}}
.st-key-close_menu_backdrop_wrap {{
    display: none !important;
}}
.st-key-erase_review_wrap div[data-testid="stButton"] > button,
.st-key-erase_review_confirm_wrap div[data-testid="stButton"] > button {{
    min-height: 2.65rem !important;
    font-size: 0.95rem !important;
    font-weight: 700 !important;
}}
.st-key-erase_review_confirm_wrap div[data-testid="stButton"] > button {{
    background-color: {t['danger']} !important;
    border-color: {t['danger']} !important;
    color: white !important;
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
.fc-inline-note {{
    font-size: 0.72em;
    font-weight: 400;
    color: {t['muted']};
    white-space: nowrap;
}}
.fc-inline-hint {{
    font-size: 0.72em;
    font-weight: 400;
    color: color-mix(in srgb, {t['muted']} 65%, {t['accent']} 35%);
    white-space: nowrap;
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
.summary-review-line {{
    font-size: 0.92rem;
    color: {t['fg']};
    margin: 0.15rem 0;
}}

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
    .st-key-review_miguel_active_wrap [data-testid="stButton"] > button,
    .st-key-review_david_active_wrap [data-testid="stButton"] > button {{
        color: {t['review']} !important;
        font-weight: 700 !important;
    }}
    .st-key-review_miguel_inactive_wrap [data-testid="stButton"] > button,
    .st-key-review_david_inactive_wrap [data-testid="stButton"] > button {{
        color: {t['muted']} !important;
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
    idx = current_card_index()
    card = st.session_state.cards[idx]
    st.session_state.delete_review_confirm_key = None
    if is_review_deck(st.session_state.selected_csv):
        review_person = review_deck_person(st.session_state.selected_csv)
        decrement_review_item(review_person, card["word"], card["answer"])
        card["repeat_score"] = max(card["repeat_score"] - 1, 0)
        advance_card()
    else:
        card["repeat_score"] = max(card["repeat_score"] - 1, 0)
        advance_card()


def mark_repeat():
    card = st.session_state.cards[current_card_index()]
    st.session_state.delete_review_confirm_key = None
    upsert_review_item(current_review_person(), card["word"], card["answer"], count=5)
    card["repeat_score"] = 5 if is_review_deck(st.session_state.selected_csv) else 2
    card["error_flag"] = 1
    advance_card()


def delete_current_review_card():
    if not is_review_deck(st.session_state.selected_csv):
        return
    idx = current_card_index()
    card = st.session_state.cards[idx]
    current_key = current_review_card_key(card)
    if st.session_state.delete_review_confirm_key != current_key:
        st.session_state.delete_review_confirm_key = current_key
        return
    review_person = review_deck_person(st.session_state.selected_csv)
    delete_review_item(review_person, card["word"], card["answer"])
    st.session_state.delete_review_confirm_key = None
    card["repeat_score"] = 0
    purge_remaining_occurrences(idx, st.session_state.index)
    advance_card(schedule_current=False)


def clear_delete_review_confirm():
    st.session_state.delete_review_confirm_key = None


def render_delete_confirm_timeout():
    components.html(
        """
        <script>
        (function() {
            function clickClearButton() {
                var doc = window.parent.document;
                var button = doc.querySelector('.st-key-clear_delete_confirm_wrap button');
                if (!button) {
                    return false;
                }
                button.dispatchEvent(new MouseEvent('click', {bubbles: true}));
                return true;
            }

            setTimeout(function() {
                if (clickClearButton()) return;
                var attempts = 0;
                var timer = setInterval(function() {
                    attempts += 1;
                    if (clickClearButton() || attempts >= 10) {
                        clearInterval(timer);
                    }
                }, 150);
            }, 2000);
        })();
        </script>
        """,
        height=0,
    )


def clear_erase_review_confirm():
    st.session_state.erase_review_confirm = False


def render_erase_review_confirm_timeout():
    components.html(
        """
        <script>
        (function() {
            function clickClearButton() {
                var doc = window.parent.document;
                var button = doc.querySelector('.st-key-clear_erase_review_confirm_wrap button');
                if (!button) {
                    return false;
                }
                button.dispatchEvent(new MouseEvent('click', {bubbles: true}));
                return true;
            }

            setTimeout(function() {
                if (clickClearButton()) return;
                var attempts = 0;
                var timer = setInterval(function() {
                    attempts += 1;
                    if (clickClearButton() || attempts >= 10) {
                        clearInterval(timer);
                    }
                }, 150);
            }, 2000);
        })();
        </script>
        """,
        height=0,
    )

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

def advance_card(schedule_current=True):
    idx  = current_card_index()
    card = st.session_state.cards[idx]
    card["shown"] = True
    if schedule_current and card["repeat_score"] > 0:
        schedule_repeat(idx, card["repeat_score"])
    st.session_state.index      += 1
    st.session_state.show_answer = False
    st.session_state.delete_review_confirm_key = None
    st.session_state.direction = effective_direction()

# ------------------------------------------------------------------------
# UI HELPERS
# ------------------------------------------------------------------------

def format_word(text, word_class, note_class):
    del note_class

    if not st.session_state.show_hints:
        text = re.sub(r'\s*\{[^{}]*\}\s*', ' ', text)

    parts = []
    last_end = 0
    has_inline_note = False

    for match in re.finditer(r'\[[^\[\]]*\]|\{[^{}]*\}', text):
        if match.start() > last_end:
            parts.append(html.escape(text[last_end:match.start()]))
        note_class_name = "fc-inline-hint" if match.group(0).startswith("{") else "fc-inline-note"
        parts.append(
            '<span class="' + note_class_name + '">'
            + html.escape(match.group(0))
            + '</span>'
        )
        last_end = match.end()
        has_inline_note = True

    if last_end < len(text):
        parts.append(html.escape(text[last_end:]))

    if has_inline_note:
        rendered_text = ''.join(parts)
    else:
        rendered_text = html.escape(text)

    return '<div class="' + word_class + '">' + rendered_text + '</div>'


def strip_spoken_text(text):
    spoken_text = re.sub(r'\[.*?\]|\(.*?\)|\{.*?\}', '', text)
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
        function clickShowAnswerButton() {
            var doc = window.parent.document;
            var showBtn = doc.querySelector('.st-key-showanswer_wrap button');
            if (showBtn) {
                showBtn.dispatchEvent(new MouseEvent('click', {bubbles:true}));
                return true;
            }

            var btns = doc.querySelectorAll('button');
            var labels = ['\u279c', '\u2192'];
            for (var i = 0; i < btns.length; i++) {
                if (labels.indexOf(btns[i].innerText.trim()) !== -1) {
                    btns[i].dispatchEvent(new MouseEvent('click', {bubbles:true}));
                    return true;
                }
            }

            return false;
        }
        function attach() {
            var doc = window.parent.document;
            var cards = doc.querySelectorAll('.fc-block');
            if (!cards.length) return false;
            if (doc._fcHandler) doc.body.removeEventListener('click', doc._fcHandler);
            doc._fcHandler = function(e) {
                if (!e.target.closest('.fc-block')) return;
                if (!showAnswer) clickShowAnswerButton();
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
            width: 3.6rem;
            min-height: 3.2rem;
            font-size: 1.15rem;
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
                    if st.session_state.menu_open:
                        close_menu_and_save()
                    else:
                        st.session_state.menu_open = True
                    st.rerun()
    with st.container(key="person_radio_wrap"):
        selected_person = st.radio(
            "Person",
            options=list(PERSON_LABELS.keys()),
            horizontal=True,
            format_func=lambda value: PERSON_LABELS[value],
            label_visibility="collapsed",
            key="person_radio",
        )
        if selected_person != st.session_state.active_person:
            store_active_person_prefs()
            st.session_state.active_person = selected_person
            apply_person_prefs(selected_person)
            st.session_state.erase_review_confirm = False
            save_prefs(current_prefs())
            if is_review_deck(st.session_state.selected_csv):
                review_person = review_deck_person(st.session_state.selected_csv)
                if review_person != selected_person:
                    reset_study_state(reset_selected=True)
            st.rerun()


def render_menu():
    if not st.session_state.menu_open:
        return
    active_review_count = review_count_for(st.session_state.active_person)
    active_person_label = PERSON_LABELS[st.session_state.active_person]
    with st.container(key="close_menu_backdrop_wrap"):
        st.button("__close_menu_backdrop__", key="close_menu_backdrop_btn", on_click=close_menu_and_save)
    st.markdown('<div class="menu-backdrop"></div>', unsafe_allow_html=True)
    render_menu_backdrop_close_handler()
    with st.container(key="menu_modal_wrap"):
        st.markdown('<div class="menu-dropdown">', unsafe_allow_html=True)
        st.markdown('<div class="menu-section-label">Hints</div>', unsafe_allow_html=True)
        hint_options = ["Hints ON", "Hints OFF"]
        new_hints = st.radio(
            "Hints",
            options=hint_options,
            index=0 if st.session_state.show_hints else 1,
            horizontal=True,
            label_visibility="collapsed",
            key="hints_radio",
        )
        hints_enabled = new_hints == "Hints ON"
        if hints_enabled != st.session_state.show_hints:
            st.session_state.show_hints = hints_enabled
            store_active_person_prefs()
            st.session_state.erase_review_confirm = False
            st.rerun()
        st.markdown('<div class="menu-section-label">Theme</div>', unsafe_allow_html=True)
        new_theme = st.radio("Theme", options=["light", "dark", "aqua", "amber"],
                             index=["light","dark","aqua", "amber"].index(st.session_state.theme),
                             label_visibility="collapsed", key="theme_radio")
        if new_theme != st.session_state.theme:
            st.session_state.theme     = new_theme
            store_active_person_prefs()
            st.session_state.erase_review_confirm = False
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
            st.session_state.direction = direction_for_mode(st.session_state.direction_mode)
            store_active_person_prefs()
            st.session_state.erase_review_confirm = False
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
            store_active_person_prefs()
            st.session_state.erase_review_confirm = False
            st.rerun()
        if active_review_count > 0:
            erase_label = f"Erase Review Deck ({active_person_label})"
            erase_wrap_key = "erase_review_confirm_wrap" if st.session_state.erase_review_confirm else "erase_review_wrap"
            with st.container(key=erase_wrap_key):
                if st.button(
                    erase_label,
                    key="erase_review_btn",
                ):
                    if st.session_state.erase_review_confirm:
                        erase_review_deck(st.session_state.active_person)
                    else:
                        st.session_state.erase_review_confirm = True
                    st.rerun()
            if st.session_state.erase_review_confirm:
                with st.container(key="clear_erase_review_confirm_wrap"):
                    st.button("__clear_erase_review_confirm__", key="clear_erase_review_confirm_btn", on_click=clear_erase_review_confirm)
                render_erase_review_confirm_timeout()
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
                    st.button("➜", key="showanswer_btn", on_click=reveal_answer)
            with col2:
                with st.container(key="quitbefore_wrap"):
                    if st.button("🛑", key="quitbefore_btn"):
                        st.session_state.quit_requested = True
                        st.rerun()
        return

    review_mode = is_review_deck(st.session_state.selected_csv)
    with st.container(key="answer_action_row_wrap"):
        action_columns = st.columns(4 if review_mode else 3, gap="small")
        col1, col2, col3 = action_columns[:3]
        with col1:
            with st.container(key="correct_wrap"):
                st.button("✓", key="correct_btn", on_click=mark_correct)
        with col2:
            with st.container(key="repeat_wrap"):
                st.button("?", key="repeat_btn", on_click=mark_repeat)
        with col3:
            with st.container(key="speaker_wrap"):
                render_speaker_button(spanish_audio_text)
        if review_mode:
            current_card = st.session_state.cards[current_card_index()]
            delete_armed = st.session_state.delete_review_confirm_key == current_review_card_key(current_card)
            with action_columns[3]:
                with st.container(key="del_confirm_wrap" if delete_armed else "del_active_wrap"):
                    st.button("X", key="del_btn", on_click=delete_current_review_card)
            if delete_armed:
                with st.container(key="clear_delete_confirm_wrap"):
                    st.button("__clear_delete_confirm__", key="clear_delete_confirm_btn", on_click=clear_delete_review_confirm)
                render_delete_confirm_timeout()


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
    if st.session_state.menu_open:
        st.stop()
    review_deck_values = visible_review_deck_values()
    deck_options = ["-- Choose a deck --", *review_deck_values, *csv_files]
    with st.container(key="mobile_deck_picker_wrap"):
        st.markdown("<div style='font-size: 0.95rem; color: " + t['fg'] + ";'>Available decks:</div>", unsafe_allow_html=True)
        deck_container = st.container(height=250)
        with deck_container:
            for person in PERSON_LABELS:
                review_value = REVIEW_DECK_VALUES[person]
                if review_value not in review_deck_values:
                    continue
                review_enabled = review_deck_selectable(review_value)
                review_wrap = f"review_{person}_{'active' if review_enabled else 'inactive'}_wrap"
                with st.container(key=review_wrap):
                    if st.button(
                        review_deck_label(person),
                        key=f"deck_btn_review_{person}",
                        use_container_width=True,
                        disabled=not review_enabled,
                    ):
                        activate_deck(review_value)
                        st.rerun()
            for csv_file in csv_files:
                deck_display = display_deck_name(csv_file)
                if st.button(deck_display, key=f"deck_btn_{csv_file}", use_container_width=True):
                    activate_deck(csv_file)
                    st.rerun()

    with st.container(key="desktop_deck_picker_wrap"):
        selected = st.selectbox(
            "Available decks:",
            deck_options,
            index=0,
            format_func=lambda value: value if value == "-- Choose a deck --" else display_deck_name(value),
        )
        if selected != deck_options[0]:
            if review_deck_selectable(selected):
                activate_deck(selected)
                st.rerun()
    st.stop()

# ========================================================================
# LOAD CSV
# ========================================================================

if st.session_state.loaded_csv != st.session_state.selected_csv or not st.session_state.cards:
    if is_review_deck(st.session_state.selected_csv):
        review_person = review_deck_person(st.session_state.selected_csv)
        review_items = list(st.session_state.review_data.get(review_person, {}).values())
        st.session_state.cards = [
            {"word": item["word"], "answer": item["answer"],
             "shown": False, "repeat_score": item["count"], "error_flag": 0}
            for item in review_items
        ]
    else:
        csv_path = os.path.join(CSV_FOLDER, st.session_state.selected_csv)
        with open(csv_path, 'r', encoding='utf-8') as _f:
            _first = _f.readline()
        _sep = ';' if ';' in _first else ','
        df = pd.read_csv(csv_path, sep=_sep)
        df.columns = [c.strip() for c in df.columns]
        if is_forced_en_es_deck(st.session_state.selected_csv):
            first_column = df.columns[0]
            second_column = df.columns[1]
            st.session_state.cards = [
                {"word": row[first_column], "answer": row[second_column],
                 "shown": False, "repeat_score": 1, "error_flag": 0}
                for _, row in df.iterrows()
            ]
        else:
            st.session_state.cards = [
                {"word": row["word"], "answer": row["answer"],
                 "shown": False, "repeat_score": 1, "error_flag": 0}
                for _, row in df.iterrows()
            ]
    st.session_state.order = list(range(len(st.session_state.cards)))
    random.shuffle(st.session_state.order)
    st.session_state.index = 0
    st.session_state.loaded_csv = st.session_state.selected_csv
    st.session_state.direction = effective_direction()

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
    current_user_label = PERSON_LABELS[st.session_state.active_person]
    current_review_cards = review_count_for(st.session_state.active_person)

    st.markdown(f"""
    <div class="summary-grid">
      <div class="sg-label">Cards Shown</div>      <div class="sg-value">{shown_cards}</div>
      <div class="sg-label">Correct</div>           <div class="sg-value">{correct_count}</div>
      <div class="sg-label">Repeat Needed</div>     <div class="sg-value">{repeat_count}</div>
      <div class="sg-label">Perfect First Try</div> <div class="sg-value">{perfect_first_try}</div>
      <div class="sg-label">Avg Repeat Score</div>  <div class="sg-value">{avg_rs:.2f}</div>
      <div class="sg-label">Accuracy</div>          <div class="sg-value">{accuracy}%</div>
      <div class="sg-label">Missed</div>            <div class="sg-value">{missed_pct}%</div>
            <div class="sg-label">REVIEW deck (# cards)</div> <div class="sg-value">{current_review_cards}</div>
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
                    reset_study_state(reset_selected=True)
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
current_direction = "EN_TO_ES" if is_forced_en_es_deck(st.session_state.selected_csv) else st.session_state.direction
if current_direction == "EN_TO_ES":
    prompt, solution = card["word"], card["answer"]
else:
    prompt, solution = card["answer"], card["word"]

spanish_text = solution if current_direction == "EN_TO_ES" else prompt

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