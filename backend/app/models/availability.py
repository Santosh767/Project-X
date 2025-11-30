from app import db
from datetime import datetime

class DoctorAvailability(db.Model):
    __tablename__ = 'doctor_availability'
    
    id = db.Column(db.Integer, primary_key=True)
    doctor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    is_available = db.Column(db.Boolean, default=True)
    lunch_break_start = db.Column(db.Time, nullable=True)
    lunch_break_end = db.Column(db.Time, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def slot_str(self):
        return f"{self.start_time.strftime('%H:%M')}-{self.end_time.strftime('%H:%M')}"

    
    def to_dict(self):
        return {
            'id': self.id,
            'doctor_id': self.doctor_id,
            'date': self.date.isoformat(),
            'start_time': self.start_time.strftime('%H:%M'),
            'end_time': self.end_time.strftime('%H:%M'),
            'is_available': self.is_available,
            'lunch_break_start': self.lunch_break_start.strftime('%H:%M') if self.lunch_break_start else None,
            'lunch_break_end': self.lunch_break_end.strftime('%H:%M') if self.lunch_break_end else None,
        }