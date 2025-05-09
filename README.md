# AI Study Assistant

An intelligent study assistant application built with Flask that helps students manage and process their study materials using AI-powered features and a modern, user-friendly interface.

## Features

- Document processing and analysis
- AI-powered study assistance (Claude AI integration)
- Q&A Generator from documents
- User authentication and management
- PDF and document text extraction (OCR supported)
- Intelligent search and organization
- RESTful API endpoints
- Modern UI with modal popups for quick info

## Tech Stack

- **Backend Framework**: Flask 2.3.3
- **Database**: SQLAlchemy with Flask-Migrate
- **Authentication**: Flask-Login
- **AI Integration**: Claude AI (Anthropic)
- **Document Processing**: 
  - PyPDF2 for PDF handling
  - python-docx for Word documents
  - pytesseract for OCR capabilities
- **Vector Search**: FAISS for efficient similarity search

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Tesseract OCR (for document text extraction)
- Virtual environment (recommended)

### Install Tesseract OCR
- **Ubuntu:**
  ```bash
  sudo apt-get update && sudo apt-get install -y tesseract-ocr
  ```
- **Windows:**
  Download and install from: https://github.com/tesseract-ocr/tesseract

## Installation

1. Clone the repository:
```bash
git clone https://github.com/amao4t/AI_Study_Assistant.git
cd AI_Study_Assistant
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
Create a `.env` file in the root directory with the following variables:
```
FLASK_APP=run.py
FLASK_ENV=development
SECRET_KEY=your-secret-key
DATABASE_URL=your-database-url
ANTHROPIC_API_KEY=your-claude-api-key
```

5. Initialize the database:
```bash
flask db upgrade
```

## Running the Application

1. Start the development server:
```bash
python run.py
```

The application will be available at `http://localhost:5000`

## Project Structure

```
AI_Study_Assistant/
├── app/
│   ├── api/            # API endpoints
│   ├── models/         # Database models
│   ├── services/       # Business logic
│   ├── static/         # Static files
│   ├── templates/      # HTML templates
│   └── utils/          # Utility functions
├── migrations/         # Database migrations
├── instance/           # Instance-specific files
├── requirements.txt    # Project dependencies
└── run.py              # Application entry point
```

## API Documentation

The application provides RESTful API endpoints for:
- User authentication
- Document management
- Study material processing
- AI-powered assistance

Detailed API documentation is available at `/api/docs` when running the application.

## Contact & Links

- **Email:** amao4t@csu.fullerton.edu
- **LinkedIn:** [Duong Manh Vu](https://www.linkedin.com/in/duong-vu-9723362b3/)
- **GitHub:** [amao4t](https://github.com/amao4t/)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

MIT License

Copyright (c) 2025 amao4t

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

## Support

For support, please contact: amao4t@csu.fullerton.edu