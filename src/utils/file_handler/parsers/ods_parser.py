import ezodf
from io import BytesIO

def ods_parser(file_data: bytes, markdown: bool = False) -> str:
    """Extract text from ODS spreadsheets."""
    try:
        ods_file = BytesIO(file_data)
        doc = ezodf.opendoc(ods_file)
        output = ""

        for sheet in doc.sheets:
            output += f"\n### Sheet: {sheet.name}\n"
            for row in sheet.rows():
                values = [str(cell.value) if cell.value is not None else "" for cell in row]
                output += " | ".join(values) + "\n"

        return output
    except Exception as e:
        raise Exception(f"Error processing ODS file: {e}")