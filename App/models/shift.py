from datetime import datetime, date, time, timedelta
from App.database import db

class Shift(db.Model):
    __tablename__ = 'shifts'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    work_date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    status = db.Column(db.String(20), default='scheduled')  # scheduled, completed, cancelled
    
    # Relationships
    user = db.relationship('User', backref='shifts')
    time_logs = db.relationship('TimeLog', backref='shift', cascade='all, delete-orphan')
    swap_requests = db.relationship('SwapRequest', backref='shift', cascade='all, delete-orphan')
    
    def __init__(self, user_id, work_date, start_time, end_time, status='scheduled'):
        self.user_id = user_id
        self.work_date = work_date if isinstance(work_date, date) else datetime.strptime(work_date, '%Y-%m-%d').date()
        self.start_time = start_time if isinstance(start_time, time) else datetime.strptime(start_time, '%H:%M').time()
        self.end_time = end_time if isinstance(end_time, time) else datetime.strptime(end_time, '%H:%M').time()
        self.status = status
    
    def duration_hours(self):
        """Calculate the duration of the shift in hours"""
        start_dt = datetime.combine(self.work_date, self.start_time)
        end_dt = datetime.combine(self.work_date, self.end_time)
        
        # Handle shifts that cross midnight
        if self.end_time < self.start_time:
            end_dt = datetime.combine(self.work_date, self.end_time) + timedelta(days=1)
        
        duration = end_dt - start_dt
        return duration.total_seconds() / 3600
    
    def overlaps(self, other_start_time, other_end_time, other_date=None):
        """Check if this shift overlaps with another time period"""
        if other_date and other_date != self.work_date:
            return False
        
        # Convert to datetime objects for comparison
        self_start = datetime.combine(self.work_date, self.start_time)
        self_end = datetime.combine(self.work_date, self.end_time)
        
        other_start = datetime.combine(self.work_date, other_start_time)
        other_end = datetime.combine(self.work_date, other_end_time)
        
        # Handle shifts that cross midnight
        if self.end_time < self.start_time:
            self_end += timedelta(days=1)
        if other_end_time < other_start_time:
            other_end += timedelta(days=1)
        
        return not (self_end <= other_start or self_start >= other_end)
    
    def get_json(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'work_date': self.work_date.isoformat(),
            'start_time': self.start_time.strftime('%H:%M'),
            'end_time': self.end_time.strftime('%H:%M'),
            'status': self.status,
            'duration_hours': self.duration_hours()
        }
    
    def __repr__(self):
        return f'<Shift {self.id}: {self.work_date} {self.start_time}-{self.end_time}>'