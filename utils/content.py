import fitz  # PyMuPDF for handling PDF files
from docx import Document

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
