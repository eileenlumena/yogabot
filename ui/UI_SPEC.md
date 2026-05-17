# UI / Control Panel Spec

Last updated: 2026-05-13

## Goal

Give Eileen a simple local control panel to manage booking classes without editing JSON manually or asking the Product thread to patch config every time.

The UI should be safe, clear, and boring. It should reduce accidental wrong bookings.

Until fully ready, the UI is a testing surface and must write to `pure_yoga_config.dev.json` by default, not the live booking config.

## User Workflows

### Add One-Off Class

1. Choose site and location.
2. Type part of class name.
3. Optionally choose class date first.
4. Search live classes.
5. Click `Use` on the desired posted class.
6. UI fills:
   - class date;
   - booking run date;
   - class name;
   - start time;
   - teacher;
   - site;
   - location.
7. User saves one-off target.
8. UI shows it in current targets.

### Add Recurring Class

1. Choose day.
2. Choose site and location.
3. Enter class name, time, teacher, and priority.
4. Save recurring target.
5. UI shows it in current targets.

Future improvement: recurring class flow should also support live class search and autofill.

### Preview Booking Run

Not fully implemented yet.

Expected future behavior:

1. User chooses booking run date or class date.
2. UI shows active targets for that run.
3. UI flags:
   - expired one-offs;
   - duplicates;
   - cross-site sequencing;
   - more than 2 or 3 classes;
   - Pure booking-limit warnings.

### Server Upload

Current behavior:

- UI displays the manual `scp` command.

Future behavior:

- UI should show local modified time and server modified time.
- UI may generate upload/verify commands.
- UI must not automatically upload without Product approval.

## Data Rules

One-off targets must include:

- `site`
- `days`
- `class_name`
- `start_time`
- `location_id`
- `location_name`
- `teacher_name`
- `teacher_policy`
- `mode`
- `priority`
- `class_date`
- `booking_run_date`
- `booking_open_days`
- `schedule_window_days`

Recurring targets must include:

- `site`
- `days`
- `class_name`
- `start_time`
- `location_id`
- `location_name`
- `teacher_name`
- `teacher_policy`
- `mode`
- `priority`
- `class_days_ahead`
- `booking_open_days`
- `schedule_window_days`

Booking Run Date:

- Must be exactly 5 days before Class Date unless Product later changes booking rules.

Teacher policy:

- Default to `prefer_named_teacher`.

Mode:

- Default to `book_all`.

## Booking Limit Warning Rules

Pure limits members to:

- maximum 6 Yoga classes within a continuous 5-day period;
- maximum 6 Pilates classes within a continuous 5-day period;
- maximum 6 Fitness classes within a continuous 5-day period;
- maximum 2 bookings per class type per class date.

The UI should classify planned targets as Yoga, Pilates, or Fitness.

Current config uses `site: "fitness"` for Fitness and `site: "yoga"` for both Yoga and Pilates. Pilates should be detected by Product-approved class mappings, including class names such as `Reformer` and `Pilates`.

The UI should warn:

- before saving a target if it would exceed a daily class-type limit;
- before saving a target if it would exceed a rolling 5-day class-type limit;
- in Active Run Preview when currently planned targets are already over limits.

Start with warnings, not hard blocks. Product can later decide which warnings should become blocking.

Known limitation:

- The UI can count planned targets in config, but it does not yet know classes manually booked outside the bot unless the user enters them or the bot can fetch account bookings.

## Safety Requirements

- Never display credentials or Telegram token/chat id.
- Default UI testing must not mutate `pure_yoga_config.json`.
- Never edit booking timing settings from the UI unless Product approves.
- Warn when planned targets exceed Pure booking limits.
- Warn before cleaning expired targets.
- Add duplicate detection before further UI expansion.
- Add active-run preview before relying on UI for important bookings.
- Prefer disabling targets over deleting them for permanent classes.

## Visual / UX Direction

- This is an operational tool, not a marketing page.
- Keep it dense, calm, and scannable.
- Prioritize target verification, warnings, and upload confidence.
- Avoid decorative UI that hides the booking-critical data.
