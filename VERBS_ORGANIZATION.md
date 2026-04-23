# Verbs Organization

This file records the current verbs folder structure and the naming system now in use.

## Folder Structure

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

## Naming Standard

Verb files now use a short readable code system.

This follows the same project-wide pattern used in the other parts of speech:

- `Adj_01_p.csv`
- `Adj_01_Stories_c1/Adj_01_Story_01a.csv`
- `Adv_01.csv`
- `Conjunct_01.csv`
- `Noun_01.csv`
- `Prep_01.csv`
- `Pron_01.csv`

The parallel idea is:

- singular `Story` for one file
- plural `Stories` for a folder that contains multiple story files

### Stage Or Tense

- `Inf`
- `Pres`
- `Past`
- `Fut`
- `MixedTense`

### Deck Type

- `Conj`
- `Sent`
- `Story`
- `Dialog`
- `Situ`
- `Ex`
- `Review`
- `Quiz`

### Verb Group

- `Reg`
- `Irreg`
- `Refl`
- `StemChange`
- `AR`
- `ER`
- `IR`
- `Mix`

## Current File Names

### 00 Infinitives

#### 01 Regular -AR

- `Inf_Reg_AR_01.csv`

#### 02 Regular -ER

- `Inf_Reg_ER_01.csv`

#### 03 Regular -IR

- `Inf_Reg_IR_01.csv`

#### 04 Regular (AR, ER, IR)

- `Inf_Reg_Mix_01.csv`
- `Inf_Reg_Mix_02.csv`
- `Inf_Reg_Mix_03.csv`
- `Inf_Reg_Mix_04.csv`
- `Inf_Reg_Mix_05.csv`
- `Inf_Reg_Mix_06.csv`
- `Inf_Reg_Mix_07.csv`
- `Inf_Reg_Mix_08.csv`
- `Inf_Reg_Mix_09.csv`
- `Inf_Reg_Mix_10.csv`

#### 06 Reflexive

- `Inf_Refl_01.csv`

### 01 Present Tense

#### 01 Conjugations

- `Pres_Conj_Reg_AR_01.csv`
- `Pres_Conj_Reg_AR_02.csv`
- `Pres_Conj_Reg_ER_01.csv`
- `Pres_Conj_Reg_ER_02.csv`
- `Pres_Conj_Reg_IR_01.csv`
- `Pres_Conj_Irreg_StemChange_01.csv`

#### 02 Sentences

- `Pres_Sent_Reg_AR_01.csv`
- `Pres_Sent_Reg_ER_01.csv`
- `Pres_Sent_Reg_IR_01.csv`
- `Pres_Sent_Reg_Mix_01.csv`
- `Pres_Sent_Mix_01.csv`
- `Pres_Sent_Irreg_01.csv`
- `Pres_Sent_Irreg_StemChange_01.csv`
- `Pres_Sent_Refl_01.csv`
- `Pres_Sent_Ser_Estar_01_EN_ES.csv`
- `Pres_Sent_Tengo_Estoy_01.csv`
- `Pres_Sent_Want_Like_Have_01.csv`

#### 03 Stories

##### 01 Regular -AR

- `Pres_Story_Reg_AR_01.csv` through `Pres_Story_Reg_AR_20.csv`

##### 02 Regular -ER

- `Pres_Story_Reg_ER_01.csv` through `Pres_Story_Reg_ER_12.csv`

##### 03 Regular -IR

- `Pres_Story_Reg_IR_01.csv` through `Pres_Story_Reg_IR_08.csv`

##### 04 Regular (AR, ER, IR)

- `Pres_Story_Reg_Mix_01a.csv` through `Pres_Story_Reg_Mix_09c.csv`

#### 04 Dialogs

- empty for now

#### 05 Situations

- empty for now

#### 06 Exercises

- empty for now

#### 07 Review

- empty for now

#### 08 Quiz

- empty for now

## Notes

1. Folder placement now drives story, dialog, sentence, and conjugation behavior in the app.
2. Filenames still must stay unique across the whole `csv` tree.
3. `EN_ES` remains a legacy exception for forced English-to-Spanish decks.
4. `_p` and `_cN` are still available when grouped picker ordering is needed, but they are not part of the default verbs naming pattern.
5. The only non-verb category currently long enough to need grouping is adjectives, which already uses grouped child folders such as `Adj_01_Stories_c1`. The other non-verb categories are still short enough that extra nesting would add clutter instead of removing it.