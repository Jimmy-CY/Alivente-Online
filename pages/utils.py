from pypdf import PdfReader, PdfWriter
from django.core.files.base import ContentFile
import io
import os


def is_pdf(file):
    """
    Check if a file is a PDF
    
    Args:
        file: Django FileField or UploadedFile object
    
    Returns:
        Boolean indicating if file is PDF
    """
    if hasattr(file, 'name'):
        file_extension = os.path.splitext(file.name)[1].lower()
        return file_extension == '.pdf'
    return False


def merge_pdfs(existing_file, new_file):
    """
    Merge two PDF files and return a ContentFile object
    
    Args:
        existing_file: Django FileField object (existing document)
        new_file: Django UploadedFile object (new document)
    
    Returns:
        ContentFile object containing the merged PDF
    
    Raises:
        ValueError: If either file is not a PDF
    """
    # Validate both files are PDFs
    if not is_pdf(existing_file):
        raise ValueError("Existing document is not a PDF file")
    
    if not is_pdf(new_file):
        raise ValueError("New document is not a PDF file")
    
    # Create a PDF writer object
    pdf_writer = PdfWriter()
    
    # Read the existing PDF
    existing_pdf = PdfReader(existing_file)
    for page in existing_pdf.pages:
        pdf_writer.add_page(page)
    
    # Read the new PDF
    new_pdf = PdfReader(new_file)
    for page in new_pdf.pages:
        pdf_writer.add_page(page)
    
    # Write to a BytesIO object
    output = io.BytesIO()
    pdf_writer.write(output)
    output.seek(0)
    
    # Return as ContentFile
    return ContentFile(output.read())