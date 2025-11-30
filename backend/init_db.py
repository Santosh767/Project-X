from app import create_app, db
from app.models import User, Department

def init_database():
    app = create_app()
    
    with app.app_context():
        # Create all tables
        db.create_all()
        
        # Create admin user
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(
                username='admin',
                email='22f3001157@ds.study.iitm.ac.in',
                role='admin',
                full_name='System Administrator',
                phone='1234567890'
            )
            admin.set_password('admin123')
            db.session.add(admin)
        
        # Create some departments
        departments = [
            {'name': 'Cardiology', 'description': 'Heart and cardiovascular system'},
            {'name': 'Neurology', 'description': 'Brain and nervous system'},
            {'name': 'Orthopedics', 'description': 'Bones, joints, and muscles'},
            {'name': 'Pediatrics', 'description': 'Children healthcare'},
            {'name': 'Dermatology', 'description': 'Skin, hair, and nails'},
            {'name': 'General Medicine', 'description': 'General health issues'}
        ]
        
        for dept_data in departments:
            dept = Department.query.filter_by(name=dept_data['name']).first()
            if not dept:
                dept = Department(**dept_data)
                db.session.add(dept)
        
        db.session.commit()
        print("Database initialized successfully!")
        print("Admin credentials: username='admin', password='admin123'")

if __name__ == '__main__':
    init_database()