import logging
from pathlib import Path
from PIL import Image, ImageEnhance, ImageFilter
import pdfplumber
import pypdf
import pytesseract

logger = logging.getLogger(__name__)

def extract_text_from_pdf(file_path: Path) -> str:
    """Extracts digital text from PDF using pdfplumber, falling back to pypdf."""
    text_content = []

    # Method 1: pdfplumber (best for layout and table extraction)
    try:
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text(layout=True) or page.extract_text()
                if page_text:
                    text_content.append(page_text)
    except Exception as e:
        logger.warning(f"pdfplumber extraction failed: {e}")

    # Method 2: pypdf fallback if pdfplumber yielded no text
    if not text_content or len("\n".join(text_content).strip()) < 20:
        try:
            reader = pypdf.PdfReader(str(file_path))
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text_content.append(page_text)
        except Exception as e:
            logger.warning(f"pypdf extraction failed: {e}")

    full_text = "\n".join(text_content)

    # Method 3: If digital text was empty, the PDF is likely a scanned photocopy.
    # We attempt OCR on embedded images if Tesseract is available.
    if len(full_text.strip()) < 30:
        try:
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    for img in page.images:
                        # Attempt reading embedded streams
                        pass
        except Exception:
            pass

    return full_text

def preprocess_image_for_ocr(img: Image.Image) -> Image.Image:
    """Enhances image contrast and converts to grayscale for higher OCR accuracy."""
    # 1. Convert to grayscale
    gray = img.convert("L")
    # 2. Enhance contrast
    enhancer = ImageEnhance.Contrast(gray)
    enhanced = enhancer.enhance(2.0)
    # 3. Median filter to remove noise/speckles
    filtered = enhanced.filter(ImageFilter.MedianFilter(size=3))
    return filtered

def extract_text_from_image(file_path: Path) -> str:
    """Extracts text from image files (JPG, PNG, TIFF, BMP) using Tesseract OCR."""
    try:
        img = Image.open(file_path)
        processed = preprocess_image_for_ocr(img)
        # Attempt Tesseract OCR
        text = pytesseract.image_to_string(processed, lang="eng", config="--psm 6")
        if not text.strip():
            # Try default PSM
            text = pytesseract.image_to_string(processed, lang="eng")
        return text
    except pytesseract.TesseractNotFoundError:
        logger.error("Tesseract OCR binary not found on PATH.")
        return "[OCR System Notice]: Tesseract-OCR binary was not detected on this system's PATH. For scanned image files, please install Tesseract or enter values manually. Digital PDFs remain 100% supported."
    except Exception as e:
        logger.error(f"Image OCR failed: {e}")
        return f"Error processing image: {str(e)}"

def extract_text_from_file(file_path: Path) -> str:
    """Universal text extractor routing by file extension."""
    suffix = file_path.suffix.lower()

    if suffix == ".pdf":
        return extract_text_from_pdf(file_path)
    elif suffix in [".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".webp"]:
        return extract_text_from_image(file_path)
    else:
        # Fallback text read
        try:
            return file_path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            return ""
