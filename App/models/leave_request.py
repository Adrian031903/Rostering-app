from App.database import db

class LeaveRequest(db.Model):
    __tablename__ = 'leave_request'
    
    id = db.Column(db.Integer, primary_key=True)
    requester_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    approver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    type = db.Column(db.String(50), nullable=False)  # vacation, sick, personal, etc.
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected
    reason = db.Column(db.Text)
    
    # Relationships
    requester = db.relationship('User', foreign_keys=[requester_id], backref='leave_requests_made')
    approver = db.relationship('User', foreign_keys=[approver_id], backref='leave_requests_approved')
    
    def __init__(self, requester_id, start_date, end_date, type, reason=None):
        self.requester_id = requester_id
        self.start_date = start_date
        self.end_date = end_date
        self.type = type
        self.reason = reason
        self.status = 'pending'
    
    def approve(self, approver_id):
        """Approve the leave request"""
        self.status = 'approved'
        self.approver_id = approver_id
        
    def reject(self, approver_id, reason=None):
        """Reject the leave request"""
        self.status = 'rejected'
        self.approver_id = approver_id
        if reason:
            self.reason = reason
    
    def overlaps_shift(self, shift_start, shift_end):
        """Check if leave request overlaps with a given shift timeframe"""
        return not (self.end_date < shift_start.date() or self.start_date > shift_end.date())
    
    def get_json(self):
        return {
            'id': self.id,
            'requester_id': self.requester_id,
            'approver_id': self.approver_id,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'type': self.type,
            'status': self.status,
            'reason': self.reason
        }
