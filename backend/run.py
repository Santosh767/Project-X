from app import create_app, db
from app.models import User, Department, Appointment, Treatment

app = create_app()

@app.shell_context_processor
def make_shell_context():
    return {
        'db': db,
        'User': User,
        'Department': Department,
        'Appointment': Appointment,
        'Treatment': Treatment
    }

if __name__ == '__main__':
    app.run(debug=True, port=5000, host='0.0.0.0')