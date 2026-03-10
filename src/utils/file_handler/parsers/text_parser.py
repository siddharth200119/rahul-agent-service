def text_parser(file_data: bytes) -> str:
    """Extract text from bytes data by decoding it as UTF-8."""
    if not isinstance(file_data, bytes):
        raise TypeError(f"Expected bytes for file_data, got {type(file_data)}")
    try:
        return file_data.decode('utf-8', errors='replace')
    except Exception as e:
        raise Exception(f"Error processing text file: {e}")