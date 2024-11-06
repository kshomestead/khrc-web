import qrcode
from fpdf import FPDF
from PIL import Image
import cv2
import pyzbar.pyzbar as pyzbar
import logging

# Set up logging configuration
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Part 1: Generate QR Codes
def generate_qr_code(data, filename, box_size):
    """Generates a QR code with the specified data and box size, then saves it as an image."""
    logging.info(f"Generating QR code for data: {data}")
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=box_size,
        border=2,
    )
    qr.add_data(data)
    qr.make(fit=True)

    # Create and save the image
    img = qr.make_image(fill='black', back_color='white')
    img.save(filename)
    logging.info(f"QR code saved as {filename}")

def generate_all_qr_codes():
    """Generates all necessary QR codes (main form and subsections) and returns filenames."""
    logging.info("Starting QR code generation for all sections.")

    # Generate the main QR code
    main_qr_filename = "main_qr_code.png"
    generate_qr_code("Operating Loan Application", main_qr_filename, box_size=10)

    # Generate smaller QR codes for each subsection
    subsection_filenames = []
    for subsection in ["1", "2", "3"]:
        filename = f"subsection_qr_{subsection}.png"
        generate_qr_code(f"Section {subsection}", filename, box_size=3)
        subsection_filenames.append(filename)
    
    logging.info("All QR codes generated successfully.")
    return main_qr_filename, subsection_filenames

# Part 2: Create PDF with QR Codes
def create_pdf_with_qr_codes(main_qr_filename, subsection_filenames, output_pdf_filename):
    """Creates a PDF document with the main QR code and subsection QR codes arranged on the page."""
    logging.info(f"Creating PDF with main QR code and subsection QR codes at {output_pdf_filename}")

    pdf = FPDF()
    pdf.add_page()

    # Add title
    pdf.set_font("Arial", "B", 16)
    pdf.cell(200, 10, "Operating Loan Application", 0, 1, "C")

    # Add the main QR code in the top-left corner
    pdf.image(main_qr_filename, x=10, y=20, w=30, h=30)

    # Add subsection QR codes at specific positions on the page
    subsection_positions = [(10, 70), (10, 100), (10, 130)]
    for i, filename in enumerate(subsection_filenames):
        x, y = subsection_positions[i]
        pdf.image(filename, x=x, y=y, w=15, h=15)  # Smaller size for subsection QR codes
        pdf.set_xy(x + 20, y + 5)  # Position text to the right of each QR code
        pdf.set_font("Arial", "B", 12)
        pdf.cell(40, 10, f"Subsection {i + 1}")

    # Save the PDF
    pdf.output(output_pdf_filename)
    logging.info(f"PDF created and saved as {output_pdf_filename}")

# Part 3: Read and Verify QR Codes in PDF
def read_qr_code_from_image(image_path):
    """Reads and decodes QR codes from an image and returns a list of decoded data."""
    logging.info(f"Reading QR code from image: {image_path}")

    # Read the image
    image = cv2.imread(image_path)
    decoded_data_list = []

    # Detect and decode QR codes
    decoded_objects = pyzbar.decode(image)
    for obj in decoded_objects:
        decoded_data = obj.data.decode("utf-8")
        decoded_data_list.append(decoded_data)
        logging.info(f"Decoded QR code data: {decoded_data}")
    
    return decoded_data_list

def verify_qr_codes(image_paths, expected_data):
    """Verifies each QR code's data in a list of images matches the expected data."""
    logging.info("Starting verification of QR codes.")
    
    for image_path, expected in zip(image_paths, expected_data):
        decoded_data_list = read_qr_code_from_image(image_path)
        
        # Verify each QR code content matches expected data
        if expected in decoded_data_list:
            logging.info(f"QR code in {image_path} matches expected data: {expected}")
        else:
            logging.warning(f"Mismatch in {image_path}. Expected: {expected}, Got: {decoded_data_list}")

# Full Workflow
def main():
    logging.info("Starting full workflow for QR code generation, PDF creation, and verification.")
    
    # Step 1: Generate QR codes
    main_qr_filename, subsection_filenames = generate_all_qr_codes()

    # Step 2: Create a PDF with the generated QR codes
    pdf_filename = "test_qr_application_form.pdf"
    create_pdf_with_qr_codes(main_qr_filename, subsection_filenames, pdf_filename)

    # Step 3: Verify the QR codes
    # Convert PDF to images for verification if necessary
    image_paths = [main_qr_filename] + subsection_filenames
    expected_data = ["Operating Loan Application", "Section 1", "Section 2", "Section 3"]
    
    verify_qr_codes(image_paths, expected_data)
    logging.info("Workflow completed successfully.")

if __name__ == "__main__":
    main()