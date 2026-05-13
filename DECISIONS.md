# Decisions

Last updated: 2026-05-13

## Thread Split

- Product / Booking Engine remains responsible for booking correctness, speed, matching rules, server behavior, and performance analysis.
- UI / Control Panel is a separate thread responsible for making target editing easier and safer.
- The UI thread must prepare handovers/status updates instead of changing booking-engine behavior directly.

## Booking Engine Decisions

- Keep `book_all` as the default mode for active targets unless Product explicitly changes the strategy.
- Keep focus-first batching for same-site multi-class runs.
- Keep `aggressive_probe_lead_ms` at `200` unless Product decides to run another timing experiment.
- Keep `focus_first_head_start_ms` at `120` unless Product decides otherwise.
- Keep post-booking schedule verification because Pure can return a generic success response while the real result is booked, waitlisted, or failed.
- Keep teacher policy as `prefer_named_teacher` for normal use:
  - match named teacher if available;
  - if the exact teacher is replaced but the same class/time/location exists, allow fallback to the replacement teacher.
- Treat `booking_run_date` one-offs as temporary; expired one-offs can remain in config but should not be treated as active.
- Use live lookup before important bookings where possible, because Pure can change names, teachers, times, and class availability.

## UI Decisions

- The UI is currently a dependency-light local Python HTTP server, not a separate web framework.
- The UI writes directly to `pure_yoga_config.json`.
- The UI should not store, display, or edit credentials or Telegram tokens unless Product approves a security design.
- Booking Run Date is derived from Class Date at 5 days before the class date.
- Live class search can work with class date selected or with only a partial class name typed.
- Recurring targets are supported, but recurring target editing/deleting is still incomplete.

## Operational Decisions

- Server config uploads are manual for now using `scp`.
- Always verify server config after uploading if the next run matters.
- Do not assume the server has the latest local config.
- For important classes, avoid using them as multi-booking stress tests.
- The project can use Git/GitHub, but GitHub must be private and the live `pure_yoga_config.json` must stay untracked.
- Commit the sanitized `pure_yoga_config.example.json`, not the live config with credentials and Telegram secrets.
- Commit to GitHub manually at meaningful checkpoints, not after every chat message.
- Commit code/docs/config-example changes after they are verified or after an important handover/status update.
- Do not commit live local-only files such as `pure_yoga_config.json`, logs, caches, bundles, or generated assets.

## Communication Protocol

- Threads must not rely on chat memory to coordinate.
- Each thread must update its own status file before ending work.
- Product / Booking Engine status lives in `product/PRODUCT_STATUS.md`.
- UI / Control Panel status lives in `ui/UI_STATUS.md`.
- Cross-thread requests, blockers, or answers must be written in `ops/HANDOFFS.md` and mentioned in the relevant status file.
- User decisions or reviews must be written in `ops/CEO_ACTION_QUEUE.md`.
- User next steps must be kept current in `ops/NEXT_ACTIONS.md`.
- Changes to future direction or constraints must be recorded in `DECISIONS.md`.
