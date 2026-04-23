# Verbs Naming Quick Reference

This is a short printable cheat sheet for naming files in the active Verbs section.

For the full rules, examples, and background, see:

- `NAMING_CONVENTIONS.md`
- `VERBS_ORGANIZATION.md`

## Main Rule

1. Put the deck in the correct folder first.
2. Use a short, readable filename.
3. Keep every CSV filename unique across the whole `csv` tree.
4. Keep `EN_ES` only when the deck must stay forced English to Spanish.

## Core Filename Pattern

`[Stage]_[Type]_[Group]_[Number].csv`

Examples:

- `Inf_Reg_AR_01.csv`
- `Pres_Conj_Reg_AR_01.csv`
- `Pres_Sent_Irreg_01.csv`
- `Pres_Story_Reg_Mix_01a.csv`

If needed, add a topic before the number:

`[Stage]_[Type]_[Topic]_[Number].csv`

Examples:

- `Pres_Sent_Ser_Estar_01_EN_ES.csv`
- `Pres_Sent_Tengo_Estoy_01.csv`
- `Pres_Sent_Want_Like_Have_01.csv`

## Token Key

### Stage

- `Inf` = infinitives
- `Pres` = present tense
- `Past` = past tense
- `Fut` = future tense
- `MixedTense` = mixed tenses

### Type

- `Conj` = conjugations
- `Sent` = sentences
- `Story` = single story file
- `Dialog` = dialogs
- `Situ` = situations
- `Ex` = exercises
- `Review` = review
- `Quiz` = quiz

### Group

- `Reg` = regular
- `Irreg` = irregular
- `Refl` = reflexive
- `StemChange` = stem-changing
- `AR` = regular `-ar`
- `ER` = regular `-er`
- `IR` = regular `-ir`
- `Mix` = mixed verb families

## Verb Folder Map And Naming Examples

```text
Verbs/
  00 Infinitives/
    01 Regular -AR/
    02 Regular -ER/
    03 Regular -IR/
    04 Regular (AR, ER, IR)/
    05 Irregular/
    06 Reflexive/

  01 Present Tense/
    01 Conjugations/
    02 Sentences/
    03 Stories/
      01 Regular -AR/
      02 Regular -ER/
      03 Regular -IR/
      04 Regular (AR, ER, IR)/
    04 Dialogs/
    05 Situations/
    06 Exercises/
    07 Review/
    08 Quiz/
```

<br><br><br><br><br><br><br>

## Section-By-Section Examples

### 00 Infinitives

| Folder | Use This Pattern | Example |
|---|---|---|
| `01 Regular -AR` | `Inf_Reg_AR_##.csv` | `Inf_Reg_AR_01.csv` |
| `02 Regular -ER` | `Inf_Reg_ER_##.csv` | `Inf_Reg_ER_01.csv` |
| `03 Regular -IR` | `Inf_Reg_IR_##.csv` | `Inf_Reg_IR_01.csv` |
| `04 Regular (AR, ER, IR)` | `Inf_Reg_Mix_##.csv` | `Inf_Reg_Mix_01.csv` |
| `05 Irregular` | `Inf_Irreg_##.csv` | `Inf_Irreg_01.csv` |
| `06 Reflexive` | `Inf_Refl_##.csv` | `Inf_Refl_01.csv` |

### 01 Present Tense

| Folder | Use This Pattern | Example |
|---|---|---|
| `01 Conjugations` regular `-AR` | `Pres_Conj_Reg_AR_##.csv` | `Pres_Conj_Reg_AR_01.csv` |
| `01 Conjugations` regular `-ER` | `Pres_Conj_Reg_ER_##.csv` | `Pres_Conj_Reg_ER_01.csv` |
| `01 Conjugations` regular `-IR` | `Pres_Conj_Reg_IR_##.csv` | `Pres_Conj_Reg_IR_01.csv` |
| `01 Conjugations` irregular stem change | `Pres_Conj_Irreg_StemChange_##.csv` | `Pres_Conj_Irreg_StemChange_01.csv` |
| `02 Sentences` regular `-AR` | `Pres_Sent_Reg_AR_##.csv` | `Pres_Sent_Reg_AR_01.csv` |
| `02 Sentences` regular `-ER` | `Pres_Sent_Reg_ER_##.csv` | `Pres_Sent_Reg_ER_01.csv` |
| `02 Sentences` regular `-IR` | `Pres_Sent_Reg_IR_##.csv` | `Pres_Sent_Reg_IR_01.csv` |
| `02 Sentences` regular mixed | `Pres_Sent_Reg_Mix_##.csv` | `Pres_Sent_Reg_Mix_01.csv` |
| `02 Sentences` general mixed | `Pres_Sent_Mix_##.csv` | `Pres_Sent_Mix_01.csv` |
| `02 Sentences` irregular | `Pres_Sent_Irreg_##.csv` | `Pres_Sent_Irreg_01.csv` |
| `02 Sentences` irregular stem change | `Pres_Sent_Irreg_StemChange_##.csv` | `Pres_Sent_Irreg_StemChange_01.csv` |
| `02 Sentences` reflexive | `Pres_Sent_Refl_##.csv` | `Pres_Sent_Refl_01.csv` |
| `02 Sentences` topic deck | `Pres_Sent_[Topic]_##.csv` | `Pres_Sent_Tengo_Estoy_01.csv` |
| `02 Sentences` forced EN to ES | `Pres_Sent_[Topic]_##_EN_ES.csv` | `Pres_Sent_Ser_Estar_01_EN_ES.csv` |

<br><br><br><br><br><br><br><br>

### 03 Stories

| Story Folder | Use This Pattern | Example |
|---|---|---|
| `01 Regular -AR` | `Pres_Story_Reg_AR_##.csv` | `Pres_Story_Reg_AR_01.csv` |
| `02 Regular -ER` | `Pres_Story_Reg_ER_##.csv` | `Pres_Story_Reg_ER_01.csv` |
| `03 Regular -IR` | `Pres_Story_Reg_IR_##.csv` | `Pres_Story_Reg_IR_01.csv` |
| `04 Regular (AR, ER, IR)` | `Pres_Story_Reg_Mix_##a.csv` | `Pres_Story_Reg_Mix_01a.csv` |

For the mixed story set:

- use the same story number with letter variants
- examples:
  - `Pres_Story_Reg_Mix_01a.csv`
  - `Pres_Story_Reg_Mix_01b.csv`
  - `Pres_Story_Reg_Mix_01c.csv`

### 04 Dialogs

| Folder | Use This Pattern | Example |
|---|---|---|
| `04 Dialogs` | `Pres_Dialog_##.csv` or `Pres_Dialog_[Topic]_##.csv` | `Pres_Dialog_01.csv` |

### 05 Situations

| Folder | Use This Pattern | Example |
|---|---|---|
| `05 Situations` | `Pres_Situ_##.csv` or `Pres_Situ_[Topic]_##.csv` | `Pres_Situ_01.csv` |

### 06 Exercises

| Folder | Use This Pattern | Example |
|---|---|---|
| `06 Exercises` | `Pres_Ex_##.csv` or `Pres_Ex_[Topic]_##.csv` | `Pres_Ex_01.csv` |

### 07 Review

| Folder | Use This Pattern | Example |
|---|---|---|
| `07 Review` | `Pres_Review_##.csv` or `Pres_Review_[Topic]_##.csv` | `Pres_Review_01.csv` |

### 08 Quiz

| Folder | Use This Pattern | Example |
|---|---|---|
| `08 Quiz` | `Pres_Quiz_##.csv` or `Pres_Quiz_[Topic]_##.csv` | `Pres_Quiz_01.csv` |

<br><br><br><br><br><br><br><br><br><br><br><br><br><br><br>

## Numbering Notes

- Use two digits for the main deck number: `01`, `02`, `03`
- Use `a`, `b`, `c` only when a story set has matched variants
- Keep numbering consistent within each folder

## Quick Do / Do Not

### Do

- `Inf_Reg_AR_01.csv`
- `Pres_Conj_Reg_ER_02.csv`
- `Pres_Sent_Irreg_01.csv`
- `Pres_Story_Reg_Mix_03b.csv`
- `Pres_Sent_Ser_Estar_01_EN_ES.csv`

### Do Not

- `PoS_verbs_reg_ar_master_01.csv`
- `Prs_story_1.csv`
- `Story_01.csv`
- `Reg_AR_01.csv`

## One-Line Reminder

Folder first. Short filename second. Keep it readable. Keep it unique.