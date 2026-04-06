# Story Pause Calculations Advanced

## Goal

This version fixes the pause ladder to match the intended learner experience:

- pause `5` = enough time for about two slow read-throughs plus thinking time
- pause `4` = enough time for about one slow read-through
- pause `3` = enough time for about one fast read-through
- pause `2` = no read-through, but enough time to comprehend
- pause `1` = almost instant comprehension, no time to repeat

The two anchor requirements are:

- keep pause `5` exactly as it already is
- make pause `4` exactly equal to the previous values that were calculated for the old pause `3`

Then levels `3`, `2`, and `1` decrease toward the minimum pause of `0.5` seconds, with level `2` nudged slightly longer so it sits about halfway between levels `1` and `3`.

## User Controls

The user only selects:

- reading speed `1-5`
- pause length `1-5`

The internal coefficients are not user inputs.

## Core Sentence Model

Let:

- $W$ = number of words
- $L$ = number of letters only
- $\alpha = 0.22$
- $p = 0.8$

Processing estimate:

$$
t_{\text{process}} = \frac{L}{c} + \alpha W + p
$$

This combines:

- raw sentence length through $L$
- extra beginner processing load through $W$
- a fixed grammar and translation buffer through $p$

## Pause Anchors

### Level 5 Anchor

Keep the longest pause exactly the same as before:

$$
t_5 = 2\left(\frac{L}{9} + 0.22W + 0.8\right)
$$

Interpretation:

- reading speed anchor uses $c = 9$
- the factor `2` means about two slow read-throughs plus processing time

### Level 4 Anchor

Set pause `4` equal to the previous values that were already calculated for the old medium setting:

$$
t_4 = 0.5 + \sqrt{0.5}\left(2\left(\frac{L}{13} + 0.22W + 0.8\right) - 0.5\right)
$$

Interpretation:

- this preserves the earlier level that felt like a good "one slow read" pause
- the anchor uses $c = 13$, which corresponds to reading speed `3`

## Exponential Drop For Levels 3, 2, 1

Now define the gap above the minimum pause:

$$
g = t_4 - 0.5
$$

Use an exponential-style power curve from level `4` down to level `1` for level `3`:

$$
t_3 = 0.5 + g\left(\frac{2}{3}\right)^\beta
$$

with:

$$
\beta = 2
$$

Set the minimum directly:

$$
t_1 = 0.5
$$

Then nudge level `2` to sit halfway between levels `1` and `3`:

$$
t_2 = \frac{t_1 + t_3}{2}
$$

So the final ladder is:

- $t_1 = 0.5$
- $t_2 = \frac{t_1 + t_3}{2}$
- $t_3 = 0.5 + g\left(\frac{2}{3}\right)^2$
- $t_4 = 0.5 + g$

And then:

$$
t_5 \text{ remains the anchored maximum pause}
$$

This is intentionally not a single smooth curve from `1` to `5`. It is an anchored design with a manual nudge at level `2`:

- level `5` preserves the maximum pause you already like
- level `4` preserves the previous usable mid-level values
- level `3` is derived from level `4` with an exponential drop
- level `2` is then placed halfway between levels `1` and `3`

That is the cleanest way to satisfy the requirements exactly.

## Why This Structure Makes Sense

This ladder now has a clearer behavioral meaning:

- `5` = two slow rereads plus thinking
- `4` = one slow reread
- `3` = one fast reread
- `2` = quick comprehension only
- `1` = minimum delay

The key point is that the middle of the scale is no longer linear. It falls faster as you move down from `4` toward `1`, but level `2` is intentionally kept a bit longer so it does not feel too abrupt.

## Counting Rules

For all examples below:

- $W$ counts words
- $L$ counts letters only
- spaces and punctuation are excluded from $L$

## Ten Example Sentences With All Five Pause Scores

Score order:

- `P1` = pause level `1`
- `P2` = pause level `2`
- `P3` = pause level `3`
- `P4` = pause level `4`
- `P5` = pause level `5`

1. Mi casa pequeña tiene una puerta azul. -> `0.50 s | 1.91 s | 3.31 s | 6.83 s | 11.57 s`
2. Hoy compro pan fresco y queso en casa. -> `0.50 s | 1.95 s | 3.40 s | 7.03 s | 11.79 s`
3. La niña inteligente escribe cartas largas, pero claras. -> `0.50 s | 2.34 s | 4.18 s | 8.77 s | 15.34 s`
4. Mi hermano alto cocina sopa caliente cada domingo. -> `0.50 s | 2.24 s | 3.98 s | 8.34 s | 14.45 s`
5. Nosotros hablamos despacio, y la profesora sonríe mucho. -> `0.50 s | 2.36 s | 4.22 s | 8.88 s | 15.56 s`
6. El gato gris duerme sobre libros viejos y limpios. -> `0.50 s | 2.29 s | 4.07 s | 8.54 s | 14.67 s`
7. Yo miro la ventana abierta mientras tomo té tranquilo. -> `0.50 s | 2.39 s | 4.27 s | 8.97 s | 15.56 s`
8. Tu amigo amable vende flores rojas en el mercado. -> `0.50 s | 2.26 s | 4.02 s | 8.43 s | 14.45 s`
9. Ellos estudian gramática básica, pronunciación y verbos aquí. -> `0.50 s | 2.49 s | 4.47 s | 9.42 s | 16.68 s`
10. La ciudad tranquila parece pequeña, aunque tiene restaurantes excelentes. -> `0.50 s | 2.82 s | 5.14 s | 10.93 s | 19.56 s`

## Summary Of The Final Advanced Model

Internal constants:

- $\alpha = 0.22$
- $p = 0.8$
- $\beta = 2$

Anchors:

- pause `5` stays exactly at the current maximum values
- pause `4` is exactly the previous usable middle-setting values
- pause `1` is always `0.5` seconds

Derived levels:

- pause `3` is computed by exponential drop from level `4`
- pause `2` is set halfway between pause `1` and pause `3`

## What To Tune Next If Needed

If you test these aloud and they still need adjustment, change only one thing at a time:

- change $\beta$ if level `3` is too short or too long
- move $t_2$ closer to $t_1$ or $t_3$ if level `2` still needs adjustment
- change $\alpha$ if many short words still feel underweighted
- change $p$ if every sentence needs more or less fixed thinking time
- change the factor `2` in $t_5$ only if the maximum pause itself stops feeling right

The current design is a pragmatic calibration model, not a pure theoretical one. That is appropriate here, because the target is user feel, not mathematical elegance.