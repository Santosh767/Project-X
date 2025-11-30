from app import db
from datetime import datetime

class Appointment(db.Model):
    __tablename__ = 'appointments'
    
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    appointment_date = db.Column(db.Date, nullable=False)
    appointment_time = db.Column(db.Time, nullable=False)
    status = db.Column(db.String(20), default='booked')  # booked, completed, cancelled
    reason = db.Column(db.Text)
    # Payment-related fields
    consultation_fee = db.Column(db.Numeric(10, 2), default=500.0)
    payment_status = db.Column(db.String(20), default='pending')  # pending, paid, refunded
    payment_method = db.Column(db.String(20))  # cash, card, upi, insurance, etc.
    transaction_id = db.Column(db.String(100))
    refund_status = db.Column(db.String(20))  # requested, approved, completed, rejected
    refund_date = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship with treatment
    treatment = db.relationship('Treatment', backref='appointment', uselist=False, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'patient_id': self.patient_id,
            'patient_name': self.patient.full_name,
            'doctor_id': self.doctor_id,
            'doctor_name': self.doctor.full_name,
            'appointment_date': self.appointment_date.isoformat(),
            'appointment_time': self.appointment_time.strftime('%H:%M'),
            'status': self.status,
            'reason': self.reason,
            'consultation_fee': float(self.consultation_fee) if self.consultation_fee else None,
            'payment_status': self.payment_status,
            'payment_method': self.payment_method,
            'transaction_id': self.transaction_id,
            'refund_status': self.refund_status,
            'refund_date': self.refund_date.isoformat() if self.refund_date else None,
            'has_treatment': self.treatment is not None
        }
