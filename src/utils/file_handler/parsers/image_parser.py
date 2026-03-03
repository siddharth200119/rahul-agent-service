from RAW.modals import Image
from RAW.llms import BaseLLM

async def image_parser(image_data: bytes, llm: BaseLLM, markdown: bool = False) -> str:
    """Extract text from an image using an LLM.
    Optionally return results as a markdown-formatted string.
    """
    print("Processing Image for OCR...")
    try:
        # if llm is None or not hasattr(llm, "generate"):
        #     return "[OCR Skipped: No text generation capability]"
        image = Image.from_bytes(image_data)
        
        prompt = "Extract all visible text from the image accurately. Return only the extracted text."
    
        result = await llm.generate(prompt=prompt, images=[image], stream=False)
        # print("result form img parser:", result)

        if not isinstance(result, str):
            raise ValueError(f"Expected string response from LLM, got {type(result)}")
        
        if markdown:
            return f"\n### OCR Result\n\n```\n{result.strip()}\n```\n"
        
        return result.strip()
    
    except Exception as e:
        raise Exception(f"Error processing image: {e}")
