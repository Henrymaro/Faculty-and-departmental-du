from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import requests
import random
from datetime import datetime

# Initialize the application
app = Flask(__name__)

# --- CONFIGURATION ---
# I am using a secret key for session security
app.config['SECRET_KEY'] = 'sYOUR_TEST_API_KEY_HERE' 
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///dues.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# --- PAYSTACK CONFIGURATION ---
# Using Test Keys for the project demonstration
# REMEMBER: Change this to the key from the Paystack Dashboard
PAYSTACK_SECRET_KEY = "YOUR_TEST_API_KEY_HERE" 
PAYSTACK_INIT_URL = "https://api.paystack.co/transaction/initialize"

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# --- DATABASE MODELS ---
# This table stores student details
class Student(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    matric_no = db.Column(db.String(20), unique=True, nullable=False) 
    password = db.Column(db.String(80), nullable=False) 
    full_name = db.Column(db.String(100), nullable=False)
    department = db.Column(db.String(50), nullable=False)

# This table records every payment attempt
class Payment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    reference = db.Column(db.String(50), unique=True, nullable=False) 
    amount = db.Column(db.Float, nullable=False)
    dues_type = db.Column(db.String(50), nullable=False) 
    status = db.Column(db.String(20), default='pending') # Status can be 'pending' or 'success'
    date_paid = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship to link payment back to the student
    student = db.relationship('Student', backref=db.backref('payments', lazy=True))

@login_manager.user_loader
def load_user(user_id):
    return Student.query.get(int(user_id))

# --- INITIAL DATA (Run once to set up users) ---
def create_initial_data():
    with app.app_context():
        db.create_all()
        
        # Check if we already have students, if not, create 10 demo students
        if not Student.query.first():
            print("Database empty. Creating demo students...")
            
            names = [
                "Musa Ibrahim", "Chinedu Okafor", "Yusuf Ali", "Ngozi Eze", 
                "Sarah Johnson", "Emeka Ugo", "Fatima Bello", "David Mark", 
                "Blessing Okon", "Samuel Adebayo"
            ]
            
            # Loop to create matric numbers from CMP2201001 to CMP2201010
            for i in range(10):
                mat_no = f"CMP220{1001 + i}"
                new_student = Student(
                    matric_no=mat_no, 
                    password='password', 
                    full_name=names[i], 
                    department='Software Engineering'
                )
                db.session.add(new_student)
                print(f" -> Added: {names[i]} ({mat_no})")

            # Create the Admin User
            admin = Student(
                matric_no='ADMIN', 
                password='admin', 
                full_name='Dr. Mrs. Okon', 
                department='Admin Office'
            )
            db.session.add(admin)
            db.session.commit()
            print("Setup Complete. Users created.")

# --- ROUTES ---

@app.route('/')
def home():
    # Redirect users to login page immediately
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Get form data
        mat_no = request.form.get('matric_no')
        pwd = request.form.get('password')
        
        # Check database
        user = Student.query.filter_by(matric_no=mat_no).first()
        
        if user and user.password == pwd:
            login_user(user)
            print(f"User logged in: {user.matric_no}") # Debug print
            
            if user.matric_no == 'ADMIN':
                return redirect(url_for('admin_dashboard'))
            return redirect(url_for('dashboard'))
        
        flash('Incorrect Matric Number or Password')
        
    return render_template('login.html')

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    # Security: Admins shouldn't be here
    if current_user.matric_no == 'ADMIN': 
        return redirect(url_for('admin_dashboard'))
        
    # Get all my past payments
    my_payments = Payment.query.filter_by(student_id=current_user.id).order_by(Payment.date_paid.desc()).all()
    return render_template('dashboard.html', student=current_user, payments=my_payments)

@app.route('/pay', methods=['POST'])
@login_required
def init_payment():
    # 1. Get Selected Due Type
    dues_type = request.form.get('dues_type')
    
    # 2. Determine price based on selection
    if dues_type == "Faculty Due":
        amount = 2000.0
    else:
        # Default to Departmental if nothing else
        amount = 3000.0
        
    print(f"Initiating payment: {dues_type} - {amount}") # Debugging
        
    # Generate a random reference code
    ref = f"REF-{random.randint(10000, 99999)}"
    
    # 3. Save "Pending" record to database first
    new_payment = Payment(
        student_id=current_user.id, 
        reference=ref, 
        amount=amount, 
        dues_type=dues_type
    )
    db.session.add(new_payment)
    db.session.commit()

    # 4. Connect to Paystack
    headers = {
        "Authorization": f"Bearer {PAYSTACK_SECRET_KEY}",
        "Content-Type": "application/json"
    }
    
    # Paystack expects amount in Kobo (multiply by 100)
    data = {
        "email": "student@example.com", 
        "amount": int(amount * 100), 
        "reference": ref, 
        "callback_url": url_for('callback', _external=True)
    }
    
    try:
        # Send request to Paystack
        req = requests.post(PAYSTACK_INIT_URL, headers=headers, json=data)
        response_data = req.json()
        
        if response_data['status']:
            # Redirect user to the Paystack payment page
            return redirect(response_data['data']['authorization_url'])
        else:
            flash("Error connecting to Paystack.")
            return redirect(url_for('dashboard'))
            
    except Exception as e:
        # OFFLINE MODE HANDLER
        # If internet fails, we simulate success for the project defense
        print(f"Connection Error: {e}")
        print("Switching to Offline Simulation...")
        
        new_payment.status = 'success'
        db.session.commit()
        flash(f"Offline Mode: Payment Simulated for {dues_type}")
        return redirect(url_for('dashboard'))

@app.route('/callback')
def callback():
    # Paystack sends user back here
    ref = request.args.get('reference')
    payment = Payment.query.filter_by(reference=ref).first()
    
    if payment:
        # In a real app, verify with Paystack API again here.
        # For now, we assume success if they return.
        payment.status = 'success' 
        db.session.commit()
        flash("Payment Successful!")
        
    return redirect(url_for('dashboard'))

@app.route('/receipt/<int:payment_id>')
@login_required
def view_receipt(payment_id):
    payment = Payment.query.get_or_404(payment_id)
    
    # Ensure students can only see their OWN receipts
    if payment.student_id != current_user.id and current_user.matric_no != 'ADMIN':
        flash("Unauthorized access")
        return redirect(url_for('dashboard'))
        
    return render_template('receipt.html', payment=payment, student=payment.student)

# --- ADMIN SECTION ---

@app.route('/admin')
@login_required
def admin_dashboard():
    # Ensure only Admin can access
    if current_user.matric_no != 'ADMIN': 
        return redirect(url_for('dashboard'))
    
    search_query = request.args.get('q')
    
    if search_query:
        # Find student by Matric No
        student = Student.query.filter_by(matric_no=search_query).first()
        if student:
            payments = Payment.query.filter_by(student_id=student.id).order_by(Payment.date_paid.desc()).all()
        else:
            payments = []
            flash("Student not found.")
    else:
        # Show all payments
        payments = Payment.query.order_by(Payment.date_paid.desc()).all()
        
    return render_template('admin_dashboard.html', payments=payments)

@app.route('/admin/approve/<int:payment_id>')
@login_required
def approve_payment(payment_id):
    if current_user.matric_no != 'ADMIN': return redirect(url_for('dashboard'))
    
    payment = Payment.query.get_or_404(payment_id)
    payment.status = 'success'
    db.session.commit()
    flash("Payment manually approved.")
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/record-cash', methods=['POST'])
@login_required
def record_cash():
    if current_user.matric_no != 'ADMIN': return redirect(url_for('dashboard'))
    
    mat_no = request.form.get('matric_no')
    amt = request.form.get('amount')
    d_type = request.form.get('dues_type')
    
    student = Student.query.filter_by(matric_no=mat_no).first()
    
    if student:
        # Create a "Cash" receipt
        ref = f"CASH-{random.randint(1000, 9999)}"
        new_pay = Payment(
            student_id=student.id, 
            reference=ref, 
            amount=float(amt), 
            dues_type=d_type, 
            status='success'
        )
        db.session.add(new_pay)
        db.session.commit()
        flash("Cash Payment Recorded Successfully")
    else:
        flash("Error: Matric No not found")
        
    return redirect(url_for('admin_dashboard'))

if __name__ == '__main__':
    # Run the initial setup
    create_initial_data()
    # Debug mode is on so errors show in browser (helpful for development)
    app.run(debug=True)