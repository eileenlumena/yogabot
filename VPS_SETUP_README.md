# Windows VPS Setup

Copy these files to `C:\Users\Administrator\PureYogaBot` on the Windows VPS:

- `pure_yoga_booking.py`
- `pure_yoga_config.json`
- `requirements.txt`
- `run_pure_booking.bat`

Optional:

- `PURE_YOGA_BOT_README.md`

Install Python on the VPS, then:

```bat
cd C:\Users\Administrator\PureYogaBot
python -m pip install -r requirements.txt
python pure_yoga_booking.py --config pure_yoga_config.json --dry-run
```

If Windows Python reports `No module named 'tzdata'` or `No time zone found with key Asia/Singapore`, rerun the `pip install -r requirements.txt` step. The requirements file includes `tzdata` for that case.

For Task Scheduler on a Japan-time VPS:

- Trigger time: `09:58 AM` daily
- Action: `C:\Users\Administrator\PureYogaBot\run_pure_booking.bat`
- The bundled `.bat` uses the full Python path `C:\Users\Administrator\AppData\Local\Programs\Python\Python312\python.exe` to avoid Task Scheduler PATH issues.

The bot keeps Singapore time internally, so it will still aim for the Singapore booking window.
