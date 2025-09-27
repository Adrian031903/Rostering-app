from datetime import datetime
from App.database import db

class SwapRequest(db.Model):
    __tablename__ = 'swap_requests'
    
    id = db.Column(db.Integer, primary_key=True)
    shift_id = db.Column(db.Integer, db.ForeignKey('shifts.id'), nullable=False)
    from_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    to_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected
    note = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    approved_at = db.Column(db.DateTime, nullable=True)
    approver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    
    # Relationships
    from_user = db.relationship('User', foreign_keys=[from_user_id], backref='swap_requests_from')
    to_user = db.relationship('User', foreign_keys=[to_user_id], backref='swap_requests_to')
    approver = db.relationship('User', foreign_keys=[approver_id], backref='approved_swaps')
    
    def __init__(self, shift_id, from_user_id, to_user_id, note=None):
        self.shift_id = shift_id
        self.from_user_id = from_user_id
        self.to_user_id = to_user_id
        self.note = note
        self.status = 'pending'
    
    def approve(self, approver_id):
        """Approve the swap request and update the shift assignment"""
        from App.models.shift import Shift
        
        # Update the shift to be assigned to the new user
        shift = Shift.query.get(self.shift_id)
        if shift:
            shift.user_id = self.to_user_id
            
        self.status = 'approved'
        self.approver_id = approver_id
        self.approved_at = datetime.utcnow()
        
        db.session.commit()
        return True
    
    def reject(self, approver_id, reason=None):
        """Reject the swap request"""
        self.status = 'rejected'
        self.approver_id = approver_id
        self.approved_at = datetime.utcnow()
        
        if reason:
            self.note = f"{self.note}\nRejection reason: {reason}" if self.note else f"Rejection reason: {reason}"
        
        db.session.commit()
        return True
    
    def check_conflicts(self):
        """Check if the target user has any conflicts with this shift"""
        from App.models.shift import Shift
        
        shift = Shift.query.get(self.shift_id)
        if not shift:
            return ["Shift not found"]
        
        # Check if target user has overlapping shifts
        existing_shifts = Shift.query.filter_by(
            user_id=self.to_user_id,
            work_date=shift.work_date,
            status='scheduled'
        ).all()
        
        conflicts = []
        for existing_shift in existing_shifts:
            if shift.overlaps(existing_shift.start_time, existing_shift.end_time):
                conflicts.append(f"Overlaps with existing shift: {existing_shift.start_time}-{existing_shift.end_time}")
        
        return conflicts
    
    def get_json(self):
        return {
            'id': self.id,
            'shift_id': self.shift_id,
            'from_user_id': self.from_user_id,
            'to_user_id': self.to_user_id,
            'status': self.status,
            'note': self.note,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'approved_at': self.approved_at.isoformat() if self.approved_at else None,
            'approver_id': self.approver_id,
            'conflicts': self.check_conflicts()
        }
    
    def __repr__(self):
        return f'<SwapRequest {self.id}: Shift {self.shift_id} from User {self.from_user_id} to User {self.to_user_id} - {self.status}>'