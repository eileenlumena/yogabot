# Pure Yoga / Pure Fitness Booking Bot Handover

Last updated: 2026-04-12

## 1. What This Bot Does

This bot automates recurring class booking on the Singapore Pure web properties:

- Pure Yoga / Pilates via `https://pure360.pure-yoga.com/en/SG`
- Pure Fitness via `https://pure360.pure-fitness.com/en/SG`

It supports:

- recurring targets
- one-off test targets
- Yoga, Pilates, and Fitness targets in one config
- teacher replacement handling
- Telegram result notifications
- booking and waitlist handling
- Windows VPS scheduled execution

The current main implementation lives in:

- `/Users/eileenmac/Documents/Yoga Booking Bot/pure_yoga_booking.py`
- `/Users/eileenmac/Documents/Yoga Booking Bot/pure_yoga_config.json`

## 2. How It Works

The booking flow is:

1. Open the Pure web page for the relevant site and location(s).
2. Extract `X-Date` and `X-Token` from the page meta tags.
3. Call `view_location` and `view_schedule`.
4. Resolve the live `class_id` for the specific class/date/time/location/teacher.
5. Refresh headers and log in shortly before the opening time.
6. Start booking attempts near 9:00 AM Singapore time.
7. Submit a booking POST to `/booking`.
8. Refresh schedule state after submission to determine whether the final result is:
   - `BOOKED`
   - `WAITLISTED`
   - `FAILED`

Important implementation details:

- `class_id` is dynamic and changes every session. It is never hardcoded long-term.
- Teacher matching supports fallback when the named teacher is replaced.
- `booking_run_date` makes one-off tests auto-expire after the intended booking day.
- Telegram notifications are sent from the bot itself after each live run.

## 3. Current Architecture / Key Logic

Key code areas:

- `SiteClient` handles HTTP requests, header bootstrap, login, booking, and schedule refreshes.
- `PureYogaBot` handles config parsing, target activation, timing, batching, logging, and notifications.

Current timing and retry features:

- timezone calibration against the Pure page `timestamp`
- millisecond log timestamps
- pre-open login retry
- aggressive probe mode
- focus-first submission strategy
- waitlist verification from refreshed schedule

Current important logic in `pure_yoga_booking.py`:

- `bootstrap_and_login`: retries header refresh + login if the pre-book login step fails
- `attempt_booking`: handles booking, waitlist fallback, `426/428` retry, and `401` re-login
- `finalize_deferred_bookings`: confirms final states after batched submissions
- focus class logging for multi-target same-window runs

## 4. Current Deployment Setup

Windows VPS path:

- `C:\Users\Administrator\PureYogaBot`

Expected files on VPS:

- `pure_yoga_booking.py`
- `pure_yoga_config.json`
- `requirements.txt`
- `run_pure_booking.bat`

Scheduler:

- Windows Task Scheduler
- daily trigger
- Japan VPS time: `09:58 AM JST`
- bot internally uses `Asia/Singapore`

Important launcher file:

- `run_pure_booking.bat`

This was important because the scheduled task originally failed silently when the batch file used bare `python`. The fix was to call the full Python path explicitly.

## 5. Current Config State

### Recurring targets still intended for long-term use

- Mon: `Calisthenics Foundations` 12:00, Fitness - Ngee Ann City, priority 1
- Mon: `Calisthenics Foundations` 18:30, Fitness - Ngee Ann City, priority 2
- Tue: `Reformer Signature` 10:00, Yoga - Ngee Ann City
- Fri: `Mat: Classical Pilates` 11:15, Yoga - Ngee Ann City, priority 1
- Sat: `Healing: Yoga Therapy` 12:30, Yoga - Ngee Ann City, priority 1
- Sat: `Healing: Yin Yoga` 14:15, Yoga - Asia Square Tower 1, priority 2

### One-off test targets currently still present in config

These remain in the config file but are controlled by `booking_run_date`, so they do not keep firing after their intended test day:

- 2026-04-07 run for 2026-04-12:
  - `Grounding: Yin-Yang`
  - `Specialised: Foundation Wall Rope Yoga`
- 2026-04-09 run for 2026-04-14:
  - `Specialised: Wall Rope` 12:15
- 2026-04-10 run for 2026-04-15:
  - `Dynamic: Vinyasa`
  - `Specialised: Wall Rope` 13:30
- 2026-04-11 run for 2026-04-16:
  - `Elevate: Chair & Wall Rope`
  - `Specialised: Upside Down`
- 2026-04-12 run for 2026-04-17:
  - `Specialised: Wall Rope` 12:30

Cleanup is recommended once testing is finished.

### Current booking strategy in config

Current booking settings in `pure_yoga_config.json`:

- `aggressive_probe_enabled: true`
- `aggressive_probe_lead_ms: 200`
- `aggressive_probe_max_retries: 40`
- `aggressive_probe_retry_interval_ms: 15`
- `book_all_submission_strategy: "focus_first"`
- `focus_first_head_start_ms: 120`
- `continue_to_next_priority_on_waitlist: false`

Current behavioral meaning:

- for priority windows, the priority 1 class is the must-win class
- if that class is `BOOKED` or `WAITLISTED`, lower-priority classes are skipped
- for same-window `book_all` windows, the focus class is the lowest-priority-number target

## 6. Main Problems Encountered and Fixes Applied

### A. Windows timezone issue

Problem:

- VPS Python could not resolve `Asia/Singapore`
- error: `No module named 'tzdata'` / `No time zone found with key Asia/Singapore`

Fix:

- added `tzdata` to `requirements.txt`
- added fixed-offset fallback handling in code

### B. Scheduler did not run automatically

Problem:

- scheduled task produced no fresh logs
- Task Scheduler was pointing at a batch file that depended on bare `python`

Fix:

- updated `run_pure_booking.bat` to use the full Python path

### C. Successful response was misreported as booked

Problem:

- Pure could return a generic `200 Success`
- the actual account state after refresh could be `IN_WAITLIST`
- initial implementation sometimes reported `BOOKED` when the real outcome was waitlist

Fix:

- added post-book schedule verification
- final status is now resolved from refreshed schedule state

### D. Same-window second class was delayed

Problem:

- second target in the same booking window was losing time because verification for the first class happened before the second submission

Fix:

- changed flow to defer verification until after submissions
- later added parallel submission for same-window `book_all`

### E. Need for better timing diagnostics

Problem:

- relative timestamps were not enough to reason about 9:00 AM behavior

Fix:

- added millisecond log timestamps
- added request timing logs
- added calibrated server offset logging

### F. Pre-book login could fail once and kill the run

Problem:

- no retry path around header refresh + login

Fix:

- added `bootstrap_and_login` retry helper

### G. Still losing competitive classes

Problem:

- even after parallelization, the first class in very competitive windows still waitlisted

Fixes attempted:

- aggressive probe mode
- focus-first submission strategy
- priority-window mode with `continue_to_next_priority_on_waitlist: false`

## 7. Performance / Tuning Timeline

### 2026-04-08

Fitness Monday pair:

- first booking sent at about `09:00:00.043`
- second booking was effectively delayed behind the first response
- both waitlisted

Conclusion:

- internal sequencing delay was still a real problem

### 2026-04-09

Yoga Tuesday pair after parallelization:

- both requests sent at `09:00:00.022`
- both waitlisted

Conclusion:

- sequencing improved
- remaining bottleneck moved closer to network/server race

### 2026-04-10

Yoga Wednesday pair after aggressive probe:

- both requests sent at `08:59:59.887`
- one booked, one waitlisted

Conclusion:

- meaningful timing improvement from aggressive probe

### 2026-04-11

Yoga Thursday pair after focus-first mode:

- focus class sent at `08:59:59.807`
- second class sent at `08:59:59.928`
- both booked

Conclusion:

- another measurable send-time improvement
- outcome may also have been helped by lower class competitiveness

### 2026-04-12

Yoga Friday pair:

- focus class sent at `08:59:59.807`
- second class sent at `08:59:59.928`
- both waitlisted (`#19` and `#11`)

Conclusion:

- no evidence of bot slowdown versus 2026-04-11
- this strongly suggests demand/capacity was the dominant factor

## 8. What We Learned

Strong conclusions:

- the bot is no longer obviously slow because of internal sequencing
- focus-first and aggressive probe improved send timing
- some classes are still so competitive that even an early, parallel, pre-open-tuned bot loses

Likely true but not fully proven:

- Japan VPS latency is now a bigger bottleneck than Python execution overhead
- a Singapore VPS might help by tens of milliseconds, but is unlikely to turn `WAITLIST #19` into guaranteed booking by itself

## 9. Current Limitations

- Pure’s private web API is reverse-engineered and may change without notice
- the bot depends on page meta extraction for `X-Date` / `X-Token`
- booking results still depend on server-side capacity and queueing
- no cancellation support is implemented
- no built-in A/B benchmarking across multiple VPS regions
- config currently contains both recurring targets and expired one-off test targets
- secrets currently live in `pure_yoga_config.json`

## 10. Known Operational Risks

- if Pure changes:
  - endpoint shape
  - JWT behavior
  - page token meta tags
  - button status semantics
  the bot may break

- if the Windows VPS changes Python path, Task Scheduler can fail again
- if Telegram token or credentials are exposed, they should be rotated

## 11. Recommended Next Steps

### Short-term

- remove expired one-off test targets from `pure_yoga_config.json`
- decide which recurring windows should stay `priority` versus `book_all`
- keep focus-first + aggressive probe enabled for ultra-competitive classes

### If trying to improve competitive-class hit rate further

- test a Singapore VPS for a short period only
- compare send timing and outcome on the same class pattern
- do not expect a miracle; likely improvement is in tens of milliseconds, not hundreds

### If simplifying the system

- split recurring production config and one-off test config into separate files
- keep a clean long-term production config on the VPS
- use a separate temp config for experiments

## 12. Suggested Cleanup After Testing

Recommended cleanup task:

1. Remove expired one-off targets from `pure_yoga_config.json`
2. Keep only recurring targets in the main config
3. Optionally create:
   - `pure_yoga_config.production.json`
   - `pure_yoga_config.testing.json`

## 13. Useful Commands

Lookup only:

```bash
python pure_yoga_booking.py --config pure_yoga_config.json --lookup-only
```

Lookup specific date:

```bash
python pure_yoga_booking.py --config pure_yoga_config.json --lookup-only --target-date 2026-04-17
```

Dry run:

```bash
python pure_yoga_booking.py --config pure_yoga_config.json --dry-run
```

Real run:

```bash
python pure_yoga_booking.py --config pure_yoga_config.json
```

## 14. Bottom-Line Status

The bot is functional, deployed, and materially optimized compared with the initial version.

The remaining problem is not “the bot does nothing” or “the bot is obviously late.” The remaining problem is that some Pure classes are so competitive that even a tuned bot on a Japan VPS still lands in waitlist.

The most sensible next move is configuration cleanup plus optional short-term Singapore VPS testing, not another large rewrite.
