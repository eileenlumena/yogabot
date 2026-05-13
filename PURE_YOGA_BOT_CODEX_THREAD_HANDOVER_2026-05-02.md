# Pure Yoga Bot Thread Handover

## 1. Project Goal
- Automate Pure Yoga / Pure Fitness Singapore class booking at the 5-days-ahead opening edge.
- Optimize for hard timing metrics, not just booked outcomes:
  - earliest accepted focus send
  - follower send timing
  - focus send delta
  - residual jitter
  - warmup RTT
  - booking RTT / queue proxy

## 2. Current Architecture
- Main runner: `/Users/eileenmac/Documents/Yoga Booking Bot/pure_yoga_booking.py`
- Config: `/Users/eileenmac/Documents/Yoga Booking Bot/pure_yoga_config.json`
- Server: Vultr Singapore Ubuntu 24.04
- Server bot path: `/root/PureYogaBot`
- Schedule: cron runs daily at `08:58 SGT`
- Flow:
  - resolve matching classes and live `class_id`
  - refresh `X-Date` / `X-Token`
  - login
  - warm shared booking transport
  - send focus-first `book_all` batch
  - log detailed transport / timing / queue proxy metrics
- Transport:
  - `httpx` with HTTP/2 when available
  - browser-like headers and cookies synced into booking transport
  - fallback path still exists via `requests`

## 3. Files Changed And Why
- `/Users/eileenmac/Documents/Yoga Booking Bot/pure_yoga_booking.py`
  - added HTTP/2 booking transport
  - added browser-mimic request headers and cookie sync
  - added late warmup on booking transport
  - added pre-armed worker pool
  - added focus-first / gate-aware follower release
  - added instrumentation:
    - warmup RTT
    - request send/response timestamps
    - HTTP version / CloudFront POP / Via / Server-Timing
    - batch id, response gap, queue proxies
- `/Users/eileenmac/Documents/Yoga Booking Bot/pure_yoga_config.json`
  - recurring targets maintained here
  - one-off test classes rotated here
  - current timing knobs live here
  - latest local change: rolled `aggressive_probe_lead_ms` back from `240` to `200`
- `/Users/eileenmac/Documents/Yoga Booking Bot/requirements.txt`
  - includes `httpx[http2]` for shared transport
- `/Users/eileenmac/Documents/Yoga Booking Bot/PURE_YOGA_BOT_HANDOVER.md`
  - older broad handover exists
- `/Users/eileenmac/Documents/Yoga Booking Bot/PURE_YOGA_BOT_CODEX_THREAD_HANDOVER_2026-05-02.md`
  - this concise new-thread handover

## 4. Important Decisions Made
- Focus on timing metrics, not booked/waitlisted outcomes.
- Keep `book_all` as default for paired windows unless explicitly changed.
- Use focus-first strategy for same-site paired runs.
- Preserve follower spacing after gate opens instead of letting both requests collapse together.
- Instrument server-path metadata instead of guessing about backend delay.
- Do not trust expired one-offs as active targets; always respect `booking_run_date`.
- Singapore VPS is helpful but has not shown a decisive standalone win yet.

## 5. Current Status
- Bot-side mechanics are now mostly good:
  - clean focus/follower spacing was restored
  - instrumentation is in place
  - same CloudFront POP (`SIN2-P11`) repeatedly observed
- Remaining issue is mainly server-side queueing after request leaves the bot.
- Latest analyzed run: `2026-05-02` for target date `2026-05-07`
  - warmup RTT: `33.8 ms`
  - accepted focus send: `08:59:59.976`
  - follower send: `09:00:00.097`
  - focus send delta: `121.2 ms`
  - residual jitter: `+1.2 ms`
  - queue proxies: `+1915.1 / +2081.3 ms`
  - issue: `aggressive_probe_lead_ms=240` caused 5 early `426` responses and made accepted sends later
- Local config is now rolled back to `aggressive_probe_lead_ms=200`
  - confirm SG server config matches before next run

## 6. Remaining TODOs
- Upload latest local config to SG server if not already done.
- Confirm SG server now has:
  - `"aggressive_probe_lead_ms": 200`
- Run the next scheduled booking and compare against:
  - `2026-05-01`
  - `2026-05-02`
  - `2026-04-30`
- Continue using instrumentation to determine whether RTT spikes are backend-only.

## 7. Known Bugs Or Risks
- Too-early probing can worsen accepted send timing by generating multiple `426` retries.
- Server RTT is highly variable and mostly outside bot control.
- Expired one-offs can confuse humans reading config; do not treat them as active.
- User is sensitive to careless date/day mistakes; verify run date vs target date carefully.
- Secrets exist in config; never echo credentials or Telegram tokens.

## 8. Exact Next Recommended Task
- Upload the rolled-back config (`aggressive_probe_lead_ms=200`) to the SG server.
- Do not change code behavior again yet.
- On the next run, compare:
  - accepted focus send
  - follower send
  - focus send delta
  - residual jitter
  - warmup RTT
  - queue proxies
- Success criteria for this next step:
  - fewer early `426`s than the `240ms` experiment
  - accepted focus send earlier than `08:59:59.976`
  - keep focus send delta near `120 ms`

## 9. Commands To Run / Test
- Upload config to SG server:
```bash
scp "/Users/eileenmac/Documents/Yoga Booking Bot/pure_yoga_config.json" root@45.77.249.30:/root/PureYogaBot/pure_yoga_config.json
```

- Upload code to SG server:
```bash
scp "/Users/eileenmac/Documents/Yoga Booking Bot/pure_yoga_booking.py" root@45.77.249.30:/root/PureYogaBot/pure_yoga_booking.py
```

- Verify config on SG server:
```bash
ssh root@45.77.249.30 'grep -n "aggressive_probe_lead_ms" /root/PureYogaBot/pure_yoga_config.json'
```

- Verify code markers on SG server:
```bash
ssh root@45.77.249.30 'grep -n "response_gap_ms\\|focus_queue_proxy_ms\\|probe_release_notifier" /root/PureYogaBot/pure_yoga_booking.py'
```

- Tail latest SG log:
```bash
ssh root@45.77.249.30 'cd /root/PureYogaBot && tail -n 150 logs/pure_booking_$(date +%Y%m%d).log'
```

- Local lookup-only verification:
```bash
python3 "/Users/eileenmac/Documents/Yoga Booking Bot/pure_yoga_booking.py" --config "/Users/eileenmac/Documents/Yoga Booking Bot/pure_yoga_config.json" --lookup-only --target-date YYYY-MM-DD
```

- Local syntax check:
```bash
python3 -m py_compile "/Users/eileenmac/Documents/Yoga Booking Bot/pure_yoga_booking.py"
```

## 10. Constraints / Things Not To Change
- Do not remove the current instrumentation.
- Do not make another major timing rewrite until one more run is observed at `200ms`.
- Do not judge improvements primarily by booked status.
- Do not assume one-offs are active without checking `booking_run_date`.
- Do not expose secrets from config or captured headers.
- Keep edits ASCII unless the file already uses non-ASCII.
