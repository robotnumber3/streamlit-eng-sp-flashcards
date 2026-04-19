import csv
import os
import re

files = [
    "PoS_reg_ER_verbs_sentences.csv",
    "PoS_reg_IR_verbs_sentences.csv",
    "PoS_reg_verbs_AR_sentences.csv"
]

def process_answer(answer):
    match = re.match(r'(\([^)]+\)\s*)(\w+)(.*)', answer)
    if not match:
        return answer.rstrip('. ') + '.'
    person, first_word, rest = match.groups()
    new_answer = f"{person}{first_word.capitalize()}{rest}"
    new_answer = new_answer.rstrip('. ') + '.'
    return new_answer

for filename in files:
    with open(filename, newline='', encoding='utf-8') as f:
        rows = list(csv.reader(f, delimiter=';', quotechar='"'))
    for i in range(1, len(rows)):
        row = [field.strip('"') for field in rows[i]]
        row[2] = process_answer(row[2])
        rows[i] = [f'"{field}"' for field in row]
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        for row in rows:
            f.write(';'.join(row) + '\n')

print("Formatting and capitalization fixed.")
