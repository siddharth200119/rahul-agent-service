import tempfile
import textract
from docx import Document

def doc_parser(file_data: bytes) -> str:
    """Extract text from .doc or .docx or .odt files."""
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".bin") as tmp:
            tmp.write(file_data)
            tmp.flush()
            try:
                # Try using python-docx (for docx)
                doc = Document(tmp.name)
                return "\n".join([para.text for para in doc.paragraphs])
            except Exception:
                # Fallback to textract (for doc or odt)
                text = textract.process(tmp.name)
                return text.decode("utf-8", errors="replace")
    except Exception as e:
        raise Exception(f"Error processing DOC/DOCX/ODT file: {e}")
