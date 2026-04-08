# REV 57
# streamlit_eng_sp_flashcards.py

import streamlit as st
import random
import os
import sys
import json
import html
import math
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
PROGRESS_FILE = os.path.expanduser("~/.flashcards_progress.json")

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


def normalize_card_id(raw_value):
    if pd.isna(raw_value):
        return None
    if isinstance(raw_value, bool):
        return str(raw_value).strip()
    if isinstance(raw_value, int):
        return str(raw_value)
    if isinstance(raw_value, float):
        if raw_value.is_integer():
            return str(int(raw_value))
        return str(raw_value).strip()
    text = str(raw_value).strip()
    if not text:
        return None
    if re.fullmatch(r"\d+\.0+", text):
        return text.split(".", 1)[0]
    return text


def completion_sort_key(value):
    return (0, int(value)) if value.isdigit() else (1, value.lower())


def load_regular_deck(filename):
    csv_path = os.path.join(CSV_FOLDER, filename)
    with open(csv_path, "r", encoding="utf-8") as handle:
        first_line = handle.readline()
    separator = ";" if ";" in first_line else ","
    df = pd.read_csv(csv_path, sep=separator)
    df.columns = [column.strip() for column in df.columns]

    lower_columns = {column.lower(): column for column in df.columns}
    id_column = lower_columns.get("id")

    if is_forced_en_es_deck(filename):
        content_columns = [column for column in df.columns if column != id_column]
        word_column = content_columns[0]
        answer_column = content_columns[1]
    else:
        word_column = lower_columns["word"]
        answer_column = lower_columns["answer"]

    cards = []
    for _, row in df.iterrows():
        cards.append(
            {
                "id": normalize_card_id(row[id_column]) if id_column else None,
                "word": row[word_column],
                "answer": row[answer_column],
                "shown": False,
                "scored": False,
                "repeat_score": 1,
                "error_flag": 0,
            }
        )

    return {
        "cards": cards,
        "supports_completion": bool(id_column),
    }


def display_deck_name(filename):
    if is_review_deck(filename):
        return review_deck_label(review_deck_person(filename))
    base_name, extension = os.path.splitext(filename)
    if extension.lower() == ".csv":
        return f"{base_name} [{csv_row_counts.get(filename, 0)}]"
    return base_name


def is_story_deck(filename):
    return bool(filename) and not is_review_deck(filename) and "story" in os.path.basename(filename).lower()


@st.cache_data(show_spinner=False)
def deck_completion_metadata(filename):
    deck_data = load_regular_deck(filename)
    valid_ids = [card["id"] for card in deck_data["cards"] if card.get("id")]
    return {
        "supported": deck_data["supports_completion"],
        "total": len(deck_data["cards"]),
        "valid_ids": valid_ids,
    }


def deck_picker_status(filename, person):
    if is_review_deck(filename):
        return "review"
    if is_story_deck(filename):
        return "story"

    metadata = deck_completion_metadata(filename)
    if not metadata["supported"]:
        return "untouched"

    completed_ids = completed_ids_for(person, filename)
    valid_ids = set(metadata["valid_ids"])
    completed_count = len(completed_ids & valid_ids)
    total_count = metadata["total"]

    if completed_count <= 0:
        return "untouched"
    if total_count > 0 and completed_count >= total_count:
        return "complete"
    return "in_progress"


def deck_picker_label(filename, person):
    symbol_map = {
        "review": "⭐",
        "story": "📖",
        "untouched": "•",
        "in_progress": "🟡",
        "complete": "✓",
    }
    status = deck_picker_status(filename, person)
    return f"{symbol_map[status]} {display_deck_name(filename)}"


def is_forced_en_es_deck(filename):
    return bool(filename) and not is_review_deck(filename) and "EN_ES" in os.path.basename(filename)

# ------------------------------------------------------------------------
# PREFS
# ------------------------------------------------------------------------

DEFAULT_THEME = "dark"
DEFAULT_DIRECTION_MODE = "random"
DEFAULT_SPEECH_SPEED = 5
DEFAULT_SHOW_HINTS = True
DEFAULT_AUTO_SPEAK_SPANISH = False
DEFAULT_STORY_READING_SPEED = 3
DEFAULT_STORY_PAUSE_AMOUNT = 5
STORY_READING_SPEED_LETTERS_PER_SECOND = {
    1: 28,
    2: 24,
    3: 21,
    4: 18,
    5: 15,
}
STORY_READING_SPEED_PROCESSING_MULTIPLIER = {
    1: 0.35,
    2: 0.50,
    3: 0.65,
    4: 0.80,
    5: 1.00,
}
STORY_BASE_WORD_WEIGHT = 0.01
STORY_EXTRA_WORD_BONUS_SCALE = 0.34
STORY_EXTRA_WORD_THRESHOLD = 6
STORY_EXTRA_WORD_BONUS_EXPONENT = 1.5
STORY_HIGH_WORD_COUNT_BONUS_SCALE = 0.035
STORY_HIGH_WORD_COUNT_THRESHOLD = 8
STORY_HIGH_WORD_COUNT_BONUS_EXPONENT = 1.8
STORY_VERY_HIGH_WORD_COUNT_BONUS_SCALE = 0.003
STORY_VERY_HIGH_WORD_COUNT_THRESHOLD = 10
STORY_VERY_HIGH_WORD_COUNT_BONUS_EXPONENT = 2.2
STORY_PROCESSING_BUFFER_SECONDS = 0.06
STORY_MIN_PAUSE_SECONDS = 0.5
STORY_LEVEL3_EXPONENT = 2


def default_person_prefs():
    return {
        "theme": DEFAULT_THEME,
        "direction_mode": DEFAULT_DIRECTION_MODE,
        "speech_speed": DEFAULT_SPEECH_SPEED,
        "show_hints": DEFAULT_SHOW_HINTS,
        "auto_speak_spanish": DEFAULT_AUTO_SPEAK_SPANISH,
        "story_reading_speed": DEFAULT_STORY_READING_SPEED,
        "story_pause_amount": DEFAULT_STORY_PAUSE_AMOUNT,
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
    auto_speak_spanish = pref_data.get("auto_speak_spanish", fallback["auto_speak_spanish"])
    if not isinstance(auto_speak_spanish, bool):
        auto_speak_spanish = fallback["auto_speak_spanish"]
    story_reading_speed = pref_data.get("story_reading_speed", fallback["story_reading_speed"])
    if story_reading_speed not in {1, 2, 3, 4, 5}:
        story_reading_speed = fallback["story_reading_speed"]
    legacy_story_pause = pref_data.get("story_pause_seconds", fallback["story_pause_amount"])
    story_pause_amount = pref_data.get("story_pause_amount", legacy_story_pause)
    if story_pause_amount not in {1, 2, 3, 4, 5}:
        story_pause_amount = fallback["story_pause_amount"]
    return {
        "theme": theme,
        "direction_mode": direction_mode,
        "speech_speed": speech_speed,
        "show_hints": show_hints,
        "auto_speak_spanish": auto_speak_spanish,
        "story_reading_speed": story_reading_speed,
        "story_pause_amount": story_pause_amount,
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


def load_progress_data():
    empty = {person: {} for person in PERSON_LABELS}
    try:
        with open(PROGRESS_FILE, encoding="utf-8") as f:
            raw = json.load(f)
    except Exception:
        return empty

    progress_data = {person: {} for person in PERSON_LABELS}
    for person in PERSON_LABELS:
        person_entries = raw.get(person, {})
        if not isinstance(person_entries, dict):
            continue
        for filename, card_ids in person_entries.items():
            if isinstance(card_ids, dict):
                card_ids = card_ids.keys()
            if not isinstance(card_ids, list) and not hasattr(card_ids, "__iter__"):
                continue
            normalized_ids = []
            seen_ids = set()
            for card_id in card_ids:
                normalized_id = normalize_card_id(card_id)
                if not normalized_id or normalized_id in seen_ids:
                    continue
                seen_ids.add(normalized_id)
                normalized_ids.append(normalized_id)
            if normalized_ids:
                progress_data[person][filename] = sorted(normalized_ids, key=completion_sort_key)
    return progress_data


def save_progress_data(progress_data):
    try:
        with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
            serializable = {
                person: {
                    filename: sorted(card_ids, key=completion_sort_key)
                    for filename, card_ids in progress_data.get(person, {}).items()
                    if card_ids
                }
                for person in PERSON_LABELS
            }
            json.dump(serializable, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def completed_ids_for(person, filename):
    return set(st.session_state.progress_data.get(person, {}).get(filename, []))


def mark_card_completed(person, filename, card_id):
    if not card_id:
        return
    person_progress = st.session_state.progress_data.setdefault(person, {})
    deck_progress = set(person_progress.get(filename, []))
    if card_id in deck_progress:
        return
    deck_progress.add(card_id)
    person_progress[filename] = sorted(deck_progress, key=completion_sort_key)
    save_progress_data(st.session_state.progress_data)


def clear_deck_progress(person, filename):
    person_progress = st.session_state.progress_data.setdefault(person, {})
    if filename in person_progress:
        del person_progress[filename]
        save_progress_data(st.session_state.progress_data)


def review_add_back_count(completed_count):
    if completed_count <= 0:
        return 0
    return max(1, int(completed_count * 0.25 + 0.5))


def restore_completed_cards(person, filename, restore_count):
    if restore_count <= 0:
        return 0

    deck_data = load_regular_deck(filename)
    valid_ids = {card["id"] for card in deck_data["cards"] if card.get("id")}
    completed_ids = list(completed_ids_for(person, filename) & valid_ids)
    restore_count = min(restore_count, len(completed_ids))
    if restore_count <= 0:
        return 0

    restored_ids = set(random.sample(completed_ids, restore_count))
    person_progress = st.session_state.progress_data.setdefault(person, {})
    remaining_completed_ids = [
        card_id
        for card_id in person_progress.get(filename, [])
        if card_id not in restored_ids
    ]

    if remaining_completed_ids:
        person_progress[filename] = remaining_completed_ids
    elif filename in person_progress:
        del person_progress[filename]

    save_progress_data(st.session_state.progress_data)
    return restore_count


def deck_progress_stats(filename, person):
    deck_data = load_regular_deck(filename)
    cards = deck_data["cards"]
    total_cards = len(cards)

    if not deck_data["supports_completion"]:
        return {
            "supported": False,
            "total": total_cards,
            "completed": 0,
            "remaining": total_cards,
        }

    valid_ids = {card["id"] for card in cards if card.get("id")}
    completed = len(completed_ids_for(person, filename) & valid_ids)
    return {
        "supported": True,
        "total": total_cards,
        "completed": completed,
        "remaining": max(total_cards - completed, 0),
    }


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
        "auto_speak_spanish": st.session_state.auto_speak_spanish,
        "story_reading_speed": st.session_state.story_reading_speed,
        "story_pause_amount": st.session_state.story_pause_amount,
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
progress_data = load_progress_data()
active_person = prefs["active_person"]
active_person_prefs = prefs["person_settings"][active_person]

defaults = {
    "theme":          active_person_prefs["theme"],
    "menu_open":      False,
    "direction_mode": active_person_prefs["direction_mode"],
    "speech_speed":   active_person_prefs["speech_speed"],
    "show_hints":     active_person_prefs["show_hints"],
    "auto_speak_spanish": active_person_prefs["auto_speak_spanish"],
    "auto_speak_spanish_generation": 0,
    "story_reading_speed": active_person_prefs["story_reading_speed"],
    "story_pause_amount": active_person_prefs["story_pause_amount"],
    "active_person":  active_person,
    "person_radio":   active_person,
    "person_selector_visible": True,
    "person_settings": prefs["person_settings"],
    "review_data":    review_data,
    "progress_data":  progress_data,
    "selected_csv":   None,
    "study_mode":     None,
    "cards":          [],
    "order":          [],
    "index":          0,
    "show_answer":    False,
    "regular_auto_mode": False,
    "regular_auto_repeat_spanish": False,
    "regular_auto_generation": 0,
    "regular_auto_mode_checkbox": False,
    "regular_auto_repeat_checkbox": False,
    "direction":      direction_for_mode(active_person_prefs["direction_mode"]),
    "quit_requested": False,
    "final_exit":     False,
    "loaded_csv":     None,
    "score_actions":  0,
    "score_correct":  0,
    "score_repeat":   0,
    "erase_review_confirm": False,
    "delete_review_confirm_key": None,
    "story_playback_mode": "continuous",
    "story_translation_on": True,
    "story_audio_on": True,
    "story_random_on": False,
    "story_started": False,
    "story_running": False,
    "story_finished": False,
    "story_run_token": 0,
    "story_resume_next": False,
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
    st.session_state.story_reading_speed_radio = st.session_state.story_reading_speed
    st.session_state.story_pause_amount_radio = st.session_state.story_pause_amount


def store_active_person_prefs():
    st.session_state.person_settings[st.session_state.active_person] = {
        "theme": st.session_state.theme,
        "direction_mode": st.session_state.direction_mode,
        "speech_speed": st.session_state.speech_speed,
        "show_hints": st.session_state.show_hints,
        "auto_speak_spanish": st.session_state.auto_speak_spanish,
        "story_reading_speed": st.session_state.story_reading_speed,
        "story_pause_amount": st.session_state.story_pause_amount,
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
            var closeButton = doc.querySelector('.st-key-hamburger_wrap button');

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
    st.session_state.auto_speak_spanish = person_prefs["auto_speak_spanish"]
    st.session_state.story_reading_speed = person_prefs["story_reading_speed"]
    st.session_state.story_pause_amount = person_prefs["story_pause_amount"]
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
    st.session_state.study_mode = None
    st.session_state.loaded_csv = None
    st.session_state.cards = []
    st.session_state.order = []
    st.session_state.index = 0
    st.session_state.show_answer = False
    st.session_state["regular_auto_mode"] = False
    st.session_state["regular_auto_repeat_spanish"] = False
    st.session_state["regular_auto_generation"] += 1
    st.session_state["regular_auto_mode_checkbox"] = False
    st.session_state["regular_auto_repeat_checkbox"] = False
    st.session_state.quit_requested = False
    st.session_state.final_exit = False
    st.session_state["score_actions"] = 0
    st.session_state["score_correct"] = 0
    st.session_state["score_repeat"] = 0
    st.session_state.delete_review_confirm_key = None
    st.session_state.story_random_on = False
    st.session_state.story_started = False
    st.session_state.story_running = False
    st.session_state.story_finished = False
    st.session_state.story_run_token = 0
    st.session_state.story_resume_next = False


def rebuild_story_order():
    st.session_state.order = list(range(len(st.session_state.cards)))
    if st.session_state.story_random_on:
        random.shuffle(st.session_state.order)


def reset_story_playback():
    st.session_state.index = 0
    st.session_state.story_started = False
    st.session_state.story_running = False
    st.session_state.story_finished = False
    st.session_state.story_run_token = 0
    st.session_state.story_resume_next = False


def finish_story():
    if not st.session_state.cards:
        reset_story_playback()
        return
    st.session_state.index = max(len(st.session_state.cards) - 1, 0)
    st.session_state.story_started = True
    st.session_state.story_running = False
    st.session_state.story_finished = True
    st.session_state.story_resume_next = False


def repeat_story():
    rebuild_story_order()
    reset_story_playback()
    start_story()


def end_story_to_final_screen():
    go_back_to_deck_picker()
    st.session_state.final_exit = True


def activate_deck(deck_value):
    reset_study_state(reset_selected=False)
    st.session_state.selected_csv = deck_value
    st.session_state.study_mode = "story" if is_story_deck(deck_value) else ("all" if is_review_deck(deck_value) else None)
    st.session_state.person_selector_visible = False
    st.session_state.direction = effective_direction(deck_value)


def go_back_to_deck_picker():
    st.session_state.menu_open = False
    st.session_state.erase_review_confirm = False
    reset_study_state(reset_selected=True)


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
.st-key-storypause_wrap div[data-testid="stButton"] > button {{
    background-color: #ffd9b0 !important;
    border-color: #d97706 !important;
    color: #8a3b00 !important;
}}
.st-key-storystop_wrap div[data-testid="stButton"] > button {{
    background-color: {BUTTON_COLORS['red']['bg']} !important;
    border-color: {BUTTON_COLORS['red']['border']} !important;
    color: {BUTTON_COLORS['red']['fg']} !important;
}}
.st-key-storystart_wrap div[data-testid="stButton"] > button {{
    background-color: {BUTTON_COLORS['green']['bg']} !important;
    border-color: {BUTTON_COLORS['green']['border']} !important;
    color: {BUTTON_COLORS['green']['fg']} !important;
}}
.st-key-storyrepeat_wrap div[data-testid="stButton"] > button {{
    background-color: {BUTTON_COLORS['yellow']['bg']} !important;
    border-color: {BUTTON_COLORS['yellow']['border']} !important;
    color: {BUTTON_COLORS['yellow']['fg']} !important;
}}
.st-key-storynext_wrap div[data-testid="stButton"] > button {{
    background-color: {BUTTON_COLORS['green']['bg']} !important;
    border-color: {BUTTON_COLORS['green']['border']} !important;
    color: {BUTTON_COLORS['green']['fg']} !important;
}}
.st-key-storynew_wrap div[data-testid="stButton"] > button {{
    background-color: {BUTTON_COLORS['blue']['bg']} !important;
    border-color: {BUTTON_COLORS['blue']['border']} !important;
    color: {BUTTON_COLORS['blue']['fg']} !important;
}}
.st-key-storyend_wrap div[data-testid="stButton"] > button {{
    background-color: {BUTTON_COLORS['red']['bg']} !important;
    border-color: {BUTTON_COLORS['red']['border']} !important;
    color: {BUTTON_COLORS['red']['fg']} !important;
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
.st-key-autospeak_on_wrap div[data-testid="stButton"] > button {{
    background-color: {BUTTON_COLORS['blue']['bg']} !important;
    border-color: {BUTTON_COLORS['blue']['border']} !important;
    color: {BUTTON_COLORS['blue']['fg']} !important;
}}
.st-key-autospeak_off_wrap div[data-testid="stButton"] > button {{
    background-color: color-mix(in srgb, {BUTTON_COLORS['blue']['bg']} 58%, {t['bg']} 42%) !important;
    border-color: {BUTTON_COLORS['blue']['border']} !important;
    color: color-mix(in srgb, {BUTTON_COLORS['blue']['fg']} 78%, white 22%) !important;
}}
.st-key-autospeak_on_wrap div[data-testid="stButton"] > button,
.st-key-autospeak_off_wrap div[data-testid="stButton"] > button {{
    width: 3.6rem !important;
    min-height: 3.2rem !important;
    padding: 0.42rem 0.2rem !important;
    font-size: 0.94rem !important;
    letter-spacing: 0 !important;
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
.st-key-study_mode_picker_wrap div[data-testid="stButton"] > button:disabled {{
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
.st-key-storyadvance_hidden_wrap {{
    position: absolute !important;
    width: 1px !important;
    height: 1px !important;
    margin: 0 !important;
    padding: 0 !important;
    overflow: hidden !important;
    clip-path: inset(50%) !important;
    opacity: 0 !important;
    pointer-events: none !important;
}}
.st-key-storyfinish_hidden_wrap {{
    position: absolute !important;
    width: 1px !important;
    height: 1px !important;
    margin: 0 !important;
    padding: 0 !important;
    overflow: hidden !important;
    clip-path: inset(50%) !important;
    opacity: 0 !important;
    pointer-events: none !important;
}}
.st-key-storyresumenext_hidden_wrap {{
    position: absolute !important;
    width: 1px !important;
    height: 1px !important;
    margin: 0 !important;
    padding: 0 !important;
    overflow: hidden !important;
    clip-path: inset(50%) !important;
    opacity: 0 !important;
    pointer-events: none !important;
}}
.st-key-regularautoreveal_hidden_wrap {{
    position: absolute !important;
    width: 1px !important;
    height: 1px !important;
    margin: 0 !important;
    padding: 0 !important;
    overflow: hidden !important;
    clip-path: inset(50%) !important;
    opacity: 0 !important;
    pointer-events: none !important;
}}
.st-key-regularautoadvance_hidden_wrap {{
    position: absolute !important;
    width: 1px !important;
    height: 1px !important;
    margin: 0 !important;
    padding: 0 !important;
    overflow: hidden !important;
    clip-path: inset(50%) !important;
    opacity: 0 !important;
    pointer-events: none !important;
}}
.st-key-regular_auto_controls_wrap {{
    margin-bottom: 0.35rem !important;
}}
.st-key-regular_auto_controls_wrap [data-testid="stHorizontalBlock"] {{
    display: flex !important;
    flex-wrap: nowrap !important;
    align-items: center !important;
    gap: 0.55rem !important;
}}
.st-key-regular_auto_controls_wrap [data-testid="stColumn"] {{
    min-width: 0 !important;
    padding: 0 !important;
}}
.st-key-regular_auto_controls_wrap [data-testid="stCheckbox"] {{
    margin: 0 !important;
}}
.st-key-regular_auto_controls_wrap [data-testid="stCheckbox"] label {{
    white-space: nowrap !important;
}}
.regular-auto-controls-spacer {{
    min-height: 1.9rem;
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
    margin-top: 0.18rem;
    font-size: 0.78rem;
    font-weight: 500;
    color: {t['muted']};
    letter-spacing: 0.08em;
    text-transform: uppercase;
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
.menu-field-label {{
    font-size: 0.95rem;
    font-weight: 400;
    color: {t['fg']};
    margin: 0.35rem 0 0.2rem 0;
    line-height: 1.2;
}}
.st-key-erase_review_wrap,
.st-key-erase_review_confirm_wrap {{
    margin-top: 0.95rem !important;
}}
.st-key-clear_erase_review_confirm_wrap {{
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
.st-key-deckstrip_row_wrap [data-testid="stHorizontalBlock"] {{
    display: flex !important;
    align-items: center !important;
    gap: 0.45rem !important;
    flex-wrap: nowrap !important;
}}
.st-key-deckstrip_row_wrap [data-testid="stColumn"] {{
    min-width: 0 !important;
}}
.st-key-deckstrip_row_wrap [data-testid="stColumn"]:first-child {{
    flex: 1 1 auto !important;
}}
.st-key-deckstrip_row_wrap [data-testid="stColumn"]:last-child {{
    flex: 0 0 auto !important;
    width: auto !important;
}}
.st-key-changedeck_wrap div[data-testid="stButton"] > button {{
    min-height: 1.65rem !important;
    width: 1.9rem !important;
    padding: 0 !important;
    font-size: 1rem !important;
    line-height: 1 !important;
    border-radius: 999px !important;
    background-color: {t['bg']} !important;
    border-color: {t['border']} !important;
    color: {t['muted']} !important;
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
.fc-block,
.story-display-block {{
    border: 1px solid {t['border']};
    border-radius: 1rem;
    padding: 0.6rem 0.9rem;
    margin-bottom: 0.5rem;
    background: {t['bg']};
    cursor: pointer;
    user-select: none;
    -webkit-user-select: none;
    transition: border-color 0.15s ease;
    position: relative;
}}
.fc-block:active,
.story-display-block:active {{ border-color: {t['accent']}; }}
.fc-block-empty,
.story-display-block-empty {{ opacity: 0.35; }}
.story-box-shield {{
    position: absolute;
    inset: 0;
    z-index: 2;
    background: transparent;
    border-radius: inherit;
}}
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
    white-space: normal;
    overflow-wrap: anywhere;
    word-break: break-word;
    line-height: 1.05;
}}
.fc-inline-hint {{
    font-size: 0.72em;
    font-weight: 400;
    color: color-mix(in srgb, {t['muted']} 65%, {t['accent']} 35%);
    white-space: normal;
    overflow-wrap: anywhere;
    word-break: break-word;
    line-height: 1.05;
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
.story-title-block {{
    padding: 0.5rem 0 0.22rem 0;
}}
.story-option-row {{
    font-size: 0.95rem;
    font-weight: 500;
    color: {t['fg']};
    padding-top: 0;
    line-height: 1.05;
}}
.st-key-storyoptions_stack_wrap [data-testid="stVerticalBlock"] {{
    gap: 0 !important;
}}
.st-key-storyoptions_stack_wrap [data-testid="stVerticalBlock"] > * {{
    margin-bottom: 0 !important;
}}
.st-key-storyoptions_stack_wrap [data-testid="stElementContainer"] {{
    margin: 0 !important;
}}
.st-key-storyplayback_row_wrap,
.st-key-storytransaudio_row_wrap {{
    margin: 0 !important;
}}
.st-key-storyplayback_row_wrap [data-testid="stHorizontalBlock"],
.st-key-storytransaudio_row_wrap [data-testid="stHorizontalBlock"] {{
    align-items: center !important;
    flex-wrap: nowrap !important;
    gap: 0.25rem !important;
    margin: 0 !important;
}}
.st-key-storyplayback_row_wrap [data-testid="stColumn"],
.st-key-storytransaudio_row_wrap [data-testid="stColumn"] {{
    padding: 0 !important;
}}
.st-key-storyplayback_row_wrap [data-testid="stColumn"] > div,
.st-key-storytransaudio_row_wrap [data-testid="stColumn"] > div {{
    padding: 0 !important;
}}
.st-key-storyplayback_row_wrap [data-testid="stColumn"]:first-child {{
    flex: 0 0 8.8rem !important;
}}
.st-key-storyplayback_row_wrap [data-testid="stColumn"]:last-child {{
    flex: 1 1 auto !important;
}}
.st-key-storyplayback_row_wrap .story-option-row {{
    white-space: nowrap !important;
}}
.st-key-storyplayback_row_wrap [data-testid="stRadio"] > div,
.st-key-storytransaudio_row_wrap [data-testid="stRadio"] > div {{
    flex-direction: row !important;
    justify-content: flex-start !important;
    gap: 0.62rem !important;
}}
.st-key-storyplayback_row_wrap [data-testid="stRadio"] label,
.st-key-storytransaudio_row_wrap [data-testid="stRadio"] label {{
    margin-bottom: 0 !important;
}}
.st-key-storyplayback_row_wrap [data-testid="stMarkdownContainer"] p,
.st-key-storytransaudio_row_wrap [data-testid="stMarkdownContainer"] p {{
    margin: 0 !important;
}}
.st-key-storyplayback_row_wrap [data-testid="stRadio"],
.st-key-storytransaudio_row_wrap [data-testid="stRadio"] {{
    margin: 0 !important;
    padding: 0 !important;
}}
.st-key-storyplayback_row_wrap [data-testid="stRadio"] > label,
.st-key-storytransaudio_row_wrap [data-testid="stRadio"] > label {{
    display: none !important;
}}
.st-key-storyplayback_row_wrap [data-testid="stRadio"] div[role="radiogroup"],
.st-key-storytransaudio_row_wrap [data-testid="stRadio"] div[role="radiogroup"] {{
    display: flex !important;
    flex-wrap: nowrap !important;
    align-items: center !important;
    margin: 0 !important;
    padding: 0 !important;
}}
.st-key-storyplayback_row_wrap [data-testid="stRadio"] div[role="radiogroup"] > label {{
    white-space: nowrap !important;
}}
.st-key-storycontrol_row_wrap [data-testid="stHorizontalBlock"] {{
    display: flex !important;
    flex-direction: row !important;
    flex-wrap: nowrap !important;
    align-items: center !important;
    justify-content: flex-start !important;
    gap: 0.5rem !important;
    width: 100% !important;
}}
.st-key-storycontrol_row_wrap [data-testid="stColumn"] {{
    flex: 0 0 calc((100% - 1rem) / 3) !important;
    width: calc((100% - 1rem) / 3) !important;
    min-width: 0 !important;
    max-width: none !important;
    padding: 0 !important;
}}
.st-key-storycontrol_row_wrap [data-testid="stColumn"] > div,
.st-key-storycontrol_row_wrap div[data-testid="stButton"],
.st-key-storycontrol_row_wrap div[data-testid="stButton"] > div {{
    width: 100% !important;
}}
.st-key-storycontrol_row_wrap div[data-testid="stButton"] > button {{
    width: 100% !important;
    min-height: 2.9rem !important;
    font-size: 1.05rem !important;
    padding-left: 0.4rem !important;
    padding-right: 0.4rem !important;
}}
.story-control-spacer {{
    width: 100%;
    min-height: 2.9rem;
}}
.story-progress {{
    margin: 0.18rem 0 0.42rem 0;
}}
.story-progress-head {{
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    margin-bottom: 0.22rem;
}}
.story-progress-label {{
    font-size: 0.62rem;
    font-weight: 600;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: {t['muted']};
}}
.story-progress-value {{
    font-size: 0.8rem;
    font-weight: 600;
    color: {t['fg']};
    white-space: pre;
}}
.story-progress-track {{
    height: 0.22rem;
    border-radius: 999px;
    background: color-mix(in srgb, {t['border']} 65%, transparent 35%);
    overflow: hidden;
}}
.story-progress-fill {{
    height: 100%;
    background: {t['accent']};
    border-radius: 999px;
}}
.story-pause-readout {{
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    margin: 0.06rem 0 0.42rem 0;
}}
.story-pause-readout-label {{
    font-size: 0.62rem;
    font-weight: 600;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: {t['muted']};
}}
.story-pause-readout-value {{
    font-size: 0.8rem;
    font-weight: 600;
    color: {t['fg']};
}}
.soft-divider {{
    border: none; border-top: 1px solid {t['border']}; margin: 0.6rem 0;
}}

/* ---- Responsive deck picker ---- */
.st-key-mobile_deck_picker_wrap {{
    display: none;
}}
@media (max-width: 767px) {{
    .title-row {{
        padding: 0.15rem 0 0.08rem 0 !important;
    }}
    .title-main {{
        line-height: 0.96 !important;
    }}
    .title-sub {{
        margin-top: 0.08rem !important;
    }}
    .st-key-person_radio_wrap {{
        margin-top: -0.08rem !important;
        margin-bottom: 0.12rem !important;
    }}
    .st-key-person_radio_wrap [data-testid="stRadio"] {{
        margin: 0 !important;
        padding: 0 !important;
    }}
    .st-key-person_radio_wrap [data-testid="stRadio"] > div {{
        margin: 0 !important;
        padding: 0 !important;
    }}
    .st-key-person_radio_wrap div[role="radiogroup"] {{
        margin: 0 !important;
        padding: 0 !important;
    }}
    .st-key-desktop_deck_picker_wrap {{
        display: none !important;
    }}
    .st-key-mobile_deck_picker_wrap {{
        display: block !important;
    }}
    .mobile-deck-picker-label {{
        display: block !important;
        margin-top: -0.04rem !important;
        margin-bottom: 0.40rem !important;
    }}
    [class*="st-key-mobile_deck_entry_"] [data-testid="stButton"] > button {{
        display: flex !important;
        align-items: center !important;
        gap: 0 !important;
        padding-left: 0 !important;
        font-size: 0.86rem !important;
    }}
    [class*="st-key-mobile_deck_entry_"] [data-testid="stButton"] > button::before {{
        display: inline-block !important;
        flex: 0 0 0.82rem !important;
        width: 0.82rem !important;
        text-align: left !important;
        font-size: 0.98rem !important;
        line-height: 1 !important;
        margin-right: 0.42rem !important;
    }}
    [class*="st-key-mobile_deck_entry_"] [data-testid="stButton"] > button > div,
    [class*="st-key-mobile_deck_entry_"] [data-testid="stButton"] > button p {{
        flex: 1 1 auto !important;
        font-size: 0.86rem !important;
    }}
    [class*="st-key-mobile_deck_entry_review_"] [data-testid="stButton"] > button::before {{
        content: '⭐';
    }}
    [class*="st-key-mobile_deck_entry_story_"] [data-testid="stButton"] > button::before {{
        content: '📖';
    }}
    [class*="st-key-mobile_deck_entry_untouched_"] [data-testid="stButton"] > button::before {{
        content: '•';
        color: #8d98a3 !important;
    }}
    [class*="st-key-mobile_deck_entry_in_progress_"] [data-testid="stButton"] > button::before {{
        content: '●';
        color: #f2c94c !important;
    }}
    [class*="st-key-mobile_deck_entry_complete_"] [data-testid="stButton"] > button::before {{
        content: '✓';
        color: {t['accent']} !important;
        font-weight: 700 !important;
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
    .st-key-mobile_deck_picker_wrap [class*="st-key-mobile_deck_entry_"] [data-testid="stButton"] > button {{
        display: grid !important;
        grid-template-columns: 1.70rem minmax(0, 1fr) !important;
        column-gap: 0 !important;
        align-items: center !important;
        padding-left: 0 !important;
        padding-right: 0.45rem !important;
        font-size: 0.91rem !important;
    }}
    .st-key-mobile_deck_picker_wrap [class*="st-key-mobile_deck_entry_"] [data-testid="stButton"] > button::before {{
        display: block !important;
        width: 1.70rem !important;
        margin-left: 0 !important;
        margin-right: 0 !important;
        justify-self: start !important;
        padding-left: 0.02rem !important;
        text-align: left !important;
        white-space: nowrap !important;
    }}
    .st-key-mobile_deck_picker_wrap [class*="st-key-mobile_deck_entry_"] [data-testid="stButton"] > button > div {{
        width: auto !important;
        min-width: 0 !important;
        margin-left: 0 !important;
    }}
    .st-key-mobile_deck_picker_wrap [class*="st-key-mobile_deck_entry_"] [data-testid="stButton"] > button p {{
        font-size: 0.91rem !important;
    }}
    .st-key-mobile_deck_picker_wrap [class*="st-key-mobile_deck_entry_story_"] [data-testid="stButton"] > button::before {{
        font-size: 1.10rem !important;
    }}
    .st-key-mobile_deck_picker_wrap [data-testid="stVerticalBlock"] > * {{
        margin-bottom: 0 !important;
    }}
    .mobile-deck-divider {{
        border-top: 1px solid {t['border']};
        margin: 0.32rem 0 0.28rem 0;
        opacity: 0.85;
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

    /* ---- Phone: Translate + Audio + Random checkboxes ---- */
    .st-key-storytransaudio_row_wrap {{
        height: 2.2rem !important;
        overflow: hidden !important;
    }}
    .st-key-storyplayback_row_wrap [data-testid="stHorizontalBlock"] {{
        display: flex !important;
        flex-wrap: nowrap !important;
        align-items: center !important;
        gap: 0.12rem !important;
    }}
    .st-key-storyplayback_row_wrap [data-testid="stColumn"]:nth-child(1) {{
        flex: 0 0 7.45rem !important;
        min-width: 7.45rem !important;
    }}
    .st-key-storyplayback_row_wrap [data-testid="stColumn"]:nth-child(2) {{
        flex: 1 1 auto !important;
        min-width: 0 !important;
    }}
    .st-key-storyplayback_row_wrap .story-option-row {{
        font-size: 0.9rem !important;
        position: relative !important;
        top: -0.28rem !important;
        white-space: nowrap !important;
    }}
    .st-key-storyplayback_row_wrap [data-testid="stRadio"] div[role="radiogroup"] {{
        gap: 0.42rem !important;
        white-space: nowrap !important;
    }}
    .st-key-storyplayback_row_wrap [data-testid="stRadio"] div[role="radiogroup"] > label {{
        white-space: nowrap !important;
    }}

    .st-key-storytransaudio_row_wrap [data-testid="stHorizontalBlock"] {{
        gap: 0 !important;
        align-items: center !important;
        height: 2.2rem !important;
    }}
    .st-key-storytransaudio_row_wrap [data-testid="stColumn"] {{
        min-width: 0 !important;
        flex: 0 0 auto !important;
        width: auto !important;
    }}
    .st-key-storytransaudio_row_wrap [data-testid="stColumn"] > div {{
        display: flex !important;
        align-items: center !important;
    }}
    .st-key-storytransaudio_row_wrap .story-option-row {{
        position: relative !important;
        top: -0.45rem !important;
    }}
    .st-key-storytransaudio_row_wrap [data-testid="stColumn"]:nth-child(1) {{
        flex: 0 0 auto !important;
        padding-right: 0.15rem !important;
    }}
    .st-key-storytransaudio_row_wrap [data-testid="stColumn"]:nth-child(2) {{
        flex: 0 0 2.0rem !important;
        padding-right: 0 !important;
        margin-right: 2ch !important;
    }}
    .st-key-storytransaudio_row_wrap [data-testid="stColumn"]:nth-child(3) {{
        flex: 0 0 auto !important;
        padding-right: 0.15rem !important;
    }}
    .st-key-storytransaudio_row_wrap [data-testid="stColumn"]:nth-child(4) {{
        flex: 0 0 2.0rem !important;
        padding-right: 0 !important;
        margin-right: 2ch !important;
    }}
    .st-key-storytransaudio_row_wrap [data-testid="stColumn"]:nth-child(5) {{
        flex: 0 0 auto !important;
        padding-right: 0.15rem !important;
    }}
    .st-key-storytransaudio_row_wrap [data-testid="stColumn"]:nth-child(6) {{
        flex: 0 0 2.0rem !important;
    }}
    .st-key-storytransaudio_row_wrap [data-testid="stRadio"] div[role="radiogroup"] {{
        position: relative !important;
        min-height: 1.9rem !important;
        min-width: 2.0rem !important;
        width: 2.0rem !important;
        display: block !important;
    }}
    .st-key-storytransaudio_row_wrap [data-testid="stRadio"] div[role="radiogroup"] > label {{
        position: absolute !important;
        top: 0 !important;
        left: 0 !important;
        width: 2.0rem !important;
        height: 1.9rem !important;
        margin: 0 !important;
        padding: 0 !important;
        opacity: 0 !important;
        cursor: pointer !important;
    }}
    .st-key-storytransaudio_row_wrap [data-testid="stRadio"] div[role="radiogroup"] > label:has(input:checked) {{
        z-index: 1 !important;
    }}
    .st-key-storytransaudio_row_wrap [data-testid="stRadio"] div[role="radiogroup"] > label:has(input:not(:checked)) {{
        z-index: 2 !important;
    }}
    .st-key-storytransaudio_row_wrap [data-testid="stRadio"] div[role="radiogroup"]::before {{
        content: '';
        position: absolute;
        top: 0.15rem;
        left: 0.2rem;
        width: 1.5rem;
        height: 1.5rem;
        border: 2px solid {t['border']};
        border-radius: 4px;
        pointer-events: none;
        box-sizing: border-box;
    }}
    .st-key-storytransaudio_row_wrap [data-testid="stRadio"] div[role="radiogroup"]:has(> label:first-child input:checked)::after {{
        content: '\\2715';
        position: absolute;
        top: 0.15rem;
        left: 0.2rem;
        width: 1.5rem;
        height: 1.5rem;
        font-size: 1.25rem;
        font-weight: 700;
        line-height: 1.45rem;
        text-align: center;
        color: {t['accent']};
        pointer-events: none;
    }}
    .st-key-regular_auto_controls_wrap [data-testid="stHorizontalBlock"] {{
        gap: 0.2rem !important;
    }}
    .st-key-regular_auto_controls_wrap [data-testid="stCheckbox"] label p {{
        font-size: 0.92rem !important;
    }}
    .st-key-regular_auto_controls_wrap [data-testid="stColumn"]:first-child {{
        flex: 0 0 47% !important;
    }}
    .st-key-regular_auto_controls_wrap [data-testid="stColumn"]:last-child {{
        flex: 0 0 53% !important;
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


def render_mobile_deck_picker_height_fix():
    components.html(
        """
        <script>
        (function() {
            var parentWindow = window.parent;
            var doc = parentWindow.document;

            function isPhoneLayout() {
                var nav = parentWindow.navigator || window.navigator;
                var ua = nav && nav.userAgent ? nav.userAgent : '';
                var hasTouch = !!(('ontouchstart' in parentWindow) || (nav && nav.maxTouchPoints > 0));
                var narrow = !!(parentWindow.matchMedia && parentWindow.matchMedia('(max-width: 767px)').matches);
                return narrow && (hasTouch || /iPhone|Android|Mobile|iPad|iPod/i.test(ua));
            }

            if (!isPhoneLayout()) {
                return;
            }

            function applyHeight() {
                var wrap = doc.querySelector('.st-key-mobile_deck_picker_wrap');
                if (!wrap) {
                    return false;
                }

                var candidates = Array.from(wrap.querySelectorAll('div')).filter(function(el) {
                    var style = parentWindow.getComputedStyle(el);
                    var overflowY = style.overflowY;
                    return (overflowY === 'auto' || overflowY === 'scroll' || el.scrollHeight > el.clientHeight + 8)
                        && !el.querySelector('.mobile-deck-picker-label')
                        && el.clientHeight >= 180;
                });

                if (!candidates.length) {
                    return false;
                }

                candidates.sort(function(a, b) {
                    if (a.clientHeight !== b.clientHeight) {
                        return a.clientHeight - b.clientHeight;
                    }
                    return a.querySelectorAll('div').length - b.querySelectorAll('div').length;
                });

                var target = candidates[0];
                target.style.height = '70svh';
                target.style.maxHeight = '70svh';
                target.style.minHeight = '70svh';
                target.style.overflowY = 'auto';
                target.style.marginTop = '0.38rem';
                return true;
            }

            if (applyHeight()) {
                return;
            }

            var attempts = 0;
            var timer = parentWindow.setInterval(function() {
                attempts += 1;
                if (applyHeight() || attempts >= 20) {
                    parentWindow.clearInterval(timer);
                }
            }, 120);
        })();
        </script>
        """,
        height=0,
    )

# ------------------------------------------------------------------------
# CARD LOGIC
# ------------------------------------------------------------------------

def current_card_index():
    return st.session_state.order[st.session_state.index]

def reveal_answer():
    st.session_state.show_answer = True


def advance_auto_card():
    advance_card(schedule_current=False)


def mark_correct():
    idx = current_card_index()
    card = st.session_state.cards[idx]
    st.session_state.delete_review_confirm_key = None
    card["scored"] = True
    st.session_state["score_actions"] += 1
    st.session_state["score_correct"] += 1
    if is_review_deck(st.session_state.selected_csv):
        review_person = review_deck_person(st.session_state.selected_csv)
        decrement_review_item(review_person, card["word"], card["answer"])
        card["repeat_score"] = max(card["repeat_score"] - 1, 0)
        advance_card()
    else:
        if card.get("id"):
            mark_card_completed(st.session_state.active_person, st.session_state.selected_csv, card["id"])
        card["repeat_score"] = max(card["repeat_score"] - 1, 0)
        advance_card()


def mark_repeat():
    card = st.session_state.cards[current_card_index()]
    st.session_state.delete_review_confirm_key = None
    card["scored"] = True
    st.session_state["score_actions"] += 1
    st.session_state["score_repeat"] += 1
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


def story_pause_seconds_for_text(text):
    spanish_text = strip_spoken_text(text)
    words = re.findall(r"[A-Za-zÁÉÍÓÚáéíóúÑñÜü]+", spanish_text)
    word_count = len(words)
    letter_count = sum(len(word) for word in words)
    reading_speed_setting = st.session_state.story_reading_speed
    reading_speed = STORY_READING_SPEED_LETTERS_PER_SECOND.get(
        reading_speed_setting,
        STORY_READING_SPEED_LETTERS_PER_SECOND[DEFAULT_STORY_READING_SPEED],
    )
    processing_multiplier = STORY_READING_SPEED_PROCESSING_MULTIPLIER.get(
        reading_speed_setting,
        STORY_READING_SPEED_PROCESSING_MULTIPLIER[DEFAULT_STORY_READING_SPEED],
    )
    base_process_seconds = 0.0
    if letter_count > 0:
        base_process_seconds = letter_count / reading_speed
    extra_word_bonus_seconds = STORY_EXTRA_WORD_BONUS_SCALE * (
        max(word_count - STORY_EXTRA_WORD_THRESHOLD, 0)
        ** STORY_EXTRA_WORD_BONUS_EXPONENT
    )
    high_word_count_bonus_seconds = STORY_HIGH_WORD_COUNT_BONUS_SCALE * (
        max(word_count - STORY_HIGH_WORD_COUNT_THRESHOLD, 0)
        ** STORY_HIGH_WORD_COUNT_BONUS_EXPONENT
    )
    very_high_word_count_bonus_seconds = STORY_VERY_HIGH_WORD_COUNT_BONUS_SCALE * (
        max(word_count - STORY_VERY_HIGH_WORD_COUNT_THRESHOLD, 0)
        ** STORY_VERY_HIGH_WORD_COUNT_BONUS_EXPONENT
    )
    t_process = processing_multiplier * (
        base_process_seconds
        + STORY_BASE_WORD_WEIGHT * word_count
        + extra_word_bonus_seconds
        + high_word_count_bonus_seconds
        + very_high_word_count_bonus_seconds
        + STORY_PROCESSING_BUFFER_SECONDS
    )
    t5 = max(STORY_MIN_PAUSE_SECONDS, 2 * t_process)
    t4 = max(
        STORY_MIN_PAUSE_SECONDS,
        STORY_MIN_PAUSE_SECONDS + math.sqrt(0.5) * (t5 - STORY_MIN_PAUSE_SECONDS),
    )
    gap = max(t4 - STORY_MIN_PAUSE_SECONDS, 0.0)
    t3 = STORY_MIN_PAUSE_SECONDS + gap * ((2 / 3) ** STORY_LEVEL3_EXPONENT)
    t2 = (STORY_MIN_PAUSE_SECONDS + t3) / 2
    return {
        1: STORY_MIN_PAUSE_SECONDS,
        2: t2,
        3: t3,
        4: t4,
        5: t5,
    }.get(st.session_state.story_pause_amount, t3)


def story_pause_seconds():
    story_card = current_story_card()
    return story_pause_seconds_for_text(story_card["answer"])


def current_story_card():
    return st.session_state.cards[current_card_index()]


def advance_story_line():
    next_index = st.session_state.index + 1
    if next_index >= len(st.session_state.cards):
        finish_story()
        return
    st.session_state.index = next_index
    st.session_state.story_finished = False


def pause_story():
    st.session_state.story_started = True
    st.session_state.story_running = False
    st.session_state.story_finished = False
    st.session_state.story_resume_next = not st.session_state.story_audio_on


def start_story():
    if st.session_state.story_resume_next:
        st.session_state.story_resume_next = False
        advance_story_line()
        if st.session_state.selected_csv is None:
            return
    st.session_state.story_started = True
    st.session_state.story_running = True
    st.session_state.story_finished = False
    st.session_state.story_run_token += 1


def stop_story():
    go_back_to_deck_picker()


def mark_story_resume_next():
    st.session_state.story_resume_next = True


def story_box_event_attrs(is_clickable):
    if is_clickable:
        return ""
    swallow = "event.preventDefault(); event.stopPropagation(); if (event.stopImmediatePropagation) { event.stopImmediatePropagation(); } return false;"
    return (
        f' onclick="{swallow}"'
        f' onmousedown="{swallow}"'
        f' onmouseup="{swallow}"'
        f' onpointerdown="{swallow}"'
        f' onpointerup="{swallow}"'
        f' ontouchstart="{swallow}"'
        f' ontouchend="{swallow}"'
    )


def story_box_shield_html(is_clickable):
    if is_clickable:
        return ""
    return '<div class="story-box-shield"' + story_box_event_attrs(False) + '></div>'


def render_story_pause_request_guard():
    story_index = st.session_state.index
    story_run_token = st.session_state.story_run_token
    components.html(
        f"""
        <script>
        (function() {{
            var doc = window.parent.document;
            var pauseState = {{
                runToken: {story_run_token},
                storyIndex: {story_index}
            }};

            function clearAdvanceRetryTimer() {{
                if (doc._storyAdvanceRetryTimer) {{
                    clearInterval(doc._storyAdvanceRetryTimer);
                    doc._storyAdvanceRetryTimer = null;
                }}
            }}

            function markPauseRequested() {{
                doc._storyPauseRequested = pauseState;
                if (doc._storyAutoAdvanceTimer) {{
                    clearTimeout(doc._storyAutoAdvanceTimer);
                    doc._storyAutoAdvanceTimer = null;
                }}
                clearAdvanceRetryTimer();
            }}

            function attach(selector, key) {{
                var button = doc.querySelector(selector);
                if (!button) return false;

                if (doc[key]) {{
                    ['pointerdown', 'mousedown', 'touchstart', 'click'].forEach(function(eventName) {{
                        button.removeEventListener(eventName, doc[key], true);
                    }});
                }}

                doc[key] = markPauseRequested;
                ['pointerdown', 'mousedown', 'touchstart', 'click'].forEach(function(eventName) {{
                    button.addEventListener(eventName, doc[key], true);
                }});
                return true;
            }}

            attach('.st-key-storypause_wrap button', '_storyPauseButtonHandler');
            attach('.st-key-storystop_wrap button', '_storyStopButtonHandler');
        }})();
        </script>
        """,
        height=0,
    )


def render_story_box_shield_handler():
    components.html(
        """
        <script>
        (function() {
            var doc = window.parent.document;
            var shields = doc.querySelectorAll('.story-box-shield');
            var eventNames = ['click', 'mousedown', 'mouseup', 'pointerdown', 'pointerup', 'touchstart', 'touchend'];

            function swallow(event) {
                event.preventDefault();
                event.stopPropagation();
                if (typeof event.stopImmediatePropagation === 'function') {
                    event.stopImmediatePropagation();
                }
                return false;
            }

            shields.forEach(function(shield) {
                shield.style.pointerEvents = 'auto';
                eventNames.forEach(function(eventName) {
                    shield.addEventListener(eventName, swallow, true);
                });
            });
        })();
        </script>
        """,
        height=0,
    )


def render_story_start_unlock_handler(
    story_lines,
    spanish_html_lines,
    translation_html_lines,
    pause_seconds_by_line,
    story_line_numbers,
    current_index,
    auto_advance=False,
    delay_seconds=0,
    running=False,
    resume_next=False,
):
    spoken_lines = [strip_spoken_text(text) for text in story_lines]
    speech_rate = speech_rate_value()
    delay_ms = max(int(delay_seconds * 1000), 0)
    story_key = st.session_state.selected_csv or ""
    story_run_token = st.session_state.story_run_token + (0 if running else 1)
    components.html(
        f"""
        <script>
        (function() {{
            var doc = window.parent.document;
            var parentWindow = window.parent;
            var synth = parentWindow.speechSynthesis || window.speechSynthesis;
            var eventNames = ['click', 'touchend'];
            var speechRate = {speech_rate};
            var config = {{
                storyKey: {json.dumps(story_key)},
                storyRunToken: {story_run_token},
                lines: {json.dumps(spoken_lines)},
                spanishHtmlLines: {json.dumps(spanish_html_lines)},
                translationHtmlLines: {json.dumps(translation_html_lines)},
                pauseSeconds: {json.dumps(pause_seconds_by_line)},
                lineNumbers: {json.dumps(story_line_numbers)},
                showLineNumbers: {str(st.session_state.story_random_on).lower()},
                serverIndex: {current_index},
                autoAdvance: {str(auto_advance).lower()},
                delayMs: {delay_ms},
                running: {str(running).lower()},
                resumeNext: {str(resume_next).lower()},
            }};

            function isPhoneStoryMode() {{
                var nav = parentWindow.navigator || window.navigator;
                var ua = nav && nav.userAgent ? nav.userAgent : '';
                var hasTouch = !!(('ontouchstart' in parentWindow) || (nav && nav.maxTouchPoints > 0));
                var narrow = !!(parentWindow.matchMedia && parentWindow.matchMedia('(max-width: 767px)').matches);
                return narrow && (hasTouch || /iPhone|Android|Mobile|iPad|iPod/i.test(ua));
            }}

            if (!doc || !synth || !isPhoneStoryMode()) return;

            function setDebug(message) {{
                var debugEl = doc.getElementById('story-mobile-debug');
                if (!debugEl) return;
                debugEl.style.display = 'block';
                debugEl.textContent = message;
            }}

            var controller = doc._storyMobileController || {{}};
            doc._storyMobileController = controller;

            function cancelTimers() {{
                if (controller.advanceTimer) {{
                    parentWindow.clearTimeout(controller.advanceTimer);
                    controller.advanceTimer = null;
                }}
                if (controller.advanceRetryTimer) {{
                    parentWindow.clearInterval(controller.advanceRetryTimer);
                    controller.advanceRetryTimer = null;
                }}
                if (controller.visualTimers) {{
                    controller.visualTimers.forEach(function(timerId) {{
                        parentWindow.clearTimeout(timerId);
                    }});
                    controller.visualTimers = [];
                }}
            }}

            function cancelSpeech() {{
                cancelTimers();
                controller.isSpeaking = false;
                controller.speakingKey = null;
                try {{
                    synth.cancel();
                }} catch (error) {{
                }}
            }}

            function pauseDelayMsForIndex(index) {{
                if (
                    controller.pauseSeconds
                    && typeof controller.pauseSeconds[index] === 'number'
                    && !Number.isNaN(controller.pauseSeconds[index])
                ) {{
                    return Math.max(Math.round(controller.pauseSeconds[index] * 1000), 0);
                }}
                return controller.delayMs > 0 ? controller.delayMs : 0;
            }}

            function renderLocalStoryView(index) {{
                if (index < 0 || index >= controller.lines.length) return;

                var spanishContent = doc.getElementById('story-spanish-content');
                var translationContent = doc.getElementById('story-translation-content');
                var progressValue = doc.getElementById('story-progress-value');
                var progressFill = doc.getElementById('story-progress-fill');
                var pauseReadoutValue = doc.getElementById('story-pause-readout-value');
                var total = controller.lines.length || 1;
                var pct = ((index + 1) / total) * 100;
                var countText = (index + 1) + ' of ' + total;
                var lineNumber = controller.lineNumbers && typeof controller.lineNumbers[index] === 'number'
                    ? controller.lineNumbers[index]
                    : (index + 1);
                var pauseSeconds = controller.pauseSeconds && typeof controller.pauseSeconds[index] === 'number'
                    ? controller.pauseSeconds[index]
                    : 0;

                if (progressValue) {{
                    progressValue.textContent = controller.showLineNumbers
                        ? ('Line: ' + lineNumber + '    ' + countText)
                        : countText;
                }}
                if (progressFill) {{
                    progressFill.style.width = pct.toFixed(2) + '%';
                }}
                if (pauseReadoutValue) {{
                    pauseReadoutValue.textContent = pauseSeconds.toFixed(2) + 's';
                }}
                if (spanishContent) {{
                    spanishContent.innerHTML = controller.spanishHtmlLines[index] || '';
                }}
                if (translationContent) {{
                    translationContent.innerHTML = controller.translationHtmlLines[index] || '<div class="fc-word-placeholder">&nbsp;</div>';
                }}
            }}

            function renderLocalStoryViewStable(index) {{
                if (index < 0 || index >= controller.lines.length) return;
                renderLocalStoryView(index);
                [0, 90, 220].forEach(function(delay) {{
                    parentWindow.setTimeout(function() {{
                        renderLocalStoryView(index);
                    }}, delay);
                }});
            }}

            function pickVoice() {{
                if (doc && typeof doc._fcPickPreferredVoice === 'function') {{
                    return doc._fcPickPreferredVoice('es', {{ randomize: true }});
                }}
                var voices = synth.getVoices ? synth.getVoices() : [];
                return voices.find(function(voice) {{ return voice.lang === 'es-MX'; }})
                    || voices.find(function(voice) {{ return voice.lang === 'es-US'; }})
                    || voices.find(function(voice) {{ return voice.lang === 'es-ES'; }})
                    || voices.find(function(voice) {{ return voice.lang && voice.lang.toLowerCase().startsWith('es'); }})
                    || null;
            }}

            function clickAdvanceButton() {{
                var hiddenButton = doc.querySelector('.st-key-storyadvance_hidden_wrap button');
                if (!hiddenButton) {{
                    return false;
                }}
                hiddenButton.click();
                hiddenButton.dispatchEvent(new MouseEvent('click', {{ bubbles: true }}));
                return true;
            }}

            function clickFinishButton() {{
                var hiddenButton = doc.querySelector('.st-key-storyfinish_hidden_wrap button');
                if (!hiddenButton) {{
                    return false;
                }}
                hiddenButton.click();
                hiddenButton.dispatchEvent(new MouseEvent('click', {{ bubbles: true }}));
                return true;
            }}

            function syncAdvanceButton() {{
                clickAdvanceButton();
                var attempts = 0;
                if (controller.advanceRetryTimer) {{
                    parentWindow.clearInterval(controller.advanceRetryTimer);
                    controller.advanceRetryTimer = null;
                }}
                controller.advanceRetryTimer = parentWindow.setInterval(function() {{
                    attempts += 1;
                    if (clickAdvanceButton() || attempts >= 10) {{
                        parentWindow.clearInterval(controller.advanceRetryTimer);
                        controller.advanceRetryTimer = null;
                    }}
                }}, 150);
            }}

            function syncFinalAdvanceButton() {{
                if (controller.advanceRetryTimer) {{
                    parentWindow.clearInterval(controller.advanceRetryTimer);
                    controller.advanceRetryTimer = null;
                }}

                var attempts = 0;
                clickAdvanceButton();
                controller.advanceRetryTimer = parentWindow.setInterval(function() {{
                    attempts += 1;
                    clickAdvanceButton();
                    if (attempts >= 12) {{
                        parentWindow.clearInterval(controller.advanceRetryTimer);
                        controller.advanceRetryTimer = null;
                    }}
                }}, 150);
            }}

            function syncFinishButton() {{
                if (controller.advanceRetryTimer) {{
                    parentWindow.clearInterval(controller.advanceRetryTimer);
                    controller.advanceRetryTimer = null;
                }}

                var attempts = 0;
                clickFinishButton();
                controller.advanceRetryTimer = parentWindow.setInterval(function() {{
                    attempts += 1;
                    if (clickFinishButton() || attempts >= 12) {{
                        parentWindow.clearInterval(controller.advanceRetryTimer);
                        controller.advanceRetryTimer = null;
                    }}
                }}, 150);
            }}

            function scheduleNextLine(nextIndex, completedIndex) {{
                if (!controller.running || !controller.autoAdvance) return;
                cancelTimers();
                controller.queuedNextIndex = nextIndex;
                setDebug('queued next: ' + (nextIndex + 1));
                var waitMs = pauseDelayMsForIndex(completedIndex);
                controller.advanceTimer = parentWindow.setTimeout(function() {{
                    if (!controller.running) return;
                    if (nextIndex >= controller.lines.length) {{
                        controller.running = false;
                        controller.active = false;
                        controller.queuedNextIndex = null;
                        setDebug('finished story');
                        return;
                    }}
                    controller.localIndex = nextIndex;
                    controller.queuedNextIndex = null;
                    renderLocalStoryView(nextIndex);
                    setDebug('speaking next: ' + (nextIndex + 1));
                    speakLine(nextIndex);
                    parentWindow.setTimeout(function() {{
                        if (!controller.running) return;
                        syncAdvanceButton();
                    }}, 250);
                }}, waitMs);
            }}

            function handleLineComplete(index) {{
                controller.isSpeaking = false;
                controller.speakingKey = null;
                controller.lastCompletedIndex = index;
                setDebug('completed: ' + (index + 1));
                if (doc._storyPauseResumeState) {{
                    doc._storyPauseResumeState.speechFinished = true;
                }}
                if (index >= controller.lines.length - 1) {{
                    controller.running = false;
                    controller.active = false;
                    controller.queuedNextIndex = null;
                    cancelTimers();
                    setDebug('finished story');
                    syncFinishButton();
                    return;
                }}
                if (controller.running && controller.autoAdvance) {{
                    scheduleNextLine(index + 1, index);
                }}
            }}

            function queueAutoFrom(startIndex) {{
                if (startIndex < 0 || startIndex >= controller.lines.length) return;

                cancelSpeech();

                controller.queueToken = (controller.queueToken || 0) + 1;
                var queueToken = controller.queueToken;
                controller.visualTimers = [];

                if (typeof synth.resume === 'function') {{
                    synth.resume();
                }}

                function estimatedDurationMs(text) {{
                    var rawText = text || '';
                    var chars = rawText.length || 1;
                    var words = rawText.trim() ? rawText.trim().split(/\\s+/).length : 1;
                    var punctuationPauses = (rawText.match(/[,:;.!?]/g) || []).length;
                    var rate = speechRate > 0 ? speechRate : 1;
                    var estimate = (words * 520) + (chars * 38) + (punctuationPauses * 240) + 650;
                    return Math.max(2200, Math.round(estimate / rate));
                }}

                function speakOne(idx) {{
                    if (controller.queueToken !== queueToken) return;
                    if (!controller.running) return;
                    if (idx >= controller.lines.length) {{
                        controller.running = false;
                        controller.active = false;
                        setDebug('finished story');
                        return;
                    }}

                    var rawSpeechText = controller.lines[idx];
                    if (!rawSpeechText) {{
                        speakOne(idx + 1);
                        return;
                    }}

                    // Update the DOM synchronously at the moment this line begins.
                    controller.localIndex = idx;
                    controller.pausedDisplayIndex = null;
                    renderLocalStoryViewStable(idx);

                    var speechKey = controller.storyKey + '|queue|' + idx + '|' + rawSpeechText + '|' + speechRate;
                    var utterance = new SpeechSynthesisUtterance(rawSpeechText);
                    var voice = pickVoice();
                    utterance.lang = voice ? voice.lang : 'es-ES';
                    utterance.rate = speechRate;
                    if (voice) utterance.voice = voice;

                    var doneFired = false;
                    var watchdogTimerId = null;
                    var pollTimerId = null;
                    var sawSpeaking = false;

                    function clearLocalTimers() {{
                        if (watchdogTimerId !== null) {{
                            parentWindow.clearTimeout(watchdogTimerId);
                            watchdogTimerId = null;
                        }}
                        if (pollTimerId !== null) {{
                            parentWindow.clearTimeout(pollTimerId);
                            pollTimerId = null;
                        }}
                    }}

                    function scheduleNext() {{
                        if (controller.queueToken !== queueToken) return;
                        if (!controller.running) return;
                        if (idx >= controller.lines.length - 1) {{
                            controller.running = false;
                            controller.active = false;
                            controller.queuedNextIndex = null;
                            setDebug('finished story');
                            syncFinishButton();
                            return;
                        }}
                        var waitMs = pauseDelayMsForIndex(idx);
                        var timerId = parentWindow.setTimeout(function() {{
                            if (controller.queueToken !== queueToken) return;
                            if (!controller.running) return;
                            speakOne(idx + 1);
                        }}, waitMs);
                        controller.visualTimers.push(timerId);
                    }}

                    function finishAndAdvance(reason) {{
                        if (doneFired) return;
                        doneFired = true;
                        clearLocalTimers();
                        controller.isSpeaking = false;
                        controller.speakingKey = null;
                        controller.lastCompletedIndex = idx;
                        setDebug('done(' + reason + '): ' + (idx + 1));
                        scheduleNext();
                    }}

                    utterance.onstart = function() {{
                        if (controller.queueToken !== queueToken || !controller.running) return;
                        controller.lastSpokenIndex = idx;
                        controller.pendingManualSpeakIndex = null;
                        controller.isSpeaking = true;
                        controller.speakingKey = speechKey;
                        sawSpeaking = true;
                        setDebug('speak: ' + (idx + 1));
                    }};

                    utterance.onend = function() {{ finishAndAdvance('onend'); }};
                    utterance.onerror = function() {{ finishAndAdvance('onerror'); }};

                    // iOS Safari frequently drops onend; poll synth.speaking as a backup.
                    function pollSpeaking() {{
                        if (doneFired) return;
                        if (controller.queueToken !== queueToken) return;
                        try {{
                            if (synth.speaking || synth.pending) {{
                                sawSpeaking = true;
                            }} else if (sawSpeaking) {{
                                finishAndAdvance('poll');
                                return;
                            }}
                        }} catch (e) {{}}
                        pollTimerId = parentWindow.setTimeout(pollSpeaking, 250);
                        controller.visualTimers.push(pollTimerId);
                    }}
                    pollTimerId = parentWindow.setTimeout(pollSpeaking, 400);
                    controller.visualTimers.push(pollTimerId);

                    // Hard watchdog: keep this close to the estimated speech duration so short lines
                    // do not get stretched into multi-second extra waits when Safari drops events.
                    var durMs = estimatedDurationMs(rawSpeechText);
                    var watchdogMs = Math.max(durMs + 1600, 3200);
                    watchdogTimerId = parentWindow.setTimeout(function() {{
                        finishAndAdvance('watchdog');
                    }}, watchdogMs);
                    controller.visualTimers.push(watchdogTimerId);

                    synth.speak(utterance);
                }}

                speakOne(startIndex);
            }}

            function speakLine(index) {{
                if (!controller.running) return;
                if (index < 0 || index >= controller.lines.length) return;

                var speechText = controller.lines[index];
                if (!speechText) {{
                    handleLineComplete(index);
                    return;
                }}

                var speechKey = controller.storyKey + '|' + index + '|' + speechText + '|' + speechRate;
                if (controller.speakingKey === speechKey && controller.isSpeaking) {{
                    return;
                }}

                try {{
                    var utterance = new SpeechSynthesisUtterance(speechText);
                    var voice = pickVoice();
                    var completionHandled = false;
                    var completionTimer = null;
                    var speakingPollTimer = null;

                    function clearCompletionTimer() {{
                        if (completionTimer) {{
                            parentWindow.clearTimeout(completionTimer);
                            completionTimer = null;
                        }}
                        if (speakingPollTimer) {{
                            parentWindow.clearInterval(speakingPollTimer);
                            speakingPollTimer = null;
                        }}
                    }}

                    function finishLine() {{
                        if (completionHandled) return;
                        completionHandled = true;
                        clearCompletionTimer();
                        handleLineComplete(index);
                    }}

                    function estimatedDurationMs() {{
                        var chars = speechText.length || 1;
                        var rate = speechRate > 0 ? speechRate : 1;
                        return Math.max(1600, Math.round((chars * 85) / rate) + 700);
                    }}

                    utterance.lang = voice ? voice.lang : 'es-ES';
                    utterance.rate = speechRate;
                    if (voice) utterance.voice = voice;

                    utterance.onstart = function() {{
                        controller.localIndex = index;
                        controller.lastSpokenIndex = index;
                        controller.isSpeaking = true;
                        controller.speakingKey = speechKey;
                        setDebug('onstart: ' + (index + 1));
                        doc._storyPauseResumeState = {{
                            runToken: controller.storyRunToken,
                            storyIndex: index,
                            speechFinished: false
                        }};
                        doc._storyPauseRequested = null;
                        speakingPollTimer = parentWindow.setInterval(function() {{
                            if (!controller.running || completionHandled) {{
                                clearCompletionTimer();
                                return;
                            }}
                            if (!synth.speaking && !synth.pending) {{
                                setDebug('poll idle: ' + (index + 1));
                                finishLine();
                            }}
                        }}, 150);
                    }};
                    utterance.onend = function() {{
                        setDebug('onend: ' + (index + 1));
                        finishLine();
                    }};
                    utterance.onerror = function() {{
                        controller.isSpeaking = false;
                        controller.speakingKey = null;
                        setDebug('onerror: ' + (index + 1));
                        finishLine();
                    }};

                    synth.cancel();
                    if (typeof synth.resume === 'function') {{
                        synth.resume();
                    }}
                    synth.speak(utterance);
                    completionTimer = parentWindow.setTimeout(function() {{
                        if (!controller.running) return;
                        if (!controller.isSpeaking && controller.lastCompletedIndex === index) return;
                        setDebug('timeout finish: ' + (index + 1));
                        finishLine();
                    }}, estimatedDurationMs());
                }} catch (error) {{
                    controller.isSpeaking = false;
                    controller.speakingKey = null;
                    setDebug('catch error: ' + (index + 1));
                }}
            }}

            function startFromGesture() {{
                var now = Date.now();
                if (controller.lastStartGestureAt && now - controller.lastStartGestureAt < 900) {{
                    return;
                }}
                controller.lastStartGestureAt = now;
                controller.active = true;
                controller.running = true;
                controller.ignorePauseUntil = Date.now() + 1200;
                cancelTimers();
                var startButton = doc.querySelector('.st-key-storystart_wrap button');
                var startMode = startButton && startButton.textContent ? startButton.textContent.trim().toUpperCase() : '';
                var targetIndex = typeof controller.localIndex === 'number' ? controller.localIndex : controller.serverIndex;
                if (startMode === 'RESUME') {{
                    if (typeof controller.resumeTargetIndex === 'number') {{
                        targetIndex = controller.resumeTargetIndex;
                    }} else if (controller.resumeNext && targetIndex < controller.lines.length - 1) {{
                        targetIndex += 1;
                    }}
                }}
                controller.resumeTargetIndex = null;
                controller.pausedDisplayIndex = null;
                controller.localIndex = targetIndex;
                renderLocalStoryViewStable(targetIndex);
                setDebug('start gesture: ' + (targetIndex + 1));
                if (controller.autoAdvance) {{
                    queueAutoFrom(targetIndex);
                    return;
                }}
                controller.pendingManualSpeakIndex = targetIndex;
                speakLine(targetIndex);
            }}

            function stepAdvanceFromGesture() {{
                if (controller.autoAdvance) return;
                var nextIndex = Math.min(controller.localIndex + 1, controller.lines.length - 1);
                if (nextIndex === controller.localIndex) return;
                controller.active = true;
                controller.running = true;
                controller.localIndex = nextIndex;
                controller.pausedDisplayIndex = null;
                controller.pendingManualSpeakIndex = nextIndex;
                renderLocalStoryViewStable(nextIndex);
                setDebug('step gesture: ' + (nextIndex + 1));
                speakLine(nextIndex);
            }}

            function nextFromGesture(event) {{
                if (event) {{
                    event.preventDefault();
                    event.stopPropagation();
                    if (typeof event.stopImmediatePropagation === 'function') {{
                        event.stopImmediatePropagation();
                    }}
                }}

                var nextIndex = Math.min(controller.localIndex + 1, controller.lines.length - 1);
                if (nextIndex === controller.localIndex) return;

                cancelTimers();
                controller.queueToken = (controller.queueToken || 0) + 1;
                controller.isSpeaking = false;
                controller.speakingKey = null;
                controller.queuedNextIndex = null;
                controller.resumeTargetIndex = null;
                controller.pausedDisplayIndex = null;
                try {{
                    synth.cancel();
                }} catch (error) {{
                }}

                controller.active = true;
                controller.running = true;
                controller.localIndex = nextIndex;
                renderLocalStoryViewStable(nextIndex);
                setDebug('next gesture: ' + (nextIndex + 1));

                // The jump onto the last card is safe to over-retry because extra advance calls
                // collapse into the same final state instead of skipping past content.
                if (nextIndex >= controller.lines.length - 1) {{
                    syncFinalAdvanceButton();
                }} else {{
                    syncAdvanceButton();
                }}

                if (controller.autoAdvance) {{
                    queueAutoFrom(nextIndex);
                    return;
                }}

                controller.pendingManualSpeakIndex = nextIndex;
                speakLine(nextIndex);
            }}

            function pauseFromGesture() {{
                function clampIndex(index) {{
                    if (typeof index !== 'number' || Number.isNaN(index)) {{
                        return null;
                    }}
                    return Math.max(0, Math.min(index, controller.lines.length - 1));
                }}

                function maxDefinedIndex() {{
                    var values = Array.prototype.slice.call(arguments)
                        .map(clampIndex)
                        .filter(function(value) {{ return value !== null; }});
                    if (!values.length) {{
                        return clampIndex(controller.serverIndex) || 0;
                    }}
                    return Math.max.apply(null, values);
                }}

                if (controller.ignorePauseUntil && Date.now() < controller.ignorePauseUntil) {{
                    return;
                }}
                if (controller.isSpeaking) {{
                    controller.resumeTargetIndex = maxDefinedIndex(
                        controller.localIndex,
                        controller.lastSpokenIndex,
                        controller.serverIndex
                    );
                }} else {{
                    controller.resumeTargetIndex = maxDefinedIndex(
                        controller.localIndex,
                        controller.serverIndex
                    );
                }}
                controller.running = false;
                controller.active = true;
                controller.queuedNextIndex = null;
                controller.pausedDisplayIndex = controller.resumeTargetIndex;
                controller.localIndex = controller.resumeTargetIndex;
                renderLocalStoryViewStable(controller.localIndex);
                setDebug('paused at: ' + (controller.resumeTargetIndex + 1));
                cancelSpeech();
            }}

            function stopFromGesture() {{
                controller.running = false;
                controller.active = false;
                controller.pausedDisplayIndex = null;
                controller.localIndex = controller.serverIndex;
                setDebug('stopped');
                cancelSpeech();
            }}

            function attachHandler(selector, key, handler) {{
                var element = doc.querySelector(selector);
                if (!element) return;
                if (doc[key]) {{
                    eventNames.forEach(function(eventName) {{
                        element.removeEventListener(eventName, doc[key], true);
                    }});
                }}
                doc[key] = handler;
                eventNames.forEach(function(eventName) {{
                    element.addEventListener(eventName, handler, true);
                }});
            }}

            if (controller.storyKey !== config.storyKey || controller.storyRunToken !== config.storyRunToken) {{
                cancelSpeech();
                controller.active = false;
                controller.localIndex = config.serverIndex;
                controller.lastSpokenIndex = null;
                controller.lastCompletedIndex = null;
                controller.queuedNextIndex = null;
                controller.resumeTargetIndex = null;
                controller.pausedDisplayIndex = null;
            }}

            controller.storyKey = config.storyKey;
            controller.storyRunToken = config.storyRunToken;
            controller.lines = config.lines;
            controller.spanishHtmlLines = config.spanishHtmlLines;
            controller.translationHtmlLines = config.translationHtmlLines;
            controller.pauseSeconds = config.pauseSeconds;
            controller.lineNumbers = config.lineNumbers;
            controller.showLineNumbers = config.showLineNumbers;
            controller.serverIndex = config.serverIndex;
            controller.autoAdvance = config.autoAdvance;
            controller.delayMs = config.delayMs;
            controller.resumeNext = config.resumeNext;

            if (typeof controller.localIndex !== 'number') {{
                controller.localIndex = config.serverIndex;
            }}

            if (
                !controller.isSpeaking
                && typeof config.serverIndex === 'number'
                && config.serverIndex !== controller.localIndex
                && (config.running || !controller.active)
            ) {{
                controller.localIndex = config.serverIndex;
                controller.pausedDisplayIndex = null;
                controller.queuedNextIndex = null;
                setDebug('synced to server: ' + (controller.localIndex + 1));
            }}

            attachHandler('.st-key-storystart_wrap button', '_storyMobileStartHandler', startFromGesture);
            attachHandler('.st-key-storypause_wrap button', '_storyMobilePauseHandler', pauseFromGesture);
            attachHandler('.st-key-storystop_wrap button', '_storyMobileStopHandler', stopFromGesture);
            attachHandler('.st-key-storynext_wrap button', '_storyMobileNextHandler', nextFromGesture);

            if (!config.running) {{
                if (!controller.active) {{
                    controller.localIndex = config.serverIndex;
                }} else if (typeof controller.pausedDisplayIndex === 'number') {{
                    controller.localIndex = controller.pausedDisplayIndex;
                }}
                cancelSpeech();
            }}

            renderLocalStoryViewStable(controller.localIndex);
            setDebug('ready: ' + (controller.localIndex + 1) + ' running=' + config.running + ' auto=' + controller.autoAdvance);

            if (config.running && !controller.active && !controller.isSpeaking) {{
                controller.active = true;
                controller.running = true;
                controller.pausedDisplayIndex = null;
                controller.queuedNextIndex = null;
                controller.pendingManualSpeakIndex = null;
                setDebug('restart run: ' + (controller.localIndex + 1));
                if (controller.autoAdvance) {{
                    queueAutoFrom(controller.localIndex);
                }} else {{
                    controller.pendingManualSpeakIndex = controller.localIndex;
                    speakLine(controller.localIndex);
                }}
                return;
            }}

            if (
                config.running
                && controller.active
                && !controller.isSpeaking
                && !controller.autoAdvance
                && controller.pendingManualSpeakIndex !== controller.localIndex
                && controller.lastSpokenIndex !== controller.localIndex
            ) {{
                setDebug('step speak: ' + (controller.localIndex + 1));
                speakLine(controller.localIndex);
            }}
        }})();
        </script>
        """,
        height=0,
    )


def render_story_mobile_controller_cleanup():
    components.html(
        """
        <script>
        (function() {
            var doc = window.parent.document;
            var parentWindow = window.parent;
            var synth = parentWindow.speechSynthesis || window.speechSynthesis;
            var controller = doc._storyMobileController;
            var bindings = [
                ['.st-key-storystart_wrap button', '_storyMobileStartHandler'],
                ['.st-key-storypause_wrap button', '_storyMobilePauseHandler'],
                ['.st-key-storystop_wrap button', '_storyMobileStopHandler'],
                ['.st-key-storynext_wrap button', '_storyMobileNextHandler'],
            ];
            var eventNames = ['click', 'touchend'];
            var debugEl = doc.getElementById('story-mobile-debug');

            bindings.forEach(function(binding) {
                var element = doc.querySelector(binding[0]);
                var handler = doc[binding[1]];
                if (!element || !handler) return;
                eventNames.forEach(function(eventName) {
                    element.removeEventListener(eventName, handler, true);
                });
                doc[binding[1]] = null;
            });

            if (controller) {
                if (controller.advanceTimer) {
                    clearTimeout(controller.advanceTimer);
                    controller.advanceTimer = null;
                }
                if (controller.advanceRetryTimer) {
                    clearInterval(controller.advanceRetryTimer);
                    controller.advanceRetryTimer = null;
                }
                if (controller.queueToken) {
                    controller.queueToken += 1;
                }
                controller.running = false;
                controller.active = false;
                controller.isSpeaking = false;
                controller.speakingKey = null;
                controller.queuedNextIndex = null;
                controller.pendingManualSpeakIndex = null;
                controller.resumeTargetIndex = null;
            }

            if (synth) {
                try {
                    synth.cancel();
                } catch (error) {
                }
            }

            if (debugEl) {
                debugEl.style.display = 'block';
                debugEl.textContent = 'DEBUG: inactive';
            }
        })();
        </script>
        """,
        height=0,
    )


def render_story_paused_cleanup():
    story_index = st.session_state.index
    story_run_token = st.session_state.story_run_token
    components.html(
        f"""
        <script>
        (function() {{
            var synth = window.parent.speechSynthesis || window.speechSynthesis;
            var doc = window.parent.document;
            var pauseCaptureKey = '{story_run_token}|' + '{story_index}';
            var pauseState = doc._storyPauseResumeState;

            doc._storyPauseRequested = {{
                runToken: {story_run_token},
                storyIndex: {story_index}
            }};

            if (doc._storyPauseCaptureKey !== pauseCaptureKey) {{
                doc._storyPauseCaptureKey = pauseCaptureKey;
                if (pauseState && pauseState.runToken === {story_run_token} && pauseState.storyIndex === {story_index} && pauseState.speechFinished) {{
                    var resumeNextButton = doc.querySelector('.st-key-storyresumenext_hidden_wrap button');
                    if (resumeNextButton) {{
                        resumeNextButton.click();
                        resumeNextButton.dispatchEvent(new MouseEvent('click', {{bubbles: true}}));
                    }}
                }}
            }}

            if (doc._storyAutoAdvanceTimer) {{
                clearTimeout(doc._storyAutoAdvanceTimer);
                doc._storyAutoAdvanceTimer = null;
            }}

            if (doc._storyAdvanceRetryTimer) {{
                clearInterval(doc._storyAdvanceRetryTimer);
                doc._storyAdvanceRetryTimer = null;
            }}

            doc._storyAutoAdvanceIndex = null;
            doc._storyLastSpeechKey = null;
            doc._storyPauseResumeState = null;

            if (synth) {{
                synth.cancel();
            }}
        }})();
        </script>
        """,
        height=0,
    )


def render_story_advance_tap_handler():
    components.html(
        """
        <script>
        (function() {
            function clickAdvanceButton() {
                var doc = window.parent.document;
                var button = doc.querySelector('.st-key-storyadvance_hidden_wrap button');
                if (!button) {
                    return false;
                }
                button.click();
                button.dispatchEvent(new MouseEvent('click', {bubbles: true}));
                return true;
            }

            function attach() {
                var doc = window.parent.document;
                var blocks = doc.querySelectorAll('.fc-story-tappable');
                if (!blocks.length) return false;

                if (doc._storyTapHandler) {
                    doc.body.removeEventListener('click', doc._storyTapHandler);
                }

                doc._storyTapHandler = function(event) {
                    if (!event.target.closest('.fc-story-tappable')) return;
                    clickAdvanceButton();
                };

                doc.body.addEventListener('click', doc._storyTapHandler);
                return true;
            }

            var attempts = 0;
            function tryAttach() {
                if (attach()) return;
                attempts += 1;
                if (attempts < 20) {
                    setTimeout(tryAttach, 150);
                }
            }

            tryAttach();
        })();
        </script>
        """,
        height=0,
    )


def render_story_advance_tap_cleanup():
    components.html(
        """
        <script>
        (function() {
            var doc = window.parent.document;
            if (doc._storyTapHandler) {
                doc.body.removeEventListener('click', doc._storyTapHandler);
                doc._storyTapHandler = null;
            }
            if (doc._storyIgnoreTapHandler) {
                ['click', 'mousedown', 'mouseup', 'pointerdown', 'pointerup', 'touchstart', 'touchend'].forEach(function(eventName) {
                    doc.body.removeEventListener(eventName, doc._storyIgnoreTapHandler, true);
                });
                doc._storyIgnoreTapHandler = null;
            }
            if (doc._fcHandler) {
                doc.body.removeEventListener('click', doc._fcHandler);
                doc._fcHandler = null;
            }
        })();
        </script>
        """,
        height=0,
    )


def render_story_ignore_tap_handler():
    components.html(
        """
        <script>
        (function() {
            var doc = window.parent.document;

            if (doc._storyTapHandler) {
                doc.body.removeEventListener('click', doc._storyTapHandler);
                doc._storyTapHandler = null;
            }

            if (doc._fcHandler) {
                doc.body.removeEventListener('click', doc._fcHandler);
                doc._fcHandler = null;
            }

            if (doc._storyIgnoreTapHandler) {
                ['click', 'mousedown', 'mouseup', 'pointerdown', 'pointerup', 'touchstart', 'touchend'].forEach(function(eventName) {
                    doc.body.removeEventListener(eventName, doc._storyIgnoreTapHandler, true);
                });
            }

            doc._storyIgnoreTapHandler = function(event) {
                if (!event.target.closest('.fc-story-static')) return;
                doc._storyStaticBoxInteraction = {
                    at: Date.now()
                };
                event.preventDefault();
                event.stopPropagation();
                if (typeof event.stopImmediatePropagation === 'function') {
                    event.stopImmediatePropagation();
                }
            };

            ['click', 'mousedown', 'mouseup', 'pointerdown', 'pointerup', 'touchstart', 'touchend'].forEach(function(eventName) {
                doc.body.addEventListener(eventName, doc._storyIgnoreTapHandler, true);
            });
        })();
        </script>
        """,
        height=0,
    )


def render_story_auto_advance(delay_seconds):
    delay_ms = max(int(delay_seconds * 1000), 0)
    story_index = st.session_state.index
    last_story_index = max(len(st.session_state.cards) - 1, 0)
    components.html(
        f"""
        <script>
        (function() {{
            var doc = window.parent.document;
            var storyIndex = {story_index};
            var lastStoryIndex = {last_story_index};

            function clearAdvanceRetryTimer() {{
                if (doc._storyAdvanceRetryTimer) {{
                    clearInterval(doc._storyAdvanceRetryTimer);
                    doc._storyAdvanceRetryTimer = null;
                }}
            }}

            function startAdvanceRetry() {{
                var attempts = 0;
                clearAdvanceRetryTimer();
                doc._storyAdvanceRetryTimer = setInterval(function() {{
                    attempts += 1;
                    if (clickAdvanceButton() || attempts >= 10) {{
                        clearAdvanceRetryTimer();
                    }}
                }}, 150);
            }}

            function clickAdvanceButton() {{
                var button = doc.querySelector('.st-key-storyadvance_hidden_wrap button');
                if (!button) {{
                    return false;
                }}
                button.click();
                button.dispatchEvent(new MouseEvent('click', {{bubbles: true}}));
                return true;
            }}

            if (doc._storyAutoAdvanceTimer) {{
                clearTimeout(doc._storyAutoAdvanceTimer);
            }}
            clearAdvanceRetryTimer();

            doc._storyAutoAdvanceIndex = storyIndex;
            doc._storyAutoAdvanceTimer = setTimeout(function() {{
                if (doc._storyAutoAdvanceIndex !== storyIndex) {{
                    return;
                }}
                if (storyIndex >= lastStoryIndex) {{
                    return;
                }}
                if (clickAdvanceButton()) return;
                startAdvanceRetry();
            }}, {delay_ms});
        }})();
        </script>
        """,
        height=0,
    )


def render_story_audio_autoplay(text, auto_advance=False, delay_seconds=0):
    speech_text = strip_spoken_text(text)
    speech_rate = speech_rate_value()
    story_index = st.session_state.index
    story_run_token = st.session_state.story_run_token
    delay_ms = max(int(delay_seconds * 1000), 0)
    last_story_index = max(len(st.session_state.cards) - 1, 0)
    components.html(
        f"""
        <script>
        (function() {{
            var parentWindow = window.parent;
            var nav = parentWindow.navigator || window.navigator;
            var ua = nav && nav.userAgent ? nav.userAgent : '';
            var hasTouch = !!(('ontouchstart' in parentWindow) || (nav && nav.maxTouchPoints > 0));
            var narrow = !!(parentWindow.matchMedia && parentWindow.matchMedia('(max-width: 767px)').matches);
            if (narrow && (hasTouch || /iPhone|Android|Mobile|iPad|iPod/i.test(ua))) return;

            var speechText = {json.dumps(speech_text)};
            var speechRate = {speech_rate};
            var storyIndex = {story_index};
            var storyRunToken = {story_run_token};
            var autoAdvance = {str(auto_advance).lower()};
            var delayMs = {delay_ms};
            var lastStoryIndex = {last_story_index};
            var synth = window.parent.speechSynthesis || window.speechSynthesis;
            var doc = window.parent.document;
            var speechKey = storyRunToken + '|' + storyIndex + '|' + speechText + '|' + speechRate;

            if (!synth || !speechText) return;

            function clearAdvanceRetryTimer() {{
                if (doc._storyAdvanceRetryTimer) {{
                    clearInterval(doc._storyAdvanceRetryTimer);
                    doc._storyAdvanceRetryTimer = null;
                }}
            }}

            function startAdvanceRetry() {{
                var attempts = 0;
                clearAdvanceRetryTimer();
                doc._storyAdvanceRetryTimer = setInterval(function() {{
                    attempts += 1;
                    if (clickAdvanceButton() || attempts >= 10) {{
                        clearAdvanceRetryTimer();
                    }}
                }}, 150);
            }}

            function clickAdvanceButton() {{
                var button = doc.querySelector('.st-key-storyadvance_hidden_wrap button');
                if (!button) {{
                    return false;
                }}
                button.click();
                button.dispatchEvent(new MouseEvent('click', {{bubbles: true}}));
                return true;
            }}

            function scheduleAdvanceAfterSpeech() {{
                if (!autoAdvance) return;
                if (doc._storyPauseRequested && doc._storyPauseRequested.runToken === storyRunToken && doc._storyPauseRequested.storyIndex === storyIndex) return;
                if (storyIndex >= lastStoryIndex) return;

                if (doc._storyAutoAdvanceTimer) {{
                    clearTimeout(doc._storyAutoAdvanceTimer);
                }}
                clearAdvanceRetryTimer();

                doc._storyAutoAdvanceIndex = storyIndex;
                doc._storyAutoAdvanceTimer = setTimeout(function() {{
                    if (doc._storyAutoAdvanceIndex !== storyIndex) {{
                        return;
                    }}
                    if (clickAdvanceButton()) return;
                    startAdvanceRetry();
                }}, delayMs);
            }}

            function attachNextHandler() {{
                var button = doc.querySelector('.st-key-storynext_wrap button');
                if (!button) return;

                if (doc._storyDesktopNextHandler) {{
                    ['click', 'touchend'].forEach(function(eventName) {{
                        button.removeEventListener(eventName, doc._storyDesktopNextHandler, true);
                    }});
                }}

                doc._storyDesktopNextHandler = function(event) {{
                    event.preventDefault();
                    event.stopPropagation();
                    if (typeof event.stopImmediatePropagation === 'function') {{
                        event.stopImmediatePropagation();
                    }}

                    doc._storyPauseRequested = {{
                        runToken: storyRunToken,
                        storyIndex: storyIndex,
                    }};

                    if (doc._storyAutoAdvanceTimer) {{
                        clearTimeout(doc._storyAutoAdvanceTimer);
                        doc._storyAutoAdvanceTimer = null;
                    }}
                    clearAdvanceRetryTimer();

                    try {{
                        synth.cancel();
                    }} catch (error) {{
                    }}

                    if (clickAdvanceButton()) return;
                    startAdvanceRetry();
                }};

                ['click', 'touchend'].forEach(function(eventName) {{
                    button.addEventListener(eventName, doc._storyDesktopNextHandler, true);
                }});
            }}

            attachNextHandler();
            if (doc._storyLastSpeechKey === speechKey) return;

            function pickVoice() {{
                if (doc && typeof doc._fcPickPreferredVoice === 'function') {{
                    return doc._fcPickPreferredVoice('es', {{ randomize: true }});
                }}
                var voices = synth.getVoices ? synth.getVoices() : [];
                return voices.find(function(voice) {{ return voice.lang === 'es-MX'; }})
                    || voices.find(function(voice) {{ return voice.lang === 'es-US'; }})
                    || voices.find(function(voice) {{ return voice.lang === 'es-ES'; }})
                    || voices.find(function(voice) {{ return voice.lang && voice.lang.toLowerCase().startsWith('es'); }})
                    || null;
            }}

            function speakNow() {{
                var utterance = new SpeechSynthesisUtterance(speechText);
                var voice = pickVoice();
                var completionHandled = false;
                var speechStarted = false;
                var startWatchdog = null;

                function handleSpeechCompletion() {{
                    if (completionHandled) return;
                    completionHandled = true;

                    if (startWatchdog) {{
                        clearTimeout(startWatchdog);
                        startWatchdog = null;
                    }}

                    var pauseRequested = doc._storyPauseRequested
                        && doc._storyPauseRequested.runToken === storyRunToken
                        && doc._storyPauseRequested.storyIndex === storyIndex;

                    if (!pauseRequested && doc._storyPauseResumeState && doc._storyPauseResumeState.runToken === storyRunToken && doc._storyPauseResumeState.storyIndex === storyIndex) {{
                        doc._storyPauseResumeState.speechFinished = true;
                    }}

                    if (pauseRequested) return;
                    doc._storyStaticBoxInteraction = null;
                    scheduleAdvanceAfterSpeech();
                }}

                doc._storyPauseResumeState = {{
                    runToken: storyRunToken,
                    storyIndex: storyIndex,
                    speechFinished: false
                }};
                doc._storyPauseRequested = null;

                utterance.lang = voice ? voice.lang : 'es-ES';
                utterance.rate = speechRate;
                if (voice) utterance.voice = voice;
                utterance.onstart = function() {{
                    speechStarted = true;
                    doc._storySpeechUnlocked = true;
                    doc._storySpeechUnlockedAt = Date.now();
                    if (startWatchdog) {{
                        clearTimeout(startWatchdog);
                        startWatchdog = null;
                    }}
                }};
                utterance.onend = handleSpeechCompletion;
                utterance.onerror = function() {{
                    var pauseRequested = doc._storyPauseRequested
                        && doc._storyPauseRequested.runToken === storyRunToken
                        && doc._storyPauseRequested.storyIndex === storyIndex;
                    if (pauseRequested) return;
                    handleSpeechCompletion();
                }};

                doc._storyLastSpeechKey = speechKey;
                synth.cancel();
                if (typeof synth.resume === 'function') {{
                    synth.resume();
                }}
                synth.speak(utterance);

                startWatchdog = window.setTimeout(function() {{
                    if (completionHandled || speechStarted) return;
                    if (synth.speaking || synth.pending) return;
                    doc._storyLastSpeechKey = null;
                    handleSpeechCompletion();
                }}, 1400);
            }}

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
        }})();
        </script>
        """,
        height=0,
    )


def render_story_view():
    story_card = current_story_card()
    spanish_text = story_card["answer"]
    translation_text = story_card["word"] if st.session_state.story_translation_on else ""
    story_position = st.session_state.index + 1
    story_total = len(st.session_state.order)
    story_progress_pct = (story_position / story_total * 100) if story_total else 0
    story_line_number = current_card_index() + 1
    story_count_text = f"{story_position} of {story_total}"
    story_progress_text = (
        f"Line: {story_line_number}    {story_count_text}"
        if st.session_state.story_random_on
        else story_count_text
    )
    playback_options = {
        "auto": "continuous",
        "step": "stop on every line",
    }
    ordered_story_cards = [st.session_state.cards[idx] for idx in st.session_state.order]
    ordered_story_line_numbers = [idx + 1 for idx in st.session_state.order]
    story_pause_delays = [
        story_pause_seconds_for_text(card["answer"])
        for card in ordered_story_cards
    ]
    story_pause_delay = story_pause_delays[st.session_state.index] if story_pause_delays else 0.0

    with st.container(key="storyoptions_stack_wrap"):
        with st.container(key="storyplayback_row_wrap"):
            playback_label_col, playback_radio_col = st.columns([0.44, 0.56], gap="small")
            with playback_label_col:
                st.markdown('<div class="story-option-row">Story Playback:</div>', unsafe_allow_html=True)
            with playback_radio_col:
                playback_choice = st.radio(
                    "Playback",
                    options=list(playback_options.keys()),
                    index=0 if st.session_state.story_playback_mode == "continuous" else 1,
                    horizontal=True,
                    label_visibility="collapsed",
                    key="story_playback_radio",
                )
        with st.container(key="storytransaudio_row_wrap"):
            ta_cols = st.columns([0.20, 0.12, 0.14, 0.12, 0.16, 0.12], gap="small")
            with ta_cols[0]:
                st.markdown('<div class="story-option-row">Translate:</div>', unsafe_allow_html=True)
            with ta_cols[1]:
                translation_choice = st.radio(
                    "Translate",
                    options=["ON", "OFF"],
                    index=0 if st.session_state.story_translation_on else 1,
                    horizontal=True,
                    label_visibility="collapsed",
                    key="story_translation_radio",
                )
            with ta_cols[2]:
                st.markdown('<div class="story-option-row">Audio:</div>', unsafe_allow_html=True)
            with ta_cols[3]:
                audio_choice = st.radio(
                    "Audio",
                    options=["ON", "OFF"],
                    index=0 if st.session_state.story_audio_on else 1,
                    horizontal=True,
                    label_visibility="collapsed",
                    key="story_audio_radio",
                )
            with ta_cols[4]:
                st.markdown('<div class="story-option-row">Random:</div>', unsafe_allow_html=True)
            with ta_cols[5]:
                random_choice = st.radio(
                    "Random",
                    options=["ON", "OFF"],
                    index=0 if st.session_state.story_random_on else 1,
                    horizontal=True,
                    label_visibility="collapsed",
                    key="story_random_radio",
                )
    new_playback_mode = playback_options[playback_choice]
    if new_playback_mode != st.session_state.story_playback_mode:
        st.session_state.story_playback_mode = new_playback_mode
        st.rerun()

    translation_enabled = translation_choice == "ON"
    if translation_enabled != st.session_state.story_translation_on:
        st.session_state.story_translation_on = translation_enabled
        st.rerun()

    audio_enabled = audio_choice == "ON"
    if audio_enabled != st.session_state.story_audio_on:
        st.session_state.story_audio_on = audio_enabled
        st.rerun()

    random_enabled = random_choice == "ON"
    if random_enabled != st.session_state.story_random_on:
        st.session_state.story_random_on = random_enabled
        rebuild_story_order()
        reset_story_playback()
        st.rerun()

    story_spanish_html_lines = [
        format_word(card["answer"], 'fc-word', 'fc-note')
        for card in ordered_story_cards
    ]
    story_translation_html_lines = [
        format_word(card["word"], 'fc-answer', 'fc-answer-note')
        if translation_enabled else '<div class="fc-word-placeholder">&nbsp;</div>'
        for card in ordered_story_cards
    ]
    last_story_index = max(len(ordered_story_cards) - 1, 0)
    story_show_end_controls = (
        bool(ordered_story_cards)
        and st.session_state.story_started
        and st.session_state.index >= last_story_index
    )

    if story_show_end_controls:
        with st.container(key="storycontrol_row_wrap"):
            control_cols = st.columns(3, gap="small")
            with control_cols[0]:
                with st.container(key="storyrepeat_wrap"):
                    if st.button("REPEAT", key="story_repeat_btn", use_container_width=True):
                        repeat_story()
                        st.rerun()
            with control_cols[1]:
                with st.container(key="storynew_wrap"):
                    if st.button("NEW", key="story_new_btn", use_container_width=True):
                        go_back_to_deck_picker()
                        st.rerun()
            with control_cols[2]:
                with st.container(key="storyend_wrap"):
                    if st.button("END", key="story_end_btn", use_container_width=True):
                        end_story_to_final_screen()
                        st.rerun()
    elif st.session_state.story_running:
        with st.container(key="storycontrol_row_wrap"):
            control_cols = st.columns(3, gap="small")
            with control_cols[0]:
                with st.container(key="storypause_wrap"):
                    if st.button("PAUSE", key="story_pause_btn", use_container_width=True):
                        pause_story()
                        st.rerun()
            with control_cols[1]:
                with st.container(key="storystop_wrap"):
                    if st.button("STOP", key="story_stop_btn", use_container_width=True):
                        stop_story()
                        st.rerun()
            with control_cols[2]:
                with st.container(key="storynext_wrap"):
                    if st.button("NEXT", key="story_next_running_btn", use_container_width=True):
                        advance_story_line()
                        st.rerun()
    else:
        with st.container(key="storycontrol_row_wrap"):
            control_cols = st.columns(3, gap="small")
            with control_cols[0]:
                with st.container(key="storystart_wrap"):
                    start_label = "RESUME" if st.session_state.story_started else "START"
                    if st.button(start_label, key="story_start_btn", use_container_width=True):
                        start_story()
                        st.rerun()
            with control_cols[1]:
                with st.container(key="storystop_wrap"):
                    if st.button("STOP", key="story_stop_btn_idle", use_container_width=True):
                        stop_story()
                        st.rerun()
            with control_cols[2]:
                st.markdown('<div class="story-control-spacer"></div>', unsafe_allow_html=True)

    if not audio_enabled:
        render_story_mobile_controller_cleanup()

    if audio_enabled:
        render_story_start_unlock_handler(
            [card["answer"] for card in ordered_story_cards],
            story_spanish_html_lines,
            story_translation_html_lines,
            story_pause_delays,
            ordered_story_line_numbers,
            st.session_state.index,
            auto_advance=st.session_state.story_playback_mode == "continuous",
            delay_seconds=story_pause_delay,
            running=st.session_state.story_running,
            resume_next=st.session_state.story_resume_next,
        )

    if not st.session_state.story_started:
        return

    st.markdown(
        "<div class='story-progress'>"
        "<div class='story-progress-head'>"
        "<div class='story-progress-label'>Sentence</div>"
        f"<div class='story-progress-value' id='story-progress-value'>{story_progress_text}</div>"
        "</div>"
        "<div class='story-progress-track'>"
        f"<div class='story-progress-fill' id='story-progress-fill' style='width:{story_progress_pct:.2f}%'></div>"
        "</div>"
        "</div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<div class='story-pause-readout'>"
        "<div class='story-pause-readout-label'>Pause target</div>"
        f"<div class='story-pause-readout-value' id='story-pause-readout-value'>{story_pause_delay:.2f}s</div>"
        "</div>",
        unsafe_allow_html=True,
    )

    story_box_shield = story_box_shield_html(False)

    spanish_html = (
        '<div class="story-display-block">'
        + story_box_shield +
        '<div class="fc-section-label">Spanish</div>'
        + '<div id="story-spanish-content">'
        + format_word(spanish_text, 'fc-word', 'fc-note')
        + '</div>'
        + '</div>'
    )
    st.markdown(spanish_html, unsafe_allow_html=True)

    if translation_enabled:
        translation_inner = format_word(translation_text, 'fc-answer', 'fc-answer-note')
        translation_html = (
            '<div class="story-display-block">'
            + story_box_shield +
            '<div class="fc-section-label">Translation</div>'
            + '<div id="story-translation-content">'
            + translation_inner
            + '</div>'
            + '</div>'
        )
    else:
        translation_html = (
            '<div class="story-display-block story-display-block-empty">'
            + story_box_shield +
            '<div class="fc-section-label">Translation</div>'
            '<div id="story-translation-content"><div class="fc-word-placeholder">&nbsp;</div></div>'
            '</div>'
        )
    st.markdown(translation_html, unsafe_allow_html=True)
    render_story_box_shield_handler()

    with st.container(key="storyadvance_hidden_wrap"):
        st.button("__story_next_hidden__", key="story_advance_hidden_btn", on_click=advance_story_line)
    with st.container(key="storyfinish_hidden_wrap"):
        st.button("__story_finish_hidden__", key="story_finish_hidden_btn", on_click=finish_story)
    with st.container(key="storyresumenext_hidden_wrap"):
        st.button("__story_resume_next_hidden__", key="story_resume_next_hidden_btn", on_click=mark_story_resume_next)

    if not st.session_state.story_running:
        render_story_paused_cleanup()

    if audio_enabled and st.session_state.story_running:
        render_story_pause_request_guard()
        render_story_audio_autoplay(
            spanish_text,
            auto_advance=st.session_state.story_playback_mode == "continuous",
            delay_seconds=story_pause_delay,
        )

    if st.session_state.story_playback_mode == "stop on every line" and st.session_state.story_running:
        pass
    elif st.session_state.story_running and not audio_enabled:
        render_story_auto_advance(story_pause_delay)

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


def inject_tap_reveal(show_answer, auto_speak_enabled=False, auto_speak_text=""):
    show_str = "true" if show_answer else "false"
    auto_speak_str = "true" if auto_speak_enabled else "false"
    speech_rate = speech_rate_value()
    components.html("""
    <script>
    (function() {
        var parentWindow = window.parent;
        var doc = parentWindow.document;
        var showAnswer = """ + show_str + """;
        var autoSpeakEnabled = """ + auto_speak_str + """;
        var speechText = """ + json.dumps(strip_spoken_text(auto_speak_text)) + """;
        var speechRate = """ + json.dumps(speech_rate) + """;

        function speakSpanishNow() {
            if (!autoSpeakEnabled || !speechText || !doc || typeof doc._fcSpeakSpanish !== 'function') return;
            doc._fcSpeakSpanish({
                text: speechText,
                rate: speechRate,
                key: 'reveal|' + speechText + '|' + speechRate,
                cancelFirst: true,
            });
        }

        function clickShowAnswerButton() {
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
            if (doc._showAnswerAutoSpeakHandler) {
                var existingShowBtn = doc.querySelector('.st-key-showanswer_wrap button');
                if (existingShowBtn) {
                    existingShowBtn.removeEventListener('click', doc._showAnswerAutoSpeakHandler, true);
                    existingShowBtn.removeEventListener('touchend', doc._showAnswerAutoSpeakHandler, true);
                }
            }
            doc._fcHandler = function(e) {
                if (!e.target.closest('.fc-block')) return;
                if (!showAnswer) {
                    speakSpanishNow();
                    clickShowAnswerButton();
                }
            };
            doc.body.addEventListener('click', doc._fcHandler);

            var showBtn = doc.querySelector('.st-key-showanswer_wrap button');
            if (showBtn) {
                doc._showAnswerAutoSpeakHandler = function() {
                    if (!showAnswer) {
                        speakSpanishNow();
                    }
                };
                showBtn.addEventListener('click', doc._showAnswerAutoSpeakHandler, true);
                showBtn.addEventListener('touchend', doc._showAnswerAutoSpeakHandler, true);
            }
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


def inject_flashcard_speech_runtime():
    components.html(
        """
        <script>
        (function() {
            var parentWindow = window.parent;
            var doc = parentWindow.document;
            var synth = parentWindow.speechSynthesis || window.speechSynthesis;
            var UtteranceCtor = parentWindow.SpeechSynthesisUtterance || window.SpeechSynthesisUtterance;

            if (!doc || !synth || !UtteranceCtor) return;
            if (doc._fcSpeechRuntimeInstalled) return;

            doc._preferredVoicePools = {
                en: {
                    female: ['Ava (Premium)', 'Samantha (Enhanced)', 'Zoe (Premium)'],
                    male: ['Evan (Enhanced)', 'Nathan (Enhanced)', 'Nicky (Enhanced)']
                },
                es: {
                    female: ['Angélica (Enhanced)', 'Paulina (Enhanced)', 'Marisol (Premium)'],
                    male: ['Juan (Enhanced)', 'Jorge (Enhanced)']
                }
            };

            function normalizeVoiceName(value) {
                return (value || '')
                    .toLowerCase()
                    .normalize('NFD')
                    .replace(/[\u0300-\u036f]/g, '')
                    .replace(/[^a-z0-9]+/g, ' ')
                    .trim();
            }

            function inferGender(voice) {
                var normalized = normalizeVoiceName((voice && voice.name) || '');
                var femaleTokens = ['ava', 'samantha', 'zoe', 'angelica', 'paulina', 'marisol', 'female', 'woman', 'victoria', 'zira', 'karen', 'monica'];
                var maleTokens = ['evan', 'nathan', 'nicky', 'juan', 'jorge', 'male', 'man', 'alex', 'daniel', 'aaron'];
                if (femaleTokens.some(function(token) { return normalized.indexOf(token) !== -1; })) return 'female';
                if (maleTokens.some(function(token) { return normalized.indexOf(token) !== -1; })) return 'male';
                return null;
            }

            function languageCandidates(voices, language) {
                var lowerLanguage = (language || '').toLowerCase();
                if (lowerLanguage === 'es') {
                    return voices.filter(function(voice) {
                        var lang = (voice.lang || '').toLowerCase();
                        return lang === 'es-mx' || lang === 'es-us' || lang === 'es-es' || lang.indexOf('es') === 0;
                    });
                }
                return voices.filter(function(voice) {
                    var lang = (voice.lang || '').toLowerCase();
                    return lang === 'en-us' || lang === 'en-gb' || lang === 'en-au' || lang.indexOf('en') === 0;
                });
            }

            function randomChoice(items) {
                if (!items || !items.length) return null;
                return items[Math.floor(Math.random() * items.length)];
            }

            function pushUnique(target, voice, seen) {
                if (!voice) return;
                var key = (voice.voiceURI || voice.name || '') + '|' + (voice.lang || '');
                if (seen[key]) return;
                seen[key] = true;
                target.push(voice);
            }

            function matchedVoicesForTokens(candidates, tokens) {
                var highQualityMatches = [];
                var baseMatches = [];
                var seenHigh = {};
                var seenBase = {};
                if (!tokens || !tokens.length) return [];

                tokens.forEach(function(token) {
                    var normalizedToken = normalizeVoiceName(token);
                    var baseMatch = normalizedToken.match(/^(.+?)(?:\\s+(premium|enhanced))?$/);
                    var normalizedBase = baseMatch ? (baseMatch[1] || '').trim() : normalizedToken;
                    var normalizedQuality = baseMatch ? (baseMatch[2] || '').trim() : '';

                    candidates.forEach(function(voice) {
                        var normalizedName = normalizeVoiceName(voice.name || '');
                        var normalizedUri = normalizeVoiceName(voice.voiceURI || '');
                        var haystack = (normalizedName + ' ' + normalizedUri).trim();
                        if (!normalizedBase || haystack.indexOf(normalizedBase) === -1) {
                            return;
                        }

                        if (normalizedQuality && haystack.indexOf(normalizedQuality) !== -1) {
                            pushUnique(highQualityMatches, voice, seenHigh);
                        }
                        pushUnique(baseMatches, voice, seenBase);
                    });

                    candidates.forEach(function(voice) {
                        var normalizedName = normalizeVoiceName(voice.name || '');
                        var normalizedUri = normalizeVoiceName(voice.voiceURI || '');
                        var haystack = (normalizedName + ' ' + normalizedUri).trim();
                        if (haystack === normalizedToken) {
                            pushUnique(highQualityMatches, voice, seenHigh);
                            pushUnique(baseMatches, voice, seenBase);
                        }
                    });
                });

                highQualityMatches.forEach(function(voice) {
                    pushUnique(baseMatches, voice, seenBase);
                });

                return highQualityMatches.concat(
                    baseMatches.filter(function(voice) {
                        var key = (voice.voiceURI || voice.name || '') + '|' + (voice.lang || '');
                        return !seenHigh[key];
                    })
                );
            }

            doc._fcPickPreferredVoice = function(language, options) {
                options = options || {};
                var voices = synth.getVoices ? synth.getVoices() : [];
                var candidates = languageCandidates(voices, language);
                var languageKey = language === 'es' ? 'es' : 'en';
                var preferredGender = options.preferredGender || null;
                var randomize = options.randomize !== false;
                var pool = doc._preferredVoicePools[languageKey] || { female: [], male: [] };
                var genders = preferredGender ? [preferredGender] : ['female', 'male'];
                var preferredMatches = [];
                var seen = {};

                genders.forEach(function(gender) {
                    matchedVoicesForTokens(candidates, pool[gender] || []).forEach(function(voice) {
                        pushUnique(preferredMatches, voice, seen);
                    });
                });

                if (preferredMatches.length) {
                    return randomize ? randomChoice(preferredMatches) : preferredMatches[0];
                }

                if (preferredGender) {
                    var genderMatches = candidates.filter(function(voice) {
                        return inferGender(voice) === preferredGender;
                    });
                    if (genderMatches.length) {
                        return randomize ? randomChoice(genderMatches) : genderMatches[0];
                    }
                }

                if (candidates.length) {
                    return randomize ? randomChoice(candidates) : candidates[0];
                }

                return null;
            };

            function pickVoice(language, options) {
                if (typeof doc._fcPickPreferredVoice === 'function') {
                    return doc._fcPickPreferredVoice(language, options);
                }
                var voices = synth.getVoices ? synth.getVoices() : [];
                return languageCandidates(voices, language)[0] || null;
            }

            function clearVoiceHandler() {
                if (!doc._fcSpeechVoicesChangedHandler) return;

                if (typeof synth.removeEventListener === 'function') {
                    synth.removeEventListener('voiceschanged', doc._fcSpeechVoicesChangedHandler);
                } else if (synth.onvoiceschanged === doc._fcSpeechVoicesChangedHandler) {
                    synth.onvoiceschanged = null;
                }

                doc._fcSpeechVoicesChangedHandler = null;
            }

            function clearPendingTimer() {
                if (doc._fcSpeechPendingTimer) {
                    parentWindow.clearTimeout(doc._fcSpeechPendingTimer);
                    doc._fcSpeechPendingTimer = null;
                }
            }

            function clearPendingSpeech() {
                clearPendingTimer();
                clearVoiceHandler();
            }

            doc._fcSpeakSpanish = function(config) {
                config = config || {};

                var speechText = (config.text || '').trim();
                var speechRate = config.rate || 1;
                var speechKey = config.key || null;
                var cancelFirst = config.cancelFirst !== false;
                var preferredGender = config.preferredGender || null;
                var randomize = config.randomize !== false;

                if (!speechText) return;
                if (speechKey && doc._fcSpeechLastKey === speechKey) return;

                doc._fcSpeechLastKey = speechKey;
                clearPendingSpeech();

                function speakNow() {
                    var utterance = new UtteranceCtor(speechText);
                    var voice = pickVoice('es', {
                        preferredGender: preferredGender,
                        randomize: randomize,
                    });

                    utterance.lang = voice ? voice.lang : 'es-ES';
                    utterance.rate = speechRate;
                    if (voice) utterance.voice = voice;

                    doc._fcSpeechActiveUtterance = utterance;
                    utterance.onend = utterance.onerror = function() {
                        if (doc._fcSpeechActiveUtterance === utterance) {
                            doc._fcSpeechActiveUtterance = null;
                        }
                    };

                    if (cancelFirst) {
                        try {
                            synth.cancel();
                        } catch (error) {
                        }
                    }

                    doc._fcSpeechPendingTimer = parentWindow.setTimeout(function() {
                        doc._fcSpeechPendingTimer = null;
                        try {
                            synth.speak(utterance);
                        } catch (error) {
                            if (speechKey) {
                                doc._fcSpeechLastKey = null;
                            }
                        }
                    }, cancelFirst ? 60 : 0);
                }

                if (synth.getVoices && synth.getVoices().length) {
                    speakNow();
                    return;
                }

                var handled = false;
                doc._fcSpeechVoicesChangedHandler = function() {
                    if (handled) return;
                    handled = true;
                    clearVoiceHandler();
                    speakNow();
                };

                if (typeof synth.addEventListener === 'function') {
                    synth.addEventListener('voiceschanged', doc._fcSpeechVoicesChangedHandler);
                } else {
                    synth.onvoiceschanged = doc._fcSpeechVoicesChangedHandler;
                }

                doc._fcSpeechPendingTimer = parentWindow.setTimeout(function() {
                    doc._fcSpeechPendingTimer = null;
                    if (handled) return;
                    handled = true;
                    clearVoiceHandler();
                    speakNow();
                }, 250);
            };

            doc._fcSpeechRuntimeInstalled = true;
        })();
        </script>
        """,
        height=0,
    )


def inject_speech_priming():
    components.html(
        """
        <script>
        (function() {
            var doc = window.parent.document;
            var synth = window.parent.speechSynthesis || window.speechSynthesis;

            if (!doc || !synth) return;
            if (doc._fcSpeechPrimingAttached) return;

            function primeSpeech() {
                if (doc._fcSpeechPrimed) return;
                doc._fcSpeechPrimed = true;

                try {
                    if (synth.getVoices) {
                        synth.getVoices();
                    }

                    var utterance = new SpeechSynthesisUtterance('.');
                    utterance.volume = 0;
                    utterance.rate = 1;
                    synth.speak(utterance);
                    setTimeout(function() {
                        synth.cancel();
                    }, 0);
                } catch (error) {
                    doc._fcSpeechPrimed = false;
                }
            }

            doc._fcSpeechPrimeHandler = function(event) {
                var target = event.target;
                if (!target || !target.closest) return;
                if (
                    target.closest('input[type="checkbox"]') ||
                    target.closest('.fc-block') ||
                    target.closest('.st-key-showanswer_wrap button') ||
                    target.closest('.st-key-correct_wrap button') ||
                    target.closest('.st-key-repeat_wrap button') ||
                    target.closest('.st-key-autospeak_on_wrap button') ||
                    target.closest('.st-key-autospeak_off_wrap button') ||
                    target.closest('.st-key-speaker_wrap button')
                ) {
                    primeSpeech();
                }
            };

            doc.body.addEventListener('click', doc._fcSpeechPrimeHandler, true);
            doc.body.addEventListener('touchend', doc._fcSpeechPrimeHandler, true);
            doc._fcSpeechPrimingAttached = true;
        })();
        </script>
        """,
        height=0,
    )


def toggle_auto_speak_spanish():
    st.session_state.auto_speak_spanish = not st.session_state.auto_speak_spanish
    if st.session_state.auto_speak_spanish:
        st.session_state.auto_speak_spanish_generation += 1
    store_active_person_prefs()
    save_prefs(current_prefs())


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
            var parentWindow = window.parent;
            var doc = parentWindow.document;
            var button = document.getElementById('speak-btn');

            if (!button || !doc || !speechText) return;

            function speakFromTap(event) {{
                if (event) event.preventDefault();
                if (typeof doc._fcSpeakSpanish !== 'function') return;
                doc._fcSpeakSpanish({{
                    text: speechText,
                    rate: speechRate,
                    cancelFirst: true,
                }});
            }}

            button.addEventListener('click', speakFromTap);
            button.addEventListener('touchend', speakFromTap);
        }})();
        </script>
        """,
        height=60,
    )


def render_auto_speak_spanish(text, speech_key):
    speech_text = strip_spoken_text(text)
    speech_rate = speech_rate_value()
    components.html(
        f"""
        <script>
        (function() {{
            var parentWindow = window.parent;
            var doc = parentWindow.document;
            var synth = parentWindow.speechSynthesis || window.speechSynthesis;
            var speechText = {json.dumps(speech_text)};
            var speechRate = {speech_rate};
            var speechKey = {json.dumps(speech_key)};
            if (!doc || !synth || !speechText || !speechKey) return;
            if (doc._autoSpeakSpanishKey === speechKey) return;
            doc._autoSpeakSpanishKey = speechKey;

            if (typeof doc._fcSpeakSpanish !== 'function') return;
            doc._fcSpeakSpanish({{
                text: speechText,
                rate: speechRate,
                key: speechKey,
                cancelFirst: true,
            }});
        }})();
        </script>
        """,
        height=0,
    )


def render_regular_auto_mode_controls():
    with st.container(key="regular_auto_controls_wrap"):
        col1, col2 = st.columns(2, gap="medium")
        with col1:
            auto_mode_value = st.checkbox(
                "AUTO mode",
                key="regular_auto_mode_checkbox",
            )
        with col2:
            if auto_mode_value:
                repeat_value = st.checkbox(
                    "REPEAT 2x",
                    key="regular_auto_repeat_checkbox",
                )
            else:
                repeat_value = st.session_state["regular_auto_repeat_spanish"]
                st.markdown('<div class="regular-auto-controls-spacer"></div>', unsafe_allow_html=True)

    if auto_mode_value != st.session_state["regular_auto_mode"]:
        st.session_state["regular_auto_mode"] = auto_mode_value
        st.session_state["regular_auto_generation"] += 1
        if auto_mode_value:
            st.session_state.show_answer = False
        st.rerun()

    if repeat_value != st.session_state["regular_auto_repeat_spanish"]:
        st.session_state["regular_auto_repeat_spanish"] = repeat_value
        st.session_state["regular_auto_generation"] += 1
        st.rerun()


def render_voice_inspector():
    with st.expander("Temporary Voice Inspector"):
        st.caption(
            "Open this on the iPhone, then tap Refresh Voice List. It shows the exact Safari-exposed voice name, quality hints, and identifier."
        )
        components.html(
            """
            <style>
            body {
                margin: 0;
                padding: 0.35rem 0 0;
                background: transparent;
                color: inherit;
                font-family: 'DM Sans', sans-serif;
            }
            .voice-inspector {
                display: flex;
                flex-direction: column;
                gap: 0.65rem;
            }
            .voice-inspector-controls {
                display: flex;
                gap: 0.5rem;
                align-items: center;
                flex-wrap: wrap;
            }
            .voice-inspector button {
                border: 1px solid #5a6b7a;
                background: #edf3f7;
                color: #123;
                border-radius: 0.6rem;
                padding: 0.45rem 0.8rem;
                font-size: 0.92rem;
                font-weight: 600;
                cursor: pointer;
            }
            .voice-inspector-status {
                font-size: 0.86rem;
                opacity: 0.8;
            }
            .voice-inspector pre {
                margin: 0;
                padding: 0.75rem;
                white-space: pre-wrap;
                word-break: break-word;
                border-radius: 0.7rem;
                background: rgba(127, 127, 127, 0.1);
                border: 1px solid rgba(127, 127, 127, 0.25);
                font-size: 0.8rem;
                line-height: 1.35;
                max-height: 19rem;
                overflow: auto;
            }
            </style>
            <div class="voice-inspector">
                <div class="voice-inspector-controls">
                    <button id="voice-inspector-refresh" type="button">Refresh Voice List</button>
                    <div id="voice-inspector-status" class="voice-inspector-status">Loading voices...</div>
                </div>
                <pre id="voice-inspector-output">Loading voices...</pre>
            </div>
            <script>
            (function() {
                var parentWindow = window.parent;
                var synth = parentWindow.speechSynthesis || window.speechSynthesis;
                var refreshButton = document.getElementById('voice-inspector-refresh');
                var statusEl = document.getElementById('voice-inspector-status');
                var outputEl = document.getElementById('voice-inspector-output');

                function setStatus(message) {
                    if (statusEl) statusEl.textContent = message;
                }

                function setOutput(message) {
                    if (outputEl) outputEl.textContent = message;
                }

                function normalizeVoiceName(value) {
                    return (value || '')
                        .toLowerCase()
                        .normalize('NFD')
                        .replace(/[\u0300-\u036f]/g, '')
                        .replace(/[^a-z0-9]+/g, ' ')
                        .trim();
                }

                function detectQuality(voice) {
                    var haystack = normalizeVoiceName((voice && voice.name) || '') + ' ' + normalizeVoiceName((voice && voice.voiceURI) || '');
                    if (haystack.indexOf('premium') !== -1) return 'premium';
                    if (haystack.indexOf('enhanced') !== -1) return 'enhanced';
                    return 'standard/unknown';
                }

                function summarizeVoice(voice, index) {
                    return [
                        '#' + (index + 1),
                        'lang: ' + (voice.lang || ''),
                        'name: ' + (voice.name || ''),
                        'qualityHint: ' + detectQuality(voice),
                        'default: ' + (voice.default ? 'yes' : 'no'),
                        'localService: ' + (voice.localService ? 'yes' : 'no'),
                        'voiceURI: ' + (voice.voiceURI || '')
                    ].join('\\n');
                }

                function renderVoices() {
                    if (!synth || !synth.getVoices) {
                        setStatus('Speech synthesis not available');
                        setOutput('This browser does not expose speechSynthesis.getVoices().');
                        return;
                    }

                    var voices = synth.getVoices() || [];
                    var sortedVoices = voices.slice().sort(function(a, b) {
                        var langA = (a.lang || '').toLowerCase();
                        var langB = (b.lang || '').toLowerCase();
                        if (langA !== langB) return langA < langB ? -1 : 1;
                        var nameA = (a.name || '').toLowerCase();
                        var nameB = (b.name || '').toLowerCase();
                        if (nameA !== nameB) return nameA < nameB ? -1 : 1;
                        return ((a.voiceURI || '').toLowerCase() < (b.voiceURI || '').toLowerCase()) ? -1 : 1;
                    });

                    setStatus(sortedVoices.length + ' voices found');
                    if (!sortedVoices.length) {
                        setOutput('No voices returned yet. Tap Refresh again after interacting with the page once.');
                        return;
                    }

                    setOutput(sortedVoices.map(summarizeVoice).join('\\n\\n---\\n\\n'));
                }

                refreshButton.addEventListener('click', function(event) {
                    event.preventDefault();
                    renderVoices();
                });

                try {
                    setStatus('Checking voices...');
                    setOutput('Checking voices...');
                    renderVoices();

                    if (synth) {
                        if (typeof synth.addEventListener === 'function') {
                            synth.addEventListener('voiceschanged', renderVoices);
                        } else {
                            var oldHandler = synth.onvoiceschanged;
                            synth.onvoiceschanged = function() {
                                if (typeof oldHandler === 'function') {
                                    oldHandler();
                                }
                                renderVoices();
                            };
                        }
                    }
                } catch (error) {
                    setStatus('Inspector error');
                    setOutput((error && error.message) ? error.message : String(error));
                }
            })();
            </script>
            """,
            height=420,
        )


def render_regular_auto_hidden_buttons():
    with st.container(key="regularautoreveal_hidden_wrap"):
        st.button("__regular_auto_reveal__", key="regular_auto_reveal_btn", on_click=reveal_answer)
    with st.container(key="regularautoadvance_hidden_wrap"):
        st.button("__regular_auto_advance__", key="regular_auto_advance_btn", on_click=advance_auto_card)


def render_regular_auto_mode_cleanup():
    components.html(
        """
        <script>
        (function() {
            var parentWindow = window.parent;
            var doc = parentWindow.document;
            var synth = parentWindow.speechSynthesis || window.speechSynthesis;
            var controller = doc && doc._regularAutoController;

            if (controller && controller.timerIds) {
                controller.timerIds.forEach(function(timerId) {
                    parentWindow.clearTimeout(timerId);
                });
                controller.timerIds = [];
                controller.phaseKey = null;
            }

            if (synth) {
                try {
                    synth.cancel();
                } catch (error) {
                }
            }
        })();
        </script>
        """,
        height=0,
    )


def render_regular_auto_mode_driver(phase, phase_key, text, language, pause_after_seconds, preferred_gender, repeat_spanish):
    speech_text = strip_spoken_text(text)
    speech_rate = speech_rate_value()
    action_delay_ms = max(int(pause_after_seconds * 1000), 0)
    components.html(
        f"""
        <script>
        (function() {{
            var parentWindow = window.parent;
            var doc = parentWindow.document;
            var synth = parentWindow.speechSynthesis || window.speechSynthesis;
            var UtteranceCtor = parentWindow.SpeechSynthesisUtterance || window.SpeechSynthesisUtterance;
            var config = {{
                phase: {json.dumps(phase)},
                phaseKey: {json.dumps(phase_key)},
                text: {json.dumps(speech_text)},
                language: {json.dumps(language)},
                rate: {speech_rate},
                delayMs: {action_delay_ms},
                preferredGender: {json.dumps(preferred_gender)},
                repeatSpanish: {str(repeat_spanish).lower()},
            }};

            if (!doc || !synth || !UtteranceCtor || !config.text || !config.phaseKey) return;

            var controller = doc._regularAutoController || {{ timerIds: [], phaseKey: null }};
            doc._regularAutoController = controller;

            function clearTimers() {{
                if (!controller.timerIds) return;
                controller.timerIds.forEach(function(timerId) {{
                    parentWindow.clearTimeout(timerId);
                }});
                controller.timerIds = [];
            }}

            function clearController(cancelSpeech) {{
                clearTimers();
                if (cancelSpeech) {{
                    try {{
                        synth.cancel();
                    }} catch (error) {{
                    }}
                }}
            }}

            if (controller.phaseKey === config.phaseKey) return;
            clearController(true);
            controller.phaseKey = config.phaseKey;

            function queueTimeout(callback, delayMs) {{
                var timerId = parentWindow.setTimeout(callback, delayMs);
                controller.timerIds.push(timerId);
            }}

            function pickVoice(language, preferredGender) {{
                if (doc && typeof doc._fcPickPreferredVoice === 'function') {{
                    return doc._fcPickPreferredVoice(language, {{
                        preferredGender: preferredGender,
                        randomize: true,
                    }});
                }}

                var voices = synth.getVoices ? synth.getVoices() : [];
                return voices[0] || null;
            }}

            function estimatedDurationMs(text, rate) {{
                var rawText = text || '';
                var chars = rawText.length || 1;
                var words = rawText.trim() ? rawText.trim().split(/\\s+/).length : 1;
                var punctuationPauses = (rawText.match(/[,:;.!?]/g) || []).length;
                var safeRate = rate > 0 ? rate : 1;
                var estimate = (words * 470) + (chars * 34) + (punctuationPauses * 220) + 500;
                return Math.max(1200, Math.round(estimate / safeRate));
            }}

            function clickHiddenButton(selector) {{
                var button = doc.querySelector(selector);
                if (!button) return false;
                button.click();
                button.dispatchEvent(new MouseEvent('click', {{ bubbles: true }}));
                return true;
            }}

            function speakOnce(text, language, preferredGender, onDone) {{
                var voice = pickVoice(language, preferredGender);
                var utterance = new UtteranceCtor(text);
                var done = false;
                var watchdogMs = estimatedDurationMs(text, config.rate) + 1200;

                utterance.lang = voice ? voice.lang : (language === 'es' ? 'es-ES' : 'en-US');
                utterance.rate = config.rate;
                if (voice) utterance.voice = voice;

                function finish() {{
                    if (done || controller.phaseKey !== config.phaseKey) return;
                    done = true;
                    onDone();
                }}

                utterance.onend = finish;
                utterance.onerror = finish;

                queueTimeout(finish, watchdogMs);

                try {{
                    synth.speak(utterance);
                }} catch (error) {{
                    finish();
                }}
            }}

            function speakSequence(onDone) {{
                speakOnce(config.text, config.language, config.preferredGender, function() {{
                    if (!(config.repeatSpanish && config.language === 'es')) {{
                        onDone();
                        return;
                    }}

                    queueTimeout(function() {{
                        if (controller.phaseKey !== config.phaseKey) return;
                        speakOnce(config.text, config.language, config.preferredGender, onDone);
                    }}, 1000);
                }});
            }}

            speakSequence(function() {{
                queueTimeout(function() {{
                    if (controller.phaseKey !== config.phaseKey) return;
                    if (config.phase === 'prompt') {{
                        clickHiddenButton('.st-key-regularautoreveal_hidden_wrap button');
                        return;
                    }}
                    clickHiddenButton('.st-key-regularautoadvance_hidden_wrap button');
                }}, config.delayMs);
            }});
        }})();
        </script>
        """,
        height=0,
    )


def stats_card_html(shown, total, correct, repeat, scored_total):
    pct        = int(shown / total * 100) if total > 0 else 0
    accuracy   = int(correct / scored_total * 100) if scored_total > 0 else 0
    missed_pct = int(repeat  / scored_total * 100) if scored_total > 0 else 0
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
                "<div>"
                "<span class='title-main'>Spanish Flashcards</span>"
                "<div class='title-sub'>" + PERSON_LABELS[st.session_state.active_person] + "</div>"
                "</div>"
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
    if st.session_state.menu_open:
        return
    if st.session_state.person_selector_visible:
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
                elif st.session_state.selected_csv:
                    reset_study_state(reset_selected=False)
                st.rerun()


def render_menu():
    if not st.session_state.menu_open:
        return
    active_review_count = review_count_for(st.session_state.active_person)
    active_person_label = PERSON_LABELS[st.session_state.active_person]
    st.markdown('<div class="menu-backdrop"></div>', unsafe_allow_html=True)
    render_menu_backdrop_close_handler()
    with st.container(key="menu_modal_wrap"):
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
        st.markdown('<div class="menu-section-label" style="margin-top:0.9rem;">STORY MODE &ndash; PAUSES BETWEEN SENTENCES</div>',
                    unsafe_allow_html=True)
        story_timing_options = [5, 4, 3, 2, 1]
        st.markdown('<div class="menu-field-label">Reading speed (1 = fastest)</div>', unsafe_allow_html=True)
        new_story_reading_speed = st.radio(
            "Reading speed (1 = fastest)",
            options=story_timing_options,
            index=story_timing_options.index(st.session_state.story_reading_speed),
            horizontal=True,
            label_visibility="collapsed",
            key="story_reading_speed_radio",
        )
        if new_story_reading_speed != st.session_state.story_reading_speed:
            st.session_state.story_reading_speed = new_story_reading_speed
            store_active_person_prefs()
            st.session_state.erase_review_confirm = False
            st.rerun()
        st.markdown('<div class="menu-field-label">Pause amount (1 = shortest)</div>', unsafe_allow_html=True)
        new_story_pause_amount = st.radio(
            "Pause amount (1 = shortest)",
            options=story_timing_options,
            index=story_timing_options.index(st.session_state.story_pause_amount),
            horizontal=True,
            label_visibility="collapsed",
            key="story_pause_amount_radio",
        )
        if new_story_pause_amount != st.session_state.story_pause_amount:
            st.session_state.story_pause_amount = new_story_pause_amount
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


def render_deck_strip():
    if not st.session_state.selected_csv:
        return
    deck_name = display_deck_name(st.session_state.selected_csv)
    with st.container(key="deckstrip_row_wrap"):
        info_col, back_col = st.columns([1, 0.08], gap="small")
        with info_col:
            st.markdown(
                '<div class="deck-strip">'
                '<span class="deck-strip-label">Deck</span>'
                '<span class="deck-strip-name">' + deck_name + '</span>'
                '</div>', unsafe_allow_html=True)
        with back_col:
            with st.container(key="changedeck_wrap"):
                if st.button("←", key="change_deck_btn"):
                    go_back_to_deck_picker()
                    st.rerun()


def render_study_mode_picker():
    filename = st.session_state.selected_csv
    person = st.session_state.active_person
    progress_stats = deck_progress_stats(filename, person)
    if not progress_stats["supported"]:
        st.session_state.study_mode = "all"
        return

    total_cards = progress_stats["total"]
    completed_cards = progress_stats["completed"]
    remaining_cards = progress_stats["remaining"]
    remaining_disabled = completed_cards == 0 or remaining_cards == 0
    review_restore_count = review_add_back_count(completed_cards)
    review_disabled = completed_cards == 0 or remaining_cards <= 10 or review_restore_count == 0
    reset_disabled = completed_cards == 0

    st.markdown(
        "<div class='title-block'>"
        "<div class='title-big'>Choose Cards</div>"
        "<div class='title-big-sub'>" + PERSON_LABELS[person] + "</div>"
        "</div>",
        unsafe_allow_html=True,
    )

    with st.container(key="study_mode_picker_wrap"):
        if st.button(f"ALL ({total_cards})", key="study_all_btn", use_container_width=True):
            st.session_state.study_mode = "all"
            st.rerun()

        remaining_label = "Remaining" if completed_cards == 0 else f"Remaining ({remaining_cards} of {total_cards})"
        if st.button(
            remaining_label,
            key="study_remaining_btn",
            use_container_width=True,
            disabled=remaining_disabled,
        ):
            st.session_state.study_mode = "remaining"
            st.rerun()

        review_label = (
            "Remaining + 25%"
            if review_restore_count == 0
            else f"Remaining + 25% ({review_restore_count} added)"
        )
        if st.button(
            review_label,
            key="study_review_add_btn",
            use_container_width=True,
            disabled=review_disabled,
        ):
            restored_count = restore_completed_cards(person, filename, review_restore_count)
            if restored_count > 0:
                st.session_state.study_mode = "remaining"
                st.rerun()

        if st.button(
            "Reset",
            key="study_reset_btn",
            use_container_width=True,
            disabled=reset_disabled,
        ):
            clear_deck_progress(person, filename)
            st.session_state.study_mode = "all"
            st.rerun()


def render_buttons(show_answer, spanish_audio_text):
    if st.session_state["regular_auto_mode"]:
        with st.container(key="icon_btn_row_wrap"):
            _, center_col, _ = st.columns([0.7, 1, 0.7])
            with center_col:
                with st.container(key="quitbefore_wrap"):
                    if st.button("🛑", key="quitbefore_btn"):
                        st.session_state.quit_requested = True
                        st.rerun()
        return

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
        action_columns = st.columns(5 if review_mode else 4, gap="small")
        col1, col2, col3, col4 = action_columns[:4]
        with col1:
            with st.container(key="correct_wrap"):
                st.button("✓", key="correct_btn", on_click=mark_correct)
        with col2:
            with st.container(key="repeat_wrap"):
                st.button("?", key="repeat_btn", on_click=mark_repeat)
        with col3:
            with st.container(key="speaker_wrap"):
                render_speaker_button(spanish_audio_text)
        with col4:
            auto_speak_key = "autospeak_on_wrap" if st.session_state.auto_speak_spanish else "autospeak_off_wrap"
            auto_speak_label = "☒∞" if st.session_state.auto_speak_spanish else "☐∞"
            with st.container(key=auto_speak_key):
                st.button(auto_speak_label, key="autospeak_btn", on_click=toggle_auto_speak_spanish)
        if review_mode:
            current_card = st.session_state.cards[current_card_index()]
            delete_armed = st.session_state.delete_review_confirm_key == current_review_card_key(current_card)
            with action_columns[4]:
                with st.container(key="del_confirm_wrap" if delete_armed else "del_active_wrap"):
                    st.button("X", key="del_btn", on_click=delete_current_review_card)
            if delete_armed:
                with st.container(key="clear_delete_confirm_wrap"):
                    st.button("__clear_delete_confirm__", key="clear_delete_confirm_btn", on_click=clear_delete_review_confirm)
                render_delete_confirm_timeout()


def restart_mistakes_only():
    mistake_cards = [
        {
            "id": card.get("id"),
            "word": card["word"],
            "answer": card["answer"],
            "shown": False,
            "scored": False,
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
    st.session_state["regular_auto_mode"] = False
    st.session_state["regular_auto_repeat_spanish"] = False
    st.session_state["regular_auto_generation"] += 1
    st.session_state["regular_auto_mode_checkbox"] = False
    st.session_state["regular_auto_repeat_checkbox"] = False
    st.session_state.quit_requested = False
    st.session_state.final_exit = False
    st.session_state.menu_open = False
    st.session_state["score_actions"] = 0
    st.session_state["score_correct"] = 0
    st.session_state["score_repeat"] = 0
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
        st.markdown("<div class='mobile-deck-picker-label' style='font-size: 0.95rem; color: " + t['fg'] + ";'>Available decks:</div>", unsafe_allow_html=True)
        deck_container = st.container(height=250)
        with deck_container:
            for person in PERSON_LABELS:
                review_value = REVIEW_DECK_VALUES[person]
                if review_value not in review_deck_values:
                    continue
                review_enabled = review_deck_selectable(review_value)
                review_wrap = f"review_{person}_{'active' if review_enabled else 'inactive'}_wrap"
                with st.container(key=review_wrap):
                    with st.container(key=f"mobile_deck_entry_review_{person}_wrap"):
                        if st.button(
                            review_deck_label(person),
                            key=f"deck_btn_review_{person}",
                            use_container_width=True,
                            disabled=not review_enabled,
                        ):
                            activate_deck(review_value)
                            st.rerun()
            divider_prefix_groups = ("ESsbs", "MAC", "PoS", "sentence")
            for current_index, csv_file in enumerate(csv_files):
                deck_status = deck_picker_status(csv_file, st.session_state.active_person)
                with st.container(key=f"mobile_deck_entry_{deck_status}_{current_index}_wrap"):
                    if st.button(display_deck_name(csv_file), key=f"deck_btn_{csv_file}", use_container_width=True):
                        activate_deck(csv_file)
                        st.rerun()
                current_group = next(
                    (prefix for prefix in divider_prefix_groups if csv_file.lower().startswith(prefix.lower())),
                    None,
                )
                next_group = None
                if current_index + 1 < len(csv_files):
                    next_file = csv_files[current_index + 1]
                    next_group = next(
                        (prefix for prefix in divider_prefix_groups if next_file.lower().startswith(prefix.lower())),
                        None,
                    )
                if current_group and current_group != next_group:
                    st.markdown('<div class="mobile-deck-divider"></div>', unsafe_allow_html=True)
            render_mobile_deck_picker_height_fix()

    with st.container(key="desktop_deck_picker_wrap"):
        selected = st.selectbox(
            "Available decks:",
            deck_options,
            index=0,
            format_func=lambda value: value if value == "-- Choose a deck --" else deck_picker_label(value, st.session_state.active_person),
        )
        if selected != deck_options[0]:
            if review_deck_selectable(selected):
                activate_deck(selected)
                st.rerun()
    st.stop()

if not is_review_deck(st.session_state.selected_csv) and not is_story_deck(st.session_state.selected_csv) and st.session_state.study_mode is None:
    progress_stats = deck_progress_stats(st.session_state.selected_csv, st.session_state.active_person)
    if progress_stats["supported"]:
        render_header()
        render_menu()
        if st.session_state.menu_open:
            st.stop()
        render_deck_strip()
        render_study_mode_picker()
        st.stop()
    st.session_state.study_mode = "all"

# ========================================================================
# LOAD CSV
# ========================================================================

if st.session_state.loaded_csv != st.session_state.selected_csv or not st.session_state.cards:
    if is_review_deck(st.session_state.selected_csv):
        review_person = review_deck_person(st.session_state.selected_csv)
        review_items = list(st.session_state.review_data.get(review_person, {}).values())
        st.session_state.cards = [
            {"id": None, "word": item["word"], "answer": item["answer"],
             "shown": False, "scored": False, "repeat_score": item["count"], "error_flag": 0}
            for item in review_items
        ]
    else:
        deck_data = load_regular_deck(st.session_state.selected_csv)
        st.session_state.cards = deck_data["cards"]
        if st.session_state.study_mode == "remaining" and deck_data["supports_completion"]:
            completed_ids = completed_ids_for(st.session_state.active_person, st.session_state.selected_csv)
            st.session_state.cards = [
                card for card in st.session_state.cards
                if card.get("id") not in completed_ids
            ]
    if is_story_deck(st.session_state.selected_csv):
        rebuild_story_order()
    else:
        st.session_state.order = list(range(len(st.session_state.cards)))
        random.shuffle(st.session_state.order)
    st.session_state.index = 0
    st.session_state.loaded_csv = st.session_state.selected_csv
    st.session_state.direction = effective_direction()

if (
    not is_review_deck(st.session_state.selected_csv)
    and not is_story_deck(st.session_state.selected_csv)
    and st.session_state.study_mode == "remaining"
    and not st.session_state.cards
):
    clear_deck_progress(st.session_state.active_person, st.session_state.selected_csv)
    st.session_state.study_mode = "all"
    st.session_state.selected_csv = None
    st.rerun()

# ========================================================================
# STATS
# ========================================================================

total_cards   = len(st.session_state.cards)
shown_cards   = sum(1 for c in st.session_state.cards if c["shown"])
correct_count = st.session_state["score_correct"]
repeat_count  = st.session_state["score_repeat"]
scored_total  = st.session_state["score_actions"]

# ========================================================================
# STORY MODE
# ========================================================================

if is_story_deck(st.session_state.selected_csv):
    if st.session_state.index >= len(st.session_state.cards):
        go_back_to_deck_picker()
        st.rerun()

    render_header()
    render_menu()
    inject_flashcard_speech_runtime()
    if st.session_state.menu_open:
        st.stop()
    render_deck_strip()
    render_story_view()
    st.stop()

# ========================================================================
# QUIT / SUMMARY
# ========================================================================

if st.session_state.quit_requested:
    render_header()
    render_menu()
    st.markdown("<div class='summary-title'>Session Summary</div>", unsafe_allow_html=True)

    perfect_first_try = sum(1 for c in st.session_state.cards
                            if c["scored"] and c["repeat_score"] == 0 and c["error_flag"] == 0)
    scored_cards = sum(1 for c in st.session_state.cards if c["scored"])
    avg_rs = (sum(c["repeat_score"] for c in st.session_state.cards if c["scored"]) / scored_cards
              ) if scored_cards > 0 else 0
    accuracy   = int(correct_count / scored_total * 100) if scored_total > 0 else 0
    missed_pct = int(repeat_count  / scored_total * 100) if scored_total > 0 else 0
    current_user_label = PERSON_LABELS[st.session_state.active_person]
    current_review_cards = review_count_for(st.session_state.active_person)

    st.markdown(f"""
    <div class="summary-grid">
      <div class="sg-label">Cards Shown</div>      <div class="sg-value">{shown_cards}</div>
            <div class="sg-label">Manual Scores</div>    <div class="sg-value">{scored_total}</div>
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
        if not is_review_deck(st.session_state.selected_csv) and st.session_state.study_mode == "remaining":
            clear_deck_progress(st.session_state.active_person, st.session_state.selected_csv)
            st.session_state.study_mode = "all"
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

spanish_text = card["answer"]
spanish_visible_phase = None
if current_direction == "EN_TO_ES":
    if st.session_state.show_answer:
        spanish_visible_phase = "answer-visible"
else:
    spanish_visible_phase = "prompt-visible"

# ========================================================================
# MAIN LAYOUT
# ========================================================================

render_header()
render_menu()
render_deck_strip()
stats_card_html(shown_cards, total_cards, correct_count, repeat_count, scored_total)
inject_flashcard_speech_runtime()
inject_speech_priming()
render_regular_auto_mode_controls()
render_voice_inspector()
render_flashcard(prompt, solution, st.session_state.show_answer)
render_regular_auto_hidden_buttons()
if st.session_state["regular_auto_mode"]:
    prompt_language = "en" if current_direction == "EN_TO_ES" else "es"
    answer_language = "es" if current_direction == "EN_TO_ES" else "en"
    preferred_gender = "female" if (st.session_state.index % 2 == 0) else "male"
    phase = "answer" if st.session_state.show_answer else "prompt"
    phase_text = solution if st.session_state.show_answer else prompt
    phase_language = answer_language if st.session_state.show_answer else prompt_language
    phase_delay_seconds = 2.0 if st.session_state.show_answer else story_pause_seconds_for_text(prompt)
    phase_key = "|".join(
        [
            st.session_state.selected_csv or "",
            str(current_card_index()),
            str(st.session_state.index),
            phase,
            str(st.session_state["regular_auto_generation"]),
            strip_spoken_text(phase_text),
        ]
    )
    render_regular_auto_mode_driver(
        phase=phase,
        phase_key=phase_key,
        text=phase_text,
        language=phase_language,
        pause_after_seconds=phase_delay_seconds,
        preferred_gender=preferred_gender,
        repeat_spanish=st.session_state["regular_auto_repeat_spanish"],
    )
else:
    render_regular_auto_mode_cleanup()
    inject_tap_reveal(
        st.session_state.show_answer,
        auto_speak_enabled=st.session_state.auto_speak_spanish and current_direction == "EN_TO_ES",
        auto_speak_text=card["answer"],
    )
if not st.session_state["regular_auto_mode"] and st.session_state.auto_speak_spanish and current_direction == "ES_TO_EN" and spanish_visible_phase:
    auto_speak_event_key = "|".join(
        [
            st.session_state.selected_csv or "",
            str(current_card_index()),
            str(st.session_state.index),
            current_direction,
            spanish_visible_phase,
            str(st.session_state.auto_speak_spanish_generation),
            strip_spoken_text(spanish_text),
        ]
    )
    render_auto_speak_spanish(spanish_text, auto_speak_event_key)
render_buttons(st.session_state.show_answer, spanish_text)