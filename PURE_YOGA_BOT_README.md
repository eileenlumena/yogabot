# Pure Booking Bot

This bot now supports recurring Pure Yoga, Pilates, and Pure Fitness targets in one config.

It works by:

1. Pulling `X-Date` and `X-Token` from the Pure web page.
2. Looking up the active target `class_id` values from `view_schedule`.
3. Handling teacher replacement with a configurable teacher policy.
4. Logging in right before the booking window opens.
5. Posting to `/booking` at the configured opening time.
6. Falling back to the waitlist with `book_type=2` if the server returns `409` ("class is full").

## Files

- `pure_yoga_booking.py`: main bot
- `pure_yoga_config.example.json`: sample config
- `logs/`: runtime logs

## Setup

1. Copy `pure_yoga_config.example.json` to `pure_yoga_config.json`.
2. Fill in:
   - `credentials.username`
   - `credentials.password`
   - each item in `targets`
3. Install dependencies if needed:

```bash
pip install requests
```

On some Windows Python installs, `tzdata` is also needed for `Asia/Singapore` timezone support. The included `requirements.txt` now installs both:

```bash
pip install -r requirements.txt
```

## Useful commands

Check the active targets for the rolling daily date without logging in:

```bash
python pure_yoga_booking.py --config pure_yoga_config.json --lookup-only --list-classes
```

Test a specific date:

```bash
python pure_yoga_booking.py --config pure_yoga_config.json --lookup-only --target-date 2026-04-06 --list-classes
```

Test login and timing logic without sending the booking request:

```bash
python pure_yoga_booking.py --config pure_yoga_config.json --dry-run
```

Run the real booking flow:

```bash
python pure_yoga_booking.py --config pure_yoga_config.json
```

## Scheduling on the VPS

The script uses `Asia/Singapore` internally, so it calculates the booking window correctly even if the VPS is in another timezone.

If your Windows VPS stays on Japan Standard Time, Singapore 9:00 AM is 10:00 AM JST. A practical Task Scheduler start time is a few minutes before that. The bot itself uses `wake_seconds_before` to decide when it refreshes headers and logs in. The current tuned defaults wake 20 seconds before the opening second and use a tighter retry loop for `426/428` responses right around 9:00 AM.

A simple Windows install location is `C:\Users\Administrator\PureYogaBot`. If you use that folder, you can point Task Scheduler directly at `python` with:

```bat
"C:\Users\Administrator\PureYogaBot\pure_yoga_booking.py" --config "C:\Users\Administrator\PureYogaBot\pure_yoga_config.json"
```

If the VPS reports `No module named 'tzdata'` or `No time zone found with key Asia/Singapore`, rerun:

```bat
python -m pip install -r requirements.txt
```

## Notes

- `targets` is the main recurring config. Each target can be tagged as `yoga` or `fitness`.
- Pilates classes on the Pure Yoga site should use `site: "yoga"`.
- `booking_run_date` is optional for one-off targets. If set, that target only becomes active on that booking day in Singapore time.
- `teacher_policy: "prefer_named_teacher"` means:
  - book the named teacher if present
  - if that teacher is replaced, still book the same class/time/location with the replacement teacher
  - if the class disappears completely, the bot logs `NO_MATCH` and does not send a booking request
- `mode: "priority"` means lower-priority targets are fallback options. By default the bot stops after the first priority target that is successfully booked, but it will continue to the next priority target if the higher-priority one only lands on the waitlist.
- `mode: "book_all"` means the bot attempts that target whenever it is active for the date. If multiple `book_all` targets are active on the same day, they are attempted in ascending `priority` order.
- Waitlist fallback uses the same `/booking` endpoint as a normal booking, but sends `book_type=2`.
- If the VPS has certificate issues, set `runtime.verify_ssl` to `false`.
