import os
import sys
import glob
from markitdown import MarkItDown

def convert_pdfs_to_markdown(source_dir, output_dir=None):
    """
    Finds all PDF files in source_dir and converts them to Markdown using MarkItDown.
    """
    if not os.path.isdir(source_dir):
        print(f"Error: {source_dir} is not a directory.")
        return

    # If output_dir is not provided, create an 'output' folder in the current directory (project-relative)
    if output_dir is None:
        output_dir = os.path.join(os.path.dirname(__file__), "output")
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Created output directory: {output_dir}")

    # Initialize MarkItDown
    md_converter = MarkItDown()

    # Find all PDFs recursively (optional) or just in the top level
    pdf_files = glob.glob(os.path.join(source_dir, "*.pdf"))
    
    if not pdf_files:
        print(f"No PDF files found in {source_dir}")
        return

    print(f"Found {len(pdf_files)} PDF files. Starting conversion...")

    for pdf_path in pdf_files:
        base_name = os.path.basename(pdf_path)
        md_name = os.path.splitext(base_name)[0] + ".md"
        output_path = os.path.join(output_dir, md_name)

        print(f"Converting: {base_name} ...", end=" ", flush=True)
        try:
            # Convert PDF to Markdown result
            result = md_converter.convert(pdf_path)
            
            # Save the text_content (Markdown strings)
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(result.text_content)
            
            print(f"Done -> {output_path}")
        except Exception as e:
            print(f"Failed! Error: {e}")

if __name__ == "__main__":
    # If no argument, use the path provided in user request
    target_path = sys.argv[1] if len(sys.argv) > 1 else "/Users/alharkan/Documents/Drive/Study/Seminar Proposal Disertasi"
    
    # Custom output path if provided
    custom_output = sys.argv[2] if len(sys.argv) > 2 else None
    
    convert_pdfs_to_markdown(target_path, custom_output)
