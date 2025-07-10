# PDF Invoice Data Extractor

A Python project to extract important data from PDF invoices and convert it to JSON format. This project supports three extraction methods:

1. **Manual Regex-Based Extraction**: Extracts data using predefined regex patterns.
2. **AI-Powered Extraction**: Utilizes Gemini 2.5 Flash Lite for intelligent parsing.
3. **Third-Party API Extraction**: Integrates with Reducto API for invoice processing.

## Features

- Extracts key invoice information including:
  - Invoice number
  - Invoice date and due date
  - Total amount, subtotal, and tax
  - Vendor and customer information
  - Line items from tables
  - Contact information (email, phone, address)
- Supports various invoice formats and layouts
- Outputs structured JSON data
- Command-line interface for easy automation
- Programmatic API for integration

## Installation

1. Make sure you have Python 3.7+ installed.
2. Install the required packages:

```bash
pip install -r requirements.txt
```

## Usage

### Command Line Usage

#### Manual Extraction

```bash
# Basic usage - extract data and print to console
python main.py path/to/invoice.pdf

# Extract data and save to JSON file
python main.py path/to/invoice.pdf -o output.json

# Pretty print JSON output
python main.py path/to/invoice.pdf --pretty

# Enable debug output to see extraction process
python main.py path/to/invoice.pdf --debug --pretty
```

#### AI-Powered Extraction

```bash
python gemini_script.py path/to/invoice.pdf
```

#### Third-Party API Extraction

```bash
python reducto_script.py
```

### Programmatic Usage

#### Manual Extraction

```python
from manual import InvoiceExtractor
import json

# Initialize the extractor
extractor = InvoiceExtractor()

# Extract data from PDF
invoice_data = extractor.extract_invoice_data("path/to/invoice.pdf")

# Print results
print(json.dumps(invoice_data, indent=2))
```

#### AI-Powered Extraction

```python
from gemini_script import parse_invoice

# Parse invoice using Gemini AI
parsed_data = parse_invoice("path/to/invoice.pdf")
print(parsed_data)
```

#### Third-Party API Extraction

```python
from reducto_script import Reducto
from pathlib import Path

client = Reducto()
upload = client.upload(file=Path("path/to/invoice.pdf"))
result = client.parse.run(document_url=upload)
print(result)
```

## Output Format

The script outputs JSON data with the following structure:

```json
{
  "invoice_number": "INV-001",
  "date": "2024-01-15",
  "due_date": "2024-02-15",
  "total": 1500.00,
  "subtotal": 1350.00,
  "tax": 150.00,
  "vendor_name": "ABC Company",
  "customer_name": "XYZ Corp",
  "vendor_info": {
    "email": "billing@abc.com",
    "phone": "(555) 123-4567",
    "address": "123 Main St"
  },
  "line_items": [
    {
      "description": "Product A",
      "quantity": 2,
      "unit_price": 500.00,
      "total_amount": 1000.00
    }
  ],
  "extraction_date": "2024-01-20T10:30:00",
  "source_file": "path/to/invoice.pdf"
}
```

## Supported Data Fields

- **invoice_number**: Invoice or document number
- **date**: Invoice date
- **due_date**: Payment due date
- **total**: Total amount due
- **subtotal**: Subtotal before tax
- **tax**: Tax amount
- **vendor_name**: Vendor/supplier name
- **customer_name**: Customer/client name
- **vendor_info**: Contact information (email, phone, address)
- **line_items**: Itemized list of products/services
- **raw_tables**: Raw table data extracted from PDF
- **extraction_date**: When the data was extracted
- **source_file**: Source PDF file path

## Troubleshooting

### Common Issues and Solutions

**No text extracted**: The PDF might be image-based. You'll need OCR tools like `pytesseract`.

**Invoice number not found**: Check if your invoice number format matches the patterns. You can add custom patterns to the `patterns` dictionary.

**Amounts not detected**: Currency symbols or formatting might be different. The script looks for common patterns like `$123.45`, `123.45$`, etc.

**Tables not extracted**: Complex table layouts might not be detected. Check the `raw_tables` output to see what was found.

### Debugging

Use debug mode to analyze extraction:

```bash
python main.py your_invoice.pdf --debug --pretty
```

## Dependencies

- `pdfplumber`: PDF text and table extraction
- `pandas`: Data manipulation and table handling
- `python-dateutil`: Date parsing
- `regex`: Advanced regex support
- `python-dotenv`: Environment variable management

## License

MIT License

## Contributing

Feel free to submit issues and enhancement requests!
