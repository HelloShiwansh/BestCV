import io
import logging
import os
from pathlib import Path

# The Windows setup script installs the official portable native runtime here.
if os.name == 'nt' and not os.environ.get('WEASYPRINT_DLL_DIRECTORIES'):
    native_dir = Path(__file__).resolve().parents[2] / '.runtime' / 'weasyprint' / '_internal'
    if native_dir.is_dir():
        os.environ['WEASYPRINT_DLL_DIRECTORIES'] = str(native_dir)

try:
    from weasyprint import HTML, CSS
    WEASYPRINT_INSTALLED = True
except (ImportError, OSError):
    WEASYPRINT_INSTALLED = False

logger = logging.getLogger('ats_resume_scorer')

def generate_combined_pdf(html_docs: dict[str, str]) -> bytes:
    if not WEASYPRINT_INSTALLED:
        raise ImportError("PDF libraries are unavailable. On Windows, run scripts/setup-pdf-runtime.ps1 and restart the backend.")
        
    documents = []
    
    # Render all 3 HTML strings to WeasyPrint Document objects
    for name, html_str in html_docs.items():
        doc = HTML(string=html_str).render()
        documents.append(doc)
    
    # Merge them into the first document
    first_doc = documents[0]
    for other_doc in documents[1:]:
        for page in other_doc.pages:
            first_doc.pages.append(page)
            
    # Write combined PDF bytes
    pdf_bytes = first_doc.write_pdf()
    return pdf_bytes
