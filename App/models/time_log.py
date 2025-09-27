from App.database import db
from datetime import datetime

class TimeLog(db.Model):
    __tablename__ = 'time_log'
    
    id = db.Column(db.Integer, primary_key=True)
    shift_id = db.Column(db.Integer, db.ForeignKey('shift.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    clock_in = db.Column(db.DateTime, nullable=True)
    clock_out = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    shift = db.relationship('Shift', backref='time_logs')
    user = db.relationship('User', backref='time_logs')
    
    def __init__(self, shift_id, user_id):
        self.shift_id = shift_id
        self.user_id = user_id
    
    def worked_minutes(self):
        """Calculate minutes worked based on clock in/out times"""
        if self.clock_in and self.clock_out:
            delta = self.clock_out - self.clock_in
            return int(delta.total_seconds() / 60)
        return 0
    
    def is_open(self):
        """Check if the time log is still open (clocked in but not out)"""
        return self.clock_in is not None and self.clock_out is None
    
    def clock_in_now(self):
        """Clock in with current timestamp"""
        self.clock_in = datetime.now()
    
    def clock_out_now(self):
        """Clock out with current timestamp"""
        self.clock_out = datetime.now()
    
    def get_json(self):
        return {
            'id': self.id,
            'shift_id': self.shift_id,
            'user_id': self.user_id,
            'clock_in': self.clock_in.isoformat() if self.clock_in else None,
            'clock_out': self.clock_out.isoformat() if self.clock_out else None,
            'worked_minutes': self.worked_minutes()
        }
