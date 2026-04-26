
"""Streamlit Spanish flashcards application.

This app now treats folder placement as the primary source of deck meaning.
In practice, that means folders such as Stories, Dialogs, Sentences, and
Conjugations drive picker grouping and deck behavior before filename keywords do.

Current naming summary:
- Put each CSV in the correct folder first.
- Keep CSV filenames short, readable, and unique across the full csv tree.
- Use grouped picker suffixes such as _p and _c1, _c2 only when a guaranteed
    parent/child picker order is needed.
- Keep EN_ES in the filename only for the legacy forced English-to-Spanish
    exception.

For the full project naming rules and active examples, see:
- NAMING_CONVENTIONS.md
- VERBS_ORGANIZATION.md
"""

# --- ALL IMPORTS AT TOP ---
import pathlib
import streamlit as st
import random
import os
import time
import secrets
import sys
import json
import base64
import html
import math
import re
import socket
import urllib.error
import urllib.request
from urllib.parse import quote
from datetime import date, datetime
import matplotlib.pyplot as plt
import pandas as pd
import streamlit.components.v1 as components
from streamlit.runtime.scriptrunner import get_script_run_ctx

# Set page config FIRST
st.set_page_config(page_title="Spanish Flashcards", page_icon="🌿", layout="wide")


# streamlit_eng_sp_flashcards.py
APP_BUILD_CODE = "rev58"
PICKER_UI_BUILD_CODE = "picker-html-v1"
PICKER_CSS_BUILD_CODE = "css-2026-04-21e"
MOBILE_PICKER_CONTAINER_KEY = f"mobile_deck_picker_wrap_{PICKER_UI_BUILD_CODE.replace('-', '_')}"
PICKER_HIDDEN_ACTIONS_WRAP_KEY = f"picker_hidden_toggle_actions_wrap_{PICKER_UI_BUILD_CODE.replace('-', '_')}"

# --- SIMPLE LOGIN SCREEN (before splash) ---
LOGIN_FLOW_VERSION = 3
LOGIN_HANDOFF_FILE = os.path.expanduser("~/.flashcards_login_handoff.json")
LOGIN_HANDOFF_TTL_SECONDS = 300
LOGIN_PASSWORDS = [
    "141592",  # Replace with your real passwords
    "3141",
    "2565",
    "62252",
    "062252",
    "2456",
    "020456"
]


def save_login_handoff(token):
    payload = {
        "token": token,
        "expires_at": int(time.time()) + LOGIN_HANDOFF_TTL_SECONDS,
        "version": LOGIN_FLOW_VERSION,
    }
    try:
        with open(LOGIN_HANDOFF_FILE, "w", encoding="utf-8") as handoff_file:
            json.dump(payload, handoff_file)
    except OSError:
        return


def clear_login_handoff():
    try:
        os.remove(LOGIN_HANDOFF_FILE)
    except FileNotFoundError:
        return
    except OSError:
        return


def consume_login_handoff(token):
    if not token:
        return False
    try:
        with open(LOGIN_HANDOFF_FILE, encoding="utf-8") as handoff_file:
            payload = json.load(handoff_file)
    except (OSError, json.JSONDecodeError):
        clear_login_handoff()
        return False

    is_valid = (
        payload.get("version") == LOGIN_FLOW_VERSION
        and payload.get("token") == token
        and int(payload.get("expires_at", 0)) >= int(time.time())
    )
    clear_login_handoff()
    return is_valid


def clear_login_handoff_query_param():
    if "auth_handoff" in st.query_params:
        del st.query_params["auth_handoff"]


def ensure_login_handoff_token():
    if not st.session_state.get("is_logged_in"):
        return None
    existing_token = st.session_state.get("login_handoff_token")
    if existing_token:
        return existing_token
    handoff_token = secrets.token_urlsafe(24)
    st.session_state["login_handoff_token"] = handoff_token
    save_login_handoff(handoff_token)
    return handoff_token


def login_screen():
    if st.session_state.get("is_logged_in"):
        return  # Already logged in, do not show login fields
    st.markdown(
        """
        <style>
        .st-key-login_title_wrap {
            width: 100%;
            margin: 6rem auto 0 auto;
            text-align: center;
        }
        .st-key-login_form_wrap {
            width: min(100%, 10rem);
            margin: 2.5rem auto 0 auto;
            transform: translateX(-1.5rem);
        }
        .st-key-login_form_wrap [data-testid="stVerticalBlock"] {
            gap: 0 !important;
        }
        .st-key-login_password_wrap,
        .st-key-login_button_wrap {
            width: 100%;
            margin-left: 0;
            margin-right: 0;
        }
        .st-key-login_password_wrap [data-testid="stWidgetLabel"] {
            margin-bottom: 0.3rem;
        }
        .st-key-login_password_wrap [data-testid="stWidgetLabel"] p {
            font-size: 0.95rem !important;
            font-weight: 500 !important;
        }
        .st-key-login_password_wrap [data-baseweb="input"] {
            width: 100%;
        }
        .st-key-login_password_wrap [data-baseweb="base-input"] {
            min-height: 2.5rem;
        }
        .st-key-login_button_wrap .stButton,
        .st-key-login_button_wrap .stButton > button {
            width: 100%;
        }
        .st-key-login_button_wrap .stButton > button {
            background: linear-gradient(135deg, #006847 0%, #008f5a 100%);
            color: #ffffff;
            border: 2px solid #00573b;
            border-radius: 0.75rem;
            font-weight: 700;
            letter-spacing: 0.08em;
            min-height: 2.75rem;
            box-shadow: 0 10px 20px rgba(0, 104, 71, 0.18);
        }
        .st-key-login_button_wrap .stButton > button:hover {
            background: linear-gradient(135deg, #00573b 0%, #007e50 100%);
            border-color: #00442d;
            color: #ffffff;
        }
        @media (min-width: 768px) {
            .stApp,
            [data-testid="stAppViewContainer"],
            [data-testid="stMain"],
            [data-testid="stMainBlockContainer"] {
                background: #000000 !important;
            }
            .st-key-login_password_wrap [data-testid="stWidgetLabel"] p {
                color: #f3f3f3 !important;
            }
            .st-key-login_password_wrap input {
                color: #ffffff !important;
            }
            .st-key-login_password_wrap [data-baseweb="base-input"] {
                background: #111111 !important;
                border-color: #2a2a2a !important;
            }
        }
        @media (max-width: 767px) {
            .st-key-login_title_wrap {
                margin-top: 5rem;
            }
            .st-key-login_form_wrap {
                width: min(100%, 10rem);
                transform: translateX(-1.5rem);
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    with st.container(key="login_title_wrap"):
        st.markdown(
            """
            <div style="width:100%; text-align:center;">
                <h1 style="font-size:2.2rem; margin:0 auto; white-space:nowrap; text-align:center; display:inline-block;">
                    <span style="color:#006847;">Spanish</span>
                    <span style="color:#ce1126;">Flashcards</span>
                </h1>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with st.container(key="login_form_wrap"):
        with st.container(key="login_password_wrap"):
            pw = st.text_input("Password", type="password", key="login_password", help="Enter your password to continue.")
        with st.container(key="login_button_wrap"):
            login_btn = st.button("LOGIN", key="login_button", type="primary", use_container_width=True)
    if login_btn or (pw and st.session_state.get("_login_attempted")):
        st.session_state["_login_attempted"] = True
        if pw in LOGIN_PASSWORDS:
            handoff_token = secrets.token_urlsafe(24)
            st.session_state["is_logged_in"] = True
            st.session_state["login_handoff_token"] = handoff_token
            st.session_state["_login_attempted"] = False
            save_login_handoff(handoff_token)
            st.rerun()
        else:
            st.error("Incorrect password. Please try again.")
    st.stop()

if st.session_state.get("login_flow_version") != LOGIN_FLOW_VERSION:
    st.session_state["login_flow_version"] = LOGIN_FLOW_VERSION
    st.session_state["_login_attempted"] = False

if "is_logged_in" not in st.session_state:
    st.session_state["is_logged_in"] = False
if "login_handoff_token" not in st.session_state:
    st.session_state["login_handoff_token"] = None

handoff_token = st.query_params.get("auth_handoff")
if not st.session_state.get("is_logged_in") and consume_login_handoff(handoff_token):
    st.session_state["is_logged_in"] = True
    st.session_state["login_handoff_token"] = None
    clear_login_handoff_query_param()

if not st.session_state.get("is_logged_in"):
    login_screen()

try:
    from supabase import create_client
except ImportError:
    create_client = None

if get_script_run_ctx() is None:
    print("Run this app with: streamlit run streamlit_eng_sp_flashcards.py")
    sys.exit(1)

# ------------------------------------------------------------------------
# CONFIG
# ------------------------------------------------------------------------



CSV_FOLDER = os.path.join(os.path.dirname(__file__), "csv")
PREFS_FILE = os.path.expanduser("~/.flashcards_prefs.json")
REVIEWS_FILE = os.path.expanduser("~/.flashcards_reviews.json")
FAVORITES_FILE = os.path.expanduser("~/.flashcards_favorites.json")
PROGRESS_FILE = os.path.expanduser("~/.flashcards_progress.json")
MONTHLY_PROGRESS_HISTORY_TABLE = "monthly_progress_history"
SPLASH_IMAGE_PATH = os.path.join(os.path.dirname(__file__), "axolotl_david_miguel.png")
GOODBYE_IMAGE_PATH = os.path.join(os.path.dirname(__file__), "axolotl_waving_goodbye.png")
SPLASH_IMAGE_DIMENSION = 1600
TRACKABLE_COUNT_EXCLUDED_LEGACY_FILENAME_TOKENS = [
    "text",
    "sentence",
    "sentences",
    "conjugated",
    "situation",
    "situations",
    "dialog",
    "story",
    "stories",
]
SPLASH_ACTIONS = {
    "david": [(285, 575), (727, 575), (727, 1387), (282, 1387)],
    "miguel": [(925, 575), (1363, 575), (1363, 1387), (925, 1387)],
    "quit": [(984, 54), (1252, 164), (1218, 321), (997, 232)],
}


def configured_setting(name):
    env_value = os.environ.get(name)
    if env_value:
        return env_value
    try:
        return st.secrets.get(name)
    except Exception:
        return None


SUPABASE_URL = configured_setting("SUPABASE_URL")
SUPABASE_ANON_KEY = configured_setting("SUPABASE_ANON_KEY")
SUPABASE_SERVICE_ROLE_KEY = configured_setting("SUPABASE_SERVICE_ROLE_KEY")

PERSON_LABELS = {
    "miguel": "Miguel",
    "david": "David",
}

AI_TENSE_OPTIONS = [
    ("present", "Pres", "presente"),
    ("ir_a", "Voy A", "ir a + infinitivo"),
    ("preterite", "Pret", "pretérito"),
    ("imperfect", "Imperf", "imperfecto"),
    ("conditional", "Cond", "condicional"),
    ("subjunctive", "Subj", "subjuntivo"),
]
AI_LEVEL_OPTIONS = [
    (
        "beginner",
        "Beg",
        "nivel de principiante absoluto: escribe para un estudiante en sus primeras semanas de español; "
        "usa solo vocabulario A1 muy común y cotidiano, palabras cortas y de alta frecuencia, "
        "una sola idea y una sola cláusula principal, orden sintáctico simple y claro, "
        "y la forma verbal permitida más sencilla disponible. "
        "Evita expresiones idiomáticas, dobles sentidos, lenguaje figurado, conectores complejos, "
        "pronombres difíciles, vocabulario raro, temas abstractos y cualquier redacción que no sea inmediata y literal",
    ),
    ("intermediate", "Int", "nivel intermedio, vocabulario cotidiano y natural"),
    ("advanced", "Adv", "nivel avanzado, vocabulario rico pero natural"),
]
DEFAULT_AI_SENTENCE_TENSES = {
    "present": True,
    "ir_a": True,
    "preterite": True,
    "imperfect": False,
    "conditional": False,
    "subjunctive": False, 
}
DEFAULT_AI_SENTENCE_LEVEL = "beginner"
AI_EXAMPLES_PER_BATCH = 3
AI_EXAMPLES_TARGET_WORDS = 12
AI_EXAMPLES_TARGET_WORDS_MIN = 6
AI_EXAMPLES_TARGET_WORDS_MAX = 25
AI_EXAMPLES_MODEL = configured_setting("OPENAI_EXAMPLES_MODEL") or "gpt-5.4-mini"
AI_EXAMPLES_STATUS_TTL_SECONDS = 30
AI_EXAMPLES_STATUS_TIMEOUT_SECONDS = 2
AI_EXAMPLES_REQUEST_TIMEOUT_SECONDS = 8
AI_EXAMPLES_ALLOWED_POS_FOLDERS = {
    "adjectives",
    "adverbs",
    "conjunctions",
    "nouns",
    "prepositions",
    "pronouns",
}
AI_EXAMPLES_ALLOWED_VERB_FOLDER = "infinitives"
AI_EXAMPLES_ALLOWED_TOP_LEVEL_FOLDERS = {
    "vocabulary",
}


def default_ai_sentence_tenses():
    return dict(DEFAULT_AI_SENTENCE_TENSES)


def sanitize_ai_examples_word_target(target_words, fallback=None):
    fallback_target = fallback if fallback is not None else AI_EXAMPLES_TARGET_WORDS
    try:
        sanitized = int(target_words)
    except (TypeError, ValueError):
        sanitized = int(fallback_target)
    sanitized = max(
        AI_EXAMPLES_TARGET_WORDS_MIN,
        min(AI_EXAMPLES_TARGET_WORDS_MAX, sanitized),
    )
    return sanitized


def sanitize_ai_sentence_tenses(raw_value, fallback=None):
    fallback = dict(fallback or default_ai_sentence_tenses())
    raw_value = raw_value if isinstance(raw_value, dict) else {}
    sanitized = {}
    for tense_key, _, _ in AI_TENSE_OPTIONS:
        value = raw_value.get(tense_key, fallback.get(tense_key, True))
        sanitized[tense_key] = bool(value)
    if not any(sanitized.values()):
        sanitized = dict(fallback)
    if not any(sanitized.values()):
        sanitized = default_ai_sentence_tenses()
    return sanitized


def allowed_ai_tense_keys(tense_settings):
    sanitized = sanitize_ai_sentence_tenses(tense_settings)
    return [
        tense_key
        for tense_key, _, _ in AI_TENSE_OPTIONS
        if sanitized.get(tense_key)
    ]


def ai_level_prompt_text(level_key):
    for option_key, _, prompt_text in AI_LEVEL_OPTIONS:
        if option_key == level_key:
            return prompt_text
    return AI_LEVEL_OPTIONS[0][2]


def ai_level_short_label(level_key):
    for option_key, short_label, _ in AI_LEVEL_OPTIONS:
        if option_key == level_key:
            return short_label
    return AI_LEVEL_OPTIONS[0][1]


def ai_tense_names_text(tense_settings):
    allowed_keys = set(allowed_ai_tense_keys(tense_settings))
    allowed_names = [
        tense_name
        for tense_key, _, tense_name in AI_TENSE_OPTIONS
        if tense_key in allowed_keys
    ]
    return ", ".join(allowed_names)
REVIEW_DECK_VALUES = {
    person: f"__review_{person}__"
    for person in PERSON_LABELS
}
FAVORITES_DECK_VALUES = {
    person: f"__favorites_{person}__"
    for person in PERSON_LABELS
}
REVIEW_DECK_ORDER = [REVIEW_DECK_VALUES["miguel"], REVIEW_DECK_VALUES["david"]]
FAVORITES_DECK_ORDER = [FAVORITES_DECK_VALUES["miguel"], FAVORITES_DECK_VALUES["david"]]


@st.cache_resource(show_spinner=False)
def get_supabase_client():
    supabase_key = SUPABASE_SERVICE_ROLE_KEY or SUPABASE_ANON_KEY
    if SUPABASE_SERVICE_ROLE_KEY:
        print("[SUPABASE] Using service role key (SUPABASE_SERVICE_ROLE_KEY)")
    else:
        print("[SUPABASE] Using anon key (SUPABASE_ANON_KEY)")
    if create_client is None or not SUPABASE_URL or not supabase_key:
        return None
    return create_client(SUPABASE_URL, supabase_key)


def cloud_sync_enabled():
    return get_supabase_client() is not None


@st.cache_data(show_spinner=False)
def image_data_uri(image_path):
    if not os.path.exists(image_path):
        return None
    with open(image_path, "rb") as image_handle:
        encoded = base64.b64encode(image_handle.read()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def splash_image_data_uri():
    return image_data_uri(SPLASH_IMAGE_PATH)


def goodbye_image_data_uri():
    return image_data_uri(GOODBYE_IMAGE_PATH)

# ------------------------------------------------------------------------
# DECK PICKER GROUPING
# ------------------------------------------------------------------------
# The picker mirrors the actual folder tree under csv/.
#
# Top-level folders become the main categories.
# Nested folders become nested submenus.
# CSV files appear only in the folder where they physically live.
#
# Playback behavior is also folder-driven for the top-level mode folders:
# - Dialogs -> dialog mode
# - Stories -> story mode
# - Sentence Practice -> sentence mode
#
# David and Miguel are kept as the visible folder names everywhere.
TOP_LEVEL_PICKER_ORDER = [
    "Miguel",
    "David",
    "Books",
    "Parts of Speech",
    "Vocabulary",
    "Sentence Practice",
    "Situations",
    "Dialogs",
    "Stories",
]
TOP_LEVEL_PICKER_ORDER_LOOKUP = {
    folder_name.casefold(): index
    for index, folder_name in enumerate(TOP_LEVEL_PICKER_ORDER)
}
DECK_MODE_TOP_LEVEL_FOLDERS = {
    "dialogs": "dialog",
    "stories": "story",
    "sentence practice": "sentence",
}
DECK_MODE_FOLDER_LABELS = {
    "dialogs": "dialog",
    "dialog": "dialog",
    "stories": "story",
    "story": "story",
    "sentence practice": "sentence",
    "sentences": "sentence",
    "sentence": "sentence",
}
TRACKABLE_COUNT_EXCLUDED_FOLDER_LABELS = {
    "conjugations",
    "conjugation",
    "dialogs",
    "dialog",
    "sentence practice",
    "sentences",
    "sentence",
    "situations",
    "situation",
    "stories",
    "story",
}

BUTTON_COLORS = {
    "green": {"bg": "#c8f0d8", "border": "#2e8b57", "fg": "#0f4f29"},
    "yellow": {"bg": "#fdf0c0", "border": "#b8860b", "fg": "#6a4b00"},
    "blue": {"bg": "#d7e5ff", "border": "#2f6fdf", "fg": "#17479a"},
    "red": {"bg": "#f8d8d8", "border": "#c23b22", "fg": "#7f1717"},
}

LEARNED_WORDS_CHALLENGE_VALUE = "__learned_words_challenge__"
LEARNED_WORDS_CHALLENGE_LABEL = "Learned Words Challenge [20]"
LEARNED_WORDS_CHALLENGE_MIN_CARDS = 20
LEARNED_WORDS_CHALLENGE_SESSION_SIZE = 20


def discover_csv_files(csv_root):
    csv_root_path = pathlib.Path(csv_root)
    deck_paths_by_name = {}
    duplicate_names = {}

    for csv_path in sorted(csv_root_path.rglob("*.csv"), key=lambda path: str(path).lower()):
        deck_name = csv_path.name
        relative_path = str(csv_path.relative_to(csv_root_path))
        if deck_name in deck_paths_by_name:
            duplicate_names.setdefault(deck_name, [deck_paths_by_name[deck_name]])
            duplicate_names[deck_name].append(relative_path)
            continue
        deck_paths_by_name[deck_name] = relative_path

    if duplicate_names:
        duplicate_lines = []
        for deck_name in sorted(duplicate_names, key=str.lower):
            duplicate_lines.append(f"{deck_name}: {', '.join(duplicate_names[deck_name])}")
        raise RuntimeError(
            "Duplicate CSV filenames found under csv/. Filenames must stay unique when using subfolders.\n"
            + "\n".join(duplicate_lines)
        )

    csv_names = sorted(deck_paths_by_name, key=str.lower)
    return csv_names, deck_paths_by_name


csv_files, csv_relative_paths = discover_csv_files(CSV_FOLDER)


def csv_path_for(filename):
    relative_path = csv_relative_paths.get(filename)
    if relative_path is None:
        raise FileNotFoundError(f"CSV file not found in index: {filename}")
    return os.path.join(CSV_FOLDER, relative_path)


def csv_relative_path_for(filename):
    relative_path = csv_relative_paths.get(filename)
    if relative_path is None:
        raise FileNotFoundError(f"CSV file not found in index: {filename}")
    return relative_path


def csv_relative_parts_for(filename):
    return pathlib.Path(csv_relative_path_for(filename)).parts


def csv_relative_folder_parts_for(filename):
    return csv_relative_parts_for(filename)[:-1]


def review_item_key(word, answer):
    return json.dumps([word, answer], ensure_ascii=False, separators=(",", ":"))


def favorite_item_key(source_deck, source_id, source_index, word, answer):
    return json.dumps(
        [source_deck or "", source_id or "", source_index, word, answer],
        ensure_ascii=False,
        separators=(",", ":"),
    )


def is_review_deck(deck_value):
    return deck_value in REVIEW_DECK_VALUES.values()


def is_favorites_deck(deck_value):
    return deck_value in FAVORITES_DECK_VALUES.values()


def review_deck_person(deck_value):
    for person, review_value in REVIEW_DECK_VALUES.items():
        if review_value == deck_value:
            return person
    return None


def favorites_deck_person(deck_value):
    for person, favorites_value in FAVORITES_DECK_VALUES.items():
        if favorites_value == deck_value:
            return person
    return None


def review_deck_label(person, include_count=False):
    label = f"Review - {PERSON_LABELS[person]}"
    if include_count:
        label += f" [{review_count_for(person)}]"
    return label


def favorites_deck_label(person, include_count=False):
    label = f"Favorites - {PERSON_LABELS[person]}"
    if include_count:
        label += f" [{favorites_count_for(person)}]"
    return label


def is_learned_words_challenge(deck_value):
    return deck_value == LEARNED_WORDS_CHALLENGE_VALUE


def learned_words_challenge_label():
    return LEARNED_WORDS_CHALLENGE_LABEL


# Standard picker naming spec:
# - Parent file/folder: BaseName_p(.csv)
# - Child file/folder: BaseName_childLabel_c1(.csv), BaseName_childLabel_c2(.csv), ...
# - The picker strips _p and _cN from the visible label.
# - Child ordering is driven by the numeric c-suffix.
#
# Legacy suffix matching below is fallback-only for existing decks that do not
# use the standard _p / _cN markers yet.
PICKER_STANDARD_PARENT_SUFFIX = "_p"
PICKER_STANDARD_CHILD_SUFFIX_PATTERN = "_c<number>"
PICKER_ROLE_SUFFIX_PATTERN = re.compile(r"^(?P<base>.+?)_(?P<role>p|c(?P<child_index>\d+))$")
PICKER_BACKCOMPAT_CHILD_SUFFIX_ORDER = (
    ("stories", 10),
    ("story", 11),
    ("dialogs", 20),
    ("dialog", 21),
    ("sentence_practice", 30),
    ("practice", 40),
    ("exercises", 41),
    ("exercise", 42),
    ("review", 43),
    ("quiz", 44),
    ("sentences", 50),
    ("sentence", 51),
    ("situations", 60),
    ("situation", 61),
)


def normalized_filename(value):
    return os.path.basename(value or "").lower()


def normalized_folder_label(value):
    label = re.sub(r"^\d+\s+", "", str(value or "").strip())
    return re.sub(r"\s+", " ", label).casefold()


def picker_display_label(value):
    label = re.sub(r"^\d+\s+", "", str(value or "").strip())
    return re.sub(r"\s+", " ", label)


def picker_entry_name_parts(raw_name, is_folder=False):
    if is_folder:
        return raw_name, ""
    return os.path.splitext(raw_name)


def picker_entry_metadata(raw_name, is_folder=False):
    stem, _ = picker_entry_name_parts(raw_name, is_folder=is_folder)
    match = PICKER_ROLE_SUFFIX_PATTERN.fullmatch(stem)

    role = None
    child_index = None
    visible_stem = stem

    if match:
        visible_stem = match.group("base")
        role_token = match.group("role")
        if role_token == "p":
            role = "parent"
        else:
            role = "child"
            child_index = int(match.group("child_index"))

    legacy_child_order = None
    if role is None:
        visible_stem_lower = visible_stem.casefold()
        for suffix, suffix_order in PICKER_BACKCOMPAT_CHILD_SUFFIX_ORDER:
            marker = f"_{suffix}"
            if visible_stem_lower.endswith(marker) and len(visible_stem_lower) > len(marker):
                legacy_child_order = suffix_order
                break

    return {
        "raw_name": raw_name,
        "visible_name": visible_stem,
        "display_name": picker_display_label(visible_stem),
        "role": role,
        "child_index": child_index,
        "legacy_child_order": legacy_child_order,
    }


def build_picker_file_entry(filename):
    return {
        "entry_type": "file",
        "filename": filename,
        "italicized": False,
        **picker_entry_metadata(filename, is_folder=False),
    }


def picker_entry_is_child(entry):
    return entry.get("role") == "child" or entry.get("legacy_child_order") is not None


def picker_entry_sort_key(entry):
    return (
        entry["visible_name"].casefold(),
        0 if entry["entry_type"] == "file" else 1,
        entry["raw_name"].casefold(),
    )


def picker_child_entry_sort_key(entry):
    return (
        0 if entry.get("role") == "child" else 1,
        entry.get("child_index") if entry.get("role") == "child" else entry.get("legacy_child_order", 10_000),
        picker_entry_sort_key(entry),
    )


def picker_find_parent_entry(child_entry, parent_entries):
    child_name = child_entry["visible_name"].casefold()
    matches = []

    for parent_entry in parent_entries:
        parent_name = parent_entry["visible_name"].casefold()
        if not parent_name or child_name == parent_name:
            continue
        if not child_name.startswith(parent_name):
            continue

        remainder = child_name[len(parent_name):]
        if not remainder.startswith("_"):
            continue

        matches.append(parent_entry)

    if not matches:
        return None

    return max(matches, key=lambda entry: len(entry["visible_name"]))


def picker_order_entries(entries):
    sorted_entries = sorted(entries, key=picker_entry_sort_key)
    parent_entries = [entry for entry in sorted_entries if not picker_entry_is_child(entry)]
    children_by_parent = {}
    attached_child_names = set()

    for entry in sorted_entries:
        if not picker_entry_is_child(entry):
            continue

        parent_entry = picker_find_parent_entry(entry, parent_entries)
        if parent_entry is None:
            continue

        children_by_parent.setdefault(parent_entry["raw_name"], []).append(entry)
        attached_child_names.add(entry["raw_name"])

    ordered_entries = []
    appended_entry_names = set()

    for entry in sorted_entries:
        raw_name = entry["raw_name"]
        if raw_name in appended_entry_names or raw_name in attached_child_names:
            continue

        ordered_entries.append(entry)
        appended_entry_names.add(raw_name)

        for child_entry in sorted(children_by_parent.get(raw_name, []), key=picker_child_entry_sort_key):
            child_raw_name = child_entry["raw_name"]
            if child_raw_name in appended_entry_names:
                continue
            ordered_entries.append({**child_entry, "is_picker_child": True})
            appended_entry_names.add(child_raw_name)

    for entry in sorted_entries:
        raw_name = entry["raw_name"]
        if raw_name in appended_entry_names:
            continue
        ordered_entries.append(entry)
        appended_entry_names.add(raw_name)

    return ordered_entries


def filename_contains_any(value, tokens):
    filename = normalized_filename(value)
    return any(token.lower() in filename for token in tokens)


def deck_folder_labels(filename):
    return [normalized_folder_label(part) for part in csv_relative_folder_parts_for(filename)]


def exclude_from_trackable_count(filename):
    if set(deck_folder_labels(filename)) & TRACKABLE_COUNT_EXCLUDED_FOLDER_LABELS:
        return True
    return filename_contains_any(filename, TRACKABLE_COUNT_EXCLUDED_LEGACY_FILENAME_TOKENS)


def deck_top_level_folder(filename):
    parts = csv_relative_parts_for(filename)
    if not parts:
        return None
    return parts[0]


def deck_mode_for_file(filename):
    if not filename or is_review_deck(filename) or is_favorites_deck(filename):
        return None

    for folder_label in reversed(deck_folder_labels(filename)):
        folder_mode = DECK_MODE_FOLDER_LABELS.get(folder_label)
        if folder_mode:
            return folder_mode

    top_level_folder = deck_top_level_folder(filename)
    if top_level_folder:
        folder_mode = DECK_MODE_TOP_LEVEL_FOLDERS.get(top_level_folder.casefold())
        if folder_mode:
            return folder_mode

    if filename_contains_any(filename, ["dialog"]):
        return "dialog"
    if filename_contains_any(filename, ["story"]):
        return "story"
    if filename_contains_any(filename, ["sentence"]):
        return "sentence"
    return None


def picker_visible_directory_entries(folder_path):
    entries = []
    for child_path in folder_path.iterdir():
        if child_path.name.startswith("."):
            continue
        if child_path.is_dir() or (child_path.is_file() and child_path.suffix.lower() == ".csv"):
            entries.append(child_path)
    return entries


def picker_top_level_sort_key(folder_name):
    return (
        TOP_LEVEL_PICKER_ORDER_LOOKUP.get(folder_name.casefold(), len(TOP_LEVEL_PICKER_ORDER)),
        folder_name.casefold(),
    )


def build_picker_folder_node(folder_path, relative_parts):
    child_entries = []
    folder_metadata = picker_entry_metadata(relative_parts[-1], is_folder=True)

    for child_path in picker_visible_directory_entries(folder_path):
        if child_path.is_dir():
            child_entries.append(build_picker_folder_node(child_path, relative_parts + (child_path.name,)))
            continue

        child_entries.append(build_picker_file_entry(child_path.name))

    return {
        "key": "/".join(relative_parts),
        "name": relative_parts[-1],
        "display_name": folder_metadata["display_name"],
        **folder_metadata,
        "entry_type": "folder",
        "entries": picker_order_entries(child_entries),
    }


def picker_root_files():
    root_files = []
    for filename in csv_files:
        if len(csv_relative_parts_for(filename)) == 1:
            root_files.append(build_picker_file_entry(filename))
    return picker_order_entries(root_files)


def picker_root_folder_nodes():
    csv_root_path = pathlib.Path(CSV_FOLDER)
    root_nodes = []

    for child_path in picker_visible_directory_entries(csv_root_path):
        if not child_path.is_dir():
            continue
        root_nodes.append(build_picker_folder_node(child_path, (child_path.name,)))

    root_nodes.sort(key=lambda node: picker_top_level_sort_key(node["visible_name"]))
    return root_nodes


def story_title_row_present_in_file(filename):
    if (
        not filename
        or is_review_deck(filename)
        or is_favorites_deck(filename)
        or is_dialog_deck(filename)
        or not is_story_deck(filename)
    ):
        return False

    csv_path = csv_path_for(filename)
    try:
        with open(csv_path, "r", encoding="utf-8") as handle:
            first_line = handle.readline()
        separator = ";" if ";" in first_line else ","
        df = pd.read_csv(csv_path, sep=separator, nrows=1)
        df.columns = [str(column).strip() for column in df.columns]
        if df.empty:
            return False

        lower_columns = {column.lower(): column for column in df.columns}
        id_column = lower_columns.get("id")
        word_column = lower_columns.get("word")
        if word_column is None:
            content_columns = [column for column in df.columns if column != id_column]
            if not content_columns:
                return False
            word_column = content_columns[0]

        first_english = str(df.iloc[0][word_column]).strip()
        return first_english.lower().startswith("title:")
    except Exception:
        return False


@st.cache_data(show_spinner=False)
def csv_data_row_count(filename):
    file_path = csv_path_for(filename)
    try:
        with open(file_path, encoding="utf-8", errors="ignore") as handle:
            row_count = max(sum(1 for _ in handle) - 1, 0)
        if story_title_row_present_in_file(filename):
            row_count = max(row_count - 1, 0)
        return row_count
    except Exception:
        return 0


csv_row_counts = {filename: csv_data_row_count(filename) for filename in csv_files}


def picker_folder_item_count(folder_node):
    return len(folder_node["entries"])


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
    csv_path = csv_path_for(filename)
    with open(csv_path, "r", encoding="utf-8") as handle:
        first_line = handle.readline()
    separator = ";" if ";" in first_line else ","
    df = pd.read_csv(csv_path, sep=separator)
    df.columns = [str(column).strip() for column in df.columns]

    lower_columns = {column.lower(): column for column in df.columns}
    id_column = lower_columns.get("id")
    uses_headerless_layout = False

    if is_forced_en_es_deck(filename):
        content_columns = [column for column in df.columns if column != id_column]
        word_column = content_columns[0]
        answer_column = content_columns[1]
    elif "word" in lower_columns and "answer" in lower_columns:
        word_column = lower_columns["word"]
        answer_column = lower_columns["answer"]
    else:
        # Some legacy decks are plain two-column CSVs without a header row.
        df = pd.read_csv(csv_path, sep=separator, header=None)
        df.columns = [f"column_{index}" for index in range(len(df.columns))]
        id_column = None
        uses_headerless_layout = True
        if len(df.columns) < 2:
            raise ValueError(f"CSV deck '{filename}' must have at least two columns")
        word_column = df.columns[0]
        answer_column = df.columns[1]

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
        "supports_completion": bool(id_column) and not uses_headerless_layout,
    }


def display_deck_name(filename):
    if is_learned_words_challenge(filename):
        return learned_words_challenge_label()
    if is_review_deck(filename):
        return review_deck_label(review_deck_person(filename))
    if is_favorites_deck(filename):
        return favorites_deck_label(favorites_deck_person(filename), include_count=True)
    base_name, extension = os.path.splitext(filename)
    if extension.lower() == ".csv":
        display_name = picker_entry_metadata(filename, is_folder=False)["display_name"]
        return f"{display_name} [{csv_row_counts.get(filename, 0)}]"
    return base_name


def picker_display_deck_name(filename, person):
    if is_learned_words_challenge(filename):
        return learned_words_challenge_label()
    if is_review_deck(filename):
        return review_deck_label(review_deck_person(filename), include_count=True)
    if is_favorites_deck(filename):
        return favorites_deck_label(favorites_deck_person(filename), include_count=True)

    base_name, extension = os.path.splitext(filename)
    if extension.lower() != ".csv":
        return base_name

    return picker_entry_metadata(filename, is_folder=False)["display_name"]


def is_dialog_deck(filename):
    return deck_mode_for_file(filename) == "dialog"


def is_story_deck(filename):
    return deck_mode_for_file(filename) == "story"


def is_sentence_deck(filename):
    return deck_mode_for_file(filename) == "sentence"


def is_playback_deck(filename):
    return is_dialog_deck(filename) or is_story_deck(filename)


@st.cache_data(show_spinner=False)
def deck_completion_metadata(filename):
    deck_data = load_regular_deck(filename)
    valid_ids = [card["id"] for card in deck_data["cards"] if card.get("id")]
    supports_completion = deck_data["supports_completion"] and not exclude_from_trackable_count(filename)
    return {
        "supported": supports_completion,
        "total": len(deck_data["cards"]),
        "valid_ids": valid_ids,
    }


def deck_picker_status(filename, person):
    if is_learned_words_challenge(filename):
        return "challenge"
    if is_review_deck(filename):
        return "review"
    if is_favorites_deck(filename):
        return "favorites"
    if is_dialog_deck(filename):
        return "dialog"
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
    return picker_display_deck_name(filename, person)


def is_forced_en_es_deck(filename):
    # Keep filename matching as a fallback for legacy one-way decks that are
    # intentionally forced to EN->ES regardless of folder placement.
    return bool(filename) and not is_review_deck(filename) and not is_favorites_deck(filename) and "EN_ES" in os.path.basename(filename)


def current_playback_kind():
    return "dialog" if is_dialog_deck(st.session_state.selected_csv) else "story"


def current_playback_heading():
    return "Dialog Playback:" if current_playback_kind() == "dialog" else "Story Playback:"


def current_playback_progress_label():
    return "Line" if current_playback_kind() == "dialog" else "Sentence"


def is_deck_category_open(category_id):
    return category_id in st.session_state.get("open_deck_categories", [])


def toggle_deck_category(category_id):
    open_categories = list(st.session_state.get("open_deck_categories", []))
    if category_id in open_categories:
        open_categories = []
        st.session_state.open_deck_subcategories = []
        st.session_state.deck_picker_scroll_target = None
    else:
        # Keep the picker simpler on mobile by allowing only one open category
        # at a time. Tapping a different header replaces the current section.
        open_categories = [category_id]
        st.session_state.open_deck_subcategories = []
        st.session_state.deck_picker_scroll_target = f"category:{category_id}"
    st.session_state.open_deck_categories = open_categories


def deck_subcategory_state_key(_category_id, subcategory_id):
    return subcategory_id


def deck_subcategory_open_chain(category_id, subcategory_id):
    chain = []
    relative_path = subcategory_id
    prefix = category_id + "/"
    if relative_path.startswith(prefix):
        relative_path = relative_path[len(prefix):]

    current_parts = []
    for part in relative_path.split("/"):
        if not part:
            continue
        current_parts.append(part)
        chain.append(prefix + "/".join(current_parts))
    return chain


def is_deck_subcategory_open(category_id, subcategory_id):
    return deck_subcategory_state_key(category_id, subcategory_id) in st.session_state.get("open_deck_subcategories", [])


def toggle_deck_subcategory(category_id, subcategory_id):
    target_key = deck_subcategory_state_key(category_id, subcategory_id)
    st.session_state.open_deck_categories = [category_id]
    current_open_subcategories = list(st.session_state.get("open_deck_subcategories", []))
    if target_key not in current_open_subcategories:
        open_subcategories = deck_subcategory_open_chain(category_id, target_key)
        st.session_state.deck_picker_scroll_target = f"folder:{subcategory_id}"
    else:
        open_subcategories = [
            key
            for key in current_open_subcategories
            if target_key.startswith(key + "/")
        ]
        st.session_state.deck_picker_scroll_target = None
    st.session_state.open_deck_subcategories = open_subcategories

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
        "ai_sentence_tenses": default_ai_sentence_tenses(),
        "ai_sentence_level": DEFAULT_AI_SENTENCE_LEVEL,
        "ai_examples_target_words": AI_EXAMPLES_TARGET_WORDS,
        "ai_auto_play_examples": False,
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
    ai_sentence_tenses = sanitize_ai_sentence_tenses(
        pref_data.get("ai_sentence_tenses", fallback["ai_sentence_tenses"]),
        fallback["ai_sentence_tenses"],
    )
    ai_sentence_level = pref_data.get("ai_sentence_level", fallback["ai_sentence_level"])
    if ai_sentence_level not in {option_key for option_key, _, _ in AI_LEVEL_OPTIONS}:
        ai_sentence_level = fallback["ai_sentence_level"]
    legacy_target = pref_data.get("ai_examples_max_words")
    ai_examples_target_words = sanitize_ai_examples_word_target(
        pref_data.get("ai_examples_target_words", legacy_target if legacy_target is not None else fallback["ai_examples_target_words"]),
        fallback["ai_examples_target_words"],
    )
    ai_auto_play_examples = pref_data.get("ai_auto_play_examples", fallback["ai_auto_play_examples"])
    if not isinstance(ai_auto_play_examples, bool):
        ai_auto_play_examples = fallback["ai_auto_play_examples"]
    return {
        "theme": theme,
        "direction_mode": direction_mode,
        "speech_speed": speech_speed,
        "show_hints": show_hints,
        "auto_speak_spanish": auto_speak_spanish,
        "story_reading_speed": story_reading_speed,
        "story_pause_amount": story_pause_amount,
        "ai_sentence_tenses": ai_sentence_tenses,
        "ai_sentence_level": ai_sentence_level,
        "ai_examples_target_words": ai_examples_target_words,
        "ai_auto_play_examples": ai_auto_play_examples,
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

def load_prefs_local():
    try:
        with open(PREFS_FILE, encoding="utf-8") as f:
            return normalize_prefs(json.load(f))
    except Exception:
        return normalize_prefs({})


def save_prefs_local(pref_data):
    try:
        with open(PREFS_FILE, "w", encoding="utf-8") as f:
            json.dump(normalize_prefs(pref_data), f, ensure_ascii=False)
    except Exception:
        pass


def load_review_data_local():
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


def save_review_data_local(review_data):
    try:
        with open(REVIEWS_FILE, "w", encoding="utf-8") as f:
            serializable = {
                person: list(review_data.get(person, {}).values())
                for person in PERSON_LABELS
            }
            json.dump(serializable, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def load_favorites_data_local():
    empty = {person: {} for person in PERSON_LABELS}
    try:
        with open(FAVORITES_FILE, encoding="utf-8") as f:
            raw = json.load(f)
    except Exception:
        return empty

    favorites_data = {person: {} for person in PERSON_LABELS}
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
            if word and answer:
                favorites_data[person][review_item_key(word, answer)] = {
                    "word": word,
                    "answer": answer,
                }
    return favorites_data


def save_favorites_data_local(favorites_data):
    try:
        with open(FAVORITES_FILE, "w", encoding="utf-8") as f:
            serializable = {
                person: list(favorites_data.get(person, {}).values())
                for person in PERSON_LABELS
            }
            json.dump(serializable, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def load_progress_data_local():
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


def save_progress_data_local(progress_data):
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


def clear_runtime_caches():
    csv_data_row_count.clear()
    load_prefs.clear()
    load_review_data.clear()
    load_favorites_data.clear()
    load_progress_data.clear()
    load_monthly_progress_history.clear()


def prefs_are_default(pref_data):
    normalized = normalize_prefs(pref_data)
    return normalized["person_settings"] == normalize_prefs({})["person_settings"]


def decode_pref_json_value(raw_value):
    if not isinstance(raw_value, str):
        return raw_value
    raw_text = raw_value.strip()
    if not raw_text:
        return raw_value
    try:
        return json.loads(raw_text)
    except (TypeError, ValueError):
        return raw_value


def merge_local_ai_pref_fields(cloud_pref_data, local_pref_data):
    cloud_normalized = normalize_prefs(cloud_pref_data)
    local_normalized = normalize_prefs(local_pref_data)
    merged = normalize_prefs(cloud_normalized)
    default_person = default_person_prefs()
    ai_field_names = (
        "ai_sentence_tenses",
        "ai_sentence_level",
        "ai_examples_target_words",
        "ai_auto_play_examples",
    )

    for person in PERSON_LABELS:
        cloud_person = cloud_normalized["person_settings"][person]
        local_person = local_normalized["person_settings"][person]
        for field_name in ai_field_names:
            if (
                cloud_person.get(field_name) == default_person[field_name]
                and local_person.get(field_name) != default_person[field_name]
            ):
                merged["person_settings"][person][field_name] = local_person[field_name]

    return normalize_prefs(merged)


def review_data_has_entries(review_data):
    return any(review_data.get(person) for person in PERSON_LABELS)


def favorites_data_has_entries(favorites_data):
    return any(favorites_data.get(person) for person in PERSON_LABELS)


def progress_data_has_entries(progress_data):
    return any(progress_data.get(person) for person in PERSON_LABELS)


def load_prefs_supabase():
    client = get_supabase_client()
    if client is None:
        return None
    try:
        response = client.table("user_preferences").select("*").execute()
    except Exception:
        return None

    person_settings = {
        person: default_person_prefs()
        for person in PERSON_LABELS
    }
    for row in response.data or []:
        user_id = str(row.get("user_id", "")).strip().lower()
        if user_id not in PERSON_LABELS:
            continue
        person_settings[user_id] = sanitize_person_prefs(
            {
                "theme": row.get("theme"),
                "direction_mode": row.get("direction_mode"),
                "speech_speed": row.get("speech_speed"),
                "show_hints": row.get("show_hints"),
                "auto_speak_spanish": row.get("auto_speak_spanish"),
                "story_reading_speed": row.get("story_reading_speed"),
                "story_pause_amount": row.get("story_pause_amount"),
                "ai_sentence_tenses": decode_pref_json_value(row.get("ai_sentence_tenses")),
                "ai_sentence_level": row.get("ai_sentence_level"),
                "ai_examples_target_words": row.get("ai_examples_target_words", row.get("ai_examples_max_words")),
                "ai_auto_play_examples": row.get("ai_auto_play_examples"),
            },
            default_person_prefs(),
        )

    return normalize_prefs({
        "active_person": "miguel",
        "person_settings": person_settings,
    })


def save_prefs_supabase(pref_data):
    client = get_supabase_client()
    if client is None:
        return False

    normalized = normalize_prefs(pref_data)
    full_rows = []
    legacy_rows = []
    for person, person_pref_data in normalized["person_settings"].items():
        legacy_row = {
            "user_id": person,
            "theme": person_pref_data["theme"],
            "direction_mode": person_pref_data["direction_mode"],
            "speech_speed": person_pref_data["speech_speed"],
            "show_hints": person_pref_data["show_hints"],
            "auto_speak_spanish": person_pref_data["auto_speak_spanish"],
            "story_reading_speed": person_pref_data["story_reading_speed"],
            "story_pause_amount": person_pref_data["story_pause_amount"],
        }
        legacy_rows.append(legacy_row)
        full_rows.append(
            {
                **legacy_row,
                "ai_sentence_tenses": json.dumps(person_pref_data["ai_sentence_tenses"], ensure_ascii=False),
                "ai_sentence_level": person_pref_data["ai_sentence_level"],
                "ai_examples_min_words": person_pref_data["ai_examples_target_words"],
                "ai_examples_max_words": person_pref_data["ai_examples_target_words"],
                "ai_auto_play_examples": person_pref_data["ai_auto_play_examples"],
            }
        )
    try:
        client.table("user_preferences").upsert(full_rows).execute()
        return True
    except Exception:
        try:
            client.table("user_preferences").upsert(legacy_rows).execute()
            return True
        except Exception:
            return False


def load_review_data_supabase():
    client = get_supabase_client()
    if client is None:
        return None
    try:
        response = client.table("review_items").select(
            "user_id,item_key,word,answer,review_count"
        ).execute()
    except Exception:
        return None

    review_data = {person: {} for person in PERSON_LABELS}
    for row in response.data or []:
        user_id = str(row.get("user_id", "")).strip().lower()
        if user_id not in PERSON_LABELS:
            continue
        word = str(row.get("word", "")).strip()
        answer = str(row.get("answer", "")).strip()
        try:
            count = int(row.get("review_count", 0))
        except (TypeError, ValueError):
            count = 0
        if not word or not answer or count <= 0:
            continue
        item_key = str(row.get("item_key") or review_item_key(word, answer))
        review_data[user_id][item_key] = {
            "word": word,
            "answer": answer,
            "count": count,
        }
    return review_data


def save_review_data_supabase(review_data):
    client = get_supabase_client()
    if client is None:
        return False

    rows = []
    for person in PERSON_LABELS:
        for item_key, entry in review_data.get(person, {}).items():
            rows.append(
                {
                    "user_id": person,
                    "item_key": item_key,
                    "word": entry["word"],
                    "answer": entry["answer"],
                    "review_count": int(entry["count"]),
                }
            )

    try:
        for person in PERSON_LABELS:
            client.table("review_items").delete().eq("user_id", person).execute()
        if rows:
            client.table("review_items").upsert(rows).execute()
        return True
    except Exception:
        return False


def load_favorites_data_supabase():
    client = get_supabase_client()
    if client is None:
        return None
    try:
        response = client.table("favorite_items").select(
            "user_id,item_key,word,answer"
        ).execute()
    except Exception:
        return None

    favorites_data = {person: {} for person in PERSON_LABELS}
    for row in response.data or []:
        user_id = str(row.get("user_id", "")).strip().lower()
        if user_id not in PERSON_LABELS:
            continue
        word = str(row.get("word", "")).strip()
        answer = str(row.get("answer", "")).strip()
        if not word or not answer:
            continue
        item_key = str(row.get("item_key") or review_item_key(word, answer))
        favorites_data[user_id][item_key] = {
            "word": word,
            "answer": answer,
        }
    return favorites_data


def save_favorites_data_supabase(favorites_data):
    client = get_supabase_client()
    if client is None:
        return False

    rows = []
    for person in PERSON_LABELS:
        for item_key, entry in favorites_data.get(person, {}).items():
            rows.append(
                {
                    "user_id": person,
                    "item_key": item_key,
                    "word": entry["word"],
                    "answer": entry["answer"],
                }
            )

    try:
        for person in PERSON_LABELS:
            client.table("favorite_items").delete().eq("user_id", person).execute()
        if rows:
            client.table("favorite_items").upsert(rows).execute()
        return True
    except Exception:
        return False


def load_progress_data_supabase():
    client = get_supabase_client()
    if client is None:
        return None
    try:
        response = client.table("deck_progress").select(
            "user_id,deck_filename,completed_card_ids"
        ).execute()
    except Exception:
        return None

    progress_data = {person: {} for person in PERSON_LABELS}
    for row in response.data or []:
        user_id = str(row.get("user_id", "")).strip().lower()
        if user_id not in PERSON_LABELS:
            continue
        filename = str(row.get("deck_filename", "")).strip()
        card_ids = row.get("completed_card_ids", [])
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

        if filename and normalized_ids:
            progress_data[user_id][filename] = sorted(normalized_ids, key=completion_sort_key)
    return progress_data


def save_progress_data_supabase(progress_data):
    client = get_supabase_client()
    if client is None:
        return False

    rows = []
    for person in PERSON_LABELS:
        for filename, card_ids in progress_data.get(person, {}).items():
            normalized_ids = []
            seen_ids = set()
            for card_id in card_ids:
                normalized_id = normalize_card_id(card_id)
                if not normalized_id or normalized_id in seen_ids:
                    continue
                seen_ids.add(normalized_id)
                normalized_ids.append(normalized_id)
            if normalized_ids:
                rows.append(
                    {
                        "user_id": person,
                        "deck_filename": filename,
                        "completed_card_ids": sorted(normalized_ids, key=completion_sort_key),
                    }
                )

    try:
        for person in PERSON_LABELS:
            client.table("deck_progress").delete().eq("user_id", person).execute()
        if rows:
            client.table("deck_progress").upsert(rows).execute()
        return True
    except Exception:
        return False


@st.cache_data(show_spinner=False, ttl=15)
def load_prefs():
    local_pref_data = load_prefs_local()
    if not cloud_sync_enabled():
        return local_pref_data

    cloud_pref_data = load_prefs_supabase()
    if cloud_pref_data is None:
        return local_pref_data
    if prefs_are_default(cloud_pref_data) and not prefs_are_default(local_pref_data):
        if save_prefs_supabase(local_pref_data):
            return normalize_prefs(local_pref_data)
    return merge_local_ai_pref_fields(cloud_pref_data, local_pref_data)


def save_prefs(pref_data):
    normalized = normalize_prefs(pref_data)
    save_prefs_local(normalized)
    save_prefs_supabase(normalized)
    clear_runtime_caches()


@st.cache_data(show_spinner=False, ttl=15)
def load_review_data():
    local_review_data = load_review_data_local()
    if not cloud_sync_enabled():
        return local_review_data

    cloud_review_data = load_review_data_supabase()
    if cloud_review_data is None:
        return local_review_data
    if not review_data_has_entries(cloud_review_data) and review_data_has_entries(local_review_data):
        if save_review_data_supabase(local_review_data):
            return local_review_data
    return cloud_review_data


def save_review_data(review_data):
    save_review_data_local(review_data)
    save_review_data_supabase(review_data)
    clear_runtime_caches()


@st.cache_data(show_spinner=False, ttl=15)
def load_favorites_data():
    local_favorites_data = load_favorites_data_local()
    if not cloud_sync_enabled():
        return local_favorites_data

    cloud_favorites_data = load_favorites_data_supabase()
    if cloud_favorites_data is None:
        return local_favorites_data
    if not favorites_data_has_entries(cloud_favorites_data) and favorites_data_has_entries(local_favorites_data):
        if save_favorites_data_supabase(local_favorites_data):
            return local_favorites_data
    return cloud_favorites_data


def save_favorites_data(favorites_data):
    save_favorites_data_local(favorites_data)
    save_favorites_data_supabase(favorites_data)
    clear_runtime_caches()


@st.cache_data(show_spinner=False, ttl=15)
def load_progress_data():
    local_progress_data = load_progress_data_local()
    if not cloud_sync_enabled():
        return local_progress_data

    cloud_progress_data = load_progress_data_supabase()
    if cloud_progress_data is None:
        return local_progress_data
    if not progress_data_has_entries(cloud_progress_data) and progress_data_has_entries(local_progress_data):
        if save_progress_data_supabase(local_progress_data):
            return local_progress_data
    return cloud_progress_data


def save_progress_data(progress_data):
    save_progress_data_local(progress_data)
    save_progress_data_supabase(progress_data)
    clear_runtime_caches()


def empty_monthly_progress_history():
    return {person: {} for person in PERSON_LABELS}


def normalize_month_key(value):
    if value is None:
        return None
    try:
        return datetime.strptime(str(value).strip(), "%Y-%m").strftime("%Y-%m")
    except ValueError:
        return None


def month_start_from_key(month_key):
    normalized = normalize_month_key(month_key)
    if normalized is None:
        return None
    return datetime.strptime(normalized, "%Y-%m").date().replace(day=1)


def month_key_from_date(value):
    return value.strftime("%Y-%m")


def add_months(value, months):
    total_months = (value.year * 12 + (value.month - 1)) + months
    year = total_months // 12
    month = total_months % 12 + 1
    return date(year, month, 1)


def previous_month_start(value):
    return add_months(value.replace(day=1), -1)


def month_key_sort_key(month_key):
    normalized = normalize_month_key(month_key)
    if normalized is None:
        return (0, 0)
    year_text, month_text = normalized.split("-", 1)
    return (int(year_text), int(month_text))


def month_keys_between(start_month_key, end_month_key):
    start_month = month_start_from_key(start_month_key)
    end_month = month_start_from_key(end_month_key)
    if start_month is None or end_month is None or start_month > end_month:
        return []

    month_keys = []
    current_month = start_month
    while current_month <= end_month:
        month_keys.append(month_key_from_date(current_month))
        current_month = add_months(current_month, 1)
    return month_keys


@st.cache_data(show_spinner=False, ttl=15)
def load_monthly_progress_history():
    empty = empty_monthly_progress_history()
    client = get_supabase_client()
    if client is None:
        return empty
    try:
        response = client.table(MONTHLY_PROGRESS_HISTORY_TABLE).select(
            "user_id,month_key,learned_count"
        ).execute()
    except Exception:
        return empty

    history = empty_monthly_progress_history()
    for row in response.data or []:
        user_id = str(row.get("user_id", "")).strip().lower()
        if user_id not in PERSON_LABELS:
            continue
        month_key = normalize_month_key(row.get("month_key"))
        if month_key is None:
            continue
        try:
            learned_count = int(row.get("learned_count", 0))
        except (TypeError, ValueError):
            learned_count = 0
        history[user_id][month_key] = max(learned_count, 0)
    return history


def save_monthly_progress_history_rows(rows):
    if not rows:
        return True
    client = get_supabase_client()
    if client is None:
        return False

    normalized_rows = []
    for row in rows:
        user_id = str(row.get("user_id", "")).strip().lower()
        month_key = normalize_month_key(row.get("month_key"))
        if user_id not in PERSON_LABELS or month_key is None:
            continue
        try:
            learned_count = int(row.get("learned_count", 0))
        except (TypeError, ValueError):
            learned_count = 0
        normalized_rows.append(
            {
                "user_id": user_id,
                "month_key": month_key,
                "learned_count": max(learned_count, 0),
            }
        )

    if not normalized_rows:
        return True

    try:
        client.table(MONTHLY_PROGRESS_HISTORY_TABLE).upsert(normalized_rows).execute()
        clear_runtime_caches()
        return True
    except Exception:
        return False


def delete_monthly_progress_history(person):
    client = get_supabase_client()
    if client is None:
        return False
    try:
        client.table(MONTHLY_PROGRESS_HISTORY_TABLE).delete().eq("user_id", person).execute()
        clear_runtime_caches()
        return True
    except Exception:
        return False


def delete_monthly_progress_history_row(person, month_key):
    client = get_supabase_client()
    normalized_month_key = normalize_month_key(month_key)
    if client is None or person not in PERSON_LABELS or normalized_month_key is None:
        return False
    try:
        client.table(MONTHLY_PROGRESS_HISTORY_TABLE).delete().eq("user_id", person).eq("month_key", normalized_month_key).execute()
        clear_runtime_caches()
        return True
    except Exception:
        return False


def current_trackable_cards_count():
    trackable_total = 0
    for filename in csv_files:
        metadata = deck_completion_metadata(filename)
        if metadata["supported"]:
            trackable_total += metadata["total"]
    return trackable_total


def learned_words_completed_count_value(person):
    total_completed = 0
    person_progress = st.session_state.progress_data.get(person, {})
    for filename in csv_files:
        metadata = deck_completion_metadata(filename)
        if not metadata["supported"]:
            continue
        completed_ids = set(person_progress.get(filename, []))
        if not completed_ids:
            continue
        total_completed += len(completed_ids & set(metadata["valid_ids"]))
    return total_completed


def repair_legacy_monthly_progress_snapshot(person, today, current_learned_count):
    current_month_key = month_key_from_date(today)
    previous_month_key = month_key_from_date(previous_month_start(today))
    person_history = dict(st.session_state.monthly_progress_history.get(person, {}))

    if current_month_key in person_history:
        return person_history
    if previous_month_key not in person_history:
        return person_history

    previous_month_count = int(person_history.get(previous_month_key, 0))
    if previous_month_count != current_learned_count:
        return person_history

    current_month_row = {
        "user_id": person,
        "month_key": current_month_key,
        "learned_count": current_learned_count,
    }
    if not save_monthly_progress_history_rows([current_month_row]):
        return person_history

    updated_history = st.session_state.monthly_progress_history.setdefault(person, {})
    updated_history[current_month_key] = current_learned_count

    if delete_monthly_progress_history_row(person, previous_month_key):
        updated_history.pop(previous_month_key, None)

    return dict(updated_history)


def ensure_monthly_progress_snapshot(person, today=None):
    if person not in PERSON_LABELS:
        return False

    today = today or date.today()
    current_learned_count = learned_words_completed_count_value(person)
    target_month_key = month_key_from_date(today)
    person_history = repair_legacy_monthly_progress_snapshot(person, today, current_learned_count)
    if target_month_key in person_history:
        existing_count = int(person_history.get(target_month_key, 0))
        if existing_count == current_learned_count:
            return False
        replacement_row = {
            "user_id": person,
            "month_key": target_month_key,
            "learned_count": current_learned_count,
        }
        if not save_monthly_progress_history_rows([replacement_row]):
            return False
        st.session_state.monthly_progress_history.setdefault(person, {})[target_month_key] = current_learned_count
        return True

    rows_to_insert = []
    existing_month_keys = sorted(person_history.keys(), key=month_key_sort_key)

    if not existing_month_keys:
        rows_to_insert.append(
            {
                "user_id": person,
                "month_key": target_month_key,
                "learned_count": current_learned_count,
            }
        )
    else:
        latest_month_key = existing_month_keys[-1]
        if month_key_sort_key(latest_month_key) >= month_key_sort_key(target_month_key):
            return False
        last_known_count = int(person_history.get(latest_month_key, 0))
        missing_month_keys = month_keys_between(
            month_key_from_date(add_months(month_start_from_key(latest_month_key), 1)),
            target_month_key,
        )
        for month_key in missing_month_keys[:-1]:
            rows_to_insert.append(
                {
                    "user_id": person,
                    "month_key": month_key,
                    "learned_count": last_known_count,
                }
            )
        rows_to_insert.append(
            {
                "user_id": person,
                "month_key": target_month_key,
                "learned_count": current_learned_count,
            }
        )

    if not save_monthly_progress_history_rows(rows_to_insert):
        return False

    updated_history = st.session_state.monthly_progress_history.setdefault(person, {})
    for row in rows_to_insert:
        updated_history[row["month_key"]] = int(row["learned_count"])
    return bool(rows_to_insert)


def progress_chart_rows(person, months=12, today=None):
    today = today or date.today()
    live_learned_count = learned_words_completed_count_value(person)
    current_month = date(today.year, today.month, 1)
    start_month = add_months(current_month, -(months - 1))
    current_month_key = month_key_from_date(today)
    person_history = dict(st.session_state.monthly_progress_history.get(person, {}))

    rows = []
    for offset in range(months):
        month_cursor = add_months(start_month, offset)
        month_key = month_key_from_date(month_cursor)
        if month_key == current_month_key:
            learned_count = live_learned_count
        else:
            learned_count = person_history.get(month_key)

        rows.append(
            {
                "Month": month_cursor.strftime("%b %y"),
                "month_key": month_key,
                "Learned Cards": learned_count,
            }
        )
    return rows


def open_progress_screen():
    st.session_state.progress_screen_open = True


def close_progress_screen():
    st.session_state.progress_screen_open = False


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
    saved_active_person = current_person if current_person in PERSON_LABELS else prefs["active_person"]
    if current_person in PERSON_LABELS:
        person_settings[current_person] = {
            "theme": st.session_state.theme,
            "direction_mode": st.session_state.direction_mode,
            "speech_speed": st.session_state.speech_speed,
            "show_hints": st.session_state.show_hints,
            "auto_speak_spanish": False,
            "story_reading_speed": st.session_state.story_reading_speed,
            "story_pause_amount": st.session_state.story_pause_amount,
            "ai_sentence_tenses": sanitize_ai_sentence_tenses(st.session_state.ai_sentence_tenses),
            "ai_sentence_level": st.session_state.ai_sentence_level,
            "ai_examples_target_words": st.session_state.ai_examples_target_words,
            "ai_auto_play_examples": st.session_state.ai_auto_play_examples,
        }
    return {
        "active_person": saved_active_person,
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
favorites_data = load_favorites_data()
progress_data = load_progress_data()
monthly_progress_history = load_monthly_progress_history()
startup_person = prefs["active_person"] if prefs["active_person"] in PERSON_LABELS else next(iter(PERSON_LABELS))
active_person_prefs = prefs["person_settings"][startup_person]

defaults = {
    "theme":          active_person_prefs["theme"],
    "menu_open":      False,
    "direction_mode": active_person_prefs["direction_mode"],
    "speech_speed":   active_person_prefs["speech_speed"],
    "show_hints":     active_person_prefs["show_hints"],
    "auto_speak_spanish": False,
    "auto_speak_spanish_generation": 0,
    "story_reading_speed": active_person_prefs["story_reading_speed"],
    "story_pause_amount": active_person_prefs["story_pause_amount"],
    "ai_sentence_tenses": sanitize_ai_sentence_tenses(active_person_prefs["ai_sentence_tenses"]),
    "ai_sentence_level": active_person_prefs["ai_sentence_level"],
    "ai_examples_target_words": active_person_prefs["ai_examples_target_words"],
    "ai_auto_play_examples": active_person_prefs["ai_auto_play_examples"],
    "active_person":  None,
    "person_radio":   None,
    "person_selector_visible": True,
    "person_settings": prefs["person_settings"],
    "review_data":    review_data,
    "favorites_data": favorites_data,
    "progress_data":  progress_data,
    "monthly_progress_history": monthly_progress_history,
    "selected_csv":   None,
    "study_mode":     None,
    "cards":          [],
    "order":          [],
    "index":          0,
    "show_answer":    False,
    "regular_auto_mode": False,
    "regular_auto_include_english": True,
    "regular_auto_repeat_spanish": False,
    "regular_auto_cue_prompt": True,
    "regular_auto_generation": 0,
    "regular_auto_mode_checkbox": False,
    "regular_auto_english_checkbox": True,
    "regular_auto_repeat_checkbox": False,
    "regular_auto_cue_checkbox": True,
    "direction":      direction_for_mode(active_person_prefs["direction_mode"]),
    "quit_requested": False,
    "final_exit":     False,
    "progress_screen_open": False,
    "loaded_csv":     None,
    "score_actions":  0,
    "score_correct":  0,
    "score_repeat":   0,
    "erase_review_confirm": False,
    "erase_favorites_confirm": False,
    "initialize_all_decks_confirm": False,
    "delete_review_confirm_key": None,
    "open_deck_categories": [],
    "open_deck_subcategories": [],
    "deck_picker_scroll_target": None,
    "story_playback_mode": "continuous",
    "story_display_mode": "both",
    "story_audio_on": True,
    "story_repeat_spanish_on": False,
    "story_random_on": False,
    "story_started": False,
    "story_running": False,
    "story_finished": False,
    "story_run_token": 0,
    "story_resume_next": False,
    "ai_examples_signature": None,
    "ai_examples_sentences": [],
    "ai_examples_index": 0,
    "ai_examples_error": None,
    "ai_examples_reload_unlocked": False,
    "ai_examples_loading": False,
    "ai_examples_pending_action": None,
    "ai_examples_autoplay_generation": 0,
    "ai_examples_translations": [],
    "ai_examples_show_english": False,
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

active_person_query_value = st.query_params.get("active_person")
if active_person_query_value in PERSON_LABELS and st.session_state.active_person not in PERSON_LABELS:
    st.session_state.active_person = active_person_query_value
    st.session_state.person_selector_visible = False
    st.session_state.person_settings = prefs["person_settings"]
    restored_person_prefs = sanitize_person_prefs(
        st.session_state.person_settings.get(active_person_query_value, {}),
        default_person_prefs(),
    )
    st.session_state.person_settings[active_person_query_value] = restored_person_prefs
    st.session_state.theme = restored_person_prefs["theme"]
    st.session_state.direction_mode = restored_person_prefs["direction_mode"]
    st.session_state.speech_speed = restored_person_prefs["speech_speed"]
    st.session_state.show_hints = restored_person_prefs["show_hints"]
    st.session_state.auto_speak_spanish = False
    st.session_state.story_reading_speed = restored_person_prefs["story_reading_speed"]
    st.session_state.story_pause_amount = restored_person_prefs["story_pause_amount"]
    st.session_state.ai_sentence_tenses = sanitize_ai_sentence_tenses(restored_person_prefs["ai_sentence_tenses"])
    st.session_state.ai_sentence_level = restored_person_prefs["ai_sentence_level"]
    st.session_state.ai_examples_target_words = restored_person_prefs["ai_examples_target_words"]
    st.session_state.ai_auto_play_examples = restored_person_prefs["ai_auto_play_examples"]
    st.session_state.direction = direction_for_mode(restored_person_prefs["direction_mode"])

if "ai_auto_play_examples_default_off_migrated" not in st.session_state:
    for person in PERSON_LABELS:
        migrated_person_prefs = sanitize_person_prefs(
            st.session_state.person_settings.get(person, {}),
            default_person_prefs(),
        )
        migrated_person_prefs["ai_auto_play_examples"] = False
        st.session_state.person_settings[person] = migrated_person_prefs
    st.session_state.ai_auto_play_examples = False
    st.session_state["ai_auto_play_examples_default_off_migrated"] = True
    save_prefs(current_prefs())

if "ai_tense_forms_v2_migrated" not in st.session_state:
    st.session_state["ai_tense_forms_v2_migrated"] = True

if "story_display_mode" not in st.session_state:
    legacy_prompt_on = st.session_state.get("story_prompt_on", True)
    legacy_english_on = st.session_state.get(
        "story_english_on",
        st.session_state.get("story_translation_on", True),
    )
    if legacy_prompt_on and legacy_english_on:
        st.session_state.story_display_mode = "both"
    elif legacy_prompt_on:
        st.session_state.story_display_mode = "spanish"
    elif legacy_english_on:
        st.session_state.story_display_mode = "english"
    else:
        st.session_state.story_display_mode = "both"

t = THEMES[st.session_state.theme]


def sync_menu_widget_state():
    st.session_state.menu_ai_word_target_pending_value = st.session_state.ai_examples_target_words


def store_active_person_prefs():
    if st.session_state.active_person not in PERSON_LABELS:
        return
    st.session_state.person_settings[st.session_state.active_person] = {
        "theme": st.session_state.theme,
        "direction_mode": st.session_state.direction_mode,
        "speech_speed": st.session_state.speech_speed,
        "show_hints": st.session_state.show_hints,
        "auto_speak_spanish": st.session_state.auto_speak_spanish,
        "story_reading_speed": st.session_state.story_reading_speed,
        "story_pause_amount": st.session_state.story_pause_amount,
        "ai_sentence_tenses": sanitize_ai_sentence_tenses(st.session_state.ai_sentence_tenses),
        "ai_sentence_level": st.session_state.ai_sentence_level,
        "ai_examples_target_words": st.session_state.ai_examples_target_words,
        "ai_auto_play_examples": st.session_state.ai_auto_play_examples,
    }


def close_menu_and_save():
    store_active_person_prefs()
    save_prefs(current_prefs())
    st.session_state.menu_open = False
    clear_menu_destructive_confirms()


def activate_person(person):
    if person not in PERSON_LABELS:
        return
    st.session_state.active_person = person
    st.session_state.person_selector_visible = False
    st.session_state.login_handoff_token = None
    clear_login_handoff()
    apply_person_prefs(person)
    clear_menu_destructive_confirms()
    save_prefs(current_prefs())
    ensure_monthly_progress_snapshot(person)


def clear_splash_query_action():
    if "splash_action" in st.query_params:
        del st.query_params["splash_action"]
    clear_login_handoff_query_param()


def handle_splash_action():
    action = st.query_params.get("splash_action")
    if action not in SPLASH_ACTIONS:
        return

    clear_splash_query_action()

    if action in PERSON_LABELS:
        if st.session_state.selected_csv is None and st.session_state.person_selector_visible:
            activate_person(action)
            st.rerun()
        return

    if action == "quit" and st.session_state.selected_csv is None and st.session_state.person_selector_visible:
        st.session_state.menu_open = False
        st.session_state.final_exit = True
        st.rerun()


def handle_splash_selection(action):
    if action in PERSON_LABELS:
        if st.session_state.selected_csv is None and st.session_state.person_selector_visible:
            activate_person(action)
        return

    if action == "quit" and st.session_state.selected_csv is None and st.session_state.person_selector_visible:
        st.session_state.menu_open = False
        st.session_state.final_exit = True


def polygon_points_attribute(points):
    return " ".join(f"{x},{y}" for x, y in points)


def inject_splash_action_bridge():
    components.html(
        """
        <script>
        (function() {
            var doc = window.parent.document;
            var bridgeKey = '__splashActionBridge_v1';

            if (window.parent[bridgeKey]) {
                return;
            }
            window.parent[bridgeKey] = true;

            function findHiddenButton(key, label) {
                if (key) {
                    var byClass = doc.querySelector(
                        '.st-key-' + key + ' button, [class*="st-key-' + key + '"] button'
                    );
                    if (byClass) return byClass;
                }

                if (label) {
                    var buttons = Array.from(doc.querySelectorAll('button'));
                    var byLabel = buttons.find(function(candidate) {
                        return candidate.textContent && candidate.textContent.trim() === label;
                    });
                    if (byLabel) return byLabel;
                }

                return null;
            }

            doc.addEventListener('click', function(event) {
                var button = event.target && event.target.closest
                    ? event.target.closest('.splash-action-button[data-splash-button-key]')
                    : null;
                if (!button) {
                    return;
                }

                event.preventDefault();

                var key = button.getAttribute('data-splash-button-key');
                var label = button.getAttribute('data-splash-button-label');
                var hiddenButton = findHiddenButton(key, label);
                if (hiddenButton) {
                    hiddenButton.click();
                }
            }, true);
        })();
        </script>
        """,
        height=0,
    )


def render_splash_selector():
    splash_data_uri = splash_image_data_uri()
    if not splash_data_uri:
        with st.container(key="person_radio_wrap"):
            selected_person = st.radio(
                "Select user:",
                options=list(PERSON_LABELS.keys()),
                index=None,
                horizontal=True,
                format_func=lambda value: PERSON_LABELS[value],
                key="person_radio",
            )
            if selected_person in PERSON_LABELS and selected_person != st.session_state.active_person:
                activate_person(selected_person)
                st.rerun()
        return

    polygon_markup = "".join(
        "<a href='#' class='splash-link splash-action-button' data-splash-button-key='"
        + html.escape(f"splash_hidden_action_{action}")
        + "' data-splash-button-label='"
        + html.escape(f"hidden-splash_hidden_action_{action}")
        + "' aria-label='"
        + html.escape(action.title())
        + "'><polygon class='splash-hotspot' points='"
        + polygon_points_attribute(points)
        + "'></polygon></a>"
        for action, points in SPLASH_ACTIONS.items()
    )

    splash_html = f"""
            <div class="splash-shell">
                <div class="splash-frame">
                    <img src="{splash_data_uri}" alt="Spanish Flashcards splash screen" class="splash-image" />
                    <svg class="splash-overlay" viewBox="0 0 {SPLASH_IMAGE_DIMENSION} {SPLASH_IMAGE_DIMENSION}" preserveAspectRatio="xMidYMid meet" aria-hidden="true">
                        {polygon_markup}
                    </svg>
                </div>
            </div>
            <style>
                html, body {{
                    margin: 0;
                    padding: 0;
                    background: transparent;
                }}
                .splash-shell {{
                    width: 100%;
                    padding: 0.25rem 0 0.2rem;
                    box-sizing: border-box;
                }}
                .splash-frame {{
                    position: relative;
                    width: 100%;
                    aspect-ratio: 1 / 1;
                    border-radius: 1.2rem;
                    overflow: hidden;
                }}
                .splash-image,
                .splash-overlay {{
                    position: absolute;
                    inset: 0;
                    width: 100%;
                    height: 100%;
                    display: block;
                }}
                .splash-hotspot {{
                    fill: rgba(0, 0, 0, 0.001);
                    stroke: transparent;
                    stroke-width: 0;
                    cursor: pointer;
                    pointer-events: all;
                }}
                .splash-link {{
                    cursor: pointer;
                }}
                .splash-hotspot:hover,
                .splash-hotspot:active {{
                    fill: rgba(0, 0, 0, 0.001);
                    stroke: transparent;
                }}
            </style>
    """

    st.markdown(splash_html, unsafe_allow_html=True)
    for action in SPLASH_ACTIONS:
        st.button(
            f"hidden-splash_hidden_action_{action}",
            key=f"splash_hidden_action_{action}",
            on_click=handle_splash_selection,
            args=(action,),
            use_container_width=True,
        )
    inject_splash_action_bridge()

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
    st.session_state.auto_speak_spanish = False
    st.session_state.story_reading_speed = person_prefs["story_reading_speed"]
    st.session_state.story_pause_amount = person_prefs["story_pause_amount"]
    st.session_state.ai_sentence_tenses = sanitize_ai_sentence_tenses(person_prefs["ai_sentence_tenses"])
    st.session_state.ai_sentence_level = person_prefs["ai_sentence_level"]
    st.session_state.ai_examples_target_words = person_prefs["ai_examples_target_words"]
    st.session_state.ai_auto_play_examples = person_prefs["ai_auto_play_examples"]
    st.session_state.direction = direction_for_mode(person_prefs["direction_mode"])
    sync_menu_widget_state()


def clear_menu_destructive_confirms():
    st.session_state.erase_review_confirm = False
    st.session_state.erase_favorites_confirm = False
    st.session_state.initialize_all_decks_confirm = False


handle_splash_action()


def review_count_for(person):
    return len(st.session_state.review_data.get(person, {}))


def favorites_count_for(person):
    return len(st.session_state.favorites_data.get(person, {}))


def person_has_regular_deck_progress(person):
    person_progress = st.session_state.progress_data.get(person, {})
    return any(
        card_ids
        for filename, card_ids in person_progress.items()
        if not is_review_deck(filename) and not is_favorites_deck(filename) and not is_learned_words_challenge(filename)
    )


def learned_words_completed_count(person):
    return learned_words_completed_count_value(person)


def learned_words_challenge_available(person):
    return learned_words_completed_count(person) >= LEARNED_WORDS_CHALLENGE_MIN_CARDS


def build_learned_words_challenge_cards(person):
    learned_cards = []
    person_progress = st.session_state.progress_data.get(person, {})

    for filename in csv_files:
        completed_ids = set(person_progress.get(filename, []))
        if not completed_ids:
            continue

        deck_data = load_regular_deck(filename)
        if not deck_data["supports_completion"]:
            continue

        for source_index, card in enumerate(deck_data["cards"]):
            card_id = card.get("id")
            if not card_id or card_id not in completed_ids:
                continue
            learned_cards.append(
                {
                    "id": card_id,
                    "word": card["word"],
                    "answer": card["answer"],
                    "shown": False,
                    "scored": False,
                    "repeat_score": 1,
                    "error_flag": 0,
                    "source_deck": filename,
                    "source_index": source_index,
                }
            )

    if len(learned_cards) < LEARNED_WORDS_CHALLENGE_SESSION_SIZE:
        return []

    return random.sample(learned_cards, LEARNED_WORDS_CHALLENGE_SESSION_SIZE)


def review_deck_selectable(deck_value):
    if not is_review_deck(deck_value):
        return True
    person = review_deck_person(deck_value)
    return person == st.session_state.active_person and review_count_for(person) > 0


def favorites_deck_selectable(deck_value):
    if not is_favorites_deck(deck_value):
        return True
    person = favorites_deck_person(deck_value)
    return person == st.session_state.active_person and favorites_count_for(person) > 0


def visible_review_deck_values():
    if review_count_for(st.session_state.active_person) <= 0:
        return []
    active_review_value = REVIEW_DECK_VALUES[st.session_state.active_person]
    return [active_review_value]


def visible_favorites_deck_values():
    if favorites_count_for(st.session_state.active_person) <= 0:
        return []
    active_favorites_value = FAVORITES_DECK_VALUES[st.session_state.active_person]
    return [active_favorites_value]


def reset_study_state(reset_selected=True):
    was_logged_in = st.session_state.get("is_logged_in", False)
    if reset_selected:
        st.session_state.selected_csv = None
    st.session_state.study_mode = None
    st.session_state.loaded_csv = None
    st.session_state.cards = []
    st.session_state.order = []
    st.session_state.index = 0
    st.session_state.show_answer = False
    st.session_state["regular_auto_mode"] = False
    st.session_state["regular_auto_include_english"] = True
    st.session_state["regular_auto_repeat_spanish"] = False
    st.session_state["regular_auto_cue_prompt"] = True
    st.session_state["regular_auto_generation"] += 1
    st.session_state["regular_auto_mode_checkbox"] = False
    st.session_state["regular_auto_english_checkbox"] = True
    st.session_state["regular_auto_repeat_checkbox"] = False
    st.session_state["regular_auto_cue_checkbox"] = True
    st.session_state.quit_requested = False
    st.session_state.final_exit = False
    st.session_state["score_actions"] = 0
    st.session_state["score_correct"] = 0
    st.session_state["score_repeat"] = 0
    st.session_state.delete_review_confirm_key = None
    st.session_state.story_repeat_spanish_on = False
    st.session_state.story_random_on = False
    st.session_state.story_started = False
    st.session_state.story_running = False
    st.session_state.story_finished = False
    st.session_state.story_run_token = 0
    st.session_state.story_resume_next = False
    st.session_state["is_logged_in"] = was_logged_in


def story_title_prefix_present():
    if not is_story_deck(st.session_state.selected_csv) or not st.session_state.cards:
        return False
    first_english = str(st.session_state.cards[0].get("word", "")).strip()
    return first_english.lower().startswith("title:")


def story_playable_card_indexes():
    start_index = 1 if story_title_prefix_present() else 0
    return list(range(start_index, len(st.session_state.cards)))


def rebuild_story_order():
    st.session_state.order = story_playable_card_indexes()
    if st.session_state.story_random_on:
        random.shuffle(st.session_state.order)


def rebuild_story_order_preserving_current():
    if not st.session_state.order:
        st.session_state.order = []
        st.session_state.index = 0
        return

    current_position = min(st.session_state.index, max(len(st.session_state.order) - 1, 0))
    current_card = current_card_index() if st.session_state.order else 0
    remaining = [idx for idx in story_playable_card_indexes() if idx != current_card]

    if st.session_state.story_random_on:
        random.shuffle(remaining)

    insert_at = min(current_position, len(remaining))
    st.session_state.order = remaining[:insert_at] + [current_card] + remaining[insert_at:]
    st.session_state.index = insert_at


def keep_story_playback_alive():
    if not st.session_state.story_running:
        return
    st.session_state.story_started = True
    st.session_state.story_running = True
    st.session_state.story_finished = False
    st.session_state.story_resume_next = False
    st.session_state.story_run_token += 1


def reset_story_playback():
    st.session_state.index = 0
    st.session_state.story_started = False
    st.session_state.story_running = False
    st.session_state.story_finished = False
    st.session_state.story_run_token = 0
    st.session_state.story_resume_next = False


def finish_story():
    if not st.session_state.order:
        reset_story_playback()
        return
    st.session_state.index = max(len(st.session_state.order) - 1, 0)
    st.session_state.story_started = True
    st.session_state.story_running = False
    st.session_state.story_finished = True
    st.session_state.story_resume_next = False


def repeat_story():
    rebuild_story_order()
    reset_story_playback()
    start_story()


def sync_story_option_widget_state():
    st.session_state["story_playback_auto_checkbox"] = st.session_state.story_playback_mode == "continuous"
    st.session_state["story_playback_step_checkbox"] = st.session_state.story_playback_mode == "stop on every line"
    st.session_state["story_audio_checkbox"] = st.session_state.story_audio_on
    st.session_state["story_repeat_checkbox"] = st.session_state.story_repeat_spanish_on
    st.session_state["story_random_checkbox"] = st.session_state.story_random_on
    st.session_state["story_display_mode_radio"] = normalize_story_display_mode(st.session_state.story_display_mode)


def select_story_playback_mode(mode):
    st.session_state.story_playback_mode = mode
    st.session_state["story_playback_auto_checkbox"] = mode == "continuous"
    st.session_state["story_playback_step_checkbox"] = mode == "stop on every line"


def toggle_story_playback_auto():
    if st.session_state.get("story_playback_auto_checkbox"):
        select_story_playback_mode("continuous")
    else:
        st.session_state["story_playback_auto_checkbox"] = True


def toggle_story_playback_step():
    if st.session_state.get("story_playback_step_checkbox"):
        select_story_playback_mode("stop on every line")
    else:
        st.session_state["story_playback_step_checkbox"] = True


def normalize_story_display_mode(value):
    if value in {"spanish", "english", "both"}:
        return value
    return "both"


def toggle_story_display_mode():
    st.session_state.story_display_mode = normalize_story_display_mode(
        st.session_state.get("story_display_mode_radio", "both")
    )


def toggle_story_audio():
    st.session_state.story_audio_on = st.session_state.get("story_audio_checkbox", True)


def toggle_story_repeat_spanish():
    st.session_state.story_repeat_spanish_on = st.session_state.get("story_repeat_checkbox", False)
    keep_story_playback_alive()


def toggle_story_random():
    random_enabled = st.session_state.get("story_random_checkbox", False)
    if random_enabled != st.session_state.story_random_on:
        st.session_state.story_random_on = random_enabled
        rebuild_story_order_preserving_current()
        st.session_state.story_started = True
        st.session_state.story_finished = False
        st.session_state.story_resume_next = False
        keep_story_playback_alive()


def end_story_to_final_screen():
    go_back_to_deck_picker()
    st.session_state.final_exit = True


def activate_deck(deck_value):
    reset_study_state(reset_selected=False)
    st.session_state.selected_csv = deck_value
    st.session_state.open_deck_categories = []
    st.session_state.open_deck_subcategories = []
    if is_dialog_deck(deck_value):
        st.session_state.study_mode = "dialog"
    elif is_story_deck(deck_value):
        st.session_state.study_mode = "story"
    else:
        st.session_state.study_mode = "all" if (is_review_deck(deck_value) or is_favorites_deck(deck_value) or is_learned_words_challenge(deck_value)) else None
    st.session_state.person_selector_visible = False
    st.session_state.direction = effective_direction(deck_value)


def go_back_to_deck_picker():
    st.session_state.menu_open = False
    clear_menu_destructive_confirms()
    st.session_state.open_deck_categories = []
    st.session_state.open_deck_subcategories = []
    reset_study_state(reset_selected=True)


def clear_picker_query_action():
    if "picker_action" in st.query_params:
        del st.query_params["picker_action"]
    if "picker_target" in st.query_params:
        del st.query_params["picker_target"]


def handle_picker_query_action():
    action = st.query_params.get("picker_action")
    target = st.query_params.get("picker_target")
    if not action:
        return

    clear_picker_query_action()

    if action == "toggle_category" and target:
        toggle_deck_category(target)
        st.rerun()
        return

    if action == "toggle_subcategory" and target:
        category_id = target.split("/", 1)[0]
        subcategory_id = target
        toggle_deck_subcategory(category_id, subcategory_id)
        st.rerun()
        return

    if action == "select_deck" and target:
        activate_deck(target)
        st.rerun()


def picker_query_href(action, target=None):
    query = [f"picker_action={quote(str(action), safe='')}"]
    if target is not None:
        query.append(f"picker_target={quote(str(target), safe='')}")

    handoff_token = st.query_params.get("auth_handoff") or ensure_login_handoff_token()
    if handoff_token:
        query.append(f"auth_handoff={quote(str(handoff_token), safe='')}")

    active_person = st.session_state.get("active_person")
    if active_person in PERSON_LABELS:
        query.append(f"active_person={quote(str(active_person), safe='')}")

    return "?" + "&".join(query)


def picker_hidden_button_key(prefix, *parts):
    sanitized_parts = [re.sub(r"[^a-zA-Z0-9_]+", "_", str(part)) for part in parts]
    return prefix + "_" + "_".join(part for part in sanitized_parts if part)


def picker_hidden_button_label(button_key):
    return f"hidden-{button_key}"


def picker_icon_for_status(status):
    return {
        "review": "★",
        "favorites": "♥︎",
        "challenge": "🎯",
        "dialog": "💬",
        "story": "📖",
        "untouched": "•",
        "in_progress": "●",
        "complete": "✓",
    }.get(status, "•")


def picker_row_label_html(label_text, italicized=False):
    escaped = html.escape(label_text)
    if italicized:
        return f"<em>{escaped}</em>"
    return escaped


def picker_row_markup(label_html, icon_text, row_class, action, target, anchor_key=None, extra_classes=None, button_key=None):
    class_names = ["deck-picker-row", row_class]
    if extra_classes:
        class_names.extend(extra_classes)

    anchor_attr = ""
    if anchor_key:
        anchor_attr = f' data-picker-anchor="{html.escape(anchor_key)}"'

    icon_markup = (
        f'<span class="deck-picker-row-icon" aria-hidden="true">{html.escape(icon_text)}&nbsp;</span>'
    )

    if button_key:
        button_label = picker_hidden_button_label(button_key)
        return (
            f'<a class="{' '.join(class_names)} deck-picker-action-button" href="#" data-picker-button-key="{html.escape(button_key)}" data-picker-button-label="{html.escape(button_label)}"{anchor_attr}>'
            f'{icon_markup}'
            f'<span class="deck-picker-row-label">{label_html}</span>'
            "</a>"
        )

    return (
        f'<a class="{' '.join(class_names)}" href="{picker_query_href(action, target)}" target="_self"{anchor_attr}>'
        f'{icon_markup}'
        f'<span class="deck-picker-row-label">{label_html}</span>'
        "</a>"
    )


def picker_status_class(status):
    return f"deck-picker-status-{status}"


def picker_folder_depth(folder_key):
    if not folder_key:
        return 0
    return max(len(pathlib.PurePosixPath(folder_key).parts) - 1, 0)


def picker_folder_depth_class(depth):
    return f"deck-picker-row-folder-depth-{min(depth, 5)}"


def picker_file_depth_class(depth):
    return f"deck-picker-row-file-depth-{min(depth, 5)}"


def picker_story_child_depth_class(depth):
    return f"deck-picker-row-story-child-depth-{min(depth, 5)}"


def append_picker_file_row(file_entry, folder_depth, picker_rows, hidden_toggle_actions, active_person, child_folder_context=False):
    csv_file = file_entry["filename"]
    status = deck_picker_status(csv_file, active_person)
    button_key = picker_hidden_button_key("picker_hidden_select_deck", csv_file)
    hidden_toggle_actions.append((button_key, activate_deck, (csv_file,)))

    if file_entry.get("is_picker_child") or child_folder_context:
        row_class = "deck-picker-row-story-child"
        extra_classes = [
            "deck-picker-row-nested-child",
            picker_story_child_depth_class(folder_depth),
            picker_status_class(status),
        ]
    else:
        row_class = "deck-picker-row-file" if folder_depth == 0 else "deck-picker-row-subcategory-file"
        extra_classes = [
            picker_file_depth_class(folder_depth),
            picker_status_class(status),
        ]

    picker_rows.append(
        picker_row_markup(
            picker_row_label_html(
                deck_picker_label(
                    csv_file,
                    active_person,
                ),
                italicized=file_entry["italicized"],
            ),
            picker_icon_for_status(status),
            row_class,
            "select_deck",
            csv_file,
            extra_classes=extra_classes,
            button_key=button_key,
        )
    )


def append_picker_file_rows(file_entries, folder_depth, picker_rows, hidden_toggle_actions, active_person, child_folder_context=False):
    for file_entry in file_entries:
        append_picker_file_row(
            file_entry,
            folder_depth,
            picker_rows,
            hidden_toggle_actions,
            active_person,
            child_folder_context=child_folder_context,
        )


def render_picker_folder_contents(folder_node, top_level_category_id, picker_rows, hidden_toggle_actions, active_person, child_folder_context=False):
    for child_entry in folder_node["entries"]:
        if child_entry["entry_type"] == "file":
            append_picker_file_row(
                child_entry,
                picker_folder_depth(folder_node["key"]),
                picker_rows,
                hidden_toggle_actions,
                active_person,
                child_folder_context=child_folder_context,
            )
            continue

        child_folder_key = child_entry["key"]
        child_folder_depth = picker_folder_depth(child_folder_key)
        child_folder_open = is_deck_subcategory_open(top_level_category_id, child_folder_key)
        child_folder_icon = "▼" if child_folder_open else "▶"
        child_folder_label_html = picker_row_label_html(
            f"{child_entry['display_name']} ({picker_folder_item_count(child_entry)})"
        )
        child_folder_button_key = picker_hidden_button_key("picker_hidden_toggle_subcategory", child_folder_key)
        hidden_toggle_actions.append((child_folder_button_key, toggle_deck_subcategory, (top_level_category_id, child_folder_key)))

        extra_classes = [picker_folder_depth_class(child_folder_depth)]
        if child_entry.get("is_picker_child") or child_folder_context:
            extra_classes.extend([
                "deck-picker-row-nested-child",
                picker_story_child_depth_class(child_folder_depth),
            ])

        picker_rows.append(
            picker_row_markup(
                child_folder_label_html,
                child_folder_icon,
                "deck-picker-row-subcategory",
                "toggle_subcategory",
                child_folder_key,
                anchor_key=f"folder:{child_folder_key}",
                extra_classes=extra_classes,
                button_key=child_folder_button_key,
            )
        )

        if child_folder_open:
            render_picker_folder_contents(
                child_entry,
                top_level_category_id,
                picker_rows,
                hidden_toggle_actions,
                active_person,
                child_folder_context=(child_folder_context or child_entry.get("is_picker_child", False)),
            )


def picker_build_code_text():
    return f"{APP_BUILD_CODE} | {PICKER_UI_BUILD_CODE} | {PICKER_CSS_BUILD_CODE}"


def inject_picker_toggle_bridge():
    components.html(
        """
        <script>
        (function() {
            var doc = window.parent.document;
            var bridgeKey = '__deckPickerToggleBridge_v2';

            if (window.parent[bridgeKey]) {
                return;
            }
            window.parent[bridgeKey] = true;

            function findHiddenButton(key, label) {
                if (key) {
                    var byClass = doc.querySelector(
                        '.st-key-' + key + ' button, [class*="st-key-' + key + '"] button'
                    );
                    if (byClass) return byClass;
                }

                if (label) {
                    var buttons = Array.from(doc.querySelectorAll('button'));
                    var byLabel = buttons.find(function(candidate) {
                        return candidate.textContent && candidate.textContent.trim() === label;
                    });
                    if (byLabel) return byLabel;
                }

                return null;
            }

            doc.addEventListener('click', function(event) {
                var button = event.target && event.target.closest
                    ? event.target.closest('.deck-picker-action-button[data-picker-button-key]')
                    : null;
                if (!button) {
                    return;
                }

                var key = button.getAttribute('data-picker-button-key');
                var label = button.getAttribute('data-picker-button-label');
                if (!key) {
                    return;
                }

                event.preventDefault();

                var attempts = 0;
                var maxAttempts = 8;

                function clickHiddenOrFallback() {
                    var hiddenButton = findHiddenButton(key, label);
                    if (hiddenButton) {
                        hiddenButton.click();
                        return;
                    }

                    attempts += 1;
                    if (attempts >= maxAttempts) {
                        return;
                    }

                    window.setTimeout(clickHiddenOrFallback, 35);
                }

                clickHiddenOrFallback();
            }, true);
        })();
        </script>
        """,
        height=0,
    )


handle_picker_query_action()


def render_grouped_deck_picker():
    review_deck_values = visible_review_deck_values()
    favorites_deck_values = visible_favorites_deck_values()
    root_files = picker_root_files()
    root_folder_nodes = picker_root_folder_nodes()
    special_deck_count = 0
    scroll_target = st.session_state.get("deck_picker_scroll_target")
    picker_rows = []
    hidden_toggle_actions = []

    with st.container(key=MOBILE_PICKER_CONTAINER_KEY):
        picker_rows.append(
            "<div class='deck-picker-meta'>"
            "<div class='mobile-deck-picker-label'>Available decks:</div>"
            # f"<div class='deck-picker-build'>{html.escape(picker_build_code_text())}</div>"
            "</div>"
        )

        if learned_words_challenge_available(st.session_state.active_person):
            special_deck_count += 1
            challenge_button_key = picker_hidden_button_key("picker_hidden_select_deck", LEARNED_WORDS_CHALLENGE_VALUE)
            hidden_toggle_actions.append((challenge_button_key, activate_deck, (LEARNED_WORDS_CHALLENGE_VALUE,)))
            picker_rows.append(
                picker_row_markup(
                    picker_row_label_html(learned_words_challenge_label()),
                    picker_icon_for_status("challenge"),
                    "deck-picker-row-special deck-picker-status-challenge",
                    "select_deck",
                    LEARNED_WORDS_CHALLENGE_VALUE,
                    button_key=challenge_button_key,
                )
            )

        for person in PERSON_LABELS:
            review_value = REVIEW_DECK_VALUES[person]
            if review_value not in review_deck_values:
                continue
            special_deck_count += 1
            review_button_key = picker_hidden_button_key("picker_hidden_select_deck", review_value)
            hidden_toggle_actions.append((review_button_key, activate_deck, (review_value,)))
            picker_rows.append(
                picker_row_markup(
                    picker_row_label_html(review_deck_label(person, include_count=True)),
                    picker_icon_for_status("review"),
                    "deck-picker-row-special deck-picker-status-review",
                    "select_deck",
                    review_value,
                    button_key=review_button_key,
                )
            )

        for person in PERSON_LABELS:
            favorites_value = FAVORITES_DECK_VALUES[person]
            if favorites_value not in favorites_deck_values:
                continue
            special_deck_count += 1
            favorites_button_key = picker_hidden_button_key("picker_hidden_select_deck", favorites_value)
            hidden_toggle_actions.append((favorites_button_key, activate_deck, (favorites_value,)))
            picker_rows.append(
                picker_row_markup(
                    picker_row_label_html(favorites_deck_label(person, include_count=True)),
                    picker_icon_for_status("favorites"),
                    "deck-picker-row-special deck-picker-status-favorites",
                    "select_deck",
                    favorites_value,
                    button_key=favorites_button_key,
                )
            )

        if special_deck_count > 0:
            picker_rows.append("<div class='special-deck-separator'></div>")
            picker_rows.append("<div class='special-deck-after-gap'></div>")

        append_picker_file_rows(root_files, 0, picker_rows, hidden_toggle_actions, st.session_state.active_person)

        for category_node in root_folder_nodes:
            category_id = category_node["key"]
            is_open = is_deck_category_open(category_id)
            category_icon = "▼" if is_open else "▶"
            category_label_html = picker_row_label_html(
                f"{category_node['display_name']} ({picker_folder_item_count(category_node)})"
            )
            category_button_key = picker_hidden_button_key("picker_hidden_toggle_category", category_id)
            hidden_toggle_actions.append((category_button_key, toggle_deck_category, (category_id,)))
            picker_rows.append(
                picker_row_markup(
                    category_label_html,
                    category_icon,
                    "deck-picker-row-category",
                    "toggle_category",
                    category_id,
                    anchor_key=f"category:{category_id}",
                    button_key=category_button_key,
                )
            )

            if not is_open:
                continue

            if not category_node["entries"]:
                picker_rows.append("<div class='deck-category-empty'>No files in this category.</div>")
                continue

            render_picker_folder_contents(
                category_node,
                category_id,
                picker_rows,
                hidden_toggle_actions,
                st.session_state.active_person,
            )

        st.markdown("<div class='deck-picker-shell'>" + "".join(picker_rows) + "</div>", unsafe_allow_html=True)

        with st.container(key=PICKER_HIDDEN_ACTIONS_WRAP_KEY):
            for button_key, callback, callback_args in hidden_toggle_actions:
                st.button(
                    picker_hidden_button_label(button_key),
                    key=button_key,
                    on_click=callback,
                    args=callback_args,
                    use_container_width=True,
                )

        inject_picker_toggle_bridge()
        render_mobile_deck_picker_height_fix(scroll_target)
        st.session_state.deck_picker_scroll_target = None


def current_review_person():
    if is_review_deck(st.session_state.selected_csv):
        return review_deck_person(st.session_state.selected_csv)
    return st.session_state.active_person


def current_review_card_key(card):
    return review_item_key(card["word"], card["answer"])


def current_favorite_person():
    if is_favorites_deck(st.session_state.selected_csv):
        return favorites_deck_person(st.session_state.selected_csv)
    return st.session_state.active_person


def favorite_item_from_card(card, source_deck=None, source_index=None):
    effective_source_deck = source_deck or st.session_state.selected_csv
    effective_source_index = current_card_index() if source_index is None else source_index
    source_id = card.get("id")
    return {
        "source_deck": effective_source_deck,
        "source_id": source_id,
        "source_index": effective_source_index,
        "word": card["word"],
        "answer": card["answer"],
    }


def favorite_item_key_from_entry(entry):
    return favorite_item_key(
        entry.get("source_deck"),
        entry.get("source_id"),
        entry.get("source_index"),
        entry.get("word", ""),
        entry.get("answer", ""),
    )


def current_favorite_card_key(card):
    entry = favorite_item_from_card(
        card,
        source_deck=card.get("source_deck"),
        source_index=card.get("source_index"),
    )
    return favorite_item_key_from_entry(entry)


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


def favorite_entry_exists(person, card, source_deck=None, source_index=None):
    entry = favorite_item_from_card(card, source_deck=source_deck, source_index=source_index)
    key = favorite_item_key_from_entry(entry)
    favorites_for_person = st.session_state.favorites_data.get(person, {})
    if key in favorites_for_person:
        return True
    return any(
        favorite_entry.get("word") == entry["word"]
        and favorite_entry.get("answer") == entry["answer"]
        for favorite_entry in favorites_for_person.values()
    )


def upsert_favorite_item(person, card, source_deck=None, source_index=None):
    entry = favorite_item_from_card(card, source_deck=source_deck, source_index=source_index)
    key = favorite_item_key_from_entry(entry)
    st.session_state.favorites_data.setdefault(person, {})[key] = entry
    save_favorites_data(st.session_state.favorites_data)
    return key


def delete_favorite_item(person, card, source_deck=None, source_index=None):
    entry = favorite_item_from_card(card, source_deck=source_deck, source_index=source_index)
    key = favorite_item_key_from_entry(entry)
    favorites_for_person = st.session_state.favorites_data.get(person, {})
    if key not in favorites_for_person:
        matching_key = next(
            (
                existing_key
                for existing_key, favorite_entry in favorites_for_person.items()
                if favorite_entry.get("word") == entry["word"]
                and favorite_entry.get("answer") == entry["answer"]
            ),
            None,
        )
        if matching_key is None:
            return False
        key = matching_key
    del st.session_state.favorites_data[person][key]
    save_favorites_data(st.session_state.favorites_data)
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
    clear_menu_destructive_confirms()
    st.session_state.menu_open = False
    if st.session_state.selected_csv == REVIEW_DECK_VALUES[person]:
        reset_study_state(reset_selected=True)


def erase_favorites_deck(person):
    st.session_state.favorites_data[person] = {}
    save_favorites_data(st.session_state.favorites_data)
    clear_menu_destructive_confirms()
    st.session_state.menu_open = False
    if st.session_state.selected_csv == FAVORITES_DECK_VALUES[person]:
        reset_study_state(reset_selected=True)


def initialize_all_decks(person):
    st.session_state.progress_data[person] = {}
    save_progress_data(st.session_state.progress_data)
    if delete_monthly_progress_history(person):
        st.session_state.monthly_progress_history[person] = {}
    clear_menu_destructive_confirms()
    st.session_state.menu_open = False
    st.session_state.progress_screen_open = False
    if st.session_state.selected_csv and not is_review_deck(st.session_state.selected_csv):
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
.st-key-person_radio_wrap [data-testid="stWidgetLabel"] {{
    margin: 0 !important;
    padding: 0 !important;
    display: flex !important;
    align-items: center !important;
}}
.st-key-person_radio_wrap [data-testid="stWidgetLabel"] p {{
    font-size: 0.95rem !important;
    font-weight: 600 !important;
    margin: 0 !important;
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
.st-key-header_quit_wrap {{
    min-width: 3.2rem !important;
    margin-top: 0.5rem !important;
}}
.st-key-header_quit_wrap div[data-testid="stButton"] {{
    display: flex !important;
    justify-content: flex-end !important;
}}
.st-key-header_quit_wrap div[data-testid="stButton"] > button {{
    min-height: 1.55rem !important;
    min-width: 2.7rem !important;
    width: auto !important;
    padding: 0.06rem 0.42rem !important;
    border-radius: 999px !important;
    background-color: {t['bg']} !important;
    border-color: {t['fg']} !important;
    color: #ff3b30 !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.8rem !important;
    font-weight: 400 !important;
    line-height: 1 !important;
    letter-spacing: 0.08em !important;
    text-transform: uppercase !important;
    white-space: nowrap !important;
}}
.st-key-header_quit_wrap div[data-testid="stButton"] > button [data-testid="stMarkdownContainer"],
.st-key-header_quit_wrap div[data-testid="stButton"] > button [data-testid="stMarkdownContainer"] p,
.st-key-header_quit_wrap div[data-testid="stButton"] > button [data-testid="stMarkdownContainer"] span,
.st-key-header_quit_wrap div[data-testid="stButton"] > button [data-testid="stMarkdownContainer"] div {{
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.8rem !important;
    font-weight: 400 !important;
    line-height: 1 !important;
    letter-spacing: 0.08em !important;
    text-transform: uppercase !important;
    color: #ff3b30 !important;
    margin: 0 !important;
}}
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
.st-key-nextunscored_wrap div[data-testid="stButton"] > button {{
    background-color: #beb0f1 !important;
    border-color: #6940c6 !important;
    color: #49258b !important;
}}
.st-key-favorite_wrap div[data-testid="stButton"] > button {{
    background-color: {t['info_light']} !important;
    border-color: {t['info']} !important;
    color: #1f7cff !important;
    border-radius: 0.75rem !important;
    border-width: 2px !important;
}}
.st-key-favorite_active_wrap div[data-testid="stButton"] > button,
.st-key-storyfavorite_active_wrap div[data-testid="stButton"] > button {{
    background-color: {t['info_light']} !important;
    border-color: {t['info']} !important;
    color: #1f7cff !important;
    border-radius: 0.75rem !important;
    border-width: 2px !important;
    opacity: 1 !important;
}}
.st-key-storyfavorite_wrap div[data-testid="stButton"] > button {{
    background-color: {t['info_light']} !important;
    border-color: {t['info']} !important;
    color: #1f7cff !important;
    border-radius: 0.75rem !important;
    border-width: 2px !important;
}}
.st-key-favorite_active_wrap div[data-testid="stButton"] > button:disabled,
.st-key-storyfavorite_active_wrap div[data-testid="stButton"] > button:disabled {{
    cursor: default !important;
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
    width: 3.6rem !important;
    min-width: 3.6rem !important;
    max-width: 3.6rem !important;
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
    background-color: #ffe0f5 !important;
    border-color: #ff1aaa !important;
    color: #ff1aaa !important;
}}
.st-key-autospeak_off_wrap div[data-testid="stButton"] > button {{
    background-color: rgba(128,128,128,0.12) !important;
    border-color: rgba(128,128,128,0.35) !important;
    color: rgba(140,140,140,0.8) !important;
}}
.st-key-autospeak_on_wrap div[data-testid="stButton"] > button,
.st-key-autospeak_off_wrap div[data-testid="stButton"] > button {{
    width: 3.6rem !important;
    min-height: 3.2rem !important;
    padding: 0.42rem 0.2rem !important;
    font-size: 0.65rem !important;
    font-weight: 700 !important;
    letter-spacing: 0.06em !important;
    line-height: 1.3 !important;
}}
.st-key-answer_action_row_wrap .st-key-autospeak_on_wrap div[data-testid="stButton"] > button [data-testid="stMarkdownContainer"],
.st-key-answer_action_row_wrap .st-key-autospeak_on_wrap div[data-testid="stButton"] > button [data-testid="stMarkdownContainer"] p,
.st-key-answer_action_row_wrap .st-key-autospeak_on_wrap div[data-testid="stButton"] > button [data-testid="stMarkdownContainer"] span,
.st-key-answer_action_row_wrap .st-key-autospeak_on_wrap div[data-testid="stButton"] > button [data-testid="stMarkdownContainer"] div,
.st-key-answer_action_row_wrap .st-key-autospeak_off_wrap div[data-testid="stButton"] > button [data-testid="stMarkdownContainer"],
.st-key-answer_action_row_wrap .st-key-autospeak_off_wrap div[data-testid="stButton"] > button [data-testid="stMarkdownContainer"] p,
.st-key-answer_action_row_wrap .st-key-autospeak_off_wrap div[data-testid="stButton"] > button [data-testid="stMarkdownContainer"] span,
.st-key-answer_action_row_wrap .st-key-autospeak_off_wrap div[data-testid="stButton"] > button [data-testid="stMarkdownContainer"] div {{
    font-size: 0.65rem !important;
    font-weight: 700 !important;
    line-height: 1.3 !important;
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
.special-deck-separator {{
    height: 1px;
    background: color-mix(in srgb, {t['border']} 72%, transparent 28%);
    margin: 0.9rem 0 !important;
}}
.special-deck-after-gap {{
    height: 0.9rem;
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
.st-key-icon_btn_row_wrap {{
    margin-top: 0.32rem !important;
    margin-bottom: 0 !important;
    padding-right: 0.62rem !important;
    box-sizing: border-box !important;
}}
.st-key-icon_btn_row_wrap [data-testid="stVerticalBlock"] {{
    gap: 0 !important;
}}
.st-key-icon_btn_row_wrap [data-testid="stElementContainer"] {{
    margin: 0 !important;
}}
.st-key-icon_btn_row_wrap [data-testid="stHorizontalBlock"] {{
    display: flex !important;
    flex-direction: row !important;
    flex-wrap: nowrap !important;
    justify-content: space-between !important;
    align-items: center !important;
    gap: 0 !important;
    width: 100% !important;
    margin: 0 !important;
}}
.st-key-icon_btn_row_wrap [data-testid="stColumn"] {{
    min-width: 0 !important;
}}
.st-key-icon_btn_row_wrap [data-testid="stColumn"] > div,
.st-key-icon_btn_row_wrap div[data-testid="stButton"],
.st-key-icon_btn_row_wrap div[data-testid="stButton"] > div {{
    width: 100% !important;
}}
.st-key-icon_btn_row_wrap .st-key-showanswer_wrap div[data-testid="stButton"] {{
    display: flex !important;
    justify-content: flex-start !important;
}}
.st-key-icon_btn_row_wrap .st-key-quitbefore_wrap div[data-testid="stButton"] {{
    display: flex !important;
    justify-content: flex-end !important;
}}
.st-key-icon_btn_row_wrap div[data-testid="stButton"] > button {{
    width: 4.8rem !important;
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
.st-key-answer_action_row_wrap {{
    margin-top: 0.32rem !important;
    margin-bottom: 0 !important;
    padding-right: 0.62rem !important;
    box-sizing: border-box !important;
}}
.st-key-answer_action_row_wrap [data-testid="stVerticalBlock"] {{
    gap: 0 !important;
}}
.st-key-answer_action_row_wrap [data-testid="stElementContainer"] {{
    margin: 0 !important;
}}
.st-key-answer_action_row_wrap [data-testid="stHorizontalBlock"] {{
    display: flex !important;
    flex-direction: row !important;
    flex-wrap: nowrap !important;
    justify-content: space-between !important;
    align-items: flex-start !important;
    gap: 0 !important;
    width: 100% !important;
    margin: 0 !important;
}}
.st-key-answer_action_row_wrap [data-testid="stColumn"] {{
    min-width: 0 !important;
}}
.st-key-answer_action_row_wrap [data-testid="stColumn"] > div,
.st-key-answer_action_row_wrap div[data-testid="stButton"],
.st-key-answer_action_row_wrap div[data-testid="stButton"] > div {{
    width: 100% !important;
}}
.st-key-answer_action_row_wrap .st-key-correct_wrap div[data-testid="stButton"],
.st-key-answer_action_row_wrap .st-key-repeat_wrap div[data-testid="stButton"],
.st-key-answer_action_row_wrap .st-key-nextunscored_wrap div[data-testid="stButton"],
.st-key-answer_action_row_wrap .st-key-favorite_wrap div[data-testid="stButton"],
.st-key-answer_action_row_wrap .st-key-favorite_active_wrap div[data-testid="stButton"] {{
    display: flex !important;
    justify-content: flex-start !important;
}}
.st-key-answer_action_row_wrap .st-key-speaker_wrap div[data-testid="stButton"],
.st-key-answer_action_row_wrap .st-key-autospeak_on_wrap div[data-testid="stButton"],
.st-key-answer_action_row_wrap .st-key-autospeak_off_wrap div[data-testid="stButton"],
.st-key-answer_action_row_wrap .st-key-del_active_wrap div[data-testid="stButton"],
.st-key-answer_action_row_wrap .st-key-del_confirm_wrap div[data-testid="stButton"] {{
    display: flex !important;
    justify-content: flex-end !important;
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
    margin: -1px 0 0 0 !important;
    position: relative !important;
    z-index: 1 !important;
}}
.st-key-answer_action_row_wrap .st-key-autoplay_btn_wrap,
.st-key-answer_action_row_wrap .st-key-autoplay_btn_wrap > div,
.st-key-answer_action_row_wrap .st-key-autoplay_btn_wrap [data-testid="stElementContainer"] {{
    width: 100% !important;
    min-width: 100% !important;
}}
.st-key-answer_action_row_wrap .st-key-autoplay_btn_wrap iframe {{
    width: 100% !important;
    min-width: 100% !important;
    max-width: 100% !important;
    display: block !important;
    margin: 0 !important;
    height: 3.2rem !important;
    min-height: 3.2rem !important;
}}
.st-key-icon_btn_row_wrap .st-key-speaker_wrap iframe {{
    width: 100% !important;
    min-width: 100% !important;
    max-width: 100% !important;
    display: block !important;
    margin: 0.16rem 0 0 0 !important;
}}
.st-key-answer_action_row_wrap div[data-testid="stButton"] > button {{
    width: 3.6rem !important;
    min-height: 3.2rem !important;
    font-size: 1.55rem !important;
    font-weight: 700 !important;
}}
.st-key-action_left_group_wrap [data-testid="stHorizontalBlock"] {{
    display: flex !important;
    flex-wrap: nowrap !important;
    justify-content: flex-start !important;
    gap: 0.26rem !important;
    width: fit-content !important;
    margin: 0 !important;
}}
.st-key-action_left_group_wrap [data-testid="stColumn"] {{
    flex: 0 0 3.6rem !important;
    width: 3.6rem !important;
    min-width: 3.6rem !important;
    max-width: 3.6rem !important;
}}
.st-key-action_right_group_wrap [data-testid="stHorizontalBlock"] {{
    display: flex !important;
    flex-wrap: nowrap !important;
    justify-content: flex-end !important;
    gap: 0.26rem !important;
    width: fit-content !important;
    margin-left: auto !important;
    margin-right: 0 !important;
}}
.st-key-action_right_group_wrap [data-testid="stVerticalBlock"] {{
    gap: 0.26rem !important;
    align-items: flex-end !important;
}}
.st-key-action_right_group_wrap [data-testid="stColumn"] {{
    flex: 0 0 3.6rem !important;
    width: 3.6rem !important;
    min-width: 3.6rem !important;
    max-width: 3.6rem !important;
}}
.st-key-action_top_row_wrap [data-testid="stHorizontalBlock"],
.st-key-action_bottom_row_wrap [data-testid="stHorizontalBlock"] {{
    display: flex !important;
    flex-wrap: nowrap !important;
    justify-content: flex-start !important;
    gap: 0.26rem !important;
    width: fit-content !important;
    margin: 0 !important;
}}
.st-key-action_top_row_wrap [data-testid="stColumn"],
.st-key-action_bottom_row_wrap [data-testid="stColumn"]:nth-child(1),
.st-key-action_bottom_row_wrap [data-testid="stColumn"]:nth-child(2) {{
    flex: 0 0 3.6rem !important;
    width: 3.6rem !important;
    min-width: 3.6rem !important;
    max-width: 3.6rem !important;
}}
.st-key-action_bottom_row_wrap [data-testid="stColumn"]:nth-child(3) {{
    flex: 0 0 7.46rem !important;
    width: 7.46rem !important;
    min-width: 7.46rem !important;
    max-width: 7.46rem !important;
}}
.st-key-answer_action_row_wrap .st-key-action_bottom_row_wrap {{
    margin-top: 0.26rem !important;
}}
.st-key-answer_action_row_wrap div[data-testid="stButton"] > button [data-testid="stMarkdownContainer"],
.st-key-answer_action_row_wrap div[data-testid="stButton"] > button [data-testid="stMarkdownContainer"] p,
.st-key-answer_action_row_wrap div[data-testid="stButton"] > button [data-testid="stMarkdownContainer"] span,
.st-key-answer_action_row_wrap div[data-testid="stButton"] > button [data-testid="stMarkdownContainer"] div {{
    font-size: 1.55rem !important;
    font-weight: 700 !important;
    line-height: 1 !important;
}}
.st-key-answer_action_row_phone_wrap {{
    display: none;
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
.st-key-aicycle_hidden_wrap {{
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
.st-key-aireload_hidden_wrap {{
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
.st-key-autospeak_toggle_hidden_wrap {{
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
.st-key-aien_hidden_wrap {{
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
.st-key-ai_autospeak_iframe_wrap {{
    position: fixed !important;
    bottom: 0 !important;
    right: 0 !important;
    width: 1px !important;
    height: 1px !important;
    margin: 0 !important;
    padding: 0 !important;
    overflow: hidden !important;
    clip-path: inset(50%) !important;
    opacity: 0 !important;
    pointer-events: none !important;
    z-index: -1 !important;
}}
.st-key-ai_autospeak_iframe_wrap iframe {{
    width: 1px !important;
    height: 1px !important;
    min-height: 0 !important;
    min-width: 0 !important;
    pointer-events: none !important;
}}
/* iPad fix (2026-04-25): force all hidden helper containers physically off-screen
   so they never paint at their natural document-flow position, even briefly before
   the per-element clip-path/opacity rules above take effect. Programmatic .click()
   on these buttons still works regardless of position, so this only suppresses the
   visual flash and prevents stray touches from landing on them during reflow. To
   revert, delete this block; per-element rules above remain functional. */
.st-key-storyadvance_hidden_wrap,
.st-key-storyfinish_hidden_wrap,
.st-key-storyresumenext_hidden_wrap,
.st-key-regularautoreveal_hidden_wrap,
.st-key-regularautoadvance_hidden_wrap,
.st-key-aicycle_hidden_wrap,
.st-key-aireload_hidden_wrap,
.st-key-aien_hidden_wrap,
.st-key-autospeak_toggle_hidden_wrap,
.st-key-ai_autospeak_iframe_wrap {{
    position: fixed !important;
    top: -10000px !important;
    left: -10000px !important;
    right: auto !important;
    bottom: auto !important;
    width: 1px !important;
    height: 1px !important;
    margin: 0 !important;
    padding: 0 !important;
    overflow: hidden !important;
    pointer-events: none !important;
    z-index: -9999 !important;
}}
.st-key-storyadvance_hidden_wrap *,
.st-key-storyfinish_hidden_wrap *,
.st-key-storyresumenext_hidden_wrap *,
.st-key-regularautoreveal_hidden_wrap *,
.st-key-regularautoadvance_hidden_wrap *,
.st-key-aicycle_hidden_wrap *,
.st-key-aireload_hidden_wrap *,
.st-key-aien_hidden_wrap *,
.st-key-autospeak_toggle_hidden_wrap *,
.st-key-ai_autospeak_iframe_wrap * {{
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
    font-family: 'DM Sans', sans-serif;
    font-size: 0.8rem;
    font-weight: 400;
    line-height: 1;
    color: {t['muted']};
    letter-spacing: 0.08em;
    text-transform: uppercase;
    margin-top: 0.18rem;
    margin-bottom: 0.65rem;
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
    padding: 0.9rem 1.1rem calc(1.4rem + env(safe-area-inset-bottom, 0px)) 1.1rem;
    margin-bottom: 0.7rem;
}}
.menu-bottom-spacer {{
    height: calc(1.35rem + env(safe-area-inset-bottom, 0px));
    width: 100%;
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
[class*="st-key-menu_divider_wrap_"] {{
    margin: 0.8rem 0 0.75rem 0 !important;
}}
[class*="st-key-menu_divider_wrap_"] [data-testid="stElementContainer"],
[class*="st-key-menu_divider_wrap_"] [data-testid="stMarkdownContainer"] {{
    width: calc(100% - 1.1rem) !important;
    max-width: calc(100% - 1.1rem) !important;
    margin-right: auto !important;
    box-sizing: border-box !important;
}}
.menu-divider {{
    width: 100%;
    height: 0.5px;
    background: color-mix(in srgb, {t['divider']} 82%, {t['menu_bg']} 18%);
}}
.st-key-erase_review_wrap,
.st-key-erase_review_confirm_wrap,
.st-key-erase_favorites_wrap,
.st-key-erase_favorites_confirm_wrap,
.st-key-initialize_all_decks_wrap,
.st-key-initialize_all_decks_confirm_wrap {{
    margin-top: 0.95rem !important;
}}
.st-key-erase_review_slot_wrap,
.st-key-erase_favorites_slot_wrap,
.st-key-initialize_all_decks_slot_wrap {{
    height: 4.15rem !important;
    min-height: 4.15rem !important;
    max-height: 4.15rem !important;
    overflow: hidden !important;
}}
.st-key-erase_review_slot_wrap > div[data-testid="stVerticalBlock"],
.st-key-erase_favorites_slot_wrap > div[data-testid="stVerticalBlock"],
.st-key-initialize_all_decks_slot_wrap > div[data-testid="stVerticalBlock"] {{
    gap: 0 !important;
    height: 100% !important;
}}
.st-key-initialize_all_decks_slot_wrap {{
    height: 5.35rem !important;
    min-height: 5.35rem !important;
    max-height: 5.35rem !important;
}}
.st-key-clear_erase_review_confirm_wrap {{
    display: none !important;
}}
.st-key-clear_erase_favorites_confirm_wrap {{
    display: none !important;
}}
.st-key-clear_initialize_all_decks_confirm_wrap {{
    display: none !important;
}}
.st-key-erase_review_wrap div[data-testid="stButton"] > button,
.st-key-erase_review_confirm_wrap div[data-testid="stButton"] > button,
.st-key-erase_favorites_wrap div[data-testid="stButton"] > button,
.st-key-erase_favorites_confirm_wrap div[data-testid="stButton"] > button,
.st-key-initialize_all_decks_wrap div[data-testid="stButton"] > button,
.st-key-initialize_all_decks_confirm_wrap div[data-testid="stButton"] > button {{
    min-height: 2.65rem !important;
    width: 100% !important;
    font-size: 0.95rem !important;
    font-weight: 700 !important;
}}
.st-key-erase_review_confirm_wrap div[data-testid="stButton"] > button {{
    background-color: {t['danger']} !important;
    border-color: {t['danger']} !important;
    color: white !important;
    animation: destructiveConfirmPulse 1s ease-in-out infinite !important;
}}
.st-key-erase_favorites_confirm_wrap div[data-testid="stButton"] > button {{
    background-color: {t['danger']} !important;
    border-color: {t['danger']} !important;
    color: white !important;
    animation: destructiveConfirmPulse 1s ease-in-out infinite !important;
}}
.st-key-initialize_all_decks_confirm_wrap div[data-testid="stButton"] > button {{
    background-color: {t['danger']} !important;
    border-color: {t['danger']} !important;
    color: white !important;
    animation: destructiveConfirmPulse 1s ease-in-out infinite !important;
}}
@media (max-width: 767px) {{
    .st-key-initialize_all_decks_slot_wrap {{
        height: 5.9rem !important;
        min-height: 5.9rem !important;
        max-height: 5.9rem !important;
    }}
}}
@keyframes destructiveConfirmPulse {{
    0%, 100% {{
        background-color: {t['danger']} !important;
        border-color: {t['danger']} !important;
        box-shadow: 0 0 0 0 rgba(255, 255, 255, 0.0), 0 0 0.18rem rgba(120, 0, 0, 0.22);
        filter: brightness(0.88) saturate(0.95);
    }}
    50% {{
        background-color: {t['danger_light']} !important;
        border-color: {t['danger']} !important;
        box-shadow: 0 0 0 0.24rem rgba(255, 255, 255, 0.22), 0 0 1rem rgba(255, 84, 84, 0.65), 0 0 1.65rem rgba(255, 48, 48, 0.35);
        filter: brightness(1.42) saturate(1.2);
    }}
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
.fc-ai-example-wrap {{
    margin-top: 0.7rem;
    padding-top: 0.55rem;
    border-top: 1px solid color-mix(in srgb, {t['border']} 80%, {t['bg']} 20%);
}}
.fc-ai-example-label {{
    font-size: 0.66rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: {t['muted']};
    margin-bottom: 0.2rem;
}}
.fc-ai-example {{
    font-size: 1.02rem;
    line-height: 1.42;
    color: {t['fg']};
}}
.fc-ai-example-count {{
    font-size: 0.76rem;
    color: {t['muted']};
    white-space: nowrap;
}}
.fc-ai-error {{
    margin-top: 0.65rem;
    font-size: 0.83rem;
    line-height: 1.35;
    color: color-mix(in srgb, {t['fg']} 78%, #b84d4d 22%);
}}
.st-key-menu_ai_tenses_wrap [data-testid="stCheckbox"] {{
    margin-bottom: 0.1rem;
}}
.st-key-menu_ai_tenses_wrap [data-testid="stHorizontalBlock"] {{
    display: grid !important;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 0.35rem 0.6rem;
    align-items: start;
}}
.st-key-menu_ai_tenses_wrap [data-testid="stColumn"] {{
    width: 100% !important;
    min-width: 0 !important;
    flex: none !important;
}}
.st-key-menu_ai_tenses_wrap [data-testid="stCheckbox"] label {{
    gap: 0.32rem;
}}
.st-key-menu_ai_tenses_wrap [data-testid="stCheckbox"] p {{
    font-size: 0.82rem;
}}
.st-key-answer_action_row_wrap .st-key-ai_single_wrap div[data-testid="stButton"],
.st-key-answer_action_row_wrap .st-key-ai_fetch_wrap div[data-testid="stButton"],
.st-key-answer_action_row_wrap .st-key-ai_reload_wrap div[data-testid="stButton"],
.st-key-answer_action_row_wrap .st-key-ai_cycle_wrap div[data-testid="stButton"] {{
    display: flex !important;
    justify-content: flex-end !important;
}}
.st-key-answer_action_row_wrap .st-key-ai_status_wrap,
.st-key-answer_action_row_wrap .st-key-ai_counter_wrap {{
    display: flex !important;
    align-items: center !important;
    justify-content: flex-end !important;
    min-height: 3.2rem !important;
}}
.st-key-answer_action_row_wrap .ai-status-label,
.st-key-answer_action_row_wrap .ai-counter-label {{
    font-size: 0.82rem;
    font-weight: 600;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: {t['muted']};
    line-height: 1;
    white-space: nowrap;
    margin: 0 !important;
    transform: translateY(-0.16rem);
}}
.st-key-answer_action_row_wrap .st-key-ai_status_wrap [data-testid="stMarkdownContainer"],
.st-key-answer_action_row_wrap .st-key-ai_status_wrap [data-testid="stMarkdownContainer"] p,
.st-key-answer_action_row_wrap .st-key-ai_status_wrap [data-testid="stMarkdownContainer"] span,
.st-key-answer_action_row_wrap .st-key-ai_status_wrap [data-testid="stMarkdownContainer"] div {{
    margin: 0 !important;
    line-height: 1 !important;
}}
.st-key-answer_action_row_wrap .st-key-ai_single_wrap div[data-testid="stButton"] > button {{
    width: 7.46rem !important;
    min-width: 7.46rem !important;
    min-height: 3.2rem !important;
    border-radius: 1rem !important;
    background: {BUTTON_COLORS['blue']['bg']} !important;
    border-color: {BUTTON_COLORS['blue']['border']} !important;
    color: {BUTTON_COLORS['blue']['fg']} !important;
    font-size: 0.82rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.08em !important;
    text-transform: uppercase !important;
    line-height: 1 !important;
    justify-content: center !important;
    text-align: center !important;
}}
.st-key-answer_action_row_wrap .st-key-ai_single_wrap div[data-testid="stButton"] > button [data-testid="stMarkdownContainer"],
.st-key-answer_action_row_wrap .st-key-ai_single_wrap div[data-testid="stButton"] > button [data-testid="stMarkdownContainer"] p,
.st-key-answer_action_row_wrap .st-key-ai_single_wrap div[data-testid="stButton"] > button [data-testid="stMarkdownContainer"] span,
.st-key-answer_action_row_wrap .st-key-ai_single_wrap div[data-testid="stButton"] > button [data-testid="stMarkdownContainer"] div {{
    font-size: 0.82rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.08em !important;
    text-transform: uppercase !important;
    line-height: 1 !important;
    text-align: center !important;
    width: 100% !important;
}}
.st-key-answer_action_row_wrap .st-key-ai_fetch_wrap button,
.st-key-answer_action_row_wrap .st-key-ai_cycle_wrap button {{
    background: {BUTTON_COLORS['blue']['bg']} !important;
    border-color: {BUTTON_COLORS['blue']['border']} !important;
    color: {BUTTON_COLORS['blue']['fg']} !important;
}}
.st-key-answer_action_row_wrap .st-key-ai_reload_wrap button {{
    background: color-mix(in srgb, {t['card_bg']} 80%, {t['bg']} 20%) !important;
    border-color: {t['border']} !important;
    color: transparent !important;
    position: relative !important;
}}
.st-key-answer_action_row_wrap .st-key-ai_reload_wrap button [data-testid="stMarkdownContainer"],
.st-key-answer_action_row_wrap .st-key-ai_reload_wrap button [data-testid="stMarkdownContainer"] p,
.st-key-answer_action_row_wrap .st-key-ai_reload_wrap button [data-testid="stMarkdownContainer"] span,
.st-key-answer_action_row_wrap .st-key-ai_reload_wrap button [data-testid="stMarkdownContainer"] div {{
    font-size: 0 !important;
    line-height: 0 !important;
}}
.st-key-answer_action_row_wrap .st-key-ai_reload_wrap button::before {{
    content: "⟳";
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -56%);
    font-size: 3.55rem !important;
    font-weight: 400 !important;
    line-height: 1 !important;
    color: {t['fg']} !important;
    pointer-events: none;
}}
.st-key-answer_action_row_wrap .st-key-ai_reload_wrap button:disabled,
.st-key-answer_action_row_wrap .st-key-ai_cycle_wrap button:disabled,
.st-key-answer_action_row_wrap .st-key-ai_single_wrap button:disabled {{
    opacity: 0.42 !important;
}}
.st-key-answer_action_row_wrap .st-key-ai_top_wrap {{
    margin-top: -0.08rem !important;
    margin-bottom: 0.16rem !important;
    position: relative !important;
    z-index: 5 !important;
}}
.st-key-answer_action_row_wrap .st-key-ai_bottom_wrap {{
    margin-top: 0 !important;
    margin-bottom: 0.16rem !important;
    position: relative !important;
    z-index: 1 !important;
}}
.st-key-answer_action_row_wrap .st-key-ai_top_wrap [data-testid="stHorizontalBlock"],
.st-key-answer_action_row_wrap .st-key-ai_bottom_wrap [data-testid="stHorizontalBlock"] {{
    gap: 0.26rem !important;
    align-items: center !important;
    justify-content: flex-end !important;
    width: fit-content !important;
    margin-left: auto !important;
    margin-right: 0 !important;
}}
.st-key-answer_action_row_wrap .st-key-ai_top_wrap,
.st-key-answer_action_row_wrap .st-key-ai_bottom_wrap {{
    width: fit-content !important;
    margin-left: auto !important;
    margin-right: 0 !important;
}}
.st-key-answer_action_row_wrap .st-key-ai_actions_wrap {{
    width: 7.46rem !important;
    display: flex !important;
    justify-content: flex-end !important;
}}
.st-key-answer_action_row_wrap .st-key-ai_actions_wrap [data-testid="stElementContainer"] {{
    width: fit-content !important;
    min-width: 7.46rem !important;
    margin-left: auto !important;
    margin-right: 0 !important;
}}
.st-key-answer_action_row_wrap .st-key-ai_actions_wrap iframe {{
    width: 7.46rem !important;
    max-width: 7.46rem !important;
    display: block !important;
    margin-left: auto !important;
    margin-right: 0 !important;
}}
.st-key-answer_action_row_wrap .st-key-ai_reload_loading_wrap [data-testid="stHorizontalBlock"] {{
    justify-content: flex-end !important;
    gap: 0.26rem !important;
    width: fit-content !important;
    margin-left: auto !important;
    margin-right: 0 !important;
}}
.st-key-answer_action_row_wrap .st-key-ai_reload_loading_wrap [data-testid="stColumn"]:first-child {{
    flex: 0 0 auto !important;
    width: auto !important;
    min-width: 0 !important;
    max-width: none !important;
}}
.st-key-answer_action_row_wrap .st-key-ai_reload_loading_wrap [data-testid="stColumn"]:last-child {{
    flex: 0 0 7.46rem !important;
    width: 7.46rem !important;
    min-width: 7.46rem !important;
    max-width: 7.46rem !important;
}}
.st-key-answer_action_row_wrap .st-key-ai_autoplay_row_wrap [data-testid="stHorizontalBlock"] {{
    justify-content: flex-end !important;
    gap: 0.45rem !important;
    width: fit-content !important;
    margin-left: auto !important;
    margin-right: 0 !important;
}}
.st-key-answer_action_row_wrap .st-key-ai_autoplay_row_wrap [data-testid="stColumn"]:first-child {{
    flex: 0 0 auto !important;
    width: auto !important;
    min-width: 0 !important;
    max-width: none !important;
}}
.st-key-answer_action_row_wrap .st-key-ai_autoplay_row_wrap [data-testid="stColumn"]:last-child {{
    flex: 0 0 7.46rem !important;
    width: 7.46rem !important;
    min-width: 7.46rem !important;
    max-width: 7.46rem !important;
}}
.st-key-answer_action_row_wrap .st-key-ai_top_wrap [data-testid="stColumn"],
.st-key-answer_action_row_wrap .st-key-ai_bottom_wrap [data-testid="stColumn"] {{
    min-width: 0 !important;
}}
.st-key-answer_action_row_wrap .st-key-ai_top_wrap [data-testid="stColumn"],
.st-key-answer_action_row_wrap .st-key-ai_bottom_wrap [data-testid="stColumn"]:first-child,
.st-key-answer_action_row_wrap .st-key-ai_bottom_wrap [data-testid="stColumn"]:last-child {{
    flex: 0 0 3.6rem !important;
    width: 3.6rem !important;
    min-width: 3.6rem !important;
    max-width: 3.6rem !important;
}}
.st-key-answer_action_row_wrap .st-key-ai_single_row_wrap [data-testid="stHorizontalBlock"] {{
    justify-content: flex-end !important;
    gap: 0 !important;
    width: fit-content !important;
    margin-left: auto !important;
    margin-right: 0 !important;
}}
.st-key-answer_action_row_wrap .st-key-ai_single_row_wrap [data-testid="stColumn"] {{
    flex: 0 0 7.46rem !important;
    width: 7.46rem !important;
    min-width: 7.46rem !important;
    max-width: 7.46rem !important;
}}
.st-key-answer_action_row_wrap .st-key-ai_loading_row_wrap [data-testid="stHorizontalBlock"] {{
    justify-content: flex-end !important;
    gap: 0.45rem !important;
    width: fit-content !important;
    margin-left: auto !important;
    margin-right: 0 !important;
}}
.st-key-answer_action_row_wrap .st-key-ai_loading_row_wrap [data-testid="stColumn"]:first-child {{
    flex: 0 0 auto !important;
    width: auto !important;
    min-width: 0 !important;
    max-width: none !important;
}}
.st-key-answer_action_row_wrap .st-key-ai_loading_row_wrap [data-testid="stColumn"]:last-child {{
    flex: 0 0 7.46rem !important;
    width: 7.46rem !important;
    min-width: 7.46rem !important;
    max-width: 7.46rem !important;
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
    padding: 1.05rem 0 0.55rem 0;
    text-align: center;
}}
.story-title-spanish {{
    font-family: 'Fraunces', serif;
    font-size: 2rem;
    font-weight: 800;
    line-height: 1.15;
    color: {t['accent']};
}}
.story-title-english {{
    margin-top: 1rem;
    font-size: 1.1rem;
    font-weight: 500;
    line-height: 1.35;
    color: {t['accent']};
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
.st-key-storytransaudio_story_row_wrap,
.st-key-storytransaudio_dialog_row_wrap,
.st-key-storydisplay_row_wrap {{
    margin: 0 !important;
    width: 100% !important;
}}
.st-key-storyplayback_row_wrap {{
    margin-bottom: 0.02rem !important;
}}
.st-key-storytransaudio_story_row_wrap,
.st-key-storytransaudio_dialog_row_wrap,
.st-key-storydisplay_row_wrap {{
    margin-bottom: 0 !important;
    margin-left: 0 !important;
    width: 100% !important;
}}
.st-key-storytransaudio_story_row_wrap,
.st-key-storytransaudio_dialog_row_wrap {{
    margin-top: -0.14rem !important;
    margin-left: -1.12rem !important;
    width: calc(100% + 1.12rem) !important;
}}
.st-key-storyplayback_row_wrap [data-testid="stHorizontalBlock"],
.st-key-storytransaudio_story_row_wrap [data-testid="stHorizontalBlock"],
.st-key-storytransaudio_dialog_row_wrap [data-testid="stHorizontalBlock"],
.st-key-storydisplay_row_wrap [data-testid="stHorizontalBlock"] {{
    align-items: center !important;
    flex-wrap: nowrap !important;
    justify-content: flex-start !important;
    gap: 0.18rem !important;
    margin: 0 !important;
    width: 100% !important;
}}
.st-key-storyplayback_row_wrap [data-testid="stColumn"],
.st-key-storytransaudio_story_row_wrap [data-testid="stColumn"],
.st-key-storytransaudio_dialog_row_wrap [data-testid="stColumn"],
.st-key-storydisplay_row_wrap [data-testid="stColumn"] {{
    padding: 0 !important;
    flex: 1 1 0 !important;
    min-width: 0 !important;
    display: flex !important;
    justify-content: flex-start !important;
}}
.st-key-storyplayback_row_wrap [data-testid="stColumn"] > div,
.st-key-storytransaudio_story_row_wrap [data-testid="stColumn"] > div,
.st-key-storytransaudio_dialog_row_wrap [data-testid="stColumn"] > div,
.st-key-storydisplay_row_wrap [data-testid="stColumn"] > div {{
    padding: 0 !important;
    width: 100% !important;
    display: flex !important;
    justify-content: flex-start !important;
    align-items: center !important;
}}
.st-key-storyplayback_row_wrap [data-testid="stColumn"]:first-child {{
    flex: 0 0 8.8rem !important;
}}
.st-key-storyplayback_row_wrap [data-testid="stColumn"]:last-child {{
    flex: 1 1 auto !important;
}}
.st-key-answer_action_row_wrap .st-key-ai_autoplay_wrap {{
    width: 7.46rem !important;
    min-width: 7.46rem !important;
    max-width: 7.46rem !important;
    margin: 0.1rem 0 0 auto !important;
}}
.st-key-answer_action_row_wrap .st-key-ai_autoplay_wrap [data-testid="stCheckbox"] {{
    width: 7.46rem !important;
    display: flex !important;
    justify-content: flex-end !important;
    margin: 0 !important;
}}
.st-key-answer_action_row_wrap .st-key-ai_autoplay_wrap [data-testid="stCheckbox"] label {{
    width: fit-content !important;
    margin-left: auto !important;
    display: flex !important;
    align-items: flex-start !important;
    gap: 0.42rem !important;
    transform: translateX(0.14rem) !important;
}}
.st-key-answer_action_row_wrap .st-key-ai_autoplay_wrap [data-testid="stCheckbox"] p {{
    font-size: 0.84rem !important;
    line-height: 1.15 !important;
    color: {t['muted']} !important;
    margin-top: 0.03rem !important;
}}
.st-key-storyplayback_row_wrap .story-option-row {{
    white-space: nowrap !important;
}}
.st-key-storyplayback_row_wrap [data-testid="stCheckbox"],
.st-key-storytransaudio_story_row_wrap [data-testid="stCheckbox"],
.st-key-storytransaudio_dialog_row_wrap [data-testid="stCheckbox"] {{
    margin: 0 !important;
    padding: 0 !important;
    width: 100% !important;
}}
.st-key-storytransaudio_story_row_wrap [data-testid="stCheckbox"],
.st-key-storytransaudio_dialog_row_wrap [data-testid="stCheckbox"] {{
    width: fit-content !important;
}}
.st-key-storyplayback_row_wrap [data-testid="stCheckbox"] label,
.st-key-storytransaudio_story_row_wrap [data-testid="stCheckbox"] label,
.st-key-storytransaudio_dialog_row_wrap [data-testid="stCheckbox"] label {{
    white-space: nowrap !important;
    margin: 0 !important;
    width: 100% !important;
    display: flex !important;
    justify-content: flex-start !important;
}}
.st-key-storytransaudio_story_row_wrap [data-testid="stCheckbox"] label,
.st-key-storytransaudio_dialog_row_wrap [data-testid="stCheckbox"] label {{
    width: fit-content !important;
    margin-right: auto !important;
}}
.st-key-storytransaudio_story_row_wrap [data-testid="stColumn"]:nth-child(2),
.st-key-storytransaudio_dialog_row_wrap [data-testid="stColumn"]:nth-child(2) {{
    margin-left: -1.02rem !important;
}}
.st-key-storyplayback_row_wrap [data-testid="stMarkdownContainer"] p,
.st-key-storytransaudio_story_row_wrap [data-testid="stMarkdownContainer"] p,
.st-key-storytransaudio_dialog_row_wrap [data-testid="stMarkdownContainer"] p,
.st-key-storydisplay_row_wrap [data-testid="stMarkdownContainer"] p {{
    margin: 0 !important;
}}
.st-key-storyplayback_row_wrap [data-testid="stRadio"],
.st-key-storytransaudio_story_row_wrap [data-testid="stRadio"],
.st-key-storytransaudio_dialog_row_wrap [data-testid="stRadio"],
.st-key-storydisplay_row_wrap [data-testid="stRadio"] {{
    margin: 0 !important;
    padding: 0 !important;
}}
.st-key-storyplayback_row_wrap [data-testid="stRadio"] > label,
.st-key-storytransaudio_story_row_wrap [data-testid="stRadio"] > label,
.st-key-storytransaudio_dialog_row_wrap [data-testid="stRadio"] > label,
.st-key-storydisplay_row_wrap [data-testid="stRadio"] > label {{
    display: none !important;
}}
.st-key-storyplayback_row_wrap [data-testid="stRadio"] div[role="radiogroup"],
.st-key-storytransaudio_story_row_wrap [data-testid="stRadio"] div[role="radiogroup"],
.st-key-storytransaudio_dialog_row_wrap [data-testid="stRadio"] div[role="radiogroup"],
.st-key-storydisplay_row_wrap [data-testid="stRadio"] div[role="radiogroup"] {{
    display: flex !important;
    flex-wrap: nowrap !important;
    align-items: center !important;
    justify-content: flex-start !important;
    margin: 0 !important;
    padding: 0 !important;
}}
.st-key-storyplayback_row_wrap [data-testid="stRadio"] div[role="radiogroup"] > label {{
    white-space: nowrap !important;
}}
.st-key-storydisplay_row_wrap [data-testid="stElementContainer"] {{
    margin: 0 !important;
    padding: 0 !important;
}}
.st-key-storydisplay_row_wrap [data-testid="stRadio"] {{
    width: 100% !important;
}}
.st-key-storydisplay_row_wrap [data-testid="stRadio"] div[role="radiogroup"] {{
    gap: 1.36rem !important;
    width: 100% !important;
    justify-content: flex-start !important;
}}
.st-key-storydisplay_row_wrap [data-testid="stRadio"] div[role="radiogroup"] > label {{
    flex: 0 0 calc((100% - 2.72rem) / 3) !important;
    min-width: calc((100% - 2.72rem) / 3) !important;
    width: calc((100% - 2.72rem) / 3) !important;
    display: flex !important;
    justify-content: flex-start !important;
    margin: 0 !important;
}}
.st-key-storydisplay_row_wrap [data-testid="stMarkdownContainer"] p {{
    white-space: nowrap !important;
    font-size: 0.9rem !important;
}}
.st-key-storydisplay_row_wrap {{
    margin-top: -0.18rem !important;
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
    flex: 1 1 0 !important;
    width: auto !important;
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
.dialog-voice-readout {{
    margin: 0.02rem 0 0.45rem 0;
    padding: 0.42rem 0.55rem;
    border-radius: 0.55rem;
    background: color-mix(in srgb, {t['card_bg']} 82%, transparent 18%);
    border: 1px solid color-mix(in srgb, {t['border']} 68%, transparent 32%);
}}
.dialog-voice-readout-label {{
    font-size: 0.62rem;
    font-weight: 600;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: {t['muted']};
    margin-bottom: 0.18rem;
}}
.dialog-voice-readout-line {{
    font-size: 0.78rem;
    line-height: 1.2;
    color: {t['fg']};
    white-space: normal;
    overflow-wrap: anywhere;
}}
.dialog-voice-readout-detected {{
    margin-top: 0.28rem;
    padding-top: 0.28rem;
    border-top: 1px solid color-mix(in srgb, {t['border']} 60%, transparent 40%);
    font-size: 0.72rem;
    line-height: 1.25;
    color: {t['muted']};
    white-space: normal;
    overflow-wrap: anywhere;
}}
.soft-divider {{
    border: none; border-top: 1px solid {t['border']}; margin: 0.6rem 0;
}}

/* ---- Responsive deck picker ---- */
.st-key-{MOBILE_PICKER_CONTAINER_KEY} {{
    display: block;
    border: 1px solid color-mix(in srgb, {t['border']} 78%, transparent 22%) !important;
    border-radius: 0.85rem !important;
    padding: 0.35rem 0.45rem !important;
    box-sizing: border-box !important;
    height: 75vh !important;
    height: 75dvh !important;
    min-height: 75vh !important;
    min-height: 75dvh !important;
    max-height: 75vh !important;
    max-height: 75dvh !important;
    overflow-y: auto !important;
    overflow-x: hidden !important;
    overscroll-behavior: contain !important;
    -webkit-overflow-scrolling: touch !important;
    touch-action: pan-y !important;
}}
.st-key-{MOBILE_PICKER_CONTAINER_KEY} [data-testid="stVerticalBlockBorderWrapper"] {{
    border: none !important;
    box-shadow: none !important;
    background: transparent !important;
    padding: 0 !important;
    height: 100% !important;
    min-height: 0 !important;
    max-height: 100% !important;
    overflow: hidden !important;
}} 
.st-key-{MOBILE_PICKER_CONTAINER_KEY} [data-testid="stVerticalBlock"] {{
    gap: 0 !important;
    height: 100% !important;
    min-height: 0 !important;
    max-height: 100% !important;
    overflow: hidden !important;
}}
.st-key-{MOBILE_PICKER_CONTAINER_KEY} [data-testid="stElementContainer"] {{
    margin: 0 !important;
}}
.mobile-deck-picker-gap {{
    height: 0.86rem;
}}
.deck-category-empty {{
    color: {t['muted']};
    font-size: 0.88rem;
    padding: 0.1rem 0 0.2rem 1.45rem;
}}
.deck-picker-shell {{
    display: flex;
    flex-direction: column;
    gap: 0;
    min-height: 0;
    overflow: visible;
    pointer-events: auto;
}}
.deck-picker-meta {{
    display: flex;
    align-items: flex-end;
    justify-content: space-between;
    gap: 0.75rem;
    margin-top: -0.04rem;
    margin-bottom: 0.62rem;
    font-family: 'DM Sans', sans-serif !important;
}}
.deck-picker-build {{
    color: {t['muted']};
    font-size: 0.72rem;
    line-height: 1.1;
    letter-spacing: 0.03em;
    text-align: right;
    white-space: nowrap;
    font-family: 'DM Sans', sans-serif !important;
}}
.deck-picker-row {{
    display: grid;
    grid-template-columns: 1.45rem minmax(0, 1fr);
    align-items: center;
    column-gap: 0.34rem;
    margin: 0 0 0.14rem 0;
    padding: 0.03rem 0.35rem 0.03rem 0;
    border: none;
    border-radius: 0;
    background: transparent;
    color: {t['fg']} !important;
    text-align: left;
    text-decoration: none !important;
    width: 100%;
    cursor: pointer;
    font: inherit;
    appearance: none;
    -webkit-appearance: none;
    font-family: 'DM Sans', sans-serif !important;
}}
.deck-picker-row:visited,
.deck-picker-row:hover,
.deck-picker-row:focus,
.deck-picker-row:focus-visible,
.deck-picker-row:active {{
    color: {t['fg']} !important;
    text-decoration: none !important;
    outline: none;
}}
[class*="st-key-picker_hidden_toggle_category_"],
[class*="st-key-picker_hidden_toggle_subcategory_"],
[class*="st-key-splash_hidden_action_"],
.st-key-{PICKER_HIDDEN_ACTIONS_WRAP_KEY} {{
    position: absolute !important;
    left: -10000px !important;
    top: auto !important;
    width: 1px !important;
    height: 1px !important;
    overflow: hidden !important;
    opacity: 0 !important;
    pointer-events: none !important;
}}
.deck-picker-row-icon {{
    display: block;
    width: 1.45rem;
    text-align: left;
    white-space: nowrap;
    line-height: 1;
}}
.deck-picker-row-label {{
    min-width: 0;
    margin: 0;
    line-height: 1;
    padding-left: 0.08rem;
    text-align: left;
    font-family: 'DM Sans', sans-serif !important;
}}
.deck-picker-row-category {{
    font-size: 1.2rem;
    font-weight: 400 !important;
    line-height: 1.1;
    min-height: 1.7rem;
    margin-top: 0.9rem;
    margin-bottom: 0.5rem;
}}
.deck-picker-row-subcategory {{
    font-size: 1rem;
    font-weight: 400 !important;
    line-height: 1.05;
    min-height: 1.9rem;
    padding-top: 0.18rem;
    padding-bottom: 0.18rem;
    margin-bottom: 0.16rem;
}}
.deck-picker-row-file,
.deck-picker-row-subcategory-file,
.deck-picker-row-story-child {{
    font-size: 0.88rem;
    line-height: 1;
    font-weight: 400 !important;
    min-height: 1.82rem;
    padding-top: 0.16rem;
    padding-bottom: 0.16rem;
    margin-bottom: 0.16rem;
}}
.deck-picker-row-file {{
}}
.deck-picker-row-subcategory-file {{
}}
.deck-picker-row-story-child {{
}}
.deck-picker-row-folder-depth-0 {{
    padding-left: 2rem;
}}
.deck-picker-row-folder-depth-1 {{
    padding-left: 2rem;
}}
.deck-picker-row-folder-depth-2 {{
    padding-left: 3.15rem;
}}
.deck-picker-row-folder-depth-3 {{
    padding-left: 4.3rem;
}}
.deck-picker-row-folder-depth-4 {{
    padding-left: 5.45rem;
}}
.deck-picker-row-folder-depth-5 {{
    padding-left: 6.6rem;
}}
.deck-picker-row-file-depth-0 {{
    padding-left: 1.45rem;
}}
.deck-picker-row-file-depth-1 {{
    padding-left: 3.3rem;
}}
.deck-picker-row-file-depth-2 {{
    padding-left: 4.45rem;
}}
.deck-picker-row-file-depth-3 {{
    padding-left: 5.6rem;
}}
.deck-picker-row-file-depth-4 {{
    padding-left: 6.75rem;
}}
.deck-picker-row-file-depth-5 {{
    padding-left: 7.9rem;
}}
.deck-picker-row-story-child-depth-0 {{
    padding-left: 2.55rem;
}}
.deck-picker-row-story-child-depth-1 {{
    padding-left: 4.4rem;
}}
.deck-picker-row-story-child-depth-2 {{
    padding-left: 5.55rem;
}}
.deck-picker-row-story-child-depth-3 {{
    padding-left: 6.7rem;
}}
.deck-picker-row-story-child-depth-4 {{
    padding-left: 7.85rem;
}}
.deck-picker-row-story-child-depth-5 {{
    padding-left: 9rem;
}}
.deck-picker-row-special {{
    font-size: 0.88rem;
    line-height: 1;
    min-height: 1.42rem;
}}
.deck-picker-status-untouched .deck-picker-row-icon {{
    color: #8d98a3;
}}
.deck-picker-status-in_progress .deck-picker-row-icon,
.deck-picker-status-review .deck-picker-row-icon {{
    color: #f2c94c;
}}
.deck-picker-status-complete .deck-picker-row-icon {{
    color: {t['accent']};
    font-weight: 700;
}}
.deck-picker-status-story .deck-picker-row-icon,
.deck-picker-status-dialog .deck-picker-row-icon,
.deck-picker-status-favorites .deck-picker-row-icon,
.deck-picker-status-challenge .deck-picker-row-icon {{
    color: inherit;
}}
@media (max-width: 767px) {{
    .st-key-icon_btn_row_wrap .st-key-action_right_group_wrap .st-key-speaker_wrap iframe {{
        margin-top: 0.34rem !important;
    }}
    .st-key-answer_action_row_desktop_wrap {{
        display: none !important;
    }}
    .st-key-answer_action_row_phone_wrap {{
        display: block !important;
        margin-top: 0.04rem !important;
    }}
    .st-key-answer_action_row_phone_wrap [data-testid="stVerticalBlock"] {{
        gap: 0.16rem !important;
    }}
    .st-key-answer_action_row_phone_wrap [data-testid="stElementContainer"] {{
        margin: 0 !important;
    }}
    .st-key-answer_action_row_phone_wrap div[data-testid="stButton"] > button {{
        width: 3.6rem !important;
        min-width: 3.6rem !important;
        max-width: 3.6rem !important;
        min-height: 3.2rem !important;
        font-size: 1.55rem !important;
        font-weight: 700 !important;
    }}
    .st-key-answer_action_row_phone_wrap div[data-testid="stButton"] > button [data-testid="stMarkdownContainer"],
    .st-key-answer_action_row_phone_wrap div[data-testid="stButton"] > button [data-testid="stMarkdownContainer"] p,
    .st-key-answer_action_row_phone_wrap div[data-testid="stButton"] > button [data-testid="stMarkdownContainer"] span,
    .st-key-answer_action_row_phone_wrap div[data-testid="stButton"] > button [data-testid="stMarkdownContainer"] div {{
        font-size: 1.55rem !important;
        font-weight: 700 !important;
        line-height: 1 !important;
    }}
    .st-key-correct_phone_wrap div[data-testid="stButton"] > button {{
        background-color: {BUTTON_COLORS['green']['bg']} !important;
        border-color: {BUTTON_COLORS['green']['border']} !important;
        color: {BUTTON_COLORS['green']['fg']} !important;
    }}
    .st-key-repeat_phone_wrap div[data-testid="stButton"] > button {{
        background-color: {BUTTON_COLORS['yellow']['bg']} !important;
        border-color: {BUTTON_COLORS['yellow']['border']} !important;
        color: {BUTTON_COLORS['yellow']['fg']} !important;
    }}
    .st-key-nextunscored_phone_wrap div[data-testid="stButton"] > button {{
        background-color: #beb0f1 !important;
        border-color: #6940c6 !important;
        color: #49258b !important;
    }}
    .st-key-favorite_phone_wrap div[data-testid="stButton"] > button {{
        background-color: {t['info_light']} !important;
        border-color: {t['info']} !important;
        color: #1f7cff !important;
    }}
    .st-key-autospeak_on_phone_wrap div[data-testid="stButton"] > button {{
        background-color: #ffe0f5 !important;
        border-color: #ff1aaa !important;
        color: #ff1aaa !important;
    }}
    .st-key-autospeak_off_phone_wrap div[data-testid="stButton"] > button {{
        background-color: rgba(128,128,128,0.12) !important;
        border-color: rgba(128,128,128,0.35) !important;
        color: rgba(140,140,140,0.8) !important;
    }}
    .st-key-autospeak_on_phone_wrap div[data-testid="stButton"] > button,
    .st-key-autospeak_off_phone_wrap div[data-testid="stButton"] > button {{
        font-size: 0.65rem !important;
        font-weight: 700 !important;
        letter-spacing: 0.06em !important;
        line-height: 1.3 !important;
        justify-content: center !important;
        text-align: center !important;
        padding-left: 0 !important;
        padding-right: 0 !important;
    }}
    .st-key-autospeak_on_phone_wrap div[data-testid="stButton"] > button [data-testid="stMarkdownContainer"],
    .st-key-autospeak_on_phone_wrap div[data-testid="stButton"] > button [data-testid="stMarkdownContainer"] p,
    .st-key-autospeak_on_phone_wrap div[data-testid="stButton"] > button [data-testid="stMarkdownContainer"] span,
    .st-key-autospeak_on_phone_wrap div[data-testid="stButton"] > button [data-testid="stMarkdownContainer"] div,
    .st-key-autospeak_off_phone_wrap div[data-testid="stButton"] > button [data-testid="stMarkdownContainer"],
    .st-key-autospeak_off_phone_wrap div[data-testid="stButton"] > button [data-testid="stMarkdownContainer"] p,
    .st-key-autospeak_off_phone_wrap div[data-testid="stButton"] > button [data-testid="stMarkdownContainer"] span,
    .st-key-autospeak_off_phone_wrap div[data-testid="stButton"] > button [data-testid="stMarkdownContainer"] div {{
        font-size: 0.65rem !important;
        font-weight: 700 !important;
        line-height: 1.3 !important;
        width: 100% !important;
        text-align: center !important;
    }}
    .st-key-action_phone_top_row_wrap [data-testid="stHorizontalBlock"] {{
        display: flex !important;
        flex-wrap: nowrap !important;
        justify-content: flex-start !important;
        gap: 0.26rem !important;
        width: fit-content !important;
        margin: 0 !important;
    }}
    .st-key-action_phone_top_row_wrap [data-testid="stColumn"] {{
        flex: 0 0 3.6rem !important;
        width: 3.6rem !important;
        min-width: 3.6rem !important;
        max-width: 3.6rem !important;
        padding: 0 !important;
    }}
    .st-key-action_phone_bottom_single_row_wrap [data-testid="stHorizontalBlock"],
    .st-key-action_phone_bottom_loading_row_wrap [data-testid="stHorizontalBlock"],
    .st-key-action_phone_bottom_actions_row_wrap [data-testid="stHorizontalBlock"] {{
        display: flex !important;
        flex-wrap: nowrap !important;
        align-items: stretch !important;
        justify-content: flex-start !important;
        gap: 0.26rem !important;
        width: 100% !important;
        margin: 0 !important;
    }}
    .st-key-action_phone_bottom_single_row_wrap,
    .st-key-action_phone_bottom_loading_row_wrap,
    .st-key-action_phone_bottom_actions_row_wrap {{
        margin-top: 0.16rem !important;
    }}
    .st-key-action_phone_bottom_actions_row_wrap .st-key-autospeak_on_phone_wrap div[data-testid="stButton"] > button,
    .st-key-action_phone_bottom_actions_row_wrap .st-key-autospeak_off_phone_wrap div[data-testid="stButton"] > button {{
        font-size: 0.65rem !important;
    }}
    .st-key-action_phone_bottom_actions_row_wrap .st-key-autospeak_on_phone_wrap div[data-testid="stButton"] > button [data-testid="stMarkdownContainer"],
    .st-key-action_phone_bottom_actions_row_wrap .st-key-autospeak_on_phone_wrap div[data-testid="stButton"] > button [data-testid="stMarkdownContainer"] p,
    .st-key-action_phone_bottom_actions_row_wrap .st-key-autospeak_on_phone_wrap div[data-testid="stButton"] > button [data-testid="stMarkdownContainer"] span,
    .st-key-action_phone_bottom_actions_row_wrap .st-key-autospeak_on_phone_wrap div[data-testid="stButton"] > button [data-testid="stMarkdownContainer"] div,
    .st-key-action_phone_bottom_actions_row_wrap .st-key-autospeak_off_phone_wrap div[data-testid="stButton"] > button [data-testid="stMarkdownContainer"],
    .st-key-action_phone_bottom_actions_row_wrap .st-key-autospeak_off_phone_wrap div[data-testid="stButton"] > button [data-testid="stMarkdownContainer"] p,
    .st-key-action_phone_bottom_actions_row_wrap .st-key-autospeak_off_phone_wrap div[data-testid="stButton"] > button [data-testid="stMarkdownContainer"] span,
    .st-key-action_phone_bottom_actions_row_wrap .st-key-autospeak_off_phone_wrap div[data-testid="stButton"] > button [data-testid="stMarkdownContainer"] div {{
        font-size: 0.65rem !important;
    }}
    .st-key-action_phone_checkbox_row_wrap {{
        margin-top: 0.08rem !important;
    }}
    .st-key-action_phone_checkbox_row_wrap [data-testid="stCheckbox"] {{
        margin: 0 !important;
    }}
    .st-key-action_phone_bottom_single_row_wrap [data-testid="stColumn"]:nth-child(1),
    .st-key-action_phone_bottom_single_row_wrap [data-testid="stColumn"]:nth-child(2),
    .st-key-action_phone_bottom_loading_row_wrap [data-testid="stColumn"]:nth-child(1),
    .st-key-action_phone_bottom_loading_row_wrap [data-testid="stColumn"]:nth-child(2),
    .st-key-action_phone_bottom_actions_row_wrap [data-testid="stColumn"]:nth-child(1),
    .st-key-action_phone_bottom_actions_row_wrap [data-testid="stColumn"]:nth-child(2) {{
        flex: 0 0 3.6rem !important;
        width: 3.6rem !important;
        min-width: 3.6rem !important;
        max-width: 3.6rem !important;
        padding: 0 !important;
    }}
    .st-key-action_phone_bottom_single_row_wrap [data-testid="stColumn"]:nth-child(3),
    .st-key-action_phone_bottom_loading_row_wrap [data-testid="stColumn"]:nth-child(3),
    .st-key-action_phone_bottom_actions_row_wrap [data-testid="stColumn"]:nth-child(3) {{
        flex: 0 0 7.46rem !important;
        width: 7.46rem !important;
        min-width: 7.46rem !important;
        max-width: 7.46rem !important;
        padding: 0 !important;
    }}
    .st-key-action_phone_bottom_loading_row_wrap [data-testid="stColumn"]:nth-child(4),
    .st-key-action_phone_bottom_actions_row_wrap [data-testid="stColumn"]:nth-child(4) {{
        flex: 1 1 auto !important;
        min-width: 0 !important;
        padding: 0 !important;
    }}
    .st-key-action_phone_bottom_actions_row_wrap [data-testid="stColumn"] {{
        align-self: stretch !important;
    }}
    .st-key-answer_action_row_phone_wrap .st-key-speaker_phone_wrap,
    .st-key-answer_action_row_phone_wrap .st-key-speaker_phone_wrap > div,
    .st-key-answer_action_row_phone_wrap .st-key-speaker_phone_wrap [data-testid="stElementContainer"] {{
        width: 3.6rem !important;
        min-width: 3.6rem !important;
        max-width: 3.6rem !important;
    }}
    .st-key-answer_action_row_phone_wrap .st-key-speaker_phone_wrap iframe {{
        width: 3.6rem !important;
        min-width: 3.6rem !important;
        max-width: 3.6rem !important;
        height: 3.2rem !important;
        min-height: 3.2rem !important;
        margin: 0 !important;
        display: block !important;
    }}
    .st-key-answer_action_row_phone_wrap .st-key-autoplay_btn_phone_wrap,
    .st-key-answer_action_row_phone_wrap .st-key-autoplay_btn_phone_wrap > div,
    .st-key-answer_action_row_phone_wrap .st-key-autoplay_btn_phone_wrap [data-testid="stElementContainer"] {{
        width: 3.6rem !important;
        min-width: 3.6rem !important;
        max-width: 3.6rem !important;
    }}
    .st-key-answer_action_row_phone_wrap .st-key-autoplay_btn_phone_wrap iframe {{
        width: 3.6rem !important;
        min-width: 3.6rem !important;
        max-width: 3.6rem !important;
        height: 3.2rem !important;
        min-height: 3.2rem !important;
        margin: 0 !important;
        display: block !important;
    }}
    .st-key-action_phone_bottom_single_row_wrap .st-key-speaker_phone_wrap iframe {{
        margin-top: 0.1rem !important;
    }}
    .st-key-action_phone_bottom_actions_row_wrap .st-key-speaker_phone_wrap iframe,
    .st-key-action_phone_bottom_actions_row_wrap .st-key-phone_ai_actions_wrap iframe {{
        margin-top: 0 !important;
    }}
    .st-key-phone_ai_single_wrap div[data-testid="stButton"] > button {{
        width: 7.46rem !important;
        min-width: 7.46rem !important;
        max-width: 7.46rem !important;
        min-height: 3.2rem !important;
        font-size: 0.82rem !important;
        background: {BUTTON_COLORS['blue']['bg']} !important;
        border-color: {BUTTON_COLORS['blue']['border']} !important;
        color: {BUTTON_COLORS['blue']['fg']} !important;
    }}
    .st-key-phone_ai_single_wrap div[data-testid="stButton"] > button [data-testid="stMarkdownContainer"],
    .st-key-phone_ai_single_wrap div[data-testid="stButton"] > button [data-testid="stMarkdownContainer"] p,
    .st-key-phone_ai_single_wrap div[data-testid="stButton"] > button [data-testid="stMarkdownContainer"] span,
    .st-key-phone_ai_single_wrap div[data-testid="stButton"] > button [data-testid="stMarkdownContainer"] div {{
        font-size: 0.82rem !important;
        font-weight: 600 !important;
        letter-spacing: 0.08em !important;
        text-transform: uppercase !important;
        line-height: 1 !important;
    }}
    .st-key-phone_ai_fetch_status_row_wrap [data-testid="stHorizontalBlock"],
    .st-key-phone_ai_actions_row_wrap [data-testid="stHorizontalBlock"] {{
        display: flex !important;
        flex-wrap: nowrap !important;
        align-items: center !important;
        justify-content: flex-start !important;
        gap: 0.35rem !important;
        width: 100% !important;
        margin: 0 !important;
    }}
    .st-key-phone_ai_fetch_status_row_wrap [data-testid="stColumn"]:first-child,
    .st-key-phone_ai_actions_row_wrap [data-testid="stColumn"]:first-child {{
        flex: 0 0 5.96rem !important;
        width: 5.96rem !important;
        min-width: 5.96rem !important;
        max-width: 5.96rem !important;
        padding: 0 !important;
    }}
    .st-key-phone_ai_fetch_status_row_wrap [data-testid="stColumn"]:last-child,
    .st-key-phone_ai_actions_row_wrap [data-testid="stColumn"]:last-child {{
        flex: 1 1 auto !important;
        min-width: 0 !important;
        padding: 0 !important;
    }}
    .st-key-phone_ai_actions_wrap,
    .st-key-phone_ai_actions_wrap [data-testid="stElementContainer"],
    .st-key-phone_ai_actions_wrap iframe {{
        width: 7.46rem !important;
        min-width: 7.46rem !important;
        max-width: 7.46rem !important;
    }}
    .st-key-phone_ai_actions_wrap iframe {{
        height: 3.2rem !important;
        min-height: 3.2rem !important;
        display: block !important;
        margin-top: 0 !important;
    }}
    .st-key-phone_ai_status_wrap .ai-status-label {{
        font-size: 0.82rem !important;
        font-weight: 600 !important;
        letter-spacing: 0.06em !important;
        text-transform: uppercase !important;
        color: {t['muted']} !important;
        white-space: nowrap !important;
        line-height: 1 !important;
        margin: 0 !important;
    }}
    .st-key-phone_ai_checkbox_wrap [data-testid="stCheckbox"] {{
        margin: 0 !important;
    }}
    .st-key-phone_ai_checkbox_wrap [data-testid="stCheckbox"] label {{
        display: flex !important;
        align-items: center !important;
        gap: 0.03rem !important;
        white-space: nowrap !important;
    }}
    .st-key-phone_ai_checkbox_wrap [data-testid="stCheckbox"] label > div:first-child {{
        transform: scale(1.3) translateY(0.06rem) !important;
        transform-origin: left center !important;
    }}
    .st-key-phone_ai_checkbox_wrap [data-testid="stCheckbox"] label > div:last-child {{
        margin-left: -0.06rem !important;
    }}
    .st-key-phone_ai_checkbox_wrap [data-testid="stCheckbox"] p {{
        font-size: 1.08rem !important;
        line-height: 1 !important;
        white-space: nowrap !important;
        margin-top: 0.18rem !important;
    }}
    .title-row {{
        padding: 0.15rem 0 0.08rem 0 !important;
    }}
    .deck-picker-meta {{
        flex-direction: column;
        align-items: flex-start;
        gap: 0.18rem;
        margin-bottom: 0.62rem;
    }}
    .deck-picker-build {{
        font-size: 0.68rem;
        text-align: left;
        white-space: normal;
        word-break: break-word;
    }}
    .deck-picker-row {{
        grid-template-columns: 1.42rem minmax(0, 1fr);
        column-gap: 0.22rem;
        padding-right: 0.35rem;
    }}
    .deck-picker-row-icon {{
        width: 1.42rem;
    }}
    .deck-picker-row-label {{
        padding-left: 0.02rem;
    }}
    .deck-picker-row-special {{
        min-height: 1.75rem;
        padding: 0.05rem 0.45rem 0.05rem 0;
        font-size: 0.86rem;
    }}
    .deck-picker-row-category {{
        font-size: 1.24rem;
        font-weight: 400;
        min-height: 1.7rem;
        padding-top: 0.08rem;
        padding-bottom: 0.08rem;
        margin-top: 0.92rem;
        margin-bottom: 0.52rem;
    }}
    .deck-picker-row-subcategory {{
        font-weight: 400;
        min-height: 1.92rem;
        padding-top: 0.18rem;
        padding-bottom: 0.18rem;
        margin-bottom: 0.16rem;
    }}
    .deck-picker-row-file,
    .deck-picker-row-subcategory-file,
    .deck-picker-row-story-child {{
        font-size: 0.84rem;
        font-weight: 400;
        min-height: 1.7rem;
        padding-top: 0.18rem;
        padding-bottom: 0.18rem;
        margin-bottom: 0.18rem;
    }}
    .deck-picker-row-file {{
    }}
    .deck-picker-row-subcategory-file {{
    }}
    .deck-picker-row-story-child {{
    }}
    .deck-picker-row-folder-depth-0 {{
        padding-left: 1.85rem;
    }}
    .deck-picker-row-folder-depth-1 {{
        padding-left: 1.85rem;
    }}
    .deck-picker-row-folder-depth-2 {{
        padding-left: 2.9rem;
    }}
    .deck-picker-row-folder-depth-3 {{
        padding-left: 3.95rem;
    }}
    .deck-picker-row-folder-depth-4 {{
        padding-left: 5rem;
    }}
    .deck-picker-row-folder-depth-5 {{
        padding-left: 6.05rem;
    }}
    .deck-picker-row-file-depth-0 {{
        padding-left: 1.55rem;
    }}
    .deck-picker-row-file-depth-1 {{
        padding-left: 3.1rem;
    }}
    .deck-picker-row-file-depth-2 {{
        padding-left: 4.15rem;
    }}
    .deck-picker-row-file-depth-3 {{
        padding-left: 5.2rem;
    }}
    .deck-picker-row-file-depth-4 {{
        padding-left: 6.25rem;
    }}
    .deck-picker-row-file-depth-5 {{
        padding-left: 7.3rem;
    }}
    .deck-picker-row-story-child-depth-0 {{
        padding-left: 2.45rem;
    }}
    .deck-picker-row-story-child-depth-1 {{
        padding-left: 4.4rem;
    }}
    .deck-picker-row-story-child-depth-2 {{
        padding-left: 5.45rem;
    }}
    .deck-picker-row-story-child-depth-3 {{
        padding-left: 6.5rem;
    }}
    .deck-picker-row-story-child-depth-4 {{
        padding-left: 7.55rem;
    }}
    .deck-picker-row-story-child-depth-5 {{
        padding-left: 8.6rem;
    }}
    .title-main {{
        line-height: 0.96 !important;
    }}
    .title-sub {{
        margin-top: 0.08rem !important;
        margin-bottom: 0.72rem !important;
    }}
    .st-key-person_radio_wrap {{
        margin-top: -0.08rem !important;
        margin-bottom: 0.12rem !important;
    }}
    .st-key-person_radio_wrap [data-testid="stRadio"] {{
        margin: 0 !important;
        padding: 0 !important;
    }}
    .st-key-person_radio_wrap [data-testid="stWidgetLabel"] p {{
        font-size: 0.92rem !important;
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
    .mobile-deck-picker-label {{
        display: block !important;
        margin-top: -0.04rem !important;
        margin-bottom: 0 !important;
    }}
    .mobile-deck-picker-gap {{
        height: 0.62rem !important;
    }}
    .st-key-{MOBILE_PICKER_CONTAINER_KEY} {{
        padding: 0.18rem 0.2rem !important;
        margin-top: -0.35rem !important;
        border: 1px solid color-mix(in srgb, {t['border']} 78%, transparent 22%) !important;
        box-shadow: none !important;
        background: transparent !important;
        border-radius: 0.85rem !important;
        height: 75vh !important;
        height: 75dvh !important;
        min-height: 75vh !important;
        min-height: 75dvh !important;
        max-height: 75vh !important;
        max-height: 75dvh !important;
        overflow-y: auto !important;
        overflow-x: hidden !important;
        overscroll-behavior: contain !important;
        -webkit-overflow-scrolling: touch !important;
        touch-action: pan-y !important;
    }}
    .st-key-{MOBILE_PICKER_CONTAINER_KEY} [data-testid="stVerticalBlockBorderWrapper"] {{
        border: none !important;
        box-shadow: none !important;
        background: transparent !important;
        padding: 0 !important;
        height: 100% !important;
        min-height: 0 !important;
        max-height: 100% !important;
        overflow: hidden !important;
    }}
    .st-key-{MOBILE_PICKER_CONTAINER_KEY} [data-testid="stVerticalBlock"] {{
        height: 100% !important;
        min-height: 0 !important;
        max-height: 100% !important;
        overflow: hidden !important;
    }}
    .st-key-{MOBILE_PICKER_CONTAINER_KEY} [data-testid="stVerticalBlock"] > * {{
        margin-bottom: 0 !important;
    }}

    /* ---- Phone: Story option rows ---- */
    .st-key-storytransaudio_story_row_wrap,
    .st-key-storytransaudio_dialog_row_wrap,
    .st-key-storydisplay_row_wrap {{
        height: auto !important;
        overflow: visible !important;
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
        flex: 0 0 auto !important;
        min-width: fit-content !important;
    }}
    .st-key-storyplayback_row_wrap [data-testid="stColumn"]:nth-child(3) {{
        flex: 0 0 auto !important;
        min-width: fit-content !important;
        margin-left: 0.45rem !important;
    }}
    .st-key-storyplayback_row_wrap .story-option-row {{
        font-size: 0.9rem !important;
        position: relative !important;
        top: -0.28rem !important;
        white-space: nowrap !important;
    }}
    .st-key-storyplayback_row_wrap [data-testid="stCheckbox"] label p,
    .st-key-storytransaudio_story_row_wrap [data-testid="stCheckbox"] label p,
    .st-key-storytransaudio_dialog_row_wrap [data-testid="stCheckbox"] label p,
    .st-key-storydisplay_row_wrap [data-testid="stRadio"] label p {{
        font-size: 0.92rem !important;
    }}
    .st-key-storyplayback_row_wrap [data-testid="stCheckbox"] label {{
        width: fit-content !important;
    }}
    .st-key-storytransaudio_story_row_wrap [data-testid="stCheckbox"] label,
    .st-key-storytransaudio_dialog_row_wrap [data-testid="stCheckbox"] label {{
        width: fit-content !important;
        display: flex !important;
        justify-content: flex-start !important;
        margin-right: auto !important;
    }}
    .st-key-storytransaudio_story_row_wrap [data-testid="stCheckbox"],
    .st-key-storytransaudio_dialog_row_wrap [data-testid="stCheckbox"] {{
        width: fit-content !important;
    }}
    .st-key-storytransaudio_story_row_wrap [data-testid="stColumn"]:first-child [data-testid="stCheckbox"],
    .st-key-storytransaudio_dialog_row_wrap [data-testid="stColumn"]:first-child [data-testid="stCheckbox"] {{
        margin-left: -0.48rem !important;
    }}

    .st-key-storytransaudio_story_row_wrap [data-testid="stHorizontalBlock"],
    .st-key-storytransaudio_dialog_row_wrap [data-testid="stHorizontalBlock"],
    .st-key-storydisplay_row_wrap [data-testid="stHorizontalBlock"] {{
        display: flex !important;
        flex-wrap: nowrap !important;
        justify-content: flex-start !important;
        gap: 0.18rem !important;
        align-items: center !important;
        height: auto !important;
        width: 100% !important;
    }}
    .st-key-storytransaudio_story_row_wrap [data-testid="stColumn"] {{
        flex: 0 0 calc((100% - 0.36rem) / 3) !important;
        min-width: calc((100% - 0.36rem) / 3) !important;
        width: calc((100% - 0.36rem) / 3) !important;
    }}
    .st-key-storytransaudio_dialog_row_wrap [data-testid="stColumn"] {{
        flex: 0 0 calc((100% - 0.36rem) / 3) !important;
        min-width: calc((100% - 0.36rem) / 3) !important;
        width: calc((100% - 0.36rem) / 3) !important;
    }}
    .st-key-storydisplay_row_wrap [data-testid="stColumn"] {{
        flex: 0 0 calc((100% - 0.36rem) / 3) !important;
        min-width: calc((100% - 0.36rem) / 3) !important;
        width: calc((100% - 0.36rem) / 3) !important;
    }}
    .st-key-storytransaudio_story_row_wrap [data-testid="stColumn"] > div,
    .st-key-storytransaudio_dialog_row_wrap [data-testid="stColumn"] > div,
    .st-key-storydisplay_row_wrap [data-testid="stColumn"] > div {{
        display: flex !important;
        align-items: center !important;
        justify-content: flex-start !important;
        width: 100% !important;
    }}
    .st-key-storytransaudio_story_row_wrap div[data-testid="stButton"] > button,
    .st-key-storytransaudio_dialog_row_wrap div[data-testid="stButton"] > button,
    .st-key-storydisplay_row_wrap div[data-testid="stButton"] > button {{
        width: 100% !important;
        min-height: 1.06rem !important;
        padding: 0.02rem 0.24rem !important;
        font-size: 0.64rem !important;
        line-height: 1 !important;
    }}
    .st-key-storytransaudio_story_row_wrap .story-option-row,
    .st-key-storytransaudio_dialog_row_wrap .story-option-row {{
        position: relative !important;
        top: -0.45rem !important;
    }}
    .st-key-storydisplay_row_wrap [data-testid="stElementContainer"],
    .st-key-storydisplay_row_wrap [data-testid="stRadio"] {{
        margin: 0 !important;
        padding: 0 !important;
    }}
    .st-key-storydisplay_row_wrap [data-testid="stRadio"] {{
        width: 100% !important;
    }}
    .st-key-storydisplay_row_wrap [data-testid="stRadio"] div[role="radiogroup"] {{
        display: flex !important;
        flex-wrap: nowrap !important;
        justify-content: flex-start !important;
        align-items: center !important;
        gap: 1.08rem !important;
        margin: 0 !important;
        padding: 0 !important;
        width: 100% !important;
    }}
    .st-key-storydisplay_row_wrap [data-testid="stRadio"] div[role="radiogroup"] > label {{
        flex: 0 0 calc((100% - 2.16rem) / 3) !important;
        min-width: calc((100% - 2.16rem) / 3) !important;
        width: calc((100% - 2.16rem) / 3) !important;
        display: flex !important;
        justify-content: flex-start !important;
        margin: 0 !important;
    }}
    .st-key-storydisplay_row_wrap [data-testid="stMarkdownContainer"] p {{
        white-space: nowrap !important;
        font-size: 0.76rem !important;
    }}
    .st-key-storydisplay_row_wrap {{
        margin-top: -0.18rem !important;
    }}
    .st-key-storyplayback_row_wrap {{
        margin-bottom: 0 !important;
    }}
    .st-key-storytransaudio_story_row_wrap,
    .st-key-storytransaudio_dialog_row_wrap,
    .st-key-storydisplay_row_wrap {{
        margin-bottom: 0 !important;
        margin-left: 0 !important;
        width: 100% !important;
    }}
    .st-key-storytransaudio_story_row_wrap,
    .st-key-storytransaudio_dialog_row_wrap {{
        margin-top: -0.16rem !important;
        margin-left: -1.32rem !important;
        width: calc(100% + 1.32rem) !important;
    }}
    .st-key-storytransaudio_story_row_wrap [data-testid="stColumn"]:nth-child(2),
    .st-key-storytransaudio_dialog_row_wrap [data-testid="stColumn"]:nth-child(2) {{
        margin-left: -1.22rem !important;
    }}
    .st-key-regular_auto_controls_wrap [data-testid="stHorizontalBlock"] {{
        gap: 0.2rem !important;
    }}
    .st-key-regular_auto_controls_wrap [data-testid="stCheckbox"] label p {{
        font-size: 0.92rem !important;
    }}
    .st-key-regular_auto_controls_wrap [data-testid="stColumn"] {{
        flex: 1 1 0 !important;
    }}
}}
    /* --- GLOBAL BUTTON LEFT ALIGNMENT OVERRIDE (added for cross-browser consistency, 2026-04-21) --- */
    button, [data-testid="stButton"] > button, .stButton > button {{
        text-align: left !important;
        justify-content: flex-start !important;
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


def render_mobile_deck_picker_height_fix(scroll_target=None):
    script = """
        <script>
        (function() {
            var parentWindow = window.parent;
            var doc = parentWindow.document;
            var resizeTimer = null;
            var pendingScrollTarget = __SCROLL_TARGET__;
            var scrollApplied = false;

            function viewportHeight() {
                if (parentWindow.visualViewport && parentWindow.visualViewport.height) {
                    return parentWindow.visualViewport.height;
                }
                return parentWindow.innerHeight || doc.documentElement.clientHeight || 0;
            }

            function px(value) {
                var parsed = parseFloat(value || '0');
                return Number.isFinite(parsed) ? parsed : 0;
            }

            function elementForScrollTarget(container, value) {
                if (!value) {
                    return null;
                }
                var escapedValue = value.replace(/\\/g, '\\\\').replace(/"/g, '\\"');
                return container.querySelector('[data-picker-anchor="' + escapedValue + '"]');
            }

            function scrollTargetIntoView(container) {
                if (scrollApplied || !pendingScrollTarget) {
                    return;
                }
                var anchor = elementForScrollTarget(container, pendingScrollTarget);
                if (!anchor) {
                    scrollApplied = true;
                    return;
                }
                var targetRect = container.getBoundingClientRect();
                var anchorRect = anchor.getBoundingClientRect();
                var nextScrollTop = container.scrollTop + (anchorRect.top - targetRect.top) - 6;
                container.scrollTop = Math.max(0, nextScrollTop);
                scrollApplied = true;
            }

            function attachTouchScroll(container) {
                if (!container || container.dataset.touchScrollAttached === '1') {
                    return;
                }

                container.dataset.touchScrollAttached = '1';

                var startY = 0;
                var startScrollTop = 0;
                var tracking = false;

                container.addEventListener('touchstart', function(event) {
                    if (!event.touches || event.touches.length !== 1) {
                        tracking = false;
                        return;
                    }
                    tracking = true;
                    startY = event.touches[0].clientY;
                    startScrollTop = container.scrollTop;
                }, { passive: true });

                container.addEventListener('touchmove', function(event) {
                    if (!tracking || !event.touches || event.touches.length !== 1) {
                        return;
                    }

                    if (container.scrollHeight <= container.clientHeight + 1) {
                        return;
                    }

                    var currentY = event.touches[0].clientY;
                    var deltaY = currentY - startY;
                    var maxScrollTop = Math.max(container.scrollHeight - container.clientHeight, 0);
                    var nextScrollTop = Math.max(0, Math.min(maxScrollTop, startScrollTop - deltaY));

                    if (nextScrollTop !== container.scrollTop) {
                        container.scrollTop = nextScrollTop;
                        event.preventDefault();
                    }
                }, { passive: false });

                function stopTracking() {
                    tracking = false;
                }

                container.addEventListener('touchend', stopTracking, { passive: true });
                container.addEventListener('touchcancel', stopTracking, { passive: true });
            }

            function applyHeight() {
                var wrap = doc.querySelector('.st-key-{MOBILE_PICKER_CONTAINER_KEY}');
                if (!wrap) {
                    return false;
                }
                var shell = wrap.querySelector('.deck-picker-shell');
                if (!shell) {
                    return false;
                }

                var wrapRect = wrap.getBoundingClientRect();
                var viewport = viewportHeight();
                var bottomGap = 36;
                var availableHeight = Math.floor(viewport - wrapRect.top - bottomGap);
                var desiredHeight = Math.floor(viewport * 0.75);
                var resolvedHeight = Math.max(Math.min(desiredHeight, availableHeight), 1);
                var targetHeight = resolvedHeight + 'px';
                var wrapStyle = parentWindow.getComputedStyle(wrap);
                var shellHeight = Math.max(
                    wrap.clientHeight - px(wrapStyle.paddingTop) - px(wrapStyle.paddingBottom),
                    1
                ) + 'px';

                wrap.style.height = targetHeight;
                wrap.style.maxHeight = targetHeight;
                wrap.style.minHeight = targetHeight;
                wrap.style.boxSizing = 'border-box';
                wrap.style.overflowY = 'auto';
                wrap.style.overflowX = 'hidden';
                wrap.style.webkitOverflowScrolling = 'touch';
                wrap.style.touchAction = 'pan-y';

                shell.style.height = 'auto';
                shell.style.maxHeight = 'none';
                shell.style.minHeight = '0';
                shell.style.overflow = 'visible';
                shell.style.marginTop = '0';
                attachTouchScroll(wrap);

                scrollTargetIntoView(wrap);
                return true;
            }

            function scheduleApplyHeight() {
                if (resizeTimer) {
                    parentWindow.clearTimeout(resizeTimer);
                }
                resizeTimer = parentWindow.setTimeout(function() {
                    applyHeight();
                }, 60);
            }

            if (applyHeight()) {
                parentWindow.addEventListener('resize', scheduleApplyHeight);
                if (parentWindow.visualViewport) {
                    parentWindow.visualViewport.addEventListener('resize', scheduleApplyHeight);
                }
                return;
            }

            var attempts = 0;
            var timer = parentWindow.setInterval(function() {
                attempts += 1;
                if (applyHeight() || attempts >= 20) {
                    if (attempts < 20) {
                        parentWindow.addEventListener('resize', scheduleApplyHeight);
                        if (parentWindow.visualViewport) {
                            parentWindow.visualViewport.addEventListener('resize', scheduleApplyHeight);
                        }
                    }
                    parentWindow.clearInterval(timer);
                }
            }, 120);
        })();
        </script>
        """.replace("__SCROLL_TARGET__", json.dumps(scroll_target))
    components.html(
        script,
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
    elif is_favorites_deck(st.session_state.selected_csv):
        card["repeat_score"] = max(card["repeat_score"] - 1, 0)
        advance_card()
    else:
        if card.get("id") and not is_learned_words_challenge(st.session_state.selected_csv):
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


def advance_unscored():
    st.session_state.delete_review_confirm_key = None
    advance_card(schedule_current=False)


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


def add_current_card_to_favorites(source_deck=None, source_index=None, advance_after=False):
    if not st.session_state.cards:
        return
    card = st.session_state.cards[current_card_index()]
    upsert_favorite_item(
        current_favorite_person(),
        card,
        source_deck=source_deck,
        source_index=source_index,
    )
    if advance_after:
        if is_playback_deck(st.session_state.selected_csv):
            advance_story_line()
        else:
            card["scored"] = True
            advance_card(schedule_current=False)


def delete_current_favorite_card():
    if not is_favorites_deck(st.session_state.selected_csv):
        return
    idx = current_card_index()
    card = st.session_state.cards[idx]
    favorites_person = favorites_deck_person(st.session_state.selected_csv)
    delete_favorite_item(
        favorites_person,
        card,
        source_deck=card.get("source_deck"),
        source_index=card.get("source_index"),
    )
    st.session_state.delete_review_confirm_key = None


def clear_delete_review_confirm():
    st.session_state.delete_review_confirm_key = None


def add_current_story_line_to_favorites():
    if not st.session_state.cards:
        return
    add_current_card_to_favorites(
        source_deck=st.session_state.selected_csv,
        source_index=current_card_index(),
        advance_after=True,
    )


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
            }, 5000);
        })();
        </script>
        """,
        height=0,
    )


def clear_erase_review_confirm():
    clear_menu_destructive_confirms()


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
            }, 5000);
        })();
        </script>
        """,
        height=0,
    )


def clear_erase_favorites_confirm():
    clear_menu_destructive_confirms()


def render_erase_favorites_confirm_timeout():
    components.html(
        """
        <script>
        (function() {
            function clickClearButton() {
                var doc = window.parent.document;
                var button = doc.querySelector('.st-key-clear_erase_favorites_confirm_wrap button');
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
            }, 5000);
        })();
        </script>
        """,
        height=0,
    )


def clear_initialize_all_decks_confirm():
    clear_menu_destructive_confirms()


def render_initialize_all_decks_confirm_timeout():
    components.html(
        """
        <script>
        (function() {
            function clickClearButton() {
                var doc = window.parent.document;
                var button = doc.querySelector('.st-key-clear_initialize_all_decks_confirm_wrap button');
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
                }, 500);
            }, 5000);
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
    st.session_state.ai_examples_signature = None
    st.session_state.ai_examples_sentences = []
    st.session_state.ai_examples_translations = []
    st.session_state.ai_examples_show_english = False
    st.session_state.ai_examples_index = 0
    st.session_state.ai_examples_error = None
    st.session_state.ai_examples_reload_unlocked = False
    st.session_state.ai_examples_loading = False
    st.session_state.ai_examples_pending_action = None
    st.session_state.direction = effective_direction()


def current_card_supports_ai_examples():
    if not st.session_state.cards or st.session_state.selected_csv is None:
        return False
    if st.session_state.regular_auto_mode:
        return False
    filename = st.session_state.selected_csv
    if (
        is_review_deck(filename)
        or is_favorites_deck(filename)
        or is_learned_words_challenge(filename)
        or filename not in csv_relative_paths
    ):
        return False
    if (
        is_playback_deck(filename)
        or is_sentence_deck(filename)
        or is_story_deck(filename)
        or is_dialog_deck(filename)
    ):
        return False

    folder_labels = [
        normalized_folder_label(part)
        for part in csv_relative_folder_parts_for(filename)
    ]
    if not folder_labels:
        return False

    if folder_labels[0] in AI_EXAMPLES_ALLOWED_TOP_LEVEL_FOLDERS:
        return True

    if len(folder_labels) < 2 or folder_labels[0] != "parts of speech":
        return False

    category_label = folder_labels[1]
    if category_label in AI_EXAMPLES_ALLOWED_POS_FOLDERS:
        return True

    return (
        category_label == "verbs"
        and len(folder_labels) >= 3
        and folder_labels[2] == AI_EXAMPLES_ALLOWED_VERB_FOLDER
    )


@st.cache_data(show_spinner=False, ttl=AI_EXAMPLES_STATUS_TTL_SECONDS)
def ai_examples_service_reachable():
    request = urllib.request.Request("https://api.openai.com/v1", method="HEAD")
    try:
        with urllib.request.urlopen(request, timeout=AI_EXAMPLES_STATUS_TIMEOUT_SECONDS):
            return True
    except urllib.error.HTTPError as error:
        return error.code in {401, 403, 404, 405}
    except (urllib.error.URLError, TimeoutError, socket.timeout, OSError):
        return False


def current_ai_examples_availability():
    if not current_card_supports_ai_examples():
        return {
            "eligible": False,
            "available": False,
            "button_label": "Examples",
            "reason": None,
        }

    api_key = configured_setting("OPENAI_API_KEY")
    if not api_key:
        return {
            "eligible": True,
            "available": False,
            "button_label": "No Key",
            "reason": "Add OPENAI_API_KEY to your environment or Streamlit secrets.",
        }

    if not ai_examples_service_reachable():
        return {
            "eligible": True,
            "available": False,
            "button_label": "Offline",
            "reason": "AI examples are unavailable right now. Check the connection and try again.",
        }

    return {
        "eligible": True,
        "available": True,
        "button_label": "Examples",
        "reason": None,
    }


def ai_examples_request_error_message(error):
    if isinstance(error, urllib.error.HTTPError):
        error_message = f"OpenAI error {error.code}"
        try:
            error_body = json.loads(error.read().decode("utf-8"))
            return error_body.get("error", {}).get("message") or error_message
        except Exception:
            return error_message

    if isinstance(error, (TimeoutError, socket.timeout)):
        return "AI examples timed out. Try again."

    if isinstance(error, urllib.error.URLError):
        if isinstance(error.reason, (TimeoutError, socket.timeout)):
            return "AI examples timed out. Try again."
        return "AI examples are unavailable right now. Check the connection and try again."

    return str(error)


def ai_prompt_text(text):
    cleaned = strip_spoken_text(text or "")
    cleaned = re.sub(r'\s+', ' ', cleaned)
    return cleaned.strip()


def current_ai_examples_signature():
    if not current_card_supports_ai_examples():
        return None
    card = st.session_state.cards[current_card_index()]
    return (
        st.session_state.selected_csv,
        current_card_index(),
        card.get("id"),
        ai_prompt_text(card.get("answer", "")),
        ai_prompt_text(card.get("word", "")),
        tuple(allowed_ai_tense_keys(st.session_state.ai_sentence_tenses)),
        st.session_state.ai_sentence_level,
        st.session_state.ai_examples_target_words,
    )


def sync_ai_examples_state():
    signature = current_ai_examples_signature()
    if st.session_state.ai_examples_signature == signature:
        return
    st.session_state.ai_examples_signature = signature
    st.session_state.ai_examples_sentences = []
    st.session_state.ai_examples_translations = []
    st.session_state.ai_examples_show_english = False
    st.session_state.ai_examples_index = 0
    st.session_state.ai_examples_error = None
    st.session_state.ai_examples_reload_unlocked = False
    st.session_state.ai_examples_loading = False
    st.session_state.ai_examples_pending_action = None


def begin_ai_examples_action(action):
    if action not in {"fetch", "reload"}:
        return
    st.session_state.ai_examples_loading = True
    st.session_state.ai_examples_pending_action = action


def process_pending_ai_examples_action():
    return True


def build_ai_examples_prompt(card, action=None, previous_sentences=None):
    filename = st.session_state.selected_csv
    spanish_term = ai_prompt_text(card.get("answer", ""))
    english_gloss = ai_prompt_text(card.get("word", ""))
    level_prompt = ai_level_prompt_text(st.session_state.ai_sentence_level)
    tense_names = ai_tense_names_text(st.session_state.ai_sentence_tenses)
    target_words = st.session_state.ai_examples_target_words
    folder_labels = [
        normalized_folder_label(part)
        for part in csv_relative_folder_parts_for(filename)
    ] if filename else []
    meaning_clause = ""
    if english_gloss:
        meaning_clause = f' con el sentido de "{english_gloss}"'

    avoid_repeat_clause = ""
    if action == "reload" and previous_sentences:
        prior_examples_text = " | ".join(
            ai_prompt_text(sentence)
            for sentence in previous_sentences
            if ai_prompt_text(sentence)
        )
        if prior_examples_text:
            avoid_repeat_clause = (
                " No repitas ni reformules de cerca estas oraciones anteriores: "
                f"{prior_examples_text}."
            )

    if folder_labels and folder_labels[0] == "vocabulary":
        return (
            f"Escribe {AI_EXAMPLES_PER_BATCH} oraciones distintas y naturales en español mexicano, "
            f"con registro adulto, de aproximadamente {target_words} palabras cada una, "
            f"donde aparezca {spanish_term}{meaning_clause} de forma natural en contexto. "
            "Si la palabra funciona como adjetivo o color, haz que concuerde naturalmente con el sustantivo. "
            f"{level_prompt}. "
            f"Usa solo estas formas verbales para cualquier verbo que aparezca: {tense_names}. "
            f"Varía el contexto y la redacción. "
            f"Cada oración debe acercarse a {target_words} palabras (más o menos 2).{avoid_repeat_clause} "
            f"Para cada oración, escribe primero la oración en español y en la siguiente línea su traducción al inglés. "
            f"Separa los pares con una línea en blanco. No uses numeración."
        )

    return (
        f"Escribe {AI_EXAMPLES_PER_BATCH} oraciones distintas y naturales en español mexicano, "
        f"con registro adulto, de aproximadamente {target_words} palabras cada una, "
        f"usando {spanish_term}{meaning_clause}. "
        f"{level_prompt}. "
        f"Usa solo estas formas verbales para cualquier verbo: {tense_names}. "
        f"Varía el contexto y la redacción. "
        f"Cada oración debe acercarse a {target_words} palabras (más o menos 2).{avoid_repeat_clause} "
        f"Para cada oración, escribe primero la oración en español y en la siguiente línea su traducción al inglés. "
        f"Separa los pares con una línea en blanco. No uses numeración."
    )


def parse_ai_examples_text(text):
    lines = []
    for raw_line in (text or "").splitlines():
        cleaned = re.sub(r'^\s*(?:\d+[\).:-]?\s*|[-*]\s*)', '', raw_line).strip()
        if cleaned:
            lines.append(cleaned)
    if len(lines) < AI_EXAMPLES_PER_BATCH:
        fallback_parts = [
            part.strip()
            for part in re.split(r'(?<=[.!?])\s+', text or "")
            if part.strip()
        ]
        lines = []
        for part in fallback_parts:
            cleaned = re.sub(r'^\s*(?:\d+[\).:-]?\s*|[-*]\s*)', '', part).strip()
            if cleaned:
                lines.append(cleaned)
    return lines[:AI_EXAMPLES_PER_BATCH]


def parse_ai_examples_pairs(text):
    raw_lines = [
        re.sub(r'^\s*(?:\d+[\).:-]?\s*|[-*]\s*)', '', line).strip()
        for line in (text or "").splitlines()
    ]
    groups, current = [], []
    for line in raw_lines:
        if line:
            current.append(line)
        else:
            if current:
                groups.append(current)
                current = []
    if current:
        groups.append(current)
    spanish_list, english_list = [], []
    for group in groups:
        if len(group) >= 2:
            spanish_list.append(group[0])
            english_list.append(group[1])
        elif len(group) == 1:
            spanish_list.append(group[0])
            english_list.append("")
    if len(spanish_list) < AI_EXAMPLES_PER_BATCH:
        non_blank = [l for l in raw_lines if l]
        if len(non_blank) >= AI_EXAMPLES_PER_BATCH * 2:
            spanish_list = [non_blank[i * 2] for i in range(AI_EXAMPLES_PER_BATCH)]
            english_list = [non_blank[i * 2 + 1] for i in range(AI_EXAMPLES_PER_BATCH)]
    return spanish_list[:AI_EXAMPLES_PER_BATCH], english_list[:AI_EXAMPLES_PER_BATCH]


def fetch_ai_examples_for_current_card():
    sync_ai_examples_state()
    st.session_state.ai_examples_error = None
    availability = current_ai_examples_availability()
    if not availability["eligible"]:
        st.session_state.ai_examples_sentences = []
        st.session_state.ai_examples_translations = []
        st.session_state.ai_examples_show_english = False
        st.session_state.ai_examples_loading = False
        st.session_state.ai_examples_pending_action = None
        return False
    if not availability["available"]:
        st.session_state.ai_examples_sentences = []
        st.session_state.ai_examples_translations = []
        st.session_state.ai_examples_show_english = False
        st.session_state.ai_examples_error = availability["reason"]
        st.session_state.ai_examples_loading = False
        st.session_state.ai_examples_pending_action = None
        return False
    api_key = configured_setting("OPENAI_API_KEY")
    card = st.session_state.cards[current_card_index()]
    pending_action = st.session_state.ai_examples_pending_action
    previous_sentences = list(st.session_state.ai_examples_sentences)
    payload = {
        "model": AI_EXAMPLES_MODEL,
        "input": build_ai_examples_prompt(card, action=pending_action, previous_sentences=previous_sentences),
        "temperature": 0.9,
    }
    request = urllib.request.Request(
        "https://api.openai.com/v1/responses",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=AI_EXAMPLES_REQUEST_TIMEOUT_SECONDS) as response:
            result = json.loads(response.read().decode("utf-8"))
    except Exception as error:
        st.session_state.ai_examples_sentences = []
        st.session_state.ai_examples_translations = []
        st.session_state.ai_examples_show_english = False
        st.session_state.ai_examples_error = ai_examples_request_error_message(error)
        st.session_state.ai_examples_loading = False
        st.session_state.ai_examples_pending_action = None
        return False

    output_text = ""
    for item in result.get("output", []):
        for content in item.get("content", []):
            if content.get("type") == "output_text":
                output_text = content.get("text", "")
                break
        if output_text:
            break

    sentences, translations = parse_ai_examples_pairs(output_text)
    if len(sentences) != AI_EXAMPLES_PER_BATCH:
        st.session_state.ai_examples_sentences = []
        st.session_state.ai_examples_translations = []
        st.session_state.ai_examples_show_english = False
        st.session_state.ai_examples_error = "Could not parse three examples from the response."
        st.session_state.ai_examples_loading = False
        st.session_state.ai_examples_pending_action = None
        return False

    st.session_state.ai_examples_sentences = sentences
    st.session_state.ai_examples_translations = translations
    st.session_state.ai_examples_show_english = False
    st.session_state.ai_examples_index = 0
    st.session_state.ai_examples_error = None
    st.session_state.ai_examples_reload_unlocked = False
    st.session_state.ai_examples_loading = False
    st.session_state.ai_examples_pending_action = None
    if st.session_state.auto_speak_spanish:
        st.session_state.ai_examples_autoplay_generation += 1
    return True


def cycle_ai_example():
    if not st.session_state.ai_examples_sentences:
        return
    total = len(st.session_state.ai_examples_sentences)
    st.session_state.ai_examples_index = (st.session_state.ai_examples_index + 1) % total
    if st.session_state.auto_speak_spanish:
        st.session_state.ai_examples_autoplay_generation += 1
    if st.session_state.ai_examples_index == total - 1:
        st.session_state.ai_examples_reload_unlocked = True


def render_ai_example_footer(show_answer):
    return


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


def story_title_card():
    if not story_title_prefix_present():
        return None
    return st.session_state.cards[0]


def story_title_english_text():
    title_card = story_title_card()
    if title_card is None:
        return ""
    return re.sub(r"^title:\s*", "", str(title_card["word"]).strip(), flags=re.IGNORECASE)


def advance_story_line():
    next_index = st.session_state.index + 1
    if next_index >= len(st.session_state.order):
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
    dialog_mode=False,
    repeat_spanish=False,
    initial_render_delay_seconds=0,
):
    spoken_lines = [strip_spoken_text(text) for text in story_lines]
    speech_rate = speech_rate_value()
    delay_ms = max(int(delay_seconds * 1000), 0)
    initial_render_delay_ms = max(int(initial_render_delay_seconds * 1000), 0)
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
                initialRenderDelayMs: {initial_render_delay_ms},
                running: {str(running).lower()},
                resumeNext: {str(resume_next).lower()},
                dialogMode: {str(dialog_mode).lower()},
                repeatSpanish: {str(repeat_spanish).lower()},
            }};

            function isPhoneStoryMode() {{
                var nav = parentWindow.navigator || window.navigator;
                var ua = nav && nav.userAgent ? nav.userAgent : '';
                var hasTouch = !!(('ontouchstart' in parentWindow) || (nav && nav.maxTouchPoints > 0));
                var compactTouchLayout = !!(parentWindow.matchMedia && parentWindow.matchMedia('(max-width: 1024px)').matches);
                var iPadDesktopMode = !!(nav && nav.platform === 'MacIntel' && nav.maxTouchPoints > 1);
                return hasTouch && (compactTouchLayout || iPadDesktopMode || /iPhone|Android|Mobile|iPad|iPod|Tablet/i.test(ua));
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

            function runAfterRenderDelay(callback) {{
                var explicitStartDelayMs = controller.pendingInitialStartDelayMs || 0;
                var effectiveDelayMs = explicitStartDelayMs > 0
                    ? explicitStartDelayMs
                    : (controller.initialRenderDelayMs || 0);
                if (isPhoneStoryMode() && explicitStartDelayMs <= 0) {{
                    effectiveDelayMs = Math.min(effectiveDelayMs, 60);
                }}

                function execute() {{
                    if (effectiveDelayMs > 0) {{
                        parentWindow.setTimeout(callback, effectiveDelayMs);
                    }} else {{
                        callback();
                    }}
                }}

                if (typeof parentWindow.requestAnimationFrame === 'function') {{
                    parentWindow.requestAnimationFrame(function() {{
                        parentWindow.requestAnimationFrame(execute);
                    }});
                    return;
                }}

                parentWindow.setTimeout(execute, 0);
            }}

            function pickStandardVoice() {{
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

            function dialogVoiceIdentity(voice) {{
                return voice ? ((voice.voiceURI || voice.name || '') + '|' + (voice.lang || '')) : '';
            }}

            function resolveDialogVoice(identity, fallbackVoice) {{
                if (doc && typeof doc._fcResolveVoiceIdentity === 'function') {{
                    var resolved = doc._fcResolveVoiceIdentity(identity, 'es');
                    if (resolved) return resolved;
                }}
                if (fallbackVoice && synth.getVoices) {{
                    var fallbackName = normalizeVoiceName(fallbackVoice.name || '');
                    var fallbackLang = (fallbackVoice.lang || '').toLowerCase();
                    var voices = synth.getVoices() || [];
                    var exactMatch = voices.find(function(voice) {{
                        return normalizeVoiceName(voice.name || '') === fallbackName
                            && (voice.lang || '').toLowerCase() === fallbackLang;
                    }});
                    if (exactMatch) return exactMatch;
                    var nameOnlyMatch = voices.find(function(voice) {{
                        return normalizeVoiceName(voice.name || '') === fallbackName;
                    }});
                    if (nameOnlyMatch) return nameOnlyMatch;
                }}
                return fallbackVoice || null;
            }}

            function chooseDialogVoice(preferredGender) {{
                if (doc && typeof doc._fcPickPreferredVoice === 'function') {{
                    return doc._fcPickPreferredVoice('es', {{
                        preferredGender: preferredGender,
                        randomize: true,
                        strictGender: true,
                    }});
                }}
                return null;
            }}

            function updateDialogVoiceReadout() {{
                if (!controller.dialogMode) return;
                var speakerAEl = doc.getElementById('dialog-voice-speaker-a');
                var speakerBEl = doc.getElementById('dialog-voice-speaker-b');
                var femaleVoice = controller.dialogFemaleVoice;
                var maleVoice = controller.dialogMaleVoice;
                var speakerAVoice = controller.dialogFirstSpeaker === 'female' ? femaleVoice : maleVoice;
                var speakerBVoice = controller.dialogFirstSpeaker === 'female' ? maleVoice : femaleVoice;
                if (speakerAEl) {{
                    speakerAEl.textContent = 'Speaker A: ' + (speakerAVoice ? ((speakerAVoice.name || speakerAVoice.voiceURI || 'unknown') + ' [' + (speakerAVoice.lang || 'n/a') + ']') : 'not found');
                }}
                if (speakerBEl) {{
                    speakerBEl.textContent = 'Speaker B: ' + (speakerBVoice ? ((speakerBVoice.name || speakerBVoice.voiceURI || 'unknown') + ' [' + (speakerBVoice.lang || 'n/a') + ']') : 'not found');
                }}
                if (doc && typeof doc._fcRenderDetectedVoices === 'function') {{
                    doc._fcRenderDetectedVoices('es', 'dialog-voice-detected');
                }}
            }}

            function dialogVoiceIdentity(voice) {{
                return voice ? ((voice.voiceURI || voice.name || '') + '|' + (voice.lang || '')) : '';
            }}

            function resolveDialogVoice(identity, fallbackVoice) {{
                if (doc && typeof doc._fcResolveVoiceIdentity === 'function') {{
                    var resolved = doc._fcResolveVoiceIdentity(identity, 'es');
                    if (resolved) return resolved;
                }}
                if (fallbackVoice && synth.getVoices) {{
                    var fallbackName = normalizeVoiceName(fallbackVoice.name || '');
                    var fallbackLang = (fallbackVoice.lang || '').toLowerCase();
                    var voices = synth.getVoices() || [];
                    var exactMatch = voices.find(function(voice) {{
                        return normalizeVoiceName(voice.name || '') === fallbackName
                            && (voice.lang || '').toLowerCase() === fallbackLang;
                    }});
                    if (exactMatch) return exactMatch;
                    var nameOnlyMatch = voices.find(function(voice) {{
                        return normalizeVoiceName(voice.name || '') === fallbackName;
                    }});
                    if (nameOnlyMatch) return nameOnlyMatch;
                }}
                return fallbackVoice || null;
            }}

            function ensureDialogVoiceState() {{
                if (!controller.dialogMode) return;
                if (!controller.dialogFirstSpeaker) {{
                    controller.dialogFirstSpeaker = Math.random() < 0.5 ? 'male' : 'female';
                }}
                if ((!controller.dialogMaleVoice || !controller.dialogFemaleVoice) && doc && typeof doc._fcPickDialogVoicePair === 'function') {{
                    var dialogPair = doc._fcPickDialogVoicePair('es') || {{}};
                    controller.dialogFemaleVoice = dialogPair.femaleVoice || controller.dialogFemaleVoice || null;
                    controller.dialogMaleVoice = dialogPair.maleVoice || controller.dialogMaleVoice || null;
                    controller.dialogFemaleVoiceId = dialogPair.femaleIdentity || controller.dialogFemaleVoiceId || '';
                    controller.dialogMaleVoiceId = dialogPair.maleIdentity || controller.dialogMaleVoiceId || '';
                }}
                if (!controller.dialogMaleVoice) {{
                    controller.dialogMaleVoice = chooseDialogVoice('male');
                    controller.dialogMaleVoiceId = dialogVoiceIdentity(controller.dialogMaleVoice);
                }}
                if (!controller.dialogFemaleVoice) {{
                    controller.dialogFemaleVoice = chooseDialogVoice('female');
                    controller.dialogFemaleVoiceId = dialogVoiceIdentity(controller.dialogFemaleVoice);
                }}
                updateDialogVoiceReadout();
            }}

            function dialogGenderForIndex(index) {{
                if (!controller.dialogMode) return null;
                ensureDialogVoiceState();
                if (controller.dialogFirstSpeaker === 'female') {{
                    return index % 2 === 0 ? 'female' : 'male';
                }}
                return index % 2 === 0 ? 'male' : 'female';
            }}

            function pickVoice(index) {{
                if (!controller.dialogMode) {{
                    return pickStandardVoice();
                }}
                ensureDialogVoiceState();
                var preferredGender = dialogGenderForIndex(index);
                if (preferredGender === 'female') {{
                    return resolveDialogVoice(controller.dialogFemaleVoiceId, controller.dialogFemaleVoice)
                        || resolveDialogVoice(controller.dialogMaleVoiceId, controller.dialogMaleVoice)
                        || pickStandardVoice();
                }}
                return resolveDialogVoice(controller.dialogMaleVoiceId, controller.dialogMaleVoice)
                    || resolveDialogVoice(controller.dialogFemaleVoiceId, controller.dialogFemaleVoice)
                    || pickStandardVoice();
            }}

            function clickAdvanceButton() {{
                var hiddenButton = doc.querySelector('.st-key-storyadvance_hidden_wrap button');
                if (!hiddenButton) {{
                    return false;
                }}
                hiddenButton.click();
                return true;
            }}

            function clickFinishButton() {{
                var hiddenButton = doc.querySelector('.st-key-storyfinish_hidden_wrap button');
                if (!hiddenButton) {{
                    return false;
                }}
                hiddenButton.click();
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

                    var totalPasses = controller.dialogMode && controller.repeatSpanish ? 2 : 1;
                    var currentPass = 0;
                    var lineCompleted = false;
                    var voice = pickVoice(idx);

                    function startPass() {{
                        if (lineCompleted || controller.queueToken !== queueToken || !controller.running) return;

                        var passHandled = false;
                        var watchdogTimerId = null;
                        var pollTimerId = null;
                        var sawSpeaking = false;
                        var speechKey = controller.storyKey + '|queue|' + idx + '|pass|' + currentPass + '|' + rawSpeechText + '|' + speechRate;
                        var utterance = new SpeechSynthesisUtterance(rawSpeechText);

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

                        function finalizeLine(reason) {{
                            if (lineCompleted) return;
                            lineCompleted = true;
                            clearLocalTimers();
                            controller.isSpeaking = false;
                            controller.speakingKey = null;
                            controller.lastCompletedIndex = idx;
                            setDebug('done(' + reason + '): ' + (idx + 1));
                            scheduleNext();
                        }}

                        function finishPass(reason) {{
                            if (passHandled || lineCompleted) return;
                            passHandled = true;
                            clearLocalTimers();
                            controller.isSpeaking = false;
                            controller.speakingKey = null;

                            if (currentPass + 1 < totalPasses) {{
                                currentPass += 1;
                                setDebug('repeat: ' + (idx + 1));
                                var repeatTimerId = parentWindow.setTimeout(function() {{
                                    startPass();
                                }}, 450);
                                controller.visualTimers.push(repeatTimerId);
                                return;
                            }}

                            finalizeLine(reason);
                        }}

                        utterance.lang = voice ? voice.lang : 'es-ES';
                        utterance.rate = speechRate;
                        if (voice) utterance.voice = voice;

                        utterance.onstart = function() {{
                            if (controller.queueToken !== queueToken || !controller.running) return;
                            controller.lastSpokenIndex = idx;
                            controller.pendingManualSpeakIndex = null;
                            controller.isSpeaking = true;
                            controller.speakingKey = speechKey;
                            sawSpeaking = true;
                            setDebug((currentPass > 0 ? 'repeat ' : 'speak ') + (idx + 1));
                        }};

                        utterance.onend = function() {{ finishPass('onend'); }};
                        utterance.onerror = function() {{ finishPass('onerror'); }};

                        function pollSpeaking() {{
                            if (passHandled || lineCompleted) return;
                            if (controller.queueToken !== queueToken) return;
                            try {{
                                if (synth.speaking || synth.pending) {{
                                    sawSpeaking = true;
                                }} else if (sawSpeaking) {{
                                    finishPass('poll');
                                    return;
                                }}
                            }} catch (e) {{}}
                            pollTimerId = parentWindow.setTimeout(pollSpeaking, 250);
                            controller.visualTimers.push(pollTimerId);
                        }}

                        pollTimerId = parentWindow.setTimeout(pollSpeaking, 400);
                        controller.visualTimers.push(pollTimerId);

                        var durMs = estimatedDurationMs(rawSpeechText);
                        var watchdogMs = Math.max(durMs + 1600, 3200);
                        watchdogTimerId = parentWindow.setTimeout(function() {{
                            finishPass('watchdog');
                        }}, watchdogMs);
                        controller.visualTimers.push(watchdogTimerId);

                        synth.speak(utterance);
                    }}

                    startPass();
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
                    function estimatedDurationMs() {{
                        var chars = speechText.length || 1;
                        var rate = speechRate > 0 ? speechRate : 1;
                        return Math.max(1600, Math.round((chars * 85) / rate) + 700);
                    }}
                    var totalPasses = controller.dialogMode && controller.repeatSpanish ? 2 : 1;
                    var currentPass = 0;
                    var lineCompleted = false;
                    var voice = pickVoice(index);

                    function startPass() {{
                        if (lineCompleted || !controller.running) return;

                        var passHandled = false;
                        var completionTimer = null;
                        var speakingPollTimer = null;
                        var utterance = new SpeechSynthesisUtterance(speechText);
                        var passKey = speechKey + '|pass|' + currentPass;

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

                        function finalizeLine(reason) {{
                            if (lineCompleted) return;
                            lineCompleted = true;
                            clearCompletionTimer();
                            setDebug(reason + ': ' + (index + 1));
                            handleLineComplete(index);
                        }}

                        function finishPass(reason) {{
                            if (passHandled || lineCompleted) return;
                            passHandled = true;
                            clearCompletionTimer();
                            controller.isSpeaking = false;
                            controller.speakingKey = null;

                            if (currentPass + 1 < totalPasses) {{
                                currentPass += 1;
                                setDebug('repeat: ' + (index + 1));
                                parentWindow.setTimeout(function() {{
                                    startPass();
                                }}, 450);
                                return;
                            }}

                            finalizeLine(reason);
                        }}

                        utterance.lang = voice ? voice.lang : 'es-ES';
                        utterance.rate = speechRate;
                        if (voice) utterance.voice = voice;

                        utterance.onstart = function() {{
                            controller.localIndex = index;
                            controller.lastSpokenIndex = index;
                            controller.isSpeaking = true;
                            controller.speakingKey = passKey;
                            setDebug((currentPass > 0 ? 'repeat start: ' : 'onstart: ') + (index + 1));
                            doc._storyPauseResumeState = {{
                                runToken: controller.storyRunToken,
                                storyIndex: index,
                                speechFinished: false
                            }};
                            doc._storyPauseRequested = null;
                            speakingPollTimer = parentWindow.setInterval(function() {{
                                if (!controller.running || passHandled || lineCompleted) {{
                                    clearCompletionTimer();
                                    return;
                                }}
                                if (!synth.speaking && !synth.pending) {{
                                    setDebug('poll idle: ' + (index + 1));
                                    finishPass('poll');
                                }}
                            }}, 150);
                        }};
                        utterance.onend = function() {{
                            finishPass('onend');
                        }};
                        utterance.onerror = function() {{
                            controller.isSpeaking = false;
                            controller.speakingKey = null;
                            finishPass('onerror');
                        }};

                        synth.cancel();
                        if (typeof synth.resume === 'function') {{
                            synth.resume();
                        }}
                        synth.speak(utterance);
                        completionTimer = parentWindow.setTimeout(function() {{
                            if (!controller.running || passHandled || lineCompleted) return;
                            if (!controller.isSpeaking && controller.lastCompletedIndex === index) return;
                            finishPass('watchdog');
                        }}, estimatedDurationMs());
                    }}

                    startPass();
                }} catch (error) {{
                    controller.isSpeaking = false;
                    controller.speakingKey = null;
                    setDebug('catch error: ' + (index + 1));
                }}
            }}

            function startFromGesture() {{
                function startImmediately(index) {{
                    setDebug('start gesture: ' + (index + 1));
                    if (controller.autoAdvance) {{
                        queueAutoFrom(index);
                        return;
                    }}
                    controller.pendingManualSpeakIndex = index;
                    speakLine(index);
                }}

                var now = Date.now();
                if (controller.lastStartGestureAt && now - controller.lastStartGestureAt < 900) {{
                    return;
                }}
                controller.lastStartGestureAt = now;
                try {{
                    if (typeof doc._fcSpeechPrimeHandler === 'function') {{
                        doc._fcSpeechPrimeHandler();
                    }}
                }} catch (error) {{
                }}
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

                if (startMode !== 'RESUME' && targetIndex === 0) {{
                    try {{
                        controller.awaitingServerStart = true;
                        controller.pendingInitialStartDelayMs = 2000;
                        setDebug('start primed: ' + (targetIndex + 1));
                        if (typeof synth.cancel === 'function') {{
                            synth.cancel();
                        }}
                        if (typeof synth.resume === 'function') {{
                            synth.resume();
                        }}
                        var primer = new SpeechSynthesisUtterance('.');
                        primer.volume = 0;
                        primer.rate = 1;
                        synth.speak(primer);
                        return;
                    }} catch (error) {{
                        controller.awaitingServerStart = false;
                        controller.pendingInitialStartDelayMs = 0;
                    }}
                }}

                startImmediately(targetIndex);
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

            if (controller.storyKey !== config.storyKey) {{
                cancelSpeech();
                controller.active = false;
                controller.localIndex = config.serverIndex;
                controller.lastSpokenIndex = null;
                controller.lastCompletedIndex = null;
                controller.queuedNextIndex = null;
                controller.resumeTargetIndex = null;
                controller.pausedDisplayIndex = null;
                controller.awaitingServerStart = false;
                controller.pendingInitialStartDelayMs = 0;
                controller.dialogMaleVoice = null;
                controller.dialogFemaleVoice = null;
                controller.dialogFirstSpeaker = null;
            }} else if (controller.storyRunToken !== config.storyRunToken) {{
                var wasAwaitingServerStart = !!controller.awaitingServerStart;
                var preservedInitialStartDelayMs = controller.pendingInitialStartDelayMs || 0;
                var preservedIndex = typeof controller.localIndex === 'number'
                    ? controller.localIndex
                    : config.serverIndex;
                cancelSpeech();
                controller.active = false;
                controller.running = false;
                controller.lastSpokenIndex = null;
                controller.lastCompletedIndex = null;
                controller.queuedNextIndex = null;
                controller.pendingManualSpeakIndex = null;
                controller.resumeTargetIndex = null;
                controller.pausedDisplayIndex = null;
                controller.awaitingServerStart = wasAwaitingServerStart && !!config.running;
                controller.pendingInitialStartDelayMs = controller.awaitingServerStart ? preservedInitialStartDelayMs : 0;
                controller.preserveLocalIndexOnRestart = !!config.running;
                controller.localIndex = (config.running && controller.active)
                    ? preservedIndex
                    : config.serverIndex;
                if (config.running) {{
                    controller.localIndex = preservedIndex;
                }}
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
            controller.initialRenderDelayMs = config.initialRenderDelayMs;
            controller.resumeNext = config.resumeNext;
            controller.dialogMode = config.dialogMode;
            controller.repeatSpanish = config.repeatSpanish;

            if (typeof controller.localIndex !== 'number') {{
                controller.localIndex = config.serverIndex;
            }}

            if (
                !controller.isSpeaking
                && typeof config.serverIndex === 'number'
                && config.serverIndex !== controller.localIndex
                && !controller.preserveLocalIndexOnRestart
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
                controller.awaitingServerStart = false;
                controller.pendingInitialStartDelayMs = 0;
                if (!controller.active) {{
                    controller.localIndex = config.serverIndex;
                }} else if (typeof controller.pausedDisplayIndex === 'number') {{
                    controller.localIndex = controller.pausedDisplayIndex;
                }}
                cancelSpeech();
            }}

            renderLocalStoryViewStable(controller.localIndex);
            setDebug('ready: ' + (controller.localIndex + 1) + ' running=' + config.running + ' auto=' + controller.autoAdvance);

            if (config.running && (controller.awaitingServerStart || !controller.active) && !controller.isSpeaking) {{
                controller.active = true;
                controller.running = true;
                controller.awaitingServerStart = false;
                controller.preserveLocalIndexOnRestart = false;
                controller.pausedDisplayIndex = null;
                controller.queuedNextIndex = null;
                controller.pendingManualSpeakIndex = null;
                setDebug('restart run: ' + (controller.localIndex + 1));
                runAfterRenderDelay(function() {{
                    controller.pendingInitialStartDelayMs = 0;
                    if (!controller.running) return;
                    if (controller.autoAdvance) {{
                        queueAutoFrom(controller.localIndex);
                    }} else {{
                        controller.pendingManualSpeakIndex = controller.localIndex;
                        speakLine(controller.localIndex);
                    }}
                }});
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
            doc._storyLastSpeechBaseKey = null;
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
    last_story_index = max(len(st.session_state.order) - 1, 0)
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


def render_story_audio_autoplay(text, auto_advance=False, delay_seconds=0, dialog_mode=False, repeat_spanish=False, render_delay_seconds=0):
    speech_text = strip_spoken_text(text)
    speech_rate = speech_rate_value()
    story_index = st.session_state.index
    story_run_token = st.session_state.story_run_token
    delay_ms = max(int(delay_seconds * 1000), 0)
    render_delay_ms = max(int(render_delay_seconds * 1000), 0)
    last_story_index = max(len(st.session_state.order) - 1, 0)
    components.html(
        f"""
        <script>
        (function() {{
            var parentWindow = window.parent;
            var nav = parentWindow.navigator || window.navigator;
            var ua = nav && nav.userAgent ? nav.userAgent : '';
            var hasTouch = !!(('ontouchstart' in parentWindow) || (nav && nav.maxTouchPoints > 0));
            var compactTouchLayout = !!(parentWindow.matchMedia && parentWindow.matchMedia('(max-width: 1024px)').matches);
            var iPadDesktopMode = !!(nav && nav.platform === 'MacIntel' && nav.maxTouchPoints > 1);
            if (hasTouch && (compactTouchLayout || iPadDesktopMode || /iPhone|Android|Mobile|iPad|iPod|Tablet/i.test(ua))) return;

            var speechText = {json.dumps(speech_text)};
            var speechRate = {speech_rate};
            var storyIndex = {story_index};
            var storyRunToken = {story_run_token};
            var autoAdvance = {str(auto_advance).lower()};
            var delayMs = {delay_ms};
            var renderDelayMs = {render_delay_ms};
            var lastStoryIndex = {last_story_index};
            var dialogMode = {str(dialog_mode).lower()};
            var repeatSpanish = {str(repeat_spanish).lower()};
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
            if (doc._storyLastSpeechBaseKey === speechKey) return;

            function pickStandardVoice() {{
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

            function dialogVoiceIdentity(voice) {{
                return voice ? ((voice.voiceURI || voice.name || '') + '|' + (voice.lang || '')) : '';
            }}

            function resolveDialogVoice(identity, fallbackVoice) {{
                if (doc && typeof doc._fcResolveVoiceIdentity === 'function') {{
                    return doc._fcResolveVoiceIdentity(identity, 'es') || fallbackVoice || null;
                }}
                return fallbackVoice || null;
            }}

            function ensureDialogVoiceState() {{
                if (!dialogMode) return null;
                var cacheKey = storyRunToken + '|' + (doc._storyPlaybackKey || 'dialog');
                if (!doc._storyDialogVoiceState || doc._storyDialogVoiceState.cacheKey !== cacheKey) {{
                    var dialogPair = doc && typeof doc._fcPickDialogVoicePair === 'function'
                        ? doc._fcPickDialogVoicePair('es')
                        : null;
                    doc._storyDialogVoiceState = {{
                        cacheKey: cacheKey,
                        firstSpeaker: Math.random() < 0.5 ? 'male' : 'female',
                        maleVoice: (dialogPair && dialogPair.maleVoice) || (doc && typeof doc._fcPickPreferredVoice === 'function'
                            ? doc._fcPickPreferredVoice('es', {{ preferredGender: 'male', randomize: true, strictGender: true }})
                            : pickStandardVoice()),
                        femaleVoice: (dialogPair && dialogPair.femaleVoice) || (doc && typeof doc._fcPickPreferredVoice === 'function'
                            ? doc._fcPickPreferredVoice('es', {{ preferredGender: 'female', randomize: true, strictGender: true }})
                            : pickStandardVoice()),
                        maleVoiceId: (dialogPair && dialogPair.maleIdentity) || '',
                        femaleVoiceId: (dialogPair && dialogPair.femaleIdentity) || '',
                        maleCandidateIdentities: (dialogPair && dialogPair.maleCandidateIdentities) || [],
                        femaleCandidateIdentities: (dialogPair && dialogPair.femaleCandidateIdentities) || [],
                    }};
                    if (!doc._storyDialogVoiceState.maleVoiceId) {{
                        doc._storyDialogVoiceState.maleVoiceId = dialogVoiceIdentity(doc._storyDialogVoiceState.maleVoice);
                    }}
                    if (!doc._storyDialogVoiceState.femaleVoiceId) {{
                        doc._storyDialogVoiceState.femaleVoiceId = dialogVoiceIdentity(doc._storyDialogVoiceState.femaleVoice);
                    }}
                }}
                var speakerAEl = doc.getElementById('dialog-voice-speaker-a');
                var speakerBEl = doc.getElementById('dialog-voice-speaker-b');
                var femaleVoice = doc._storyDialogVoiceState.femaleVoice;
                var maleVoice = doc._storyDialogVoiceState.maleVoice;
                var speakerAVoice = doc._storyDialogVoiceState.firstSpeaker === 'female' ? femaleVoice : maleVoice;
                var speakerBVoice = doc._storyDialogVoiceState.firstSpeaker === 'female' ? maleVoice : femaleVoice;
                if (speakerAEl) {{
                    speakerAEl.textContent = 'Speaker A: ' + (speakerAVoice ? ((speakerAVoice.name || speakerAVoice.voiceURI || 'unknown') + ' [' + (speakerAVoice.lang || 'n/a') + ']') : 'not found');
                }}
                if (speakerBEl) {{
                    speakerBEl.textContent = 'Speaker B: ' + (speakerBVoice ? ((speakerBVoice.name || speakerBVoice.voiceURI || 'unknown') + ' [' + (speakerBVoice.lang || 'n/a') + ']') : 'not found');
                }}
                if (doc && typeof doc._fcRenderDetectedVoices === 'function') {{
                    doc._fcRenderDetectedVoices('es', 'dialog-voice-detected');
                }}
                return doc._storyDialogVoiceState;
            }}

            function preferredGenderForLine(dialogState) {{
                if (!dialogState) return null;
                return dialogState.firstSpeaker === 'female'
                    ? (storyIndex % 2 === 0 ? 'female' : 'male')
                    : (storyIndex % 2 === 0 ? 'male' : 'female');
            }}

            function rotateDialogVoiceCandidate(dialogState, gender) {{
                if (!dialogState) return false;
                var candidateKey = gender === 'female' ? 'femaleCandidateIdentities' : 'maleCandidateIdentities';
                var activeKey = gender === 'female' ? 'femaleVoiceId' : 'maleVoiceId';
                var voiceKey = gender === 'female' ? 'femaleVoice' : 'maleVoice';
                var identities = dialogState[candidateKey] || [];
                if (identities.length <= 1) return false;

                var currentId = dialogState[activeKey] || '';
                var currentIndex = identities.indexOf(currentId);
                var startIndex = currentIndex >= 0 ? currentIndex : 0;

                for (var step = 1; step < identities.length; step += 1) {{
                    var nextId = identities[(startIndex + step) % identities.length];
                    if (!nextId || nextId === currentId) continue;
                    var nextVoice = resolveDialogVoice(nextId, null);
                    if (!nextVoice) continue;
                    dialogState[activeKey] = nextId;
                    dialogState[voiceKey] = nextVoice;
                    return true;
                }}

                return false;
            }}

            function pickVoiceForLine() {{
                if (!dialogMode) {{
                    return pickStandardVoice();
                }}
                var dialogState = ensureDialogVoiceState();
                if (!dialogState) return pickStandardVoice();
                var preferredGender = preferredGenderForLine(dialogState);
                if (preferredGender === 'female') {{
                    return resolveDialogVoice(dialogState.femaleVoiceId, dialogState.femaleVoice)
                        || resolveDialogVoice(dialogState.maleVoiceId, dialogState.maleVoice)
                        || pickStandardVoice();
                }}
                return resolveDialogVoice(dialogState.maleVoiceId, dialogState.maleVoice)
                    || resolveDialogVoice(dialogState.femaleVoiceId, dialogState.femaleVoice)
                    || pickStandardVoice();
            }}

            function speakNow() {{
                doc._storyPauseResumeState = {{
                    runToken: storyRunToken,
                    storyIndex: storyIndex,
                    speechFinished: false
                }};
                doc._storyPauseRequested = null;

                var totalPasses = dialogMode && repeatSpanish ? 2 : 1;
                var currentPass = 0;
                var speechFinished = false;
                var lineVoice = pickVoiceForLine();

                function finalizeSpeech() {{
                    if (speechFinished) return;
                    speechFinished = true;

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

                function speakPass() {{
                    if (speechFinished) return;
                    var completionHandled = false;
                    var speechStarted = false;
                    var startWatchdog = null;
                    var startAttempts = 0;
                    var lineVoiceId = dialogVoiceIdentity(lineVoice);
                    var currentVoiceEl = doc.getElementById('dialog-voice-current');

                    function updateCurrentVoiceReadout(statusLabel) {{
                        if (!currentVoiceEl) return;
                        currentVoiceEl.textContent = 'Current line: ' + (lineVoice
                            ? ((lineVoice.name || lineVoice.voiceURI || 'unknown') + ' [' + (lineVoice.lang || 'n/a') + ']')
                            : 'not found')
                            + (statusLabel ? (' (' + statusLabel + ')') : '');
                    }}

                    updateCurrentVoiceReadout('queued');

                    function finishPass() {{
                        if (completionHandled || speechFinished) return;
                        completionHandled = true;

                        if (startWatchdog) {{
                            clearTimeout(startWatchdog);
                            startWatchdog = null;
                        }}

                        if (currentPass + 1 < totalPasses) {{
                            currentPass += 1;
                            window.setTimeout(function() {{
                                speakPass();
                            }}, 450);
                            return;
                        }}

                        finalizeSpeech();
                    }}

                    function retryCurrentLine(statusLabel, delayMs) {{
                        if (completionHandled || speechFinished) return true;
                        if (startAttempts >= 3) return false;
                        var dialogState = ensureDialogVoiceState();
                        var preferredGender = preferredGenderForLine(dialogState);
                        if (preferredGender) {{
                            rotateDialogVoiceCandidate(dialogState, preferredGender);
                            lineVoice = pickVoiceForLine() || lineVoice;
                            lineVoiceId = dialogVoiceIdentity(lineVoice);
                        }}
                        if (startWatchdog) {{
                            clearTimeout(startWatchdog);
                            startWatchdog = null;
                        }}
                        try {{
                            synth.cancel();
                        }} catch (error) {{
                        }}
                        updateCurrentVoiceReadout(statusLabel);
                        window.setTimeout(startSpeaking, delayMs || 260);
                        return true;
                    }}

                    doc._storyLastSpeechBaseKey = speechKey;
                    doc._storyLastSpeechKey = speechKey + '|pass|' + currentPass;

                    function startSpeaking() {{
                        if (speechFinished || completionHandled) return;
                        startAttempts += 1;
                        lineVoice = pickVoiceForLine() || lineVoice;
                        lineVoiceId = dialogVoiceIdentity(lineVoice);
                        speechStarted = false;
                        updateCurrentVoiceReadout(startAttempts > 1 ? ('retry ' + startAttempts) : 'speaking');
                        var utterance = new SpeechSynthesisUtterance(speechText);
                        utterance.lang = lineVoice ? lineVoice.lang : 'es-ES';
                        utterance.rate = speechRate;
                        if (lineVoice) {{
                            utterance.voice = lineVoice;
                            utterance.lang = lineVoice.lang || utterance.lang;
                        }}
                        utterance.onstart = function() {{
                            speechStarted = true;
                            doc._storySpeechUnlocked = true;
                            doc._storySpeechUnlockedAt = Date.now();
                            if (startWatchdog) {{
                                clearTimeout(startWatchdog);
                                startWatchdog = null;
                            }}
                        }};
                        utterance.onend = finishPass;
                        utterance.onerror = function() {{
                            var pauseRequested = doc._storyPauseRequested
                                && doc._storyPauseRequested.runToken === storyRunToken
                                && doc._storyPauseRequested.storyIndex === storyIndex;
                            if (pauseRequested) return;
                            if (!speechStarted && retryCurrentLine('retrying after error', 320)) return;
                            finishPass();
                        }};
                        if (typeof synth.resume === 'function') {{
                            synth.resume();
                        }}
                        doc._storyLastRequestedVoiceId = lineVoiceId || '';
                        synth.speak(utterance);
                    }}

                    var voiceSwitchDelay = 0;
                    if (lineVoiceId && doc._storyLastRequestedVoiceId && lineVoiceId !== doc._storyLastRequestedVoiceId) {{
                        voiceSwitchDelay = 220;
                        try {{
                            synth.cancel();
                        }} catch (error) {{
                        }}
                    }}

                    if (synth.speaking || synth.pending) {{
                        synth.cancel();
                        voiceSwitchDelay = Math.max(voiceSwitchDelay, 120);
                    }}

                    if (voiceSwitchDelay > 0) {{
                        window.setTimeout(startSpeaking, voiceSwitchDelay);
                    }} else {{
                        startSpeaking();
                    }}

                    startWatchdog = window.setTimeout(function() {{
                        if (completionHandled || speechStarted) return;
                        if (synth.speaking || synth.pending) return;
                        if (retryCurrentLine('retrying', 260)) {{
                            return;
                        }}
                        doc._storyLastSpeechKey = null;
                        doc._storyLastSpeechBaseKey = null;
                        updateCurrentVoiceReadout('skipped');
                        finishPass();
                    }}, 1400);
                }}

                speakPass();
            }}

            function startSpeechAfterRenderDelay(runSpeech) {{
                var execute = function() {{
                    if (renderDelayMs > 0) {{
                        window.setTimeout(runSpeech, renderDelayMs);
                    }} else {{
                        runSpeech();
                    }}
                }};

                if (typeof parentWindow.requestAnimationFrame === 'function') {{
                    parentWindow.requestAnimationFrame(function() {{
                        parentWindow.requestAnimationFrame(execute);
                    }});
                    return;
                }}

                if (typeof window.requestAnimationFrame === 'function') {{
                    window.requestAnimationFrame(function() {{
                        window.requestAnimationFrame(execute);
                    }});
                    return;
                }}

                window.setTimeout(execute, 0);
            }}

            if (synth.getVoices && synth.getVoices().length) {{
                startSpeechAfterRenderDelay(speakNow);
                return;
            }}

            var handled = false;
            function handleVoicesChanged() {{
                if (handled) return;
                handled = true;
                startSpeechAfterRenderDelay(speakNow);
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
    dialog_mode = current_playback_kind() == "dialog"
    story_card = current_story_card()
    title_card = None if dialog_mode else story_title_card()
    sync_story_option_widget_state()
    display_mode = normalize_story_display_mode(st.session_state.story_display_mode)
    show_spanish = display_mode in {"spanish", "both"}
    show_english = display_mode in {"english", "both"}
    spanish_text = story_card["answer"]
    translation_text = story_card["word"] if show_english else ""
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
    ordered_story_cards = [st.session_state.cards[idx] for idx in st.session_state.order]
    ordered_story_line_numbers = [idx + 1 for idx in st.session_state.order]
    story_pause_delays = [
        story_pause_seconds_for_text(card["answer"])
        for card in ordered_story_cards
    ]
    story_pause_delay = story_pause_delays[st.session_state.index] if story_pause_delays else 0.0
    current_story_favorited = favorite_entry_exists(
        st.session_state.active_person,
        story_card,
        source_deck=st.session_state.selected_csv,
        source_index=current_card_index(),
    )

    with st.container(key="storyoptions_stack_wrap"):
        with st.container(key="storyplayback_row_wrap"):
            playback_cols = st.columns([0.50, 0.17, 0.17], gap="small")
            with playback_cols[0]:
                st.markdown(
                    f'<div class="story-option-row">{current_playback_heading()}</div>',
                    unsafe_allow_html=True,
                )
            with playback_cols[1]:
                st.checkbox(
                    "Auto",
                    key="story_playback_auto_checkbox",
                    on_change=toggle_story_playback_auto,
                )
            with playback_cols[2]:
                st.checkbox(
                    "Step",
                    key="story_playback_step_checkbox",
                    on_change=toggle_story_playback_step,
                )
        with st.container(key="storytransaudio_dialog_row_wrap" if dialog_mode else "storytransaudio_story_row_wrap"):
            ta_cols = st.columns(3, gap="small")
            with ta_cols[0]:
                st.checkbox(
                    "Audio",
                    key="story_audio_checkbox",
                    on_change=toggle_story_audio,
                )
            with ta_cols[1]:
                st.checkbox(
                    "Random",
                    key="story_random_checkbox",
                    on_change=toggle_story_random,
                )
            if dialog_mode:
                with ta_cols[2]:
                    st.checkbox(
                        "2x",
                        key="story_repeat_checkbox",
                        on_change=toggle_story_repeat_spanish,
                    )
            else:
                with ta_cols[2]:
                    st.empty()
        with st.container(key="storydisplay_row_wrap"):
            st.radio(
                "Story display mode",
                options=["spanish", "english", "both"],
                horizontal=True,
                key="story_display_mode_radio",
                on_change=toggle_story_display_mode,
                format_func=lambda value: {
                    "spanish": "Spanish",
                    "english": "English",
                    "both": "Both",
                }[value],
                label_visibility="collapsed",
            )

    audio_enabled = st.session_state.story_audio_on

    story_spanish_html_lines = [
        format_word(card["answer"], 'fc-word', 'fc-note') if show_spanish else '<div class="fc-word-placeholder">&nbsp;</div>'
        for card in ordered_story_cards
    ]
    story_translation_html_lines = [
        format_word(card["word"], 'fc-answer', 'fc-answer-note')
        if show_english else '<div class="fc-word-placeholder">&nbsp;</div>'
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
            control_cols = st.columns(4, gap="small")
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
            with control_cols[3]:
                with st.container(key="storyfavorite_active_wrap" if current_story_favorited else "storyfavorite_wrap"):
                    if st.button("♥︎", key="story_favorite_end_btn", use_container_width=True, disabled=current_story_favorited):
                        add_current_story_line_to_favorites()
                        st.rerun()
    elif st.session_state.story_running:
        with st.container(key="storycontrol_row_wrap"):
            control_cols = st.columns(4, gap="small")
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
            with control_cols[3]:
                with st.container(key="storyfavorite_active_wrap" if current_story_favorited else "storyfavorite_wrap"):
                    if st.button("♥︎", key="story_favorite_running_btn", use_container_width=True, disabled=current_story_favorited):
                        add_current_story_line_to_favorites()
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
                with st.container(key="storyfavorite_active_wrap" if current_story_favorited else "storyfavorite_wrap"):
                    if st.button("♥︎", key="story_favorite_idle_btn", use_container_width=True, disabled=current_story_favorited):
                        add_current_story_line_to_favorites()
                        st.rerun()
        if not st.session_state.story_started and title_card is not None:
            title_spanish = html.escape(str(title_card["answer"]))
            title_english = html.escape(story_title_english_text())
            st.markdown(
                "<div class='story-title-block'>"
                f"<div class='story-title-spanish'>{title_spanish}</div>"
                f"<div class='story-title-english'>{title_english}</div>"
                "</div>",
                unsafe_allow_html=True,
            )

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
            dialog_mode=dialog_mode,
            repeat_spanish=dialog_mode and st.session_state.story_repeat_spanish_on,
            initial_render_delay_seconds=1.0,
        )

    if not st.session_state.story_started:
        return

    st.markdown(
        "<div class='story-progress'>"
        "<div class='story-progress-head'>"
        f"<div class='story-progress-label'>{current_playback_progress_label()}</div>"
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
    if dialog_mode:
        pass
        # Temporary dialog voice diagnostics retained for future debugging.
        # st.markdown(
        #     "<div class='dialog-voice-readout'>"
        #     "<div class='dialog-voice-readout-label'>Dialog Voices</div>"
        #     "<div class='dialog-voice-readout-line' id='dialog-voice-speaker-a'>Speaker A: selecting...</div>"
        #     "<div class='dialog-voice-readout-line' id='dialog-voice-speaker-b'>Speaker B: selecting...</div>"
        #     "<div class='dialog-voice-readout-line' id='dialog-voice-current'>Current line: waiting...</div>"
        #     "<div class='dialog-voice-readout-detected' id='dialog-voice-detected'>Spanish voices: scanning...</div>"
        #     "</div>",
        #     unsafe_allow_html=True,
        # )

    story_box_shield = story_box_shield_html(False)

    if show_spanish:
        spanish_html = (
            '<div class="story-display-block">'
            + story_box_shield
            + '<div class="fc-section-label">Spanish</div>'
            + '<div id="story-spanish-content">'
            + format_word(spanish_text, 'fc-word', 'fc-note')
            + '</div>'
            + '</div>'
        )
        st.markdown(spanish_html, unsafe_allow_html=True)

    if show_english:
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
            dialog_mode=dialog_mode,
            repeat_spanish=dialog_mode and st.session_state.story_repeat_spanish_on,
            render_delay_seconds=1.0,
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
    spoken_text = re.sub(r'_{3,}', ' ', spoken_text)
    spoken_text = re.sub(r'\s+', ' ', spoken_text)
    return spoken_text.strip()


def render_flashcard(prompt, solution, show_answer):
    q_inner = format_word(prompt, 'fc-word', 'fc-note')
    q_html  = '<div class="fc-block"><div class="fc-section-label">Prompt</div>' + q_inner + '</div>'
    st.markdown(q_html, unsafe_allow_html=True)
    if show_answer:
        a_inner = format_word(solution, 'fc-answer', 'fc-answer-note')
        ai_extra_html = ''
        if current_card_supports_ai_examples():
            sync_ai_examples_state()
            if st.session_state.ai_examples_sentences:
                idx = st.session_state.ai_examples_index
                show_en = st.session_state.ai_examples_show_english
                translations = st.session_state.ai_examples_translations
                if show_en and idx < len(translations) and translations[idx]:
                    current_example = translations[idx]
                    example_label = "Translation"
                else:
                    current_example = st.session_state.ai_examples_sentences[idx]
                    example_label = "Example"
                current_position = idx + 1
                total_examples = len(st.session_state.ai_examples_sentences)
                ai_extra_html = (
                    '<div class="fc-ai-example-wrap">'
                    f'<div class="fc-ai-example-label">{example_label}</div>'
                    '<div class="fc-ai-example">'
                    + html.escape(current_example)
                    + ' <span class="fc-ai-example-count">['
                    + f'{current_position}/{total_examples}'
                    + ']</span></div>'
                    '</div>'
                )
            elif st.session_state.ai_examples_error:
                ai_extra_html = (
                    '<div class="fc-ai-error">'
                    + html.escape(st.session_state.ai_examples_error)
                    + '</div>'
                )
        a_html  = '<div class="fc-block"><div class="fc-section-label">Answer</div>' + a_inner + ai_extra_html + '</div>'
    else:
        a_html  = '<div class="fc-block fc-block-empty"><div class="fc-section-label">Answer</div><div class="fc-word-placeholder">&nbsp;</div></div>'
    st.markdown(a_html, unsafe_allow_html=True)


def inject_tap_reveal(show_answer):
    show_str = "true" if show_answer else "false"
    components.html("""
    <script>
    (function() {
        var parentWindow = window.parent;
        var doc = parentWindow.document;
        var showAnswer = """ + show_str + """;

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
            doc._fcHandler = function(e) {
                if (!e.target.closest('.fc-block')) return;
                if (!showAnswer) {
                    clickShowAnswerButton();
                }
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
                    female: ['Angélica (Enhanced)', 'Paulina (Enhanced)', 'Marisol (Premium)', 'Soledad', 'Mónica'],
                    male: ['Juan (Enhanced)', 'Jorge (Enhanced)', 'Diego', 'Carlos']
                }
            };

            doc._fallbackVoicePools = {
                en: {
                    female: ['Samantha', 'Karen', 'Moira', 'Tessa'],
                    male: ['Daniel']
                },
                es: {
                    female: ['Isabela', 'Francisca', 'Jimena', 'Soledad', 'Angélica', 'Angelica', 'Paulina', 'Marisol', 'Mónica', 'Monica'],
                    male: ['Diego', 'Carlos', 'Juan', 'Jorge']
                }
            };

            doc._preferredDialogVoicePairs = {
                es: [
                    { female: ['Paulina (Enhanced)', 'Paulina'], male: ['Juan (Enhanced)', 'Juan'] },
                    { female: ['Paulina (Enhanced)', 'Paulina'], male: ['Jorge (Enhanced)', 'Jorge'] },
                    { female: ['Marisol (Premium)', 'Marisol'], male: ['Jorge (Enhanced)', 'Jorge'] },
                    { female: ['Mónica', 'Monica'], male: ['Carlos (Enhanced)', 'Carlos'] }
                ],
                en: []
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
                var normalizedUri = normalizeVoiceName((voice && voice.voiceURI) || '');
                var combined = (normalized + ' ' + normalizedUri).trim();
                var femaleTokens = ['ava', 'samantha', 'zoe', 'angelica', 'paulina', 'marisol', 'female', 'woman', 'victoria', 'zira', 'karen', 'monica', 'maria', 'sofia', 'soledad', 'paloma', 'lucia', 'luciana', 'isabela', 'francisca', 'jimena'];
                var maleTokens = ['evan', 'nathan', 'nicky', 'juan', 'jorge', 'male', 'man', 'alex', 'daniel', 'aaron', 'rishi', 'diego', 'raul', 'carlos', 'miguel', 'antonio', 'felipe', 'pedro'];
                if (femaleTokens.some(function(token) { return combined.indexOf(token) !== -1; })) return 'female';
                if (maleTokens.some(function(token) { return combined.indexOf(token) !== -1; })) return 'male';
                return null;
            }

            function voiceIdentity(voice) {
                if (!voice) return '';
                return (voice.voiceURI || voice.name || '') + '|' + (voice.lang || '');
            }

            function findVoiceByIdentity(voices, identity) {
                if (!identity) return null;
                return voices.find(function(voice) {
                    return voiceIdentity(voice) === identity;
                }) || null;
            }

            function voiceQualityRank(voice) {
                var haystack = normalizeVoiceName((voice && voice.name) || '') + ' ' + normalizeVoiceName((voice && voice.voiceURI) || '');
                if (haystack.indexOf('premium') !== -1) return 4;
                if (haystack.indexOf('enhanced') !== -1) return 3;
                if (haystack.indexOf('super compact') !== -1) return 2;
                if (haystack.indexOf('compact') !== -1) return 1;
                return 0;
            }

            function isNoveltyVoice(voice) {
                var normalizedName = normalizeVoiceName((voice && voice.name) || '');
                var normalizedUri = normalizeVoiceName((voice && voice.voiceURI) || '');
                var noveltyNames = [
                    'bad news', 'bahh', 'bells', 'boing', 'bubbles', 'cellos', 'good news',
                    'hysterical', 'jester', 'organ', 'princess', 'superstar', 'trinoids',
                    'whisper', 'deranged', 'wobble', 'zarvox'
                ];
                if (noveltyNames.some(function(token) { return normalizedName.indexOf(token) !== -1 || normalizedUri.indexOf(token) !== -1; })) {
                    return true;
                }
                return normalizedUri.indexOf('com apple speech synthesis voice') !== -1;
            }

            function sortVoicesByPreference(voices) {
                return voices.slice().sort(function(a, b) {
                    var qualityDiff = voiceQualityRank(b) - voiceQualityRank(a);
                    if (qualityDiff !== 0) return qualityDiff;

                    var defaultDiff = (b && b.default ? 1 : 0) - (a && a.default ? 1 : 0);
                    if (defaultDiff !== 0) return defaultDiff;

                    var localDiff = (b && b.localService ? 1 : 0) - (a && a.localService ? 1 : 0);
                    if (localDiff !== 0) return localDiff;

                    var nameA = normalizeVoiceName((a && a.name) || '');
                    var nameB = normalizeVoiceName((b && b.name) || '');
                    if (nameA !== nameB) return nameA < nameB ? -1 : 1;

                    var uriA = normalizeVoiceName((a && a.voiceURI) || '');
                    var uriB = normalizeVoiceName((b && b.voiceURI) || '');
                    if (uriA !== uriB) return uriA < uriB ? -1 : 1;
                    return 0;
                });
            }

            function languageCandidates(voices, language) {
                var lowerLanguage = (language || '').toLowerCase();
                if (lowerLanguage === 'es') {
                    return sortVoicesByPreference(voices.filter(function(voice) {
                        var lang = (voice.lang || '').toLowerCase();
                        return (lang === 'es-mx' || lang === 'es-us' || lang === 'es-es' || lang.indexOf('es') === 0) && !isNoveltyVoice(voice);
                    }));
                }
                return sortVoicesByPreference(voices.filter(function(voice) {
                    var lang = (voice.lang || '').toLowerCase();
                    return (lang === 'en-us' || lang === 'en-gb' || lang === 'en-au' || lang.indexOf('en') === 0) && !isNoveltyVoice(voice);
                }));
            }

            doc._fcRenderDetectedVoices = function(language, elementId) {
                var target = doc.getElementById(elementId || 'dialog-voice-detected');
                if (!target) return;

                var voices = synth.getVoices ? synth.getVoices() : [];
                var candidates = languageCandidates(voices, language || 'es');
                if (!candidates.length) {
                    target.textContent = 'Spanish voices: none detected by browser';
                    return;
                }

                var labels = candidates.map(function(voice) {
                    var name = voice.name || voice.voiceURI || 'unknown';
                    var lang = voice.lang || 'n/a';
                    return name + ' [' + lang + ']';
                });
                target.textContent = 'Spanish voices: ' + labels.join(', ');
            };

            function randomChoice(items) {
                if (!items || !items.length) return null;
                return items[Math.floor(Math.random() * items.length)];
            }

            function highestQualityVoices(voices) {
                if (!voices || !voices.length) return [];
                var ordered = sortVoicesByPreference(voices);
                var topRank = voiceQualityRank(ordered[0]);
                return ordered.filter(function(voice) {
                    return voiceQualityRank(voice) === topRank;
                });
            }

            function chooseBestVoice(voices, randomize) {
                if (!voices || !voices.length) return null;
                var bestVoices = highestQualityVoices(voices);
                if (!bestVoices.length) return null;
                return randomize ? randomChoice(bestVoices) : bestVoices[0];
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
                var strictGender = options.strictGender === true;
                var pool = doc._preferredVoicePools[languageKey] || { female: [], male: [] };
                var fallbackPool = doc._fallbackVoicePools[languageKey] || { female: [], male: [] };
                var genders = preferredGender ? [preferredGender] : ['female', 'male'];
                var preferredMatches = [];
                var seen = {};

                genders.forEach(function(gender) {
                    matchedVoicesForTokens(candidates, pool[gender] || []).forEach(function(voice) {
                        pushUnique(preferredMatches, voice, seen);
                    });
                });

                if (preferredMatches.length) {
                    return chooseBestVoice(preferredMatches, randomize);
                }

                var fallbackMatches = [];
                genders.forEach(function(gender) {
                    matchedVoicesForTokens(candidates, fallbackPool[gender] || []).forEach(function(voice) {
                        pushUnique(fallbackMatches, voice, seen);
                    });
                });

                if (fallbackMatches.length) {
                    return chooseBestVoice(fallbackMatches, randomize);
                }

                if (preferredGender) {
                    var genderMatches = sortVoicesByPreference(candidates.filter(function(voice) {
                        return inferGender(voice) === preferredGender;
                    }));
                    if (genderMatches.length) {
                        return chooseBestVoice(genderMatches, randomize);
                    }
                    if (strictGender) {
                        return null;
                    }
                }

                if (candidates.length) {
                    return chooseBestVoice(candidates, randomize);
                }

                return null;
            };

            doc._fcPickDialogVoicePair = function(language) {
                var voices = synth.getVoices ? synth.getVoices() : [];
                var candidates = languageCandidates(voices, language);
                var languageKey = language === 'es' ? 'es' : 'en';

                function orderedCandidatesForGender(gender) {
                    var ordered = [];
                    var seen = {};
                    var pool = doc._preferredVoicePools[languageKey] || { female: [], male: [] };
                    var fallbackPool = doc._fallbackVoicePools[languageKey] || { female: [], male: [] };

                    matchedVoicesForTokens(candidates, pool[gender] || []).forEach(function(voice) {
                        pushUnique(ordered, voice, seen);
                    });

                    matchedVoicesForTokens(candidates, fallbackPool[gender] || []).forEach(function(voice) {
                        pushUnique(ordered, voice, seen);
                    });

                    sortVoicesByPreference(candidates.filter(function(voice) {
                        return inferGender(voice) === gender;
                    })).forEach(function(voice) {
                        pushUnique(ordered, voice, seen);
                    });

                    return sortVoicesByPreference(ordered);
                }

                function bestVoiceForTokens(tokens) {
                    return chooseBestVoice(matchedVoicesForTokens(candidates, tokens || []), false);
                }

                function pairScore(femaleVoice, maleVoice) {
                    if (!femaleVoice || !maleVoice) return -9999;
                    if (voiceIdentity(femaleVoice) === voiceIdentity(maleVoice)) return -9999;

                    var femaleLang = (femaleVoice.lang || '').toLowerCase();
                    var maleLang = (maleVoice.lang || '').toLowerCase();
                    var femaleBaseLang = femaleLang.split('-')[0] || '';
                    var maleBaseLang = maleLang.split('-')[0] || '';
                    var score = 0;

                    if (femaleLang && maleLang && femaleLang === maleLang) {
                        score += 20;
                    } else if (femaleBaseLang && maleBaseLang && femaleBaseLang === maleBaseLang) {
                        score += 6;
                    }

                    score += voiceQualityRank(femaleVoice) + voiceQualityRank(maleVoice);

                    if (inferGender(femaleVoice) === 'female') score += 2;
                    if (inferGender(maleVoice) === 'male') score += 2;

                    return score;
                }

                var femaleCandidates = orderedCandidatesForGender('female');
                var maleCandidates = orderedCandidatesForGender('male');
                var orderedCandidates = sortVoicesByPreference(candidates);

                var preferredPairs = doc._preferredDialogVoicePairs[languageKey] || [];
                for (var pairIndex = 0; pairIndex < preferredPairs.length; pairIndex += 1) {
                    var preferredPair = preferredPairs[pairIndex];
                    var preferredFemale = bestVoiceForTokens(preferredPair.female || []);
                    var preferredMale = bestVoiceForTokens(preferredPair.male || []);
                    if (preferredFemale && preferredMale && voiceIdentity(preferredFemale) !== voiceIdentity(preferredMale)) {
                        return {
                            femaleVoice: preferredFemale,
                            maleVoice: preferredMale,
                            femaleIdentity: voiceIdentity(preferredFemale),
                            maleIdentity: voiceIdentity(preferredMale),
                            femaleCandidateIdentities: femaleCandidates.map(function(voice) { return voiceIdentity(voice); }),
                            maleCandidateIdentities: maleCandidates.map(function(voice) { return voiceIdentity(voice); }),
                        };
                    }
                }

                var bestPair = null;
                femaleCandidates.forEach(function(femaleVoiceCandidate) {
                    maleCandidates.forEach(function(maleVoiceCandidate) {
                        var score = pairScore(femaleVoiceCandidate, maleVoiceCandidate);
                        if (!bestPair || score > bestPair.score) {
                            bestPair = {
                                femaleVoice: femaleVoiceCandidate,
                                maleVoice: maleVoiceCandidate,
                                score: score,
                            };
                        }
                    });
                });

                var femaleVoice = bestPair ? bestPair.femaleVoice : (femaleCandidates[0] || null);
                var femaleKey = voiceIdentity(femaleVoice);
                var maleVoice = bestPair
                    ? bestPair.maleVoice
                    : (maleCandidates.find(function(voice) {
                        return voiceIdentity(voice) !== femaleKey;
                    }) || maleCandidates[0] || null);

                if (!femaleVoice && maleVoice) {
                    femaleVoice = orderedCandidates.find(function(voice) {
                        return voiceIdentity(voice) !== voiceIdentity(maleVoice);
                    }) || maleVoice;
                    femaleKey = voiceIdentity(femaleVoice);
                }

                if (!maleVoice) {
                    maleVoice = orderedCandidates.find(function(voice) {
                        return voiceIdentity(voice) !== femaleKey;
                    }) || femaleVoice || null;
                }

                return {
                    femaleVoice: femaleVoice,
                    maleVoice: maleVoice,
                    femaleIdentity: voiceIdentity(femaleVoice),
                    maleIdentity: voiceIdentity(maleVoice),
                    femaleCandidateIdentities: femaleCandidates.map(function(voice) { return voiceIdentity(voice); }),
                    maleCandidateIdentities: maleCandidates.map(function(voice) { return voiceIdentity(voice); }),
                };
            };

            doc._fcResolveVoiceIdentity = function(identity, language) {
                var voices = synth.getVoices ? synth.getVoices() : [];
                var resolved = findVoiceByIdentity(voices, identity);
                if (resolved) return resolved;
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

                function clearStartWatchdog() {
                    if (doc._fcSpeechStartWatchdog) {
                        parentWindow.clearTimeout(doc._fcSpeechStartWatchdog);
                        doc._fcSpeechStartWatchdog = null;
                    }
                }

            function clearPendingSpeech() {
                clearPendingTimer();
                    clearStartWatchdog();
                clearVoiceHandler();
                    doc._fcSpeechPendingKey = null;
            }

            doc._fcSpeakSpanish = function(config) {
                config = config || {};

                var speechText = (config.text || '').trim();
                var speechRate = config.rate || 1;
                var speechKey = config.key || null;
                var cancelFirst = config.cancelFirst !== false;
                var preferredGender = config.preferredGender || null;
                var randomize = config.randomize !== false;
                var immediate = config.immediate === true;

                if (!speechText) return;
                if (speechKey && (doc._fcSpeechLastKey === speechKey || doc._fcSpeechPendingKey === speechKey)) return;

                clearPendingSpeech();
                doc._fcSpeechPendingKey = speechKey;

                function speakNow() {
                    var voice = pickVoice('es', {
                        preferredGender: preferredGender,
                        randomize: randomize,
                    });
                    var attemptCount = 0;

                    if (cancelFirst) {
                        try {
                            synth.cancel();
                        } catch (error) {
                        }
                    }

                    function queueSpeakAttempt() {
                        clearStartWatchdog();
                        attemptCount += 1;
                        try {
                            if (typeof synth.resume === 'function') {
                                synth.resume();
                            }

                            var utterance = new UtteranceCtor(speechText);
                            var started = false;
                            utterance.lang = voice ? voice.lang : 'es-ES';
                            utterance.rate = speechRate;
                            if (voice) utterance.voice = voice;

                            doc._fcSpeechActiveUtterance = utterance;
                            utterance.onstart = function() {
                                started = true;
                                clearStartWatchdog();
                                doc._fcSpeechPendingKey = null;
                                doc._fcSpeechUnlocked = true;
                                if (speechKey) {
                                    doc._fcSpeechLastKey = speechKey;
                                }
                            };
                            utterance.onend = function() {
                                if (doc._fcSpeechActiveUtterance === utterance) {
                                    doc._fcSpeechActiveUtterance = null;
                                }
                                clearStartWatchdog();
                                if (!started && speechKey && doc._fcSpeechLastKey === speechKey) {
                                    doc._fcSpeechLastKey = null;
                                }
                                if (!started && doc._fcSpeechPendingKey === speechKey) {
                                    doc._fcSpeechPendingKey = null;
                                }
                            };
                            utterance.onerror = function() {
                                if (doc._fcSpeechActiveUtterance === utterance) {
                                    doc._fcSpeechActiveUtterance = null;
                                }
                                clearStartWatchdog();
                                if (!started && attemptCount < 2) {
                                    parentWindow.setTimeout(queueSpeakAttempt, 120);
                                    return;
                                }
                                if (speechKey && doc._fcSpeechLastKey === speechKey) {
                                    doc._fcSpeechLastKey = null;
                                }
                                if (doc._fcSpeechPendingKey === speechKey) {
                                    doc._fcSpeechPendingKey = null;
                                }
                            };

                            doc._fcSpeechStartWatchdog = parentWindow.setTimeout(function() {
                                if (started) return;
                                if (doc._fcSpeechActiveUtterance === utterance) {
                                    doc._fcSpeechActiveUtterance = null;
                                }
                                if (attemptCount < 2) {
                                    try {
                                        synth.cancel();
                                    } catch (error) {
                                    }
                                    parentWindow.setTimeout(queueSpeakAttempt, 120);
                                    return;
                                }
                                if (speechKey && doc._fcSpeechLastKey === speechKey) {
                                    doc._fcSpeechLastKey = null;
                                }
                                if (doc._fcSpeechPendingKey === speechKey) {
                                    doc._fcSpeechPendingKey = null;
                                }
                            }, immediate ? 900 : 1200);

                            synth.speak(utterance);
                        } catch (error) {
                            clearStartWatchdog();
                            if (speechKey) {
                                doc._fcSpeechLastKey = null;
                            }
                            if (doc._fcSpeechPendingKey === speechKey) {
                                doc._fcSpeechPendingKey = null;
                            }
                        }
                    }

                    doc._fcSpeechPendingTimer = parentWindow.setTimeout(function() {
                        doc._fcSpeechPendingTimer = null;
                        queueSpeakAttempt();
                    }, immediate ? 0 : (cancelFirst ? 60 : 0));
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
            var AudioCtx = window.parent.AudioContext || window.parent.webkitAudioContext || window.AudioContext || window.webkitAudioContext;
            var cueAudioSrc = 'data:audio/wav;base64,UklGRiYfAABXQVZFZm10IBAAAAABAAEAIlYAAESsAAACABAAZGF0YQIfAAAAAAwALwBdAIoApQChAHYAJQC2/zj/wf5p/kT+Yv7H/mz/PQAfAfEBjQLXArsCMgJKARsA0f6Y/aH8GPwY/Kr8w/1B//MAnAL9A98EGAWYBGcDqQGY/3v9ovtT+sb5F/pF+y39kf8eAncERQZABzoHLQY0BI8Bm/6/+2X55/eF91T4QfoO/VwAtwOlBrcInAkrCWkHjgT5ACn9pvnx9nL1aPXe9qn5a/2gAbYFFglBC+IL2ApACG8E6P9K+z33V/QG84PzxvWH+UX+WQMQCLsL0A3+DTMMpwjRA1z+B/mU9KnxtvDm8Rj14vme/4AFtgqBDlEQ3Q8rDZMIswJb/Gr2u/H87pbuovDf9L76cQEKCJoNVhGwEm4RtA3/BxUB7PmD88TuYey47MXvJfUe/LoD6wqrECcU2hShEsMN5gb7/hr3YPDC6+7pLetd7/D1Af5yBhYO1xPgFr0WZxNPDUYFafzy8xPtyei15wbqdO9D92IAjQl6EQoXbRlGGLMTUQwgA2f5gfCv6e3lyeVS6RPwIfk9A/4MBxUwGrobZRl6E8UKeAAC9tjsR+ZB4zzkHulB8Yn7iAa4EKcYNR21HQwasxKrCFb9RvIJ6e/i2+Af43XpAfN1/jkKqBRJHAQgSh8sGlkRBAbA+ULuKOW9383egeJf6lX13wFBDrwY1h+JImogvRlnD9QCxPUI6knhxtwp3W/i4+s6+L8FkRLhHDojsCQFIbMY3Qwk/2/xq+WC3R7aAdzz4gPurPsHChYXASFfJmcmDiELF7wJ+vrR7D/h59nY12XbF+TB8KP/qg6/GwclMCmcJ3ogwBQLBmX2/ufb3JDWCdZg2+HlGvQUBJcTdCDcKJkrQCg/H9ERzwF08Qjjk9iS08rUItx86B742AhXGHEkditqLCwndxzJDTD9++xt32rWNNM/1hzfkey7/FkNHBzyJloskiu1JLoYSwmS+OHoadzp1GzTJ9hx4tvwYAG2EZMfCCnELEEq2SG4FLMEB/QG5cjZ39Mf1H3aF+ZP9QMG4hWzIq0qsix8KJ8efRAOAJ7vduGR11DTStU73QXq4PmVCtEZcyXbKyYsRyYRGxUMavti6zreydU70+zWWOAv7oL+Cg95HcwnkSwfK6kjOReLB9L2X+dc23XUotP/2M3ji/IoA1UT0CC3KcwsoSmoICAT7QJT8qDj4tia04PUftuQ5wv3xQdrF8wjLyuLLLEnTR3SDkf++e0v4NXWOdPd1WHeluul+04MQBtlJi8szytTJaEZXAqm+dLpFt051VTTqteh4dXvSQC0EMoelSi2LJsqjSKuFckFFfXn5V3aE9Tq0+fZNeVA9O4E7BT/IVQqwizwKGkfgBEmAaPwReIM2GbT+dSN3BPpzPiFCesY1ySfK1Is1SbuGyENgPxc7PTeKdY104DWld8w7Wv9AQ6kHEgncixnK08kJhieCOT3Suj/27rUf9N52PbigfERAlcSDyBOKcksBSpkIRsUBARe83rkbdnC00PU39qo5vr1sgZ7FiEj4SqlLC8oHh7ZD1//+u724EbXRdOB1avdn+qP+kALYBrTJf4rBizqJYQaawu7+sbqx92P1ULTNNfW4NLuM/+vD/0dHCiiLO4qPSOhFt0GJfbM5vfaTdS801fZV+Qz89gD9BNHIfYpyixfKS4ggBI9AqvxGOON2ITTr9Tl2yXouPdzCAEYNSRcK3csXifGHCsOl/1Y7bTfkNY10xrW19407FT89wzLG78mSyypK/AkDxmwCff4Oemo3AbVYtP41yTievD5AFcRSh/eKMAsYyocIhMVGQVr9Fnl/tny0wrURdrD5ev0nQWIFXEijSq5LKgo6h7dEHUA/u/C4b3XV9Ms1frcq+l6+TEKfRk6JcYrNyx8JmMbeAzR+77rft7s1TjTw9YQ4NHtG/6pDisdnCeGLDor5iOQF/EHNve155fbjtSU083YfuMp8sEC+BKJIJEpzCzHKe4gfRNUA7Xy8OMV2ajTa9RC2zrnpvZgBxMXjiMTK5Ys4CeaHTMPrv5Y7njg/tY907rVHd476z776wvuGjAmHizkK4sl9RnACgz6K+pX3VjVTdN+11bhde/j/1QQfx5pKK8suirPIggWLwZ59Tvmldoo1NjTsdnj5N3zhwSRFLwhMirGLBopsh/eEYwBBPGS4jvYcNPd1E/cu+hm+CAJlRicJIcrYCwIJz4cgw3n/LjsOt9P1jTTWdZO39PsBP2fDVUcFydkLIAriyR8GAMJSfii6D3c1dRz00nYqOIg8aoB+RHHHyUpxywoKqkhdxRqBMHzy+Si2dPTLtSl2lPmlvVMBiIW4SLDKq0sXChqHjkQxv9a70DhcddL02HVad1F6in63AoNGpsl6isZLCEm1xrOCyH7IesK3rDVPtMK14zgc+7M/k8PsB3tJ5gsCyt8I/oWQweK9iLnMttk1KzTI9kH5NHycQOXEwIh0SnLLIYpdSDdEqQCDfJn47/YkNOV1KjbzudT9w4IqRf4I0IrgyyOJxUdjQ7+/bbt+9+41jfT9tWS3tjr7vuUDHobiyY7LMArKiVkGRQKXfmS6ejcI9VZ08rX1+Ea8JMA+BAAH7QouyyEKl4ibhWABc70rOU12gXU99MO2nDlh/Q3BS0VLyJsKr4s0ig0HzwR3ABe8A7i69dg0w7VutxS6RT5zAkoGQAlsCtHLLAmtBvbDDf8GuzD3g/WNtOc1sjfc+21/UcO3RxsJ3osVSskJOgXVgic9wzo1Nun1IfTm9gu48fxWgKaEkIgainLLOspMyHZE7oDF/NA5EjZt9NU1Ajb5eZC9voGuhZPI/YqnywOKOcdlA8V/7buweAo10HTmNXa3eDq2PqHC5wa+iUMLPgrwyVJGiQLcvqF6pjdeNVG01LXC+EW73z/9A8zHjwoqCzZKg8jYRaVBt71kObO2j3Ux9N82ZHkevMhBDUUeCEPKsksQin7Hz0S8wFl8eDia9h708LUEdxj6AH4uwg/GGAkbytuLDonjhzlDU79Fe2B33XWNNM01gjfduye/D0NBRzkJlYsmCvGJNIYaAmv+Proe9zx1GnTGdhb4r/wQwGbEX4f/CjDLEsq7CHSFNAEJPQe5djZ5dMZ1G3a/+Uy9eYFyBWgIqQqtCyIKLUemRAsALnvjOGd11LTQtUo3evpw/l4CrkZYyXVKyssViYpGzEMh/t8607e09U60+DWQ+AU7mX+7g5jHb4njiwnK7ojUheoB+72d+dt23zUntPx2Lbjb/IKAzoTvCCsKcwsrCm8IDoTCgNv8rbj8die03zUbdt35+72qAdSF7ojJyuOLL4nYx3uDmX+FO5D4ODWOtPT1U7efOuH+zEMKRtWJiss1StjJbkZeArD+evpKN1C1VLTndeM4bnvLACZELUeiCi0LKQqoCLIFeYFMvX/5W3aGdTl09jZHuUk9NAE0hTsIUsqwyz8KH4fmxFDAb/wW+IZ2GnT8dR73Pror/hoCdIYxiSYK1Ys5CYFHD0Nnvx27AjfNNY003XWgd8V7U795Q2OHDonbixvK2AkPxi7CAH4Y+gR3MLUe9Nr2ODiZfHzAT0S+x9CKcksDyp4ITUUIQR685HkfNnH0z3UztqQ5t71lQZhFg8j2SqoLDwoMx70D3z/Fu8L4VLXRtN41Zjdhepy+iQLSRrDJfgrDCz6JZwahwvY+uDq2t2Y1UHTKNfB4LbuFf+UD+cdDiifLPYqTyO6FvoGQvbl5gjbVNS300jZQOQX87oD2RMzIespyyxqKUIgmhJaAsfxLuOb2IfTp9TU2wzonPdWCOgXJCRVK3osbCfdHEcOtf1z7cjfnNY20w/Ww94a7Df82wy0G7AmRyywKwAlKBnMCRT5Uum63A7VYNPr1w7iXvDcADwRNB/SKL4sbCovIi0VNwWH9HDlDtr30wXUNdqs5c70gAVuFV4ihCq7LLQoAB/4EJMAGvDX4crXWdMj1ejckuld+RQKZBkqJcArOyyLJnoblAzu+9jrkt721TfTuNb737bt/v2NDhUdjieDLEIr+COpFw4IU/fO56jbldSQ07/YZ+MN8qQC3RJ1IIYpyyzRKQIhlxNxA9HyB+Qj2azTZNQy2yLnivZDB/oWfCMLK5gs7SewHU8PzP5z7ozgCtc+07DVCt4h6yH7zgvXGiEmGSzqK5slDRrcCin6Repp3WHVS9Nx10DhWu/G/zkQah5cKK0swyrhIiIWTAaW9VPmpdou1NPTotnL5MHzagR3FKkhKCrHLCUpxx/5EaoBIPGo4knYc9PV1D3couhJ+AMJfBiLJIArZCwXJ1Ucnw0E/dPsTt9Z1jTTT9Y637js5/yDDT4cCCdgLIcrnCSVGCAJZvi76E/c3dRw0zvYkuIE8YwB3hGyHxopxiwyKrwhkRSHBN3z4+Sx2djTKNSV2jvmefUvBggWzyK6Kq8saSh/HlQQ4/9171bhftdN01jVV90r6gz6wAr1GYsl5CseLDAm7hrrCz77O+sd3rrVPdP+1njgWO6u/jMPmh3gJ5YsEyuOIxMXYAem9jrnQttr1KjTFdnw47XyVAN9E+4gxynMLJEpiSD4EsECKfJ+483YlNOO1Jfbtec29/EHkBfmIzorhiycJysdqQ4b/tHtEODD1jjT7NV+3r7r0ft4DGMbfCY3LMYrOiV9GTEKevmr6frcLNVX073XwuH+73UA3RDqHqgouSyNKnEiiBWdBev0w+VF2grU8tP+2Vnla/QZBRMVHCJjKsAs3ihKH1cR+QB68CTi+Ndi0wbVqNw56ff4sAkPGfAkqStLLL8myxv3DFT8NOzX3hrWNdOQ1rTfWO2X/SsOxhxeJ3csXCs1JAEYcwi49yXo5duv1ITTjdgY46vxPQKAEi4gXynKLPYpRyH0E9gDM/NX5FfZvNNN1PfazOYl9t0GoRY9I+4qoiwcKP0drw8z/9Lu1uA010LTj9XH3cbqu/prC4Qa6iUGLP4r0yVgGkALj/qf6qvdgdVF00bX9uD67l//2Q8eHi8opSzhKiEjexayBvr1qObf2kPUwtNt2XrkXvMEBBsUZCEFKsksTikPIFcSEQKB8fbiedh/07rU/9tK6OT3nggmGE8kZytyLEgnpBwBDmv9MO2V34DWNdMp1vTeXOyA/CEN7hvVJlIsnyvXJOsYhQnM+BPpjdz51GbTDNhF4qPwJgGAEWkf8CjCLFQq/yHsFO4EQPQ15efZ6tMT1F3a5+UV9ckFrhWNIpsqtiyVKMoetBBJANXvoeGq11TTOdUW3dLppvlcCqEZUyXPKy8sZSZAG04MpfuW62He3dU509XWL+D57Uf+0g5NHbEniywvK8wjaxfFBwv3kOd+24PUmtPi2KDjU/LtAiATqCChKcwstynQIFUTKAOL8s3j/9ii03XUXNtf59L2iwc5F6kjHyuRLMwneR0KD4L+L+5Y4OzWO9PJ1TreYutq+xUMERtHJiYs2ytzJdEZlQrg+QXqO91K1VDTkdd24Z7vDgB9EJ8efCiyLK0qsyLiFQMGT/UX5n3aH9Tf08jZBuUH9LMEuBTZIUEqxCwIKZMfthFgAdvwceIn2GzT6dRp3OHokvhLCboYtSSSK1os8iYcHFkNu/yR7BzfP9Y002rWbd/77DD9yQ13HCwnaix2K3EkVxjYCB74fOgi3MrUeNNd2MriSvHWASIS5h83KcgsGSqMIVAUPgSW86jki9nM0zfUvtp35sH1dwZIFv0i0CqqLEkoSR4QEJr/Me8g4V/XSNNu1YXdbOpV+gcLMRqzJfMrESwJJrMapAv1+vrq7d2i1UDTHNes4Jvu+P54D9EdASicLP4qYSPUFhcHX/b95hnbWtSz0znZKeT78p0DvxMfIeEpyyx1KVcgtRJ4AuPxReOp2IvToNTC2/Pnf/c5CM8XEiRNK34seifzHGMO0v2O7dzfp9Y20wXWr97/6xr8vwydG6ImQiy2KxElQBnpCTH5bOnM3BbVXdPe1/jhQ/C/ACERHx/GKL0sdipCIkcVVAWj9IjlHtr80//TJdqU5bL0YgVUFUwieiq8LMAoFR8TEbAANfDt4dfXXNMb1dbceOlA+fcJTBkZJbkrQCyaJpIbsAwL/PLrpd4A1jbTrdbn35vt4f1xDv4cgCeALEorCiTCFysIcPfn57rbnNSN07DYUOPx8YYCwxJhIHspyyzcKRYhshOOA+3yHuQy2bHTXdQh2wnnbfYmB+AWaiMDK5ss+yfGHWoP6f6O7qHgFtc/06fV990H6wT7sgu/GhEmFCzwK6slJRr5Ckb6X+p83WrVSdNl1yvhPu+o/x0QVB5PKKsszCr0IjsWaQaz9Wvmtto01M7Tk9m05KTzTQRdFJUhHirHLDEp3B8UEscBPPG+4lbYd9PN1Cvciegs+OYIZBh6JHkraCwlJ2wcuw0i/e3sYt9k1jTTRNYm357syvxnDScc+iZcLI4rrSStGD0Jg/jU6GDc5dRt0y7YfOLo8G8BwxGdHw4pxSw8Ks8hqxSlBPnz+uTB2d3TItSF2iPmXfUSBu4VvCKxKrEsdiiVHnAQAACQ72vhitdP00/VRN0S6u75owrdGXsl3isjLD8mBhsHDFv7Vesx3sTVO9Py1mPgPe6R/hgPhB3SJ5MsGyugIywXfQfD9lPnU9ty1KTTBtnZ45nyNgNiE9ogvCnMLJwpniATE94CRfKU49vYmNOH1IbbnOca99QHdxfVIzMriSyqJ0IdxA45/uztJODP1jnT4tVr3qPrs/tcDEwbbSYyLMwrSiWVGU0Kl/nF6QzdNNVV07HXrOHj71gAwhDVHpsotyyWKoQioRW6BQf12+VV2hDU7NPv2UHlTvT8BPkUCSJZKsEs6ihfH3IRFwGW8DriBdhl0/3Ultwg6dr4kwn3GN8koytPLM4m4hsTDXL8Tuzq3iTWNdOF1p/fPe16/Q8OsBxQJ3MsZCtGJBkYkAjV9z7o9tu21IDTgNgC44/xHwJlEhkgUynKLAAqWyEOFPUDUPNu5GbZwNNH1OfatOYJ9sAGiBYqI+UqpCwpKBMeyw9Q/+3u6+BA10TThtW03azqnvpOC2wa2yUBLAQs4iV4Gl0LrPq56r7ditVD0zrX4eDf7kH/vQ8IHiIooyzqKjQjlBbPBhf2wObv2krUvtNe2WPkQfPmAwEUUSH7KcosWSkkIHISLgKd8Q3jhtiC07PU7tsx6Mf3gQgNGD4kYCt1LFcnuxwdD6D+Su5t4PjWPNO/1SfeSOtN+/kL+ho4JiEs4SuDJekZsQr9+R7qTd1T1U7ThNdh4YPv8v9iEIoebyiwLLYqxSL7FSAGa/Uv5o3aJdTa07nZ7+Tr85YEnhTGITcqxSwUKagfzxF9Af/wn+Je2KjTItWW3PXohfgYCV8YOiQCK8krdSbHGz8N5vwD7czfGtce1ELXEuBR7SX9Vg2lGxImLCs/Km8jshetCHv4XOls3VPWDtXF2c7jwPGnAU0RgR5vJ9kqSSgdIHoTJwRI9BLmgNsK1m/WoNy75zP2AQbyFPAgUCgPKvAlihwuD7z/WvAu4w3aOtY82Mjfzuue+iYKPRjsIrgo1Cg/I8MY2Qp0+7jss+AR2eDWbNoy4/jv8/4MDigbdSSoKC8nQCDWFIsGXvds6afejdj21/Tc0uYt9CYDqBGsHYglJCgnJf4czxBOAoPzfeYM3X/YddnL35rqX/gsB/IUxh8mJjInxyKFGboMMP7u7/Hj49vi2Fbb5eJ+7oL8+grkF3IhUibYJRgg4hWlCDv6puzL4SvbsdmP3TfmcvKKAIcOdxqwIg8mHiQmHSESnAR79rTpEODk2ufaFuC16Wn2bATKEaYcfiNgJQsi+hlODqsA+PId58DeCtt93OLiU+1X+h4IvBRvHt8jTCSqH6EWdgrd/Lvv5eTc3Zrba97o5QTxMf6VC1YXzx/UI9kiBB0mE6MGPPnM7BHjZN2N3KfgHOm+9OkByg6TGcYgYyMQISMalg/jAtH1Meqj4VTd3d0o43TsdPh5BbURcRtUIY8i+R4TF/sLQP+m8u/nmuCq3YTf4+Xj7xv81ghPFOwcfCFfIZwc3xNiCML7we8K5vjfX9544dDoXvOo//cLkxYEHkIh2x8EGpEQ1QR1+CnthOS533DfsePh69r2EQPUDn8YuR6oIAkePBc2DWABYfXj6l7j29/U4CXmDe9M+k4GaBEOGg0ftR/yG0wU2AkL/ozy9OiY4lngheLL6Enyqf1VCa0TQBsDH3AeoBlCEYEG4Pr9713nMeIw4XrkmOuJ9egAIAyfFRUcnR7fHB0XJg48A+j3u+0g5ibiV+Kq5oLuxPgABKcOPBeOHOIdCxtxFAMLEwAp9cjrPuV04srjDOl+8e/76QbmEIEYrBzWHPsYqBHlBw/9qvIn6rbkFuN/5ZfrgvQC/5wJ2BJuGXQcgRu6FswO0wQ3+nDw2+iF5AfkbudA7oX38QERDHsUBBrqG+oZUBTlC9kBk/eA7uTnqeRA5ZDp/fB8+rcERA7MFUUaEhsZGMcRAAn//in13exC5x3luuba68XzXv1MBzAQyxY0GvQZFxYpDyQGS/z+8ojr8ubd5W3oQ+6O9iIAqgnSEXgX1RmWGOwTfwxaA8b5F/GD6vLm4uZR6sPwT/nCAssLKRPVFysZ/xahEdIJrAB293jvzek/5yboXuxP8//7NQWrDTIU5Bc+GDgVQA8tByL+YPUh7mXp0+eh6Yvu3/WW/ncHRw/vFKgXFBdIE9EMlgTA+4jzFO1J6aroTevP8Gr4CwGBCZwQYRUnF7IVORFeChcCjvny8VLsdOm96SDtIPPm+loDUAuqEYoVZRYiFBIP7ge3/5H3n/DY6+TpBusT73f1Tf17Bd8McRJsFWgVahLdDIwFfP3N9ZHvpeuT6n3sHfHL95j/agctDvESDBU3FJIQogo9A237RvTJ7rfre+sb7jbzFPq9ASIJOQ8sE28U2RKkDmkICgGN+f3yRO4I7Jbs1+9V9Ur8uwOgCgMQJROaE1QRpgw7Bvn+4/f18QLulezd7avxc/dm/ooF4QuKEOESlBKxD6IKHgQP/XD2LPEA7ljtSu+N84j5YQAmB+UM0hBiEmIR+A2fCBkCUfs39aPwOe5L7tTwd/WM+zcCjQirDdwQsBENEC8MpAYzAMT5OfRY8KruaO908mD3eP3jA7wJNA6rEM4Qmg5gCrkEc/5q+HfzSfBO76jwI/RB+Uj/YAWzCoEORhDEDxINkQjlAtn8Rffw8nHwIPAF8tn1E/v0AKwGbwuVDq8PmA57C8kGLAFt+1j2ovLN8BjxdvOP99D8eQLEB/MLcw7sDlEN3gkQBZX/MPqi9YvyWPEx8vX0Pvlx/tQDqAhADB8OBA72C0EIawMk/iX5IvWp8g3yZPN69t768/8BBVYJWAyeDf0MjgqrBuEB3PxN+Nj09vLn8qr0//dr/E8B/gXPCT4M9AzcCyAJIwV1AMD7qffB9G/z3vP99X353v2EAskGFQr1CygMqgqyB64DLv/S+jf32vQO9O30Vfft+jT/jgNjBysKgws/C2wJTAZRAg3+FPr29h/1z/QN9qz4S/xlAGwEzQcSCuwKQAopCPMEEwEV/Yb55PaM9ar1OPf7+ZD9cgEbBQcIzwk2CjEJ6AatA/f/Sfwm+f/2HPaa9mf4Pvu4/lcCnQUTCGUJZgkZCK4FfwL+/qj79fhB98n2mveT+W38v/8SA/EF9gfbCIMI/QaCBG0BLf41++74qPeP96H4t/qE/aEAogMZBrIHNQiTB+UFagN8AIX97foQ+S/4Zvir+c37f/5fAQYEGAZLB3gHmwbVBGkCrv8G/c/6+r5hfkz+qz7u/0SAGACUwSlBSoG0wWuBOcCvgCE/oX8CftC+kr6HPuZ/Ir+pgCkAj4EOwV6BfYExQMRAhsAKv6B/Fr73foY+wD8cv05/xQBwQIGBLYEvQQbBOsCWAGe//j9ofzI+4j76PvX/DL+x/9aAbcCrgMdBPgDRwMmAr8ARf/s/eP8T/xA/Lb8n/3W/i8AewGKAjoDdAMyA4ACegFHABL/BP5E/en8/vx8/VD+Wv9zAHUBPQKwAsACbwLKAesA9P8E/z/+vv2R/bv9NP7o/r3/kgBNAdMBEwIIArYBKwF8AMT/HP+Z/k7+Qv50/tn+Y//7/4wAAwFQAWoBUgEMAaYALwC6/1b/D//u/vX+If9n/73/FABiAJsAuQC7AKIAdgA/AAYA1f+v/5v/mf+m/77/2v/1/woAFgAZABQACgA=';

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

            function primeCueAudio() {
                if (!doc._fcCueAudioElement) {
                    try {
                        var cueAudioElement = new Audio(cueAudioSrc);
                        cueAudioElement.preload = 'auto';
                        cueAudioElement.playsInline = true;
                        cueAudioElement.setAttribute('playsinline', '');
                        cueAudioElement.style.display = 'none';
                        if (doc.body && !cueAudioElement.parentNode) {
                            doc.body.appendChild(cueAudioElement);
                        }
                        doc._fcCueAudioElement = cueAudioElement;
                    } catch (error) {
                    }
                }

                doc._fcCreateCueAudioInstance = function() {
                    var sourceAudio = doc._fcCueAudioElement;
                    if (!sourceAudio || !sourceAudio.src) return null;
                    try {
                        var cueAudio = sourceAudio.cloneNode(true);
                        cueAudio.preload = 'auto';
                        cueAudio.playsInline = true;
                        cueAudio.setAttribute('playsinline', '');
                        cueAudio.style.display = 'none';
                        if (doc.body) {
                            doc.body.appendChild(cueAudio);
                        }
                        return cueAudio;
                    } catch (error) {
                        return null;
                    }
                };

                if (doc._fcCueAudioElement) {
                    try {
                        var audioEl = doc._fcCueAudioElement;
                        audioEl.volume = 1;
                        audioEl.currentTime = 0;
                        var playAttempt = audioEl.play();
                        if (playAttempt && typeof playAttempt.then === 'function') {
                            playAttempt.then(function() {
                                audioEl.pause();
                                audioEl.currentTime = 0;
                                doc._fcCueAudioPrimed = true;
                            }).catch(function() {
                            });
                        } else {
                            audioEl.pause();
                            audioEl.currentTime = 0;
                            doc._fcCueAudioPrimed = true;
                        }
                    } catch (error) {
                    }
                }

                if (!AudioCtx) return;

                try {
                    if (!doc._fcCueAudioContext) {
                        doc._fcCueAudioContext = new AudioCtx();
                    }

                    var audioContext = doc._fcCueAudioContext;

                    function unlockContext() {
                        var buffer = audioContext.createBuffer(1, 1, Math.max(22050, audioContext.sampleRate || 44100));
                        var source = audioContext.createBufferSource();
                        var gainNode = audioContext.createGain();
                        gainNode.gain.value = 0.00001;
                        source.buffer = buffer;
                        source.connect(gainNode);
                        gainNode.connect(audioContext.destination);
                        source.start(0);
                        source.stop(0.01);
                        doc._fcCueAudioPrimed = true;
                    }

                    if (audioContext.state === 'suspended' && typeof audioContext.resume === 'function') {
                        audioContext.resume().then(unlockContext).catch(function() {
                        });
                        return;
                    }

                    unlockContext();
                } catch (error) {
                }
            }

            doc._fcPrimeCueAudioNow = primeCueAudio;

            doc._fcSpeechPrimeHandler = function() {
                primeSpeech();
                primeCueAudio();
            };

            ['pointerdown', 'mousedown', 'touchstart', 'touchend', 'click', 'keydown'].forEach(function(eventName) {
                doc.body.addEventListener(eventName, doc._fcSpeechPrimeHandler, true);
            });
            doc._fcSpeechPrimingAttached = true;
        })();
        </script>
        """,
        height=0,
    )


def toggle_ai_examples_en():
    st.session_state.ai_examples_show_english = not st.session_state.ai_examples_show_english


def toggle_auto_speak_spanish():
    st.session_state.auto_speak_spanish = not st.session_state.auto_speak_spanish
    if st.session_state.auto_speak_spanish:
        st.session_state.auto_speak_spanish_generation += 1
        if st.session_state.ai_examples_sentences:
            st.session_state.ai_examples_autoplay_generation += 1
    store_active_person_prefs()
    save_prefs(current_prefs())


def render_speaker_button(text, icon_font_size="1.15rem"):
    speech_text = strip_spoken_text(text)
    speech_rate = speech_rate_value()
    components.html(
        f"""
        <style>
        html, body {{
            width: 100%;
            height: 3.2rem;
            min-height: 3.2rem;
            overflow: hidden;
        }}
        body {{
            margin: 0;
            background: transparent;
            display: flex;
            justify-content: center;
            align-items: center;
            width: 100%;
            min-width: 0;
            min-height: 3.2rem;
            box-sizing: border-box;
        }}
        #speak-btn {{
            width: 100%;
            height: 3.2rem;
            min-width: 0;
            min-height: 3.2rem;
            font-size: {icon_font_size};
            font-weight: 600;
            border-radius: 0.75rem;
            border: 2px solid {t['info']};
            background-color: {t['info_light']};
            color: {t['info']};
            cursor: pointer;
            font-family: 'DM Sans', sans-serif;
            display: flex;
            align-items: center;
            justify-content: center;
            line-height: 1;
            margin: 0;
            padding: 0.22rem 0 0 0;
            box-sizing: border-box;
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
            var suppressClickUntil = 0;

            if (!button || !doc || !speechText) return;

            function speakFromTap(event) {{
                var now = Date.now();
                if (event) {{
                    if (event.type === 'click' && now < suppressClickUntil) {{
                        event.preventDefault();
                        event.stopPropagation();
                        if (typeof event.stopImmediatePropagation === 'function') {{
                            event.stopImmediatePropagation();
                        }}
                        return;
                    }}
                    if (event.type === 'touchend') {{
                        suppressClickUntil = now + 700;
                    }}
                    event.preventDefault();
                    event.stopPropagation();
                    if (typeof event.stopImmediatePropagation === 'function') {{
                        event.stopImmediatePropagation();
                    }}
                }}
                if (typeof doc._fcSpeakSpanish !== 'function') return;
                doc._fcSpeakSpanish({{
                    text: speechText,
                    rate: speechRate,
                    cancelFirst: true,
                    immediate: true,
                }});
            }}

            button.addEventListener('click', speakFromTap);
            button.addEventListener('touchend', speakFromTap);
        }})();
        </script>
        """,
        height=64,
    )


def render_auto_speak_button(is_on):
    if is_on:
        bg_color = "#ffe0f5"
        border_color = "#ff1aaa"
        text_color = "#ff1aaa"
    else:
        bg_color = "rgba(128,128,128,0.12)"
        border_color = "rgba(128,128,128,0.35)"
        text_color = "rgba(140,140,140,0.8)"
    components.html(
        f"""
        <style>
        html, body {{
            width: 100%;
            height: 3.2rem;
            min-height: 3.2rem;
            overflow: hidden;
        }}
        body {{
            margin: 0;
            background: transparent;
            display: flex;
            justify-content: center;
            align-items: center;
            width: 100%;
            min-width: 0;
            min-height: 3.2rem;
            box-sizing: border-box;
        }}
        #autoplay-btn {{
            width: 100%;
            height: 3.2rem;
            min-width: 0;
            min-height: 3.2rem;
            font-size: 0.65rem;
            font-weight: 700;
            letter-spacing: 0.06em;
            border-radius: 0.75rem;
            border: 2px solid {border_color};
            background-color: {bg_color};
            color: {text_color};
            cursor: pointer;
            font-family: 'DM Sans', sans-serif;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            gap: 0;
            line-height: 1.35;
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        </style>
        <button id="autoplay-btn" type="button"><span>AUTO</span><span>PLAY</span></button>
        <script>
        (function() {{
            var parentWindow = window.parent;
            var doc = parentWindow.document;
            var synth = parentWindow.speechSynthesis || window.speechSynthesis;
            var UtteranceCtor = parentWindow.SpeechSynthesisUtterance || window.SpeechSynthesisUtterance;
            var button = document.getElementById('autoplay-btn');
            var suppressClickUntil = 0;
            if (!button || !doc) return;

            function handleTap(event) {{
                var now = Date.now();
                if (event) {{
                    if (event.type === 'click' && now < suppressClickUntil) {{
                        event.preventDefault();
                        event.stopPropagation();
                        if (typeof event.stopImmediatePropagation === 'function') event.stopImmediatePropagation();
                        return;
                    }}
                    if (event.type === 'touchend') suppressClickUntil = now + 700;
                    event.preventDefault();
                    event.stopPropagation();
                    if (typeof event.stopImmediatePropagation === 'function') event.stopImmediatePropagation();
                }}
                if (synth && UtteranceCtor && !doc._fcSpeechUnlocked) {{
                    try {{
                        var primer = new UtteranceCtor('.');
                        primer.volume = 0;
                        primer.rate = 3;
                        primer.onstart = function() {{ doc._fcSpeechUnlocked = true; }};
                        synth.speak(primer);
                        setTimeout(function() {{ try {{ synth.cancel(); }} catch(e) {{}} }}, 150);
                    }} catch(e) {{}}
                }}
                var hiddenBtn = doc.querySelector('.st-key-autospeak_toggle_hidden_wrap button');
                if (hiddenBtn) hiddenBtn.click();
            }}

            button.addEventListener('click', handleTap);
            button.addEventListener('touchend', handleTap);
        }})();
        </script>
        """,
        height=64,
    )


def render_ai_cycle_button(disabled=False):
    disabled_attr = "disabled" if disabled else ""
    cursor_value = "default" if disabled else "pointer"
    opacity_value = "0.42" if disabled else "1"
    components.html(
        f"""
        <style>
        body {{
            margin: 0;
            background: transparent;
            display: flex;
            justify-content: flex-start;
            align-items: center;
            min-height: 3.2rem;
            width: 100%;
            padding-left: 0.34rem;
            box-sizing: border-box;
        }}
        #ai-cycle-btn {{
            width: 3.6rem;
            min-height: 3.2rem;
            font-size: 1.55rem;
            font-weight: 700;
            border-radius: 0.75rem;
            border: 2px solid {BUTTON_COLORS['blue']['border']};
            background: {BUTTON_COLORS['blue']['bg']};
            color: {BUTTON_COLORS['blue']['fg']};
            cursor: {cursor_value};
            font-family: 'DM Sans', sans-serif;
            opacity: {opacity_value};
            margin: 0;
        }}
        </style>
        <button id="ai-cycle-btn" type="button" {disabled_attr}>→</button>
        <script>
        (function() {{
            var parentWindow = window.parent;
            var doc = parentWindow.document;
            var button = document.getElementById('ai-cycle-btn');
            if (!button || !doc || button.disabled) return;

            function triggerCycle(event) {{
                if (event) {{
                    event.preventDefault();
                    event.stopPropagation();
                    if (typeof event.stopImmediatePropagation === 'function') {{
                        event.stopImmediatePropagation();
                    }}
                }}
                var hiddenButton = doc.querySelector('.st-key-aicycle_hidden_wrap button');
                if (!hiddenButton) return;
                hiddenButton.click();
            }}

            button.addEventListener('click', triggerCycle);
            button.addEventListener('touchend', triggerCycle);
        }})();
        </script>
        """,
        height=60,
    )


def render_ai_action_buttons(cycle_disabled=False, reload_disabled=False, en_disabled=False, en_is_on=False):
    cycle_disabled_attr = "disabled" if cycle_disabled else ""
    reload_disabled_attr = "disabled" if reload_disabled else ""
    en_disabled_attr = "disabled" if en_disabled else ""
    cycle_cursor = "default" if cycle_disabled else "pointer"
    reload_cursor = "default" if reload_disabled else "pointer"
    en_cursor = "default" if en_disabled else "pointer"
    cycle_opacity = "0.42" if cycle_disabled else "1"
    reload_opacity = "0.42" if reload_disabled else "1"
    en_opacity = "0.42" if en_disabled else "1"
    if reload_disabled:
        reload_border = "color-mix(in srgb, " + t['border'] + " 60%, " + t['card_bg'] + " 40%)"
        reload_bg = "color-mix(in srgb, " + t['card_bg'] + " 88%, " + t['bg'] + " 12%)"
        reload_fg = "color-mix(in srgb, " + t['fg'] + " 55%, " + t['card_bg'] + " 45%)"
    else:
        reload_border = BUTTON_COLORS['green']['border']
        reload_bg = "color-mix(in srgb, " + BUTTON_COLORS['green']['bg'] + " 68%, " + t['card_bg'] + " 32%)"
        reload_fg = BUTTON_COLORS['green']['border']
    if en_is_on and not en_disabled:
        en_border = "#ff8800"
        en_bg = "rgba(255,136,0,0.13)"
        en_fg = "#ff8800"
    else:
        en_border = "rgba(128,128,128,0.35)"
        en_bg = "rgba(128,128,128,0.08)"
        en_fg = "rgba(120,120,120,0.85)"
    components.html(
        f"""
        <style>
        html, body {{
            width: 100%;
            height: 3.2rem;
            min-height: 3.2rem;
            overflow: hidden;
        }}
        body {{
            margin: 0;
            background: transparent;
            width: 100%;
            min-width: 0;
            max-width: none;
            min-height: 3.2rem;
            box-sizing: border-box;
        }}
        .ai-action-row {{
            width: 100%;
            height: 3.2rem;
            min-width: 0;
            max-width: none;
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            column-gap: 0.26rem;
            align-items: center;
            justify-items: stretch;
        }}
        .ai-action-btn {{
            width: 100%;
            height: 3.2rem;
            min-width: 0;
            min-height: 3.2rem;
            border-radius: 0.75rem;
            font-family: 'DM Sans', sans-serif;
            display: flex;
            align-items: center;
            justify-content: center;
            line-height: 1;
            margin: 0;
            padding: 0.18rem 0 0 0;
            box-sizing: border-box;
        }}
        #ai-cycle-btn {{
            font-size: 1.55rem;
            font-weight: 700;
            border: 2px solid {BUTTON_COLORS['blue']['border']};
            background: {BUTTON_COLORS['blue']['bg']};
            color: {BUTTON_COLORS['blue']['fg']};
            cursor: {cycle_cursor};
            opacity: {cycle_opacity};
        }}
        #ai-reload-btn {{
            font-size: 2.62rem;
            font-weight: 400;
            border: 2px solid {reload_border};
            background: {reload_bg};
            color: {reload_fg};
            cursor: {reload_cursor};
            opacity: {reload_opacity};
            padding-top: 0;
        }}
        #ai-en-btn {{
            font-size: 0.78rem;
            font-weight: 800;
            letter-spacing: 0.1em;
            border: 2px solid {en_border};
            background: {en_bg};
            color: {en_fg};
            cursor: {en_cursor};
            opacity: {en_opacity};
            padding-top: 0;
        }}
        </style>
        <div class="ai-action-row">
            <button id="ai-cycle-btn" class="ai-action-btn" type="button" {cycle_disabled_attr}>→</button>
            <button id="ai-reload-btn" class="ai-action-btn" type="button" {reload_disabled_attr}>⟳</button>
            <button id="ai-en-btn" class="ai-action-btn" type="button" {en_disabled_attr}>EN</button>
        </div>
        <script>
        (function() {{
            var parentWindow = window.parent;
            var doc = parentWindow.document;
            var cycleButton = document.getElementById('ai-cycle-btn');
            var reloadButton = document.getElementById('ai-reload-btn');
            var enButton = document.getElementById('ai-en-btn');
            if (!doc) return;

            function triggerHidden(selector, event) {{
                if (event) {{
                    event.preventDefault();
                    event.stopPropagation();
                    if (typeof event.stopImmediatePropagation === 'function') {{
                        event.stopImmediatePropagation();
                    }}
                }}
                var hiddenButton = doc.querySelector(selector);
                if (!hiddenButton) return;
                hiddenButton.click();
            }}

            if (cycleButton && !cycleButton.disabled) {{
                cycleButton.addEventListener('click', function(event) {{
                    triggerHidden('.st-key-aicycle_hidden_wrap button', event);
                }});
            }}

            if (reloadButton && !reloadButton.disabled) {{
                reloadButton.addEventListener('click', function(event) {{
                    triggerHidden('.st-key-aireload_hidden_wrap button', event);
                }});
            }}

            if (enButton && !enButton.disabled) {{
                enButton.addEventListener('click', function(event) {{
                    triggerHidden('.st-key-aien_hidden_wrap button', event);
                }});
            }}
        }})();
        </script>
        """,
        height=64,
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
            if (!doc || !synth || !speechText || !speechKey ) return;

            function attemptSpeak(remainingAttempts) {{
                if (doc._autoSpeakSpanishKey === speechKey) return;
                if (typeof doc._fcSpeakSpanish !== 'function') {{
                    if (remainingAttempts <= 0) return;
                    setTimeout(function() {{
                        attemptSpeak(remainingAttempts - 1);
                    }}, 120);
                    return;
                }}
                if (doc._fcSpeechUnlocked) {{
                    doc._autoSpeakSpanishKey = speechKey;
                }}
                doc._fcSpeakSpanish({{
                    text: speechText,
                    rate: speechRate,
                    key: speechKey,
                    cancelFirst: true,
                }});
            }}

            attemptSpeak(8);
        }})();
        </script>
        """,
        height=0,
    )


def render_regular_auto_mode_controls():
    with st.container(key="regular_auto_controls_wrap"):
        if st.session_state["regular_auto_mode"]:
            col1, col2, col3, col4 = st.columns(4, gap="small")
            with col1:
                auto_mode_value = st.checkbox(
                    "AUTO",
                    key="regular_auto_mode_checkbox",
                )
            with col2:
                english_value = st.checkbox(
                    "ENGLISH",
                    key="regular_auto_english_checkbox",
                )
            with col3:
                cue_value = st.checkbox(
                    "CUE",
                    key="regular_auto_cue_checkbox",
                )
            with col4:
                repeat_value = st.checkbox(
                    "REPEAT 2x",
                    key="regular_auto_repeat_checkbox",
                )
        else:
            auto_mode_value = st.checkbox(
                "AUTO",
                key="regular_auto_mode_checkbox",
            )
            st.session_state["regular_auto_english_checkbox"] = st.session_state["regular_auto_include_english"]
            st.session_state["regular_auto_cue_checkbox"] = st.session_state["regular_auto_cue_prompt"]
            english_value = st.session_state["regular_auto_include_english"]
            repeat_value = st.session_state["regular_auto_repeat_spanish"]
            cue_value = st.session_state["regular_auto_cue_prompt"]

    if auto_mode_value != st.session_state["regular_auto_mode"]:
        st.session_state["regular_auto_mode"] = auto_mode_value
        st.session_state["regular_auto_generation"] += 1
        if auto_mode_value:
            st.session_state.show_answer = False
            st.session_state["regular_auto_english_checkbox"] = st.session_state["regular_auto_include_english"]
            st.session_state["regular_auto_cue_checkbox"] = st.session_state["regular_auto_cue_prompt"]
        st.rerun()

    if english_value != st.session_state["regular_auto_include_english"]:
        st.session_state["regular_auto_include_english"] = english_value
        st.session_state["regular_auto_generation"] += 1
        st.rerun()

    if repeat_value != st.session_state["regular_auto_repeat_spanish"]:
        st.session_state["regular_auto_repeat_spanish"] = repeat_value
        st.session_state["regular_auto_generation"] += 1
        st.rerun()

    if cue_value != st.session_state["regular_auto_cue_prompt"]:
        st.session_state["regular_auto_cue_prompt"] = cue_value
        st.session_state["regular_auto_generation"] += 1
        st.rerun()


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


def render_browser_audio_cleanup():
    components.html(
        """
        <script>
        (function() {
            var parentWindow = window.parent;
            var doc = parentWindow.document;
            var synth = parentWindow.speechSynthesis || window.speechSynthesis;
            var debugEl = doc.getElementById('story-mobile-debug');
            var bindings = [
                ['.st-key-storystart_wrap button', '_storyMobileStartHandler'],
                ['.st-key-storypause_wrap button', '_storyMobilePauseHandler'],
                ['.st-key-storystop_wrap button', '_storyMobileStopHandler'],
                ['.st-key-storynext_wrap button', '_storyMobileNextHandler'],
            ];
            var eventNames = ['click', 'touchend'];
            var storyController = doc._storyMobileController;
            var regularController = doc._regularAutoController;

            bindings.forEach(function(binding) {
                var element = doc.querySelector(binding[0]);
                var handler = doc[binding[1]];
                if (!element || !handler) return;
                eventNames.forEach(function(eventName) {
                    element.removeEventListener(eventName, handler, true);
                });
                doc[binding[1]] = null;
            });

            if (storyController) {
                if (storyController.advanceTimer) {
                    clearTimeout(storyController.advanceTimer);
                    storyController.advanceTimer = null;
                }
                if (storyController.advanceRetryTimer) {
                    clearInterval(storyController.advanceRetryTimer);
                    storyController.advanceRetryTimer = null;
                }
                if (storyController.queueToken) {
                    storyController.queueToken += 1;
                }
                storyController.running = false;
                storyController.active = false;
                storyController.isSpeaking = false;
                storyController.speakingKey = null;
                storyController.queuedNextIndex = null;
                storyController.pendingManualSpeakIndex = null;
                storyController.resumeTargetIndex = null;
                storyController.pendingInitialStartDelayMs = 0;
                storyController.awaitingServerStart = false;
            }

            if (regularController && regularController.timerIds) {
                regularController.timerIds.forEach(function(timerId) {
                    parentWindow.clearTimeout(timerId);
                });
                regularController.timerIds = [];
            }
            if (regularController) {
                regularController.phaseKey = null;
            }

            doc._storyPauseRequested = null;
            doc._storyPauseResumeState = null;
            doc._storyPauseCaptureKey = null;

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


def render_regular_auto_mode_driver(phase, phase_key, text, language, pause_after_seconds, preferred_gender, repeat_spanish, cue_prompt, should_speak=True, cue_before_speech=False):
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
                cuePrompt: {str(cue_prompt).lower()},
                shouldSpeak: {str(should_speak).lower()},
                cueBeforeSpeech: {str(cue_before_speech).lower()},
            }};

            if (!doc || !synth || !UtteranceCtor || !config.phaseKey) return;
            if (config.shouldSpeak && !config.text) return;

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
                return true;
            }}

            function playCueSequence(cueCount, onDone) {{
                var AudioCtx = parentWindow.AudioContext || parentWindow.webkitAudioContext || window.AudioContext || window.webkitAudioContext;
                var remainingCueCount = Math.max(cueCount || 1, 1);
                var finished = false;

                function finishCue() {{
                    if (finished || controller.phaseKey !== config.phaseKey) return;
                    finished = true;
                    onDone();
                }}

                function playSingleHtmlCue(onCueDone) {{
                    var createCueAudioInstance = doc._fcCreateCueAudioInstance;
                    if (typeof createCueAudioInstance !== 'function') {{
                        onCueDone(false);
                        return;
                    }}

                    try {{
                        var audioEl = createCueAudioInstance();
                        if (!audioEl) {{
                            onCueDone(false);
                            return;
                        }}
                        var completed = false;
                        var finishHtmlCue = function(success) {{
                            if (completed) return;
                            completed = true;
                            audioEl.onended = null;
                            audioEl.onerror = null;
                            if (audioEl.parentNode) {{
                                audioEl.parentNode.removeChild(audioEl);
                            }}
                            onCueDone(success);
                        }};

                        audioEl.currentTime = 0;
                        audioEl.volume = 1;
                        audioEl.onended = function() {{
                            finishHtmlCue(true);
                        }};
                        audioEl.onerror = function() {{
                            finishHtmlCue(false);
                        }};

                        var playAttempt = audioEl.play();
                        if (playAttempt && typeof playAttempt.then === 'function') {{
                            playAttempt.then(function() {{
                                queueTimeout(function() {{
                                    finishHtmlCue(true);
                                }}, 260);
                            }}).catch(function() {{
                                finishHtmlCue(false);
                            }});
                        }} else {{
                            queueTimeout(function() {{
                                finishHtmlCue(true);
                            }}, 260);
                        }}
                    }} catch (error) {{
                        onCueDone(false);
                    }}
                }}

                function scheduleHtmlCueSequence() {{
                    if (finished || controller.phaseKey !== config.phaseKey) return;
                    playSingleHtmlCue(function(success) {{
                        if (finished || controller.phaseKey !== config.phaseKey) return;
                        if (!success) {{
                            scheduleWebAudioCueSequence();
                            return;
                        }}
                        remainingCueCount -= 1;
                        if (remainingCueCount <= 0) {{
                            queueTimeout(finishCue, 620);
                            return;
                        }}
                        queueTimeout(scheduleHtmlCueSequence, 220);
                    }});
                }}

                function scheduleWebAudioCueSequence() {{
                    if (!AudioCtx) {{
                        finishCue();
                        return;
                    }}

                    try {{
                        if (!doc._fcCueAudioContext) {{
                            doc._fcCueAudioContext = new AudioCtx();
                        }}

                        var audioContext = doc._fcCueAudioContext;

                        function startSingleCue() {{
                            var startAt = audioContext.currentTime + 0.02;
                            var oscillator = audioContext.createOscillator();
                            var gainNode = audioContext.createGain();

                            oscillator.type = 'sine';
                            oscillator.frequency.setValueAtTime(1318.5, startAt);

                            gainNode.gain.setValueAtTime(0.0001, startAt);
                            gainNode.gain.exponentialRampToValueAtTime(0.28, startAt + 0.018);
                            gainNode.gain.exponentialRampToValueAtTime(0.0001, startAt + 0.22);

                            oscillator.connect(gainNode);
                            gainNode.connect(audioContext.destination);

                            oscillator.start(startAt);
                            oscillator.stop(startAt + 0.24);
                        }}

                        function scheduleSingleCue() {{
                            if (finished || controller.phaseKey !== config.phaseKey) return;
                            startSingleCue();
                            remainingCueCount -= 1;
                            if (remainingCueCount <= 0) {{
                                queueTimeout(finishCue, 720);
                                return;
                            }}
                            queueTimeout(scheduleSingleCue, 320);
                        }}

                        if (typeof audioContext.resume === 'function') {{
                            audioContext.resume().then(function() {{
                                if (controller.phaseKey !== config.phaseKey) return;
                                scheduleSingleCue();
                            }}).catch(function() {{
                                finishCue();
                            }});
                            return;
                        }}

                        scheduleSingleCue();
                    }} catch (error) {{
                        finishCue();
                    }}
                }}

                if (typeof doc._fcPrimeCueAudioNow === 'function') {{
                    try {{
                        doc._fcPrimeCueAudioNow();
                    }} catch (error) {{
                    }}
                }}

                if (doc._fcCueAudioElement) {{
                    scheduleHtmlCueSequence();
                    return;
                }}

                scheduleWebAudioCueSequence();
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

            function finalizePhase() {{
                queueTimeout(function() {{
                    if (controller.phaseKey !== config.phaseKey) return;
                    if (config.phase === 'prompt') {{
                        clickHiddenButton('.st-key-regularautoreveal_hidden_wrap button');
                        return;
                    }}
                    clickHiddenButton('.st-key-regularautoadvance_hidden_wrap button');
                }}, config.delayMs);
            }}

            function startSpeechSequence() {{
                if (!config.shouldSpeak) {{
                    finalizePhase();
                    return;
                }}
                speakSequence(finalizePhase);
            }}

            if (config.cueBeforeSpeech && config.shouldSpeak) {{
                playCueSequence(1, startSpeechSequence);
            }} else if (config.cuePrompt && config.phase === 'prompt') {{
                playCueSequence(1, startSpeechSequence);
            }} else {{
                startSpeechSequence();
            }}
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


def render_header(summary_mode=False):
    if not summary_mode and st.session_state.person_selector_visible:
        render_splash_selector()
        return

    menu_icon = "✕" if st.session_state.menu_open else "☰"
    with st.container(key="header_row_wrap"):
        show_picker_quit = st.session_state.selected_csv is None and not summary_mode
        show_menu_button = not st.session_state.person_selector_visible and not summary_mode
        title_subtitle = "" if summary_mode else PERSON_LABELS.get(st.session_state.active_person, "")
        if summary_mode:
            title_col = st.container()
            quit_col = None
            ham_col = None
        elif show_picker_quit and show_menu_button:
            title_col, quit_col, ham_col = st.columns([1, 0.24, 0.12], gap="small")
        elif show_picker_quit:
            title_col, quit_col = st.columns([1, 0.24], gap="small")
        else:
            title_col, ham_col = st.columns([1, 0.14], gap="small")
        with title_col:
            st.markdown(
                "<div class='title-row'>"
                "<div>"
                "<span class='title-main'>Spanish Flashcards</span>"
                "<div class='title-sub'>" + title_subtitle + "</div>"
                "</div>"
                "</div>",
                unsafe_allow_html=True,
            )
        if show_picker_quit:
            with quit_col:
                with st.container(key="header_quit_wrap"):
                    if st.button("QUIT", key="header_quit_btn"):
                        st.session_state.menu_open = False
                        st.session_state.final_exit = True
                        st.rerun()
        if show_menu_button:
            with ham_col:
                with st.container(key="hamburger_wrap"):
                    if st.button(menu_icon, key="hamburger_btn"):
                        if st.session_state.menu_open:
                            close_menu_and_save()
                        else:
                            st.session_state.menu_open = True
                        st.rerun()
    if summary_mode:
        return
    if st.session_state.menu_open:
        return
    if st.session_state.person_selector_visible:
        render_splash_selector()


def render_menu():
    if not st.session_state.menu_open:
        return
    active_review_count = review_count_for(st.session_state.active_person)
    active_favorites_count = favorites_count_for(st.session_state.active_person)
    has_regular_progress = person_has_regular_deck_progress(st.session_state.active_person)
    active_person_label = PERSON_LABELS[st.session_state.active_person]

    def render_menu_divider(divider_key):
        with st.container(key=divider_key):
            st.markdown('<div class="menu-divider" aria-hidden="true"></div>', unsafe_allow_html=True)

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
        )
        hints_enabled = new_hints == "Hints ON"
        if hints_enabled != st.session_state.show_hints:
            st.session_state.show_hints = hints_enabled
            store_active_person_prefs()
            sync_menu_widget_state()
            save_prefs(current_prefs())
            clear_menu_destructive_confirms()
            st.rerun()
        render_menu_divider("menu_divider_wrap_1")
        st.markdown('<div class="menu-section-label">Theme</div>', unsafe_allow_html=True)
        new_theme = st.radio("Theme", options=["light", "dark", "aqua", "amber"],
                             index=["light","dark","aqua", "amber"].index(st.session_state.theme),
                             label_visibility="collapsed")
        if new_theme != st.session_state.theme:
            st.session_state.theme     = new_theme
            store_active_person_prefs()
            sync_menu_widget_state()
            save_prefs(current_prefs())
            clear_menu_destructive_confirms()
            st.rerun()
        render_menu_divider("menu_divider_wrap_2")
        st.markdown('<div class="menu-section-label" style="margin-top:0.9rem;">Direction</div>',
                    unsafe_allow_html=True)
        dir_options = ["Random 50/50", "EN → ES only", "ES → EN only"]
        dir_keys    = ["random", "en_to_es", "es_to_en"]
        cur_idx     = dir_keys.index(st.session_state.direction_mode)
        new_dir     = st.radio("Direction", options=dir_options, index=cur_idx,
                               label_visibility="collapsed")
        if dir_options.index(new_dir) != cur_idx:
            st.session_state.direction_mode = dir_keys[dir_options.index(new_dir)]
            st.session_state.direction = direction_for_mode(st.session_state.direction_mode)
            store_active_person_prefs()
            sync_menu_widget_state()
            save_prefs(current_prefs())
            clear_menu_destructive_confirms()
            st.rerun()
        render_menu_divider("menu_divider_wrap_3")
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
        )
        if new_speed != st.session_state.speech_speed:
            st.session_state.speech_speed = new_speed
            store_active_person_prefs()
            sync_menu_widget_state()
            save_prefs(current_prefs())
            clear_menu_destructive_confirms()
            st.rerun()
        render_menu_divider("menu_divider_wrap_4")
        st.markdown('<div class="menu-section-label" style="margin-top:0.9rem;">AI Examples</div>', unsafe_allow_html=True)
        st.markdown('<div class="menu-field-label">Allowed tenses/forms</div>', unsafe_allow_html=True)
        new_ai_tenses = dict(st.session_state.ai_sentence_tenses)
        with st.container(key="menu_ai_tenses_wrap"):
            for tense_group in (AI_TENSE_OPTIONS[:3], AI_TENSE_OPTIONS[3:]):
                tense_columns = st.columns(3, gap="small")
                for column, (tense_key, short_label, _) in zip(tense_columns, tense_group):
                    with column:
                        new_ai_tenses[tense_key] = st.checkbox(
                            short_label,
                            value=st.session_state.ai_sentence_tenses.get(
                                tense_key,
                                DEFAULT_AI_SENTENCE_TENSES.get(tense_key, False),
                            ),
                        )
        sanitized_new_ai_tenses = sanitize_ai_sentence_tenses(
            new_ai_tenses,
            st.session_state.ai_sentence_tenses,
        )
        if sanitized_new_ai_tenses != st.session_state.ai_sentence_tenses:
            st.session_state.ai_sentence_tenses = sanitized_new_ai_tenses
            store_active_person_prefs()
            sync_menu_widget_state()
            save_prefs(current_prefs())
            clear_menu_destructive_confirms()
            st.rerun()
        st.markdown('<div class="menu-field-label">Complexity</div>', unsafe_allow_html=True)
        ai_level_labels = [short_label for _, short_label, _ in AI_LEVEL_OPTIONS]
        ai_level_keys = [option_key for option_key, _, _ in AI_LEVEL_OPTIONS]
        new_ai_level_label = st.radio(
            "Complexity",
            options=ai_level_labels,
            index=ai_level_keys.index(st.session_state.ai_sentence_level),
            horizontal=True,
            label_visibility="collapsed",
        )
        new_ai_level = ai_level_keys[ai_level_labels.index(new_ai_level_label)]
        if new_ai_level != st.session_state.ai_sentence_level:
            st.session_state.ai_sentence_level = new_ai_level
            store_active_person_prefs()
            sync_menu_widget_state()
            save_prefs(current_prefs())
            clear_menu_destructive_confirms()
            st.rerun()
        st.markdown('<div class="menu-field-label">Sentence length (words)</div>', unsafe_allow_html=True)
        pending_ai_word_target = st.session_state.pop("menu_ai_word_target_pending_value", None)
        ai_word_target_key = "menu_ai_word_target"
        if pending_ai_word_target is not None:
            st.session_state[ai_word_target_key] = pending_ai_word_target
        elif ai_word_target_key not in st.session_state:
            st.session_state[ai_word_target_key] = st.session_state.ai_examples_target_words
        new_ai_word_target = st.slider(
            "Sentence length",
            min_value=AI_EXAMPLES_TARGET_WORDS_MIN,
            max_value=AI_EXAMPLES_TARGET_WORDS_MAX,
            value=st.session_state[ai_word_target_key],
            step=1,
            key=ai_word_target_key,
            label_visibility="collapsed",
        )
        sanitized_ai_word_target = sanitize_ai_examples_word_target(
            new_ai_word_target,
            st.session_state.ai_examples_target_words,
        )
        if sanitized_ai_word_target != st.session_state.ai_examples_target_words:
            st.session_state.ai_examples_target_words = sanitized_ai_word_target
            st.session_state.menu_ai_word_target_pending_value = sanitized_ai_word_target
            store_active_person_prefs()
            sync_menu_widget_state()
            save_prefs(current_prefs())
            clear_menu_destructive_confirms()
            st.rerun()
        render_menu_divider("menu_divider_wrap_5")
        st.markdown('<div class="menu-section-label" style="margin-top:0.9rem;">STORY &amp; DIALOG MODES &ndash; PAUSES BETWEEN SENTENCES</div>',
                    unsafe_allow_html=True)
        story_timing_options = [5, 4, 3, 2, 1]
        st.markdown('<div class="menu-field-label">Reading speed (1 = fastest)</div>', unsafe_allow_html=True)
        new_story_reading_speed = st.radio(
            "Reading speed (1 = fastest)",
            options=story_timing_options,
            index=story_timing_options.index(st.session_state.story_reading_speed),
            horizontal=True,
            label_visibility="collapsed",
        )
        if new_story_reading_speed != st.session_state.story_reading_speed:
            st.session_state.story_reading_speed = new_story_reading_speed
            store_active_person_prefs()
            sync_menu_widget_state()
            save_prefs(current_prefs())
            clear_menu_destructive_confirms()
            st.rerun()
        st.markdown('<div class="menu-field-label">Pause amount (1 = shortest)</div>', unsafe_allow_html=True)
        new_story_pause_amount = st.radio(
            "Pause amount (1 = shortest)",
            options=story_timing_options,
            index=story_timing_options.index(st.session_state.story_pause_amount),
            horizontal=True,
            label_visibility="collapsed",
        )
        if new_story_pause_amount != st.session_state.story_pause_amount:
            st.session_state.story_pause_amount = new_story_pause_amount
            store_active_person_prefs()
            sync_menu_widget_state()
            save_prefs(current_prefs())
            clear_menu_destructive_confirms()
            st.rerun()
        if active_review_count > 0:
            erase_label = f"Erase ⭐️ REVIEW ⭐️ deck for {active_person_label}"
            erase_verify_label = "Verify ⭐️ REVIEW ⭐️ deck deletion!"
            erase_wrap_key = "erase_review_confirm_wrap" if st.session_state.erase_review_confirm else "erase_review_wrap"
            with st.container(key="erase_review_slot_wrap"):
                with st.container(key=erase_wrap_key):
                    if st.button(
                        erase_verify_label if st.session_state.erase_review_confirm else erase_label,
                        key="erase_review_btn",
                        use_container_width=True,
                    ):
                        if st.session_state.erase_review_confirm:
                            erase_review_deck(st.session_state.active_person)
                        else:
                            st.session_state.erase_favorites_confirm = False
                            st.session_state.initialize_all_decks_confirm = False
                            st.session_state.erase_review_confirm = True
                        st.rerun()
                if st.session_state.erase_review_confirm:
                    with st.container(key="clear_erase_review_confirm_wrap"):
                        st.button("__clear_erase_review_confirm__", key="clear_erase_review_confirm_btn", on_click=clear_erase_review_confirm)
                    render_erase_review_confirm_timeout()

        if active_favorites_count > 0:
            erase_favorites_label = f"Erase 💙 FAVORITES 💙 deck for {active_person_label}"
            erase_favorites_verify_label = "Verify 💙 FAVORITES 💙 deck deletion!"
            erase_favorites_wrap_key = "erase_favorites_confirm_wrap" if st.session_state.erase_favorites_confirm else "erase_favorites_wrap"
            with st.container(key="erase_favorites_slot_wrap"):
                with st.container(key=erase_favorites_wrap_key):
                    if st.button(
                        erase_favorites_verify_label if st.session_state.erase_favorites_confirm else erase_favorites_label,
                        key="erase_favorites_btn",
                        use_container_width=True,
                    ):
                        if st.session_state.erase_favorites_confirm:
                            erase_favorites_deck(st.session_state.active_person)
                        else:
                            st.session_state.erase_review_confirm = False
                            st.session_state.initialize_all_decks_confirm = False
                            st.session_state.erase_favorites_confirm = True
                        st.rerun()
                if st.session_state.erase_favorites_confirm:
                    with st.container(key="clear_erase_favorites_confirm_wrap"):
                        st.button(
                            "__clear_erase_favorites_confirm__",
                            key="clear_erase_favorites_confirm_btn",
                            on_click=clear_erase_favorites_confirm,
                        )
                    render_erase_favorites_confirm_timeout()

        if has_regular_progress:
            initialize_wrap_key = "initialize_all_decks_confirm_wrap" if st.session_state.initialize_all_decks_confirm else "initialize_all_decks_wrap"
            initialize_label = f"Initialize ❗ ALL ❗ decks + history for {active_person_label}"
            initialize_verify_label = "Verify ❗ ALL ❗ decks + history deletion!"
            with st.container(key="initialize_all_decks_slot_wrap"):
                with st.container(key=initialize_wrap_key):
                    if st.button(
                        initialize_verify_label if st.session_state.initialize_all_decks_confirm else initialize_label,
                        key="initialize_all_decks_btn",
                        use_container_width=True,
                    ):
                        if st.session_state.initialize_all_decks_confirm:
                            initialize_all_decks(st.session_state.active_person)
                        else:
                            st.session_state.erase_review_confirm = False
                            st.session_state.erase_favorites_confirm = False
                            st.session_state.initialize_all_decks_confirm = True
                        st.rerun()
                if st.session_state.initialize_all_decks_confirm:
                    with st.container(key="clear_initialize_all_decks_confirm_wrap"):
                        st.button(
                            "__clear_initialize_all_decks_confirm__",
                            key="clear_initialize_all_decks_confirm_btn",
                            on_click=clear_initialize_all_decks_confirm,
                        )
                    render_initialize_all_decks_confirm_timeout()

        st.markdown('<div class="menu-bottom-spacer"></div>', unsafe_allow_html=True)


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


def render_buttons(show_answer, spanish_audio_text, spanish_visible_before_answer=False):
    if st.session_state["regular_auto_mode"]:
        with st.container(key="icon_btn_row_wrap"):
            left_col, right_col = st.columns(2, gap="small")
            with left_col:
                st.empty()
            with right_col:
                with st.container(key="action_right_group_wrap"):
                    right_group_columns = st.columns(1, gap="small")
                    with right_group_columns[0]:
                        with st.container(key="quitbefore_wrap"):
                            if st.button("🛑", key="quitbefore_btn"):
                                st.session_state.quit_requested = True
                                st.rerun()
        return

    if not show_answer:
        with st.container(key="icon_btn_row_wrap"):
            left_col, right_col = st.columns(2, gap="small")
            with left_col:
                with st.container(key="showanswer_wrap"):
                    st.button("➜", key="showanswer_btn", on_click=reveal_answer)
            with right_col:
                with st.container(key="action_right_group_wrap"):
                    right_group_columns = st.columns(2 if spanish_visible_before_answer else 1, gap="small")
                    if spanish_visible_before_answer:
                        with right_group_columns[0]:
                            with st.container(key="speaker_wrap"):
                                render_speaker_button(spanish_audio_text, icon_font_size="1.9rem")
                        with right_group_columns[1]:
                            with st.container(key="quitbefore_wrap"):
                                if st.button("🛑", key="quitbefore_btn"):
                                    st.session_state.quit_requested = True
                                    st.rerun()
                    else:
                        with right_group_columns[0]:
                            with st.container(key="quitbefore_wrap"):
                                if st.button("🛑", key="quitbefore_btn"):
                                    st.session_state.quit_requested = True
                                    st.rerun()
        return

    review_mode = is_review_deck(st.session_state.selected_csv)
    favorites_mode = is_favorites_deck(st.session_state.selected_csv)
    current_card = st.session_state.cards[current_card_index()]
    current_card_is_favorite = favorite_entry_exists(st.session_state.active_person, current_card)
    current_favorites_entry_exists = favorite_entry_exists(
        current_favorite_person(),
        current_card,
        source_deck=current_card.get("source_deck"),
        source_index=current_card.get("source_index"),
    ) if favorites_mode else False
    ai_examples_supported = (
        show_answer
        and not review_mode
        and not favorites_mode
        and current_card_supports_ai_examples()
    )
    sync_ai_examples_state()
    ai_availability = current_ai_examples_availability() if ai_examples_supported else None
    ai_examples_available = bool(ai_availability and ai_availability["available"])
    ai_disabled_label = ai_availability["button_label"] if ai_availability else "Examples"
    ai_disabled_reason = ai_availability["reason"] if ai_availability else None
    ai_has_sentences = bool(st.session_state.ai_examples_sentences)
    ai_reload_unlocked = bool(st.session_state.ai_examples_reload_unlocked)
    ai_error_message = st.session_state.ai_examples_error
    ai_examples_loading = bool(st.session_state.ai_examples_loading)
    ai_pending_action = st.session_state.ai_examples_pending_action
    speaker_audio_text = spanish_audio_text
    if ai_examples_supported and ai_has_sentences:
        speaker_audio_text = st.session_state.ai_examples_sentences[st.session_state.ai_examples_index]
    desktop_action_container = st.container(key="answer_action_row_desktop_wrap") if (not review_mode and not favorites_mode) else st.container()
    with desktop_action_container:
        with st.container(key="answer_action_row_wrap"):
            if review_mode or favorites_mode:
                left_col, right_col = st.columns(2, gap="small")
                with left_col:
                    with st.container(key="action_left_group_wrap"):
                        left_group_columns = st.columns(2, gap="small")
                        with left_group_columns[0]:
                            with st.container(key="correct_wrap"):
                                st.button("✓", key="correct_btn", on_click=mark_correct)
                        with left_group_columns[1]:
                            if favorites_mode:
                                if current_favorites_entry_exists:
                                    with st.container(key="del_active_wrap"):
                                        st.button("🗑", key="del_btn", on_click=delete_current_favorite_card)
                                else:
                                    st.empty()
                            else:
                                with st.container(key="repeat_wrap"):
                                    st.button("?", key="repeat_btn", on_click=mark_repeat)
                with right_col:
                    with st.container(key="action_right_group_wrap"):
                        right_group_columns = st.columns(3 if review_mode else 2, gap="small")
                        with right_group_columns[0]:
                            with st.container(key="speaker_wrap"):
                                render_speaker_button(spanish_audio_text)
                        with right_group_columns[1]:
                            with st.container(key="autoplay_btn_wrap"):
                                render_auto_speak_button(st.session_state.auto_speak_spanish)
                if review_mode:
                    delete_armed = st.session_state.delete_review_confirm_key == current_review_card_key(current_card)
                    with right_group_columns[2]:
                        with st.container(key="del_confirm_wrap" if delete_armed else "del_active_wrap"):
                            st.button("X", key="del_btn", on_click=delete_current_review_card)
                    if delete_armed:
                        with st.container(key="clear_delete_confirm_wrap"):
                            st.button("__clear_delete_confirm__", key="clear_delete_confirm_btn", on_click=clear_delete_review_confirm)
                        render_delete_confirm_timeout()
            else:
                with st.container(key="action_top_row_wrap"):
                    top_cols = st.columns(4, gap="small")
                    with top_cols[0]:
                        with st.container(key="correct_wrap"):
                            st.button("✓", key="correct_btn", on_click=mark_correct)
                    with top_cols[1]:
                        with st.container(key="repeat_wrap"):
                            st.button("?", key="repeat_btn", on_click=mark_repeat)
                    with top_cols[2]:
                        with st.container(key="nextunscored_wrap"):
                            st.button("↓", key="nextunscored_btn", on_click=advance_unscored)
                    with top_cols[3]:
                        if current_card_is_favorite:
                            st.empty()
                        else:
                            with st.container(key="favorite_wrap"):
                                st.button("♥︎", key="favorite_btn", on_click=add_current_card_to_favorites)
                with st.container(key="action_bottom_row_wrap"):
                    bottom_cols = st.columns([1, 1, 2], gap="small")
                    with bottom_cols[0]:
                        with st.container(key="speaker_wrap"):
                            render_speaker_button(speaker_audio_text)
                    with bottom_cols[1]:
                        with st.container(key="autoplay_btn_wrap"):
                            render_auto_speak_button(st.session_state.auto_speak_spanish)
                    with bottom_cols[2]:
                        if ai_examples_supported:
                            if ai_has_sentences:
                                if ai_examples_loading:
                                    with st.container(key="ai_actions_wrap"):
                                        render_ai_action_buttons(cycle_disabled=True, reload_disabled=True, en_disabled=True, en_is_on=False)
                                else:
                                    with st.container(key="ai_actions_wrap"):
                                        render_ai_action_buttons(
                                            cycle_disabled=False,
                                            reload_disabled=(not ai_reload_unlocked) or (not ai_examples_available),
                                            en_disabled=False,
                                            en_is_on=st.session_state.ai_examples_show_english,
                                        )
                            elif ai_examples_loading:
                                with st.container(key="ai_single_wrap"):
                                    st.button("Loading...", key="ai_fetch_btn", disabled=True, help=ai_disabled_reason)
                            else:
                                button_label = ai_disabled_label
                                if ai_examples_available:
                                    button_label = "Retry" if ai_error_message else "Examples"
                                with st.container(key="ai_single_wrap"):
                                    if st.button(button_label, key="ai_fetch_btn", disabled=not ai_examples_available, help=ai_disabled_reason):
                                        begin_ai_examples_action("fetch")
                                        st.rerun()
                if ai_examples_supported and ai_examples_loading and ai_pending_action in {"fetch", "reload"}:
                    fetch_ai_examples_for_current_card()
                    st.rerun()
    if not review_mode and not favorites_mode:
        with st.container(key="answer_action_row_phone_wrap"):
            with st.container(key="action_phone_top_row_wrap"):
                phone_top_columns = st.columns(4, gap="small")
                with phone_top_columns[0]:
                    with st.container(key="correct_phone_wrap"):
                        st.button("✓", key="correct_phone_btn", on_click=mark_correct)
                with phone_top_columns[1]:
                    with st.container(key="repeat_phone_wrap"):
                        st.button("?", key="repeat_phone_btn", on_click=mark_repeat)
                with phone_top_columns[2]:
                    with st.container(key="nextunscored_phone_wrap"):
                        st.button("↓", key="nextunscored_phone_btn", on_click=advance_unscored)
                with phone_top_columns[3]:
                    if current_card_is_favorite:
                        st.empty()
                    else:
                        with st.container(key="favorite_phone_wrap"):
                            st.button("♥︎", key="favorite_phone_btn", on_click=add_current_card_to_favorites)
            if ai_examples_supported:
                if ai_examples_loading and not ai_has_sentences:
                    with st.container(key="action_phone_bottom_loading_row_wrap"):
                        phone_loading_row_columns = st.columns([1, 1, 2.08], gap="small")
                        with phone_loading_row_columns[0]:
                            with st.container(key="speaker_phone_wrap"):
                                render_speaker_button(speaker_audio_text, icon_font_size="1.9rem")
                        with phone_loading_row_columns[1]:
                            with st.container(key="autoplay_btn_phone_wrap"):
                                render_auto_speak_button(st.session_state.auto_speak_spanish)
                        with phone_loading_row_columns[2]:
                            with st.container(key="phone_ai_single_wrap"):
                                st.button(
                                    "Loading...",
                                    key="ai_fetch_phone_btn",
                                    disabled=True,
                                    help=ai_disabled_reason,
                                )
                elif ai_has_sentences:
                    with st.container(key="action_phone_bottom_actions_row_wrap"):
                        phone_actions_row_columns = st.columns([1, 1, 2.08], gap="small")
                        with phone_actions_row_columns[0]:
                            with st.container(key="speaker_phone_wrap"):
                                render_speaker_button(speaker_audio_text, icon_font_size="1.9rem")
                        with phone_actions_row_columns[1]:
                            with st.container(key="autoplay_btn_phone_wrap"):
                                render_auto_speak_button(st.session_state.auto_speak_spanish)
                        with phone_actions_row_columns[2]:
                            with st.container(key="phone_ai_actions_wrap"):
                                render_ai_action_buttons(
                                    cycle_disabled=ai_examples_loading,
                                    reload_disabled=(not ai_reload_unlocked) or (not ai_examples_available) or ai_examples_loading,
                                    en_disabled=ai_examples_loading,
                                    en_is_on=st.session_state.ai_examples_show_english,
                                )
                else:
                    button_label = ai_disabled_label
                    if ai_examples_available:
                        button_label = "Retry" if ai_error_message else "Examples"
                    with st.container(key="action_phone_bottom_single_row_wrap"):
                        phone_single_row_columns = st.columns([1, 1, 2.08], gap="small")
                        with phone_single_row_columns[0]:
                            with st.container(key="speaker_phone_wrap"):
                                render_speaker_button(speaker_audio_text, icon_font_size="1.9rem")
                        with phone_single_row_columns[1]:
                            with st.container(key="autoplay_btn_phone_wrap"):
                                render_auto_speak_button(st.session_state.auto_speak_spanish)
                        with phone_single_row_columns[2]:
                            with st.container(key="phone_ai_single_wrap"):
                                if st.button(
                                    button_label,
                                    key="ai_fetch_phone_btn",
                                    disabled=not ai_examples_available,
                                    help=ai_disabled_reason,
                                ):
                                    begin_ai_examples_action("fetch")
                                    st.rerun()
            else:
                with st.container(key="action_phone_bottom_single_row_wrap"):
                    phone_single_row_columns = st.columns([1, 1, 2.08], gap="small")
                    with phone_single_row_columns[0]:
                        with st.container(key="speaker_phone_wrap"):
                            render_speaker_button(spanish_audio_text, icon_font_size="1.9rem")
                    with phone_single_row_columns[1]:
                        with st.container(key=auto_speak_phone_key):
                            st.button("AUTO  \nPLAY", key="autospeak_phone_btn", on_click=toggle_auto_speak_spanish)
                    with phone_single_row_columns[2]:
                        st.empty()
    if ai_examples_supported:
        if ai_has_sentences and st.session_state.auto_speak_spanish:
            ai_autoplay_key = "|".join(
                [
                    st.session_state.selected_csv or "",
                    str(current_card_index()),
                    "ai-example-autoplay",
                    str(st.session_state.ai_examples_autoplay_generation),
                ]
            )
            with st.container(key="ai_autospeak_iframe_wrap"):
                render_auto_speak_spanish(
                    st.session_state.ai_examples_sentences[st.session_state.ai_examples_index],
                    ai_autoplay_key,
                )
        with st.container(key="aicycle_hidden_wrap"):
            if st.button("__ai_cycle_hidden__", key="ai_cycle_hidden_btn"):
                cycle_ai_example()
                st.rerun()
        with st.container(key="aireload_hidden_wrap"):
            if st.button("__ai_reload_hidden__", key="ai_reload_hidden_btn"):
                begin_ai_examples_action("reload")
                st.rerun()
        with st.container(key="aien_hidden_wrap"):
            st.button("__ai_en_hidden__", key="ai_en_hidden_btn", on_click=toggle_ai_examples_en)
    with st.container(key="autospeak_toggle_hidden_wrap"):
        st.button("__autospeak_toggle__", key="autospeak_toggle_hidden_btn", on_click=toggle_auto_speak_spanish)


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
    st.session_state["regular_auto_include_english"] = True
    st.session_state["regular_auto_repeat_spanish"] = False
    st.session_state["regular_auto_cue_prompt"] = True
    st.session_state["regular_auto_generation"] += 1
    st.session_state["regular_auto_mode_checkbox"] = False
    st.session_state["regular_auto_english_checkbox"] = True
    st.session_state["regular_auto_repeat_checkbox"] = False
    st.session_state["regular_auto_cue_checkbox"] = True
    st.session_state.quit_requested = False
    st.session_state.final_exit = False
    st.session_state.menu_open = False
    st.session_state["score_actions"] = 0
    st.session_state["score_correct"] = 0
    st.session_state["score_repeat"] = 0
    st.rerun()


def restart_to_splash():
    reset_study_state(reset_selected=True)
    st.session_state.person_selector_visible = True
    st.session_state.menu_open = False
    st.session_state.quit_requested = False
    st.session_state.final_exit = False
    st.session_state.progress_screen_open = False
    st.session_state.open_deck_categories = []
    st.session_state.open_deck_subcategories = []


def render_progress_screen():
    ensure_monthly_progress_snapshot(st.session_state.active_person)
    current_learned_count = learned_words_completed_count(st.session_state.active_person)
    current_trackable_count = current_trackable_cards_count()
    chart_rows = progress_chart_rows(st.session_state.active_person, months=12)
    cloud_history_available = cloud_sync_enabled()
    learned_percent = 0.0
    if current_trackable_count > 0:
        learned_percent = current_learned_count / current_trackable_count * 100.0
    chart_values = [int(row["Learned Cards"]) for row in chart_rows if row.get("Learned Cards") is not None]
    chart_max_value = max(chart_values) if chart_values else 0
    y_axis_max = max(5, chart_max_value + max(3, math.ceil(chart_max_value * 0.25)))
    progress_accent_color = t["fg"]
    y_tick_step = max(1, math.ceil(y_axis_max / 6))
    y_ticks = list(range(0, y_axis_max + 1, y_tick_step))
    if y_ticks[-1] != y_axis_max:
        y_ticks.append(y_axis_max)

    st.markdown(
        "<div class='progress-screen'>"
        "<div class='title-big progress-title'>Progress</div>"
        "<div class='title-big-sub progress-subtitle'>12-month learned cards history</div>"
        "</div>"
        "<style>"
        ".progress-screen { width: 100%; text-align: center; padding: 0.75rem 0 0.1rem 0; }"
        f".progress-title {{ display: block; color: {progress_accent_color}; margin-bottom: 0.3rem; }}"
        ".progress-subtitle { display: block; margin-top: 0; }"
        ".progress-summary-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 0.7rem 1rem; margin: 1.25rem 0 0.9rem 0; }"
        ".progress-card { border: 1px solid rgba(0,0,0,0.08); border-radius: 0.9rem; padding: 0.85rem 0.7rem; background: rgba(255,255,255,0.04); text-align: center; }"
        ".progress-card-label { font-size: 0.78rem; letter-spacing: 0.06em; text-transform: uppercase; opacity: 0.72; margin-bottom: 0.25rem; }"
        ".progress-card-value { font-size: 1.35rem; font-weight: 700; line-height: 1.1; }"
        ".progress-note { font-size: 0.88rem; opacity: 0.82; margin: 0.7rem 0 0.2rem 0; text-align: center; }"
        ".progress-chart-shell { width: 100%; display: block; margin: 0.35rem 0 0 0; }"
        f".st-key-progress_chart_wrap {{ display: block; width: 100%; margin: 0 auto; border: 2px solid {progress_accent_color}; border-radius: 0; padding: 0.18rem 0.16rem 0.16rem 0.16rem; background: rgba(255,255,255,0.02); box-sizing: border-box; overflow: hidden; text-align: center; }}"
        ".st-key-progress_chart_wrap [data-testid='stVerticalBlockBorderWrapper'] { display: block !important; width: 100% !important; max-width: 100% !important; border: none !important; background: transparent !important; box-shadow: none !important; padding: 0 !important; }"
        ".st-key-progress_chart_inner_wrap { width: calc(100% - 8px); max-width: calc(100% - 8px); margin: 0 auto; overflow: hidden; }"
        ".st-key-progress_chart_inner_wrap [data-testid='stVerticalBlockBorderWrapper'] { display: block !important; width: 100% !important; max-width: 100% !important; border: none !important; background: transparent !important; box-shadow: none !important; padding: 0 !important; }"
        ".st-key-progress_chart_inner_wrap [data-testid='stImage'], .st-key-progress_chart_inner_wrap [data-testid='stPyplot'] { width: 100% !important; max-width: 100% !important; margin: 0 auto !important; overflow: hidden; display: block; }"
        ".st-key-progress_chart_inner_wrap img, .st-key-progress_chart_inner_wrap canvas { width: 100% !important; max-width: 100% !important; display: block; margin: 0 auto; }"
        ".st-key-progress_back_wrap { width: 100%; margin: 0.7rem 0 0 0; }"
        ".st-key-progress_back_wrap [data-testid='stVerticalBlockBorderWrapper'] { width: min(100%, 11rem); margin: 0 auto; padding: 0 !important; border: none !important; background: transparent !important; box-shadow: none !important; }"
        ".st-key-progress_back_wrap .stButton, .st-key-progress_back_wrap .stButton > button { width: 100%; }"
        "@media (max-width: 767px) { .progress-screen { padding-top: 0.35rem; } .st-key-progress_back_wrap [data-testid='stVerticalBlockBorderWrapper'] { width: min(100%, 11rem); } }"
        "</style>",
        unsafe_allow_html=True,
    )

    st.markdown(
        "<div class='progress-summary-grid'>"
        f"<div class='progress-card'><div class='progress-card-label'>Learned To Date</div><div class='progress-card-value'>{current_learned_count}</div></div>"
        f"<div class='progress-card'><div class='progress-card-label'>Trackable Cards To Date</div><div class='progress-card-value'>{current_trackable_count}</div></div>"
        f"<div class='progress-card'><div class='progress-card-label'>% Cards Learned</div><div class='progress-card-value'>{learned_percent:.2f}%</div></div>"
        f"<div class='progress-card'><div class='progress-card-label'>User</div><div class='progress-card-value'>{PERSON_LABELS[st.session_state.active_person]}</div></div>"
        "</div>",
        unsafe_allow_html=True,
    )

    if not chart_rows:
        st.markdown("<div class='progress-note'>No chart data available yet.</div>", unsafe_allow_html=True)
    else:
        month_labels = [row["Month"] for row in chart_rows]
        x_positions = list(range(len(chart_rows)))
        plotted_x = [index for index, row in enumerate(chart_rows) if row.get("Learned Cards") is not None]
        plotted_y = [int(chart_rows[index]["Learned Cards"]) for index in plotted_x]

        fig, ax = plt.subplots(figsize=(7.2, 2.7), dpi=100)
        fig.patch.set_facecolor("white")
        ax.set_facecolor("white")
        if plotted_x and plotted_y:
            ax.scatter(plotted_x, plotted_y, s=38, color="#6e9df0", zorder=3)
        ax.set_xlim(-0.5, len(chart_rows) - 0.28)
        ax.set_ylim(0, y_axis_max)
        ax.set_xticks(x_positions)
        ax.set_xticklabels(month_labels, rotation=90, fontsize=7.5, color="#5f6880", fontweight="bold")
        ax.set_yticks(y_ticks)
        ax.yaxis.tick_right()
        ax.yaxis.set_label_position("right")
        ax.tick_params(axis="y", labelsize=7.5, colors="#5f6880", length=0, pad=3, labelright=True, labelleft=True)
        ax.tick_params(axis="x", length=0)
        ax.grid(axis="y", color="#d8deea", linewidth=0.8)
        ax.grid(axis="x", visible=False)
        for tick_label in ax.get_yticklabels():
            tick_label.set_fontweight("bold")
        for tick_label in ax.get_yticklabels(minor=False):
            tick_label.set_fontweight("bold")
        for spine_name in ["top", "right", "left", "bottom"]:
            ax.spines[spine_name].set_visible(False)
        fig.text(0.018, 0.52, "# Trackable Cards Learned", rotation=90, va="center", ha="center", fontsize=8, color="#4f5568", fontweight="bold")
        fig.subplots_adjust(left=0.055, right=0.93, bottom=0.30, top=0.98)

        st.markdown("<div class='progress-chart-shell'>", unsafe_allow_html=True)
        with st.container(key="progress_chart_wrap"):
            with st.container(key="progress_chart_inner_wrap"):
                st.pyplot(fig, clear_figure=True, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
        plt.close(fig)

    if not cloud_history_available:
        st.markdown(
            "<div class='progress-note'>Monthly history needs Supabase connectivity. Current totals are still shown.</div>",
            unsafe_allow_html=True,
        )

    with st.container(key="progress_back_wrap"):
        st.button("BACK", key="progress_back_btn", on_click=close_progress_screen, use_container_width=True)


if st.session_state.active_person in PERSON_LABELS and not st.session_state.person_selector_visible:
    ensure_monthly_progress_snapshot(st.session_state.active_person)


if st.session_state.progress_screen_open:
    render_browser_audio_cleanup()
    render_progress_screen()
    st.stop()

# ========================================================================
# FINAL EXIT
# ========================================================================

if st.session_state.final_exit:
    render_browser_audio_cleanup()
    goodbye_data_uri = goodbye_image_data_uri()
    goodbye_image_markup = (
        f"<div class='exit-image-wrap'><img src='{goodbye_data_uri}' alt='Goodbye axolotl' class='exit-image' /></div>"
        if goodbye_data_uri
        else "<div class='exit-image-wrap'></div>"
    )
    st.markdown(
        "<div class='exit-screen'>"
        "<div class='title-big exit-title'>¡Buen trabajo!</div>"
        + goodbye_image_markup
        + "<div class='title-big-sub exit-subtitle'>SIGUE PRACTICANDO TODOS LOS DÍAS</div>"
        "</div>"
        "<style>"
        ".exit-screen { width: 100%; text-align: center; padding: 0.8rem 0 0.35rem 0; }"
        ".exit-title { display: block; color: #ce1126; margin-bottom: 0.25rem; }"
        ".exit-image-wrap { width: 100%; margin: 0.4rem auto 0.55rem auto; padding: 0.1rem 0 0; box-sizing: border-box; max-width: none; }"
        ".exit-image { display: block; width: 100%; height: auto; margin: 0 auto; }"
        ".exit-subtitle { display: block; margin-top: 0; }"
        ".st-key-exit_btn_row_wrap { width: 100%; margin: 0.65rem 0 0 0; }"
        ".st-key-exit_btn_row_wrap [data-testid='stVerticalBlockBorderWrapper'] { width: min(100%, 23rem); margin: 0 auto; padding: 0 !important; border: none !important; background: transparent !important; box-shadow: none !important; }"
        ".st-key-exit_btn_row_wrap [data-testid='stHorizontalBlock'] { display: flex !important; flex-wrap: nowrap !important; gap: 0.7rem !important; justify-content: center !important; width: 100% !important; }"
        ".st-key-exit_btn_row_wrap [data-testid='stColumn'] { flex: 1 1 0 !important; min-width: 0 !important; }"
        ".st-key-exit_btn_row_wrap [data-testid='stColumn'] > div { width: 100% !important; }"
        ".st-key-exit_restart_wrap,"
        ".st-key-exit_progress_wrap { width: 100%; margin: 0; }"
        ".st-key-exit_restart_wrap [data-testid='stVerticalBlockBorderWrapper'],"
        ".st-key-exit_restart_wrap .stButton,"
        ".st-key-exit_restart_wrap .stButton > button { width: 100%; }"
        ".st-key-exit_restart_wrap .stButton > button { background: linear-gradient(135deg, #006847 0%, #008f5a 100%); color: #ffffff; border: 2px solid #00573b; border-radius: 0.75rem; font-weight: 700; letter-spacing: 0.08em; min-height: 2.75rem; box-shadow: 0 10px 20px rgba(0, 104, 71, 0.18); }"
        ".st-key-exit_restart_wrap .stButton > button:hover { background: linear-gradient(135deg, #00573b 0%, #007e50 100%); border-color: #00442d; color: #ffffff; }"
        ".st-key-exit_progress_wrap [data-testid='stVerticalBlockBorderWrapper'] { width: 100%; margin: 0 auto; padding: 0 !important; border: none !important; background: transparent !important; box-shadow: none !important; }"
        ".st-key-exit_progress_wrap .stButton,"
        ".st-key-exit_progress_wrap .stButton > button { width: 100%; }"
        ".st-key-exit_progress_wrap .stButton > button { background: transparent; color: #e8e4dc; border: 2px solid #008fb3; border-radius: 0.75rem; font-weight: 700; letter-spacing: 0.08em; min-height: 2.75rem; }"
        ".st-key-exit_progress_wrap .stButton > button:hover { background: rgba(255,255,255,0.03); color: #ffffff; border-color: #00a9d4; }"
        "@media (max-width: 767px) { .exit-screen { padding-top: 0.35rem; } .exit-image-wrap { margin-top: 0.25rem; margin-bottom: 0.45rem; } .st-key-exit_btn_row_wrap [data-testid='stVerticalBlockBorderWrapper'] { width: min(100%, 22rem); } }"
        "</style>",
        unsafe_allow_html=True,
    )
    with st.container(key="exit_btn_row_wrap"):
        progress_col, restart_col = st.columns(2)
        with progress_col:
            with st.container(key="exit_progress_wrap"):
                st.button("PROGRESS", key="exit_progress_btn", on_click=open_progress_screen, use_container_width=True)
        with restart_col:
            with st.container(key="exit_restart_wrap"):
                st.button("RESTART", key="exit_restart_btn", on_click=restart_to_splash, use_container_width=True)
    st.stop()

# ========================================================================
# DECK PICKER
# ========================================================================

if st.session_state.selected_csv is None:
    render_browser_audio_cleanup()
    render_header()
    render_menu()
    if st.session_state.menu_open:
        st.stop()
    if st.session_state.person_selector_visible:
        st.stop()
    render_grouped_deck_picker()
    st.stop()

if (
    not is_review_deck(st.session_state.selected_csv)
    and not is_favorites_deck(st.session_state.selected_csv)
    and not is_learned_words_challenge(st.session_state.selected_csv)
    and not is_playback_deck(st.session_state.selected_csv)
    and st.session_state.study_mode is None
):
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
    if is_learned_words_challenge(st.session_state.selected_csv):
        st.session_state.cards = build_learned_words_challenge_cards(st.session_state.active_person)
    elif is_review_deck(st.session_state.selected_csv):
        review_person = review_deck_person(st.session_state.selected_csv)
        review_items = list(st.session_state.review_data.get(review_person, {}).values())
        st.session_state.cards = [
            {"id": None, "word": item["word"], "answer": item["answer"],
             "shown": False, "scored": False, "repeat_score": item["count"], "error_flag": 0}
            for item in review_items
        ]
    elif is_favorites_deck(st.session_state.selected_csv):
        favorites_person = favorites_deck_person(st.session_state.selected_csv)
        favorite_items = list(st.session_state.favorites_data.get(favorites_person, {}).values())
        st.session_state.cards = [
            {
                "id": item.get("source_id"),
                "word": item["word"],
                "answer": item["answer"],
                "shown": False,
                "scored": False,
                "repeat_score": 1,
                "error_flag": 0,
                "source_deck": item.get("source_deck"),
                "source_index": item.get("source_index"),
            }
            for item in favorite_items
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
    if is_playback_deck(st.session_state.selected_csv):
        rebuild_story_order()
    else:
        st.session_state.order = list(range(len(st.session_state.cards)))
        random.shuffle(st.session_state.order)
    st.session_state.index = 0
    st.session_state.loaded_csv = st.session_state.selected_csv
    st.session_state.direction = effective_direction()

if (
    not is_review_deck(st.session_state.selected_csv)
    and not is_favorites_deck(st.session_state.selected_csv)
    and not is_learned_words_challenge(st.session_state.selected_csv)
    and not is_playback_deck(st.session_state.selected_csv)
    and st.session_state.study_mode == "remaining"
    and not st.session_state.cards
):
    clear_deck_progress(st.session_state.active_person, st.session_state.selected_csv)
    st.session_state.study_mode = "all"
    st.session_state.selected_csv = None
    st.rerun()

if is_learned_words_challenge(st.session_state.selected_csv) and not st.session_state.cards:
    go_back_to_deck_picker()
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

if is_playback_deck(st.session_state.selected_csv):
    if st.session_state.index >= len(st.session_state.order):
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
    render_browser_audio_cleanup()
    render_header(summary_mode=True)
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
        if (
            not is_review_deck(st.session_state.selected_csv)
            and not is_favorites_deck(st.session_state.selected_csv)
            and not is_learned_words_challenge(st.session_state.selected_csv)
            and st.session_state.study_mode == "remaining"
        ):
            clear_deck_progress(st.session_state.active_person, st.session_state.selected_csv)
            st.session_state.study_mode = "all"
        st.session_state.quit_requested = True
        st.rerun()

if not st.session_state.order:
    st.stop()

process_pending_ai_examples_action()

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
render_flashcard(prompt, solution, st.session_state.show_answer)
render_buttons(
    st.session_state.show_answer,
    spanish_text,
    spanish_visible_before_answer=spanish_visible_phase == "prompt-visible",
)
render_regular_auto_hidden_buttons()
if st.session_state["regular_auto_mode"]:
    sentence_auto_mode = is_sentence_deck(st.session_state.selected_csv)
    prompt_language = "en" if current_direction == "EN_TO_ES" else "es"
    answer_language = "es" if current_direction == "EN_TO_ES" else "en"
    include_english_audio = st.session_state["regular_auto_include_english"]
    preferred_gender = "female" if (st.session_state.index % 2 == 0) else "male"
    phase = "answer" if st.session_state.show_answer else "prompt"
    phase_text = solution if st.session_state.show_answer else prompt
    phase_language = answer_language if st.session_state.show_answer else prompt_language
    phase_is_spanish = phase_language == "es"
    prompt_should_speak = prompt_language == "es" or include_english_audio
    phase_should_speak = phase_is_spanish or include_english_audio
    phase_starts_sentence_pair = phase == "prompt" or not prompt_should_speak
    phase_delay_seconds = story_pause_seconds_for_text(phase_text) if sentence_auto_mode else (2.0 if st.session_state.show_answer else story_pause_seconds_for_text(prompt))
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
        cue_prompt=st.session_state["regular_auto_cue_prompt"],
        should_speak=phase_should_speak,
        cue_before_speech=st.session_state["regular_auto_cue_prompt"] and sentence_auto_mode and phase_should_speak and phase_starts_sentence_pair,
    )
else:
    render_regular_auto_mode_cleanup()
    inject_tap_reveal(st.session_state.show_answer)
if not st.session_state["regular_auto_mode"] and st.session_state.auto_speak_spanish and spanish_visible_phase and not bool(st.session_state.ai_examples_sentences):
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
