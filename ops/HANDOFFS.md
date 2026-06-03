# Handoffs

Last updated: 2026-06-03

## Active Handoffs

1. Date: 2026-05-17
   From: Product / Booking Engine
   To: UI / Control Panel
   Request: Add Pure booking-limit warnings to the UI.
   Context: Pure limits members to 6 Yoga, 6 Pilates, and 6 Fitness bookings within a continuous 5-day period, plus a daily limit of 2 bookings per class type. A previous multi-class test likely failed because this kind of limit was exceeded.
   Required output: UI should classify planned targets by class type, warn before saving targets, and show warnings in Active Run Preview. Start as warnings, not hard blocks.
   Urgency: High for UI safety before relying on the control panel.
   Status: resolved by Product on 2026-06-02. Uploaded `pure_yoga_booking.py` to DigitalOcean and verified server-side `py_compile` plus presence of `format_display_datetime`.

2. Date: 2026-05-18
   From: Product / Booking Engine
   To: Product / Booking Engine
   Request: Investigate Pure existing-bookings/account-bookings endpoint before adding manual booking counts to Telegram/UI limit warnings.
   Context: Telegram pre-run warnings currently count planned config targets only. Existing manual bookings would make limit warnings more accurate, but extra account calls should not disturb the booking session near 9am.
   Required output: Identify a safe endpoint and timing strategy, or document that the feature should wait.
   Urgency: Medium.
   Status: resolved by Product on 2026-05-18. Safe read-only endpoint identified as `GET /api/v3/get_booking_history`; booking engine now fetches it before pre-run warning calculation and continues with config-only warnings if the fetch fails.

3. Date: 2026-05-23
   From: Product / Booking Engine
   To: UI / Control Panel
   Request: Add a "Skip this run" control for active scheduled bot targets.
   Context: Eileen may see an evening or morning warning that a teacher changed, a class is missing, or a booking-limit issue exists. She needs a fast way to stop the bot from attempting one target in the next booking run without deleting the permanent recurring target.
   Required output: In Active Run Preview, show a per-target "Skip this run" action. For recurring targets, add the target's booking run date to `skip_booking_run_dates`. For one-off targets, remove the one-off target or mark it inactive for that run. The UI should label skipped targets clearly and allow undo before saving. Avoid the word "cancel" because this does not cancel an already-booked Pure class; it only prevents the bot from attempting a future booking.
   Urgency: High for morning/evening warning workflow.
   Status: implemented by UI on 2026-05-23; browser verified against dev config.

4. Date: 2026-05-30
   From: Product / Booking Engine
   To: UI / Control Panel
   Request: Treat the future phone experience as a mobile-first web UI / PWA option before considering a native app.
   Context: Eileen asked whether the bot could become an internal phone app for personal use and close friends without App Store distribution. Product recommendation is to build this as a password-protected mobile web app / Progressive Web App first. Users can open the web UI in Safari/Chrome and use "Add to Home Screen" to get a phone icon; updates stay server-side, and Telegram remains the notification channel.
   Required output: UI thread should consider responsive/mobile-first layouts and PWA readiness for the control panel roadmap. Expected workflows include view upcoming booking schedule, add one-off target, add recurring target, edit/disable target, skip this run, view warnings/results, run lookup/test notification, and eventually sync with the DigitalOcean bot server. Do not prioritize native iOS/TestFlight unless PWA proves insufficient.
   Urgency: Medium. This is roadmap/product direction, not blocking current booking engine work.
   Status: open.

5. Date: 2026-06-02
   From: UI / Control Panel
   To: Product / Booking Engine
   Request: Upload updated booking engine after confirmation-message date formatting change.
   Context: The UI thread accidentally handled a Product-owned formatting request and changed local `pure_yoga_booking.py` so booking confirmation rows use the warning-style date/time format, e.g. `Sat 6 Jun 2026 13:00`.
   Required output: Product should review and upload the changed booking engine to the current DigitalOcean bot server, then verify the deployed file. UI should not perform the server upload.
   Urgency: Medium; needed before live Telegram booking confirmations reflect the new format.
   Status: resolved by Product on 2026-06-03. Uploaded `pure_yoga_booking.py` to DigitalOcean, verified server-side `py_compile`, and confirmed live booking summaries now use display date/time formatting.

6. Date: 2026-06-03
   From: Product / Booking Engine
   To: Product / Booking Engine
   Request: Continue Product work in a fresh thread using the new detailed handover.
   Context: The current Product thread is compacting. Product created a fresh handover covering DigitalOcean cron, current recurring targets, recent booking engine changes, automated performance reports, deployment commands, dirty repo state, and risks.
   Required output: New Product thread should read `PRODUCT_THREAD_HANDOVER_2026-06-03.md`, inspect the repo/server, summarize understanding, and not code until after summarizing.
   Urgency: High for context continuity.
   Status: open until new Product thread confirms the handover.

## Protocol

- Use this file when Product / Booking Engine needs UI / Control Panel to do or answer something.
- Use this file when UI / Control Panel needs Product / Booking Engine to do or answer something.
- Each handoff should include:
  - date;
  - from thread;
  - to thread;
  - request;
  - context;
  - required output;
  - urgency;
  - status.

## Template

```text
Date:
From:
To:
Request:
Context:
Required output:
Urgency:
Status:
```
