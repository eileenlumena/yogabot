# Product / Booking Engine Thread Handover

Last updated: 2026-05-18 14:40 SGT

Use this document to start a fresh Codex Product / Booking Engine thread. Do not rely on old chat memory. First read this file, then inspect the repo before making changes.

## First Instructions For New Thread

1. Work from:
   `/Users/eileenmac/Documents/Yoga Booking Bot`
2. This thread owns Product / Booking Engine work:
   - `pure_yoga_booking.py`
   - booking correctness
   - matching logic
   - Telegram booking notifications
   - SG server deployment commands
   - performance and timing analysis
3. UI / Control Panel work is separate unless Eileen explicitly asks this thread to handle UI.
4. Before ending work, update:
   - `product/PRODUCT_STATUS.md`
   - `ops/NEXT_ACTIONS.md`
5. If UI needs to do something, write it in:
   - `ops/HANDOFFS.md`
6. If Eileen needs to decide or review something, write it in:
   - `ops/CEO_ACTION_QUEUE.md`
7. If direction or constraints change, update:
   - `DECISIONS.md`
8. Do not commit secrets. `pure_yoga_config.json` is live and intentionally ignored by Git.

## Permission / Access Checklist

For the new thread, Eileen may need to grant or confirm these permissions again:

1. Filesystem access to:
   `/Users/eileenmac/Documents/Yoga Booking Bot`
2. Network access / approval when running read-only Pure lookups from local Codex:
   - `python3 pure_yoga_booking.py --config pure_yoga_config.json --lookup-only ...`
   - `python3 pure_yoga_booking.py --config pure_yoga_config.json --warnings-only ...`
3. GitHub push permission for:
   `https://github.com/eileenlumena/yogabot.git`
4. SSH/SCP permission to SG server:
   - host: `root@45.77.249.30`
   - server path: `/root/PureYogaBot`
5. Computer Use / Chrome permission only if inspecting the logged-in Pure website manually.
6. Do not ask Eileen to move the bot out of Documents. She explicitly said not to.

Current useful approved commands have previously included:

```bash
python3 pure_yoga_booking.py
python3 -m py_compile pure_yoga_booking.py pure_yoga_admin.py
scp "/Users/eileenmac/Documents/Yoga Booking Bot/pure_yoga_booking.py" root@45.77.249.30:/root/PureYogaBot/pure_yoga_booking.py
scp "/Users/eileenmac/Documents/Yoga Booking Bot/pure_yoga_config.json" root@45.77.249.30:/root/PureYogaBot/pure_yoga_config.json
ssh root@45.77.249.30
git add
git commit
git push
```

If a command fails due to sandbox/network restrictions, request escalation normally.

## Current Repo State

Latest Product commits pushed to GitHub:

```text
f4deb7f Add warning-only preflight mode
612c65b Include existing bookings in limit warnings
d49faf6 Add Telegram pre-run warnings
60206c6 Document Pure booking limit UI handoff
c4fe71d Document Saturday Yoga Therapy removal
```

Important: at handover time there are unrelated UI-thread local modifications:

```text
M pure_yoga_admin.py
M ui/UI_STATUS.md
```

Those were not Product changes. Do not revert them unless Eileen explicitly asks.

## Current Architecture

Main runner:

```bash
python3 pure_yoga_booking.py --config pure_yoga_config.json
```

Main files:

- `pure_yoga_booking.py`: booking engine.
- `pure_yoga_config.json`: live local config with credentials and Telegram tokens. Ignored by Git.
- `pure_yoga_config.example.json`: tracked sanitized example.
- `pure_yoga_admin.py`: UI / Control Panel, defaulting to `pure_yoga_config.dev.json`.
- `product/PRODUCT_STATUS.md`: Product status.
- `ui/UI_STATUS.md`: UI status.
- `ops/HANDOFFS.md`: cross-thread handoffs.
- `ops/NEXT_ACTIONS.md`: what Eileen/thread should do next.
- `DECISIONS.md`: project constraints and decisions.

## What The Bot Does In A Normal Morning Run

Assume Pure booking opens at 09:00 SGT.

1. Server cron starts the bot around 08:58 SGT.
2. Bot reads `pure_yoga_config.json`.
3. Bot identifies active targets for the run date.
4. Bot fetches Pure schedule for each active site/location.
5. Bot matches targets by class name, time, location, and teacher policy.
6. Bot checks warning conditions:
   - class not found / `NO_MATCH`
   - teacher changed / replacement teacher fallback
   - Pure booking limits
   - existing bookings/waitlists from My Bookings
7. Bot sends Telegram warning only if there is something to warn about.
8. Around 08:59:40, bot logs in and prepares booking transport.
9. Around 08:59:59.300, bot sends late warmup request and logs warmup RTT / CloudFront POP.
10. Around 08:59:59.800, aggressive probe starts.
11. At booking open, bot sends booking requests.
12. For same-site multi-class `book_all`, bot uses focus-first strategy.
13. Bot refreshes schedule after batch submissions to confirm real outcome.
14. Bot sends final Telegram summary.

## New Evening Warning-Only Mode

Eileen said the 08:58 warning is too late to react. Product added:

```bash
python3 pure_yoga_booking.py --config pure_yoga_config.json --warnings-only
```

This mode:

- reads active targets
- fetches Pure schedule
- checks existing My Bookings / waitlists
- sends Telegram warnings only if needed
- sends no booking requests
- exits before sleep/login/warmup booking sequence

Recommended schedule: evening before the 09:00 booking run, for example 20:00 SGT.

The normal 08:58 run still keeps warning checks as a last safety backup.

Important: `--warnings-only` with no `--target-date` checks the run date implied by that day. Because booking opens 5 days before class date, an evening run on 18 May checks the same booking run date as the 19 May morning run only if the config targets are active for that run date. Verify expected behavior before relying on cron.

Tested locally:

```bash
python3 pure_yoga_booking.py --config pure_yoga_config.json --warnings-only --target-date 2026-05-23
```

Result: resolved classes, fetched My Bookings, sent no booking requests, exited cleanly.

## Existing Bookings / My Bookings Endpoint

Safe read-only endpoint identified from Pure frontend bundle and tested:

```text
GET https://pure360-api-sg.pure-international.com/api/v3/get_booking_history
```

The bot uses it via `SiteClient.fetch_booking_history()`.

Purpose:

- include already booked classes
- include waitlisted classes
- include signed-in classes
- combine with planned config targets
- warn before hitting Pure limits

If this fetch fails, bot logs the failure and continues with config-only warnings. It must not block booking.

Pure booking limits Eileen supplied:

- max 6 Yoga classes in any continuous 5-day period
- max 6 Pilates classes in any continuous 5-day period
- max 6 Fitness classes in any continuous 5-day period
- max 2 bookings per class type per day

Classification logic:

- `site == fitness` -> Fitness
- Yoga-site class names containing `reformer` or `pilates` -> Pilates
- other Yoga-site classes -> Yoga

## Telegram Notifications

Final booking summaries are user-clean:

```text
Pure booking run for 2026-05-23

BOOKED | 2026-05-23 13:45 | Grounding: Yin-Yang | Sandy Shum
Yoga - Ngee Ann City
```

Class id and generic `Success` text were removed.

If waitlisted, bot should show waitlist status/number where Pure exposes it through schedule verification.

Pre-run warnings can include:

- booking limit warning
- schedule/teacher warning
- no-match warning

## Current Live Config Summary

Live config file:

```text
pure_yoga_config.json
```

It is ignored by Git and contains secrets. Do not print or commit credentials/tokens.

Current important recurring targets:

1. Mon Fitness `Calisthenics Foundations` 12:00, Fitness - Ngee Ann City, Joshua Tay.
2. Mon Fitness `Calisthenics Foundations` 18:30, Fitness - Ngee Ann City, Joshua Tay.
3. Tue Yoga/Pilates `Reformer Signature` 10:00, Yoga - Ngee Ann City, Kelvin Teo.
4. Fri Yoga/Pilates `Mat: Classical Pilates` 11:15, Yoga - Ngee Ann City, April Lu.
5. Mon Yoga `Specialised: Yogasthenics Foundation` 16:30, Yoga - Ngee Ann City, Aries Ong.
6. Tue Yoga `Specialised: Wall Rope` 12:15, Yoga - Ngee Ann City, Dagge Ong.
7. Tue Yoga `Specialised: Yogasthenics` 13:30, Yoga - Ngee Ann City, Wen Wen Chen.
8. Thu Yoga `Specialised: Upside Down` 09:45, Yoga - Ngee Ann City, Kelvin Teo.
9. Sat Fitness `Calisthenics Foundations` 12:00, Fitness - Ngee Ann City, Joshua Tay.
10. Sat Yoga `Healing: Sound Bath Therapy` 15:30, Yoga - Asia Square Tower 1, Inder S.

Current one-off still relevant as of 2026-05-18:

- 2026-05-23 Yoga `Grounding: Yin-Yang` 13:45, Yoga - Ngee Ann City, Sandy Shum, booking_run_date 2026-05-18.

There are several expired one-offs still in config. They are controlled by old `booking_run_date` values and should not activate, but they clutter the file.

Known removed classes:

- Sat `Healing: Yin Yoga` 14:15 at Asia Square removed/replaced.
- Sat `Healing: Yoga Therapy` 12:30 at Ngee Ann removed.

## Latest Schedule Check

On 2026-05-18, Eileen asked what is on schedule tomorrow.

Read-only lookup was run:

```bash
python3 pure_yoga_booking.py --config pure_yoga_config.json --lookup-only --target-date 2026-05-24
```

Result:

```text
No configured targets are active for 2026-05-24.
```

Interpretation: for Tuesday 19 May 2026 booking run, there are no configured targets to book for Sunday 24 May 2026.

## SG Server

Server:

```text
root@45.77.249.30
```

Project path:

```text
/root/PureYogaBot
```

Upload booking engine:

```bash
scp "/Users/eileenmac/Documents/Yoga Booking Bot/pure_yoga_booking.py" root@45.77.249.30:/root/PureYogaBot/pure_yoga_booking.py
```

Upload live config:

```bash
scp "/Users/eileenmac/Documents/Yoga Booking Bot/pure_yoga_config.json" root@45.77.249.30:/root/PureYogaBot/pure_yoga_config.json
```

Check server file timestamp:

```bash
ssh root@45.77.249.30 'stat /root/PureYogaBot/pure_yoga_config.json'
```

Check server logs:

```bash
ssh root@45.77.249.30 'cd /root/PureYogaBot && tail -n 150 logs/pure_booking_$(date +%Y%m%d).log'
```

Important: after `f4deb7f`, server needs updated `pure_yoga_booking.py` uploaded before `--warnings-only` exists on the server.

## Suggested SG Cron Setup

Existing live booking cron should continue around 08:58 SGT.

Add separate warning-only cron, preferably evening before booking, for example 20:00 SGT:

```bash
cd /root/PureYogaBot
python3 pure_yoga_booking.py --config pure_yoga_config.json --warnings-only
```

Before adding cron, run manually once on server:

```bash
ssh root@45.77.249.30 'cd /root/PureYogaBot && python3 pure_yoga_booking.py --config pure_yoga_config.json --warnings-only'
```

If no warnings exist, Telegram may stay quiet. Check logs to confirm it ran.

## GitHub

Repo:

```text
https://github.com/eileenlumena/yogabot
```

Remote:

```bash
git remote -v
```

Expected:

```text
origin https://github.com/eileenlumena/yogabot.git
```

Commit/push guidance:

- Commit and push meaningful verified Product changes.
- Do not commit live config, logs, caches, generated files, or secrets.
- If unrelated UI files are dirty, do not stage them from Product thread.

## Performance Context

The bot has performed well recently after code improvements and SG server migration.

Important metrics in logs:

- warmup RTT
- booking RTT
- response gap
- focus send delta
- residual jitter
- focus queue proxy
- follower queue proxy
- CloudFront POP

Current strategy:

- `book_all`
- HTTP/2 booking transport
- late warmup
- aggressive probe
- focus-first multi-class submission
- deferred schedule verification after batch submission

Multi-site behavior:

- Yoga and Fitness are handled sequentially to avoid session replacement.
- If Yoga and Fitness are in same run, second site sends later.
- This is currently accepted because results have been good.

## Recent Live Outcomes / Context

2026-05-14 run for 2026-05-19:

- BOOKED Yoga 12:15 Wall Rope, Dagge Ong.
- BOOKED Yoga 10:00 Reformer Signature, Kelvin Teo.
- BOOKED Yoga 13:30 Yogasthenics, Wen Wen Chen.
- BOOKED Fitness 18:45 RPM, Ayu Astutik.
- BOOKED Fitness 17:45 BODYCOMBAT, House Chaalane.

Notes:

- Yoga warmup RTT was elevated at 218.6ms but still booked all.
- Fitness was sent after Yoga due to multi-site sequencing and still booked.

2026-05-17 issue:

- Friday Classical Pilates did not book because the recurring target was missing from live local config.
- It was restored.
- Eileen uploaded latest live config to SG server after 2026-05-17 updates.

## Important User Preferences

- Keep answers short and practical unless asked for detail.
- Eileen wants plain English explanations, not too technical.
- Do not set reminders at weird times without thinking about whether Eileen is actively present.
- Do not move the bot out of Documents.
- UI testing must not affect live config.
- For important classes, avoid using them as stress tests.
- Compare performance side by side over multiple days, not just single-day metrics.

## Open / Next Tasks

1. Upload latest `pure_yoga_booking.py` to SG server so `--warnings-only` and existing-booking limit warnings are live.
2. Add SG cron for evening `--warnings-only` check.
3. Confirm whether warning-only cron should run at 20:00 SGT or another time Eileen prefers.
4. Watch next warning-only run log and Telegram behavior.
5. Clean expired one-offs later when Eileen is ready.
6. Continue UI thread separately for control panel and warning UI.

## Verification Commands

Compile:

```bash
python3 -m py_compile pure_yoga_booking.py pure_yoga_admin.py
```

Lookup active targets for a class date:

```bash
python3 pure_yoga_booking.py --config pure_yoga_config.json --lookup-only --target-date YYYY-MM-DD
```

Warning-only local test:

```bash
python3 pure_yoga_booking.py --config pure_yoga_config.json --warnings-only --target-date YYYY-MM-DD
```

Normal dry run:

```bash
python3 pure_yoga_booking.py --config pure_yoga_config.json --dry-run
```

Normal live run:

```bash
python3 pure_yoga_booking.py --config pure_yoga_config.json
```

Be careful: normal live run can book classes when run at the right time.

