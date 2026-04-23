# ⭐ **MASTER INSTRUCTION SHEET FOR GENERATING STORY SETS**  
*(For adjectives, adverbs, nouns, pronouns, or any other word type)*

## **1. Input Format**
You will provide a list of words (usually 100, but can be any number).  
Each word has:

- An **ID number**  
- An **English word**  
- A **Spanish translation**

Example format (CSV-like):

```
"id";"word";"answer"
"1";"blue";"azul"
"2";"green";"verde"
...
```

The list may contain **adjectives, adverbs, nouns, pronouns, verbs, etc.**  
The method below applies to **any part of speech**.

---

# **2. Story Grouping Rules**
You may specify **any grouping structure**, such as:

- 20 words per story  
- 10 words per story  
- 25 words per story  
- 1, 2, 3, or more stories per group  
- Any number of total stories  

The system must adapt to **whatever grouping you specify**.

### **Default pattern used so far (but fully customizable):**
- 100 words → 5 sets  
- Each set = 20 words  
- Each set = 2 stories  
- Total = 10 stories  

But this can change completely.  
The instructions must always override the default.

---

# **3. Word Usage Rules**
For **each story**:

### **3.1 Use each word exactly once**
- If the story uses 20 words, all 20 must appear.
- No word may repeat.
- No word may be omitted.

### **3.2 Do NOT use the words in numerical order**
- The order must be **mixed** to improve narrative quality.
- The story must feel natural, not mechanical.

### **3.3 Words must be used in their correct meaning**
- If the list contains adjectives → use them as adjectives.  
- If the list contains adverbs → use them as adverbs.  
- If the list contains nouns → use them as nouns.  
- If the list contains pronouns → use them as pronouns.  
- If the list contains verbs → conjugate them naturally in Spanish.  

---

# **4. Story Structure Requirements**
Every story must have:

### **4.1 Exactly 20 sentences**
- No more, no fewer.

### **4.2 Each sentence must have 6–8 words**
- English sentence: 6–8 words  
- Spanish sentence: 6–8 words  
- Both must be natural and not forced.

### **4.3 Real plot arc**
Every story must have:

- **Beginning** (setup)  
- **Middle** (conflict or development)  
- **End** (resolution or shift)

No “list-like” stories.  
No repetitive beats.  
No template reuse.

### **4.4 Natural Mexican Spanish**
- No unnecessary pronouns  
- No Spain-specific vocabulary  
- No awkward literal translations  

---

# **5. Tense Requirements**
Each story must follow:

### **5.1 75% present tense**
- 15 sentences in present tense

### **5.2 25% “going to” future**
- Exactly **5 sentences** using “going to”  
- Spanish uses **“voy a / vamos a / va a / van a / vas a”**  
- English uses **“I am going to / we are going to / etc.”**

### **5.3 Future sentences must be distributed**
- At least one in the beginning third  
- At least one in the middle third  
- At least one in the final third  
- Never clustered together

---

# **6. Output Format**
Each story must be printed in **CSV‑ready bilingual format**:

```
"Title: English Title";"Título en Español"
"English sentence 1";"Spanish sentence 1"
"English sentence 2";"Spanish sentence 2"
...
"English sentence 20";"Spanish sentence 20"
```

### **6.1 Titles**
- Must be original  
- Must reflect the plot  
- Must be bilingual  
- Must not reuse previous titles  

---

# **7. Narrative Quality Requirements**
Every story must be:

- **Cohesive**  
- **Non-repetitive**  
- **Distinct from all other stories**  
- **Emotionally or visually engaging**  
- **Logically consistent**  
- **Free of recycled structures**  

No story may resemble another in plot, tone, or structure.

---

# **8. Flexibility for Future Word Types**
This instruction sheet applies to:

- **Adjectives**  
- **Adverbs**  
- **Nouns**  
- **Pronouns**  
- **Verbs**  
- **Prepositions**  
- **Determiners**  
- **Conjunctions**  
- **Any other part of speech**

The system must adapt the grammar naturally.

Examples:

- If the word is a **noun**, it must appear as a noun.  
- If the word is a **verb**, it must be conjugated correctly.  
- If the word is a **pronoun**, it must be placed naturally.  
- If the word is an **adverb**, it must modify a verb or adjective.  

---

# **9. What You (the user) Can Customize**
You may change:

- Number of stories  
- Number of words per story  
- Number of stories per group  
- Tense distribution  
- Sentence length  
- Plot style  
- Spanish dialect  
- Whether words must appear literally or metaphorically  
- Whether words must appear in order or mixed  

The system must obey **your version**, not the default.

---

# **10. What You (the user) Should Paste in Future**
Whenever you want new stories, paste:

- This instruction sheet  
- The new word list  
- The grouping structure (if different)  
- Any special constraints  

And I will generate the stories exactly as specified.

---
