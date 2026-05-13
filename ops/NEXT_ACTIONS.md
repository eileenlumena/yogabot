# Next Actions

Last updated: 2026-05-13

## For Eileen

1. Decide how you want to create the private GitHub repo for the already-created local Git baseline:
   - install/use GitHub CLI (`gh`), or
   - create a private repo on github.com and provide the remote URL.
   - A new GitHub account is fine if you want this project separated from your main account.

2. Upload the latest local config to the SG server before the 2026-05-14 booking run if you want the new 2026-05-19 targets active on the server.

```bash
scp "/Users/eileenmac/Documents/Yoga Booking Bot/pure_yoga_config.json" root@45.77.249.30:/root/PureYogaBot/pure_yoga_config.json
```

3. Verify the server config timestamp after upload.

```bash
ssh root@45.77.249.30 'stat -c "%y" /root/PureYogaBot/pure_yoga_config.json'
```

4. After the 2026-05-14 run, share the log if you want Product / Booking Engine to compare performance side by side against previous runs.

## For Product / Booking Engine

1. Before ending future work, update `product/PRODUCT_STATUS.md`.
2. If UI needs to act, write the handoff in `ops/HANDOFFS.md` and mention it in `product/PRODUCT_STATUS.md`.
3. If Eileen needs to decide something, add it to `ops/CEO_ACTION_QUEUE.md`.

## For UI / Control Panel

1. Before ending future work, update `ui/UI_STATUS.md`.
2. If Product needs to act, write the handoff in `ops/HANDOFFS.md` and mention it in `ui/UI_STATUS.md`.
3. Keep UI work within `ui/UI_HANDOVER.md` and `ui/UI_SPEC.md` unless Product approves behavior changes.
