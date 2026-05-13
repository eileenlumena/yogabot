# UI / Control Panel Status

Last updated: 2026-05-13

## Current State

The UI is halfway built and usable locally. It is not production-grade yet.

Working:

- Local browser UI at `http://127.0.0.1:8501/`.
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

## Current Run Command

```bash
cd "/Users/eileenmac/Documents/Yoga Booking Bot"
python3 pure_yoga_admin.py --host 127.0.0.1 --port 8501
```

## Current Verification

```bash
python3 -m py_compile pure_yoga_admin.py pure_yoga_booking.py
python3 -m json.tool pure_yoga_config.json
```

## Main Risk

The UI writes directly to the real local config. A bad UI save can alter tomorrow's booking behavior. Until edit/preview/duplicate protection is added, verify active targets before upload.

