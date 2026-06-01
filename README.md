# YogaBot

YogaBot is a personal automation bot for booking Pure Yoga, Pilates, and Pure Fitness Singapore classes at the moment the booking window opens.

It was built to reduce the friction between wanting to attend wellness classes and actually getting a spot, especially for popular classes that open for booking several days in advance and fill quickly.

The project combines scheduling logic, booking target management, class matching, waitlist fallback, Telegram notifications, and a local admin panel for managing recurring and one-off booking targets.

## Why This Exists

Wellness habits often fail not because people lack intention, but because the logistics get annoying.

YogaBot helps with one very specific problem:

> “I want to attend my regular classes, but I do not want to manually log in at exactly the booking window every time.”

The bot is designed to automate that repetitive booking workflow while still keeping the user in control through configuration, logs, dry runs, lookup tools, and optional Telegram notifications.

## What It Does

YogaBot can:

* Book Pure Yoga classes
* Book Pure Pilates classes through the Pure Yoga site
* Book Pure Fitness classes
* Support recurring booking targets
* Support one-off booking targets
* Match classes by site, date, time, location, class name, and teacher
* Handle teacher replacement through configurable teacher policies
* Log in shortly before the booking window opens
* Attempt booking at the configured opening time
* Fall back to waitlist booking when a class is full
* Send Telegram notifications
* Run lookup-only checks without making bookings
* Run dry-run tests without sending booking requests
* Manage targets through a local browser-based admin panel

## Project Status

This is a working personal automation project.

The booking engine and config workflow are functional, but the project is still evolving. Current improvement areas include safer target management, better validation, cleaner documentation, and more reliable deployment workflows.

## Core Features

### Booking Engine

The main booking script is:

```txt
pure_yoga_booking.py
```

It handles:

* Loading booking configuration
* Reading recurring and one-off targets
* Calculating the correct booking date and class date
* Fetching class schedules
* Matching the correct class
* Logging in
* Booking or joining the waitlist
* Sending notifications
* Writing runtime logs

### Local Admin Panel

The local admin panel is:

```txt
pure_yoga_admin.py
```

It provides a small browser-based control panel for managing booking targets.

The admin panel supports:

* Viewing active targets
* Adding one-off targets
* Adding recurring targets
* Searching live classes
* Checking saved targets for a date
* Cleaning expired one-off targets
* Applying skip dates
* Deleting targets

By default, the admin panel works with a development config so UI testing does not accidentally affect the live booking config.

### Config-Based Targets

Booking targets are configured in JSON.

Each target can define:

* Site: Yoga / Pilates / Fitness
* Class name
* Start time
* Location
* Teacher name
* Teacher policy
* Priority
* Recurring days
* One-off class date
* Booking run date
* Skip dates
* Booking window settings

### Waitlist Fallback

If a class is full, the bot can attempt to join the waitlist instead of failing immediately.

This behavior is controlled by config.

### Teacher Policy

The bot supports teacher matching behavior.

For example:

* Prefer a named teacher
* Still book the same class if the teacher is replaced
* Require exact teacher matching
* Ignore teacher matching

This is useful because class schedules sometimes change after the user sets a target.

### Telegram Notifications

YogaBot can send Telegram messages for booking updates when a bot token and chat ID are provided in the config.

This allows the user to know whether a class was booked, waitlisted, skipped, or not found.

## Tech Stack

* Python
* requests
* httpx with HTTP/2 support
* tzdata
* JSON config files
* Local browser-based admin UI
* Telegram Bot API for optional notifications
* Windows VPS / Task Scheduler deployment support

## Repository Structure

```txt
yogabot/
  pure_yoga_booking.py
  pure_yoga_admin.py
  pure_yoga_config.example.json
  requirements.txt
  run_pure_booking.bat
  PROJECT_BRIEF.md
  ROADMAP.md
  PURE_YOGA_BOT_README.md
  PURE_YOGA_BOT_HANDOVER.md
  VPS_SETUP_README.md
  product/
  ui/
  ops/
```

## Setup

### 1. Clone the Repository

```bash
git clone https://github.com/eileenlumena/yogabot.git
cd yogabot
```

### 2. Create Your Config File

Copy the example config:

```bash
cp pure_yoga_config.example.json pure_yoga_config.json
```

Then edit:

```txt
pure_yoga_config.json
```

Fill in your own:

* Pure account username
* Pure account password
* Booking targets
* Telegram bot token, optional
* Telegram chat ID, optional

Do not commit your real config file.

Your real `pure_yoga_config.json` should stay private because it contains credentials and personal booking preferences.

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

The requirements include:

```txt
requests
httpx[http2]
tzdata
```

`tzdata` is included for systems where the `Asia/Singapore` timezone is not available by default.

## Usage

### Lookup Classes Without Booking

Use lookup mode to check active targets and class matches without logging in or booking:

```bash
python pure_yoga_booking.py --config pure_yoga_config.json --lookup-only --list-classes
```

### Lookup a Specific Date

```bash
python pure_yoga_booking.py --config pure_yoga_config.json --lookup-only --target-date 2026-04-06 --list-classes
```

### Dry Run

Use dry run mode to test login and timing logic without sending the booking request:

```bash
python pure_yoga_booking.py --config pure_yoga_config.json --dry-run
```

### Run the Real Booking Flow

```bash
python pure_yoga_booking.py --config pure_yoga_config.json
```

Only run the real booking flow when your config is correct.

## Local Admin Panel

Start the local admin panel:

```bash
python pure_yoga_admin.py
```

By default, it runs at:

```txt
http://127.0.0.1:8501
```

The admin panel can be used to:

* Add one-off booking targets
* Add recurring booking targets
* Search live classes
* Preview active targets
* Clean expired targets
* Apply skip dates
* Delete targets

By default, the admin UI uses a development config file to reduce the risk of accidentally changing the live booking config.

## Example Target

A recurring target may look like this:

```json
{
  "site": "yoga",
  "days": ["Sat"],
  "class_name": "Healing: Yoga Therapy",
  "start_time": "12:30",
  "location_id": 19,
  "location_name": "Yoga - Ngee Ann City",
  "teacher_name": "Arun R.",
  "teacher_policy": "prefer_named_teacher",
  "mode": "book_all",
  "priority": 1,
  "class_days_ahead": 5,
  "booking_open_days": 5,
  "schedule_window_days": 1
}
```

## Configuration Notes

### `site`

Supported values include:

```txt
yoga
fitness
```

Pilates classes that appear on the Pure Yoga site should use:

```txt
yoga
```

### `teacher_policy`

Common values:

```txt
prefer_named_teacher
exact
any_teacher
```

### `mode`

Common values:

```txt
book_all
priority
```

`book_all` attempts the target whenever it is active.

`priority` treats lower-priority targets as fallback options.

### `booking.open_time`

The default booking open time is:

```txt
09:00:00
```

The bot uses Singapore time internally.

## Deployment Notes

The bot can be deployed on a VPS and scheduled to run automatically.

For Windows VPS usage, the repository includes:

```txt
run_pure_booking.bat
VPS_SETUP_README.md
```

The bot is timezone-aware and uses `Asia/Singapore` internally, even if the server itself is in another timezone.

## Security Notes

Do not commit:

* `pure_yoga_config.json`
* Pure account credentials
* Telegram bot tokens
* Telegram chat IDs
* Cookies
* Captured headers
* Session values
* Server IPs or private deployment details

Use the example config for public documentation.

Keep real credentials only on your local machine or private server.

## Responsible Use

This project is intended for personal booking automation and learning purposes.

Use responsibly:

* Do not abuse booking systems
* Do not spam booking endpoints
* Do not use it to hoard class spots
* Respect cancellation rules
* Respect the platform’s terms and booking policies
* Keep automation limited and intentional

The goal is to reduce personal friction around attending wellness classes, not to create unfair access or overload a booking system.

## Roadmap

Planned or possible improvements:

* Better README and contributor documentation
* Safer config validation
* More robust target editing
* Disable / enable targets
* Duplicate targets
* Better skip-date management
* Server sync helper
* Clearer booking logs
* More structured error reporting
* Improved Telegram command support
* Tests for date calculation and target matching
* Safer secret handling
* Optional PWA or lightweight dashboard
* Cleaner separation between booking engine, config, and UI

## Philosophy

YogaBot is part of a broader idea:

AI and automation should not only make digital systems more addictive. They should also help people follow through on real-world habits that support their health, attention, and agency.

This bot uses software to reduce the tiny moments of friction that stop people from showing up for themselves.

Book the class.

Go practice.

Let the bot handle the repetitive part.
