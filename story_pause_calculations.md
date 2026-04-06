# Story Pause Calculations

## Goal

The current story pause model now uses two user controls:

- reading speed `1-5`
- pause amount `1-5`

And one internal timing model that tries to do two things at once:

- keep short simple sentences from feeling too slow
- give word-heavy sentences noticeably more time, especially for beginners

## Reading Speed

Reading speed is mapped to letters per second:

$$
c \in \{17, 15, 13, 11, 9\}
$$

where:

- `1` = fastest
- `5` = slowest

## Core Processing Model

Let:

- $L$ = number of letters only
- $W$ = number of words

Processing time is estimated by:

$$
t_{\mathrm{process}} = \frac{L}{c} + \alpha W + \delta \max(W - W_0, 0)^\gamma + p
$$

with the current constants:

$$
\alpha = 0.16, \quad \delta = 0.12, \quad W_0 = 6, \quad \gamma = 1.5, \quad p = 0.8
$$

Interpretation:

- $\frac{L}{c}$ handles raw reading length
- $\alpha W$ is the normal per-word processing cost
- $\delta \max(W-W_0,0)^\gamma$ is an extra overload bonus that only activates once the sentence gets word-heavy
- $p$ is a fixed thinking / translation buffer

## Why The Extra Word Bonus Helps

A constant word weight alone is not enough:

- if it is large enough for `12-15` word sentences, it makes `4-6` word sentences too long
- if it is small enough for short sentences, it underestimates longer sentences made of many short words

The thresholded bonus solves that problem because it stays small for short sentences and grows only after the word count passes `6`.

For example, the extra bonus term is:

- `0.00` at `6` words or fewer
- `0.12` at `7` words
- `0.34` at `8` words
- `0.62` at `9` words
- `1.34` at `11` words

That is exactly the intended behavior: mild effect on short sentences, stronger effect on crowded ones.

## Pause Ladder

The pause ladder still works the same way once $t_{\mathrm{process}}$ is known.

Longest pause:

$$
t_5 = \max\left(0.5, 2t_{\mathrm{process}}\right)
$$

Long pause:

$$
t_4 = \max\left(0.5, 0.5 + \sqrt{0.5}(t_5 - 0.5)\right)
$$

Define:

$$
g = t_4 - 0.5
$$

Then:

$$
t_3 = 0.5 + g\left(\frac{2}{3}\right)^2
$$

$$
t_2 = \frac{t_1 + t_3}{2}
$$

$$
t_1 = 0.5
$$

So the user-facing meaning remains:

- pause `5` = longest
- pause `4` = long
- pause `3` = medium
- pause `2` = short
- pause `1` = shortest

## Bottom Line

The model now uses:

- letters for base reading duration
- words for normal linguistic load
- an extra nonlinear bonus for sentences with many words

That makes it better suited for beginners who need disproportionately more time once a sentence becomes crowded with words, even when the words themselves are short.
