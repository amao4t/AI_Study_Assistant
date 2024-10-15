import traceback
from flask import Flask, request, jsonify, render_template, redirect, url_for, session, flash
from flask_wtf import CSRFProtect
from datetime import timedelta
from utils.auth import login_user, signup_user, logout_user
import os

# Import forms and utility functions
from forms import LoginForm, SignupForm, UploadForm
from utils.content import extract_content
from utils.summarizer import summarize_content, generate_quiz_questions

print("Initializing Flask application...")
app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Replace with a secure key
csrf = CSRFProtect(app)

ALLOWED_EXTENSIONS = {'txt', 'pdf', 'docx'}

# Function to check allowed file extensions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def home():
    print("Home page accessed")
    login_form = LoginForm()
    signup_form = SignupForm()
    upload_form = UploadForm()
    logged_in = 'username' in session
    return render_template('index.html', login_form=login_form, signup_form=signup_form, upload_form=upload_form, logged_in=logged_in)

@app.route('/upload', methods=['POST'])
def upload():
    if 'username' not in session:
        flash('Please login to access this feature.', 'danger')
        return redirect(url_for('home'))

    form = UploadForm()
    if form.validate_on_submit():
        file = form.studyMaterial.data

        if not allowed_file(file.filename):
            return jsonify({'error': 'Unsupported file type'}), 400

        try:
            # Extract content from the uploaded file
            content, error = extract_content(file)
            if error:
                return jsonify({'error': error}), 400

            # Validate content length for summarization
            if len(content) < 50:
                return jsonify({'error': 'Content too short for summarization'}), 400

            # Summarize the content
            summary, error = summarize_content(content)
            if error:
                return jsonify({'error': f'Error during summarization: {error}'}), 400

            # Generate quiz questions from the summary
            quiz_questions = generate_quiz_questions(summary)

            return jsonify({
                'summary': summary,
                'questions': quiz_questions
            })

        except Exception as e:
            # Log the detailed error to the console for debugging
            print("Error during processing:")
            print(traceback.format_exc())  # Print the full traceback for detailed error
            return jsonify({'error': 'An unexpected error occurred during processing. Please check the server logs for more details.'}), 500

    flash('Invalid form submission.', 'danger')
    return redirect(url_for('home'))


@app.route('/login', methods=['POST'])
def login():
    print("Login route accessed")
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        remember_me = form.remember_me.data

        success, message = login_user(username, password, remember_me)
        if success:
            flash(message, 'success')
            return redirect(url_for('home'))
        else:
            flash(message, 'danger')
            return redirect(url_for('home'))

    flash('Invalid form submission.', 'danger')
    return redirect(url_for('home'))

@app.route('/signup', methods=['POST'])
def signup():
    print("Signup route accessed")
    form = SignupForm()
    if form.validate_on_submit():
        username = form.new_username.data
        password = form.new_password.data
        confirm_password = form.confirm_password.data

        success, message = signup_user(username, password, confirm_password)
        if success:
            flash(message, 'success')
            return redirect(url_for('home'))
        else:
            flash(message, 'danger')
            return redirect(url_for('home'))

    flash('Invalid form submission.', 'danger')
    return redirect(url_for('home'))

@app.route('/logout')
def logout():
    print("Logout route accessed")
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('home'))

if __name__ == '__main__':
    os.makedirs('uploads', exist_ok=True)
    app.run(debug=True)
