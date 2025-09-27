from datetime import datetime, date
from App.database import db

class LeaveRequest(db.Model):
    __tablename__ = 'leave_requests'
    
    id = db.Column(db.Integer, primary_key=True)
    requester_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    approver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    type = db.Column(db.String(50), nullable=False)  # sick, vacation, personal, etc.
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected
    reason = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    approved_at = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    requester = db.relationship('User', foreign_keys=[requester_id], backref='leave_requests')
    approver = db.relationship('User', foreign_keys=[approver_id], backref='approved_leaves')
    
    def __init__(self, requester_id, start_date, end_date, type, reason=None):
        self.requester_id = requester_id
        self.start_date = start_date if isinstance(start_date, date) else datetime.strptime(start_date, '%Y-%m-%d').date()
        self.end_date = end_date if isinstance(end_date, date) else datetime.strptime(end_date, '%Y-%m-%d').date()
        self.type = type
        self.reason = reason
        self.status = 'pending'
    
    def approve(self, approver_id):
        """Approve the leave request"""
        self.status = 'approved'
        self.approver_id = approver_id
        self.approved_at = datetime.utcnow()
        return True
    
    def reject(self, approver_id, reason=None):
        """Reject the leave request"""
        self.status = 'rejected'
        self.approver_id = approver_id
        self.approved_at = datetime.utcnow()
        if reason:
            self.reason = f"{self.reason}\nRejection reason: {reason}" if self.reason else f"Rejection reason: {reason}"
        return True
    
    def overlaps_shift(self, shift_start_date, shift_end_date):
        """Check if this leave request overlaps with a shift period"""
        shift_start = shift_start_date if isinstance(shift_start_date, date) else datetime.strptime(shift_start_date, '%Y-%m-%d').date()
        shift_end = shift_end_date if isinstance(shift_end_date, date) else datetime.strptime(shift_end_date, '%Y-%m-%d').date()
        
        return not (self.end_date < shift_start or self.start_date > shift_end)
    
    def duration_days(self):
        """Calculate the number of days in the leave request"""
        return (self.end_date - self.start_date).days + 1
    
    def get_json(self):
        return {
            'id': self.id,
            'requester_id': self.requester_id,
            'approver_id': self.approver_id,
            'start_date': self.start_date.isoformat(),
            'end_date': self.end_date.isoformat(),
            'type': self.type,
            'status': self.status,
            'reason': self.reason,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'approved_at': self.approved_at.isoformat() if self.approved_at else None,
            'duration_days': self.duration_days()
        }
    
    def __repr__(self):
        return f'<LeaveRequest {self.id}: {self.requester_id} ({self.start_date} to {self.end_date}) - {self.status}>'