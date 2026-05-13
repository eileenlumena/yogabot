# Product / Booking Engine Handover

Last updated: 2026-05-13

## Ownership

This thread owns the booking engine and optimization work:

- `pure_yoga_booking.py`
- booking strategy and timing settings in `pure_yoga_config.json`
- target activation rules
- live class matching
- booking, waitlist, and failure handling
- Telegram notification formatting
- server deployment and log analysis

The UI thread may edit the control panel, but must not change booking behavior without Product approval.

## Current Engine

The bot:

1. Loads `pure_yoga_config.json`.
2. Determines the active class date from the booking run date and each target's `class_days_ahead`, `class_date`, or `booking_run_date`.
3. Fetches Pure schedule data and resolves live `class_id` values.
4. Refreshes `X-Date` / `X-Token`.
5. Logs in shortly before booking open.
6. Warms the booking transport.
7. Sends booking requests using aggressive probe and focus-first batching.
8. Refreshes schedule state after submissions to confirm final status.
9. Sends Telegram notification output.

## Important Code Areas

- `TargetSpec`: parsed target model.
- `build_targets()`: config-to-target parsing.
- `is_target_active()`: active target logic, including `booking_run_date` and `skip_booking_run_dates`.
- `SiteClient`: Pure HTTP client for headers, login, schedule, booking, and final verification.
- `attempt_booking()`: booking request, early gate responses, waitlist fallback, relogin handling.
- `finalize_deferred_bookings()`: confirms final booked/waitlisted/failed result after batch submission.
- batch logic around `focus_first` and `parallel_book_all_submissions`: same-window performance logic.

## Current Timing Settings

Current local config uses:

- `aggressive_probe_enabled: true`
- `aggressive_probe_lead_ms: 200`
- `aggressive_probe_max_retries: 40`
- `aggressive_probe_retry_interval_ms: 15`
- `book_all_submission_strategy: "focus_first"`
- `focus_first_head_start_ms: 120`
- `parallel_book_all_submissions: true`
- `stop_after_first_priority_success: true`
- `continue_to_next_priority_on_waitlist: false`

Do not change these casually. Recent outcomes are good, and the remaining variability often appears to be Pure/backend queue time rather than local bot send timing.

## Current Config Notes

Current local targets include:

- Recurring Monday Fitness:
  - `Calisthenics Foundations` 12:00, Fitness - Ngee Ann City, Joshua Tay.
  - `Calisthenics Foundations` 18:30, Fitness - Ngee Ann City, Joshua Tay.
- Recurring Tuesday Yoga/Pilates:
  - `Reformer Signature` 10:00, Yoga - Ngee Ann City, Kelvin Teo.
- One-off 2026-05-14 booking run for 2026-05-19:
  - `Specialised: Wall Rope` 12:15, Dagge Ong, Yoga - Ngee Ann City.
  - `Specialised: Yogasthenics` 13:30, Wen Wen Chen, Yoga - Ngee Ann City.
  - `RPM™` 18:45, Ayu Astutik, Fitness - Asia Square Tower 1.
  - `BODYCOMBAT™` 17:45, House Chaalane, Fitness - Ngee Ann City.
- Recurring Saturday Yoga:
  - `Healing: Yoga Therapy` 12:30, Yoga - Ngee Ann City.
  - `Healing: Yin Yoga` 14:15, Yoga - Asia Square Tower 1.

Several expired one-off test targets remain in config. They should not activate because their `booking_run_date` is in the past, but they add reading noise.

## Performance Interpretation

Key metrics:

- warmup RTT: network/backend responsiveness before booking POST.
- focus send delta: actual spacing between focus and follower send.
- residual jitter: difference between configured spacing and actual spacing.
- booking RTT: total request/response time for each booking POST.
- queue proxy: booking RTT minus warmup RTT; rough signal for Pure/backend queue delay.
- response gap: difference between focus/follower response arrival.

Booked outcome matters, but timing analysis should compare side by side across days.

## Verification Commands

Local syntax check:

```bash
python3 -m py_compile pure_yoga_booking.py pure_yoga_admin.py
```

Local lookup for active run:

```bash
python3 pure_yoga_booking.py --config pure_yoga_config.json --lookup-only --list-classes
```

Local lookup for a specific class date:

```bash
python3 pure_yoga_booking.py --config pure_yoga_config.json --lookup-only --target-date 2026-05-19 --list-classes
```

Upload config:

```bash
scp "/Users/eileenmac/Documents/Yoga Booking Bot/pure_yoga_config.json" root@45.77.249.30:/root/PureYogaBot/pure_yoga_config.json
```

Verify server config timestamp:

```bash
ssh root@45.77.249.30 'stat -c "%y" /root/PureYogaBot/pure_yoga_config.json'
```

Tail server log:

```bash
ssh root@45.77.249.30 'cd /root/PureYogaBot && tail -n 150 logs/pure_booking_$(date +%Y%m%d).log'
```

## Product Must Protect

- Do not expose secrets.
- Do not remove timing instrumentation.
- Do not rewrite booking timing while a test window is in progress.
- Do not assume server config matches local config.
- Do not use important classes for stress tests.
- Do not let UI changes redefine matching, waitlist, priority, or batching behavior.

