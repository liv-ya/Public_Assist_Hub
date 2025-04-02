import os
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash  
import random
from flask_mail import Mail, Message
from dotenv import load_dotenv
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
import mysql.connector
from db_connection import Db 
import torch
from PIL import Image
from ultralytics import YOLO
from flask_socketio import SocketIO
import traceback
import logging

# Initialize app before other imports
app = Flask(__name__)
# app.config.from_object(Config)


load_dotenv()  # Load environment variables first

yolo_model_path = os.getenv("MODEL_PATH")
model=YOLO(yolo_model_path)

app.secret_key = os.environ.get('SECRET_KEY')

# Email configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.environ.get('EMAIL_USER') 
app.config['MAIL_PASSWORD'] = os.environ.get('EMAIL_PASS')  

mail = Mail(app)

# Add these configurations before the directory creation
app.config['ALLOWED_EXTENSIONS'] = {'jpg', 'jpeg', 'png', 'gif'}
app.config['UPLOAD_FOLDER'] = 'uploads'

# Then create the directory if it doesn't exist
if 'UPLOAD_FOLDER' in app.config:
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
else:
    app.logger.warning("UPLOAD_FOLDER not configured, file uploads will fail")

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# Initialize SocketIO after creating your Flask app
socketio = SocketIO(app)

@app.before_request
def set_session_permanent():
    session.permanent = False

@app.route('/')
def index():
    return render_template('home.html') 





@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        try:
            data = request.get_json()
            print("Data is..", data)
            if not data:
                return jsonify({'error': 'No data received'}), 400

            # Handle email submission
            email = data.get('email')
            print("Email is...", email)
            if not email:
                return jsonify({'error': 'Email is required'}), 400

            # Validate email domain
            if not email.endswith('@gmail.com'):
                return jsonify({'error': 'Only Gmail addresses are allowed.'}), 400

            otp = random.randint(100000, 999999)
            print("OTP is ...", otp)
            session['otp'] = str(otp)
            session['email'] = email

            # Store OTP and timestamp in the database
            with Db() as db:
                query = """
                    INSERT INTO users (email, otp, otp_timestamp)
                    VALUES (%s, %s, NOW())
                    ON DUPLICATE KEY UPDATE otp = %s, otp_timestamp = NOW()
                """
                values = (email, otp, otp)
                db.execute(query, values)
                app.logger.info(f"OTP {otp} inserted/updated for email {email}")  # Log the OTP insertion

            try:
                msg = Message('Your Login OTP',
                              sender=app.config['MAIL_USERNAME'],
                              recipients=[email])
                msg.body = f'Your OTP is: {otp}'
                mail.send(msg)
                return jsonify({'message': 'OTP sent successfully'})
            except Exception as e:
                return jsonify({'error': f'Error sending email: {str(e)}'}), 500

        except Exception as e:
            return jsonify({'error': f'Server error: {str(e)}'}), 500

    return render_template('login.html')



@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        data = request.get_json()
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        print("Email received:", email)
        
        try:
            if not email or not password:
                return jsonify({"success": False, "error": "Email and password required"}), 400

            # Determine role and redirect URL based on email domain
            if '@admin' in email:
                role = 'Admin'
                redirect_url = url_for('admin')
            elif '@pwd' in email:
                role = 'PWD'
                redirect_url = url_for('pwd')
            elif '@municipality' in email:
                role = 'Municipality'
                redirect_url = url_for('municipality')
            else:
                return jsonify({"success": False, "error": "Invalid email domain"}), 400

            with Db() as db:
                try:
                    # Handle admin login separately (only from Admin table)
                    if role == 'Admin':
                        db.execute(
                            "SELECT adminID FROM admin WHERE email = %s AND password = %s",
                            (email, password)
                        )
                        admin = db.fetchone()
                        if not admin:
                            return jsonify({"success": False, "error": "Invalid admin credentials"}), 401
                        
                        # Set admin session
                        session.update({
                            'admin_id': admin['adminID'],
                            'role': 'Admin'
                        })
                        print("Admin login successful. Redirecting to:", redirect_url)
                        return jsonify({
                            "success": True,
                            "redirect": redirect_url
                        })

                    # Handle PWD login (from PWD table)
                    elif role == 'PWD':
                        db.execute(
                            "SELECT deptID FROM pwd WHERE email = %s AND password = %s",
                            (email, password)
                        )
                        pwd = db.fetchone()
                        if not pwd:
                            return jsonify({"success": False, "error": "Invalid PWD credentials"}), 401
                        
                        # Set PWD session
                        session.update({
                            'dept_id': pwd['deptID'],
                            'role': 'PWD'
                        })
                        print("PWD login successful. Redirecting to:", redirect_url)
                        return jsonify({
                            "success": True,
                            "redirect": redirect_url
                        })

                    # Handle Municipality login (from Municipality table)
                    elif role == 'Municipality':
                        db.execute(
                            "SELECT deptID FROM municipality WHERE email = %s AND password = %s",
                            (email, password)
                        )
                        municipality = db.fetchone()
                        if not municipality:
                            return jsonify({"success": False, "error": "Invalid Municipality credentials"}), 401
                        
                        # Set Municipality session
                        session.update({
                            'dept_id': municipality['deptID'],
                            'role': 'Municipality'
                        })
                        print("Municipality login successful. Redirecting to:", redirect_url)
                        return jsonify({
                            "success": True,
                            "redirect": redirect_url
                        })

                    # Handle Officials login (from Officials table)
                    else:
                        db.execute(
                            "SELECT officialID, deptID FROM officials WHERE email = %s AND password = %s",
                            (email, password)
                        )
                        official = db.fetchone()
                        if not official:
                            return jsonify({"success": False, "error": "Invalid credentials"}), 401
                        
                        # Set Officials session
                        session.update({
                            'official_id': official['officialID'],
                            'dept_id': official['deptID'],
                            'role': 'Official'
                        })
                        return jsonify({
                            "success": True,
                            "redirect": redirect_url
                        })

                except Exception as db_error:
                    db.rollback()
                    print(f"Database error: {str(db_error)}")
                    return jsonify({"success": False, "error": "Database operation failed"}), 500

        except Exception as e:
            print(f"General error: {traceback.format_exc()}")
            return jsonify({"success": False, "error": "Internal server error"}), 500

    # Render the login page for GET requests
    return render_template('/login_pwd_municipality.html')



@app.route('/municipality')
def municipality():
    try:
        with Db() as db:
            # Fetch all issues assigned to the Municipality department
            query = """
                SELECT complaintID AS id, category, description, status
                FROM complaint
                WHERE assignedDept = (SELECT deptID FROM department WHERE name = 'Municipality')
            """
            db.execute(query)
            issues = db.fetchall()
            app.logger.info(f"Fetched issues: {issues}")

            # Fetch count of Pending issues with category 'Waste Management'
            query_pending = """
                SELECT COUNT(*) AS pending_count
                FROM complaint
                WHERE assignedDept = (SELECT deptID FROM department WHERE name = 'Municipality')
                AND category = 'waste'
                AND status = 'Pending'
            """
            db.execute(query_pending)
            pending_count = db.fetchone()['pending_count']

            # Fetch count of Resolved issues
            query_resolved = """
                SELECT COUNT(*) AS resolved_count
                FROM complaint
                WHERE assignedDept = (SELECT deptID FROM department WHERE name = 'Municipality')
                AND status = 'Resolved'
            """
            db.execute(query_resolved)
            resolved_count = db.fetchone()['resolved_count']

        # Render the municipality.html template with the issues and counts data
        return render_template('municipality.html', issues=issues, pending_count=pending_count, resolved_count=resolved_count)
    except Exception as e:
        app.logger.error(f"Error fetching issues: {str(e)}", exc_info=True)
        return render_template('municipality.html', issues=[], pending_count=0, resolved_count=0)



@app.route('/pwd')
def pwd():
    try:
        with Db() as db:
            # Fetch all issues assigned to the PWD department
            query = """
                SELECT complaintID AS id, category, description, status
                FROM complaint
                WHERE assignedDept = (SELECT deptID FROM department WHERE name = 'Pwd')
            """
            db.execute(query)
            issues = db.fetchall()
            app.logger.info(f"Fetched PWD issues: {issues}")

            # Fetch count of Pending issues with category 'Pothole'
            query_pending = """
                SELECT COUNT(*) AS pending_count
                FROM complaint
                WHERE assignedDept = (SELECT deptID FROM department WHERE name = 'Pwd')
                AND category = 'Pothole'
                AND status = 'Pending'
            """
            db.execute(query_pending)
            pending_count = db.fetchone()['pending_count']

            # Fetch count of Resolved issues
            query_resolved = """
                SELECT COUNT(*) AS resolved_count
                FROM complaint
                WHERE assignedDept = (SELECT deptID FROM department WHERE name = 'Pwd')
                AND status = 'Resolved'
            """
            db.execute(query_resolved)
            resolved_count = db.fetchone()['resolved_count']

        # Render the pwd.html template with the issues and counts data
        return render_template('pwd.html', issues=issues, pending_count=pending_count, resolved_count=resolved_count)
    except Exception as e:
        app.logger.error(f"Error fetching PWD issues: {str(e)}", exc_info=True)
        return render_template('pwd.html', issues=[], pending_count=0, resolved_count=0)



@app.route('/api/issues/<int:issue_id>/resolve', methods=['PUT'])
def resolve_issue(issue_id):
    try:
        with Db() as db:
            # Update the status of the issue to "Resolved"
            query = """
                UPDATE complaint
                SET status = 'Resolved'
                WHERE complaintID = %s
            """
            db.execute(query, (issue_id,))
            app.logger.info(f"Issue {issue_id} resolved successfully")
        
        return jsonify({'success': True, 'message': 'Issue resolved successfully'})
    except Exception as e:
        app.logger.error(f"Error resolving issue: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'message': 'Failed to resolve issue'}), 500

@app.route('/api/issues/<int:issue_id>/check', methods=['PUT'])
def check_issue(issue_id):
    try:
        with Db() as db:
            # Mark the issue as checked (you can add a 'checked' column to the complaint table if needed)
            query = """
                UPDATE complaint
                SET checked = 1
                WHERE complaintID = %s
            """
            db.execute(query, (issue_id,))
            app.logger.info(f"Issue {issue_id} checked successfully")
        
        return jsonify({'success': True, 'message': 'Issue checked successfully'})
    except Exception as e:
        app.logger.error(f"Error checking issue: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'message': 'Failed to check issue'}), 500



@app.route('/admin', methods=['GET'])
def admin():
    try:
        with Db() as db:
            # Fetch complaintID, category, description, and status from the complaint table
            db.execute("""
                SELECT complaintID, category, description, status
                FROM complaint
            """)
            complaints = db.fetchall()

            # Fetch total number of users
            db.execute("SELECT COUNT(*) AS total_users FROM users")
            total_users = db.fetchone()['total_users']

            # Fetch count of active issues (status = 'Pending' or 'In Progress')
            db.execute("""
                SELECT COUNT(*) AS active_issues
                FROM complaint
                WHERE status IN ('Pending', 'In Progress')
            """)
            active_issues = db.fetchone()['active_issues']

            # Fetch count of resolved issues (status = 'Resolved')
            db.execute("""
                SELECT COUNT(*) AS resolved_issues
                FROM complaint
                WHERE status = 'Resolved'
            """)
            resolved_issues = db.fetchone()['resolved_issues']

        # Pass the data to the template
        return render_template('admin.html', 
                             complaints=complaints,
                             total_users=total_users,
                             active_issues=active_issues,
                             resolved_issues=resolved_issues)

    except Exception as e:
        app.logger.error(f"Error fetching admin data: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'message': 'Error fetching admin data'}), 500

@app.route('/admin/add-user', methods=['POST'])
def admin_add_user():
    try:
        data = request.get_json()

        if not data:
            return jsonify({'success': False, 'message': 'Invalid JSON input'}), 400

        email = data.get('email')
        password = data.get('password')
        role = data.get('role').upper()  # Ensure consistency

        if not all([email, password, role]):
            return jsonify({'success': False, 'message': 'All fields are required'}), 400

        if role not in ["MUNICIPALITY", "PWD"]:
            return jsonify({'success': False, 'message': 'Invalid role'}), 400

        # Assign fixed deptID based on role
        dept_id = 2 if role == "MUNICIPALITY" else 1

        with Db() as db:
            db.execute("START TRANSACTION")

            try:
                # Ensure the department exists
                db.execute("SELECT deptID FROM department WHERE deptID = %s", (dept_id,))
                existing_department = db.fetchone()

                if not existing_department:
                    db.execute("INSERT INTO department (deptID, name) VALUES (%s, %s)", (dept_id, role))

                # Determine the correct table
                table_name = "municipality" if role == "MUNICIPALITY" else "pwd"

                # Ensure email is unique
                db.execute(f"SELECT id FROM {table_name} WHERE email = %s", (email,))
                existing_user = db.fetchone()

                if existing_user:
                    return jsonify({'success': False, 'message': 'Email already exists'}), 400

                # Insert into role-specific table (municipality or pwd)
                db.execute(
                    f"INSERT INTO {table_name} (deptID, name, email, password) VALUES (%s, %s, %s, %s)",
                    (dept_id, role, email, password)
                )

                # Insert into officials table
                db.execute(
                    "INSERT INTO officials (name, email, password, deptID) VALUES (%s, %s, %s, %s)",
                    (role, email, password, dept_id)
                )

                db.execute("COMMIT")

                return jsonify({
                    'success': True,
                    'message': 'User added successfully',
                    'data': {
                        'deptID': dept_id,
                        'email': email,
                        'role': role
                    }
                })

            except Exception as e:
                db.execute("ROLLBACK")
                app.logger.error(f"Database error: {str(e)}")
                return jsonify({'success': False, 'message': 'Database error occurred'}), 500

    except Exception as e:
        app.logger.error(f"Unexpected error: {str(e)}")
        return jsonify({'success': False, 'message': 'An unexpected error occurred'}), 500



@app.route('/get-officials', methods=['GET'])
def get_officials():
    try:
        with Db() as db:
            db.execute("SELECT officialID, name, email, deptID FROM officials")
            officials = db.fetchall()
            return jsonify([dict(official) for official in officials])
    except Exception as e:
        app.logger.error(f"Error fetching officials: {str(e)}")
        return jsonify({'success': False, 'message': 'Error fetching officials'}), 500
    
    
@app.route('/delete-official/<int:officialID>', methods=['DELETE'])
def delete_official(officialID):
    try:
        with Db() as db:
            db.execute("START TRANSACTION")

            try:
                # Get the official's details (including deptID) before deletion
                db.execute("SELECT deptID, email FROM officials WHERE officialID = %s", (officialID,))
                official = db.fetchone()

                if not official:
                    return jsonify({'success': False, 'message': 'Official not found'}), 404

                dept_id = official['deptID']
                email = official['email']

                # Delete from officials table
                db.execute("DELETE FROM officials WHERE officialID = %s", (officialID,))

                # Delete from role-specific table (municipality or pwd)
                db.execute("DELETE FROM municipality WHERE email = %s", (email,))
                db.execute("DELETE FROM pwd WHERE email = %s", (email,))

                # Check if the department has any remaining officials
                db.execute("SELECT COUNT(*) AS count FROM officials WHERE deptID = %s", (dept_id,))
                count_result = db.fetchone()

                # If no officials left in the department, delete the department
                if count_result['count'] == 0:
                    db.execute("DELETE FROM department WHERE deptID = %s", (dept_id,))

                db.execute("COMMIT")
                return jsonify({'success': True, 'message': 'Official and associated records deleted successfully'})

            except Exception as e:
                db.execute("ROLLBACK")
                app.logger.error(f"Database error during deletion: {str(e)}")
                return jsonify({'success': False, 'message': 'Database error during deletion'}), 500

    except Exception as e:
        app.logger.error(f"Unexpected error: {str(e)}")
        return jsonify({'success': False, 'message': 'An unexpected error occurred'}), 500

# Update the model loading code to:
# model = YOLO(os.environ.get('YOLO_MODEL_PATH')) 

@app.route('/report_issue', methods=['GET'])
def report_issue():
    # Get userID and email from query parameters
    user_id = request.args.get('userID')
    email = request.args.get('email')
    print("USerID is....",user_id)
    print("EMAIL iss...",email)
    if not user_id or not email:
        return redirect('/login')  # Redirect to login if parameters are missing

    try:
        with Db() as db:
            # Verify the user exists in the users table
            db.execute("SELECT userID FROM users WHERE email = %s AND userID = %s", (email, user_id))
            user = db.fetchone()

            if not user:
                return redirect('/login')  # Redirect to login if user is invalid

        # If the user exists, render the report issue page
        return render_template('report_issue.html')

    except Exception as e:
        app.logger.error(f"Error verifying user: {str(e)}", exc_info=True)
        return redirect('/login')

@app.route('/submit_issue', methods=['POST'])
def submit_issue():
    try:
        # Validate required fields
        if not all(key in request.form for key in ['title', 'description', 'location']):
            raise ValueError("Missing required fields")
        
        title = request.form['title']
        description = request.form['description']
        location = request.form['location']
        image = request.files.get('image')
        user_id = session.get('userID')  # Get userID from session

        if not user_id:
            raise ValueError("User not logged in. Please log in to report an issue.")

        # Process image and get prediction
        category = "General"  # Default category
        filename = None
        if image and image.filename != '':
            if not allowed_file(image.filename):
                raise ValueError("Invalid file type")
            
            # Create the complaint_images folder if it doesn't exist
            image_folder = os.path.join(app.static_folder, 'complaint_images')
            os.makedirs(image_folder, exist_ok=True)

            # Generate a unique filename
            filename = secure_filename(f"{datetime.now().timestamp()}_{image.filename}")
            upload_path = os.path.join(image_folder, filename)
            image.save(upload_path)
            
            # YOLO prediction
            img = Image.open(image.stream)
            results = model.predict(img)
            if results and len(results[0]) > 0:
                class_id = int(results[0].boxes.cls[0])
                category = model.names[class_id]
            else:
                # If no prediction is made, return a popup message
                return jsonify({
                    'success': False,
                    'message': 'Image not detected. Please upload a valid image.'
                }), 400

        # Determine department based on category
        with Db() as db:
            category_lower = category.lower()
            app.logger.info(f"Looking up department for category: {category_lower}")

            if category_lower == 'waste':
                dept_name = 'Municipality'
            elif category_lower == 'pothole':
                dept_name = 'Pwd'
            else:
                raise ValueError("Invalid category. Please provide a valid issue category.")

            # Fetch department ID
            db.execute("SELECT deptID FROM department WHERE name = %s", (dept_name,))
            dept_result = db.fetchone()
            if not dept_result:
                raise ValueError(f"No department found for category '{category}'. Please contact support.")
            
            dept_id = dept_result['deptID']
            app.logger.info(f"Assigned department: {dept_name} (ID: {dept_id})")

            # Insert into complaint table
            query = """
            INSERT INTO complaint 
                (title, description, photo, geoLocation, category, userID, assignedDept)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            values = (title, description, filename, location, category, user_id, dept_id)
            db.execute(query, values)

            # Get the last inserted complaint ID
            complaint_id = db.cursor.lastrowid

            # Insert into imagerecognition table
            query = """
            INSERT INTO imagerecognition 
                (model, detectedIssueType, complaintID)
            VALUES (%s, %s, %s)
            """
            values = ("yolo11", category, complaint_id)  # Use "yolo11" as the model name
            db.execute(query, values)

        # Customize success message based on department
        if dept_name == 'Municipality':
            success_message = f"Issue assigned to Municipality."
        else:
            success_message = f"Issue assigned to PWD."

        # Return success message
        return jsonify({
            'success': True,
            'message': success_message,
            'image_url': f"/static/complaint_images/{filename}" if filename else None
        })

    except ValueError as ve:
        app.logger.error(f"Validation error: {str(ve)}", exc_info=True)
        return jsonify({'success': False, 'message': str(ve)}), 400
    except RuntimeError as re:
        app.logger.error(f"Runtime error: {str(re)}", exc_info=True)
        return jsonify({'success': False, 'message': str(re)}), 500
    except Exception as e:
        app.logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'message': 'An unexpected error occurred.'}), 500


@app.route('/get_issues', methods=['GET'])
def get_issues():
    try:
        user_id = session.get('userID')  # Get userID from session
        if not user_id:
            return jsonify({'success': False, 'message': 'User not logged in. Please log in to view issues.'}), 401

        with Db() as db:
            # Fetch issues for the logged-in user
            db.execute("""
                SELECT complaintID, title, status 
                FROM complaint 
                WHERE userID = %s
                ORDER BY complaintID DESC
            """, (user_id,))
            issues = db.fetchall()

        # Return issues as JSON
        return jsonify({
            'success': True,
            'issues': issues
        })

    except Exception as e:
        app.logger.error(f"Error fetching issues: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'message': 'Failed to fetch issues.'}), 500

@app.route('/get-users')
def get_users():
    try:
        with Db() as db:
            query = """
                SELECT a.adminID, a.email, a.name, d.deptID
                FROM admin a
                JOIN department d ON a.name = d.name
            """
            db.execute(query)
            rows = db.fetchall()
            app.logger.info(f"Raw database rows: {rows}")

            users = [{
                'id': row['adminID'],
                'email': row['email'],
                'role': row['name'],
                'deptID': row['deptID']
            } for row in rows]
            
            app.logger.info(f"Processed users: {users}")
            return jsonify(users)
    except Exception as e:
        app.logger.error(f"Error fetching users: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/delete-user/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    try:
        with Db() as db:
            db.execute("START TRANSACTION")

            db.execute("SELECT deptID, name FROM department WHERE deptID = %s", (user_id,))
            dept_result = db.fetchone()

            if not dept_result:
                db.execute("ROLLBACK")
                return jsonify({'success': False, 'message': 'User not found'}), 404

            dept_id, dept_name = dept_result['deptID'], dept_result['name']

            db.execute("DELETE FROM admin WHERE adminID = %s", (user_id,))
            db.execute("DELETE FROM department WHERE deptID = %s", (dept_id,))

            table_name = "municipality" if dept_name == "MUNICIPALITY" else "pwd"
            db.execute(f"DELETE FROM {table_name} WHERE deptID = %s", (dept_id,))

            db.execute("COMMIT")

            socketio.emit('user_deleted', {'id': user_id})
            return jsonify({'success': True, 'message': 'User deleted successfully'})

    except Exception as e:
        return jsonify({'success': False, 'message': 'An error occurred'}), 500

@app.route('/update-user/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    try:
        data = request.get_json()
        if not data or 'email' not in data or 'role' not in data:
            return jsonify({'success': False, 'message': 'Missing required fields'}), 400

        email, role = data['email'], data['role']

        with Db() as db:
            db.execute("START TRANSACTION")
            db.execute("UPDATE admin SET email = %s, name = %s WHERE adminID = %s", (email, role, user_id))
            db.execute("UPDATE department d JOIN admin a ON a.name = d.name SET d.name = %s WHERE a.adminID = %s",
                      (role, user_id))
            db.execute("COMMIT")

        socketio.emit('user_updated', {'id': user_id, 'email': email, 'role': role})
        return jsonify({'success': True, 'message': 'User updated successfully'})

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/submit_feedback', methods=['POST'])
def submit_feedback():
    try:
        data = request.get_json()
        user_id = session.get('userID')
        complaint_id = data.get('complaintID')
        rating = data.get('rating')
        comments = data.get('comments')

        if not user_id:
            return jsonify({'success': False, 'message': 'User not logged in.'}), 401

        if not all([complaint_id, rating, comments]):
            return jsonify({'success': False, 'message': 'All fields are required.'}), 400

        with Db() as db:
            # Insert feedback into the feedback table
            query = """
                INSERT INTO feedback 
                    (userID, complaintID, rating, comments)
                VALUES (%s, %s, %s, %s)
            """
            values = (user_id, complaint_id, rating, comments)
            db.execute(query, values)

        return jsonify({'success': True, 'message': 'Feedback submitted successfully!'})
    except Exception as e:
        app.logger.error(f"Error submitting feedback: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'message': 'Failed to submit feedback.'}), 500

@app.route('/api/issues/municipality', methods=['GET'])
def get_municipality_issues():
    try:
        with Db() as db:
            # Fetch issues assigned to the Municipality department
            query = """
                SELECT c.complaintID AS id, c.category, c.description, c.status
                FROM complaint c
                JOIN department d ON c.assignedDept = d.deptID
                WHERE d.name = 'Municipality'
            """
            db.execute(query)
            issues = db.fetchall()
            app.logger.info(f"Fetched Municipality issues: {issues}")
        
        return jsonify(issues)
    except Exception as e:
        app.logger.error(f"Error fetching Municipality issues: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'message': 'Failed to fetch Municipality issues'}), 500

@app.route('/api/issues/counts/municipality', methods=['GET'])
def get_municipality_issue_counts():
    try:
        with Db() as db:
            # Fetch count of Pending issues with category 'Waste Management'
            query_pending = """
                SELECT COUNT(*) AS pending_count
                FROM complaint c
                JOIN department d ON c.assignedDept = d.deptID
                WHERE d.name = 'Municipality'
                AND c.category = 'waste'
                AND c.status = 'Pending'
            """
            db.execute(query_pending)
            pending_count = db.fetchone()['pending_count']
            print("Pending Counnts....",pending_count)

            # Fetch count of Resolved issues
            query_resolved = """
                SELECT COUNT(*) AS resolved_count
                FROM complaint c
                JOIN department d ON c.assignedDept = d.deptID
                WHERE d.name = 'Municipality'
                AND c.status = 'Resolved'
            """
            db.execute(query_resolved)
            resolved_count = db.fetchone()['resolved_count']

        return jsonify({
            'pending_count': pending_count,
            'resolved_count': resolved_count
        })
    except Exception as e:
        app.logger.error(f"Error fetching Municipality issue counts: {str(e)}", exc_info=True)
        return jsonify({'pending_count': 0, 'resolved_count': 0}), 500

@app.route('/api/issues/pwd', methods=['GET'])
def get_pwd_issues():
    try:
        with Db() as db:
            # Fetch issues assigned to the PWD department
            query = """
                SELECT c.complaintID AS id, c.category, c.description, c.status
                FROM complaint c
                JOIN department d ON c.assignedDept = d.deptID
                WHERE d.name = 'Pwd'
            """
            db.execute(query)
            issues = db.fetchall()
            app.logger.info(f"Fetched PWD issues: {issues}")
        
        return jsonify(issues)
    except Exception as e:
        app.logger.error(f"Error fetching PWD issues: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'message': 'Failed to fetch PWD issues'}), 500

@app.route('/send_otp', methods=['POST'])
def send_otp():
    try:
        data = request.get_json()
        email = data.get('email')

        if not email:
            return jsonify({'success': False, 'message': 'Email is required.'}), 400

        with Db() as db:
            # Check if the email exists in the users table
            db.execute("SELECT userID FROM users WHERE email = %s", (email,))
            user = db.fetchone()

            # If the user doesn't exist, create a new user
            if not user:
                db.execute("INSERT INTO users (email) VALUES (%s)", (email,))
                user_id = db.cursor.lastrowid
            else:
                user_id = user['userID']

            # Generate a random OTP (e.g., 6 digits)
            otp = ''.join(random.choices('0123456789', k=6))

            # Update the OTP in the users table
            db.execute("UPDATE users SET otp = %s WHERE userID = %s", (otp, user_id))

            # TODO: Send the OTP to the user's email (implement email sending logic here)

            return jsonify({
                'success': True,
                'message': 'OTP sent successfully!'
            })

    except Exception as e:
        app.logger.error(f"Error sending OTP: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'message': 'Failed to send OTP.'}), 500

@app.route('/verify_otp', methods=['POST'])
def verify_otp():
    try:
        data = request.get_json()
        email = data.get('email')
        otp = data.get('otp')
        print("VERIFY OTP DATA isss...", data)

        if not email or not otp:
            return jsonify({'success': False, 'message': 'Email and OTP are required.'}), 400

        with Db() as db:
            # Fetch the OTP and its timestamp from the database
            db.execute("""
                SELECT userID, otp_timestamp
                FROM users
                WHERE email = %s AND otp = %s
            """, (email, otp))
            user = db.fetchone()

            if not user:
                return jsonify({'success': False, 'message': 'Invalid OTP or email.'}), 401

            # Check if the OTP is expired (older than 5 minutes)
            otp_timestamp = user['otp_timestamp']
            if datetime.now() - otp_timestamp > timedelta(minutes=5):
                return jsonify({'success': False, 'message': 'OTP has expired.'}), 401

            # Set userID in session
            session['userID'] = user['userID']

            # Return userID and email in the redirect URL
            return jsonify({
                'success': True,
                'message': 'OTP verified successfully!',
                'redirect': f'/report_issue?userID={user["userID"]}&email={email}'
            })

    except Exception as e:
        app.logger.error(f"Error verifying OTP: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'message': 'Failed to verify OTP.'}), 500

@app.route('/api/issues/counts/pwd', methods=['GET'])
def get_pwd_issue_counts():
    try:
        with Db() as db:
            # Fetch count of Pending issues with category 'Pothole'
            query_pending = """
                SELECT COUNT(*) AS pending_count
                FROM complaint c
                JOIN department d ON c.assignedDept = d.deptID
                WHERE d.name = 'Pwd'
                AND c.category = 'pothole'
                AND c.status = 'Pending'
            """
            db.execute(query_pending)
            pending_count = db.fetchone()['pending_count']

            # Fetch count of Resolved issues
            query_resolved = """
                SELECT COUNT(*) AS resolved_count
                FROM complaint c
                JOIN department d ON c.assignedDept = d.deptID
                WHERE d.name = 'Pwd'
                AND c.status = 'Resolved'
            """
            db.execute(query_resolved)
            resolved_count = db.fetchone()['resolved_count']

        return jsonify({
            'pending_count': pending_count,
            'resolved_count': resolved_count
        })
    except Exception as e:
        app.logger.error(f"Error fetching PWD issue counts: {str(e)}", exc_info=True)
        return jsonify({'pending_count': 0, 'resolved_count': 0}), 500

@app.route('/api/feedback/pwd', methods=['GET'])
def get_pwd_feedback():
    try:
        with Db() as db:
            # Fetch feedback for issues assigned to the PWD department
            query = """
                SELECT f.feedbackID, f.rating, f.comments, c.complaintID, c.title, u.email
                FROM feedback f
                JOIN complaint c ON f.complaintID = c.complaintID
                JOIN users u ON f.userID = u.userID
                JOIN department d ON c.assignedDept = d.deptID
                WHERE d.name = 'PWD' AND f.userID IS NOT NULL
            """
            db.execute(query)
            feedback = db.fetchall()
        
        return jsonify(feedback)
    except Exception as e:
        app.logger.error(f"Error fetching PWD feedback: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'message': 'Failed to fetch feedback'}), 500




@app.route('/api/feedback/municipality', methods=['GET'])
def get_municipality_feedback():
    try:
        with Db() as db:
            # Fetch feedback for issues assigned to the PWD department
            query = """
                SELECT f.feedbackID, f.rating, f.comments, c.complaintID, c.title, u.email
                FROM feedback f
                JOIN complaint c ON f.complaintID = c.complaintID
                JOIN users u ON f.userID = u.userID
                JOIN department d ON c.assignedDept = d.deptID
                WHERE d.name = 'MUNICIPALITY' AND f.userID IS NOT NULL
            """
            db.execute(query)
            feedback = db.fetchall()
        
        return jsonify(feedback)
    except Exception as e:
        app.logger.error(f"Error fetching PWD feedback: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'message': 'Failed to fetch feedback'}), 500



@app.route('/logout', methods=['GET'])
def logout():
    session.clear()  # Clear the session
    app.logger.info("Session cleared on logout")  # Log session clearing
    return redirect(url_for('index'))  # Redirect to the home page

@app.before_request
def check_login():
    # List of routes that don't require authentication
    allowed_routes = ['login', 'verify_otp', 'static', 'index', 'admin_login']
    
    # If the route is allowed, skip authentication
    if request.endpoint in allowed_routes:
        return

    # Check for session keys based on user roles
    if 'userID' in session:  # Regular user
        return
    elif 'admin_id' in session:  # Admin user
        return
    elif 'dept_id' in session and 'role' in session:  # Municipality, PWD, or Official
        return
    else:
        # If no valid session key is found, redirect to the home page
        return redirect(url_for('index'))

@app.after_request
def add_no_cache_headers(response):
    # Add headers to prevent caching
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

if __name__ == '__main__':
    app.run(debug=True,)
    