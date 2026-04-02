 # Spanish-English Vocabulary Extraction Ruleset

## 0. INITIAL INSTRUCTIONS: PROCESSING PDF PAGE(S) OR CHAPTER

### 0.1 Attached text file – Instructions
Attached is one or more PDF pages (or a complete chapter PDF – typically 10+ pages with grammar explanations, vocabulary lists, verb conjugation tables, example sentences, exercises, and reading passages).

Follow these steps **in order**:

1. **Scan the entire PDF** to identify its structural sections (see 0.2 below)
2. **Extract vocabulary pairs** according to Section 2 (What to Extract) and Section 2.4 (What NOT to Extract)
3. **Apply all formatting rules** from Sections 1–10 to each pair
4. **Check for duplicates** using Section 10.1
5. **Output the complete CSV** in a single code block
6. **Summarize what was extracted** (see 0.4 below)

### 0.2 Typical Chapter Structure
Most textbook chapters follow this pattern (you may not encounter all sections):

| Section | Extract? | Notes |
|---------|----------|-------|
| Chapter title & intro | **NO** | Instructional text only |
| Grammar/usage rules | **NO** | Meta-language (but extract vocabulary *within* rules) |
| Pronunciation guidance | **NO** | Unless paired with a specific vocabulary word (Section 13.4) |
| Vocabulary lists | **YES** | Core pairs; extract all |
| Conjugation tables | **YES** | Each row is a separate entry (Section 6.2–6.4) |
| Example sentences with translations | **YES** | Extract the paired translations (Section 11) |
| Exercises with instructions | **PARTIAL** | Skip instructions; extract vocabulary lists within exercises |
| Reading comprehension passage | **NO** | Narrative text only |
| Footnoted vocabulary below passage | **YES** | Extract all footnoted definitions (Section 13.7) |
| Comprehension questions | **NO** | Questions are prompts, not vocabulary (Section 13.8) |

### 0.3 Key Extraction Priorities
Process the chapter in this priority order to avoid missing pairs:

1. **Vocabulary lists** (explicitly formatted translations)
2. **Conjugation tables** (each conjugation is a separate entry)
3. **Footnoted vocabulary** in reading passages
4. **Example sentences** with English translations
5. **Exercise vocabulary lists** (ignore instructions and blanks)

### 0.4 Output Summary Format
After extracting all pairs, provide a **summary statement** like this:

```
All pairs extracted. No unclear words detected.

**Summary:**
- Vocabulary lists: [X] pairs
- Conjugation tables: [Y] pairs
- Example sentences: [Z] pairs
- Footnoted terms: [W] pairs
- **Total: [X+Y+Z+W] pairs**

**Sections skipped:**
- Grammar explanations and rules
- Pronunciation guidance
- Exercise instructions
- Narrative reading passages
```

### 0.5 When NOT to Use This Full Process
- **Single vocabulary list or short excerpt:** Jump directly to Section 2 (Content Extraction Rules)
- **Just conjugation tables:** Use Section 6 (Handling Verb Conjugations) and extract all rows
- **Clarifying one problematic pair:** Reference the relevant section (e.g., "Section 3.2 for parentheses handling")

### 0.6 Reference Sections During Extraction
As you work through the PDF, **reference specific sections** for formatting decisions:

- **Parentheses or brackets confusion?** → Section 3
- **Multiple English meanings?** → Section 4
- **Gender markers or plurals?** → Section 5
- **Verb conjugations?** → Section 6
- **Articles with nouns?** → Section 5.1
- **Special characters or accents?** → Section 7
- **Numbers or ordinals?** → Section 9

---

**Now proceed to Section 1 for detailed formatting rules.**

---

## 1. FORMAT SPECIFICATION

### 1.1 Output Format
All extracted pairs must follow this exact format:
```
"English";"Spanish"
```

### 1.2 Quotation Marks
- **REQUIRED:** Both English and Spanish terms must be enclosed in double quotation marks (`"`)
- **NO SPACES:** There are no spaces between the closing quote and the semicolon, or between the semicolon and the opening quote
- **EXAMPLE:** `"to dance";"bailar"` ✓ | `"to dance" ; "bailar"` ✗

### 1.3 Semicolon Separator
- **MANDATORY:** A single semicolon (`;`) separates English from Spanish with no spaces
- **PLACEMENT:** Appears directly after the closing quote of the English term and directly before the opening quote of the Spanish term
- **NEVER:** Use commas, colons, or other delimiters

---

## 2. CONTENT EXTRACTION RULES

### 2.1 Pairing Identification
- Extract only Spanish-English translation pairs found in the PDFs
- Pairs appear in two configurations:
  1. **Side-by-side:** Spanish on left, English italicized on right
  2. **Stacked:** Spanish above English (less common in these textbooks)

### 2.2 Language Direction
- **Spanish term goes on the right** (after semicolon)
- **English term goes on the left** (after opening quote)
- **NEVER reverse:** Do not write `"bailar";"to dance"`

### 2.3 What to Extract
Extract pairs for:
- **Nouns** (with articles: `"the kitchen";"la cocina"`)
- **Verbs** (infinitives: `"to sing";"cantar"` AND conjugated forms: `"I sing";"yo canto"`)
- **Adjectives** (with English translations: `"tall";"alto"`)
- **Adverbs** (e.g., `"while";"mientras"`)
- **Prepositions** (e.g., `"in, on";"en"`)
- **Interrogative words** (e.g., `"How?";"¿Cómo?"`)
- **Phrases and expressions** (e.g., `"at the beginning";"al principio"`)
- **Numbers** (written out: `"twenty-one";"veintiuno"`)
- **Days, months, seasons** (e.g., `"Monday, on Monday";"el lunes"`)

### 2.4 What NOT to Extract
- **Spanish-only content:** If only Spanish appears with no English translation, skip it
- **English-only explanations:** Grammar rules, instructions, or meta-language are ignored
- **Conjugation tables headers:** e.g., "Infinitive," "Stem," "Ending" (these are structural labels, not translations)
- **Pronunciation notes** (unless paired with a vocabulary word)
- **Duplicate pairs:** If the same pair appears multiple times in the PDF, extract it only once
- **Incomplete or fragmented pairs:** If English or Spanish is missing, do not extract

---

## 3. HANDLING BRACKETS [ ] AND PARENTHESES ( )

### 3.1 Brackets [ ]
**Rule:** Convert parentheses in the original text to square brackets in the English translation.

**When brackets appear in source:**
- Source: `"la arqueóloga (archeologist)"`
- Extract as: `"archeologist";"la arqueóloga"`
- If brackets are part of the English meaning, include them:
  - Source: `"entrar (en) to enter (in)"`
  - Extract as: `"to enter [in]";"entrar [en]"`

**When source has parenthetical clarifications:**
- Source: `"tomar (a) half"`
- This indicates "tomar" can mean "to take" or variations; extract the clearest pairing only
- Extract as: `"to take";"tomar"` OR `"[a] half";"la mitad"` (if these are separate translations)

### 3.2 Parentheses in Source Material
**Rule:** Replace curved parentheses `( )` with square brackets `[ ]` in the extracted format.

**Examples:**

| Source | Extraction |
|--------|-----------|
| `el otoño the autumn, the fall` | `"the autumn, the fall";"el otoño"` |
| `entrar (en) to enter (in)` | `"to enter [in]";"entrar [en]"` |
| `tocar to touch, to play (an instrument)` | `"to touch, to play [an instrument]";"tocar"` |
| `tomar to take, to have (something to drink)` | `"to take, to have [something to drink]";"tomar"` |
| `Fifth Avenue (the fifth avenue)` | `"Fifth Avenue [the fifth avenue]";"la quinta avenida"` |

### 3.3 Optional Clarifications
If parentheses indicate optional variations:
- Source: `cómico(a) funny`
- Extract only the base form: `"funny";"cómico"` (the feminine marker is grammatical, not a separate meaning)

### 3.4 Nested or Complex Brackets
If the original has nested structures:
- Source: `"tomar (to have [breakfast, lunch, dinner])"`
- Extract as: `"to have [breakfast, lunch, dinner]";"tomar"`
- Keep inner brackets as they clarify the meaning

---

## 4. HANDLING MULTIPLE ENGLISH MEANINGS

### 4.1 Comma-Separated Meanings
When a Spanish word has multiple English translations separated by commas, **keep all of them in one pair** separated by commas.

**Examples:**
- Source: `el otoño the autumn, the fall`
- Extract as: `"the autumn, the fall";"el otoño"`

- Source: `la noche the night, the evening`
- Extract as: `"the night, the evening";"la noche"`

- Source: `saludable healthy, healthful`
- Extract as: `"healthy, healthful";"saludable"`

### 4.2 Synonyms or Alternative Translations
When multiple translations are offered with equal weight, include all on one line separated by commas.

**Examples:**
- Source: `pasar to pass (by), to happen, to spend (time)`
- Extract as: `"to pass [by], to happen, to spend [time]";"pasar"`

- Source: `leer to read`
- Extract as: `"to read";"leer"` (single meaning — simple extraction)

### 4.3 Context-Dependent Meanings (Advanced Verbs)
For verbs with multiple meanings depending on context:

| Source | Extraction | Notes |
|--------|-----------|-------|
| `deber should, ought to, must (plus infinitive), to owe` | `"should, ought to, must [plus infinitive], to owe";"deber"` | All meanings on one line |
| `ganar to win, to earn` | `"to win, to earn";"ganar"` | Two equal meanings |
| `llevar to carry, to wear` | `"to carry, to wear";"llevar"` | Two primary meanings |

---

## 5. HANDLING ARTICLES AND GENDER MARKERS

### 5.1 Include Articles with Nouns
**Rule:** Include the definite or indefinite article when it appears with the noun.

**Examples:**
- Source: `el agua the water`
- Extract as: `"the water";"el agua"`

- Source: `la mesa the table`
- Extract as: `"the table";"la mesa"`

- Source: `un desorden a mess`
- Extract as: `"a mess";"un desorden"`

- Source: `una vez one time, once`
- Extract as: `"one time, once";"una vez"`

### 5.2 Gender Markers on Adjectives
**Rule:** Extract only the base form; omit gender/number markers in parentheses.

**Examples:**
- Source: `cómico(a) funny`
- Extract as: `"funny";"cómico"` (ignore the feminine marker)

- Source: `sabroso delicious`
- Extract as: `"delicious";"sabroso"` (no marker needed)

### 5.3 Plural Forms
**Rule:** Extract plural nouns when they appear as distinct entries; ignore routine plurals in conjugation tables.

**Examples:**
- Source: `los lunes Mondays, on Mondays`
- Extract as: `"Mondays, on Mondays";"los lunes"`

- Source: `la gente the people`
- Extract as: `"the people";"la gente"`

---

## 6. HANDLING VERB CONJUGATIONS

### 6.1 Infinitive Forms
**Rule:** Always extract infinitives with the English translation "to [verb]".

**Examples:**
- Source: `cantar to sing`
- Extract as: `"to sing";"cantar"`

- Source: `comer to eat`
- Extract as: `"to eat";"comer"`

### 6.2 Conjugated Forms in Tables
**Rule:** Extract each conjugated form paired with its corresponding English pronoun translation.

**Format:**
```
"[pronoun] [verb meaning]";"[spanish pronoun] [conjugated verb]"
```

**Examples from conjugation tables:**

| English | Spanish | Extraction |
|---------|---------|-----------|
| yo canto = I sing | yo canto | `"I sing";"yo canto"` |
| tú cantas = you sing | tú cantas | `"you sing";"tú cantas"` |
| él canta = he sings | él canta | `"he sings";"él canta"` |
| nosotros cantamos = we sing | nosotros cantamos | `"we sing";"nosotros cantamos"` |
| vosotros cantáis = you [pl.] sing | vosotros cantáis | `"you [pl.] sing";"vosotros cantáis"` |
| ellos cantan = they sing | ellos cantan | `"they sing";"ellos cantan"` |
| Uds. cantan = you [pl.] sing | Uds. cantan | `"you [pl.] sing";"Uds. cantan"` |

### 6.3 Conjugation Table Completeness
**Rule:** Extract all conjugations provided, even if the table repeats the same verb multiple times across pages.

**Why?** Each conjugation form is a separate vocabulary entry for flashcard study.

### 6.4 Third-Person Forms with Multiple Pronouns
When the textbook shows that multiple pronouns share the same conjugation:
- Source: `él canta ellos cantan` (he sings, they sing)
- Extract both:
  - `"he sings";"él canta"`
  - `"they sing";"ellos cantan"`

---

## 7. HANDLING SPECIAL CHARACTERS AND ACCENTS

### 7.1 Preserve All Accents
**Rule:** Maintain all Spanish accents and diacritical marks exactly as they appear.

**Examples:**
- `cantáis` (NOT `cantais`)
- `sé` (NOT `se`)
- `dímelo` (NOT `dimelo`)
- `¿Cómo?` (NOT `Como?`)

### 7.2 Inverted Question and Exclamation Marks
**Rule:** Include opening inverted punctuation in Spanish where appropriate.

**Examples:**
- Source: `¿Cómo está? How are you?`
- Extract as: `"How are you?";"¿Cómo está?"`

- Source: `¿Qué? What?`
- Extract as: `"What?";"¿Qué?"`

### 7.3 Tildes and Special Vowels
**Rule:** Always preserve ñ, á, é, í, ó, ú, ü exactly.

**Examples:**
- `niño` (NOT `nino`)
- `mañana` (NOT `manana`)
- `día` (NOT `dia`)

---

## 8. HANDLING PROPER NOUNS AND PLACE NAMES

### 8.1 Capitalization
**Rule:** Preserve capitalization exactly as it appears in source.

**Examples:**
- `Fifth Avenue` (capitalized in English)
- Extract as: `"Fifth Avenue [the fifth avenue]";"la quinta avenida"`

- `Sixth Street`
- Extract as: `"Sixth Street [the sixth street]";"la sexta calle"`

### 8.2 City and Country Names
Extract with English equivalents if provided.

**Example:**
- Source: `México Mexico`
- Extract as: `"Mexico";"México"`

---

## 9. HANDLING NUMBERS AND ORDINALS

### 9.1 Cardinal Numbers
**Rule:** Write out numbers in English, preserve Spanish spelling.

**Examples:**
- Source: `0 cero`
- Extract as: `"zero";"cero"`

- Source: `21 veintiuno`
- Extract as: `"twenty-one";"veintiuno"`

- Source: `100 cien`
- Extract as: `"100";"cien"` OR `"one hundred";"cien"` (both acceptable)

### 9.2 Ordinal Numbers
**Rule:** Write out ordinals in English with proper hyphenation.

**Examples:**
- Source: `primero first`
- Extract as: `"first";"primero"`

- Source: `segundo second`
- Extract as: `"second";"segundo"`

- Source: `veintitrés twenty-three`
- Extract as: `"twenty-three";"veintitrés"`

### 9.3 Compound Numbers
**Rule:** Use hyphens in English compound numbers where standard English does so.

**Examples:**
- `"twenty-one";"veintiuno"`
- `"ninety-nine";"noventa y nueve"`
- `"one hundred and third";"ciento tres"`

---

## 10. DUPLICATE HANDLING

### 10.1 No Repeat Extraction
**Rule:** If an identical pair appears multiple times in the PDFs, extract it only once.

**Rationale:** The same vocabulary word appearing in multiple conjugation tables or example sentences should appear only once in the final CSV.

### 10.2 Near-Duplicates
If slightly different formulations exist:
- Source 1: `"to sing";"cantar"`
- Source 2: `"singing";"cantar"`
- These are different meanings → **extract both** (one is infinitive, one is gerund)

### 10.3 Tracking Duplicates
When writing output: note if a pair was already extracted earlier in the conversation and skip it.

---

## 11. EXAMPLE APPLICATION: COMPLETE WALKTHROUGH

### Sample Source Text:
```
la escuela the school
escolar to study
vosotros estudiáis you [pl.] study
entrañar (to) enter (in)
el otoño the autumn, the fall
¿Quién? (sing.), ¿Quiénes? (pl.) Who?
```

### Extraction Process:

1. **`la escuela the school`**
   - Contains article + noun + English translation ✓
   - Extract as: `"the school";"la escuela"`

2. **`escolar to study`**
   - Verb infinitive with English translation ✓
   - Extract as: `"to study";"escolar"`

3. **`vosotros estudiáis you [pl.] study`**
   - Conjugated form with pronoun and English equivalent ✓
   - Extract as: `"you [pl.] study";"vosotros estudiáis"`

4. **`entrañar (to) enter (in)`**
   - Parentheses around "to" indicate optional; brackets in output
   - Extract as: `"to enter [in]";"entrañar"`

5. **`el otoño the autumn, the fall`**
   - Multiple English meanings separated by comma ✓
   - Extract as: `"the autumn, the fall";"el otoño"`

6. **`¿Quién? (sing.), ¿Quiénes? (pl.) Who?`**
   - Interrogative with gender/number markers in parentheses
   - Markers are grammar notation, not part of meaning
   - Extract as: `"Who?";"¿Quién?"` (could also extract `"Who?";"¿Quiénes?"`)

### Final Output:
```
"the school";"la escuela"
"to study";"escolar"
"you [pl.] study";"vosotros estudiáis"
"to enter [in]";"entrañar"
"the autumn, the fall";"el otoño"
"Who?";"¿Quién?"
```

---

## 12. QUALITY ASSURANCE CHECKLIST

Before finalizing each CSV output:

- [ ] Every line has exactly one semicolon
- [ ] Both English and Spanish are enclosed in double quotes
- [ ] No spaces around the semicolon
- [ ] Spanish is on the right, English on the left
- [ ] All accents and special characters preserved
- [ ] Parentheses converted to brackets where appropriate
- [ ] No duplicate pairs
- [ ] No Spanish-only or English-only fragments
- [ ] All conjugations from tables are extracted
- [ ] Multiple English meanings are comma-separated on one line
- [ ] Articles are included with nouns
- [ ] Infinitives prefixed with "to"
- [ ] Conjugated forms include pronoun + verb meaning

---

## 13. PROCESSING A FULL TEXTBOOK CHAPTER

### 13.1 Chapter Structure Recognition
When an entire chapter PDF is uploaded, the structure typically follows this pattern:

1. **Chapter title and introduction** (usually short explanatory text)
2. **Grammar or usage explanation** (rules, conjugation patterns, pronunciation guidance)
3. **Vocabulary lists** (core extraction targets)
4. **Conjugation tables for verbs** (comprehensive extraction needed)
5. **Example sentences** (paired Spanish-English)
6. **Exercises** (usually fill-in-the-blank or matching; ignore instruction text, extract only vocabulary in questions)
7. **Reading comprehension passage** (often with footnoted vocabulary definitions)
8. **Comprehension questions** (extract questions with Spanish-English pairs if they exist)

### 13.2 Extraction Priority
When processing a full chapter, prioritize in this order:

1. **Vocabulary lists** — these are explicitly formatted translation pairs
2. **Conjugation tables** — each row is a separate entry to extract
3. **Example sentences** — extract pairs that appear in context
4. **Reading passage vocabulary** — footnoted translations; apply all rules
5. **Exercise questions** — only extract if they contain Spanish-English pairs (skip instruction text like "Complete the following sentences")

### 13.3 Handling Repetition Across Chapter
**Rule:** A single verb may appear:
- In the infinitive list at the top
- In a conjugation table
- In multiple example sentences
- In exercises

Extract each **distinct form** (infinitive vs. each conjugation), but only once. Do not duplicate the infinitive + all conjugations + example usages of the same verb.

**Example:**
```
Source appears as:
  cantar (infinitive in vocab list)
  yo canto, tú cantas, él canta (conjugation table)
  Ella canta bien (example sentence)

Extract as:
  "to sing";"cantar"
  "I sing";"yo canto"
  "you sing";"tú cantas"
  "he sings";"él canta"
  
Do NOT extract "She sings well";"Ella canta bien" (this is a full sentence, not vocabulary)
```

### 13.4 Pronunciation Notes in Chapters
**Rule:** Pronunciation notes (marked with 🔊 or "Pronunciation Reminder") are explanatory meta-language and should NOT be extracted, but the vocabulary words they discuss may be extracted if they also appear in vocabulary lists.

**Example:**
```
Pronunciation Reminder: The Spanish d is pronounced like the d in 
English dog when it appears at the beginning of a breath group...

Source: donde, la falda, el conde

Do NOT extract pronunciation explanation. 
DO extract vocabulary if it appears elsewhere:
  "where";"donde" (IF "donde" appears in a vocab list)
```

### 13.5 Grammar Rules and Structural Information
**Rule:** Skip all instructional text about grammar, conjugation patterns, and language rules. Extract only concrete vocabulary pairs.

**Examples to SKIP:**
- "All infinitives end in -ar, -er, or -ir"
- "Verbs are considered regular if there is no change in the stem"
- "To conjugate a regular -ar verb, drop the infinitive ending..."
- "The present tense is used to express the English simple present"

**Examples to EXTRACT:**
- `cantar to sing` (within this instruction: extract the pair)
- Any Spanish-English translation pair, regardless of context

### 13.6 Exercise Section Handling
**Rule:** Skip exercise instructions; extract only Spanish-English vocabulary or question pairs if they appear as distinct translation units.

**Example exercise section:**

```
Exercise 5.1
Complete the following sentences with the correct form of the 
appropriate verb. Choose from the verbs listed below:

bailar, bajar, caminar, cantar, cocinar...

1. Ricardo ___________________ en la piscina.
2. Ella ___________________ mucho porque...
```

**Action:**
- DO NOT extract: "Complete the following sentences..." (instruction)
- DO extract verbs from the list at the top if not already extracted: `"to dance";"bailar"`, etc.
- DO NOT extract the numbered blanks (they're exercises, not vocab)

### 13.7 Reading Comprehension Passage
**Rule:** Reading passages are narrative text, not vocabulary lists. However, **footnoted vocabulary definitions** within or below the passage should be extracted.

**Example:**

```
Una escuela en México
Es el año mil novecientos sesenta y tres...

_________
°la época period of time
°estar seguro(a) to be sure
```

**Action:**
- Skip the narrative paragraph
- Extract the footnoted pairs:
  - `"period of time";"la época"`
  - `"to be sure";"estar seguro[a]"`

### 13.8 Questions Following Reading
**Rule:** Comprehension questions are typically "Answer the following questions in Spanish," but the questions themselves may contain Spanish-English pairs if they're teaching questions.

**Example:**

```
Preguntas
1. ¿Cómo es Guanajuato?
2. ¿Qué estación del año es?
```

**Action:**
- These are exercise prompts, not vocabulary pairs → skip

But if a question contains a vocabulary teaching pair:
```
1. ¿Quién es el profesor? (Who is the teacher?)
```

Then extract: `"Who is the teacher?";"¿Quién es el profesor?"`

### 13.9 Output Organization for Full Chapters
When extracting a complete chapter:

1. **Extract in order of appearance** (but consolidate duplicates)
2. **Group output logically** in the final CSV:
   - Vocabulary lists first
   - Conjugations of each verb in sequence
   - Example sentences and phrases
   - Footnoted terms from reading passages
3. **Note any sections skipped** at the end:
   - "All pairs extracted. No unclear words detected."
   - Or: "Grammar explanations skipped. Pronunciation notes skipped. Exercise instructions skipped."

### 13.10 Full Chapter Extraction Template Response

When you provide a full chapter, the extraction response should follow this pattern:

````
```
"English";"Spanish"
"English";"Spanish"
[... all extracted pairs ...]
```

All pairs extracted. No unclear words detected.

**Summary:**
- Vocabulary lists: [X] pairs
- Conjugation tables: [Y] pairs  
- Example sentences: [Z] pairs
- Footnoted terms: [W] pairs
- **Total: [X+Y+Z+W] pairs**

**Sections skipped:**
- Grammar explanations and rules
- Pronunciation guidance (unless paired with vocabulary)
- Exercise instructions
- Narrative text from reading passages
````

---



## 14. REPORTING UNCLEAR OR PROBLEMATIC PAIRS

### 14.1 Definition of "Unclear"
A pair is **unclear** if any of the following conditions apply:

1. **Unreadable text:** The PDF image quality is poor, blurry, or corrupted, making the Spanish or English illegible
2. **Missing translation:** One side of the pair is present but the other is absent or cut off by page boundaries
3. **Ambiguous pairing:** It is unclear which Spanish term corresponds to which English term (e.g., multiple columns misaligned)
4. **Incomplete or fragmented:** The pair is partial—e.g., only "to" without the verb, or a Spanish word without context
5. **Handwritten or non-standard text:** Annotations, corrections, or handwriting that cannot be reliably interpreted
6. **Context-dependent meaning:** The translation depends on surrounding text that is missing or unclear
7. **OCR errors:** If the PDF has embedded text, OCR corruption may have created gibberish (e.g., "to sing" appears as "to s1ng")

### 14.2 How to Report Unclear Pairs
When you encounter an unclear pair, **halt extraction of that section** and report it in this format:

```
[UNCLEAR - Line X, Page Y]
Source text: [exact text as it appears in PDF]
Reason: [one of: unreadable | missing translation | ambiguous pairing | fragmented | handwritten | context-dependent | OCR error]
Context: [surrounding text or clarification if helpful]
```

### 14.3 Placement of Unclear Reports
Place all unclear pairs in a separate block **after** the extracted CSV pairs, like this:

```
"English";"Spanish"
"English";"Spanish"
[... all extracted pairs ...]

---

**UNCLEAR OR PROBLEMATIC PAIRS:**

[UNCLEAR - Page 5, line 3]
Source text: el ___________ the (text obscured by page crease)
Reason: unreadable
Context: appears in vocabulary list

[UNCLEAR - Page 12, after conjugation table]
Source text: vosotros hab|s (OCR corruption visible)
Reason: OCR error
Context: should probably be "vosotros habláis" but text is corrupted

[UNCLEAR - Page 8, Exercise 5.2, question 1]
Source text: ¿___________ Ud.? [no English equivalent provided]
Reason: missing translation
Context: appears to be an exercise prompt without a translation pair
```

### 14.4 Frequency Threshold
**If fewer than 3 unclear pairs in a chapter:** Report them in the [UNCLEAR] block at the end.

**If 3–10 unclear pairs:** Report them in the [UNCLEAR] block AND note in the summary: "X unclear pairs encountered—see section below."

**If more than 10 unclear pairs in a section:** **STOP extraction of that section** and ask for clarification before continuing. Example:

```
STOPPING EXTRACTION: Pages 14–16 have extensive OCR corruption or image quality issues.
More than 10 pairs are unreadable. Would you like to:
a) Re-upload a clearer version of this section?
b) I can skip these pages and continue with the rest of the chapter?
c) You can manually clarify these terms?
```

### 14.5 User Response Options
When you report unclear pairs, the user can:

1. **Provide clarification:** "That unreadable word on page 5 is 'libro' (the book)"
2. **Re-upload:** "Let me scan that page again with better quality"
3. **Skip the section:** "Just skip pages 14–16 and extract the rest"
4. **Proceed anyway:** "Extract everything you can read, flag the unclear ones"

### 14.6 Handling User Clarification
If the user provides clarification for an unclear pair:

1. **Add it to the extracted CSV** with a note
2. **Mark it as clarified** in a separate comment block if needed

**Example:**
```
"the book";"el libro"  [clarified by user: page 5 was unreadable]
```

### 14.7 Examples of Unclear vs. Clear

| Status | Source | Reason | Action |
|--------|--------|--------|--------|
| **CLEAR** | `el agua the water` | Both sides present and readable | Extract: `"the water";"el agua"` |
| **UNCLEAR** | `el _____ the (image cut off)` | Spanish visible, English missing | Report in [UNCLEAR] block |
| **UNCLEAR** | `la ___ [blurry]` | Entire pair unreadable | Report in [UNCLEAR] block |
| **CLEAR** | `cantar (to sing)` | Both sides clear despite parentheses | Extract: `"to sing";"cantar"` |
| **UNCLEAR** | `yo c@nt0 I sing` | OCR corruption in Spanish | Report in [UNCLEAR] block |
| **CLEAR** | `°lavar to wash` | Superscript marker is structural, not part of meaning | Extract: `"to wash";"lavar"` |
| **UNCLEAR** | `¿Quién? (sing./pl.) Who? [context missing]` | Unclear if gender markers are part of the pair or just grammatical notation | Report in [UNCLEAR] block if ambiguous |

### 14.8 Summary Statement Including Unclear Pairs
Modify the extraction summary (Section 0.4) to include unclear counts:

```
All extractable pairs extracted. [X] unclear pairs encountered.

**Summary:**
- Vocabulary lists: [X] pairs
- Conjugation tables: [Y] pairs
- Example sentences: [Z] pairs
- Footnoted terms: [W] pairs
- **Total extracted: [X+Y+Z+W] pairs**

**Unclear or problematic pairs: [N]**
- See [UNCLEAR] section below for details

**Sections skipped:**
- Grammar explanations and rules
- Pronunciation guidance
- Exercise instructions
- Narrative reading passages
```
---


## 15. Verb Conjugation Entries: Stem Changes, Register Markers, and Subject Conventions

### 15.1 Stem-Change Hints in Curly Braces

When a verb has a stem change, append the change rule in curly braces `{...}` to **every** English entry in the conjugation block. The hint appears on both stem-changed and non-stem-changed rows (nosotros, vosotros) for consistency.

Supported patterns:

- `{e > ie}` — e.g. cerrar, entender, querer
- `{o > ue}` — e.g. almorzar, poder, volver
- `{u > ue}` — e.g. jugar
- `{e > i}`  — e.g. pedir, servir, sonreír

Example (cerrar):

```
"I close {e > ie}";"cierro"
"you close [sing, inf] {e > ie}";"cierras"
"he, she, you close [sing, formal] {e > ie}";"cierra"
"we close {e > ie}";"cerramos"
"you close [pl] {e > ie}";"cerráis"
"they close {e > ie}";"cierran"
```

The hints in `{...}` are optional display elements — they can be toggled off in the flashcard app's Settings (hamburger menu).

---

### 15.2 Irregular yo Form Only

When only the yo form is irregular (no stem change throughout), tag the yo row with `[irreg yo]` and leave all other rows untagged.

```
"I hear [irreg yo]";"oigo"
"you hear [sing, inf]";"oyes"
"he, she, you hear [sing, formal]";"oye"
"we hear";"oímos"
"you hear [pl]";"oís"
"they hear";"oyen"
```

---

### 15.3 Register and Number Markers in Square Brackets

Use square brackets `[...]` in the English column to disambiguate person, number, and formality. The Spanish column never includes subject pronouns (yo, tú, él, etc.).

| Situation | English tag | Example Spanish |
|---|---|---|
| 2nd person singular, informal | `[sing, inf]` | `hablas` |
| 2nd person singular, formal (Ud.) | `[sing, formal]` | `habla` |
| 2nd person plural (vosotros / Uds.) | `[pl]` | `hablan` |

Bracket tags and curly-brace hints can combine:

```
"you close [sing, inf] {e > ie}";"cierras"
"he, she, you close [sing, formal] {e > ie}";"cierra"
```

---

### 15.4 The Five Conjugation Rows (Mexican Spanish)

Every verb block produces exactly **five rows**. The vosotros form is retained in the Spanish column when the book supplies it, but the English tag is `[pl]` — vosotros is not used in Mexican (Latin American) Spanish.

| Row | English subject phrase | Notes |
|---|---|---|
| 1 | `I verb` | yo form |
| 2 | `you verb [sing, inf]` | tú form |
| 3 | `he, she, you verb [sing, formal]` | él/ella/Ud. form |
| 4 | `we verb` | nosotros form |
| 5 | `you verb [pl]` | vosotros/Uds. form; `[pl]` only |

Row 5 uses the vosotros conjugation when the book gives it, or the Uds. conjugation when vosotros is absent.

---

### 15.5 Spanish Column Conventions

- **Never** include subject pronouns (yo, tú, él, ella, Ud., nosotros, vosotros, ellos, ellas, Uds.) in the Spanish column.
- Include accents and special characters exactly as printed: `é`, `í`, `ó`, `ú`, `ü`, `ñ`, `¿`, `¡`.
- For entries using `Ud.` / `Uds.` in the source, the Spanish column contains only the conjugated verb form.


