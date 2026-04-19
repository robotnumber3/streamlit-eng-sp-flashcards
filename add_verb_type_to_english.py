import csv
import re

input_file = "PoS_reg_verbs_PRIMARY_csv.csv"
output_file = "PoS_reg_verbs_PRIMARY_csv.csv"

def get_verb_type(spanish):
    if spanish.endswith("ar"):
        return "-ar"
    elif spanish.endswith("er"):
        return "-er"
    elif spanish.endswith("ir"):
        return "-ir"
    else:
        return ""

rows = []
with open(input_file, newline='', encoding='utf-8') as f:
    reader = csv.reader(f)
    header = next(reader)
    rows.append(header)
    for row in reader:
        if len(row) != 3:
            rows.append(row)
            continue
        eng = row[1]
        spa = row[2]
        verb_type = get_verb_type(spa)
        if verb_type:
            # Insert {type} before the closing quote, preserving quotes
            if not re.search(r'\{-[aei]r\}', eng):
                eng = eng.rstrip('"') + f' {{{verb_type}}}'
        row[1] = eng
        rows.append(row)

with open(output_file, 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f, quoting=csv.QUOTE_ALL)
    writer.writerows(rows)

print("Verb types added to English column.")
