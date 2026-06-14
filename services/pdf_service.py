import fitz  # PyMuPDF
import re

class PDFService:
    @staticmethod
    def extract_text_from_pdf(file_path):
        """
        Extracts raw text from a PDF file using PyMuPDF.
        """
        try:
            doc = fitz.open(file_path)
            full_text = []
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                full_text.append(page.get_text())
            doc.close()
            return "\n".join(full_text)
        except Exception as e:
            raise Exception(f"Failed to extract text from PDF: {str(e)}")

    @staticmethod
    def extract_text_from_pptx(file_path):
        """
        Extracts raw text from a PowerPoint PPTX file.
        """
        try:
            from pptx import Presentation
            prs = Presentation(file_path)
            full_text = []
            for slide_num, slide in enumerate(prs.slides):
                slide_text = []
                for shape in slide.shapes:
                    if hasattr(shape, "text") and shape.text.strip():
                        slide_text.append(shape.text.strip())
                if slide_text:
                    full_text.append(f"[Slide {slide_num + 1}]\n" + "\n".join(slide_text))
            return "\n\n".join(full_text)
        except Exception as e:
            raise Exception(f"Failed to extract text from PowerPoint: {str(e)}")

    @staticmethod
    def extract_text(file_path):
        """
        Extracts raw text from a document based on file extension.
        """
        if file_path.lower().endswith('.pptx'):
            return PDFService.extract_text_from_pptx(file_path)
        else:
            return PDFService.extract_text_from_pdf(file_path)

    @staticmethod
    def get_page_count(file_path):
        """
        Extracts page or slide count from PDF or PPTX.
        """
        try:
            if file_path.lower().endswith('.pptx'):
                from pptx import Presentation
                prs = Presentation(file_path)
                return len(prs.slides)
            else:
                doc = fitz.open(file_path)
                count = len(doc)
                doc.close()
                return count
        except Exception as e:
            print(f"Error getting page/slide count for {file_path}: {e}")
            return 0

    @staticmethod
    def clean_text(text):
        """
        Cleans extracted text by normalizing whitespace, removing typical PDF hyphenation
        artifacts, and cleaning up formatting.
        """
        if not text:
            return ""
        
        # Standardize newlines
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        
        # Remove line-break hyphens (e.g. "de- \n velopment" -> "development")
        text = re.sub(r'(\w+)-\s*\n\s*(\w+)', r'\1\2', text)
        
        # Replace multiple spaces with a single space
        text = re.sub(r'[ \t]+', ' ', text)
        
        # Standardize multiple newlines
        text = re.sub(r'\n+', '\n', text)
        
        return text.strip()

    @staticmethod
    def split_into_chunks(text, chunk_size=1000, chunk_overlap=200):
        """
        Splits clean text into overlapping chunks for vector search and AI processing.
        """
        if not text:
            return []
            
        chunks = []
        start = 0
        text_len = len(text)
        
        while start < text_len:
            end = min(start + chunk_size, text_len)
            
            # Adjust end to not cut in the middle of a word if possible
            if end < text_len:
                # Find the last space or newline in the end region to break cleanly
                last_space = text.rfind(' ', start, end)
                if last_space != -1 and last_space > start + (chunk_size // 2):
                    end = last_space
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
                
            start = end - chunk_overlap
            if start >= text_len - chunk_overlap:
                break
                
        return chunks
