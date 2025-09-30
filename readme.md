![Tests](https://github.com/uwidcit/flaskmvc/actions/workflows/dev.yml/badge.svg)

# Rostering App (CLI)

An app for scheduling and tracking shifts with a simple, marker-friendly CLI. All features are demonstrated below and mapped to the four required items.

## Quick Start

Prereqs: Python 3, pip, packages in `requirements.txt`.

```bash
pip install -r requirements.txt

# initialize a fresh sqlite DB and seed admin + a sample staff
FLASK_APP=wsgi.py flask init

# login as admin to perform admin-only actions
FLASK_APP=wsgi.py flask auth login admin admin123
```

## Commands

- Auth
  - Login: `flask auth login <username> <password>`
  - Logout: `flask auth logout`
  - Who am I: `flask auth whoami`

- Users (admin only where noted)
  - Create (admin): `flask user create <username> <password> --role <staff|supervisor|admin>`
  - List (login required): `flask user list`

- Shifts
  - Schedule (admin): `flask shift schedule <user_id> <YYYY-MM-DD> <HH:MM> <HH:MM>`
    - Make sure: no past dates, start<end, user exists, conflict detection.
  - View roster (login): `flask shift view`
  - Weekly report (admin): `flask shift report <week_start YYYY-MM-DD>` -weekly report auto gives report 7 days after the date you request, so a week worth of shift report.

- Time tracking (staff)
  - Clock in: `flask time in <shift_id>`
  - Clock out: `flask time out <shift_id>`

- Staff stats
  - `flask stats staff <username>`

- Leave requests
  - Request (login): `flask leave request <start YYYY-MM-DD> <end YYYY-MM-DD> <type> [--reason <text>]`
  - List (admin/supervisor): `flask leave list --status <pending|approved|rejected|all>`
  - Approve (admin/supervisor): `flask leave approve <request_id>`
  - Reject (admin/supervisor): `flask leave reject <request_id> [--reason <text>]`

- Swap requests
  - Request (login): `flask swap request <shift_id> <target_username> [--note <text>]`
  - List (admin/supervisor): `flask swap list --status <pending|approved|rejected|all>`
  - Approve (admin/supervisor): `flask swap approve <request_id>` (blocks if conflicts)
  - Reject (admin/supervisor): `flask swap reject <request_id> [--reason <text>]`

## Maps to the 4 requirements

1) Admin schedule shifts for the week → `flask shift schedule ...`
2) Staff view combined roster → `flask shift view`
3) Staff time in/out at start/end of shift → `flask time in/out <shift_id>`
4) Admin view shift report for the week → `flask shift report <week_start>`

RBAC is enforced: admin-only where noted; supervisor can review leave/swap; staff can view roster and time in/out their assigned shifts.

## demo (copy/paste)

```bash
# 0) init and login
FLASK_APP=wsgi.py flask init
FLASK_APP=wsgi.py flask auth login admin admin123

# 1) create a supervisor and a staff
FLASK_APP=wsgi.py flask user create sue suepass --role supervisor
FLASK_APP=wsgi.py flask user create alice alicepass --role staff

# 2) schedule two shifts on the same day
FLASK_APP=wsgi.py flask shift schedule 3 2025-09-28 09:00 17:00   # sue
FLASK_APP=wsgi.py flask shift schedule 4 2025-09-28 09:00 17:00   # alice

# 3) staff clocks time and views stats
FLASK_APP=wsgi.py flask auth login alice alicepass
FLASK_APP=wsgi.py flask shift view
FLASK_APP=wsgi.py flask time in 2
FLASK_APP=wsgi.py flask time out 2
FLASK_APP=wsgi.py flask stats staff alice

# 4) weekly report (admin)
FLASK_APP=wsgi.py flask auth login admin admin123
FLASK_APP=wsgi.py flask shift report 2025-09-23
```

Notes:
- Dates above are examples; use future dates to avoid “past-date” validation.
- Swap/Leave flows are available and validated (conflict checks for swap, no past leave dates). See Commands.

## Testing

```bash
pytest   # 17 tests should pass
```

## Troubleshooting

- If you see “Cannot schedule shifts in the past”, use a future date.
- “Access denied” means your role doesn’t match; login as admin or supervisor where required.
- To reset the environment, run `flask init` again (fresh DB).
