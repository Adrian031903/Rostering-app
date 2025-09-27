# Rostering Application

CLI-based staff scheduling system meeting all 4 core requirements.

## Quick Start for Marker

```bash
# 1. Setup
pip install -r requirements.txt
flask init

# 2. Test All 4 Requirements
flask auth login admin admin123             # Login as admin

flask shift schedule 1 2025-09-30 09:00 17:00   # Requirement 1: Admin schedules shifts
flask shift view                             # Requirement 2: View roster (works for anyone)
flask time in 1                             # Requirement 3: Staff time in/out
flask time out 1
flask shift report 2025-09-30               # Requirement 4: Admin views reports
```

## The 4 Core Requirements

### ✅ 1. (Admin) Schedule Staff Shifts for the Week
```bash
flask shift schedule <user_id> <date> <start_time> <end_time>
# Example: flask shift schedule 2 2025-10-01 08:00 16:00
```

### ✅ 2. (Staff) View Combined Roster of All Staff
```bash
flask shift view
# Shows all scheduled shifts for all staff members
```

### ✅ 3. (Staff) Time In/Time Out at Start/End of Shift
```bash
flask time in <shift_id>     # Clock in
flask time out <shift_id>    # Clock out
```

### ✅ 4. (Admin) View Shift Report for the Week
```bash
flask shift report <start_date>
# Shows total hours and shift details for the week
```

## Authentication (Simplified)

```bash
flask auth login admin admin123      # Admin login (secure)
flask auth login any_name any_pass   # Staff login (any credentials work)
flask auth whoami                    # Check who's logged in
```

## Complete Demo Script

```bash
# Setup
flask init

# Create some staff
flask auth login admin admin123
flask user create sarah staff123 --role staff
flask user create mike mike123 --role staff

# Schedule shifts (Admin only)
flask shift schedule 2 2025-10-01 08:00 16:00
flask shift schedule 3 2025-10-01 16:00 00:00
flask shift schedule 2 2025-10-05 10:00 18:00

# Anyone can view roster
flask shift view

# Staff can clock in/out
flask time in 1
flask time out 1

# Admin can generate reports
flask shift report 2025-10-01
```

## System Features

- **Professional CLI Output** - Clean formatted tables with colors
- **Role-Based Access** - Admin vs Staff permissions  
- **Complete Time Tracking** - Automatic status updates
- **Input Validation** - Prevents scheduling conflicts and invalid data
- **Staff Statistics** - Performance analytics and reporting
- **SQLite Database** - Persistent data storage

## Additional Professional Features

### 📊 Staff Performance Analytics
```bash
flask stats staff sarah
# Shows: Total hours, completion rate, shift statistics
```

### ✅ Smart Validation
- Prevents scheduling shifts in the past
- Detects scheduling conflicts for same staff member
- Validates time ranges (start must be before end)
- Checks user existence before scheduling