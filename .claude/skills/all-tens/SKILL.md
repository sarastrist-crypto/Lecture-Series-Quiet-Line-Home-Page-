---
name: all-tens
description: >-
  Grade your own output against five criteria you pick before you look at it,
  critique every score under 10 with the specific change that closes the gap,
  redo the work, and repeat until it is all 10s or the round cap stops you. Use
  whenever the operator says "/all-tens", "grade your output", "score this out
  of 10", "rate this", "critique your own work", "why isn't this a 10", "make it
  a 10/10", "run it again until it's perfect", "self-critique this", "poke holes
  in this", "be your own harshest critic", "is this good enough", "grade it
  on the most relevant criteria", or "don't show me the first draft". Works on
  anything: an email, a page, a deck, copy, code, a plan, a proposal. Carries
  the criteria-selection method (the part that decides whether the loop is worth
  anything), the anti-inflation rules that stop a self-grade from being a
  formality, and the round cap so it never spins.
---

# all-tens: grade, critique, redo, until it earns the score

**Why this exists.** A first pass is a first pass. The cheap way to make it
better is to force the work to survive a rubric it did not get to write after
the fact. The loop is simple enough to say in one sentence: *grade the output on
the five most relevant criteria, critique why each one did not hit 10 out of 10,
then do the work again until they are all 10s.*

The loop is easy. Making it honest is the hard part, and that is most of what is
written down here. A self-grade run carelessly awards itself 9s on round one and
10s on round two, changes almost nothing in between, and hands over the same
draft wearing a scorecard. Everything below exists to stop that.

## How it gets invoked

- **`/all-tens`** on its own: run the loop on the last thing produced.
- **`/all-tens <task>`**: do the task, then run the loop on the result before
  showing anything.
- **Tacked onto any request** ("write the client update, all tens"): same as
  above. The operator sees the graded version, never the first draft.

## The loop

**0. Do the work properly first.** A real, complete draft at normal quality. The
loop sharpens a finished thing; it cannot rescue a stub, and starting from a
deliberate throwaway just burns rounds climbing back to where step 0 should have
been.

**1. Name the five criteria before re-reading the draft.** Derived from the job
the work has to do, not from the draft you happen to have. Writing the criteria
after re-reading is how you end up with five criteria the draft already passes.
Each one gets a sentence for what a 10 looks like. This step decides whether the
whole run is worth anything; see the section below.

**2. Grade with the evidence first, the number second.** For each criterion:
quote the exact line, element, or behavior that costs the point, then assign the
score. In that order, always. A number written first drags the evidence toward
it; evidence written first forces the number to follow.

**3. Critique: name what would close each gap.** For every criterion under 10,
state the specific change. Not "tighten the opening", but "the opening asks for
a call before it says what the thing costs; lead with the price". If you cannot
name the change, the score was wrong: either it was already a 10, or you do not
actually understand the criterion.

**4. Redo the work, do not patch it.** Rewrite or rebuild carrying every fix at
once. Patching the flagged lines produces an artifact that scores well
criterion by criterion and reads stitched together as a whole, which is the
exact failure the scorecard is blind to.

**5. Re-grade against the same five criteria.** The goalposts do not move. New
criteria discovered mid-loop get noted for the operator, not swapped in to
rescue a score.

Repeat 2 through 5 until all five are 10s, or the cap stops you.

**At least one revision round always happens.** Round one's grade is never
final, and an opening scorecard of all 10s is not a pass, it is proof the
criteria were too soft. Send it back to step 1 and sharpen them. The loop is
only finished after a draft has been redone and re-graded at least once.

## The round cap

**Three revision rounds**, counting from the first redo, not from the opening
grade. If it is not all 10s after three, stop and hand it over with the
remaining gap named. In practice a stuck criterion means one of three things,
and each has a different answer:

- **It needs a fact only the operator has** (a real number, a name, whether the
  meeting happened). Ask for that one thing; do not invent it to buy a 10.
- **Two criteria genuinely conflict** (short versus complete, warm versus
  direct). Say which one you traded away and why, and let the operator overrule.
- **The format is the ceiling.** An email cannot do what a page does. Say so and
  propose the format that can.

**A round that changes nothing ends the loop early.** Report the plateau
honestly. A round of cosmetic edits so the scorecard can climb is worse than
stopping, because it hides the plateau behind a number.

## Picking criteria that actually bite

This is the whole game. Generic criteria make the loop a formality.

**Useless:** clarity, structure, engagement, tone, impact, professionalism.
Nothing can fail them, so everything scores 9 and a light polish pass buys the
10. Five vague criteria are worth less than one sharp one.

**A criterion bites when:**

- **It names one reader and what they have to do.** "A pool owner who has never
  met us can say what this costs and what happens next, in under ten seconds"
  beats "clarity" every time.
- **It can fail.** If you cannot picture the version of this work that scores a
  4 on it, the criterion is not real. Rewrite it until you can.
- **It is about this piece, not about writing.** "Every claim about the referral
  program survives a skeptic asking if this is an MLM" is a criterion. "Accurate"
  is not.
- **It is checkable where checking is possible.** Prefer the criterion you can
  test over the one you can only feel.

**Sharpening a weak one.** Almost every first-pass criterion is a noun that
needs a reader and a failure attached to it:

| Weak (unfalsifiable) | Sharp (can score a 4) |
|---|---|
| Clear | A pool owner who has never met us can say what this costs and what happens next inside ten seconds |
| Persuasive | The single strongest reason to say no is answered on screen, before the ask |
| On brand | Opened cold on a phone, the first paint is the real mark and the real type, not a fallback font wall |
| Well organized | Someone who reads only the bolded lines still gets the whole argument |
| Accurate | Every claim about a person or a past conversation traces to a line in `memory/log/` |

**Where to find the five:** what does this have to accomplish, for exactly whom,
and what is the most likely reason they bounce? The answers to those three, plus
the one thing that would embarrass us if it were wrong, plus the thing the
operator will ask about first. That is five.

## The anti-inflation rules

Without these the loop is theater.

1. **A 10 has to be defensible out loud.** Name the strongest objection a
   hostile reader would raise against that criterion, and show where the work
   already answers it. Cannot do that, it is not a 10.
2. **No score rises without a named change.** "It reads better now" is not a
   change. Point at what moved.
3. **Never self-grade something you can test.** Run it, open it, screenshot it,
   click the link, count the words, load the page at 390px wide. Awarding a 10
   on a checkable property is the single most common lie this loop tells, and
   the CLAUDE.md design rule says it plainly: a page can pass every automated
   check with its headline invisible.
4. **Grade the whole once at the end.** Five 10s and a piece that reads like it
   was assembled by committee is a failure the scorecard cannot see. Read it
   straight through as the reader would, last thing, before delivery.
5. **Round one does not get to be good.** If the first grade comes back all 9s,
   the criteria are too soft. Go back to step 1.

## House gates come first, and they are not scored

For anything CobbledWorks puts in front of a person, the studio standards are
**pass/fail gates checked before grading**, not criteria competing for one of
the five slots. A gate failure is not a 7, it is a blocker: fix it, then grade.

- Anti-slop (`/anti-slop-writing`), run before the operator sees any draft
- No em dashes, anywhere
- Voice: plain, warm, no pressure, no corporate-speak
- Polish standard: real brand tokens, real type scale, depth, phone-first
- No claimed conversation that did not happen
- Delivery: a live, clickable link, never a repo or a blob

Spending a criterion slot on "follows our style guide" wastes it. Those are
already required. The five are for what is specific to this piece.

## What the operator sees

Lead with the finished work. Then a compact scorecard, five lines, criterion and
final score, and one line naming the biggest thing the loop actually fixed. Not
the transcript of every round.

If a criterion ended under 10, say so in that line with the reason and the one
thing that would close it. A scorecard of five 10s with no story is less
believable than a 9 with a named trade-off.

Say **"show the grading"** to get round one's full critique printed.

## When this is the wrong instrument

- **Trivial or factual asks.** A one-line answer does not need three rounds.
- **Audience reaction.** Whether a real person would reply is not something to
  self-grade. That is `/internal-focus-group`.
- **Bugs and security.** A self-assessment is not a QA verdict. Dispatch
  **Watch**.
- **Visual judgment.** Screenshot it at phone width and look at it
  (`/screenshot`). Do not score a design you have not seen rendered.

Self-grading raises the floor on work you can reason about. It is not evidence,
and it never substitutes for the check that would settle the question.

> This skill is mirrored into every repo so `/all-tens` loads anywhere. The
> companion skills it routes to (`/anti-slop-writing`, `/internal-focus-group`,
> `/screenshot`) and the Studio teams live in `cobbled-works`. In a repo without
> them, do the thing they describe by hand rather than skipping the step.

## Gotchas

- **Criteria written after re-reading the draft are worthless.** The single most
  common way this run goes soft. Write them from the job, then look.
- **Score first, evidence second inverts the whole thing.** Once a 9 is on the
  page the critique quietly becomes a justification. Evidence first, always.
- **Patching instead of redoing** is the second most common failure. The
  scorecard climbs, the piece gets choppier, and nothing in the rubric notices.
- **Do not let round two invent a sixth criterion** to explain a score that did
  not move. Note it for the operator and keep grading the original five.
- **All 10s on round two is a smell, not a win.** Real work usually plateaus at
  one stubborn criterion. A clean sweep after one revision usually means the
  criteria never bit.
- **The loop cannot verify facts.** It improves how well the work does its job,
  not whether the claims in it are true. Check claims against the record
  separately, and if a fact is missing, ask rather than fill the hole.
