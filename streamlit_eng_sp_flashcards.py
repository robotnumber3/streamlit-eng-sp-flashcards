# streamlit_eng_sp_flashcards.py

import streamlit as st
import random
import os
import pandas as pd


# ------------------------------------------------------------------------

# --- CSV FOLDER ---
CSV_FOLDER = os.path.join(os.path.dirname(__file__), "csv")

# --- FIND CSV FILES ---
csv_files = [
    f for f in os.listdir(CSV_FOLDER)
    if f.endswith(".csv")
]

# --- SESSION STATE INITIALIZATION ---
if "selected_csv" not in st.session_state:
    st.session_state.selected_csv = None

if "cards" not in st.session_state:
    st.session_state.cards = []

if "order" not in st.session_state:
    st.session_state.order = []

if "index" not in st.session_state:
    st.session_state.index = 0

if "show_answer" not in st.session_state:
    st.session_state.show_answer = False

if "direction" not in st.session_state:
    st.session_state.direction = random.choice(["EN_TO_ES", "ES_TO_EN"])

if "quit_requested" not in st.session_state:
    st.session_state.quit_requested = False

if "final_exit" not in st.session_state:
    st.session_state.final_exit = False

if "loaded_csv" not in st.session_state:
    st.session_state.loaded_csv = None

# --- IF NO CSV SELECTED, SHOW PICKER ---
if st.session_state.selected_csv is None:
    st.title("Choose a deck")

    deck_options = ["-- Choose a deck --", *csv_files]
    selected = st.selectbox("Available CSV files:", deck_options, index=0)

    if selected != deck_options[0]:
        # Set deck and reset deck-related state
        st.session_state.selected_csv = selected
        st.session_state.cards = []
        st.session_state.order = []
        st.session_state.index = 0
        st.session_state.show_answer = False
        st.session_state.quit_requested = False
        st.session_state.final_exit = False
        st.session_state.loaded_csv = None

        st.rerun()

    st.stop()

# --- LOAD THE SELECTED CSV ---
if st.session_state.loaded_csv != st.session_state.selected_csv or not st.session_state.cards:
    df = pd.read_csv(os.path.join(CSV_FOLDER, st.session_state.selected_csv))

    st.session_state.cards = [
        {
            "word": row["word"],
            "answer": row["answer"],
            "shown": False,
            "repeat_score": 1,
            "error_flag": 0,
        }
        for _, row in df.iterrows()
    ]

    st.session_state.order = list(range(len(st.session_state.cards)))
    random.shuffle(st.session_state.order)
    st.session_state.index = 0
    st.session_state.loaded_csv = st.session_state.selected_csv




# -----------------------------------------------------------------------------------







    
    


# --- FINAL EXIT SCREEN ---
if "final_exit" in st.session_state and st.session_state.final_exit:
    st.title("Great work! Keep practicing!")
    st.stop()


# --- LARGE FONT FOR TRANSLATE + ANSWER ---
st.markdown(
    """
    <style>
    .flashcard-text {
        font-size: 1.8rem !important;
        font-weight: 400;
    }
    .flashcard-text strong {
        font-weight: 700;
    }
    </style>
    """,
    unsafe_allow_html=True,
)
# -----------------------------------------------------------------------------------

# --- LIVE STATS HUD ---
total_cards = len(st.session_state.cards)
shown_cards = sum(1 for current_card in st.session_state.cards if current_card["shown"])
remaining_cards = total_cards - shown_cards

correct_count = sum(
    1
    for current_card in st.session_state.cards
    if current_card["repeat_score"] == 0 and current_card["shown"]
)
repeat_count = sum(1 for current_card in st.session_state.cards if current_card["error_flag"] == 1)

accuracy = (correct_count / shown_cards * 100) if shown_cards > 0 else 0
missed = (repeat_count / shown_cards * 100) if shown_cards > 0 else 0

progress_segments = 10
filled = int((shown_cards / total_cards) * progress_segments) if total_cards > 0 else 0
bar = "█" * filled + "░" * (progress_segments - filled)
percent = int((shown_cards / total_cards) * 100) if total_cards > 0 else 0

st.markdown(f"**Completed:** [{bar}] {percent}%")
st.markdown(
    f"**Correct:** {correct_count} &nbsp;&nbsp;&nbsp; "
    f"**Repeat:** {repeat_count} &nbsp;&nbsp;&nbsp; "
    f"**Remaining:** {remaining_cards}"
)
st.markdown(
    f"**Accuracy:** {accuracy:.0f}% &nbsp;&nbsp;&nbsp; "
    f"**Missed:** {missed:.0f}%"
)


# --- CALLBACKS ---
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


def request_quit():
    st.session_state.quit_requested = True


def schedule_repeat(card_index, repeat_score):
    next_position = st.session_state.index + 1
    remaining_cards = len(st.session_state.order) - next_position

    if remaining_cards <= 0:
        st.session_state.order.append(card_index)
        return

    if repeat_score >= 2:
        midpoint_offset = max(1, remaining_cards // 2)
        window_size = max(1, remaining_cards // 6)
        lower_bound = max(next_position, next_position + midpoint_offset - window_size)
        upper_bound = min(len(st.session_state.order), next_position + midpoint_offset + window_size)
        insert_at = random.randint(lower_bound, upper_bound)
    else:
        insert_at = random.randint(next_position, len(st.session_state.order))

    insert_at = min(insert_at, len(st.session_state.order))
    st.session_state.order.insert(insert_at, card_index)


def advance_card():
    current_index = current_card_index()
    current_card = st.session_state.cards[current_index]
    current_card["shown"] = True

    if current_card["repeat_score"] > 0:
        schedule_repeat(current_index, current_card["repeat_score"])

    st.session_state.index += 1
    st.session_state.show_answer = False
    st.session_state.direction = random.choice(["EN_TO_ES", "ES_TO_EN"])


def current_card_index():
    return st.session_state.order[st.session_state.index]




# --- QUIT SCREEN ---
if st.session_state.quit_requested:

    st.subheader("Session Summary")

    # --- END‑OF‑SESSION SUMMARY ---
    total_cards = len(st.session_state.cards)
    shown_cards = sum(1 for c in st.session_state.cards if c["shown"])
    correct_count = sum(1 for c in st.session_state.cards if c["repeat_score"] == 0 and c["shown"])
    repeat_count = sum(1 for c in st.session_state.cards if c["error_flag"] == 1)

    accuracy = (correct_count / shown_cards * 100) if shown_cards > 0 else 0
    missed = (repeat_count / shown_cards * 100) if shown_cards > 0 else 0

    cards_needing_repeats = sum(
        1 for c in st.session_state.cards
        if c["shown"] and c["error_flag"] == 1
    )

    perfect_first_try = sum(
        1 for c in st.session_state.cards
        if c["shown"] and c["repeat_score"] == 0 and c["error_flag"] == 0
    )

    avg_repeat_score = (
        sum(c["repeat_score"] for c in st.session_state.cards if c["shown"]) / shown_cards
        if shown_cards > 0 else 0
    )

    st.markdown(f"- **Total Cards Shown:** {shown_cards}")
    st.markdown(f"- **Correct:** {correct_count}")
    st.markdown(f"- **Repeat Needed:** {repeat_count}")
    st.markdown(f"- **Cards Needing Repeats:** {cards_needing_repeats}")
    st.markdown(f"- **Perfect on First Try:** {perfect_first_try}")
    st.markdown(f"- **Average Repeat Score:** {avg_repeat_score:.2f}")
    st.markdown(f"- **Accuracy:** {accuracy:.0f}%")
    st.markdown(f"- **Missed:** {missed:.0f}%")

    # --- STYLE QUIT NOW + START NEW SESSION BUTTONS ---
    st.markdown(
        """
        <style>
        /* Quit Now (red) */
        .st-key-quitnow_wrap div[data-testid="stButton"] > button {
            background-color: #ffd9d9;
            border-color: #b22222;
            color: #b22222 !important;
            min-height: 3.25rem;
            font-size: 1.6rem;
            font-weight: 700;
            border-radius: 0.85rem;
            border-width: 2px;
            width: 100%;
        }

        /* Start New Session (green) */
        .st-key-newsession_wrap div[data-testid="stButton"] > button {
            background-color: #d7f7d4;
            border-color: #2e8b57;
            color: #1f7a1f !important;
            min-height: 3.25rem;
            font-size: 1.6rem;
            font-weight: 700;
            border-radius: 0.85rem;
            border-width: 2px;
            width: 100%;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # --- QUIT NOW BUTTON ---
    with st.container(key="quitnow_wrap"):
        if st.button("Quit Now", key="quitnow_btn"):
            st.session_state.final_exit = True
            st.rerun()

    # --- START NEW SESSION BUTTON ---
    with st.container(key="newsession_wrap"):
        if st.button("Start New Session", key="newsession_btn"):
            # Reset only your app’s state
            st.session_state.selected_csv = None
            st.session_state.loaded_csv = None
            st.session_state.cards = []
            st.session_state.order = []
            st.session_state.index = 0
            st.session_state.show_answer = False
            st.session_state.quit_requested = False
            st.session_state.final_exit = False

            st.rerun()













# --- END OF DECK CHECK ---
if st.session_state.cards and st.session_state.order:
    if st.session_state.index >= len(st.session_state.order):
        st.session_state.quit_requested = True
        st.rerun()


# --- GET CURRENT CARD ---
if not st.session_state.order:
    st.stop()
card_idx = current_card_index()
card = st.session_state.cards[card_idx]

word = card["word"]
answer = card["answer"]

# --- DISPLAY CARD ---
if st.session_state.direction == "EN_TO_ES":
    prompt = word
    solution = answer
else:
    prompt = answer
    solution = word

st.markdown(f"<div class='flashcard-text'>Translate: <strong>{prompt}</strong></div>", unsafe_allow_html=True)

# --- BEFORE ANSWER IS SHOWN ---
if not st.session_state.show_answer:

    # Green arrow + Quit button side by side
    colA, colB, _ = st.columns([0.12, 0.12, 0.76])

    # --- GREEN ARROW BUTTON (styled like ✓ button) ---
    with colA:
        with st.container(key="showanswer_wrap"):
            st.markdown(
                """
                <style>
                .st-key-showanswer_wrap div[data-testid="stButton"] > button {
                    background-color: #d7f7d4;      /* same green as ✓ */
                    border-color: #2e8b57;
                    color: #1f7a1f !important;
                    min-height: 3.25rem;
                    font-size: 2.0rem;              /* large arrow */
                    font-weight: 700;
                    border-radius: 0.85rem;
                    border-width: 2px;
                }
                </style>
                """,
                unsafe_allow_html=True,
            )
            st.button("→", key="showanswer_btn", on_click=reveal_answer)

    # --- RED STOP SIGN BUTTON (Quit Immediately) ---
    with colB:
        with st.container(key="quitbefore_wrap"):
            st.markdown(
                """
                <style>
                .st-key-quitbefore_wrap div[data-testid="stButton"] > button {
                    background-color: #ffd9d9;
                    border-color: #b22222;
                    color: #b22222 !important;
                    min-height: 3.25rem;
                    font-size: 1.6rem;
                    font-weight: 700;
                    border-radius: 0.85rem;
                    border-width: 2px;
                }
                </style>
                """,
                unsafe_allow_html=True,
            )
            if st.button("🛑", key="quitbefore_btn"):
                st.session_state.quit_requested = True
                st.rerun()






# --- AFTER ANSWER IS SHOWN ---
else:
    # "Answer" label not bold, answer bold
    st.markdown(f"<div class='flashcard-text'>Answer:   <strong>{solution}</strong></div>", unsafe_allow_html=True)

    # Styling for ✓ and ? buttons only
    st.markdown(
        """
        <style>
        div[data-testid="stButton"] > button {
            width: 100%;
            min-height: 3.25rem;
            font-size: 1.6rem;
            font-weight: 700;
            border-radius: 0.85rem;
            border-width: 2px;
        }

        /* Correct button (green) */
        .st-key-correct_wrap div[data-testid="stButton"] > button {
            background-color: #d7f7d4;
            border-color: #2e8b57;
            color: #1f7a1f !important;
        }

        /* Repeat button (yellow) */
        .st-key-repeat_wrap div[data-testid="stButton"] > button {
            background-color: #fff4bf;
            border-color: #d4a017;
            color: #d4a017 !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Two buttons: ✓ and ?
    col1, col2, _ = st.columns([0.12, 0.12, 0.76])

    with col1:
        with st.container(key="correct_wrap"):
            st.button("✓", key="correct_btn", on_click=mark_correct)

    with col2:
        with st.container(key="repeat_wrap"):
            st.button("?", key="repeat_btn", on_click=mark_repeat)
