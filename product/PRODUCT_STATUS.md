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
- Push from Codex was blocked by GitHub credential prompting.
- Eileen tried HTTPS username/password push; GitHub rejected it because password authentication is no longer supported for Git operations.
- Next GitHub auth path should use either a personal access token, SSH key, or GitHub CLI login.
- Eileen could not see `Developer settings` in the visible GitHub settings sidebar; direct fine-grained token URL was provided in `ops/NEXT_ACTIONS.md`.

## Current State

- Booking outcomes have recently been strong.
- The Singapore server likely helps with path consistency, but backend queueing still varies day to day.
- The engine has useful timing logs for warmup RTT, booking RTT, focus/follower spacing, queue proxy, CloudFront POP, and response metadata.
- Telegram notifications are cleaner than the original format: class id and generic success text were removed from user-facing final summaries.
- The config supports `skip_booking_run_dates` for temporary schedule changes.

## Immediate Run Context

Tomorrow's intended booking run is 2026-05-14 for 2026-05-19 classes.

Local config currently includes five active targets for that run:

- Yoga 10:00 `Reformer Signature`, Kelvin Teo, Yoga - Ngee Ann City.
- Yoga 12:15 `Specialised: Wall Rope`, Dagge Ong, Yoga - Ngee Ann City.
- Yoga 13:30 `Specialised: Yogasthenics`, Wen Wen Chen, Yoga - Ngee Ann City.
- Fitness 18:45 `RPM™`, Ayu Astutik, Fitness - Asia Square Tower 1.
- Fitness 17:45 `BODYCOMBAT™`, House Chaalane, Fitness - Ngee Ann City.

The server may not have this latest config unless it has been uploaded.

## Known Issues / Risks

- Server config can fall behind local config.
- Expired one-off targets clutter the config.
- Multi-site runs handle Yoga and Fitness one after another, so they are not the cleanest test of exact 9:00 same-site parallel timing.
- Pure may enforce an advance-booking limit by category/account; this can look like a bot failure if not controlled.
- Pure schedule changes can produce `NO_MATCH`; this is correct behavior when the target class is no longer posted at that time/location.
- `pure_yoga_config.json` contains secrets and must not be committed.

## Next Product Tasks

1. Push the safe local baseline to GitHub from an authenticated Mac Terminal session.
2. Upload and verify config before any important run.
3. After the next run, compare performance against previous days side by side.
4. Plan a multi-booking test on non-critical classes:
   - fewer than 5 advance bookings first;
   - 3+ classes on the same site;
   - avoid mixing Yoga/Fitness unless testing cross-site behavior.
5. Clean expired one-offs when the user is ready.
