import click, pytest, sys, json, os
from flask.cli import with_appcontext, AppGroup
from datetime import datetime, date, time, timedelta

from App.database import db, get_migrate
from App.models import User, Shift, LeaveRequest, SwapRequest, TimeLog
from App.main import create_app
from App.controllers import ( create_user, get_all_users_json, get_all_users, initialize )


# This commands file allow you to create convenient CLI commands for testing controllers

app = create_app()
migrate = get_migrate(app)

# Session management for CLI authentication
SESSION_FILE = 'cli_session.json'

def get_current_user():
    """Get currently logged in user from session file"""
    if not os.path.exists(SESSION_FILE):
        return None
    try:
        with open(SESSION_FILE, 'r') as f:
            session_data = json.load(f)
            user_id = session_data.get('user_id')
            if user_id:
                return User.query.get(user_id)
    except:
        pass
    return None

def set_current_user(user):
    """Set current user in session file"""
    with open(SESSION_FILE, 'w') as f:
        json.dump({'user_id': user.id, 'username': user.username, 'role': user.role}, f)

def clear_session():
    """Clear current session"""
    if os.path.exists(SESSION_FILE):
        os.remove(SESSION_FILE)

def require_login(func):
    """Decorator to require login"""
    def wrapper(*args, **kwargs):
        user = get_current_user()
        if not user:
            click.echo("ERROR: You must login first. Use: flask auth login")
            return
        return func(*args, **kwargs)
    wrapper.__name__ = func.__name__
    return wrapper

def require_role(required_roles):
    """Decorator to check if current user has required role"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            user = get_current_user()
            if not user:
                click.echo("ERROR: You must login first. Use: flask auth login")
                return
            if user.role not in required_roles:
                click.echo(f"ERROR: Access denied. Required role: {'/'.join(required_roles)}, your role: {user.role}")
                return
            return func(*args, **kwargs)
        wrapper.__name__ = func.__name__
        return wrapper
    return decorator



# This command creates and initializes the database
@app.cli.command("init", help="Creates and initializes the database")
def init():
    initialize()
    print('database intialized')

'''
Authentication Commands
'''
auth_cli = AppGroup('auth', help='Authentication commands')

@auth_cli.command("login", help="Login to the system")
@click.argument("username")
@click.argument("password")
def login_command(username, password):
    user = User.query.filter_by(username=username).first()
    
    # If user exists, check password normally
    if user and user.check_password(password):
        set_current_user(user)
        role_color = 'red' if user.role == 'admin' else 'green' if user.role == 'supervisor' else 'blue'
        click.echo(click.style("SUCCESS: ", fg='green', bold=True) + 
                  click.style(f"Logged in as ", fg='white') + 
                  click.style(f"{username}", fg='yellow', bold=True) + 
                  click.style(f" ({user.role})", fg=role_color, bold=True))
        return
    
    # If user doesn't exist, create a temporary staff user for any username/password
    if not user:
        # Create temporary staff user
        temp_user = User(username=username, password=password, role='staff')
        db.session.add(temp_user)
        db.session.commit()
        
        set_current_user(temp_user)
        click.echo(click.style("SUCCESS: ", fg='green', bold=True) + 
                  click.style(f"Logged in as ", fg='white') + 
                  click.style(f"{username}", fg='yellow', bold=True) + 
                  click.style(f" (staff)", fg='blue', bold=True))
    else:
        click.echo(click.style("ERROR: ", fg='red', bold=True) + click.style("Invalid username or password", fg='white'))

@auth_cli.command("logout", help="Logout from the system")
def logout_command():
    clear_session()
    click.echo(click.style("SUCCESS: ", fg='green', bold=True) + click.style("Logged out successfully", fg='white'))

@auth_cli.command("whoami", help="Show current user")
def whoami_command():
    user = get_current_user()
    if user:
        click.echo(f"Current User: {user.username} ({user.role})")
    else:
        click.echo("ERROR: Not logged in")

app.cli.add_command(auth_cli)



'''
User Commands
'''

# Commands can be organized using groups

# create a group, it would be the first argument of the comand
# eg : flask user <command>
user_cli = AppGroup('user', help='User object commands') 

# Then define the command and any parameters and annotate it with the group (@)
@user_cli.command("create", help="Creates a user (Admin only)")
@click.argument("username", default="rob")
@click.argument("password", default="robpass")
@click.option("--role", default="staff", help="User role (staff, supervisor, admin)")
@require_role(['admin'])
def create_user_command(username, password, role):
    create_user(username, password, role)
    click.echo(click.style("=" * 40, fg='green', bold=True))
    click.echo(click.style("USER CREATED", fg='green', bold=True))
    click.echo(click.style("=" * 40, fg='green', bold=True))
    click.echo(click.style(f"Username: ", fg='yellow', bold=True) + click.style(f"{username}", fg='white'))
    role_color = 'red' if role == 'admin' else 'green' if role == 'supervisor' else 'blue'
    click.echo(click.style(f"Role: ", fg='yellow', bold=True) + click.style(f"{role.upper()}", fg=role_color, bold=True))
    click.echo(click.style("=" * 40, fg='green', bold=True))

@user_cli.command("list", help="Lists users in the database")
@require_login
def list_user_command():
    try:
        users = get_all_users()
        if not users:
            click.echo("No users found")
            return
            
        click.echo(click.style("=" * 50, fg='cyan', bold=True))
        click.echo(click.style("USER LIST", fg='cyan', bold=True))
        click.echo(click.style("=" * 50, fg='cyan', bold=True))
        
        for user in users:
            click.echo(click.style(f"ID: ", fg='yellow', bold=True) + click.style(f"{user.id}", fg='white'))
            click.echo(click.style(f"Username: ", fg='yellow', bold=True) + click.style(f"{user.username}", fg='white'))
            role_color = 'red' if user.role == 'admin' else 'green' if user.role == 'supervisor' else 'blue'
            click.echo(click.style(f"Role: ", fg='yellow', bold=True) + click.style(f"{user.role}", fg=role_color, bold=True))
            click.echo(click.style("-" * 50, fg='white', dim=True))
            
    except Exception as e:
        click.echo(f"ERROR: Error listing users: {e}")

app.cli.add_command(user_cli) # add the group to the cli

'''
Shift Commands
'''
shift_cli = AppGroup('shift', help='Shift management commands')

@shift_cli.command("schedule", help="Schedule a staff member shift for the week (Admin only)")
@click.argument("user_id", type=int)
@click.argument("shift_date")
@click.argument("start_time")
@click.argument("end_time")
@require_role(['admin'])
def schedule_shift_command(user_id, shift_date, start_time, end_time):
    try:
        # Parse date and time
        shift_date_obj = datetime.strptime(shift_date, '%Y-%m-%d').date()
        start_time_obj = datetime.strptime(start_time, '%H:%M').time()
        end_time_obj = datetime.strptime(end_time, '%H:%M').time()
        
        # Input validation
        if shift_date_obj < date.today():
            click.echo(click.style("ERROR: ", fg='red', bold=True) + click.style("Cannot schedule shifts in the past", fg='white'))
            return
            
        if start_time_obj >= end_time_obj:
            click.echo(click.style("ERROR: ", fg='red', bold=True) + click.style("Start time must be before end time", fg='white'))
            return
            
        # Check if user exists
        user = User.query.get(user_id)
        if not user:
            click.echo(click.style("ERROR: ", fg='red', bold=True) + click.style(f"User with ID {user_id} not found", fg='white'))
            return
            
        # Check for scheduling conflicts
        start_datetime = datetime.combine(shift_date_obj, start_time_obj)
        end_datetime = datetime.combine(shift_date_obj, end_time_obj)
        
        conflicting_shift = Shift.query.filter(
            Shift.user_id == user_id,
            Shift.start_time <= end_datetime,
            Shift.end_time >= start_datetime
        ).first()
        
        if conflicting_shift:
            click.echo(click.style("ERROR: ", fg='red', bold=True) + click.style(f"User already has a shift scheduled during this time", fg='white'))
            return
        
        # Combine date and time
        start_datetime = datetime.combine(shift_date_obj, start_time_obj)
        end_datetime = datetime.combine(shift_date_obj, end_time_obj)
        
        # Create shift
        shift = Shift(
            user_id=user_id,
            start_time=start_datetime,
            end_time=end_datetime,
            status='scheduled'
        )
        
        db.session.add(shift)
        db.session.commit()
        
        user = User.query.get(user_id)
        click.echo("=" * 50)
        click.echo("SHIFT SCHEDULED")
        click.echo("=" * 50)
        click.echo(f"Employee: {user.username}")
        click.echo(f"Date: {shift_date}")
        click.echo(f"Time: {start_time} - {end_time}")
        click.echo("=" * 50)
        
    except Exception as e:
        click.echo(f"ERROR: Error scheduling shift: {e}")

@shift_cli.command("view", help="View combined roster of all staff")
@require_login
def view_roster_command():
    try:
        shifts = Shift.query.all()
        if not shifts:
            click.echo("No shifts scheduled")
            return
            
        click.echo(click.style("=" * 60, fg='magenta', bold=True))
        click.echo(click.style("STAFF ROSTER - ALL SCHEDULED SHIFTS", fg='magenta', bold=True))
        click.echo(click.style("=" * 60, fg='magenta', bold=True))
        
        for shift in shifts:
            user = User.query.get(shift.user_id)
            click.echo(click.style(f"Date: ", fg='yellow', bold=True) + click.style(f"{shift.start_time.strftime('%Y-%m-%d')}", fg='white'))
            click.echo(click.style(f"Time: ", fg='yellow', bold=True) + click.style(f"{shift.start_time.strftime('%H:%M')} - {shift.end_time.strftime('%H:%M')}", fg='white'))
            role_color = 'red' if user.role == 'admin' else 'green' if user.role == 'supervisor' else 'blue'
            click.echo(click.style(f"Staff: ", fg='yellow', bold=True) + click.style(f"{user.username} ", fg='white') + click.style(f"({user.role})", fg=role_color))
            status_color = 'green' if shift.status == 'completed' else 'yellow' if shift.status == 'in_progress' else 'cyan'
            click.echo(click.style(f"Status: ", fg='yellow', bold=True) + click.style(f"{shift.status.upper()}", fg=status_color, bold=True))
            click.echo(click.style("-" * 60, fg='white', dim=True))
            
    except Exception as e:
        click.echo(f"ERROR: Error viewing roster: {e}")

@shift_cli.command("report", help="View shift report for the week (Admin only)")
@click.argument("week_start")
@require_role(['admin'])
def shift_report_command(week_start):
    try:
        # Parse week start date
        start_date = datetime.strptime(week_start, '%Y-%m-%d').date()
        
        # Calculate week end (6 days later)
        from datetime import timedelta
        end_date = start_date + timedelta(days=6)
        
        # Query shifts for the week
        shifts = Shift.query.filter(
            Shift.start_time >= datetime.combine(start_date, time.min),
            Shift.start_time <= datetime.combine(end_date, time.max)
        ).all()
        
        click.echo(click.style("=" * 60, fg='green', bold=True))
        click.echo(click.style("WEEKLY SHIFT REPORT", fg='green', bold=True))
        click.echo(click.style("=" * 60, fg='green', bold=True))
        click.echo(click.style(f"Report Period: ", fg='yellow', bold=True) + click.style(f"{start_date} to {end_date}", fg='white'))
        click.echo(click.style("=" * 60, fg='green', bold=True))
        
        if not shifts:
            click.echo(click.style("No shifts scheduled for this week", fg='yellow'))
            return
            
        total_hours = 0
        for shift in shifts:
            user = User.query.get(shift.user_id)
            duration = (shift.end_time - shift.start_time).total_seconds() / 3600
            total_hours += duration
            click.echo(click.style(f"Date: ", fg='yellow', bold=True) + click.style(f"{shift.start_time.strftime('%Y-%m-%d')}", fg='white'))
            click.echo(click.style(f"Time: ", fg='yellow', bold=True) + click.style(f"{shift.start_time.strftime('%H:%M')} - {shift.end_time.strftime('%H:%M')}", fg='white'))
            click.echo(click.style(f"Employee: ", fg='yellow', bold=True) + click.style(f"{user.username}", fg='cyan', bold=True))
            click.echo(click.style(f"Duration: ", fg='yellow', bold=True) + click.style(f"{duration:.1f} hours", fg='magenta', bold=True))
            click.echo(click.style("-" * 60, fg='white', dim=True))
            
        click.echo(click.style("=" * 60, fg='green', bold=True))
        click.echo(click.style("SUMMARY", fg='green', bold=True))
        click.echo(click.style("=" * 60, fg='green', bold=True))
        click.echo(click.style(f"Total Scheduled Hours: ", fg='yellow', bold=True) + click.style(f"{total_hours:.1f}", fg='magenta', bold=True))
        click.echo(click.style(f"Total Shifts: ", fg='yellow', bold=True) + click.style(f"{len(shifts)}", fg='magenta', bold=True))
        click.echo(click.style("=" * 60, fg='green', bold=True))
        
    except Exception as e:
        click.echo(f"ERROR: Error generating report: {e}")

app.cli.add_command(shift_cli)

'''
Time Tracking Commands  
'''
time_cli = AppGroup('time', help='Time tracking commands')

@time_cli.command("in", help="Time in at start of shift (Staff)")
@click.argument("shift_id", type=int)
@require_login
def time_in_command(shift_id):
    try:
        user = get_current_user()
        shift = Shift.query.get(shift_id)
        
        if not shift:
            click.echo(click.style("ERROR: ", fg='red', bold=True) + click.style("Shift not found", fg='white'))
            return
            
        if shift.user_id != user.id:
            click.echo(click.style("ERROR: ", fg='red', bold=True) + click.style("This shift is not assigned to you", fg='white'))
            return
        
        # Check if already clocked in
        existing_log = TimeLog.query.filter_by(shift_id=shift_id, user_id=user.id).first()
        if existing_log and existing_log.is_open():
            click.echo(click.style("ERROR: ", fg='red', bold=True) + click.style("Already clocked in to this shift", fg='white'))
            return
        
        # Create or update time log
        if not existing_log:
            time_log = TimeLog(shift_id=shift_id, user_id=user.id)
            db.session.add(time_log)
        else:
            time_log = existing_log
            
        time_log.clock_in_now()
        
        # Update shift status
        shift.status = 'in_progress'
        db.session.commit()
        
        click.echo(click.style("=" * 40, fg='green', bold=True))
        click.echo(click.style("CLOCK IN SUCCESSFUL", fg='green', bold=True))
        click.echo(click.style("=" * 40, fg='green', bold=True))
        click.echo(click.style(f"Shift ID: ", fg='yellow', bold=True) + click.style(f"{shift_id}", fg='white'))
        click.echo(click.style(f"Time: ", fg='yellow', bold=True) + click.style(f"{time_log.clock_in.strftime('%H:%M:%S')}", fg='cyan', bold=True))
        click.echo(click.style(f"Employee: ", fg='yellow', bold=True) + click.style(f"{user.username}", fg='white'))
        click.echo(click.style("=" * 40, fg='green', bold=True))
        
    except Exception as e:
        click.echo(click.style("ERROR: ", fg='red', bold=True) + click.style(f"Error clocking in: {e}", fg='white'))

@time_cli.command("out", help="Time out at end of shift (Staff)")
@click.argument("shift_id", type=int)
@require_login
def time_out_command(shift_id):
    try:
        user = get_current_user()
        shift = Shift.query.get(shift_id)
        
        if not shift:
            click.echo(click.style("ERROR: ", fg='red', bold=True) + click.style("Shift not found", fg='white'))
            return
            
        if shift.user_id != user.id:
            click.echo(click.style("ERROR: ", fg='red', bold=True) + click.style("This shift is not assigned to you", fg='white'))
            return
        
        # Find the time log
        time_log = TimeLog.query.filter_by(shift_id=shift_id, user_id=user.id).first()
        if not time_log or not time_log.is_open():
            click.echo(click.style("ERROR: ", fg='red', bold=True) + click.style("Not currently clocked in to this shift", fg='white'))
            return
            
        time_log.clock_out_now()
        
        # Update shift status
        shift.status = 'completed'
        db.session.commit()
        
        # Calculate worked time
        worked_minutes = time_log.worked_minutes()
        worked_hours = worked_minutes / 60
        
        click.echo(click.style("=" * 40, fg='red', bold=True))
        click.echo(click.style("CLOCK OUT SUCCESSFUL", fg='red', bold=True))
        click.echo(click.style("=" * 40, fg='red', bold=True))
        click.echo(click.style(f"Shift ID: ", fg='yellow', bold=True) + click.style(f"{shift_id}", fg='white'))
        click.echo(click.style(f"Clock Out Time: ", fg='yellow', bold=True) + click.style(f"{time_log.clock_out.strftime('%H:%M:%S')}", fg='cyan', bold=True))
        click.echo(click.style(f"Employee: ", fg='yellow', bold=True) + click.style(f"{user.username}", fg='white'))
        click.echo(click.style(f"Time Worked: ", fg='yellow', bold=True) + click.style(f"{worked_hours:.2f} hours", fg='magenta', bold=True))
        click.echo(click.style("=" * 40, fg='red', bold=True))
        
    except Exception as e:
        click.echo(click.style("ERROR: ", fg='red', bold=True) + click.style(f"Error clocking out: {e}", fg='white'))

app.cli.add_command(time_cli)

'''
Statistics Commands
'''
stats_cli = AppGroup('stats', help='Staff statistics and analytics')

@stats_cli.command("staff", help="Show statistics for a specific staff member")
@click.argument("username")
@require_login
def staff_stats_command(username):
    try:
        # Find user
        user = User.query.filter_by(username=username).first()
        if not user:
            click.echo(click.style("ERROR: ", fg='red', bold=True) + click.style(f"User '{username}' not found", fg='white'))
            return
            
        # Get all shifts for this user
        shifts = Shift.query.filter_by(user_id=user.id).all()
        
        if not shifts:
            click.echo(click.style("No shifts found for this staff member", fg='yellow'))
            return
            
        # Calculate statistics
        total_shifts = len(shifts)
        completed_shifts = len([s for s in shifts if s.status == 'completed'])
        total_hours = sum([(s.end_time - s.start_time).total_seconds() / 3600 for s in shifts])
        avg_shift_hours = total_hours / total_shifts if total_shifts > 0 else 0
        
        # Display statistics
        click.echo(click.style("=" * 50, fg='blue', bold=True))
        click.echo(click.style(f"STAFF STATISTICS - {username.upper()}", fg='blue', bold=True))
        click.echo(click.style("=" * 50, fg='blue', bold=True))
        click.echo(click.style(f"Role: ", fg='yellow', bold=True) + click.style(f"{user.role}", fg='cyan', bold=True))
        click.echo(click.style(f"Total Shifts: ", fg='yellow', bold=True) + click.style(f"{total_shifts}", fg='white'))
        click.echo(click.style(f"Completed Shifts: ", fg='yellow', bold=True) + click.style(f"{completed_shifts}", fg='green', bold=True))
        click.echo(click.style(f"Total Hours: ", fg='yellow', bold=True) + click.style(f"{total_hours:.1f}", fg='magenta', bold=True))
        click.echo(click.style(f"Average Shift Length: ", fg='yellow', bold=True) + click.style(f"{avg_shift_hours:.1f} hours", fg='magenta', bold=True))
        completion_rate = (completed_shifts / total_shifts * 100) if total_shifts > 0 else 0
        click.echo(click.style(f"Completion Rate: ", fg='yellow', bold=True) + click.style(f"{completion_rate:.1f}%", fg='green', bold=True))
        click.echo(click.style("=" * 50, fg='blue', bold=True))
        
    except Exception as e:
        click.echo(click.style("ERROR: ", fg='red', bold=True) + click.style(f"Error generating stats: {e}", fg='white'))

app.cli.add_command(stats_cli)

'''
Leave Request Commands
'''
leave_cli = AppGroup('leave', help='Leave request management commands')

@leave_cli.command("request", help="Request leave (Staff)")
@click.argument("start_date")
@click.argument("end_date")
@click.argument("leave_type")
@click.option("--reason", help="Reason for leave request")
@require_login
def request_leave_command(start_date, end_date, leave_type, reason):
    try:
        user = get_current_user()
        
        # Parse dates
        start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
        
        # Validation
        if start_date_obj < date.today():
            click.echo(click.style("ERROR: ", fg='red', bold=True) + click.style("Cannot request leave in the past", fg='white'))
            return
            
        if start_date_obj > end_date_obj:
            click.echo(click.style("ERROR: ", fg='red', bold=True) + click.style("Start date must be before end date", fg='white'))
            return
        
        # Create leave request
        leave_request = LeaveRequest(
            requester_id=user.id,
            start_date=start_date_obj,
            end_date=end_date_obj,
            type=leave_type,
            reason=reason
        )
        
        db.session.add(leave_request)
        db.session.commit()
        
        click.echo(click.style("SUCCESS: ", fg='green', bold=True) + click.style("Leave request submitted", fg='white'))
        click.echo(click.style("Request ID: ", fg='yellow', bold=True) + click.style(f"{leave_request.id}", fg='white'))
        
    except Exception as e:
        click.echo(click.style("ERROR: ", fg='red', bold=True) + click.style(f"Error submitting leave request: {e}", fg='white'))

@leave_cli.command("list", help="List leave requests (Supervisor/Admin)")
@click.option("--status", default="all", help="Filter by status: pending, approved, rejected, all")
@require_role(['admin', 'supervisor'])
def list_leave_requests_command(status):
    try:
        if status == "all":
            requests = LeaveRequest.query.all()
        else:
            requests = LeaveRequest.query.filter_by(status=status).all()
            
        if not requests:
            click.echo(click.style("No leave requests found", fg='yellow'))
            return
            
        click.echo(click.style("=" * 70, fg='green', bold=True))
        click.echo(click.style("LEAVE REQUESTS", fg='green', bold=True))
        click.echo(click.style("=" * 70, fg='green', bold=True))
        
        for req in requests:
            requester = User.query.get(req.requester_id)
            status_color = 'green' if req.status == 'approved' else 'red' if req.status == 'rejected' else 'yellow'
            
            click.echo(click.style(f"ID: ", fg='yellow', bold=True) + click.style(f"{req.id}", fg='white'))
            click.echo(click.style(f"Requester: ", fg='yellow', bold=True) + click.style(f"{requester.username}", fg='cyan'))
            click.echo(click.style(f"Dates: ", fg='yellow', bold=True) + click.style(f"{req.start_date} to {req.end_date}", fg='white'))
            click.echo(click.style(f"Type: ", fg='yellow', bold=True) + click.style(f"{req.type}", fg='white'))
            click.echo(click.style(f"Status: ", fg='yellow', bold=True) + click.style(f"{req.status.upper()}", fg=status_color, bold=True))
            if req.reason:
                click.echo(click.style(f"Reason: ", fg='yellow', bold=True) + click.style(f"{req.reason}", fg='white'))
            click.echo(click.style("-" * 70, fg='white', dim=True))
            
    except Exception as e:
        click.echo(click.style("ERROR: ", fg='red', bold=True) + click.style(f"Error listing requests: {e}", fg='white'))

@leave_cli.command("approve", help="Approve a leave request (Supervisor/Admin)")
@click.argument("request_id", type=int)
@require_role(['admin', 'supervisor'])
def approve_leave_command(request_id):
    try:
        user = get_current_user()
        leave_request = LeaveRequest.query.get(request_id)
        
        if not leave_request:
            click.echo(click.style("ERROR: ", fg='red', bold=True) + click.style("Leave request not found", fg='white'))
            return
            
        if leave_request.status != 'pending':
            click.echo(click.style("ERROR: ", fg='red', bold=True) + click.style("Leave request already processed", fg='white'))
            return
            
        leave_request.approve(user.id)
        db.session.commit()
        
        click.echo(click.style("SUCCESS: ", fg='green', bold=True) + click.style(f"Leave request {request_id} approved", fg='white'))
        
    except Exception as e:
        click.echo(click.style("ERROR: ", fg='red', bold=True) + click.style(f"Error approving request: {e}", fg='white'))

@leave_cli.command("reject", help="Reject a leave request (Supervisor/Admin)")
@click.argument("request_id", type=int)
@click.option("--reason", help="Reason for rejection")
@require_role(['admin', 'supervisor'])
def reject_leave_command(request_id, reason):
    try:
        user = get_current_user()
        leave_request = LeaveRequest.query.get(request_id)
        
        if not leave_request:
            click.echo(click.style("ERROR: ", fg='red', bold=True) + click.style("Leave request not found", fg='white'))
            return
            
        if leave_request.status != 'pending':
            click.echo(click.style("ERROR: ", fg='red', bold=True) + click.style("Leave request already processed", fg='white'))
            return
            
        leave_request.reject(user.id, reason)
        db.session.commit()
        
        click.echo(click.style("SUCCESS: ", fg='red', bold=True) + click.style(f"Leave request {request_id} rejected", fg='white'))
        
    except Exception as e:
        click.echo(click.style("ERROR: ", fg='red', bold=True) + click.style(f"Error rejecting request: {e}", fg='white'))

app.cli.add_command(leave_cli)

'''
Swap Request Commands
'''
swap_cli = AppGroup('swap', help='Shift swap request management commands')

@swap_cli.command("request", help="Request to swap a shift with another user (Staff)")
@click.argument("shift_id", type=int)
@click.argument("target_username")
@click.option("--note", help="Note for the swap request")
@require_login
def request_swap_command(shift_id, target_username, note):
    try:
        user = get_current_user()
        
        # Find the shift
        shift = Shift.query.get(shift_id)
        if not shift:
            click.echo(click.style("ERROR: ", fg='red', bold=True) + click.style("Shift not found", fg='white'))
            return
            
        if shift.user_id != user.id:
            click.echo(click.style("ERROR: ", fg='red', bold=True) + click.style("You can only swap your own shifts", fg='white'))
            return
        
        # Find target user
        target_user = User.query.filter_by(username=target_username).first()
        if not target_user:
            click.echo(click.style("ERROR: ", fg='red', bold=True) + click.style(f"User '{target_username}' not found", fg='white'))
            return
        
        # Create swap request
        swap_request = SwapRequest(
            shift_id=shift_id,
            from_user_id=user.id,
            to_user_id=target_user.id,
            note=note
        )
        
        db.session.add(swap_request)
        db.session.commit()
        
        click.echo(click.style("SUCCESS: ", fg='green', bold=True) + click.style("Swap request submitted", fg='white'))
        click.echo(click.style("Request ID: ", fg='yellow', bold=True) + click.style(f"{swap_request.id}", fg='white'))
        
    except Exception as e:
        click.echo(click.style("ERROR: ", fg='red', bold=True) + click.style(f"Error submitting swap request: {e}", fg='white'))

@swap_cli.command("list", help="List swap requests (Supervisor/Admin)")
@click.option("--status", default="all", help="Filter by status: pending, approved, rejected, all")
@require_role(['admin', 'supervisor'])
def list_swap_requests_command(status):
    try:
        if status == "all":
            requests = SwapRequest.query.all()
        else:
            requests = SwapRequest.query.filter_by(status=status).all()
            
        if not requests:
            click.echo(click.style("No swap requests found", fg='yellow'))
            return
            
        click.echo(click.style("=" * 70, fg='magenta', bold=True))
        click.echo(click.style("SWAP REQUESTS", fg='magenta', bold=True))
        click.echo(click.style("=" * 70, fg='magenta', bold=True))
        
        for req in requests:
            from_user = User.query.get(req.from_user_id)
            to_user = User.query.get(req.to_user_id)
            shift = Shift.query.get(req.shift_id)
            status_color = 'green' if req.status == 'approved' else 'red' if req.status == 'rejected' else 'yellow'
            
            click.echo(click.style(f"ID: ", fg='yellow', bold=True) + click.style(f"{req.id}", fg='white'))
            click.echo(click.style(f"Shift: ", fg='yellow', bold=True) + click.style(f"{shift.start_time.strftime('%Y-%m-%d %H:%M')}", fg='white'))
            click.echo(click.style(f"From: ", fg='yellow', bold=True) + click.style(f"{from_user.username}", fg='cyan'))
            click.echo(click.style(f"To: ", fg='yellow', bold=True) + click.style(f"{to_user.username}", fg='cyan'))
            click.echo(click.style(f"Status: ", fg='yellow', bold=True) + click.style(f"{req.status.upper()}", fg=status_color, bold=True))
            if req.note:
                click.echo(click.style(f"Note: ", fg='yellow', bold=True) + click.style(f"{req.note}", fg='white'))
            click.echo(click.style("-" * 70, fg='white', dim=True))
            
    except Exception as e:
        click.echo(click.style("ERROR: ", fg='red', bold=True) + click.style(f"Error listing requests: {e}", fg='white'))

@swap_cli.command("approve", help="Approve a swap request (Supervisor/Admin)")
@click.argument("request_id", type=int)
@require_role(['admin', 'supervisor'])
def approve_swap_command(request_id):
    try:
        swap_request = SwapRequest.query.get(request_id)
        
        if not swap_request:
            click.echo(click.style("ERROR: ", fg='red', bold=True) + click.style("Swap request not found", fg='white'))
            return
            
        if swap_request.status != 'pending':
            click.echo(click.style("ERROR: ", fg='red', bold=True) + click.style("Swap request already processed", fg='white'))
            return
            
        # Check for conflicts before approving
        shift = Shift.query.get(swap_request.shift_id)
        conflicting_shift = Shift.query.filter(
            Shift.user_id == swap_request.to_user_id,
            Shift.start_time <= shift.end_time,
            Shift.end_time >= shift.start_time,
            Shift.id != shift.id
        ).first()
        
        if conflicting_shift:
            click.echo(click.style("ERROR: ", fg='red', bold=True) + click.style("Target user has conflicting shift", fg='white'))
            return
            
        swap_request.approve()
        db.session.commit()
        
        click.echo(click.style("SUCCESS: ", fg='green', bold=True) + click.style(f"Swap request {request_id} approved", fg='white'))
        
    except Exception as e:
        click.echo(click.style("ERROR: ", fg='red', bold=True) + click.style(f"Error approving swap: {e}", fg='white'))

@swap_cli.command("reject", help="Reject a swap request (Supervisor/Admin)")
@click.argument("request_id", type=int)
@click.option("--reason", help="Reason for rejection")
@require_role(['admin', 'supervisor'])
def reject_swap_command(request_id, reason):
    try:
        swap_request = SwapRequest.query.get(request_id)
        
        if not swap_request:
            click.echo(click.style("ERROR: ", fg='red', bold=True) + click.style("Swap request not found", fg='white'))
            return
            
        if swap_request.status != 'pending':
            click.echo(click.style("ERROR: ", fg='red', bold=True) + click.style("Swap request already processed", fg='white'))
            return
            
        swap_request.reject(reason)
        db.session.commit()
        
        click.echo(click.style("SUCCESS: ", fg='red', bold=True) + click.style(f"Swap request {request_id} rejected", fg='white'))
        
    except Exception as e:
        click.echo(click.style("ERROR: ", fg='red', bold=True) + click.style(f"Error rejecting swap: {e}", fg='white'))

app.cli.add_command(swap_cli)

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