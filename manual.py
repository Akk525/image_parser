import json
import re
import pdfplumber
import pandas as pd
from datetime import datetime
from dateutil import parser as date_parser
import argparse
import sys
from pathlib import Path

class InvoiceExtractor:
    def __init__(self, debug=False):
        self.debug = debug
        # Enhanced patterns for invoice data extraction
        self.patterns = {
            'invoice_number': [
                r'invoice\s*number\s*:?\s*([A-Fa-f0-9]{8}[0-9]{4})',  # "Invoice number 4E62BC7A0001"
                r'invoice\s*number\s*:?\s*([A-Za-z0-9\-_]+)',
                r'invoice\s*#?\s*:?\s*([A-Za-z0-9\-_]+)',
                r'inv\s*#?\s*:?\s*([A-Za-z0-9\-_]+)',
                r'#\s*([A-Za-z0-9\-_]+)',
                r'doc\s*#?\s*:?\s*([A-Za-z0-9\-_]+)',
                r'reference\s*#?\s*:?\s*([A-Za-z0-9\-_]+)',
                r'([A-Fa-f0-9]{8}[0-9]{4})',  # Pattern like 4E62BC7A0001 (no dashes)
                r'([A-Za-z0-9]{4}-[A-Za-z0-9]{8}-[A-Za-z0-9]{4})',  # Pattern like 4E62BC7A-0001
            ],
            'date': [
                r'date\s*of\s*issue\s*:?\s*([A-Za-z]{3,9}\s+[0-9]{1,2},?\s+[0-9]{4})',
                r'invoice\s*date\s*:?\s*([A-Za-z]{3,9}\s+[0-9]{1,2},?\s+[0-9]{4})',
                r'date\s*:?\s*([0-9]{1,2}[\/\-\.][0-9]{1,2}[\/\-\.][0-9]{2,4})',
                r'([A-Za-z]{3,9}\s+[0-9]{1,2},?\s+[0-9]{4})',
                r'([0-9]{4}-[0-9]{2}-[0-9]{2})',  # ISO format
                r'([0-9]{2}\/[0-9]{2}\/[0-9]{4})',  # MM/DD/YYYY format
                r'([0-9]{1,2}[\/\-\.][0-9]{1,2}[\/\-\.][0-9]{2,4})',
            ],
            'due_date': [
                r'date\s*due\s*:?\s*([A-Za-z]{3,9}\s+[0-9]{1,2},?\s+[0-9]{4})',
                r'due\s*date\s*:?\s*([A-Za-z]{3,9}\s+[0-9]{1,2},?\s+[0-9]{4})',
                r'due\s*:?\s*([A-Za-z]{3,9}\s+[0-9]{1,2},?\s+[0-9]{4})',
                r'due\s*date\s*:?\s*([0-9]{1,2}[\/\-\.][0-9]{1,2}[\/\-\.][0-9]{2,4})',
                r'payment\s*due\s*:?\s*([0-9]{1,2}[\/\-\.][0-9]{1,2}[\/\-\.][0-9]{2,4})',
                r'due\s*:?\s*([0-9]{1,2}[\/\-\.][0-9]{1,2}[\/\-\.][0-9]{2,4})',
            ],
            'total': [
                r'total\s*:?\s*us\$\s*([0-9,]+\.?[0-9]*)',
                r'total\s*:?\s*\$\s*([0-9,]+\.?[0-9]*)',
                r'total\s*:?\s*([0-9,]+\.?[0-9]*)',
                r'amount\s*due\s*:?\s*us\$\s*([0-9,]+\.?[0-9]*)',
                r'amount\s*due\s*:?\s*\$\s*([0-9,]+\.?[0-9]*)',
                r'balance\s*due\s*:?\s*\$?\s*([0-9,]+\.?[0-9]*)',
                r'grand\s*total\s*:?\s*\$?\s*([0-9,]+\.?[0-9]*)',
                r'total\s*amount\s*:?\s*\$?\s*([0-9,]+\.?[0-9]*)',
                r'net\s*amount\s*:?\s*\$?\s*([0-9,]+\.?[0-9]*)',
            ],
            'subtotal': [
                r'subtotal\s*:?\s*us\$\s*([0-9,]+\.?[0-9]*)',
                r'subtotal\s*:?\s*\$\s*([0-9,]+\.?[0-9]*)',
                r'sub\s*total\s*:?\s*us\$\s*([0-9,]+\.?[0-9]*)',
                r'sub\s*total\s*:?\s*\$\s*([0-9,]+\.?[0-9]*)',
                r'sub-total\s*:?\s*\$?\s*([0-9,]+\.?[0-9]*)',
            ],
            'tax': [
                r'tax\s*:?\s*us\$\s*([0-9,]+\.?[0-9]*)',
                r'tax\s*:?\s*\$\s*([0-9,]+\.?[0-9]*)',
                r'sales\s*tax\s*:?\s*\$?\s*([0-9,]+\.?[0-9]*)',
                r'vat\s*:?\s*\$?\s*([0-9,]+\.?[0-9]*)',
                r'gst\s*:?\s*\$?\s*([0-9,]+\.?[0-9]*)',
                r'hst\s*:?\s*\$?\s*([0-9,]+\.?[0-9]*)',
            ],
            'vendor_name': [
                # This won't work well with regex, better to use alternative method
            ],
            'customer_name': [
                # This won't work well with regex, better to use alternative method
            ],
        }
    
    def log_debug(self, message):
        """Debug logging"""
        if self.debug:
            print(f"[DEBUG] {message}")
    
    def extract_text_from_pdf(self, pdf_path):
        """Extract text from PDF using pdfplumber"""
        text = ""
        try:
            with pdfplumber.open(pdf_path) as pdf:
                self.log_debug(f"PDF has {len(pdf.pages)} pages")
                for page_num, page in enumerate(pdf.pages):
                    page_text = page.extract_text()
                    if page_text:
                        self.log_debug(f"Page {page_num + 1} extracted {len(page_text)} characters")
                        text += page_text + "\n"
                    else:
                        self.log_debug(f"Page {page_num + 1} has no extractable text")
        except Exception as e:
            print(f"Error extracting text from PDF: {e}")
        
        self.log_debug(f"Total extracted text length: {len(text)}")
        if self.debug and text:
            print("\n--- EXTRACTED TEXT ---")
            print(text[:1000] + "..." if len(text) > 1000 else text)
            print("--- END EXTRACTED TEXT ---\n")
        
        return text
    
    def extract_tables_from_pdf(self, pdf_path):
        """Extract tables from PDF using pdfplumber"""
        tables = []
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages):
                    page_tables = page.extract_tables()
                    for table_num, table in enumerate(page_tables):
                        if table:
                            df = pd.DataFrame(table[1:], columns=table[0])
                            tables.append({
                                'page': page_num + 1,
                                'table_number': table_num + 1,
                                'data': df.to_dict('records')
                            })
        except Exception as e:
            print(f"Error extracting tables from PDF: {e}")
        return tables
    
    def extract_using_patterns(self, text, field):
        """Extract data using regex patterns with enhanced debugging"""
        if field not in self.patterns:
            self.log_debug(f"No patterns defined for field: {field}")
            return None
        
        text_lower = text.lower()
        self.log_debug(f"Trying to extract '{field}' using {len(self.patterns[field])} patterns")
        
        for i, pattern in enumerate(self.patterns[field]):
            try:
                match = re.search(pattern, text_lower, re.IGNORECASE | re.MULTILINE)
                if match:
                    result = match.group(1).strip()
                    self.log_debug(f"Pattern {i+1} for '{field}' matched: '{result}' using pattern: {pattern}")
                    return result
                else:
                    self.log_debug(f"Pattern {i+1} for '{field}' no match: {pattern}")
            except Exception as e:
                self.log_debug(f"Error with pattern {i+1} for '{field}': {e}")
        
        # Try alternative extraction methods for specific fields
        if field == 'invoice_number':
            return self._extract_invoice_number_alternative(text)
        elif field == 'total':
            return self._extract_total_alternative(text)
        elif field == 'vendor_name':
            return self._extract_vendor_name_alternative(text)
        elif field == 'customer_name':
            return self._extract_customer_name_alternative(text)
        
        self.log_debug(f"No matches found for field: {field}")
        return None
    
    def _extract_invoice_number_alternative(self, text):
        """Alternative method to extract invoice number"""
        # Look for patterns like "Invoice-4E62BC7A-0001" in the filename or text
        patterns = [
            r'invoice\s*number\s*([A-Fa-f0-9]{8}[0-9]{4})',  # "Invoice number 4E62BC7A0001"
            r'([A-Fa-f0-9]{8}[0-9]{4})',  # 4E62BC7A0001 format (no dashes)
            r'([A-Za-z0-9]+-[A-Fa-f0-9]{8}-[0-9]{4})',  # Invoice-4E62BC7A-0001 format
            r'([A-Fa-f0-9]{8}-[0-9]{4})',  # 4E62BC7A-0001 format
            r'(INV[A-Za-z0-9\-_]+)',
            r'([0-9]{4,})',  # Fallback to any 4+ digit number
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                self.log_debug(f"Alternative invoice number extraction found: {match.group(1)}")
                return match.group(1)
        return None
    
    def _extract_vendor_name_alternative(self, text):
        """Alternative method to extract vendor name from document structure"""
        lines = text.split('\n')
        
        # For Khan Academy format, look for the line that contains "Khan Academy"
        # and appears before "Bill to"
        for i, line in enumerate(lines):
            line = line.strip()
            # Look for the vendor name - it should be a standalone line before "Bill to"
            if line and 'khan academy' in line.lower() and 'bill to' in line.lower():
                # Extract just "Khan Academy" part from "Khan Academy Bill to"
                vendor_match = re.search(r'^(.*?)\s+bill\s+to', line, re.IGNORECASE)
                if vendor_match:
                    vendor_name = vendor_match.group(1).strip()
                    self.log_debug(f"Alternative vendor name extraction found: {vendor_name}")
                    return vendor_name
            elif line and re.match(r'^[A-Za-z\s]+$', line) and 'khan' in line.lower():
                # If we find a line that just says "Khan Academy"
                self.log_debug(f"Alternative vendor name extraction found: {line}")
                return line
        
        # Fallback: look for any line containing "Khan Academy"
        for line in lines:
            if 'khan academy' in line.lower():
                # Try to extract just the company name
                match = re.search(r'(khan academy)', line, re.IGNORECASE)
                if match:
                    self.log_debug(f"Alternative vendor name extraction (fallback) found: {match.group(1)}")
                    return match.group(1).title()
        
        return None
    
    def _extract_customer_name_alternative(self, text):
        """Alternative method to extract customer name"""
        lines = text.split('\n')
        
        # For Khan Academy format: "Khan Academy Bill to" followed by customer info
        # Text structure:
        # Khan Academy Bill to
        # PO Box 1630 Aditya Kuniyil Kattil
        # Mountain View, California 94042 1101 3rd Street
        
        bill_to_found = False
        for i, line in enumerate(lines):
            line = line.strip()
            
            # Look for "Bill to" line
            if 'bill to' in line.lower():
                bill_to_found = True
                continue
            
            # If we found "Bill to", look in subsequent lines for the customer name
            if bill_to_found and line:
                # Skip lines that are clearly addresses or contact info
                if any(keyword in line.lower() for keyword in [
                    'po box', 'mountain view', 'california', 'united states', 
                    '@', '.com', '.org', 'honors college', 'west lafayette', 'indiana'
                ]):
                    continue
                
                # Look for a line that appears to be a person's name
                # Should contain letters, spaces, and possibly common name patterns
                if re.match(r'^[A-Za-z\s]+$', line) and len(line.split()) >= 2:
                    self.log_debug(f"Alternative customer name extraction found: {line}")
                    return line
        
        # Alternative approach: look for pattern in the specific Khan Academy format
        # where customer name appears after "PO Box 1630"
        text_lower = text.lower()
        po_box_pattern = r'po\s+box\s+\d+\s+([A-Za-z\s]+?)(?:\s+\d+\s+[A-Za-z\s]+|$)'
        match = re.search(po_box_pattern, text_lower, re.MULTILINE)
        if match:
            customer_name = match.group(1).strip()
            # Convert back to proper case
            customer_name_proper = ' '.join(word.capitalize() for word in customer_name.split())
            self.log_debug(f"Alternative customer name extraction (PO Box pattern) found: {customer_name_proper}")
            return customer_name_proper
        
        return None
    
    def _extract_total_alternative(self, text):
        """Alternative method to extract total amount"""
        # Look for currency amounts in various formats
        patterns = [
            r'\$\s*([0-9,]+\.?[0-9]*)',  # $123.45
            r'([0-9,]+\.?[0-9]*)\s*\$',  # 123.45$
            r'([0-9,]+\.[0-9]{2})',      # 123.45 (decimal format)
        ]
        
        amounts = []
        for pattern in patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                try:
                    # Clean and convert to float
                    cleaned = re.sub(r'[^\d\.]', '', match)
                    amount = float(cleaned)
                    if amount > 0:
                        amounts.append(amount)
                except:
                    continue
        
        if amounts:
            # Return the largest amount found (likely to be the total)
            max_amount = max(amounts)
            self.log_debug(f"Alternative total extraction found amounts: {amounts}, returning: {max_amount}")
            return str(max_amount)
        return None
    
    def parse_date(self, date_string):
        """Parse various date formats"""
        if not date_string:
            return None
        
        try:
            # Try to parse the date
            parsed_date = date_parser.parse(date_string)
            return parsed_date.strftime('%Y-%m-%d')
        except:
            return date_string
    
    def parse_amount(self, amount_string):
        """Parse monetary amounts"""
        if not amount_string:
            return None
        
        # Remove currency symbols and commas
        cleaned = re.sub(r'[^\d\.]', '', amount_string)
        try:
            return float(cleaned)
        except:
            return amount_string
    
    def extract_line_items(self, tables, text=""):
        """Extract line items from tables or text"""
        line_items = []
        
        # First try to extract from tables
        for table in tables:
            df_records = table['data']
            if not df_records:
                continue
                
            # Look for common column patterns
            for record in df_records:
                if not record:
                    continue
                    
                # Try to identify description, quantity, price, amount columns
                item = {}
                for key, value in record.items():
                    if not key or not value:
                        continue
                        
                    key_lower = str(key).lower()
                    value_str = str(value).strip()
                    
                    if any(word in key_lower for word in ['description', 'item', 'product', 'service']):
                        item['description'] = value_str
                    elif any(word in key_lower for word in ['qty', 'quantity', 'qnt']):
                        item['quantity'] = self.parse_amount(value_str)
                    elif any(word in key_lower for word in ['price', 'rate', 'unit']):
                        item['unit_price'] = self.parse_amount(value_str)
                    elif any(word in key_lower for word in ['amount', 'total', 'sum']):
                        item['total_amount'] = self.parse_amount(value_str)
                
                if item and len(item) > 1:  # Only add if we found multiple fields
                    line_items.append(item)
        
        # If no line items found in tables, try to extract from text
        if not line_items and text:
            line_items = self._extract_line_items_from_text(text)
        
        return line_items
    
    def _extract_line_items_from_text(self, text):
        """Extract line items directly from text when tables aren't detected"""
        line_items = []
        lines = text.split('\n')
        
        # Look for line item patterns in Khan Academy format
        for i, line in enumerate(lines):
            line = line.strip()
            
            # Look for lines that match the pattern: "Description Qty Unit price Amount"
            # Example: "Khanmigo 1 US$4.00 US$4.00"
            
            # Pattern for line items with currency amounts
            item_pattern = r'^([A-Za-z\s]+)\s+(\d+)\s+(US\$[0-9,]+\.?[0-9]*)\s+(US\$[0-9,]+\.?[0-9]*)$'
            match = re.match(item_pattern, line)
            
            if match:
                description = match.group(1).strip()
                quantity = int(match.group(2))
                unit_price = self.parse_amount(match.group(3))
                total_amount = self.parse_amount(match.group(4))
                
                item = {
                    'description': description,
                    'quantity': quantity,
                    'unit_price': unit_price,
                    'total_amount': total_amount
                }
                
                # Look for date range in the next line
                if i + 1 < len(lines):
                    next_line = lines[i + 1].strip()
                    date_pattern = r'([A-Za-z]{3}\s+\d{1,2},\s+\d{4})\s*[–-]\s*(\d{1,2}\s+[A-Za-z]{3}\s+\d{4})'
                    date_match = re.search(date_pattern, next_line)
                    if date_match:
                        item['service_period'] = f"{date_match.group(1)} - {date_match.group(2)}"
                
                line_items.append(item)
                self.log_debug(f"Extracted line item from text: {item}")
        
        return line_items
    
    def extract_vendor_info(self, text):
        """Extract vendor information"""
        lines = text.split('\n')
        vendor_info = {}
        
        # Look for vendor information in the first part of the document (before customer info)
        for i, line in enumerate(lines[:15]):  # Focus on first 15 lines for vendor info
            line = line.strip()
            if not line:
                continue
                
            # Email pattern - prioritize khanacademy.org emails for vendor
            email_match = re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', line)
            if email_match:
                email = email_match.group()
                # Prefer Khan Academy email as vendor email
                if 'khanacademy.org' in email.lower():
                    vendor_info['email'] = email
                elif 'email' not in vendor_info:  # Only set if we don't have one yet
                    vendor_info['vendor_or_customer_email'] = email
            
            # Phone pattern
            phone_match = re.search(r'(\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4})', line)
            if phone_match:
                vendor_info['phone'] = phone_match.group()
            
            # Address patterns (basic) - look for PO Box, street addresses
            if re.search(r'po\s+box\s+\d+|mountain\s+view|california', line, re.IGNORECASE):
                vendor_info['address'] = line
        
        return vendor_info
    
    def extract_invoice_data(self, pdf_path):
        """Main method to extract all invoice data with enhanced processing"""
        try:
            self.log_debug(f"Starting extraction for: {pdf_path}")
            
            # Extract text and tables
            text = self.extract_text_from_pdf(pdf_path)
            if not text:
                self.log_debug("No text extracted from PDF")
                return {'error': 'No text could be extracted from PDF'}
            
            tables = self.extract_tables_from_pdf(pdf_path)
            self.log_debug(f"Extracted {len(tables)} tables")
            
            # Try to extract invoice number from filename if not found in text
            pdf_filename = Path(pdf_path).name
            filename_invoice_match = re.search(r'([A-Fa-f0-9]{8}-[0-9]{4})', pdf_filename)
            filename_invoice_number = filename_invoice_match.group(1) if filename_invoice_match else None
            
            # Extract basic fields using patterns
            invoice_data = {}
            
            # Extract invoice number with fallback to filename
            invoice_number = self.extract_using_patterns(text, 'invoice_number')
            if not invoice_number and filename_invoice_number:
                invoice_number = filename_invoice_number
                self.log_debug(f"Using invoice number from filename: {invoice_number}")
            invoice_data['invoice_number'] = invoice_number
            
            # Extract other fields
            invoice_data['date'] = self.parse_date(self.extract_using_patterns(text, 'date'))
            invoice_data['due_date'] = self.parse_date(self.extract_using_patterns(text, 'due_date'))
            invoice_data['total'] = self.parse_amount(self.extract_using_patterns(text, 'total'))
            invoice_data['subtotal'] = self.parse_amount(self.extract_using_patterns(text, 'subtotal'))
            invoice_data['tax'] = self.parse_amount(self.extract_using_patterns(text, 'tax'))
            invoice_data['vendor_name'] = self.extract_using_patterns(text, 'vendor_name')
            invoice_data['customer_name'] = self.extract_using_patterns(text, 'customer_name')
            
            # Extract vendor information
            vendor_info = self.extract_vendor_info(text)
            if vendor_info:
                invoice_data['vendor_info'] = vendor_info
            
            # Extract line items
            line_items = self.extract_line_items(tables, text)
            if line_items:
                invoice_data['line_items'] = line_items
            
            # Try to extract additional data using text analysis
            additional_data = self.extract_additional_data(text)
            invoice_data.update(additional_data)
            
            # Add metadata
            invoice_data['extraction_date'] = datetime.now().isoformat()
            invoice_data['source_file'] = str(pdf_path)
            
            # Add raw data for debugging
            if self.debug:
                invoice_data['debug_info'] = {
                    'extracted_text_length': len(text),
                    'tables_found': len(tables),
                    'filename_invoice_number': filename_invoice_number
                }
                invoice_data['raw_text'] = text[:1000] + "..." if len(text) > 1000 else text
            
            # Add raw tables for reference
            if tables:
                invoice_data['raw_tables'] = tables
            
            return invoice_data
            
        except Exception as e:
            error_msg = f'Failed to extract data: {str(e)}'
            self.log_debug(f"Error: {error_msg}")
            return {'error': error_msg}
    
    def extract_additional_data(self, text):
        """Extract additional data using enhanced text analysis"""
        additional_data = {}
        
        # Look for PO numbers (but exclude "PO Box" addresses)
        po_patterns = [
            r'p\.?o\.?\s*#?\s*:?\s*([A-Za-z0-9\-_]+)',
            r'purchase\s*order\s*#?\s*:?\s*([A-Za-z0-9\-_]+)',
            r'order\s*#?\s*:?\s*([A-Za-z0-9\-_]+)',
        ]
        for pattern in po_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                po_value = match.group(1).strip()
                # Don't include "Box" from "PO Box" addresses
                if po_value.lower() != 'box':
                    additional_data['po_number'] = po_value
                    break
        
        # Look for payment terms
        terms_patterns = [
            r'terms?\s*:?\s*([A-Za-z0-9\s\-,]+)',
            r'payment\s*terms?\s*:?\s*([A-Za-z0-9\s\-,]+)',
            r'net\s*(\d+)',
        ]
        for pattern in terms_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                additional_data['payment_terms'] = match.group(1).strip()
                break
        
        # Look for currency
        currency_patterns = [
            r'\$',  # USD
            r'USD',
            r'CAD',
            r'EUR',
            r'€',
            r'£',
        ]
        for pattern in currency_patterns:
            if re.search(pattern, text):
                if pattern == r'\$':
                    additional_data['currency'] = 'USD'
                elif pattern == '€':
                    additional_data['currency'] = 'EUR'
                elif pattern == '£':
                    additional_data['currency'] = 'GBP'
                else:
                    additional_data['currency'] = pattern
                break
        
        return additional_data

def main():
    parser = argparse.ArgumentParser(description='Extract data from PDF invoices')
    parser.add_argument('pdf_path', help='Path to the PDF invoice file')
    parser.add_argument('-o', '--output', help='Output JSON file path (optional)')
    parser.add_argument('--pretty', action='store_true', help='Pretty print JSON output')
    parser.add_argument('--debug', action='store_true', help='Enable debug output')
    
    args = parser.parse_args()
    
    # Check if PDF file exists
    pdf_path = Path(args.pdf_path)
    if not pdf_path.exists():
        print(f"Error: PDF file '{pdf_path}' not found.")
        sys.exit(1)
    
    # Extract invoice data with debug option
    extractor = InvoiceExtractor(debug=args.debug)
    invoice_data = extractor.extract_invoice_data(pdf_path)
    
    # Format JSON output
    if args.pretty:
        json_output = json.dumps(invoice_data, indent=2, ensure_ascii=False)
    else:
        json_output = json.dumps(invoice_data, ensure_ascii=False)
    
    # Output results
    if args.output:
        output_path = Path(args.output)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(json_output)
        print(f"Invoice data extracted and saved to: {output_path}")
    else:
        print(json_output)

if __name__ == "__main__":
    main()