from flask import Flask, request, jsonify, render_template, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from flask_wtf import FlaskForm, CSRFProtect
from wtforms import StringField, PasswordField, FileField, SelectField, BooleanField
from wtforms.validators import InputRequired
import spacy
from transformers import pipeline
import fitz  # PyMuPDF for handling PDF files
from docx import Document  # python-docx for handling DOCX files
from datetime import timedelta
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Replace with a secure key
csrf = CSRFProtect(app)

# Simulated user database
users = {}

# Load spaCy model for NLP processing
nlp = spacy.load('en_core_web_sm')

# Load summarization model from HuggingFace
summarizer = pipeline('summarization')

# Allowed file extensions
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'docx'}

# Flask-WTF Form Classes
class LoginForm(FlaskForm):
    username = StringField('Username', validators=[InputRequired()])
    password = PasswordField('Password', validators=[InputRequired()])
    remember_me = BooleanField('Remember Me')

class SignupForm(FlaskForm):
    new_username = StringField('Username', validators=[InputRequired()])
    new_password = PasswordField('Password', validators=[InputRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[InputRequired()])

class UploadForm(FlaskForm):
    studyMaterial = FileField('Study Material', validators=[InputRequired()])
    summary_type = SelectField('Summary Length', choices=[('short', 'Short'), ('medium', 'Medium'), ('detailed', 'Detailed')])

# Helper function to extract content from files
def extract_content(file):
    content = ""
    try:
        if file.filename.endswith('.txt'):
            content = file.read().decode('utf-8')
        elif file.filename.endswith('.pdf'):
            with fitz.open(stream=file.read(), filetype="pdf") as pdf_document:
                for page_num in range(pdf_document.page_count):
                    page = pdf_document.load_page(page_num)
                    content += page.get_text()
        elif file.filename.endswith('.docx'):
            document = Document(file)
            for para in document.paragraphs:
                content += para.text + "\n"
    except Exception as e:
        return None, f"Error reading {file.filename}: {str(e)}"
    return content, None

# Function to check allowed file extensions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def home():
    login_form = LoginForm()
    signup_form = SignupForm()
    upload_form = UploadForm()
    return render_template('index.html', login_form=login_form, signup_form=signup_form, upload_form=upload_form)

@app.route('/upload', methods=['POST'])
def upload():
    if 'username' not in session:
        flash('Please login to access this feature.', 'danger')
        return redirect(url_for('home'))

    form = UploadForm()
    if form.validate_on_submit():
        file = form.studyMaterial.data
        summary_type = form.summary_type.data

        if not allowed_file(file.filename):
            return jsonify({'error': 'Unsupported file type'}), 400

        # Extract content from the uploaded file
        content, error = extract_content(file)
        if error:
            return jsonify({'error': error}), 400

        # Validate content length for summarization
        if len(content) < 50:
            return jsonify({'error': 'Content too short for summarization'}), 400
        elif len(content) > 10000:
            return jsonify({'error': 'Content too large to summarize, please reduce the size'}), 400

        # Set summarization length based on user input
        max_len, min_len = {
            'short': (60, 20),
            'medium': (150, 50),
            'detailed': (300, 100)
        }[summary_type]

        # Perform summarization
        try:
            summary = summarizer(content, max_length=max_len, min_length=min_len, do_sample=False)
        except Exception as e:
            return jsonify({'error': f'Error during summarization: {str(e)}'}), 400

        return jsonify({'summary': summary[0]['summary_text']})

    flash('Invalid form submission.', 'danger')
    return redirect(url_for('home'))

@app.route('/login', methods=['POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        remember_me = form.remember_me.data

        if not username or not password:
            flash('Both username and password are required.', 'danger')
            return redirect(url_for('home'))

        user = users.get(username)
        if user and check_password_hash(user['password'], password):
            session['username'] = username

            if remember_me:
                session.permanent = True  # Sets a long expiration time
                app.permanent_session_lifetime = timedelta(days=7)  # User will be remembered for 7 days

            flash('Login successful!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Invalid username or password', 'danger')
            return redirect(url_for('home'))

    flash('Invalid form submission.', 'danger')
    return redirect(url_for('home'))

@app.route('/signup', methods=['POST'])
def signup():
    form = SignupForm()
    if form.validate_on_submit():
        username = form.new_username.data
        password = form.new_password.data
        confirm_password = form.confirm_password.data

        if not username or not password or not confirm_password:
            flash('All fields are required.', 'danger')
            return redirect(url_for('home'))

        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return redirect(url_for('home'))

        if username in users:
            flash('Username already exists.', 'danger')
            return redirect(url_for('home'))

        users[username] = {'password': generate_password_hash(password)}
        flash('Account created successfully. Please login.', 'success')
        return redirect(url_for('home'))

    flash('Invalid form submission.', 'danger')
    return redirect(url_for('home'))

@app.route('/logout')
def logout():
    session.pop('username', None)
    flash('You have been logged out.', 'success')
    return redirect(url_for('home'))

if __name__ == '__main__':
    # Make sure any required directories exist
    os.makedirs('uploads', exist_ok=True)
    app.run(debug=True)