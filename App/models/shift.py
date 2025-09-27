from App.database import db
from datetime import datetime

class Shift(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), default='scheduled')  # scheduled, in_progress, completed
    
    def __init__(self, user_id, start_time, end_time, status='scheduled'):
        self.user_id = user_id
        self.start_time = start_time
        self.end_time = end_time
        self.status = status
    
    def duration_hours(self):
        """Calculate shift duration in hours"""
        return (self.end_time - self.start_time).total_seconds() / 3600
    
    def overlaps(self, other_start, other_end):
        """Check if this shift overlaps with another time period"""
        return not (self.end_time <= other_start or self.start_time >= other_end)
    
    def get_json(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat(),
            'status': self.status,
            'duration_hours': self.duration_hours()
        }