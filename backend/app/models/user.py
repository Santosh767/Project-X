from app import db, bcrypt
from datetime import datetime

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # admin, doctor, patient
    is_active = db.Column(db.Boolean, default=True)
    
    # Common fields
    full_name = db.Column(db.String(120))
    phone = db.Column(db.String(20))
    address = db.Column(db.Text)
    date_of_birth = db.Column(db.Date)
    gender = db.Column(db.String(10))
    
    # Doctor-specific fields
    specialization_id = db.Column(db.Integer, db.ForeignKey('departments.id'))
    qualification = db.Column(db.String(200))
    experience_years = db.Column(db.Integer, default=0)
    consultation_fee = db.Column(db.Numeric(10, 2), default=0.0)
    
    # Relationships
    specialization = db.relationship('Department', backref='doctors')
    doctor_appointments = db.relationship('Appointment', 
                                         foreign_keys='Appointment.doctor_id',
                                         backref='doctor', 
                                         lazy='dynamic',
                                         cascade='all, delete-orphan')
    patient_appointments = db.relationship('Appointment', 
                                          foreign_keys='Appointment.patient_id',
                                          backref='patient', 
                                          lazy='dynamic',
                                          cascade='all, delete-orphan')
    
    def set_password(self, password):
        """Hash and set password"""
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
    
    def check_password(self, password):
        """Verify password"""
        return bcrypt.check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        data = {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'role': self.role,
            'full_name': self.full_name,
            'phone': self.phone,
            'address': self.address,
            'date_of_birth': self.date_of_birth.isoformat() if self.date_of_birth else None,
            'gender': self.gender,
            'is_active': self.is_active,
            'department_id': self.specialization_id, 
            'specialization': self.specialization.name if self.specialization else None,
        }
        
        if self.role == 'doctor':
            data.update({
                'qualification': self.qualification,
                'experience_years': self.experience_years,
                'consultation_fee': float(self.consultation_fee) if self.consultation_fee else 0.0,
                'specialization_id': self.specialization_id  
            })
        
        return data
    
    def __repr__(self):
        return f'<User {self.username} ({self.role})>'