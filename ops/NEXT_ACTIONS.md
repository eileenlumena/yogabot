# Next Actions

Last updated: 2026-05-18

## For Eileen

1. Upload the updated booking engine to the SG server before relying on the latest Telegram pre-run warnings there.

```bash
scp "/Users/eileenmac/Documents/Yoga Booking Bot/pure_yoga_booking.py" root@45.77.249.30:/root/PureYogaBot/pure_yoga_booking.py
```

2. If any future Fitness class is highly important at the 9:00 edge, decide whether to avoid mixing Yoga and Fitness in the same run because current multi-site behavior books the second site only after the first site finishes.

3. Watch the next Telegram pre-run warning, if any, to confirm it makes sense with the current My Bookings page.

4. Continue comparing future runs side by side, not as single-day metrics.

## For Product / Booking Engine

1. Before ending future work, update `product/PRODUCT_STATUS.md`.
2. If UI needs to act, write the handoff in `ops/HANDOFFS.md` and mention it in `product/PRODUCT_STATUS.md`.
3. If Eileen needs to decide something, add it to `ops/CEO_ACTION_QUEUE.md`.
4. Commit and push meaningful verified code/docs changes to GitHub before ending substantial work.

## For UI / Control Panel

1. Before ending future work, update `ui/UI_STATUS.md`.
2. If Product needs to act, write the handoff in `ops/HANDOFFS.md` and mention it in `ui/UI_STATUS.md`.
3. Keep UI work within `ui/UI_HANDOVER.md` and `ui/UI_SPEC.md` unless Product approves behavior changes.
4. Commit and push meaningful verified UI/docs changes to GitHub before ending substantial work.
