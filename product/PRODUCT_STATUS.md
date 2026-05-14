# Product / Booking Engine Status

Last updated: 2026-05-13

## Coordination Status

- This is the Product / Booking Engine status file.
- Communication protocol is now documented in `DECISIONS.md`.
- Ops coordination files now exist:
  - `ops/HANDOFFS.md`
  - `ops/CEO_ACTION_QUEUE.md`
  - `ops/NEXT_ACTIONS.md`
- Active cross-thread handoffs: none.
- CEO action queue items from Product: none.
- Current user next actions are in `ops/NEXT_ACTIONS.md`.
- Latest discussion: GitHub is recommended only as a private repo after secrets and generated/local files are excluded.
- Local Git baseline commit exists: `Initial safe project baseline`.
- `.gitignore` excludes live config, logs, bundles, caches, and generated artifacts.
- Eileen can use either an existing GitHub account or a new GitHub account, as long as the repo is private and secrets remain untracked.
- GitHub remote is configured as `https://github.com/eileenlumena/yogabot.git`.
- GitHub push is complete; `main` and `origin/main` are synced at `8020788` (`Add direct GitHub token link`).
- GitHub workflow guidance added: commit/push manually at meaningful checkpoints after verified code/docs changes, not for every small conversation.

## Current State

- Booking outcomes have recently been strong.
- The Singapore server likely helps with path consistency, but backend queueing still varies day to day.
- The engine has useful timing logs for warmup RTT, booking RTT, focus/follower spacing, queue proxy, CloudFront POP, and response metadata.
- Telegram notifications are cleaner than the original format: class id and generic success text were removed from user-facing final summaries.
- The config supports `skip_booking_run_dates` for temporary schedule changes.
- 2026-05-14 run booked all 5 active targets for 2026-05-19 successfully.

## Immediate Run Context

Latest analyzed booking run: 2026-05-14 for 2026-05-19 classes.

Outcome:

- BOOKED Yoga 12:15 `Specialised: Wall Rope`, Dagge Ong, Yoga - Ngee Ann City.
- BOOKED Yoga 10:00 `Reformer Signature`, Kelvin Teo, Yoga - Ngee Ann City.
- BOOKED Yoga 13:30 `Specialised: Yogasthenics`, Wen Wen Chen, Yoga - Ngee Ann City.
- BOOKED Fitness 18:45 `RPM™`, Ayu Astutik, Fitness - Asia Square Tower 1.
- BOOKED Fitness 17:45 `BODYCOMBAT™`, House Chaalane, Fitness - Ngee Ann City.

Important metrics:

- Yoga sent focus at 08:59:59.800 and followers at about 08:59:59.920.
- Yoga focus send delta was 120.3ms against configured 120ms; residual jitter was +0.3ms.
- Yoga warmup RTT was elevated at 218.6ms.
- Yoga queue proxy was +2299.1ms focus / +2015.4ms follower.
- Fitness was handled after Yoga because multi-site runs are sequential to avoid session replacement; fitness booking requests sent at about 09:00:05.085 and both booked.

## Known Issues / Risks

- Server config can fall behind local config.
- Expired one-off targets clutter the config.
- Multi-site runs handle Yoga and Fitness one after another, so they are not the cleanest test of exact 9:00 same-site parallel timing.
- Pure may enforce an advance-booking limit by category/account; this can look like a bot failure if not controlled.
- Pure schedule changes can produce `NO_MATCH`; this is correct behavior when the target class is no longer posted at that time/location.
- `pure_yoga_config.json` contains secrets and must not be committed.

## Next Product Tasks

1. Upload and verify config before any important run.
2. After the next run, compare performance against previous days side by side.
3. Plan a multi-booking test on non-critical classes:
   - fewer than 5 advance bookings first;
   - 3+ classes on the same site;
   - avoid mixing Yoga/Fitness unless testing cross-site behavior.
4. Clean expired one-offs when the user is ready.
