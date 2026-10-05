# PayTrack

A mobile-friendly work-hours tracker and paycheck estimator.

## Features

- Log shifts, start/end times, breaks, and notes
- Estimate gross and take-home pay
- Configurable hourly rate, tax percentage, overtime multiplier, and work week
- Browse current and previous weeks
- Installable Progressive Web App for Android/Chrome
- Offline support

## Run locally

```bash
python3 server.py
```

Then open `http://localhost:8000`.

The standalone interface stores data in the browser. The included Python server also provides an SQLite-backed API.

## Important

Pay and tax figures are estimates and are not payroll or tax advice.
