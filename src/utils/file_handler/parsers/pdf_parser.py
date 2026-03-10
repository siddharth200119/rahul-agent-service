import fitz  # PyMuPDF
import io
from io import BytesIO
from .image_parser import image_parser
from RAW.llms import BaseLLM
from typing import Optional, List, Dict, Any
from PIL import Image

async def pdf_parser(
    pdf_data: bytes,
    llm: Optional[BaseLLM] = None,
    markdown: bool = False
) -> List[Dict[str, Any]]:
    """
    Extract text from PDF using PyMuPDF.
    Splits images into three overlapping segments to stay under the 8192 token limit.
    """
    print("Processing PDF with 3-chunk overlapping OCR logic...")

    try:
        if not isinstance(pdf_data, bytes):
            raise TypeError(f"Expected bytes for pdf_data, got {type(pdf_data)}")

        pages: List[Dict[str, Any]] = []
        pdf_stream = BytesIO(pdf_data)

        with fitz.open(stream=pdf_stream, filetype="pdf") as doc:
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                page_text = page.get_text("text")
                image_list = page.get_images(full=True)

                if not page_text and not image_list:
                    continue

                page_content = ""
                if page_text:
                    page_content += page_text.strip() + "\n"

                for img_index, img in enumerate(image_list):
                    try:
                        xref = img[0]
                        base_image = doc.extract_image(xref)
                        image_bytes = base_image.get("image")

                        if not image_bytes:
                            continue

                        # Split into 3 chunks with overlap to ensure no text is cut off
                        image_chunks = split_image_into_safe_chunks(image_bytes, num_chunks=3, overlap=100)
                        
                        for i, chunk in enumerate(image_chunks):
                            print(f"Sending Chunk {i+1}/{len(image_chunks)} of Image {img_index+1} (Page {page_num+1}) to OCR...")
                            ocr_text = await image_parser(chunk, llm, markdown=markdown)
                            if ocr_text:
                                page_content += ocr_text.strip() + "\n"

                    except Exception as img_err:
                        print(f"OCR failed for image {img_index} on page {page_num + 1}: {img_err}")

                if page_content.strip():
                    pages.append({
                        "page": page_num + 1,
                        "text": page_content.strip()
                    })

        return pages

    except Exception as e:
        raise Exception(f"Error processing PDF: {e}")

def split_image_into_safe_chunks(image_bytes: bytes, num_chunks: int = 3, overlap: int = 100) -> List[bytes]:
    """
    Splits an image into overlapping vertical chunks.
    Overlap ensures that text lines cut at the boundary are captured completely in one of the segments.
    """
    try:
        img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        width, height = img.size
        
        if height < 500:
            return [image_bytes]

        chunk_height = height // num_chunks
        chunks = []

        for i in range(num_chunks):
            # Calculate start and end with overlap
            start_y = max(0, i * chunk_height - overlap)
            end_y = min(height, (i + 1) * chunk_height + overlap)
            
            chunk_img = img.crop((0, start_y, width, end_y))
            
            buf = io.BytesIO()
            chunk_img.save(buf, format="JPEG", quality=95)
            chunks.append(buf.getvalue())
        
        return chunks
    except Exception as e:
        print(f"Safe split error: {e}")
        return [image_bytes]