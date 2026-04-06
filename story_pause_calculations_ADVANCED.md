# Story Pause Calculations Advanced

## Goal

This version recalibrates the pause ladder to match the intended learner experience:

- pause `5` = enough time for about two slow read-throughs plus thinking time
- pause `4` = enough time for about one slow read-through
- pause `3` = enough time for about one fast read-through
- pause `2` = no read-through, but enough time to comprehend
- pause `1` = almost instant comprehension, no time to repeat

The ladder still uses two anchors:

- pause `5` is tied to the full processing estimate
- pause `4` is derived from that top anchor with the same square-root compression as before

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
- $\alpha = 0.04$
- $\delta = 0.22$
- $W_0 = 6$
- $\gamma = 1.5$
- $p = 0.25$

Processing estimate:

$$
t_{\text{process}} = \frac{L}{c} + \alpha W + \delta \max(W-W_0, 0)^\gamma + p
$$

This combines:

- raw sentence length through $L$
- extra beginner processing load through $W$
- extra overload time only after the sentence becomes word-heavy
- a fixed grammar and translation buffer through $p$

With the current constants, the extra overload term is:

- `0.00` at `6` words or fewer
- `0.22` at `7` words
- `0.62` at `8` words
- `1.14` at `9` words
- `2.46` at `11` words

That is why short sentences do not get over-penalized while longer ones still get noticeably more time.

## Pause Anchors

### Level 5 Anchor

Set the longest pause from the full processing estimate:

$$
t_5 = 2\left(\frac{L}{9} + 0.04W + 0.22\max(W-6, 0)^{1.5} + 0.25\right)
$$

Interpretation:

- reading speed anchor uses $c = 9$
- the factor `2` means about two slow read-throughs plus processing time

### Level 4 Anchor

Set pause `4` from the same compressed top-anchor structure:

$$
t_4 = 0.5 + \sqrt{0.5}\left(2\left(\frac{L}{13} + 0.04W + 0.22\max(W-6, 0)^{1.5} + 0.25\right) - 0.5\right)
$$

Interpretation:

- this keeps level `4` clearly below level `5` while staying much longer than the lower settings
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

- level `5` is the full maximum pause derived from the sentence model
- level `4` is a compressed upper-mid pause derived from that maximum
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

1. Mi casa pequeña tiene una puerta azul. -> `0.50 s | 1.74 s | 2.98 s | 6.08 s | 8.39 s`
2. Hoy compro pan fresco y queso en casa. -> `0.50 s | 1.84 s | 3.19 s | 6.55 s | 9.05 s`
3. La niña inteligente escribe cartas largas, pero claras. -> `0.50 s | 2.40 s | 4.30 s | 9.06 s | 12.61 s`
4. Mi hermano alto cocina sopa caliente cada domingo. -> `0.50 s | 2.26 s | 4.03 s | 8.43 s | 11.72 s`
5. Nosotros hablamos despacio, y la profesora sonríe mucho. -> `0.50 s | 2.44 s | 4.37 s | 9.22 s | 12.83 s`
6. El gato gris duerme sobre libros viejos y limpios. -> `0.50 s | 2.40 s | 4.31 s | 9.07 s | 12.62 s`
7. Yo miro la ventana abierta mientras tomo té tranquilo. -> `0.50 s | 2.54 s | 4.59 s | 9.70 s | 13.51 s`
8. Tu amigo amable vende flores rojas en el mercado. -> `0.50 s | 2.37 s | 4.24 s | 8.91 s | 12.40 s`
9. Ellos estudian gramática básica, pronunciación y verbos aquí. -> `0.50 s | 2.61 s | 4.72 s | 10.00 s | 13.94 s`
10. La ciudad tranquila parece pequeña, aunque tiene restaurantes excelentes. -> `0.50 s | 3.17 s | 5.84 s | 12.53 s | 17.51 s`

## Summary Of The Final Advanced Model

Internal constants:

- $\alpha = 0.04$
- $\delta = 0.22$
- $W_0 = 6$
- $\gamma = 1.5$
- $p = 0.25$
- $\beta = 2$

Anchors:

- pause `5` comes directly from the full sentence-processing estimate
- pause `4` is the compressed upper-mid pause derived from that estimate
- pause `1` is always `0.5` seconds

Derived levels:

- pause `3` is computed by exponential drop from level `4`
- pause `2` is set halfway between pause `1` and pause `3`

## What To Tune Next If Needed

If you test these aloud and they still need adjustment, change only one thing at a time:

- change $\beta$ if level `3` is too short or too long
- move $t_2$ closer to $t_1$ or $t_3$ if level `2` still needs adjustment
- change $\alpha$ if the normal per-word cost is too high or too low across all sentence lengths
- change $\delta$ if crowded sentences need more or less extra help
- change $W_0$ if the overload bonus should start earlier or later
- change $\gamma$ if the high-word-count bonus grows too slowly or too aggressively
- change $p$ if every sentence needs more or less fixed thinking time
- change the factor `2` in $t_5$ only if the maximum pause itself stops feeling right

The current design is a pragmatic calibration model, not a pure theoretical one. That is appropriate here, because the target is user feel, not mathematical elegance.