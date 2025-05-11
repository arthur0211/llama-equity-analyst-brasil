import os
import sys # Import sys for environment diagnostics
from dotenv import load_dotenv

# Attempt to import the specialized PDFReader
try:
    from llama_index.readers.file import PDFReader
    print("Successfully imported PDFReader from llama_index.readers.file")
    SPECIALIZED_PDF_READER_AVAILABLE = True
except ImportError:
    print("Failed to import PDFReader from llama_index.readers.file. Falling back to SimpleDirectoryReader.")
    from llama_index.core import SimpleDirectoryReader
    SPECIALIZED_PDF_READER_AVAILABLE = False
except Exception as e:
    print(f"An unexpected error occurred during PDFReader import: {e}")
    from llama_index.core import SimpleDirectoryReader # Fallback
    SPECIALIZED_PDF_READER_AVAILABLE = False

# --- Environment Diagnostics ---
print(f"Python Executable: {sys.executable}")
print("Python Path (sys.path):")
for p in sys.path:
    print(f"  - {p}")
print("--- End of Environment Diagnostics ---")
# --- Environment Diagnostics End ---

# Load environment variables (though not strictly needed for this script, good practice)
load_dotenv()

# Define the path to the PDF file and directory
TAESA_REPORTS_DIR = os.path.join("data", "release-taee")
TAESA_REPORT_FILENAME = "TAESA-Release-1T25.pdf"
TAESA_REPORT_FULL_PATH = os.path.join(TAESA_REPORTS_DIR, TAESA_REPORT_FILENAME)

def load_and_inspect_pdf_custom(file_path: str):
    """
    Loads and inspects a PDF, trying the specialized PDFReader first.
    """
    print(f"Attempting to load PDF: {file_path}")
    if not os.path.exists(file_path):
        print(f"Error: File not found at {file_path}")
        return None

    documents = None
    try:
        if SPECIALIZED_PDF_READER_AVAILABLE and PDFReader:
            print(f"Using specialized PDFReader for {file_path}")
            reader_instance = PDFReader() # Instantiate the specialized reader
            documents = reader_instance.load_data(file=file_path) # Pass the file path string
        else:
            print(f"Using SimpleDirectoryReader for {file_path}")
            # SimpleDirectoryReader expects a list of input_files or an input_dir
            reader_instance = SimpleDirectoryReader(input_files=[file_path])
            documents = reader_instance.load_data()
        
        print(f"Successfully loaded {len(documents)} document(s).")

        if not documents:
            print("No documents were loaded.")
            return None

        for i, doc in enumerate(documents):
            print(f"--- Document {i+1} ---")
            print(f"Metadata: {doc.metadata}")
            text_snippet = doc.text[:1000] if doc.text else "No text content"
            print(f"Text length: {len(doc.text) if doc.text else 0}")
            print(f"Text snippet (first 1000 chars):\n'{text_snippet}'")
            print("--- End of Document {i+1} ---")
        return documents
    except Exception as e:
        print(f"An error occurred during PDF loading or inspection: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    print("--- Starting PDF Loader Script ---")
    if os.path.exists(TAESA_REPORT_FULL_PATH):
        print(f"Found target file: {TAESA_REPORT_FULL_PATH}")
        taesa_documents = load_and_inspect_pdf_custom(TAESA_REPORT_FULL_PATH)
        if taesa_documents:
            print(f"Script finished. Processed {len(taesa_documents)} main document(s).")
        else:
            print("Script finished. No documents were successfully processed.")
    else:
        print(f"Critical Error: Target PDF file not found at {TAESA_REPORT_FULL_PATH}")
    print("--- PDF Loader Script Ended ---") 