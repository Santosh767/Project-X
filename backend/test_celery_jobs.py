import os
import sys
from datetime import date, timedelta, datetime, time
from colorama import init, Fore, Style

# Initialize colorama for colored output
init(autoreset=True)

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app import create_app, db
from app.models import User, Appointment, DoctorAvailability
from app.celery_config import make_celery

# Create app and celery instances
app = create_app()
celery = make_celery(app)


def print_header(text):
    """Print formatted header"""
    print(f"\n{Fore.CYAN}{'='*80}")
    print(f"{Fore.CYAN}{text}")
    print(f"{Fore.CYAN}{'='*80}{Style.RESET_ALL}")


def print_success(text):
    """Print success message"""
    print(f"{Fore.GREEN} {text}{Style.RESET_ALL}")


def print_error(text):
    """Print error message"""
    print(f"{Fore.RED} {text}{Style.RESET_ALL}")


def print_warning(text):
    """Print warning message"""
    print(f"{Fore.YELLOW} {text}{Style.RESET_ALL}")


def print_info(text):
    """Print info message"""
    print(f"{Fore.BLUE}ℹ️  {text}{Style.RESET_ALL}")


def test_celery_connection():
    """Test Celery connection to Redis broker"""
    print_header("TEST 1: Celery Connection & Configuration")
    
    try:
        # Test broker connection
        print_info("Testing Redis connection...")
        celery.control.ping(timeout=5)
        print_success("Redis broker connection successful")
        
        # Check registered tasks
        print_info("Checking registered tasks...")
        inspector = celery.control.inspect()
        registered = inspector.registered()
        
        if registered:
            print_success("Celery worker is running and tasks are registered")
            
            for worker, tasks in registered.items():
                print(f"\n{Fore.MAGENTA}Worker: {worker}{Style.RESET_ALL}")
                
                expected_tasks = [
                    'app.tasks.send_daily_reminders',
                    'app.tasks.send_monthly_reports',
                    'app.tasks.export_patient_treatments',
                    'app.tasks.cleanup.cleanup_old_availability',
                    'app.tasks.auto_cancel.cancel_missed_appointments'
                ]
                
                found_tasks = [t for t in tasks if 'app.tasks' in t]
                
                for task in expected_tasks:
                    if task in found_tasks:
                        print_success(f"Found: {task}")
                    else:
                        print_error(f"Missing: {task}")
                
                # Check for unexpected tasks
                for task in found_tasks:
                    if task not in expected_tasks:
                        print_warning(f"Unexpected task: {task}")
        else:
            print_warning("No Celery workers running")
            print_info("Start worker with: celery -A celery_worker.celery worker --loglevel=info")
        
        # Check beat schedule
        print_info("\nChecking Beat scheduler configuration...")
        schedule = celery.conf.beat_schedule
        
        if schedule:
            print_success(f"Beat schedule configured with {len(schedule)} tasks:")
            for task_name, task_config in schedule.items():
                print(f"  • {Fore.CYAN}{task_name}{Style.RESET_ALL}: {task_config['task']}")
                print(f"    Schedule: {task_config['schedule']}")
        else:
            print_error("No beat schedule configured")
        
        return True
        
    except Exception as e:
        print_error(f"Celery connection failed: {str(e)}")
        print_warning("\nMake sure:")
        print("  1. Redis is running: redis-server")
        print("  2. Celery worker is running: celery -A celery_worker.celery worker")
        print("  3. Celery beat is running: celery -A celery_worker.celery beat")
        return False


def test_daily_reminders():
    """Test daily reminder task"""
    print_header("🧪 TEST 2: Daily Reminders Task")
    
    with app.app_context():
        try:
            today = date.today()
            
            print_info(f"Checking appointments for {today}...")
            
            # Get today's appointments
            appointments = Appointment.query.filter_by(
                appointment_date=today,
                status='booked'
            ).all()
            
            print_info(f"Found {len(appointments)} appointments for today")
            
            if len(appointments) == 0:
                print_warning("No appointments today - creating test appointment...")
                
                # Get or create test users
                patient = User.query.filter_by(role='patient').first()
                doctor = User.query.filter_by(role='doctor').first()
                
                if not patient:
                    print_error("No patients found in database")
                    return False
                
                if not doctor:
                    print_error("No doctors found in database")
                    return False
                
                # Create test appointment
                test_apt = Appointment(
                    patient_id=patient.id,
                    doctor_id=doctor.id,
                    appointment_date=today,
                    appointment_time=time(14, 30),
                    status='booked',
                    reason='Test appointment for reminder testing'
                )
                db.session.add(test_apt)
                db.session.commit()
                
                print_success(f"Created test appointment ID: {test_apt.id}")
                appointments = [test_apt]
            
            # Display appointments
            for apt in appointments:
                print(f"\n  Appointment #{apt.id}")
                print(f"     Patient: {apt.patient.full_name} ({apt.patient.email})")
                print(f"     Doctor: Dr. {apt.doctor.full_name}")
                print(f"     Time: {apt.appointment_time.strftime('%H:%M')}")
            
            # Run the task
            print_info("\nExecuting send_daily_reminders task...")
            from app.tasks.reminders import send_daily_reminders
            result = send_daily_reminders()
            
            # Display results
            print_success("Task completed!")
            print(f"\n{Fore.MAGENTA}Results:{Style.RESET_ALL}")
            print(f"  Status: {result.get('status')}")
            print(f"  Date: {result.get('date')}")
            print(f"  Total appointments: {result.get('total_appointments')}")
            print(f"  Reminders sent: {result.get('reminders_sent')}")
            print(f"  Failed: {result.get('failed', 0)}")
            
            if result.get('reminder_details'):
                print(f"\n{Fore.MAGENTA}Reminder Details:{Style.RESET_ALL}")
                for detail in result['reminder_details']:
                    print(f"  • {detail['patient_name']} - {detail['channels']}")
            
            return True
            
        except Exception as e:
            print_error(f"Test failed: {str(e)}")
            import traceback
            traceback.print_exc()
            return False


def test_monthly_reports():
    """Test monthly report task"""
    print_header("🧪 TEST 3: Monthly Reports Task")
    
    with app.app_context():
        try:
            # Get active doctors
            doctors = User.query.filter_by(role='doctor', is_active=True).all()
            print_info(f"Found {len(doctors)} active doctors")
            
            if not doctors:
                print_warning("No active doctors found in database")
                return False
            
            for doctor in doctors[:3]:  # Show first 3 doctors
                print(f"  • Dr. {doctor.full_name} - {doctor.email}")
            
            if len(doctors) > 3:
                print(f"  ... and {len(doctors) - 3} more")
            
            # Run the task
            print_info("\nExecuting send_monthly_reports task...")
            from app.tasks.reports import send_monthly_reports
            result = send_monthly_reports()
            
            print_success("Task completed!")
            print(f"\n{Fore.MAGENTA}Result:{Style.RESET_ALL} {result}")
            
            return True
            
        except Exception as e:
            print_error(f"Test failed: {str(e)}")
            import traceback
            traceback.print_exc()
            return False


def test_csv_export():
    """Test CSV export task"""
    print_header("TEST 4: CSV Export Task")
    
    with app.app_context():
        try:
            # Get a patient with appointments
            patient = User.query.filter_by(role='patient').first()
            
            if not patient:
                print_error("No patients found in database")
                return False
            
            print_info(f"Testing export for: {patient.full_name} (ID: {patient.id})")
            
            # Check completed appointments
            appointments = Appointment.query.filter_by(
                patient_id=patient.id,
                status='completed'
            ).count()
            
            print_info(f"Patient has {appointments} completed appointments")
            
            if appointments == 0:
                print_warning("No completed appointments - export will be empty")
            
            # Run the task
            print_info("\nExecuting export_patient_treatments task...")
            from app.tasks.exports import export_patient_treatments
            result = export_patient_treatments(patient.id)
            
            print_success("Task completed!")
            print(f"\n{Fore.MAGENTA}Results:{Style.RESET_ALL}")
            print(f"  Status: {result.get('status')}")
            print(f"  Filename: {result.get('filename')}")
            print(f"  Records: {result.get('records')}")
            print(f"  Filepath: {result.get('filepath')}")
            
            # Check if file exists
            if result.get('filepath'):
                import os
                if os.path.exists(result['filepath']):
                    file_size = os.path.getsize(result['filepath'])
                    print_success(f"File created successfully ({file_size} bytes)")
                else:
                    print_warning("File path returned but file doesn't exist")
            
            return True
            
        except Exception as e:
            print_error(f"Test failed: {str(e)}")
            import traceback
            traceback.print_exc()
            return False


def test_cleanup():
    """Test cleanup task"""
    print_header("TEST 5: Cleanup Old Availability Task")
    
    with app.app_context():
        try:
            cutoff_date = date.today() - timedelta(days=30)
            
            # Count old records
            old_records = DoctorAvailability.query.filter(
                DoctorAvailability.date < cutoff_date
            ).count()
            
            print_info(f"Checking for availability records older than {cutoff_date}")
            print_info(f"Found {old_records} old records")
            
            if old_records == 0:
                print_warning("No old records to clean up")
                print_info("Creating test old record...")
                
                doctor = User.query.filter_by(role='doctor').first()
                if doctor:
                    old_avail = DoctorAvailability(
                        doctor_id=doctor.id,
                        date=date.today() - timedelta(days=35),
                        start_time=time(9, 0),
                        end_time=time(17, 0),
                        is_available=True
                    )
                    db.session.add(old_avail)
                    db.session.commit()
                    print_success("Created test old record")
                    old_records = 1
            
            # Run the task
            print_info("\nExecuting cleanup_old_availability task...")
            from app.tasks.cleanup import cleanup_old_availability
            result = cleanup_old_availability()
            
            print_success("Task completed!")
            print(f"\n{Fore.MAGENTA}Results:{Style.RESET_ALL}")
            print(f"  Status: {result.get('status')}")
            print(f"  Deleted: {result.get('deleted_count')} records")
            print(f"  Cutoff date: {result.get('cutoff_date')}")
            
            return True
            
        except Exception as e:
            print_error(f"Test failed: {str(e)}")
            import traceback
            traceback.print_exc()
            return False


def test_auto_cancel():
    """Test auto-cancel task"""
    print_header("TEST 6: Auto-Cancel Missed Appointments Task")
    
    with app.app_context():
        try:
            yesterday = date.today() - timedelta(days=1)
            
            # Count missed appointments
            missed = Appointment.query.filter(
                Appointment.appointment_date == yesterday,
                Appointment.status == 'booked'
            ).count()
            
            print_info(f"Checking for missed appointments on {yesterday}")
            print_info(f"Found {missed} booked appointments from yesterday")
            
            if missed == 0:
                print_warning("No missed appointments - creating test appointment...")
                
                patient = User.query.filter_by(role='patient').first()
                doctor = User.query.filter_by(role='doctor').first()
                
                if patient and doctor:
                    test_apt = Appointment(
                        patient_id=patient.id,
                        doctor_id=doctor.id,
                        appointment_date=yesterday,
                        appointment_time=time(10, 0),
                        status='booked',
                        reason='Test missed appointment',
                        consultation_fee=500,
                        payment_status='paid'
                    )
                    db.session.add(test_apt)
                    db.session.commit()
                    print_success(f"Created test missed appointment ID: {test_apt.id}")
                    missed = 1
            
            # Run the task
            print_info("\nExecuting cancel_missed_appointments task...")
            from app.tasks.auto_cancel import cancel_missed_appointments
            result = cancel_missed_appointments()
            
            print_success("Task completed!")
            print(f"\n{Fore.MAGENTA}Results:{Style.RESET_ALL}")
            print(f"  Status: {result.get('status')}")
            print(f"  Date: {result.get('date')}")
            print(f"  Cancelled: {result.get('cancelled_count')} appointments")
            
            if result.get('cancelled_appointments'):
                print(f"\n{Fore.MAGENTA}Cancelled Appointments:{Style.RESET_ALL}")
                for apt in result['cancelled_appointments']:
                    print(f"  • ID {apt['appointment_id']}: {apt['patient_name']} with Dr. {apt['doctor_name']}")
                    print(f"    Time: {apt['appointment_time']}, Fee: ₹{apt['consultation_fee']}")
                
                total_refund = result.get('total_refund_amount', 0)
                print(f"\n  Total Refund Amount: ₹{total_refund}")
            
            return True
            
        except Exception as e:
            print_error(f"Test failed: {str(e)}")
            import traceback
            traceback.print_exc()
            return False


def test_database_connection():
    """Test database connection"""
    print_header("TEST 0: Database Connection")
    
    with app.app_context():
        try:
            # Count records in each table
            users = User.query.count()
            appointments = Appointment.query.count()
            availability = DoctorAvailability.query.count()
            
            print_success("Database connection successful")
            print(f"\n{Fore.MAGENTA}Database Statistics:{Style.RESET_ALL}")
            print(f"  Users: {users}")
            print(f"  Appointments: {appointments}")
            print(f"  Availability Records: {availability}")
            
            # Count by role
            admins = User.query.filter_by(role='admin').count()
            doctors = User.query.filter_by(role='doctor').count()
            patients = User.query.filter_by(role='patient').count()
            
            print(f"\n{Fore.MAGENTA}Users by Role:{Style.RESET_ALL}")
            print(f"  Admins: {admins}")
            print(f"  Doctors: {doctors}")
            print(f"  Patients: {patients}")
            
            # Count appointments by status
            booked = Appointment.query.filter_by(status='booked').count()
            completed = Appointment.query.filter_by(status='completed').count()
            cancelled = Appointment.query.filter_by(status='cancelled').count()
            
            print(f"\n{Fore.MAGENTA}Appointments by Status:{Style.RESET_ALL}")
            print(f"  Booked: {booked}")
            print(f"  Completed: {completed}")
            print(f"  Cancelled: {cancelled}")
            
            return True
            
        except Exception as e:
            print_error(f"Database connection failed: {str(e)}")
            return False


def run_all_tests():
    """Run all tests in sequence"""
    print(f"\n{Fore.YELLOW}{'='*80}")
    print(f"{Fore.YELLOW} HOSPITAL MANAGEMENT SYSTEM - CELERY JOBS TEST SUITE")
    print(f"{Fore.YELLOW}{'='*80}{Style.RESET_ALL}")
    
    tests = [
        ("Database Connection", test_database_connection),
        ("Celery Connection", test_celery_connection),
        ("Daily Reminders", test_daily_reminders),
        ("Monthly Reports", test_monthly_reports),
        ("CSV Export", test_csv_export),
        ("Cleanup Task", test_cleanup),
        ("Auto-Cancel Task", test_auto_cancel),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except KeyboardInterrupt:
            print_warning("\n\nTests interrupted by user")
            break
        except Exception as e:
            print_error(f"Unexpected error in {test_name}: {str(e)}")
            results.append((test_name, False))
    
    # Print summary
    print_header("TEST SUMMARY")
    
    passed = sum(1 for _, result in results if result)
    failed = len(results) - passed
    
    for test_name, result in results:
        status = f"{Fore.GREEN} PASSED" if result else f"{Fore.RED} FAILED"
        print(f"  {status}{Style.RESET_ALL} - {test_name}")
    
    print(f"\n{Fore.MAGENTA}Total Tests: {len(results)}")
    print(f"{Fore.GREEN}Passed: {passed}")
    print(f"{Fore.RED}Failed: {failed}{Style.RESET_ALL}")
    
    if failed == 0:
        print(f"\n{Fore.GREEN}{'='*80}")
        print(f"{Fore.GREEN} ALL TESTS PASSED! Your Celery setup is working perfectly!")
        print(f"{Fore.GREEN}{'='*80}{Style.RESET_ALL}")
    else:
        print(f"\n{Fore.RED}{'='*80}")
        print(f"{Fore.RED} SOME TESTS FAILED - Please check the errors above")
        print(f"{Fore.RED}{'='*80}{Style.RESET_ALL}")
    
    return failed == 0


if __name__ == '__main__':
    try:
        success = run_all_tests()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Tests interrupted by user{Style.RESET_ALL}")
        sys.exit(1)
    except Exception as e:
        print_error(f"Fatal error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)