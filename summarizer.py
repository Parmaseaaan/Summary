from flask import Flask, render_template, request, flash, redirect
from werkzeug.utils import secure_filename
import os
import tempfile
import shutil
import requests
import fitz  # PyMuPDF
from paddleocr import PaddleOCR

app = Flask(__name__)
app.secret_key = "bigyanmokongpiso"

ALLOWED_EXTENSIONS = {'pdf'}

# Initialize PaddleOCR
ocr_model = PaddleOCR(lang='en')

# Function to check if file extension is allowed
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def summary(payload):
    API_URL2 = "https://api-inference.huggingface.co/models/facebook/bart-large-cnn"
    headers2 = {"Authorization": "Bearer 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"}

    response = requests.post(API_URL2, headers=headers2, json=payload)
    data = response.json()

    # Extract the 'summary_text' values from the list of dictionaries
    summary_texts = [item['summary_text'] for item in data]

    # Return the list of summary texts without combining into a single string
    return summary_texts

# Function to preprocess PDFs and extract summary
def extract_summary_from_pdf(pdf_path):
    with tempfile.TemporaryDirectory() as temp_dir:
        output_folder = os.path.join(temp_dir, "output_images")
        os.makedirs(output_folder, exist_ok=True)

        # Open the PDF file
        pdf_document = fitz.open(pdf_path)

        summaries = []

        # Iterate over each page in the PDF
        for i in range(pdf_document.page_count):
            # Get the page
            page = pdf_document.load_page(i)
            # Render the page as an image
            pix = page.get_pixmap()
            # Save the image
            image_path = os.path.join(output_folder, f"page_{i + 1}.png")
            pix.save(image_path)
            # Use PaddleOCR for OCR
            result = ocr_model.ocr(image_path)
            # Extract text from PaddleOCR result
            page_text = ''
            for res in result:
                page_text += res[1][0] + ' '
            # Get summary for the page
            payload = {'inputs': page_text}
            # Get summary for the page
            combined_summary = summary(payload)
            # Append page summary to the list
            summaries.append(combined_summary)

        # Flatten the nested list and convert to a single string
        summary_string = ' '.join([item for sublist in summaries for item in sublist])

        return summary_string

@app.route('/')
def index():
    return render_template('upload.html')

@app.route("/upload", methods=["POST"])
def upload():
    if request.method == 'POST':
        uploaded_file = request.files.get('pdf_file')

        # Check if a file is uploaded
        if uploaded_file and allowed_file(uploaded_file.filename):
            title = secure_filename(uploaded_file.filename)

            # Create a copy of the file for processing
            copy_file_path = os.path.join(tempfile.mkdtemp(), title)
            uploaded_file.seek(0)  # Reset file pointer
            with open(copy_file_path, 'wb') as copy_file:
                shutil.copyfileobj(uploaded_file, copy_file)

            # Extract summary from the copy
            summary_text = extract_summary_from_pdf(copy_file_path)

            flash('Summary extracted successfully!')

            return render_template("upload.html", summary=summary_text)
        else:
            flash('Invalid file format or no file selected')

    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)
