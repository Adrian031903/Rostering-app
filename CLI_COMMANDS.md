# Rostering App - CLI Commands Reference

## Overview
This document provides a comprehensive guide to all CLI commands available in the Rostering App. The application supports staff scheduling, shift management, leave requests, shift swaps, and time tracking.

## Database Initialization
```bash
flask init
```
Creates and initializes the database with all required tables.

## User Management

### Create Users
```bash
# Basic user creation
flask user create <username> <password>

# Create user with additional details
flask user create john johnpass --email john@example.com --role supervisor --name "John Smith"

# Create different user roles
flask user create admin adminpass --role admin --name "Admin User"
flask user create supervisor suppass --role supervisor --name "Jane Supervisor"
flask user create staff staffpass --role staff --name "Bob Staff"
```

### List Users
```bash
# List all users (string format)
flask user list

# List all users (JSON format)
flask user list json
```

## Shift Management

### Create Shifts
```bash
# Create a shift for a user
flask shift create <user_id> <work_date> <start_time> <end_time>

# Examples:
flask shift create 1 2025-09-27 09:00 17:00
flask shift create 2 2025-09-28 14:00 22:00 --status scheduled
```

### List Shifts
```bash
# List all shifts
flask shift list

# Filter shifts by user
flask shift list --user-id 1

# Filter shifts by date
flask shift list --date 2025-09-27

# Filter shifts by status
flask shift list --status scheduled

# Combine filters
flask shift list --user-id 1 --date 2025-09-27
```

### Delete Shifts
```bash
flask shift delete <shift_id>
```

## Leave Request Management

### Create Leave Requests
```bash
# Create a leave request
flask leave create <user_id> <start_date> <end_date> <leave_type>

# Examples:
flask leave create 1 2025-10-01 2025-10-03 vacation --reason "Family vacation"
flask leave create 2 2025-09-30 2025-09-30 sick --reason "Doctor appointment"
```

### List Leave Requests
```bash
# List all leave requests
flask leave list

# Filter by status
flask leave list --status pending
flask leave list --status approved

# Filter by user
flask leave list --user-id 1
```

### Approve/Reject Leave Requests
```bash
# Approve a leave request
flask leave approve <request_id> <approver_id>

# Reject a leave request
flask leave reject <request_id> <approver_id> --reason "Insufficient coverage"
```

## Shift Swap Management

### Create Swap Requests
```bash
# Create a shift swap request
flask swap create <shift_id> <from_user_id> <to_user_id>

# With note
flask swap create 1 2 3 --note "Emergency family matter"
```

### List Swap Requests
```bash
# List all swap requests
flask swap list

# Filter by status
flask swap list --status pending
```

### Approve Swap Requests
```bash
# Approve a swap request
flask swap approve <request_id> <approver_id>
```

## Time Logging

### Clock In/Out
```bash
# Clock in to a shift
flask timelog clockin <shift_id> <user_id>

# Clock out from a shift
flask timelog clockout <shift_id> <user_id>
```

### List Time Logs
```bash
# List all time logs
flask timelog list

# Filter by user
flask timelog list --user-id 1

# Filter by shift
flask timelog list --shift-id 1

# Show only open time logs (not clocked out)
flask timelog list --open-only
```

## Roster Management

### View Roster
```bash
# View roster for a date range
flask roster view <start_date> <end_date>

# Example: View roster for a week
flask roster view 2025-09-27 2025-10-03
```

### Generate Weekly Reports
```bash
# Generate weekly report starting from a specific date
flask roster report <start_date>

# Example: Generate report for week starting Monday
flask roster report 2025-09-23
```

## Complete Example Workflow

### 1. Initialize Database and Create Users
```bash
# Initialize database
flask init

# Create admin user
flask user create admin adminpass --role admin --name "System Admin" --email admin@company.com

# Create supervisors
flask user create supervisor1 suppass --role supervisor --name "Jane Smith" --email jane@company.com
flask user create supervisor2 suppass --role supervisor --name "Bob Wilson" --email bob@company.com

# Create staff members
flask user create alice alicepass --role staff --name "Alice Johnson" --email alice@company.com
flask user create charlie charliepass --role staff --name "Charlie Brown" --email charlie@company.com
flask user create diana dianapass --role staff --name "Diana Prince" --email diana@company.com
```

### 2. Create Weekly Schedule
```bash
# Monday shifts
flask shift create 3 2025-09-29 09:00 17:00  # Alice morning
flask shift create 4 2025-09-29 13:00 21:00  # Charlie afternoon
flask shift create 5 2025-09-29 17:00 01:00  # Diana night

# Tuesday shifts
flask shift create 3 2025-09-30 09:00 17:00  # Alice morning
flask shift create 4 2025-09-30 13:00 21:00  # Charlie afternoon
flask shift create 5 2025-09-30 17:00 01:00  # Diana night

# Continue for rest of week...
```

### 3. Handle Leave Requests
```bash
# Alice requests vacation
flask leave create 3 2025-10-01 2025-10-03 vacation --reason "Wedding anniversary trip"

# Supervisor approves
flask leave approve 1 2
```

### 4. Handle Shift Swaps
```bash
# Charlie wants Diana to cover his Tuesday shift
flask swap create 4 4 5 --note "Doctor appointment"

# Supervisor approves swap
flask swap approve 1 2
```

### 5. Time Tracking
```bash
# Alice clocks in for Monday shift
flask timelog clockin 1 3

# Alice clocks out
flask timelog clockout 1 3
```

### 6. Generate Reports
```bash
# View roster for the week
flask roster view 2025-09-29 2025-10-05

# Generate weekly report
flask roster report 2025-09-29
```

## User Roles and Permissions

### Staff (role: 'staff')
- Clock in/out of their shifts
- Request leave
- Request shift swaps
- View their own schedule

### Supervisor (role: 'supervisor')  
- All staff permissions
- Approve/reject leave requests
- Approve/reject shift swap requests
- View all schedules
- Generate reports

### Admin (role: 'admin')
- All supervisor permissions  
- Create/modify shifts
- Create users
- Full system access

## Status Values

### Shift Status
- `scheduled` - Shift is scheduled (default)
- `completed` - Shift has been completed
- `cancelled` - Shift has been cancelled

### Leave Request Status
- `pending` - Awaiting approval (default)
- `approved` - Request has been approved
- `rejected` - Request has been rejected

### Swap Request Status
- `pending` - Awaiting approval (default)
- `approved` - Swap has been approved and processed
- `rejected` - Swap request has been rejected

## Tips and Best Practices

1. **Always initialize the database first** with `flask init`
2. **Create admin and supervisor users first** to manage approvals
3. **Use consistent date formats** (YYYY-MM-DD) and time formats (HH:MM)
4. **Check for conflicts** before creating overlapping shifts
5. **Regular reporting** helps track performance and attendance
6. **Use descriptive notes** in swap requests and leave reasons

## Troubleshooting

### Common Issues
- **User not found**: Verify user ID exists with `flask user list`
- **Shift not found**: Check shift ID with `flask shift list`  
- **Permission denied**: Ensure approver has supervisor or admin role
- **Date format errors**: Use YYYY-MM-DD format for dates, HH:MM for times
- **Already clocked in**: Check existing time logs with `flask timelog list --open-only`

### Checking Data
```bash
# View all users and their IDs
flask user list

# Check shifts for a specific date
flask shift list --date 2025-09-27

# Check pending requests
flask leave list --status pending
flask swap list --status pending

# Check open time logs
flask timelog list --open-only
```