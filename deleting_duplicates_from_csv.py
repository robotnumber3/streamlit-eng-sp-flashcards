import pandas as pd
import os

primary_path = "/Volumes/Squallywag/Python/Current Python Projects/streamlit_eng_sp_flashcards/csv/PoS_verbs_reg_PRIMARY.csv"
huge_path = "/Volumes/Squallywag/Python/Current Python Projects/streamlit_eng_sp_flashcards/csv/PoS_verbs_reg_HUGE.csv"
output_path = "/Volumes/Squallywag/Python/Current Python Projects/streamlit_eng_sp_flashcards/csv/PoS_verbs_reg_HUGE_filtered.csv"

# PRIMARY is normal CSV with commas
primary_df = pd.read_csv(primary_path)

# HUGE uses semicolons
huge_df = pd.read_csv(huge_path, sep=";", on_bad_lines="skip")

print("PRIMARY columns:", primary_df.columns.tolist())
print("HUGE columns:", huge_df.columns.tolist())

primary_verbs = set(primary_df["answer"].str.strip().str.lower())

filtered_df = huge_df[~huge_df["answer"].str.strip().str.lower().isin(primary_verbs)]
filtered_df = filtered_df.reset_index(drop=True)

filtered_df.to_csv(output_path, index=False)

print("Done! Saved to:", os.path.abspath(output_path))
