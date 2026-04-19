import csv
import os
import re

# List of files to process
files = [
    "PoS_reg_ER_verbs_sentences.csv",
    "PoS_reg_IR_verbs_sentences.csv",
    "PoS_reg_verbs_AR_sentences.csv"
]

# Use the current working directory as the base
base_dir = os.path.dirname(__file__)

def process_answer(answer):
    match = re.match(r'(\([^)]+\)\s*)(\w+)(.*)', answer)
    if not match:
        return answer if answer.endswith('.') else answer + '.'
    person, first_word, rest = match.groups()
    new_answer = f"{person}{first_word.capitalize()}{rest}"
    new_answer = new_answer.rstrip('. ') + '.'
    return new_answer

for filename in files:
    path = os.path.join(base_dir, filename)
    if not os.path.exists(path):
        print(f"File not found: {filename}")
        continue
    with open(path, newline='', encoding='utf-8') as f:
        rows = list(csv.reader(f, delimiter=';'))
    for i in range(1, len(rows)):
        answer = rows[i][2].strip('"')
        rows[i][2] = f'"{process_answer(answer)}"'
    with open(path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f, delimiter=';')
        writer.writerows(rows)

print("All files processed.")
