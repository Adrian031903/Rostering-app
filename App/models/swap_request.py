from App.database import db

class SwapRequest(db.Model):
    __tablename__ = 'swap_request'
    
    id = db.Column(db.Integer, primary_key=True)
    shift_id = db.Column(db.Integer, db.ForeignKey('shift.id'), nullable=False)
    from_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    to_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected
    note = db.Column(db.Text)
    
    # Relationships
    shift = db.relationship('Shift', backref='swap_requests')
    from_user = db.relationship('User', foreign_keys=[from_user_id], backref='swap_requests_sent')
    to_user = db.relationship('User', foreign_keys=[to_user_id], backref='swap_requests_received')
    
    def __init__(self, shift_id, from_user_id, to_user_id, note=None):
        self.shift_id = shift_id
        self.from_user_id = from_user_id
        self.to_user_id = to_user_id
        self.note = note
        self.status = 'pending'
    
    def approve(self):
        """Approve the swap request and update the shift assignment"""
        from App.models.shift import Shift
        
        self.status = 'approved'
        
        # Update the shift assignment
        shift = Shift.query.get(self.shift_id)
        if shift:
            shift.user_id = self.to_user_id
    
    def reject(self, reason=None):
        """Reject the swap request"""
        self.status = 'rejected'
        if reason:
            self.note = reason
    
    def get_json(self):
        return {
            'id': self.id,
            'shift_id': self.shift_id,
            'from_user_id': self.from_user_id,
            'to_user_id': self.to_user_id,
            'status': self.status,
            'note': self.note
        }
