from dotenv import load_dotenv
import os
from google import genai
from google.genai import types
from pathlib import Path

load_dotenv()

def parse_invoice(pdf_path):
    try:
        API_KEY = os.getenv("GEMINI_API_KEY")
        if not API_KEY:
            raise ValueError("API key not found. Please set the GEMINI_API_KEY environment variable.")

        client = genai.Client(api_key=API_KEY)

        filepath = Path(pdf_path)
        pdf_bytes = filepath.read_bytes()

        prompt = "Extract and summarize the invoice details from this document."

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[
                types.Part.from_bytes(
                    data=pdf_bytes,
                    mime_type='application/pdf',
                ),
                prompt
            ]
        )

        print("Parsed invoice data:")
        print(response.text)
        return response.text
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

if __name__ == "__main__":
    pdf_path = "Invoice-4E62BC7A-0001.pdf"
    parsed_data = parse_invoice(pdf_path)

    if parsed_data:
        output_path = Path("parsed_invoice.json")
        output_path.write_text(parsed_data, encoding="utf-8")
        print(f"Parsed data saved to {output_path}")