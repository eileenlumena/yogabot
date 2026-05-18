# Handoffs

Last updated: 2026-05-18

## Active Handoffs

1. Date: 2026-05-17
   From: Product / Booking Engine
   To: UI / Control Panel
   Request: Add Pure booking-limit warnings to the UI.
   Context: Pure limits members to 6 Yoga, 6 Pilates, and 6 Fitness bookings within a continuous 5-day period, plus a daily limit of 2 bookings per class type. A previous multi-class test likely failed because this kind of limit was exceeded.
   Required output: UI should classify planned targets by class type, warn before saving targets, and show warnings in Active Run Preview. Start as warnings, not hard blocks.
   Urgency: High for UI safety before relying on the control panel.
   Status: open.

2. Date: 2026-05-18
   From: Product / Booking Engine
   To: Product / Booking Engine
   Request: Investigate Pure existing-bookings/account-bookings endpoint before adding manual booking counts to Telegram/UI limit warnings.
   Context: Telegram pre-run warnings currently count planned config targets only. Existing manual bookings would make limit warnings more accurate, but extra account calls should not disturb the booking session near 9am.
   Required output: Identify a safe endpoint and timing strategy, or document that the feature should wait.
   Urgency: Medium.
   Status: resolved by Product on 2026-05-18. Safe read-only endpoint identified as `GET /api/v3/get_booking_history`; booking engine now fetches it before pre-run warning calculation and continues with config-only warnings if the fetch fails.

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
