## Flashcard Deck Maintenance Policy

Use a permanent `id` column as column 1 in every deck.

### General rule
- Every card gets one `id`.
- That `id` is the card’s identity forever.
- Do not renumber old cards.

### Adding a card
- Add a new row.
- Give it a new `id` equal to the next unused number.
- Example: if the highest existing `id` is `83`, the new card gets `84`.

### Editing a card
- If you are only fixing or improving the existing card, keep the same `id`.
- Examples:
  - spelling correction
  - punctuation change
  - clearer wording
  - better translation of the same card

### Deleting a card
- Delete the row.
- Do not reuse its `id`.
- Do not renumber the cards below it.
- Gaps are fine.

<br><br><br><br>

### Replacing a card
- If the old row is being turned into a genuinely different card, do not keep the old `id`.
- Delete the old row or retire it.
- Add the replacement as a new row with a new `id`.

### Reordering cards
- You may reorder rows in the CSV.
- The saved progress will still work, because tracking is based on `id`, not row position.

### What not to do
- Do not identify cards by line number.
- Do not renumber all cards after deleting one.
- Do not reuse an old deleted `id` for a different card.

### Simple rule of thumb
- Same card, same `id`.
- New card, new `id`.

### Example

```csv
id,word,answer
1,house,casa
2,dog,perro
3,red,rojo
```

If you:
- change `dog` to `the dog`: keep `id=2`
- add `blue,azul`: use `id=4`
- delete `red,rojo`: remove `id=3`
- reorder the rows: keep the same IDs

<br><br>

Result:

```csv
id,word,answer
2,the dog,perro
1,house,casa
4,blue,azul
```

That is still valid.

## Best practical policy
- Column 1 is `id`
- IDs are integers
- IDs are permanent
- Gaps are allowed
- Never renumber
