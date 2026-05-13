# Roadmap

Last updated: 2026-05-13

## Product / Booking Engine

1. Continue observing live booking performance before further timing changes.
2. Compare multi-class runs side by side using focus send time, follower send time, residual jitter, warmup RTT, booking RTT, and queue proxy.
3. Run a controlled multi-booking test on less-important classes:
   - fewer than Pure's possible advance-booking limit;
   - 3 or more classes on the same site first;
   - only mix Yoga/Fitness if deliberately testing cross-site behavior.
4. Clean old one-off targets after they are no longer useful.
5. Decide final permanent recurring class list and priorities.

## UI / Control Panel

1. Make search and target creation safer:
   - clearer search state;
   - no duplicate accidental target creation;
   - better validation before save.
2. Add proper target management:
   - edit target;
   - disable target;
   - delete target;
   - duplicate target for another date.
3. Add server sync assistance:
   - show local config modified time;
   - show server config modified time;
   - generate or run upload/verify commands safely.
4. Improve recurring class workflow:
   - recurring list section;
   - skip-date management;
   - permanent class priorities once Product approves them.

## Not Yet Planned

- Public hosted UI.
- Multi-user account management.
- Automatic server upload from UI.
- Secret editing in UI.

