from datetime import datetime, timedelta
from App.database import db

class TimeLog(db.Model):
    __tablename__ = 'time_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    shift_id = db.Column(db.Integer, db.ForeignKey('shifts.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    clock_in = db.Column(db.DateTime, nullable=False)
    clock_out = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='time_logs')
    
    def __init__(self, shift_id, user_id, clock_in=None):
        self.shift_id = shift_id
        self.user_id = user_id
        self.clock_in = clock_in or datetime.utcnow()
    
    def clock_out_now(self):
        """Clock out the user"""
        if self.clock_out:
            return False, "Already clocked out"
        
        self.clock_out = datetime.utcnow()
        db.session.commit()
        return True, "Successfully clocked out"
    
    def worked_minutes(self):
        """Calculate worked minutes. Returns 0 if not clocked out yet."""
        if not self.clock_out:
            return 0
        
        duration = self.clock_out - self.clock_in
        return int(duration.total_seconds() / 60)
    
    def is_open(self):
        """Check if this is an open time log (not clocked out)"""
        return self.clock_out is None
    
    def worked_hours(self):
        """Calculate worked hours as a float"""
        return self.worked_minutes() / 60.0
    
    def is_overtime(self, shift_duration_hours):
        """Check if worked time exceeds shift duration"""
        worked_hours = self.worked_hours()
        return worked_hours > shift_duration_hours
    
    def get_duration_string(self):
        """Get human readable duration string"""
        if not self.clock_out:
            return "In progress"
        
        minutes = self.worked_minutes()
        hours = minutes // 60
        mins = minutes % 60
        
        if hours > 0:
            return f"{hours}h {mins}m"
        else:
            return f"{mins}m"
    
    def get_json(self):
        return {
            'id': self.id,
            'shift_id': self.shift_id,
            'user_id': self.user_id,
            'clock_in': self.clock_in.isoformat() if self.clock_in else None,
            'clock_out': self.clock_out.isoformat() if self.clock_out else None,
            'worked_minutes': self.worked_minutes(),
            'worked_hours': self.worked_hours(),
            'is_open': self.is_open(),
            'duration_string': self.get_duration_string(),
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self):
        status = "Open" if self.is_open() else f"Closed ({self.get_duration_string()})"
        return f'<TimeLog {self.id}: User {self.user_id} - {status}>'