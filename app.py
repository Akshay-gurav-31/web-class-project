from flask import Flask, render_template, request, redirect, url_for, flash, session, abort, jsonify, send_file
from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.lib.colors import Color
from io import BytesIO
from datetime import datetime
import qrcode
from supabase import create_client, Client
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
import json
from functools import wraps

app = Flask(__name__)
app.secret_key = "supersecret123"

# Configurations
UPLOAD_FOLDER = 'static/uploads'
DATA_FILE = 'enrollments.json'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
TEMPLATE_PDF = "static/images/Template.pdf"  # Fallback template
CERTIFICATES_DIR = "static/certificates"
VIDEOS_DIR = "static/videos"

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB

# Ensure folders exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs('static', exist_ok=True)
os.makedirs('templates', exist_ok=True)
os.makedirs('static/images', exist_ok=True)
os.makedirs(CERTIFICATES_DIR, exist_ok=True)
os.makedirs(VIDEOS_DIR, exist_ok=True)

# Supabase Config
SUPABASE_URL = "https://siolenykcgnnthwjongt.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InNpb2xlbnlrY2dubnRod2pvbmd0Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjI3NDYyNzEsImV4cCI6MjA3ODMyMjI3MX0.DES4jyP4UDwTzqGnns_kouhhKdmFk87a-CVHhHsNQFI"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

ADMIN_EMAIL = "admin@rdguravmusic.com"
ADMIN_PASSWORD = "Admin@123"

# Course to certificate template mapping
COURSE_CERTIFICATE_MAP = {
    'guitar': 'guitar_certificate.pdf',
    'electric_guitar': 'electrical_guitar_certificate.pdf',
    'electric-guitar': 'electrical_guitar_certificate.pdf',
    'piano': 'electrical_keyboard_certificate.pdf',  # Piano uses keyboard certificate
    'ukulele': 'ukulele_certificate.pdf',
}

# Course video lesson configurations
COURSE_VIDEOS = {
    'guitar': [
        {'title': 'Introduction to Guitar', 'filename': 'intro.mp4', 'description': 'Learn the basics of guitar playing'},
        {'title': 'Basic Chords', 'filename': 'chords.mp4', 'description': 'Master fundamental guitar chords'},
        {'title': 'Strumming Patterns', 'filename': 'strumming.mp4', 'description': 'Learn various strumming techniques'},
        {'title': 'Advanced Techniques', 'filename': 'advanced.mp4', 'description': 'Explore advanced guitar techniques'}
    ],
    'electric_guitar': [
        {'title': 'Introduction to Electric Guitar', 'filename': 'intro.mp4', 'description': 'Introduction to electric guitar'},
        {'title': 'Power Chords & Riffs', 'filename': 'power_chords.mp4', 'description': 'Learn power chords and riffs'},
        {'title': 'Solo Techniques', 'filename': 'solo.mp4', 'description': 'Master solo playing techniques'},
        {'title': 'Effects & Amplification', 'filename': 'effects.mp4', 'description': 'Understanding guitar effects and amps'}
    ],
    'piano': [
        {'title': 'Introduction to Piano', 'filename': 'intro.mp4', 'description': 'Get started with piano basics'},
        {'title': 'Basic Piano Techniques', 'filename': 'basic.mp4', 'description': 'Learn fundamental piano techniques'},
        {'title': 'Piano Practice', 'filename': 'practice.mp4', 'description': 'Practice exercises and techniques'}
    ],
    'ukulele': [
        {'title': 'Introduction to Ukulele', 'filename': 'intro.mp4', 'description': 'Introduction to ukulele playing'},
        {'title': 'Basic Chords & Strumming', 'filename': 'chords_strumming.mp4', 'description': 'Learn basic chords and strumming'},
        {'title': 'Ukulele Techniques', 'filename': 'techniques.mp4', 'description': 'Advanced ukulele techniques'},
        {'title': 'Popular Songs', 'filename': 'songs.mp4', 'description': 'Play popular ukulele songs'}
    ]
}

# Ensure video directories for all courses exist
def ensure_course_video_directories():
    """Create video directories for each course"""
    for course_slug in COURSE_VIDEOS.keys():
        course_dir = os.path.join(VIDEOS_DIR, course_slug)
        os.makedirs(course_dir, exist_ok=True)

# Initialize video directories on startup
ensure_course_video_directories()

def get_student_by_email(email):
    try:
        response = supabase.table("students").select("*").eq("email", email).execute()
        if response.data:
            return response.data[0]
        return None
    except Exception as e:
        print(f"Error fetching student by email: {e}")
        return None

def get_student_by_id(student_id):
    try:
        response = supabase.table("students").select("*").eq("id", student_id).execute()
        if response.data:
            return response.data[0]
        return None
    except Exception as e:
        print(f"Error fetching student by ID: {e}")
        return None

def get_user(email):
    """Get user certificate information from students table"""
    try:
        response = supabase.table("students").select("name, certificate_generated, certificate_file").eq("email", email).execute()
        if response.data:
            return response.data[0]
        return None
    except Exception as e:
        print(f"Error fetching user: {e}")
        return None

def save_certificate(email, name, pdf_bytes):
    """Update certificate info in DB"""
    try:
        response = supabase.table("students").update({
            "name": name,
            "certificate_generated": True,
            "certificate_file": pdf_bytes
        }).eq("email", email).execute()
        return response
    except Exception as e:
        print(f"Error saving certificate: {e}")
        return None

# ----------------- Helper Functions -----------------
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def load_enrollments():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    return []

def save_enrollments(enrollments):
    with open(DATA_FILE, 'w') as f:
        json.dump(enrollments, f, indent=2)

def generate_enrollment_id():
    enrollments = load_enrollments()
    if not enrollments:
        return "ENR001"
    last_id = enrollments[-1]['id']
    num = int(last_id.replace('ENR', '')) + 1
    return f"ENR{num:03d}"

def get_user_course_slug(email):
    """Get the course slug for a user from their enrolled courses"""
    student = get_student_by_email(email)
    if not student:
        return None
    
    raw = student.get('enrolled_courses') or '[]'
    try:
        courses_data = json.loads(raw) if isinstance(raw, (str, bytes)) else raw
        if courses_data and len(courses_data) > 0:
            course_item = courses_data[-1]
            if isinstance(course_item, dict):
                slug = course_item.get('slug') or ''
                if slug:
                    return slug.lower().replace('-', '_')
            elif isinstance(course_item, str):
                return course_item.strip().lower().replace('-', '_')
    except Exception:
        pass
    
    current_course = student.get('current_course', '').strip().lower()
    if current_course:
        return current_course.replace('-', '_').replace(' ', '_')
    return None

def get_user_course_name(email):
    """Get the course name for a user from their enrolled courses"""
    student = get_student_by_email(email)
    if not student:
        return "Music Course"
    raw = student.get('enrolled_courses') or '[]'
    try:
        courses_data = json.loads(raw) if isinstance(raw, (str, bytes)) else raw
        if courses_data and len(courses_data) > 0:
            if isinstance(courses_data[-1], dict):
                return courses_data[-1].get('name', student.get('current_course', 'Music Course'))
            elif isinstance(courses_data[-1], str):
                return courses_data[-1].replace('_', ' ').title()
    except Exception:
        pass
    return student.get('current_course') or 'Music Course'

def get_certificate_template(course_slug):
    """Get the certificate template path for a course"""
    if not course_slug:
        return TEMPLATE_PDF
    course_slug_norm = course_slug.lower().replace('-', '_')
    cert_filename = COURSE_CERTIFICATE_MAP.get(course_slug_norm)
    if cert_filename:
        cert_path = os.path.join(CERTIFICATES_DIR, cert_filename)
        if os.path.exists(cert_path):
            return cert_path
    return TEMPLATE_PDF

def get_course_videos(course_slug):
    """Get video list for a course with file paths"""
    if not course_slug:
        return []
    normalized_slug = course_slug.lower().replace('-', '_')
    video_config = COURSE_VIDEOS.get(normalized_slug, [])
    videos = []
    course_video_dir = os.path.join(VIDEOS_DIR, normalized_slug)
    for idx, video_info in enumerate(video_config):
        filename = video_info.get('filename', '')
        video_path = os.path.join(course_video_dir, filename)
        if os.path.exists(video_path):
            video_url = f"/static/videos/{normalized_slug}/{filename}"
        else:
            # fallback or placeholder
            video_url = f"/static/videos/{normalized_slug}/{filename}"
        videos.append({
            'title': video_info.get('title', f'Lesson {idx + 1}'),
            'src': video_url,
            'filename': filename,
            'description': video_info.get('description', ''),
            'watched': False,
            'index': idx
        })
    return videos

def generate_certificate_pdf(name, email, course_name=None, course_slug=None):
    """Generate a certificate PDF with the name filled in the blank area."""
    if not course_slug:
        course_slug = get_user_course_slug(email)
    if not course_name:
        course_name = get_user_course_name(email)
    template_path = get_certificate_template(course_slug)
    if not os.path.exists(template_path):
        raise FileNotFoundError(f"Certificate template not found: {template_path}")

    # Create a PDF overlay with the name
    packet = BytesIO()
    c = canvas.Canvas(packet)

    # Set font and size for the name
    c.setFont("Helvetica-Bold", 36)

    # Calculate text width to center it
    page_width = 842  # Assuming A4 landscape width in points
    text_width = c.stringWidth(name, "Helvetica-Bold", 36)
    name_x = (page_width - text_width) / 2  # Center horizontally
    name_y = 380  # Vertical position (adjust as needed)

    # Draw the name at the specified position
    c.setFillColor(Color(0.749, 0.557, 0.298))
    c.drawString(name_x, name_y, name)

    # Add other details (course, date) if needed
    c.setFont("Helvetica", 16)
    course_y = name_y - 50
    c.drawString(name_x, course_y, f"Course: {course_name}")

    date_y = course_y - 30
    c.drawString(name_x, date_y, f"Date: {datetime.now().strftime('%B %d, %Y')}")

    c.save()

    # Merge overlay with template
    packet.seek(0)
    overlay_pdf = PdfReader(packet)
    template = PdfReader(open(template_path, "rb"))
    page = template.pages[0]
    page.merge_page(overlay_pdf.pages[0])

    # Save the final PDF
    output = PdfWriter()
    output.add_page(page)
    final_pdf = BytesIO()
    output.write(final_pdf)
    final_pdf.seek(0)
    return final_pdf.getvalue()

# ----------------- Routes -----------------
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/syllabus/<page>.html')
def syllabus_page(page):
    allowed = {'electric', 'guitar', 'piano', 'ukulele'}
    if page in allowed:
        return render_template(f'syllabus/{page}.html')
    abort(404)

# Signup
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        if not name or not email or not password:
            flash("Please fill all fields.", "danger")
            return redirect(url_for('signup'))
        if get_student_by_email(email):
            flash("Email already registered. Please login.", "warning")
            return redirect(url_for('login'))
        hashed_password = generate_password_hash(password)
        try:
            response = supabase.table("students").insert({
                "name": name,
                "email": email,
                "password": hashed_password,
                "current_course": "",
                "joining_date": datetime.now().date().isoformat(),
                "enrolled_courses": json.dumps([])
            }).execute()
            flash("Account created successfully! Please login.", 'success')
            return redirect(url_for('index'))
        except Exception as e:
            flash(f"Error creating account: {e}", 'danger')
    return render_template('signup.html')

# Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'loggedin' in session:
        return redirect(url_for('index'))
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        if not email or not password:
            flash("Please fill all fields!", 'danger')
            return redirect(url_for('login'))
        if email == ADMIN_EMAIL and password == ADMIN_PASSWORD:
            session['loggedin'] = True
            session['admin'] = True
            session['name'] = 'Administrator'
            flash('Welcome Administrator!', 'success')
            return redirect(url_for('index'))
        student = get_student_by_email(email)
        if student and check_password_hash(student['password'], password):
            session['loggedin'] = True
            session['id'] = student['id']
            session['name'] = student['name']
            flash(f"Welcome back, {student['name']}!", 'success')
            return redirect(url_for('index'))
        flash("Invalid email or password!", 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out.", 'info')
    return redirect(url_for('login'))

# Dashboard
@app.route('/dashboard')
def dashboard():
    if 'loggedin' not in session:
        flash("Please login to access dashboard.", 'warning')
        return redirect(url_for('login'))

    if session.get('admin'):
        return render_template('dashboard/dashboard.html',
            student={'name': 'Administrator', 'email': ADMIN_EMAIL},
            enrolled_courses=[],
            certificates=[],
            now=datetime.now()
        )

    student = get_student_by_id(session.get('id'))
    if not student:
        flash("Student not found. Please login again.", 'danger')
        return redirect(url_for('login'))

    raw = student.get('enrolled_courses') or '[]'
    try:
        courses_data = json.loads(raw) if isinstance(raw, (str, bytes)) else raw
    except Exception:
        courses_data = []

    def slugify(text):
        if not text:
            return ''
        text = str(text).strip().lower()
        return ''.join(ch if ch.isalnum() else '_' for ch in text).strip('_')

    normalized_courses = []
    for item in courses_data:
        if not item:
            continue
        if isinstance(item, str):
            slug = slugify(item)
            if not slug:
                continue
            name = item.replace('_', ' ').title()
            normalized_courses.append({
                'slug': slug,
                'name': name,
                'progress': 0,
                'completed': False,
                'enrollment_date': '',
                'continue_url': url_for('dashboard_course', course_slug=slug)
            })
            continue
        if isinstance(item, dict):
            slug_source = item.get('slug') or item.get('id') or item.get('name') or ''
            slug = slugify(slug_source)
            if not slug:
                slug = slugify(item.get('course') or item.get('title') or '')
            if not slug:
                continue
            name = item.get('name') or item.get('title') or slug.replace('_', ' ').title()
            progress = int(item.get('progress') or 0)
            completed = bool(item.get('completed')) if 'completed' in item else False
            enrollment_date = item.get('enrollment_date') or item.get('enrollmentDate') or ''
            normalized_courses.append({
                'slug': slug,
                'name': name,
                'progress': progress,
                'completed': completed,
                'enrollment_date': enrollment_date,
                'continue_url': url_for('dashboard_course', course_slug=slug)
            })
            continue

    return render_template('dashboard/dashboard.html',
        student=student,
        enrolled_courses=normalized_courses,
        certificates=[],
        now=datetime.now()
    )

# Certificate routes
@app.route('/certificate')
def certificate_index():
    if not session.get('loggedin'):
        flash("Please login to download your certificate.", "warning")
        return redirect(url_for('login'))
    if session.get('admin'):
        flash("Admin cannot download certificates.", "warning")
        return redirect(url_for('dashboard'))
    student = get_student_by_id(session.get('id'))
    if not student:
        flash("Student not found. Please login again.", 'danger')
        return redirect(url_for('login'))
    return redirect(url_for('enter_name', email=student['email']))

@app.route('/enter_name/<email>', methods=['GET', 'POST'])
def enter_name(email):
    if not session.get('loggedin'):
        flash("Please login to download your certificate.", "warning")
        return redirect(url_for('login'))

    user = get_user(email)
    if not user:
        flash("Invalid email or not enrolled.", 'danger')
        return redirect(url_for('dashboard'))

    certificate_generated = user.get('certificate_generated', 0)
    certificate_file = user.get('certificate_file')
    if certificate_generated and certificate_file:
        name = user.get('name', '')
        return send_file(
            BytesIO(certificate_file),
            as_attachment=True,
            download_name=f"{name}_certificate.pdf" if name else "certificate.pdf",
            mimetype="application/pdf"
        )

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        if not name:
            flash("Please enter your name.", "warning")
            return redirect(url_for('enter_name', email=email))
        course_slug = get_user_course_slug(email)
        course_name = get_user_course_name(email)
        try:
            pdf_bytes = generate_certificate_pdf(name, email, course_name, course_slug)
            save_certificate(email, name, pdf_bytes)
            return send_file(
                BytesIO(pdf_bytes),
                as_attachment=True,
                download_name=f"{name}_certificate.pdf",
                mimetype="application/pdf"
            )
        except Exception as e:
            flash(f"Error generating certificate: {str(e)}", "danger")
            return redirect(url_for('dashboard'))

    return render_template('enter_name.html', 
        email=email,
        name=user.get('name', ''),
        course_name=get_user_course_name(email)
    )

# Enrollment Routes
@app.route('/Enroll.html')
def enroll():
    return render_template('Enroll.html')

@app.route('/submit_enroll', methods=['POST'])
def submit_enrollment():
    try:
        student_name = request.form.get('studentName')
        student_email = request.form.get('studentEmail')
        student_mobile = request.form.get('studentMobile')
        student_address = request.form.get('studentAddress')
        course = request.form.get('course')
        if not all([student_name, student_email, student_mobile, student_address, course]):
            flash("Please fill all fields.", 'danger')
            return redirect(url_for('enroll'))
        if 'screenshot' not in request.files:
            flash("Upload payment screenshot.", 'danger')
            return redirect(url_for('enroll'))
        file = request.files['screenshot']
        if file.filename == '':
            flash("No file selected.", 'danger')
            return redirect(url_for('enroll'))
        if file and allowed_file(file.filename):
            enrollment_id = generate_enrollment_id()
            filename = f"{enrollment_id}_{secure_filename(file.filename or '')}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            enrollment = {
                'id': enrollment_id,
                'studentName': student_name,
                'studentEmail': student_email,
                'studentMobile': student_mobile,
                'studentAddress': student_address,
                'course': course,
                'screenshotFilename': filename,
                'enrollmentDate': datetime.now().isoformat(),
                'paymentStatus': 'pending'
            }
            enrollments = load_enrollments()
            enrollments.append(enrollment)
            save_enrollments(enrollments)
            return render_template('success.html', enrollment=enrollment)
        else:
            flash("Invalid file type.", 'danger')
            return redirect(url_for('enroll'))
    except Exception as e:
        flash(f"Error: {e}", 'danger')
        return redirect(url_for('enroll'))

@app.route('/dashboard/course/<course_slug>')
def dashboard_course(course_slug):
    normalized_slug = course_slug.lower().replace('-', '_')
    course_videos = get_course_videos(normalized_slug)
    if session.get('admin'):
        tpl = f"dashboard/dashboard_{normalized_slug}.html"
        if not os.path.exists(os.path.join(app.template_folder or 'templates', tpl)):
            abort(404)
        return render_template(tpl, student={'name': 'Administrator', 'email': ADMIN_EMAIL}, videos=course_videos)
    if 'loggedin' not in session or not session.get('id'):
        flash("Please login to access course dashboard.", "warning")
        return redirect(url_for('login'))
    student = get_student_by_id(session['id'])
    if not student:
        flash("Student not found. Please login again.", "danger")
        return redirect(url_for('login'))
    raw = student.get('enrolled_courses') or '[]'
    try:
        courses_data = json.loads(raw) if isinstance(raw, (str, bytes)) else raw
    except Exception:
        courses_data = []

    enrolled_slugs = set()
    for item in courses_data:
        if isinstance(item, str):
            slug = item.strip().lower().replace('-', '_')
            enrolled_slugs.add(slug)
        elif isinstance(item, dict):
            slug = (item.get('slug') or item.get('id') or item.get('name') or '').strip().lower()
            if not slug and item.get('name'):
                slug = item['name'].strip().lower().replace(' ', '_')
            if slug:
                slug = slug.replace('-', '_')
                enrolled_slugs.add(slug)

    if normalized_slug not in enrolled_slugs:
        flash("You are not enrolled in this course.", "warning")
        return redirect(url_for('dashboard'))

    tpl = f"dashboard/dashboard_{normalized_slug}.html"
    if not os.path.exists(os.path.join(app.template_folder or 'templates', tpl)):
        abort(404)
    return render_template(tpl, student=student, videos=course_videos)

# Context processor
@app.context_processor
def inject_current_user():
    user = None
    try:
        if session.get('loggedin'):
            if session.get('admin'):
                user = {'name': session.get('name'), 'is_admin': True}
            else:
                student = get_student_by_id(session.get('id'))
                if student:
                    user = student
                    user['is_admin'] = False
                else:
                    user = {'name': session.get('name'), 'is_admin': False} if session.get('name') else None
    except:
        user = {'name': session.get('name'), 'is_admin': False} if session.get('name') else None
    return dict(current_user=user)

# Admin Routes
@app.route('/admin')
def admin():
    if not session.get('admin'):
        abort(403)
    return render_template('admin.html')

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin'):
            return jsonify({'error': 'Unauthorized'}), 403
        return f(*args, **kwargs)
    return decorated_function

@app.route('/api/enrollments')
@admin_required
def api_enrollments():
    try:
        if not os.path.exists(DATA_FILE):
            return jsonify([])
        with open(DATA_FILE, 'r') as f:
            enrollments = json.load(f)
        return jsonify(enrollments)
    except Exception as e:
        app.logger.error(f"Error reading enrollments: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/enrollments/<enrollment_id>/approve', methods=['POST'])
@admin_required
def approve_enrollment(enrollment_id):
    try:
        if not os.path.exists(DATA_FILE):
            return jsonify({'error': 'No enrollments found'}), 404
        with open(DATA_FILE, 'r') as f:
            enrollments = json.load(f)
        enrollment = None
        for e in enrollments:
            if e.get('id') == enrollment_id:
                enrollment = e
                e['paymentStatus'] = 'approved'
                break
        if not enrollment:
            return jsonify({'error': 'Enrollment not found'}), 404
        student_email = enrollment.get('studentEmail')
        if not student_email:
            return jsonify({'error': 'Student email not found'}), 400
        try:
            # Get current enrolled courses
            student = get_student_by_email(student_email)
            if not student:
                return jsonify({'error': 'Student not found'}), 404
                
            current_courses = json.loads(student.get('enrolled_courses', '[]')) if student.get('enrolled_courses') else []
            course_slug = enrollment.get('course', '').lower().replace('-', '_')
            course_obj = {
                'slug': course_slug,
                'name': enrollment.get('course'),
                'progress': 0,
                'completed': False,
                'enrollment_date': enrollment.get('enrollmentDate')
            }
            if not any(c.get('slug') == course_obj['slug'] for c in current_courses):
                current_courses.append(course_obj)
                # Update student's enrolled courses
                supabase.table("students").update({
                    "enrolled_courses": json.dumps(current_courses)
                }).eq("email", student_email).execute()
            
            with open(DATA_FILE, 'w') as f:
                json.dump(enrollments, f, indent=2)
            return jsonify({'message': 'Enrollment approved and course added to student'})
        except Exception as e:
            return jsonify({'error': f"Database error: {str(e)}"}), 500
    except Exception as e:
        return jsonify({'error': f"Server error: {str(e)}"}), 500

@app.route('/api/enrollments/<enrollment_id>/reject', methods=['POST'])
@admin_required
def reject_enrollment(enrollment_id):
    try:
        if not os.path.exists(DATA_FILE):
            return jsonify({'error': 'No enrollments found'}), 404
        with open(DATA_FILE, 'r') as f:
            enrollments = json.load(f)
        found = False
        for e in enrollments:
            if e.get('id') == enrollment_id:
                e['paymentStatus'] = 'rejected'
                found = True
                break
        if not found:
            return jsonify({'error': 'Enrollment not found'}), 404
        with open(DATA_FILE, 'w') as f:
            json.dump(enrollments, f, indent=2)
        return jsonify({'message': 'Enrollment rejected successfully'})
    except Exception as e:
        app.logger.error(f"Error rejecting enrollment: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

# Run server
if __name__ == "__main__":
    app.run(debug=True)