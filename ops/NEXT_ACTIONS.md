# Next Actions

Last updated: 2026-06-03

## For Eileen

1. Start the new Product / Booking Engine Codex thread with the prompt in `PRODUCT_THREAD_HANDOVER_2026-06-03.md`.

2. After any future config change, make sure Product uploads the live config to DigitalOcean:

```bash
scp "/Users/eileenmac/Documents/Yoga Booking Bot/pure_yoga_config.json" root@104.248.150.64:/root/PureYogaBot/pure_yoga_config.json
```

3. Watch the next automatic 09:08 Telegram performance report. It should now summarize outcome, first POST timing, Pure queue/backend pressure, multi-site delay, by-site timing, and takeaway.

4. If any future Yoga or Fitness class is highly competitive, avoid mixing important Yoga and Fitness targets in the same run where possible, because multi-site runs are sequential.

5. Keep using Telegram warnings to decide whether to skip one run, remove a recurring target, or adjust config before the morning booking run.

## For Product / Booking Engine

1. Before coding in the next Product thread, read `PRODUCT_THREAD_HANDOVER_2026-06-03.md`, inspect the repo, and verify relevant DigitalOcean state.

2. Continue owning only:
   - `pure_yoga_booking.py`
   - live booking behavior
   - Telegram warnings/notifications
   - DigitalOcean deployment
   - booking performance and timing analysis

3. After every code change that should affect live behavior:

```bash
scp "/Users/eileenmac/Documents/Yoga Booking Bot/pure_yoga_booking.py" root@104.248.150.64:/root/PureYogaBot/pure_yoga_booking.py
ssh root@104.248.150.64 'cd /root/PureYogaBot && .venv/bin/python -m py_compile pure_yoga_booking.py'
```

4. After every config change that should affect live behavior:

```bash
scp "/Users/eileenmac/Documents/Yoga Booking Bot/pure_yoga_config.json" root@104.248.150.64:/root/PureYogaBot/pure_yoga_config.json
ssh root@104.248.150.64 'cd /root/PureYogaBot && .venv/bin/python pure_yoga_booking.py --config pure_yoga_config.json --lookup-only --target-date YYYY-MM-DD'
```

5. Keep `pure_yoga_config.json`, Vultr logs, cron logs, and secrets out of Git.

6. Commit and push safe verified Product code/docs at meaningful checkpoints.

## For UI / Control Panel

1. Keep UI work within UI-owned files unless Product explicitly approves booking-engine changes.

2. Continue treating phone access as a mobile-first web UI / PWA first, not native iOS first.

3. Keep the "Skip this run" workflow clear: it prevents a future bot attempt and does not cancel an already-booked Pure class.
