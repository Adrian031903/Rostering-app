import click, pytest, sys
from flask.cli import with_appcontext, AppGroup

from App.database import db, get_migrate
from App.models import User, Shift, LeaveRequest, SwapRequest, TimeLog
from App.main import create_app
from App.controllers import ( create_user, get_all_users_json, get_all_users, initialize )
from datetime import datetime, date, time, timedelta

# Color codes for aesthetic output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def success_msg(text):
    return f"{Colors.OKGREEN}✅ {text}{Colors.ENDC}"

def error_msg(text):
    return f"{Colors.FAIL}❌ {text}{Colors.ENDC}"

def info_msg(text):
    return f"{Colors.OKBLUE}ℹ️  {text}{Colors.ENDC}"

def warning_msg(text):
    return f"{Colors.WARNING}⚠️  {text}{Colors.ENDC}"

def header_msg(text):
    return f"{Colors.BOLD}{Colors.HEADER}🏢 {text}{Colors.ENDC}"

def print_separator(char="═", length=80):
    print(f"{Colors.OKCYAN}{char * length}{Colors.ENDC}")

def print_table_header(headers, widths=None):
    """Print a beautiful table header with proper formatting"""
    if widths is None:
        widths = [15] * len(headers)
    
    # Top border
    border_parts = ["┌"]
    for i, width in enumerate(widths):
        border_parts.append("─" * (width + 2))
        if i < len(widths) - 1:
            border_parts.append("┬")
    border_parts.append("┐")
    border = "".join(border_parts)
    print(f"{Colors.OKCYAN}{border}{Colors.ENDC}")
    
    # Header row
    row_parts = [f"{Colors.OKCYAN}│{Colors.ENDC}"]
    for i, (header, width) in enumerate(zip(headers, widths)):
        # Pad header text to exact width
        padded_header = f"{header:<{width}}"
        row_parts.append(f" {Colors.BOLD}{padded_header}{Colors.ENDC} ")
        row_parts.append(f"{Colors.OKCYAN}│{Colors.ENDC}")
    
    print("".join(row_parts))
    
    # Separator
    sep_parts = ["├"]
    for i, width in enumerate(widths):
        sep_parts.append("─" * (width + 2))
        if i < len(widths) - 1:
            sep_parts.append("┼")
    sep_parts.append("┤")
    separator = "".join(sep_parts)
    print(f"{Colors.OKCYAN}{separator}{Colors.ENDC}")

def print_table_footer(widths):
    """Print table bottom border"""
    border_parts = ["└"]
    for i, width in enumerate(widths):
        border_parts.append("─" * (width + 2))
        if i < len(widths) - 1:
            border_parts.append("┴")
    border_parts.append("┘")
    border = "".join(border_parts)
    print(f"{Colors.OKCYAN}{border}{Colors.ENDC}")

def print_table_row(values, widths, colors=None):
    """Print a formatted table row with proper alignment"""
    if colors is None:
        colors = [Colors.ENDC] * len(values)
    
    # Build the row with proper padding calculations
    row_content = []
    
    for i, (value, width, color) in enumerate(zip(values, widths, colors)):
        # Convert value to string
        str_value = str(value)
        
        # Calculate actual display width (without ANSI codes)
        # This handles cases where the value might contain color codes
        display_length = len(str_value)
        
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            # Right-align numbers
            padding = width - display_length
            cell_content = " " * padding + str_value
        else:
            # Left-align text
            padding = width - display_length
            cell_content = str_value + " " * padding
        
        # Ensure exact width
        cell_content = cell_content[:width].ljust(width)
        row_content.append(f" {color}{cell_content}{Colors.ENDC} ")
    
    # Print with borders
    print(f"{Colors.OKCYAN}│{Colors.ENDC}" + f"{Colors.OKCYAN}│{Colors.ENDC}".join(row_content) + f"{Colors.OKCYAN}│{Colors.ENDC}")


# This commands file allow you to create convenient CLI commands for testing controllers

app = create_app()
migrate = get_migrate(app)

# This command creates and initializes the database
@app.cli.command("init", help="Creates and initializes the database")
def init():
    print(header_msg("ROSTERING APP - DATABASE INITIALIZATION"))
    print_separator()
    try:
        initialize()
        print(success_msg("Database initialized successfully!"))
        print(info_msg("You can now create users and start managing your roster"))
    except Exception as e:
        print(error_msg(f"Failed to initialize database: {e}"))

'''
User Commands
'''

# Commands can be organized using groups

# create a group, it would be the first argument of the comand
# eg : flask user <command>
user_cli = AppGroup('user', help='User object commands') 

# Then define the command and any parameters and annotate it with the group (@)
@user_cli.command("create", help="Creates a user")
@click.argument("username", default="rob")
@click.argument("password", default="robpass")
@click.option("--email", help="User email")
@click.option("--role", default="staff", help="User role (staff, supervisor, admin)")
@click.option("--name", help="User's full name")
def create_user_command(username, password, email, role, name):
    print(header_msg("CREATE NEW USER"))
    print_separator("─", 50)
    try:
        # Validate role
        valid_roles = ['staff', 'supervisor', 'admin']
        if role not in valid_roles:
            print(error_msg(f"Invalid role '{role}'. Must be one of: {', '.join(valid_roles)}"))
            return
        
        user = User(username, password, email, role, name)
        db.session.add(user)
        db.session.commit()
        
        print(success_msg(f"User '{username}' created successfully!"))
        print(info_msg(f"Role: {role.upper()}"))
        if email:
            print(info_msg(f"Email: {email}"))
        if name:
            print(info_msg(f"Full Name: {name}"))
        print(f"{Colors.OKCYAN}👤 User ID: {user.id}{Colors.ENDC}")
    except Exception as e:
        print(error_msg(f"Failed to create user: {e}"))

# this command will be : flask user create bob bobpass

@user_cli.command("list", help="Lists users in the database")
@click.argument("format", default="table")
def list_user_command(format):
    print(header_msg("USER DIRECTORY"))
    print_separator()
    
    users = get_all_users()
    if not users:
        print(warning_msg("No users found in the system"))
        return
    
    if format == 'json':
        import json
        print(json.dumps(get_all_users_json(), indent=2))
    else:
        # Beautiful table format
        headers = ["ID", "USERNAME", "ROLE", "NAME", "EMAIL"]
        widths = [4, 20, 18, 30, 35]
        
        print_table_header(headers, widths)
        
        for user in users:
            role_color = Colors.FAIL if user.role == 'admin' else Colors.WARNING if user.role == 'supervisor' else Colors.OKGREEN
            role_display = f"{user.role.upper()}"
            
            values = [
                str(user.id),
                user.username,
                role_display,
                user.name or 'N/A',
                user.email or 'N/A'
            ]
            
            colors = [Colors.OKCYAN, Colors.ENDC, role_color, Colors.ENDC, Colors.ENDC]
            print_table_row(values, widths, colors)
        
        print_table_footer(widths)
        print(f"\n{info_msg(f'Total users: {len(users)}')}")

app.cli.add_command(user_cli) # add the group to the cli

'''
Test Commands
'''

test = AppGroup('test', help='Testing commands') 

@test.command("user", help="Run User tests")
@click.argument("type", default="all")
def user_tests_command(type):
    if type == "unit":
        sys.exit(pytest.main(["-k", "UserUnitTests"]))
    elif type == "int":
        sys.exit(pytest.main(["-k", "UserIntegrationTests"]))
    else:
        sys.exit(pytest.main(["-k", "App"]))
    

app.cli.add_command(test)

'''
Shift Commands
'''

shift_cli = AppGroup('shift', help='Shift management commands')

@shift_cli.command("create", help="Creates a shift")
@click.argument("user_id", type=int)
@click.argument("work_date")  # YYYY-MM-DD format
@click.argument("start_time")  # HH:MM format
@click.argument("end_time")  # HH:MM format
@click.option("--status", default="scheduled", help="Shift status")
def create_shift_command(user_id, work_date, start_time, end_time, status):
    print(header_msg("CREATE NEW SHIFT"))
    print_separator("─", 50)
    
    try:
        user = User.query.get(user_id)
        if not user:
            print(error_msg(f"User with ID {user_id} not found"))
            return
        
        shift = Shift(user_id, work_date, start_time, end_time, status)
        
        # Check for conflicts
        conflicts = []
        existing_shifts = Shift.query.filter_by(
            user_id=user_id,
            work_date=shift.work_date,
            status='scheduled'
        ).all()
        
        for existing_shift in existing_shifts:
            if shift.overlaps(existing_shift.start_time, existing_shift.end_time):
                conflicts.append(f"{existing_shift.start_time}-{existing_shift.end_time}")
        
        if conflicts:
            print(warning_msg(f"⚠️  Potential conflicts with existing shifts: {', '.join(conflicts)}"))
            if not click.confirm("Continue anyway?"):
                print(info_msg("Shift creation cancelled"))
                return
        
        db.session.add(shift)
        db.session.commit()
        
        print(success_msg("Shift created successfully!"))
        print(f"{Colors.OKCYAN}👤 Employee: {user.username} ({user.role}){Colors.ENDC}")
        print(f"{Colors.OKCYAN}📅 Date: {work_date}{Colors.ENDC}")
        print(f"{Colors.OKCYAN}⏰ Time: {start_time} - {end_time} ({shift.duration_hours():.1f} hours){Colors.ENDC}")
        print(f"{Colors.OKCYAN}📊 Status: {status.upper()}{Colors.ENDC}")
        print(f"{Colors.OKCYAN}🆔 Shift ID: {shift.id}{Colors.ENDC}")
        
    except Exception as e:
        print(error_msg(f"Failed to create shift: {e}"))

@shift_cli.command("list", help="Lists all shifts")
@click.option("--user-id", type=int, help="Filter by user ID")
@click.option("--date", help="Filter by date (YYYY-MM-DD)")
@click.option("--status", help="Filter by status")
def list_shifts_command(user_id, date, status):
    print(header_msg("SHIFT SCHEDULE"))
    
    # Show active filters
    filters = []
    if user_id:
        user = User.query.get(user_id)
        filters.append(f"User: {user.username if user else user_id}")
    if date:
        filters.append(f"Date: {date}")
    if status:
        filters.append(f"Status: {status}")
    
    if filters:
        print(f"{Colors.OKCYAN}🔍 Filters: {' | '.join(filters)}{Colors.ENDC}")
    
    print_separator()
    
    query = Shift.query
    
    if user_id:
        query = query.filter_by(user_id=user_id)
    if date:
        query = query.filter_by(work_date=datetime.strptime(date, '%Y-%m-%d').date())
    if status:
        query = query.filter_by(status=status)
    
    shifts = query.order_by(Shift.work_date, Shift.start_time).all()
    
    if not shifts:
        print(warning_msg("No shifts found matching the criteria"))
        return
    
    headers = ["ID", "EMPLOYEE", "DATE", "TIME", "DURATION", "STATUS"]
    widths = [4, 20, 16, 25, 15, 18]
    
    print_table_header(headers, widths)
    
    for shift in shifts:
        user = User.query.get(shift.user_id)
        status_color = Colors.OKGREEN if shift.status == 'completed' else Colors.WARNING if shift.status == 'scheduled' else Colors.FAIL
        
        values = [
            str(shift.id),
            user.username,
            str(shift.work_date),
            f"{shift.start_time}-{shift.end_time}",
            f"{shift.duration_hours():.1f}h",
            shift.status.upper()
        ]
        
        colors = [Colors.OKCYAN, Colors.ENDC, Colors.ENDC, Colors.ENDC, Colors.OKGREEN, status_color]
        print_table_row(values, widths, colors)
    
    print_table_footer(widths)
    print(f"\n{info_msg(f'Total shifts: {len(shifts)}')}")

@shift_cli.command("delete", help="Deletes a shift")
@click.argument("shift_id", type=int)
def delete_shift_command(shift_id):
    shift = Shift.query.get(shift_id)
    if not shift:
        print(f"Error: Shift with ID {shift_id} not found")
        return
    
    db.session.delete(shift)
    db.session.commit()
    print(f'Shift {shift_id} deleted')

app.cli.add_command(shift_cli)

'''
Leave Request Commands
'''

leave_cli = AppGroup('leave', help='Leave request management commands')

@leave_cli.command("create", help="Creates a leave request")
@click.argument("user_id", type=int)
@click.argument("start_date")  # YYYY-MM-DD format
@click.argument("end_date")  # YYYY-MM-DD format
@click.argument("leave_type")
@click.option("--reason", help="Reason for leave")
def create_leave_command(user_id, start_date, end_date, leave_type, reason):
    try:
        user = User.query.get(user_id)
        if not user:
            print(f"Error: User with ID {user_id} not found")
            return
        
        leave_request = LeaveRequest(user_id, start_date, end_date, leave_type, reason)
        db.session.add(leave_request)
        db.session.commit()
        print(f'Leave request created for {user.username} from {start_date} to {end_date}')
    except Exception as e:
        print(f'Error creating leave request: {e}')

@leave_cli.command("list", help="Lists leave requests")
@click.option("--status", help="Filter by status")
@click.option("--user-id", type=int, help="Filter by user ID")
def list_leave_command(status, user_id):
    query = LeaveRequest.query
    
    if status:
        query = query.filter_by(status=status)
    if user_id:
        query = query.filter_by(requester_id=user_id)
    
    requests = query.all()
    
    if not requests:
        print("No leave requests found")
        return
    
    print(header_msg("LEAVE REQUESTS"))
    print_separator()
    
    headers = ["ID", "EMPLOYEE", "DATES", "TYPE", "STATUS", "APPROVER"]
    widths = [4, 20, 30, 18, 18, 20]
    
    print_table_header(headers, widths)
    
    for req in requests:
        user = User.query.get(req.requester_id)
        approver = User.query.get(req.approver_id) if req.approver_id else None
        
        status_color = Colors.WARNING if req.status == 'pending' else Colors.OKGREEN if req.status == 'approved' else Colors.FAIL
        status_display = f"{req.status.upper()}"
        
        date_range = f"{req.start_date} to {req.end_date}"
        
        values = [
            str(req.id),
            user.username,
            date_range,
            req.type.upper(),
            status_display,
            approver.username if approver else 'None'
        ]
        
        colors = [Colors.OKCYAN, Colors.ENDC, Colors.ENDC, Colors.OKBLUE, status_color, Colors.ENDC]
        print_table_row(values, widths, colors)
    
    print_table_footer(widths)
    print(f"\n{info_msg(f'Total leave requests: {len(requests)}')}")

@leave_cli.command("approve", help="Approves a leave request")
@click.argument("request_id", type=int)
@click.argument("approver_id", type=int)
def approve_leave_command(request_id, approver_id):
    leave_request = LeaveRequest.query.get(request_id)
    if not leave_request:
        print(f"Error: Leave request with ID {request_id} not found")
        return
    
    approver = User.query.get(approver_id)
    if not approver or not approver.can_approve_requests():
        print(f"Error: User {approver_id} cannot approve requests")
        return
    
    leave_request.approve(approver_id)
    db.session.commit()
    print(f'Leave request {request_id} approved by {approver.username}')

@leave_cli.command("reject", help="Rejects a leave request")
@click.argument("request_id", type=int)
@click.argument("approver_id", type=int)
@click.option("--reason", help="Rejection reason")
def reject_leave_command(request_id, approver_id, reason):
    leave_request = LeaveRequest.query.get(request_id)
    if not leave_request:
        print(f"Error: Leave request with ID {request_id} not found")
        return
    
    approver = User.query.get(approver_id)
    if not approver or not approver.can_approve_requests():
        print(f"Error: User {approver_id} cannot approve requests")
        return
    
    leave_request.reject(approver_id, reason)
    db.session.commit()
    print(f'Leave request {request_id} rejected by {approver.username}')

app.cli.add_command(leave_cli)

'''
Swap Request Commands
'''

swap_cli = AppGroup('swap', help='Shift swap management commands')

@swap_cli.command("create", help="Creates a shift swap request")
@click.argument("shift_id", type=int)
@click.argument("from_user_id", type=int)
@click.argument("to_user_id", type=int)
@click.option("--note", help="Note for swap request")
def create_swap_command(shift_id, from_user_id, to_user_id, note):
    try:
        shift = Shift.query.get(shift_id)
        if not shift:
            print(f"Error: Shift with ID {shift_id} not found")
            return
        
        if shift.user_id != from_user_id:
            print(f"Error: Shift {shift_id} is not assigned to user {from_user_id}")
            return
        
        from_user = User.query.get(from_user_id)
        to_user = User.query.get(to_user_id)
        
        if not from_user or not to_user:
            print("Error: One or both users not found")
            return
        
        swap_request = SwapRequest(shift_id, from_user_id, to_user_id, note)
        db.session.add(swap_request)
        db.session.commit()
        print(f'Swap request created: {from_user.username} -> {to_user.username} for shift {shift_id}')
    except Exception as e:
        print(f'Error creating swap request: {e}')

@swap_cli.command("list", help="Lists swap requests")
@click.option("--status", help="Filter by status")
def list_swap_command(status):
    query = SwapRequest.query
    
    if status:
        query = query.filter_by(status=status)
    
    requests = query.all()
    
    if not requests:
        print("No swap requests found")
        return
    
    print(header_msg("SHIFT SWAP REQUESTS"))
    print_separator()
    
    headers = ["ID", "SHIFT DETAILS", "FROM", "TO", "STATUS", "APPROVER"]
    widths = [4, 35, 18, 18, 18, 20]
    
    print_table_header(headers, widths)
    
    for req in requests:
        from_user = User.query.get(req.from_user_id)
        to_user = User.query.get(req.to_user_id)
        shift = Shift.query.get(req.shift_id)
        approver = User.query.get(req.approver_id) if req.approver_id else None
        
        status_color = Colors.WARNING if req.status == 'pending' else Colors.OKGREEN if req.status == 'approved' else Colors.FAIL
        
        shift_details = f"{shift.work_date} {shift.start_time}-{shift.end_time}"
        
        values = [
            str(req.id),
            shift_details,
            from_user.username,
            to_user.username,
            req.status.upper(),
            approver.username if approver else 'None'
        ]
        
        colors = [Colors.OKCYAN, Colors.ENDC, Colors.FAIL, Colors.OKGREEN, status_color, Colors.ENDC]
        print_table_row(values, widths, colors)
    
    print_table_footer(widths)
    print(f"\n{info_msg(f'Total swap requests: {len(requests)}')}")

@swap_cli.command("approve", help="Approves a swap request")
@click.argument("request_id", type=int)
@click.argument("approver_id", type=int)
def approve_swap_command(request_id, approver_id):
    swap_request = SwapRequest.query.get(request_id)
    if not swap_request:
        print(f"Error: Swap request with ID {request_id} not found")
        return
    
    approver = User.query.get(approver_id)
    if not approver or not approver.can_approve_requests():
        print(f"Error: User {approver_id} cannot approve requests")
        return
    
    swap_request.approve(approver_id)
    print(f'Swap request {request_id} approved by {approver.username}')

app.cli.add_command(swap_cli)

'''
Time Log Commands
'''

timelog_cli = AppGroup('timelog', help='Time logging commands')

@timelog_cli.command("clockin", help="Clock in to a shift")
@click.argument("shift_id", type=int)
@click.argument("user_id", type=int)
def clockin_command(shift_id, user_id):
    try:
        shift = Shift.query.get(shift_id)
        if not shift:
            print(f"Error: Shift with ID {shift_id} not found")
            return
        
        if shift.user_id != user_id:
            print(f"Error: Shift {shift_id} is not assigned to user {user_id}")
            return
        
        # Check if user is already clocked in for this shift
        existing_log = TimeLog.query.filter_by(shift_id=shift_id, user_id=user_id, clock_out=None).first()
        if existing_log:
            print("Error: User is already clocked in for this shift")
            return
        
        time_log = TimeLog(shift_id, user_id)
        db.session.add(time_log)
        db.session.commit()
        print(f'User {user_id} clocked in to shift {shift_id} at {time_log.clock_in}')
    except Exception as e:
        print(f'Error clocking in: {e}')

@timelog_cli.command("clockout", help="Clock out from a shift")
@click.argument("shift_id", type=int)
@click.argument("user_id", type=int)
def clockout_command(shift_id, user_id):
    try:
        time_log = TimeLog.query.filter_by(shift_id=shift_id, user_id=user_id, clock_out=None).first()
        if not time_log:
            print("Error: No open time log found for this shift and user")
            return
        
        success, message = time_log.clock_out_now()
        print(message)
        if success:
            print(f'Worked duration: {time_log.get_duration_string()}')
    except Exception as e:
        print(f'Error clocking out: {e}')

@timelog_cli.command("list", help="Lists time logs")
@click.option("--user-id", type=int, help="Filter by user ID")
@click.option("--shift-id", type=int, help="Filter by shift ID")
@click.option("--open-only", is_flag=True, help="Show only open time logs")
def list_timelog_command(user_id, shift_id, open_only):
    query = TimeLog.query
    
    if user_id:
        query = query.filter_by(user_id=user_id)
    if shift_id:
        query = query.filter_by(shift_id=shift_id)
    if open_only:
        query = query.filter_by(clock_out=None)
    
    logs = query.all()
    
    if not logs:
        print("No time logs found")
        return
    
    print(header_msg("TIME LOGS"))
    print_separator()
    
    headers = ["ID", "EMPLOYEE", "DATE", "CLOCK IN", "DURATION", "STATUS"]
    widths = [4, 20, 16, 15, 18, 15]
    
    print_table_header(headers, widths)
    
    for log in logs:
        user = User.query.get(log.user_id)
        shift = Shift.query.get(log.shift_id)
        status = "🔓 Open" if log.is_open() else "🔒 Closed"
        status_color = Colors.WARNING if log.is_open() else Colors.OKGREEN
        
        clock_in_time = log.clock_in.strftime('%H:%M') if log.clock_in else 'N/A'
        
        values = [
            str(log.id),
            user.username,
            str(shift.work_date),
            clock_in_time,
            log.get_duration_string(),
            status
        ]
        
        colors = [Colors.OKCYAN, Colors.ENDC, Colors.ENDC, Colors.ENDC, Colors.OKBLUE, status_color]
        print_table_row(values, widths, colors)
    
    print_table_footer(widths)
    print(f"\n{info_msg(f'Total time logs: {len(logs)}')}")

app.cli.add_command(timelog_cli)

'''
Roster Commands
'''

roster_cli = AppGroup('roster', help='Roster management commands')

@roster_cli.command("view", help="View roster for a date range")
@click.argument("start_date")  # YYYY-MM-DD format
@click.argument("end_date")  # YYYY-MM-DD format
def view_roster_command(start_date, end_date):
    try:
        print(header_msg("STAFF ROSTER"))
        start = datetime.strptime(start_date, '%Y-%m-%d').date()
        end = datetime.strptime(end_date, '%Y-%m-%d').date()
        
        print(f"{Colors.OKCYAN}📅 Period: {start_date} to {end_date} ({(end-start).days + 1} days){Colors.ENDC}")
        print_separator()
        
        shifts = Shift.query.filter(
            Shift.work_date >= start,
            Shift.work_date <= end
        ).order_by(Shift.work_date, Shift.start_time).all()
        
        if not shifts:
            print(warning_msg(f"No shifts scheduled between {start_date} and {end_date}"))
            return
        
        current_date = None
        day_count = 0
        
        for shift in shifts:
            if current_date != shift.work_date:
                current_date = shift.work_date
                day_count += 1
                
                # Day header with emoji for day of week
                day_emoji = {
                    'Monday': '💼', 'Tuesday': '📋', 'Wednesday': '⚡', 
                    'Thursday': '📊', 'Friday': '🎯', 'Saturday': '🌟', 'Sunday': '🔔'
                }
                day_name = current_date.strftime('%A')
                emoji = day_emoji.get(day_name, '📅')
                
                print(f"\n{Colors.BOLD}{Colors.HEADER}{emoji} {current_date} - {day_name}{Colors.ENDC}")
                print(f"{Colors.OKCYAN}{'─' * 60}{Colors.ENDC}")
            
            user = User.query.get(shift.user_id)
            
            # Role badges
            role_badge = {'admin': '👑', 'supervisor': '⭐', 'staff': '👤'}
            badge = role_badge.get(user.role, '👤')
            
            # Status indicators
            status_indicator = {'scheduled': '⏰', 'completed': '✅', 'cancelled': '❌'}
            indicator = status_indicator.get(shift.status, '❓')
            
            # Time formatting
            duration = shift.duration_hours()
            duration_color = Colors.OKGREEN if duration <= 8 else Colors.WARNING if duration <= 10 else Colors.FAIL
            
            print(f"  {indicator} {Colors.BOLD}{shift.start_time} - {shift.end_time}{Colors.ENDC} "
                  f"{badge} {user.username} ({user.role}) "
                  f"{duration_color}[{duration:.1f}h]{Colors.ENDC}")
        
        print_separator()
        
        # Summary statistics
        total_hours = sum(shift.duration_hours() for shift in shifts)
        unique_staff = len(set(shift.user_id for shift in shifts))
        
        print(f"{Colors.BOLD}📊 SUMMARY:{Colors.ENDC}")
        print(f"   • Total Shifts: {len(shifts)}")
        print(f"   • Total Hours: {total_hours:.1f}h")
        print(f"   • Staff Members: {unique_staff}")
        print(f"   • Days with Coverage: {day_count}")
    
    except Exception as e:
        print(error_msg(f"Error viewing roster: {e}"))

@roster_cli.command("report", help="Generate weekly report")
@click.argument("start_date")  # YYYY-MM-DD format (start of week)
def weekly_report_command(start_date):
    try:
        start = datetime.strptime(start_date, '%Y-%m-%d').date()
        end = start + timedelta(days=6)  # End of week
        
        print(header_msg("📊 WEEKLY PERFORMANCE REPORT"))
        print(f"{Colors.OKCYAN}📅 Week of {start} to {end}{Colors.ENDC}")
        print_separator()
        
        # Get all shifts for the week
        shifts = Shift.query.filter(
            Shift.work_date >= start,
            Shift.work_date <= end
        ).all()
        
        # Get all time logs for the week
        time_logs = TimeLog.query.join(Shift).filter(
            Shift.work_date >= start,
            Shift.work_date <= end
        ).all()
        
        if not shifts:
            print(warning_msg("No shifts found for this week"))
            return
        
        # Calculate statistics by user
        user_stats = {}
        total_scheduled = 0
        total_worked = 0
        
        for shift in shifts:
            user_id = shift.user_id
            if user_id not in user_stats:
                user_stats[user_id] = {
                    'scheduled_hours': 0,
                    'worked_hours': 0,
                    'shifts_count': 0,
                    'completed_shifts': 0
                }
            
            hours = shift.duration_hours()
            user_stats[user_id]['scheduled_hours'] += hours
            user_stats[user_id]['shifts_count'] += 1
            total_scheduled += hours
            
            if shift.status == 'completed':
                user_stats[user_id]['completed_shifts'] += 1
        
        for log in time_logs:
            user_id = log.user_id
            if user_id in user_stats:
                hours = log.worked_hours()
                user_stats[user_id]['worked_hours'] += hours
                total_worked += hours
        
        # Display performance table
        print(f"{Colors.BOLD}👥 STAFF PERFORMANCE{Colors.ENDC}")
        print()
        
        headers = ["EMPLOYEE", "ROLE", "SCHEDULED", "WORKED", "SHIFTS", "COMPLETION"]
        widths = [22, 20, 16, 16, 14, 25]
        
        print_table_header(headers, widths)
        
        for user_id, stats in user_stats.items():
            user = User.query.get(user_id)
            completion_rate = (stats['completed_shifts'] / stats['shifts_count'] * 100) if stats['shifts_count'] > 0 else 0
            
            # Performance indicators
            if completion_rate >= 90:
                perf_color = Colors.OKGREEN
                perf_icon = " 🌟"
            elif completion_rate >= 70:
                perf_color = Colors.WARNING
                perf_icon = " ⚡"
            else:
                perf_color = Colors.FAIL
                perf_icon = " ⚠️"
            
            role_badge = {'admin': '👑', 'supervisor': '⭐', 'staff': '👤'}
            badge = role_badge.get(user.role, '👤')
            
            values = [
                user.username,
                f"{badge} {user.role}",
                f"{stats['scheduled_hours']:.1f}h",
                f"{stats['worked_hours']:.1f}h",
                str(stats['shifts_count']),
                f"{completion_rate:.1f}%{perf_icon}"
            ]
            
            colors = [Colors.ENDC, Colors.ENDC, Colors.OKCYAN, Colors.OKBLUE, Colors.ENDC, perf_color]
            print_table_row(values, widths, colors)
        
        print_table_footer(widths)
        
        # Summary statistics
        print(f"\n{Colors.BOLD}📈 WEEK SUMMARY{Colors.ENDC}")
        print_separator("─", 40)
        
        efficiency = (total_worked / total_scheduled * 100) if total_scheduled > 0 else 0
        efficiency_icon = "🎯" if efficiency >= 90 else "📊" if efficiency >= 80 else "📉"
        
        print(f"📋 Total Shifts Scheduled: {len(shifts)}")
        print(f"⏰ Total Scheduled Hours: {total_scheduled:.1f}h")
        print(f"✅ Total Worked Hours: {total_worked:.1f}h")
        print(f"📊 Overall Efficiency: {efficiency:.1f}% {efficiency_icon}")
        print(f"👥 Active Staff Members: {len(user_stats)}")
        
        # Leave requests summary
        leave_requests = LeaveRequest.query.filter(
            LeaveRequest.start_date <= end,
            LeaveRequest.end_date >= start
        ).all()
        
        if leave_requests:
            print(f"\n{Colors.BOLD}🏖️  LEAVE REQUESTS{Colors.ENDC}")
            print_separator("─", 60)
            
            status_icons = {'pending': '⏳', 'approved': '✅', 'rejected': '❌'}
            
            for req in leave_requests:
                user = User.query.get(req.requester_id)
                icon = status_icons.get(req.status, '❓')
                status_color = Colors.WARNING if req.status == 'pending' else Colors.OKGREEN if req.status == 'approved' else Colors.FAIL
                
                print(f"{icon} {user.username}: {req.type.upper()} "
                      f"({req.start_date} to {req.end_date}) - "
                      f"{status_color}{req.status.upper()}{Colors.ENDC}")
        
        # Recommendations
        print(f"\n{Colors.BOLD}💡 RECOMMENDATIONS{Colors.ENDC}")
        print_separator("─", 50)
        
        if efficiency < 80:
            print(f"{Colors.WARNING}⚠️  Consider reviewing scheduling efficiency{Colors.ENDC}")
        if len([s for s in user_stats.values() if (s['completed_shifts'] / s['shifts_count'] * 100) < 70]) > 0:
            print(f"{Colors.WARNING}⚠️  Some staff members have low completion rates{Colors.ENDC}")
        if efficiency >= 95:
            print(f"{Colors.OKGREEN}🌟 Excellent week! Team is performing at optimal levels{Colors.ENDC}")
    
    except Exception as e:
        print(error_msg(f"Error generating report: {e}"))

app.cli.add_command(roster_cli)