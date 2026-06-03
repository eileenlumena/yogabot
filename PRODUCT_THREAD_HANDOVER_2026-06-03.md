# Product / Booking Engine Thread Handover

Date: 2026-06-03
Timezone: Asia/Singapore

Use this document to start a fresh Codex Product / Booking Engine thread. Do not rely on old chat memory. First read this file, then inspect the repo and server state before making changes.

## Thread Scope

This Product / Booking Engine thread owns only:

- `pure_yoga_booking.py`
- live booking behavior
- Telegram warnings and notifications
- DigitalOcean / SG server deployment
- booking performance and timing analysis

Do not touch UI files unless Eileen explicitly asks. UI/control-panel roadmap and cross-thread requests live in `ops/HANDOFFS.md`.

## Workspace

Local workspace:

```text
/Users/eileenmac/Documents/Yoga Booking Bot
```

Important local files:

- `pure_yoga_booking.py`: live booking engine.
- `pure_yoga_config.json`: live config with secrets; ignored by Git; never commit or print whole.
- `pure_yoga_config.dev.json`: safe-ish dev config for UI/admin testing.
- `product/PRODUCT_STATUS.md`: Product status.
- `ops/HANDOFFS.md`: cross-thread handoffs.
- `ops/NEXT_ACTIONS.md`: operational next actions.

## Active Server

Active live bot server is DigitalOcean Singapore:

```text
root@104.248.150.64
/root/PureYogaBot
```

Vultr server `root@45.77.249.30` is disabled and retained only as backup. Its crontab entries were commented out.

DigitalOcean verified on 2026-06-03 at 10:47 +08:

```bash
ssh root@104.248.150.64 'date; crontab -l | grep -E "warnings-only|performance-report|pure_yoga_booking.py --config"; cd /root/PureYogaBot && .venv/bin/python -m py_compile pure_yoga_booking.py'
```

Server date returned `Wed Jun 3 10:47:02 +08 2026`.

## DigitalOcean Cron

Current active crontab:

```cron
0 20 * * * cd /root/PureYogaBot && /root/PureYogaBot/.venv/bin/python /root/PureYogaBot/pure_yoga_booking.py --config /root/PureYogaBot/pure_yoga_config.json --warnings-only >> /root/PureYogaBot/warnings_only_cron.log 2>&1

45 8 * * * cd /root/PureYogaBot && /root/PureYogaBot/.venv/bin/python /root/PureYogaBot/pure_yoga_booking.py --config /root/PureYogaBot/pure_yoga_config.json >> /root/PureYogaBot/cron.log 2>&1

8 9 * * * cd /root/PureYogaBot && /root/PureYogaBot/.venv/bin/python /root/PureYogaBot/pure_yoga_booking.py --config /root/PureYogaBot/pure_yoga_config.json --performance-report >> /root/PureYogaBot/performance_report.log 2>&1
```

Meaning:

- 20:00: evening warning-only scan for the next booking run.
- 08:45: live booking run.
- 09:08: automated Telegram performance report based on latest completed `cron.log`.

## Upload / Verification Commands

Upload code:

```bash
scp "/Users/eileenmac/Documents/Yoga Booking Bot/pure_yoga_booking.py" root@104.248.150.64:/root/PureYogaBot/pure_yoga_booking.py
```

Upload live config:

```bash
scp "/Users/eileenmac/Documents/Yoga Booking Bot/pure_yoga_config.json" root@104.248.150.64:/root/PureYogaBot/pure_yoga_config.json
```

Server compile check:

```bash
ssh root@104.248.150.64 'cd /root/PureYogaBot && .venv/bin/python -m py_compile pure_yoga_booking.py'
```

Lookup test:

```bash
ssh root@104.248.150.64 'cd /root/PureYogaBot && .venv/bin/python pure_yoga_booking.py --config pure_yoga_config.json --lookup-only --target-date YYYY-MM-DD'
```

Performance report dry-run:

```bash
ssh root@104.248.150.64 'cd /root/PureYogaBot && .venv/bin/python pure_yoga_booking.py --config pure_yoga_config.json --performance-report --dry-run'
```

Send live performance report:

```bash
ssh root@104.248.150.64 'cd /root/PureYogaBot && .venv/bin/python pure_yoga_booking.py --config pure_yoga_config.json --performance-report'
```

## Current Live Config / Recurring Targets

As read from local `pure_yoga_config.json` on 2026-06-03. The same config was uploaded to DigitalOcean during recent work.

```text
fitness | Mon | Calisthenics Foundations | 12:00 | Fitness - Ngee Ann City | Joshua Tay | priority=1
fitness | Mon | Mat: Power Pilates | 11:15 | Fitness - Asia Square Tower 1 | Stephany Widjaya | priority=1
yoga | Mon | Specialised: Yogasthenics Foundation | 16:30 | Yoga - Ngee Ann City | Aries Ong | priority=1

yoga | Tue | Reformer Dynamic | 10:00 | Yoga - Ngee Ann City | Kelvin Teo | priority=2
yoga | Tue | Mat: Strength Pilates | 11:15 | Yoga - Ngee Ann City | Thu Nguyen | priority=4
yoga | Tue | Specialised: Wall Rope | 12:15 | Yoga - Ngee Ann City | Dagge Ong | priority=1
yoga | Tue | Specialised: Yogasthenics Foundation | 13:45 | Yoga - Ngee Ann City | Wen Wen Chen | priority=3

yoga | Wed | Specialised: Yogasthenics Foundation | 13:45 | Yoga - Asia Square Tower 1 | Wen Wen Chen | priority=1
yoga | Wed | Specialised: Aerial Stretch | 15:00 | Yoga - Asia Square Tower 1 | Sandy Shum | priority=2

yoga | Thu | Specialised: Upside Down | 09:45 | Yoga - Ngee Ann City | Kelvin Teo | priority=4
yoga | Thu | Grounding: Hatha Advanced | 11:00 | Yoga - Ngee Ann City | Sandy Shum | priority=1

yoga | Fri | Mat: Classical Pilates | 11:15 | Yoga - Ngee Ann City | April Lu | priority=1

fitness | Sat | Calisthenics Foundations | 13:00 | Fitness - Ngee Ann City | Joshua Tay | priority=1
yoga | Sat | Healing: Sound Bath Therapy | 15:30 | Yoga - Asia Square Tower 1 | Inder S. | priority=2
```

No active one-offs are expected at this handover. If adding one-offs, remember to upload `pure_yoga_config.json` to DigitalOcean after editing.

## Recent Config Decisions

- Monday `BODYCOMBAT™` 10:15 Fitness Asia Square by Stephany was permanently removed because three Fitness classes in one day is not allowed.
- Monday `Calisthenics Foundations` changed permanently from 18:30 to 12:00 and should remain priority 1.
- Tuesday Kelvin Pilates class changed permanently from `Reformer Signature` to `Reformer Dynamic`.
- Tuesday `Specialised: Yogasthenics Foundation` changed permanently from 13:30 to 13:45.
- Saturday `Calisthenics Foundations` changed permanently from 12:00 to 13:00.
- Expired one-offs were cleared.

## Important Booking Engine Behavior

Current `pure_yoga_booking.py` includes:

- Aggressive probe mode with booking attempts beginning 200ms before 9am.
- HTTP/2 booking transport via `httpx` where available.
- Focus-first parallel submission for multiple same-site `book_all` targets.
- Multi-site runs are sequential to avoid Pure session replacement across Yoga/Fitness sites.
- Late booking transport warmup logs RTT, CloudFront POP, HTTP version, and response metadata.
- Final summaries use display date/time format like `Sat 6 Jun 2026 13:00`.

## Warnings / Safety Features

Telegram pre-run warnings include:

- Rolling 5-day booking limit warnings.
- Daily class-type booking limit warnings.
- Schedule `NO_MATCH` warnings.
- Replacement-teacher warnings.
- Existing booked/waitlisted/signed-in classes from Pure's read-only `get_booking_history`.
- Overlap warnings using Pure start/end/duration fields.

Important logic correction:

- Booking-limit warnings count existing Pure bookings plus only the targets active in the current booking run. Future recurring targets in the same rolling window are not counted as "Bot plans to book" unless they are active for the current run.

Schedule/teacher warnings now use a high-visibility Telegram format:

```text
🚨 SCHEDULE / TEACHER WARNING 🚨
⚠️ 1. Class name
Date/time: Wed 3 Jun 2026 15:00
Location: Asia Sq
Issue: class not matched / teacher changed
Detail: ...
Possible match(es): ...
Action: check Pure app or skip this run.
```

`NO_MATCH` closest-match logic:

- Shows exact target-time/location replacements.
- Shows close same-date class-name matches across locations.
- Class IDs are omitted.
- Recently fixed so related classes at very different times on the same date can still appear, e.g. Calisthenics 18:30 target vs actual 12:00 class.

## Automated Performance Reports

New on 2026-06-03:

- Added CLI flag `--performance-report`.
- Cron runs daily at 09:08.
- It reads latest completed booking run from `/root/PureYogaBot/cron.log`.
- It does not call Pure and does not affect booking speed.
- It sends a Telegram report with:
  - overall verdict: `GOOD`, `MIXED`, or `NEEDS ATTENTION`;
  - booked count;
  - first POST timing vs 9am;
  - Pure queue/backend wait;
  - multi-site delay;
  - class-by-class outcomes;
  - timing health;
  - by-site breakdown;
  - plain-English takeaway.

Example latest report from 2026-06-03:

```text
PURE BOT PERFORMANCE: GOOD
Run: Wed 3 Jun 2026
Target class date: Mon 8 Jun 2026

SUMMARY
- Booked: 3/3
- First booking POST: 08:59:59.800 (-0.200s vs 9am, on target)
- Pure queue/backend wait: up to 2192.1ms (busy)
- Multi-site note: last site started +5.146s vs 9am

CLASSES
- BOOKED: Mon 8 Jun 2026 12:00 Calisthenics Foundations by Joshua Tay, Ngee Ann City
- BOOKED: Mon 8 Jun 2026 11:15 Power Pilates by Stephany Widjaya, Asia Sq
- BOOKED: Mon 8 Jun 2026 16:30 Yogasthenics Foundation by Aries Ong, Ngee Ann City

TIMING HEALTH
- Network warmup: 50.0ms (good)
- Booking response time: 141.6-2242.1ms
- Pure queue/backend pressure: 2192.1ms max (busy)
- CloudFront POP: SIN2-P11

BY SITE
- Fitness: warmup 50.0ms, first POST 08:59:59.800 (-0.200s), RTT 2118.2-2242.1ms, 2 request(s)
- Yoga: first POST 09:00:05.146 (+5.146s), RTT 141.6ms, 1 request(s)

TAKEAWAY
- Booking outcome was good: all final targets booked.
- Main performance bottleneck: multi-site sequencing delayed the later site.
```

## Recent Performance Notes

- DigitalOcean performance is generally good and comparable to good Vultr runs.
- 2026-05-30 DO run for 2026-06-04:
  - booked Upside Down 09:45 and Hatha Advanced 11:00;
  - warmup RTT 31.1ms;
  - focus send residual jitter +0.7ms;
  - both booked.
- 2026-06-01 DO run for 2026-06-06:
  - booked Sat Calisthenics 13:00 and Sound Bath 15:30;
  - Fitness first POST was on target at 08:59:59.800;
  - Yoga was second site and started around 09:00:07 due sequential multi-site behavior;
  - both booked.
- 2026-06-03 DO run for 2026-06-08:
  - booked all three targets;
  - bottleneck was multi-site sequencing and Pure backend queue, not DigitalOcean network warmup.

## Git / Repo State

Remote:

```text
origin https://github.com/eileenlumena/yogabot.git
```

Latest pushed commit as of handover:

```text
d0ce24a Improve booking warnings and UI handoff docs
```

Current known local dirty state after the latest work:

- `pure_yoga_booking.py` modified with:
  - UI-thread confirmation date formatting that Product reviewed/uploaded;
  - no-match suggestion timing improvements;
  - `--performance-report` implementation and improved report formatting.
- `ops/HANDOFFS.md` modified.
- `product/PRODUCT_STATUS.md`, `ops/NEXT_ACTIONS.md`, and this handover file may be modified by this handover pass.
- `pure_yoga_config.json` modified but intentionally ignored by Git.
- Untracked `vultr_cron.log` and `vultr_warnings_only_cron.log`; do not commit.

If committing, stage only tracked code/docs that are safe:

```bash
git add pure_yoga_booking.py product/PRODUCT_STATUS.md ops/HANDOFFS.md ops/NEXT_ACTIONS.md PRODUCT_THREAD_HANDOVER_2026-06-03.md
git commit -m "Add performance reports and product handover"
git push
```

Do not stage `pure_yoga_config.json` or Vultr logs.

## Open Risks / Things To Watch

- Server config can fall behind local config. After every config edit, upload to DigitalOcean and explicitly say whether upload happened.
- Multi-site runs book one site after another. If a high-demand Yoga class and high-demand Fitness class open in the same run, the second site can start several seconds late.
- Pure backend queue can dominate response time even when warmup is good.
- Booking-limit warnings depend on Pure existing bookings fetch. If that read-only call fails, bot continues with config-only warning counts.
- `Mat: Classical Pilates` Friday may be temporary on/off depending on teacher availability; current policy is to keep the recurring target and let it fail with warning if unavailable.
- `Specialised: Upside Down` usually expects Kelvin Teo but replacements can happen; current `teacher_policy=prefer_named_teacher` books replacement teachers with warning unless Eileen skips the run.
- The 09:08 performance report currently analyzes only latest completed run in `cron.log`. If cron log is manually truncated or malformed, report may fail gracefully and Telegram a failure message.

## Next Product Thread Start Prompt

Paste this into the new Product / Booking Engine thread:

```text
You are continuing the Pure Yoga Booking Bot Product / Booking Engine thread.

First read this handover carefully:
`/Users/eileenmac/Documents/Yoga Booking Bot/PRODUCT_THREAD_HANDOVER_2026-06-03.md`

Then inspect the repo before making any changes. Do not rely on chat memory. Do not assume anything not confirmed by files.

This thread owns Product / Booking Engine work only:
- `pure_yoga_booking.py`
- live booking behavior
- Telegram warnings/notifications
- DigitalOcean / SG server deployment
- booking performance and timing analysis

Do not touch UI files unless I explicitly ask.

After reading and inspecting, summarize:
1. current bot state
2. current live config / active booking targets
3. current DigitalOcean cron/server deployment
4. what changed since the previous thread
5. any risks or next actions

Do not code until you summarize your understanding first.
```

