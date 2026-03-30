# Spanish Flashcards - Streamlit app

### Safe checklist for adding many CSV files without breaking the app:

1. Put every new deck in the existing `csv` folder.

2. Make sure every file ends with `.csv`.
   Good examples:
   `food.csv`
   `travel_phrases.csv`
   `verbs_past_tense.csv`

 
3. Make sure every CSV uses the same two headers:

```
word,answer
```

4. Make sure the first row is the header row.

```
word,answer
apple,manzana
dog,perro
```

5. Do not use different column names like:
   `english,spanish`
   `prompt,response`
   `front,back`
   The current app expects exactly:
   `word`
   `answer`

6. Avoid blank rows at the bottom of the file.
   Blank rows can create messy or empty cards.

7. Avoid duplicate filenames.
   Each deck file should have its own unique name.

<br><br><br>

8. Use simple filenames.
   Best practice:
   `animals.csv`
   `food.csv`
   `travel.csv`
   `household_words.csv`

9. After copying in new CSVs, test locally with:
```bash
streamlit run streamlit_eng_sp_flashcards.py
```

10.  Verify three things in the app:
   1. the new files appear in the deck picker
   2. the picker is alphabetized
   3. opening a few decks actually shows the expected cards

11.  Then push the new files to GitHub:
```bash
git add .
git commit -m "Add new flashcard decks"
git push
```

12.  Wait for Streamlit Cloud to redeploy.
   Then test the live app too.

Practical batch workflow for 30 to 40 files:

- Copy all new CSVs into the `csv` folder.
- Open 2 or 3 of them and confirm the headers are `word,answer`.
- Run the app locally.
- Confirm the new decks appear alphabetically.
- Commit and push.

<br><br><br>

### One thing to watch:

If even one CSV has the wrong columns, the app can fail when that deck is selected, because this code reads:

```python
row["word"]
row["answer"]
```

So consistency across files matters.

If you want, I can do one more improvement next:

- add validation so the app shows a friendly error when a CSV has the wrong columns instead of crashing
- make deck names prettier in the dropdown, for example turning `travel_phrases.csv` into `Travel Phrases`
