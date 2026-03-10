# zip_utils.py
import zipfile
from io import BytesIO
from pathlib import Path

async def process_zip_data(zip_data: bytes, llm, process_file_fn) -> str:
    """Extract and process files within a ZIP archive using the supplied process_file function."""
    try:
        results = []
        with zipfile.ZipFile(BytesIO(zip_data)) as z:
            for name in z.namelist():
                if z.getinfo(name).is_dir():
                    continue
                with z.open(name) as file:
                    content = file.read()
                    path = Path(name)
                    try:
                        result = await process_file_fn(file_data=content, llm=llm, file_path=path)
                        results.append(f"### File: {name}\n{result}")
                    except Exception as inner_e:
                        results.append(f"### File: {name}\nError: {inner_e}")
        return "\n\n".join(results)
    except Exception as e:
        raise Exception(f"Error processing ZIP file: {e}")
