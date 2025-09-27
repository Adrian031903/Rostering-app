from werkzeug.security import check_password_hash, generate_password_hash
from App.database import db

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username =  db.Column(db.String(20), nullable=False, unique=True)
    password = db.Column(db.String(256), nullable=False)
    email = db.Column(db.String(120), nullable=True)
    role = db.Column(db.String(20), default='staff')  # staff, supervisor, admin
    name = db.Column(db.String(100), nullable=True)

    def __init__(self, username, password, email=None, role='staff', name=None):
        self.username = username
        self.email = email
        self.role = role
        self.name = name
        self.set_password(password)

    def get_json(self):
        return{
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'role': self.role,
            'name': self.name
        }

    def set_password(self, password):
        """Create hashed password."""
        self.password = generate_password_hash(password)
    
    def check_password(self, password):
        """Check hashed password."""
        return check_password_hash(self.password, password)
    
    def is_admin(self):
        """Check if user is admin"""
        return self.role == 'admin'
    
    def is_supervisor(self):
        """Check if user is supervisor"""
        return self.role == 'supervisor'
    
    def is_staff(self):
        """Check if user is staff"""
        return self.role == 'staff'
    
    def can_approve_requests(self):
        """Check if user can approve leave/swap requests"""
        return self.role in ['admin', 'supervisor']
    
    def __repr__(self):
        return f'<User {self.id}: {self.username} ({self.role})>'

