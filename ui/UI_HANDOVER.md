# UI / Control Panel Handover

Last updated: 2026-05-13

## 1. UI Files Already Exist

Current UI implementation:

- `pure_yoga_admin.py`
- `pure_yoga_config.dev.json` is the default UI test config at runtime. It is created from the live config if missing and is ignored by Git.

Supporting files the UI reads or calls:

- `pure_yoga_config.json`
- `pure_yoga_booking.py`

No separate frontend framework exists yet. The UI is a single Python file with:

- embedded HTML;
- embedded CSS;
- embedded JavaScript;
- local HTTP API endpoints;
- direct config-file read/write helpers.

There is no `templates/`, `static/`, React app, Streamlit app, database, or separate backend service.

## 2. What Is Already Working

The local UI can:

- run in a browser at `http://127.0.0.1:8501/`;
- show current targets from the selected UI config;
- add one-off booking targets;
- auto-generate Booking Run Date from Class Date by subtracting 5 days;
- add recurring targets;
- clear the one-off form;
- clear the recurring form;
- clear live class suggestions;
- search live Pure classes by selected date/site/location;
- search live Pure classes by typing at least 3 letters of a class name even without choosing a date;
- click `Use` on a live class suggestion to fill class date, booking run date, class name, start time, teacher, site, and location;
- run lookup-only checks by shelling out to `pure_yoga_booking.py`;
- clean expired one-off targets;
- show the manual `scp` upload command.

## 3. What Is Incomplete Or Broken

Known gaps:

- The UI does not edit existing targets.
- The UI does not delete or disable individual targets.
- The UI does not manage `skip_booking_run_dates`.
- The UI does not warn clearly about duplicate targets.
- The UI does not show whether local config has been uploaded to the server.
- The UI does not verify server config timestamp or content.
- The UI does not show active targets for a chosen booking run date in a clean preview.
- The UI does not protect against accidental creation of too many one-off test targets.
- Search is limited to the selected site and selected location. It does not search every location/site at once.
- Live search depends on network access to Pure.
- There are no browser automation tests.
- There is no authentication; it is intended for local use only.
- The UI still displays a live server upload command. This is intentional caution text now, but the UI should eventually make dev-vs-live mode more visually obvious.

Potential UX issue:

- Some Pure class names contain symbols such as `™`. The UI and JSON can handle them, but the UI thread should be careful not to strip or silently alter official Pure names.

## 4. How The UI Connects To Booking Bot / Config

The UI has local paths:

- `LIVE_CONFIG_PATH = BASE_DIR / "pure_yoga_config.json"`
- `CONFIG_PATH = BASE_DIR / "pure_yoga_config.dev.json"` by default
- `BOT_PATH = BASE_DIR / "pure_yoga_booking.py"`

The UI can be pointed at another config with:

```bash
python3 pure_yoga_admin.py --config some_config.json
```

Do not use `--config pure_yoga_config.json` for UI testing unless Product explicitly wants to edit the live local booking config.

Config flow:

- `load_config()` reads `pure_yoga_config.json`.
- `save_config()` writes `pure_yoga_config.json`.
- `/api/config` returns a safe subset of config fields and does not return credentials or Telegram settings.
- `/api/add-oneoff` validates the payload and appends a target to `config["targets"]`.
- `/api/add-recurring` validates the payload and appends a target to `config["targets"]`.
- `/api/clean-expired` removes one-off targets with past `booking_run_date`.

Live schedule flow:

- `/api/classes` imports `pure_yoga_booking`.
- It constructs `PureYogaBot` and `SiteClient`.
- It bootstraps headers and fetches Pure schedule data.
- It returns matching class rows to the browser.

Lookup flow:

- `/api/lookup` runs:

```bash
python3 pure_yoga_booking.py --config pure_yoga_config.json --lookup-only
```

with optional:

```bash
--target-date YYYY-MM-DD --list-classes
```

## 5. How To Run The UI Locally

From the project folder:

```bash
cd "/Users/eileenmac/Documents/Yoga Booking Bot"
python3 pure_yoga_admin.py --host 127.0.0.1 --port 8501
```

Open:

```text
http://127.0.0.1:8501/
```

If the browser says connection refused, the server is not running or another process stopped.

Default mode writes to:

```text
pure_yoga_config.dev.json
```

not the live booking config.

## 6. Commands / Tests That Verify It

Syntax check:

```bash
python3 -m py_compile pure_yoga_admin.py pure_yoga_booking.py
```

Config JSON check:

```bash
python3 -m json.tool pure_yoga_config.json
python3 -m json.tool pure_yoga_config.dev.json
```

Start UI:

```bash
python3 pure_yoga_admin.py --host 127.0.0.1 --port 8501
```

API config check:

```bash
curl -sS http://127.0.0.1:8501/api/config
```

Live class search with date:

```bash
curl -sS -X POST http://127.0.0.1:8501/api/classes \
  -H 'Content-Type: application/json' \
  -d '{"target_date":"2026-05-19","site":"yoga","location_id":19,"query":"Wall Rope"}'
```

Live class search without date:

```bash
curl -sS -X POST http://127.0.0.1:8501/api/classes \
  -H 'Content-Type: application/json' \
  -d '{"target_date":"","site":"yoga","location_id":19,"query":"reformer"}'
```

Booking engine lookup through UI-equivalent command:

```bash
python3 pure_yoga_booking.py --config pure_yoga_config.json --lookup-only --target-date 2026-05-19 --list-classes
```

## 7. Next 3 UI Tasks

1. Add an Active Run Preview.
   - User chooses a booking run date or class date.
   - UI shows exactly which targets will run.
   - Include warnings for expired one-offs, duplicates, and cross-site runs.

2. Add target edit/delete/disable controls.
   - Edit existing targets safely.
   - Disable instead of deleting where appropriate.
   - Delete expired one-offs only after confirmation.

3. Add server sync visibility.
   - Show local config modified time.
   - Show server config modified time if SSH check is available.
   - Provide clear upload and verify commands.
   - Do not auto-upload unless Product approves.

## 8. What The UI Thread Must Not Change Without Product Approval

Do not change:

- `pure_yoga_booking.py` booking timing behavior;
- aggressive probe settings;
- focus-first batching behavior;
- priority semantics;
- `book_all` vs `priority` semantics;
- waitlist fallback behavior;
- final schedule verification;
- teacher matching policy;
- Telegram notification semantics;
- server cron or deployment behavior;
- config schema fields used by the booking engine;
- credentials, Telegram tokens, or any secret-handling design.

The UI may propose Product changes, but must not implement them directly without approval.
