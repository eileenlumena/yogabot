# Handoffs

Last updated: 2026-05-13

## Active Handoffs

1. Date: 2026-05-17
   From: Product / Booking Engine
   To: UI / Control Panel
   Request: Add Pure booking-limit warnings to the UI.
   Context: Pure limits members to 6 Yoga, 6 Pilates, and 6 Fitness bookings within a continuous 5-day period, plus a daily limit of 2 bookings per class type. A previous multi-class test likely failed because this kind of limit was exceeded.
   Required output: UI should classify planned targets by class type, warn before saving targets, and show warnings in Active Run Preview. Start as warnings, not hard blocks.
   Urgency: High for UI safety before relying on the control panel.
   Status: open.

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
