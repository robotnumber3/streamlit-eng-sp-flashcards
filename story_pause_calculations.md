# Story Pause Calculations

Both controls now move in the same direction:

- `1` = fastest / shortest time
- `5` = slowest / longest time

This is the clean, consistent redesign.

## Core Separation

Still keep the two independent concepts:

$$
\operatorname{reading\ speed}(c) \quad \text{and} \quad \text{pause scaling }(m)
$$

## 1. Reading Speed \(c)

User profile scale:

- `1` = very fast
- `2` = fast
- `3` = medium
- `4` = slow
- `5` = very slow

Mapped to letters per second:

$$
c \in \{17, 15, 13, 11, 9\}
$$

Interpretation:

- lower number -> higher speed -> shorter base time
- higher number -> slower reading -> longer base time

## 2. Pause Between Lines (m)

Story mode pause scale:

- `1` = minimal pause
- `2` = short pause
- `3` = medium pause
- `4` = long pause
- `5` = very long pause

Mapped to pause multipliers:

$$
m \in \{0.15, 0.35, 0.60, 1.00, 2.00\}
$$

Interpretation:

- `1` -> almost no extra time
- `5` -> about two full readbacks

## 3. Timing Model

Base reading time:

$$
t_{\text{base}} = \frac{L}{c}
$$

Pause time:

$$
t_{\text{pause}} = T\left(1 - e^{-m t_{\text{base}} / T}\right)
$$

with:

$$
T \approx 12 \text{ to } 20
$$

If you want units stated explicitly, use:

$$
T \approx 12 \text{ to } 20 \text{ seconds}
$$

## 4. Behavior

If the user picks:

- Speed = `1` (very fast)
- Pause = `1` (minimal)

Then the result is the fastest possible experience.

If the user picks:

- Speed = `5` (very slow)
- Pause = `5` (very long)

Then the result is maximum support: slow reading plus multiple repeats.

Mixed example:

- Speed = `2` (fast)
- Pause = `5` (very long)

That means a fast reader who still wants time to repeat carefully. This is an important language-learning case.

## 5. Why This Ordering Is Better

Now both controls obey the same rule:

- smaller number = faster / less time
- larger number = slower / more time

There is no cognitive mismatch. Users do not need to mentally invert one slider.

## 6. If You Use Only One 1-5 Scale

Define combined presets like this:

| Level | Meaning | $c$ (letters/sec) | $m$ |
| --- | --- | ---: | ---: |
| 1 | very fast | 17 | 0.15 |
| 2 | fast | 15 | 0.35 |
| 3 | medium | 13 | 0.60 |
| 4 | slow | 11 | 1.00 |
| 5 | very slow | 9 | 2.00 |

So:

- `1` = minimal wait + fast reading
- `5` = maximum wait + slow reading

This keeps everything consistent, but removes flexibility.

## 7. Final Recommendation

Best design:

- Reading speed: `1-5` (fast -> slow)
- Pause length: `1-5` (short -> long)

Both are aligned:

- `1` = shortest time everywhere

## Bottom Line

You now have:

- a calibrated human-speed model
- a nonlinear curve that prevents long waits
- a UI that is cognitively consistent

That combination is what makes a system like this feel right instead of mechanical.

If needed later, the exact $c$ and $m$ values can be tuned so that:

- 30-letter sentences do not feel rushed
- 200-letter sentences never exceed a specific maximum, for example 12 seconds
