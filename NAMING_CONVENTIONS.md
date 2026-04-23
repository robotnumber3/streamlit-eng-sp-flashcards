# Flashcard Naming Conventions

This guide defines the current naming system for folders and CSV files in this project.

The app now reads most deck meaning from folder placement first. Filenames still matter for two reasons:

1. every CSV filename must remain unique across the whole `csv` tree
2. filenames should stay short and readable for the learner

## Main Rule

Put the deck in the correct folder first.

Then use a short filename that adds only the detail the folder does not already provide.

Example:

- a file in `Verbs/01 Present Tense/03 Stories/` does not need the word `story` for the app to treat it as a story deck
- a file in `Verbs/01 Present Tense/02 Sentences/` does not need the word `sentence` for the app to treat it as a sentence deck

## Two Naming Modes

### 1. Standard Readable Code Naming

This is the default for the current project.

Use short, memorable tokens such as:

- `Inf`
- `Pres`
- `Past`
- `MixedTense`
- `Conj`
- `Sent`
- `Story`
- `Dialog`
- `Situ`
- `Reg`
- `Irreg`
- `Refl`
- `StemChange`
- `AR`
- `ER`
- `IR`
- `Mix`
- `Adj`
- `Adv`
- `Conjunct`
- `Prep`
- `Pron`
- `Noun`
- `Verb`

This keeps names readable while still making them unique.

### 2. Grouped Picker Naming

Use `_p` and `_c1`, `_c2`, `_c3`, and so on only when you want items to stay grouped together in a guaranteed picker order.

Examples:

- `Adj_01_p.csv`
- `Adj_01_Stories_c1`
- `Adj_01_Dialog_c2.csv`

The picker hides `_p` and `_cN` from the display label.

## Current Token Meanings

### Tense Or Stage

- `Inf` = infinitives
- `Pres` = present tense
- `Past` = past tense
- `Fut` = future tense
- `MixedTense` = decks that intentionally mix tenses

### Deck Type

- `Conj` = conjugations
- `Sent` = sentences
- `Story` = stories
- `Dialog` = dialogs
- `Situ` = situations
- `Ex` = exercises
- `Review` = review
- `Quiz` = quiz

### Verb Group

- `Reg` = regular
- `Irreg` = irregular
- `Refl` = reflexive
- `StemChange` = stem-changing
- `AR` = regular `-ar`
- `ER` = regular `-er`
- `IR` = regular `-ir`
- `Mix` = mixed families inside one tense or section

### Parts Of Speech

- `Adj` = adjective
- `Adv` = adverb
- `Conjunct` = conjunction
- `Prep` = preposition
- `Pron` = pronoun
- `Noun` = noun
- `Verb` = verb

## Recommended Filename Pattern

Use this pattern when a code-style filename is helpful:

`[Stage]_[Type]_[Group]_[Number].csv`

Examples:

- `Inf_Reg_AR_01.csv`
- `Pres_Conj_Reg_AR_01.csv`
- `Pres_Sent_Irreg_01.csv`
- `Pres_Story_Reg_Mix_01a.csv`

When needed, add one more descriptive token before the number:

`[Stage]_[Type]_[Topic]_[Number].csv`

Examples:

- `Pres_Sent_Ser_Estar_01_EN_ES.csv`
- `Pres_Sent_Tengo_Estoy_01.csv`
- `Pres_Conj_Irreg_StemChange_01.csv`

## Why This System Works

It balances three things:

1. short enough for learners to read
2. clear enough that the meaning is easy to remember
3. unique enough to avoid filename collisions elsewhere in `csv`

## What To Avoid

Avoid very long legacy-style names like:

- `PoS_verbs_prs_reg_ar_core_master_01.csv`

Avoid overly short names that will collide later, such as:

- `Reg_AR_01.csv`
- `Story_01.csv`
- `Mix_01.csv`

Avoid inconsistent forms like mixing:

- `Prs` and `Pres`
- `Conjunct` and `Conjunction`
- `Prep` and `Preposition`

Use one standard form and keep it consistent.

## Folder And File Label Rule

Use Sentence Case for the readable tokens in both filenames and grouped child folders.

Use:

- singular labels for individual files
- plural labels for folders that contain multiple items

Examples:

- `Adj_01_Story_01a.csv`
- `Adj_01_Stories_c1`
- `Pres_Story_Reg_AR_01.csv`
- `03 Stories/`

This means `Story` and `Stories` are both valid when they are doing different jobs:

- `Story` = one file
- `Stories` = one folder that contains multiple story files

## Important Distinction

Use:

- `Conj` = conjugation
- `Conjunct` = conjunction

Do not use `Conj` for both. In this project, `Conj` is reserved for verb conjugation decks.

## Verbs Standard In Use Now

The active verb files now use this style:

### Infinitives

- `Inf_Reg_AR_01.csv`
- `Inf_Reg_ER_01.csv`
- `Inf_Reg_IR_01.csv`
- `Inf_Reg_Mix_01.csv`
- `Inf_Refl_01.csv`

### Present Tense Conjugations

- `Pres_Conj_Reg_AR_01.csv`
- `Pres_Conj_Reg_AR_02.csv`
- `Pres_Conj_Reg_ER_01.csv`
- `Pres_Conj_Reg_ER_02.csv`
- `Pres_Conj_Reg_IR_01.csv`
- `Pres_Conj_Irreg_StemChange_01.csv`

### Present Tense Sentences

- `Pres_Sent_Reg_AR_01.csv`
- `Pres_Sent_Reg_ER_01.csv`
- `Pres_Sent_Reg_IR_01.csv`
- `Pres_Sent_Reg_Mix_01.csv`
- `Pres_Sent_Mix_01.csv`
- `Pres_Sent_Irreg_01.csv`
- `Pres_Sent_Irreg_StemChange_01.csv`
- `Pres_Sent_Refl_01.csv`
- `Pres_Sent_Ser_Estar_01_EN_ES.csv`

### Present Tense Stories

- `Pres_Story_Reg_AR_01.csv`
- `Pres_Story_Reg_ER_01.csv`
- `Pres_Story_Reg_IR_01.csv`
- `Pres_Story_Reg_Mix_01a.csv`

## Other Parts Of Speech Standard In Use Now

The active non-verb files now use this style:

- `Adj_01_p.csv`
- `Adj_01_Stories_c1`
- `Adj_01_Story_01a.csv`
- `Adv_01.csv`
- `Conjunct_01.csv`
- `Noun_01.csv`
- `Prep_01.csv`
- `Prep_Sent_01.csv`
- `Pron_01.csv`

## Legacy Exception

`EN_ES` is still a live exception.

If a deck depends on forced English-to-Spanish direction, keep `EN_ES` in the filename.

Example:

- `Pres_Sent_Ser_Estar_01_EN_ES.csv`

## Folder-First Behavior

The app now prefers folder names to determine deck behavior.

Examples:

- a file inside `Stories` is treated as a story deck
- a file inside `Dialogs` is treated as a dialog deck
- a file inside `Sentences` is treated as a sentence deck
- a file inside `Conjugations` is treated as a conjugation deck

That means filenames do not need to repeat those full words just for app behavior.

## Grouped Picker Naming Rules

Use grouped naming only when picker order matters.

### Parent

- `BaseName_p.csv`

### Child

- `BaseName_label_c1.csv`
- `BaseName_label_c2.csv`

Example:

- `Adj_01_p.csv`
- `Adj_01_Stories_c1`
- `Adj_01_Dialog_c2.csv`

## Bottom Line

Use the folder for the big category.

Use short readable filename tokens for the remaining detail.

For current verb work, the project standard is:

- `Inf`
- `Pres`
- `Conj`
- `Conjunct`
- `Sent`
- `Story`
- `Stories`
- `Reg`
- `Irreg`
- `Refl`
- `StemChange`
- `AR`
- `ER`
- `IR`
- `Mix`

Keep CSV filenames unique across the full `csv` tree.