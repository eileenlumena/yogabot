# Product / Booking Engine Status

Last updated: 2026-05-18

## Coordination Status

- This is the Product / Booking Engine status file.
- Communication protocol is now documented in `DECISIONS.md`.
- Ops coordination files now exist:
  - `ops/HANDOFFS.md`
  - `ops/CEO_ACTION_QUEUE.md`
  - `ops/NEXT_ACTIONS.md`
- Active cross-thread handoffs: UI booking-limit warning request in `ops/HANDOFFS.md`.
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
- UI testing has been moved off the live config: `pure_yoga_admin.py` now defaults to `pure_yoga_config.dev.json`.
- 2026-05-17 issue: no Friday `Mat: Classical Pilates` booking happened because the live local config was missing the recurring Friday Pilates target. Local live config has been restored with `Mat: Classical Pilates` 11:15, April Lu, Yoga - Ngee Ann City.
- 2026-05-17 config update: added recurring Mon Yogasthenics Foundation 16:30, Tue Wall Rope 12:15, Tue Yogasthenics 13:30, Thu Upside Down 09:45, Sat Fitness Calisthenics 12:00, Sat Sound Bath Therapy 15:30; removed Sat Yin Yoga 14:15 and Sat Yoga Therapy 12:30; added one-off 2026-05-23 Yin-Yang 13:45 by Sandy Shum.
- Eileen uploaded the latest live config to the SG server after the 2026-05-17 updates.
- New Product constraint captured for UI: Pure allows max 6 Yoga, 6 Pilates, and 6 Fitness bookings in any continuous 5-day period, plus max 2 bookings per class type per day.
- Booking engine now has Telegram pre-run warnings for booking-limit issues, schedule `NO_MATCH`, and replacement-teacher fallback. Warnings are sent after schedule lookup and before the sleep/login/warmup phase.
- Existing account bookings are now fetched read-only from Pure's `get_booking_history` endpoint before warnings are calculated, so Telegram limit warnings include booked, waitlisted, and signed-in classes in the relevant window plus config-planned targets.
- Added `--warnings-only` mode so SG server can run an evening planning check without sending booking requests. The morning run still keeps its last-minute warning as backup.

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
- Restored live config changes are not in Git because `pure_yoga_config.json` is intentionally ignored; they must be uploaded to SG server separately.
- Existing-booking warning fetch is read-only and non-blocking; if it fails, the bot logs the failure and continues with config-only warning counts.
- Expired one-off targets clutter the config.
- Multi-site runs handle Yoga and Fitness one after another, so they are not the cleanest test of exact 9:00 same-site parallel timing.
- Pure may enforce an advance-booking limit by category/account; this can look like a bot failure if not controlled.
- Pure schedule changes can produce `NO_MATCH`; this is correct behavior when the target class is no longer posted at that time/location.
- `pure_yoga_config.json` contains secrets and must not be committed.

## Next Product Tasks

1. Upload `pure_yoga_booking.py` to the SG server before relying on the latest Telegram pre-run warnings there.
2. Add a separate SG server cron for `--warnings-only`, preferably the evening before the 9am booking run.
3. Upload and verify config before any important run.
4. After the next run, compare performance against previous days side by side.
5. Plan a multi-booking test on non-critical classes:
   - fewer than 5 advance bookings first;
   - 3+ classes on the same site;
   - avoid mixing Yoga/Fitness unless testing cross-site behavior.
6. Clean expired one-offs when the user is ready.
