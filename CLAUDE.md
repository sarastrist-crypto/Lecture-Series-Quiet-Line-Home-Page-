# CLAUDE.md — Lecture-Series-Quiet-Line-Home-Page-

Guidance for Claude Code working in this repo.

## ⏱ Stop a watch at 3 hours — standing rule (July 28, 2026)

**Standing operator rule (Tristian), applies in EVERY repo and EVERY session
without being re-asked.** No self-scheduled watch, poll, or check-in loop runs
past **three hours**. Hourly wake-ups on something only a person can unblock are
wasted motion — the operator is not sitting there to make the call in the moment.

- **Three hours, counted from the first check-in** on that subject, not the last.
  Six 60-minute re-arms is a three-hour watch.
- **At the cap, stop and write the report:** what was being watched, why it
  stopped, the single decision or action waiting on him, what happens after, and
  the one line that restarts it.
- **Delete the pending trigger** when you stop. A stop report with a live timer
  behind it is not a stop.
- **Decision-blocked work never starts a loop at all.** If no event could move it
  without a person acting, skip the watch and deliver the report immediately.
- **Machines still get watched** — a running CI job, deploy, migration, or an
  external approval with a real SLA — but report at the three-hour mark anyway
  and pace the checks to how fast the thing actually changes.

Full procedure, report format, and the trigger cleanup:
[`/watch-stop`](.claude/skills/watch-stop/SKILL.md). Canonical statement: the
`cobbled-works` CLAUDE.md.
