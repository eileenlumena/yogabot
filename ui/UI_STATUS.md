# UI / Control Panel Status

Last updated: 2026-05-30

## Current State

The UI is halfway built and usable locally. It is not production-grade yet.

Product direction as of 2026-05-30: the future phone experience should be a mobile-first web UI / Progressive Web App before considering a native app. Users can open the hosted control panel in a mobile browser and use "Add to Home Screen" for phone-icon access. This keeps distribution internal and avoids App Store/TestFlight complexity for now.

Working:

- Local browser UI at `http://127.0.0.1:8501/`.
- Default UI save path is now `pure_yoga_config.dev.json`, so UI testing does not affect the live booking config.
- Four-tab layout: Targets, Active run, Add target, Search classes.
- Targets tab with All / Recurring / One-off filters.
- Active Run Preview by booking run date.
- Per-target `Skip this run` staging with Undo before save.
- Saving skipped recurring targets appends the run date to `skip_booking_run_dates`.
- Saving skipped one-off targets removes the one-off target from the dev config.
- Current target table on desktop with inline delete-on-hover.
- Mobile Current Targets card view below 560px.
- Add target tab with segmented One-off / Recurring forms.
- Auto Booking Run Date from Class Date.
- Clear buttons for one-off form, recurring form, and suggestions.
- Search classes tab with live class search results shown inline.
- Saved-target date lookup results shown inline.
- Live class suggestions from Pure.
- Partial class-name search without selecting class date first.
- `Use` button fills selected live class details.
- Lookup-only command integration.
- Collapsible output log on Targets tab.
- Expired one-off cleanup with browser confirmation.
- Dev-config target delete endpoint and browser-confirmed delete buttons.

Incomplete:

- No edit/disable per target.
- No general skip-date editor outside Active Run Preview.
- No server sync status.
- No duplicate detection.
- No automated browser tests.
- No UI-level protection around important classes vs test classes.
- No booking-limit warning yet for Pure's 6-per-5-day and 2-per-day class-type limits.
- No PWA install metadata / app manifest yet.
- No hosted password-protected mobile deployment yet.
- No DigitalOcean server sync workflow yet.

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

Mobile viewport check:

- Verified 390px wide mobile viewport with the Codex in-app browser against `http://127.0.0.1:8501/`.
- Current Targets switches from the desktop table to stacked cards.
- Targets filters, tab navigation, and action buttons remain usable on mobile.
- Search tab stacks the live-search and saved-target lookup sections vertically.
- Saved-target date lookup writes visible inline output instead of only writing to the old shared Output area.

## Main Risk

The UI no longer writes to the real local config by default. The remaining risk is accidentally running it with `--config pure_yoga_config.json` or manually copying dev config into live config without review.
