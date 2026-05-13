# CEO Action Queue

Last updated: 2026-05-13

## Open Actions

1. Decide whether to create a private GitHub repo for this project.
   - Owner thread: Product / Booking Engine.
   - Why it matters: GitHub would make version history, rollback, and thread handoff cleaner, but the live config contains secrets and must be excluded first.
   - Recommended decision: yes, but private only, with `.gitignore` and a sanitized example config.
   - Status: Eileen asked Product to do this. Local Git setup is being done first; GitHub push still needs a private repo/auth route because `gh` is not installed locally.

## Protocol

Use this file only for items that need Eileen to decide, review, approve, or provide information.

Each action should include:

- date added;
- owner thread;
- decision or review needed;
- why it matters;
- deadline if any;
- status.
