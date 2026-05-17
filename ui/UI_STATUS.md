# UI / Control Panel Status

Last updated: 2026-05-13

## Current State

The UI is halfway built and usable locally. It is not production-grade yet.

Working:

- Local browser UI at `http://127.0.0.1:8501/`.
- Default UI save path is now `pure_yoga_config.dev.json`, so UI testing does not affect the live booking config.
- Current target table.
- One-off target creation.
- Recurring target creation.
- Auto Booking Run Date from Class Date.
- Clear buttons for one-off form, recurring form, and suggestions.
- Live class suggestions from Pure.
- Partial class-name search without selecting class date first.
- `Use` button fills selected live class details.
- Lookup-only command integration.
- Expired one-off cleanup.
- Upload command display.

Incomplete:

- No edit/delete/disable per target.
- No skip-date editor.
- No server sync status.
- No duplicate detection.
- No clean active-run preview.
- No automated browser tests.
- No UI-level protection around important classes vs test classes.
- No booking-limit warning yet for Pure's 6-per-5-day and 2-per-day class-type limits.

## Current Run Command

```bash
cd "/Users/eileenmac/Documents/Yoga Booking Bot"
python3 pure_yoga_admin.py --host 127.0.0.1 --port 8501
```

This defaults to dev config mode. Live config editing requires an explicit `--config pure_yoga_config.json` and should not be used for UI testing.

## Current Verification

```bash
python3 -m py_compile pure_yoga_admin.py pure_yoga_booking.py
python3 -m json.tool pure_yoga_config.json
```

## Main Risk

The UI no longer writes to the real local config by default. The remaining risk is accidentally running it with `--config pure_yoga_config.json` or manually copying dev config into live config without review.
