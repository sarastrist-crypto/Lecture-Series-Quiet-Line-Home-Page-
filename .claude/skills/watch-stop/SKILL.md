---
name: watch-stop
description: Caps any self-scheduled watch, poll, or check-in loop at 3 hours and replaces it with a written stop report — what was being watched, why it stopped, and the one decision or action it is waiting on. Use whenever a PR watch, CI poll, deploy watch, send_later/CronCreate check-in, or /loop has been re-arming without a state change, whenever about to schedule another check-in on something that has not moved, and before starting any watch whose only unblocker is a human decision. Carries the 3-hour rule, the stop-report format, the trigger cleanup, and how to restart.
---

# /watch-stop — a watch that isn't moving becomes a report

**Standing operator rule (Tristian, July 28, 2026), applies in EVERY repo and
EVERY session without being re-asked.**

An hourly check-in on something that only a person can unblock is wasted motion.
It burns tokens, it produces a string of identical "no change" lines, and it
still doesn't get the decision made — because the operator isn't sitting there
waiting to make it in the moment. **Three hours is the cap.** At three hours,
the watch stops and turns into a written handoff he can act on when he's next at
a keyboard.

The failure this exists to prevent: July 28, 2026, two A2P PRs were watched with
six consecutive hourly check-ins. Every one returned the same clean, unchanged
state. Nothing was ever going to change, because the only thing standing there
was Tristian clicking merge. That should have been one stop report at hour three,
not six wake-ups.

## The rule

1. **Three hours, hard cap.** Count from the first check-in on that subject, not
   from the last one. Six 60-minute re-arms is a three-hour watch, no matter how
   the timers were scheduled.
2. **No state change means stop sooner.** If two consecutive checks return the
   same state AND the only thing that would change it is a human decision, stop
   at that point. Don't run out the clock to look thorough.
3. **Decision-blocked work never starts a loop at all.** Before scheduling the
   first check-in, ask: *is there any event that could move this without a
   person acting?* If the answer is no — a PR waiting on a merge click, a form
   waiting on an EIN, an approval waiting on a reply — skip the watch entirely
   and deliver the stop report immediately.
4. **Delete the pending trigger.** Stopping means the next wake-up does not
   fire. List triggers, find the one still `enabled`, delete it. A stop report
   with a live timer behind it is not a stop.
5. **One report, then silence.** After the stop report, say nothing further
   about it until he responds or asks. No "just checking again."

## The stop report

Lead with the decision, not the history. Five parts, short:

```
**Stopped watching <what> after <N> hours.**

**Why it stopped:** <one sentence — nothing changed, and what would have
                     to happen for it to change>

**Waiting on you:** <the single decision or action, named plainly. If it's a
                     click, say which button and where. If it's a fact only he
                     has, name the fact.>

**Next step after that:** <what happens once he does it, and who does it —
                           him, me, or a teammate>

**Current state:** <the facts as of the last check: links, status, anything
                    that would have to be re-verified before acting>

**To restart:** <the one sentence that would put the watch back on>
```

Live links per the Delivery rule, one per line. If several things were being
watched, one block each, most-blocking first.

## What still gets watched

The cap is on *waiting for a person*. Keep watching, past three hours if the job
genuinely runs that long, when a machine is going to change the state on its own
and nothing else will tell you:

- a CI run, build, or deploy that's actually in progress
- a long migration, import, or backfill
- an external approval with a real SLA (carrier vetting, a domain transfer)

Even then: **report at the three-hour mark anyway**, say it's still running and
why the watch is being kept, and pace the checks to how fast the thing actually
changes. A 20-minute deploy does not need a 60-second poll.

## Restarting

He replies, the decision lands, or the blocker clears → resume normally. A new
watch starts a new three-hour clock. Don't carry the old one forward, and don't
re-open a watch on the same stalled subject without a new reason.

## Mechanics

- **List and clean the timers.** `list_triggers` on the claude-code-remote MCP
  server, then `delete_trigger` on any row where `enabled` is true and the
  subject is the one being dropped. Rows with `ended_reason: run_once_fired`
  already fired and need nothing.
- **`/loop` in dynamic mode:** call `ScheduleWakeup` with `stop: true`.
- **Cron-based watches:** `CronDelete`, or `update_trigger` with
  `enabled: false` if it should come back later.
- **PR subscriptions:** `unsubscribe_pr_activity` only if he asks to stop
  following the PR entirely. Webhook events are cheap and land only when
  something real happens — the thing being stopped is the *self-scheduled
  polling*, not the event feed. Stopping the poll doesn't abandon the PR: a CI
  failure or review comment still wakes the session and still gets handled.

## The line to hold

Stopping a watch is not giving up on the work. It's refusing to pretend that
checking again is progress. The report is the deliverable; the timer never was.
