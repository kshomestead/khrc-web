import boto3
import cv2
import pyzbar.pyzbar as pyzbar
import time
import csv

# Initialize AWS Textract client
textract = boto3.client('textract')

# Define predefined field keys for each section
form_template = {
    "Personal Details": {
        "First Name:": None,
        "Last Name:": None,
        "Date of Birth:": None,
        "Social Security Number:": None,
    },
    "Employment History": {
        "Employer Name:": None,
        "Job Title:": None,
        "Start Date:": None,
        "End Date:": None,
    },
    "Loan Details": {
        "Loan Amount:": None,
        "Interest Rate:": None,
        "Repayment Term:": None,
        "Monthly Payment:": None,
    }
}

# Function to start Textract Form and Table Analysis
def start_analysis_job(bucket, document):
    response = textract.start_document_analysis(
        DocumentLocation={'S3Object': {'Bucket': bucket, 'Name': document}},
        FeatureTypes=['FORMS', 'TABLES']
    )
    job_id = response['JobId']
    print(f"Textract job started with Job ID: {job_id}")
    return job_id

# Check job status and retrieve results
def check_job_status(job_id):
    status = "IN_PROGRESS"
    while status == "IN_PROGRESS":
        response = textract.get_document_analysis(JobId=job_id)
        status = response['JobStatus']
        print(f"Current Job Status: {status}")
        time.sleep(10)
    return response if status == "SUCCEEDED" else None

# Parse Textract response and populate the template
def populate_template(response, template, section_name):
    for block in response['Blocks']:
        if block['BlockType'] == 'KEY_VALUE_SET':
            key_text = ""
            value_text = ""

            # Identify key text
            if 'EntityTypes' in block and "KEY" in block['EntityTypes']:
                key_text = block['Text'] if 'Text' in block else ""

            # Identify value text
            if block.get('Relationships'):
                for relationship in block['Relationships']:
                    if relationship['Type'] == "VALUE":
                        for value_id in relationship['Ids']:
                            value_block = next((b for b in response['Blocks'] if b['Id'] == value_id), None)
                            if value_block and 'Text' in value_block:
                                value_text = value_block['Text']
                                break

            # Populate template if key matches predefined fields in the section
            if key_text in template.get(section_name, {}):
                template[section_name][key_text] = value_text

    return template

# Detect and Decode QR Codes in Document Images
def decode_qr_code(image_path):
    image = cv2.imread(image_path)
    decoded_objects = pyzbar.decode(image)
    qr_data = {}
    for obj in decoded_objects:
        if obj.type == "QRCODE":
            section_name = obj.data.decode("utf-8")
            qr_data[section_name] = obj.rect
    return qr_data

# Save data to CSV, alphabetized by key name
def save_to_csv(template, filename="extracted_data_sorted.csv"):
    # Flatten the template dictionary for easier CSV writing
    flat_data = []
    for section, fields in template.items():
        for key, value in fields.items():
            flat_data.append({"Section": section, "Key": key, "Value": value})

    # Sort data alphabetically by key name
    flat_data_sorted = sorted(flat_data, key=lambda x: x["Key"])

    # Write to CSV
    with open(filename, mode="w", newline="") as csvfile:
        fieldnames = ["Section", "Key", "Value"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        writer.writerows(flat_data_sorted)
        
    print(f"Data successfully saved to {filename}")

# Main function to run the extraction
def main():
    # Define S3 bucket and document
    bucket = 'your-s3-bucket'
    document = 'your-multi-page-document.pdf'

    # Step 1: Detect QR codes to identify sections
    # Replace 'image_path' with actual path to each document page as an image
    qr_sections = decode_qr_code("path_to_each_page_image.jpg")
    print("QR Codes Detected for Sections:", qr_sections)

    # Step 2: Start the Textract job to extract key-value pairs and tables
    job_id = start_analysis_job(bucket, document)
    response = check_job_status(job_id)

    # Step 3: Populate the template with extracted data based on identified sections
    if response:
        for section_name in qr_sections:
            print(f"Processing section: {section_name}")
            populated_template = populate_template(response, form_template, section_name)
        
        # Save the populated template to a CSV file, sorted alphabetically by key name
        save_to_csv(populated_template, filename="extracted_data_sorted.csv")
    else:
        print("Textract job failed or did not return data.")

# Run the main function
if __name__ == "__main__":
    main()