# Pure Booking Bot Project Brief

Last updated: 2026-05-13

## Purpose

Automate Pure Yoga, Pilates, and Pure Fitness Singapore bookings at the 5-days-ahead opening window, while keeping enough timing instrumentation to understand performance rather than judging only by final booked/waitlisted outcomes.

The project is now split into two working threads:

1. Product / Booking Engine
   - Owns `pure_yoga_booking.py`, booking strategy, timing, matching, waitlist handling, Telegram notifications, server deployment, and performance analysis.
2. UI / Control Panel
   - Owns `pure_yoga_admin.py` and the local control panel used to edit booking targets in `pure_yoga_config.json`.

## Current Files

- `pure_yoga_booking.py`: main booking engine.
- `pure_yoga_admin.py`: local browser control panel.
- `pure_yoga_config.json`: live local config with credentials, targets, booking settings, and Telegram settings.
- `pure_yoga_config.example.json`: sample config.
- `requirements.txt`: Python dependencies.
- `logs/`: local booking and lookup logs.
- `PURE_YOGA_BOT_README.md`, `PURE_YOGA_BOT_HANDOVER.md`, `PURE_YOGA_BOT_CODEX_THREAD_HANDOVER_2026-05-02.md`: older project docs retained for reference.
- `product/`: Product / Booking Engine handover and status.
- `ui/`: UI / Control Panel handover, status, and spec.

## Deployment

Current server target:

```bash
root@45.77.249.30:/root/PureYogaBot/
```

Common upload commands:

```bash
scp "/Users/eileenmac/Documents/Yoga Booking Bot/pure_yoga_config.json" root@45.77.249.30:/root/PureYogaBot/pure_yoga_config.json
scp "/Users/eileenmac/Documents/Yoga Booking Bot/pure_yoga_booking.py" root@45.77.249.30:/root/PureYogaBot/pure_yoga_booking.py
```

Do not expose credentials, Telegram tokens, cookies, captured headers, or Pure session values in docs or chat.

