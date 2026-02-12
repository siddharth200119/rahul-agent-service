from typing import List, Dict, Any
import json
from src.utils.database import get_db_cursor
from src.agentic.llms.primary import get_primary_llm
from src.utils import logger

class SOValidationService:
    @staticmethod
    async def validate_so(product_ids: List[int], quantities: List[float], weights: List[float]) -> List[Dict[str, Any]]:
        results = []
        llm = get_primary_llm()
        
        for p_id, qty, weight in zip(product_ids, quantities, weights):
            try:
                # 1. Fetch data from DB (Remote DB erp)
                db_data = None
                with get_db_cursor(commit=False) as cursor:
                    query = """
                        SELECT gsm, number_of_sheets, item_gross_weight, item_name
                        FROM item_master 
                        WHERE product_id = %s 
                        ORDER BY created_at DESC 
                        LIMIT 1
                    """
                    cursor.execute(query, (p_id,))
                    db_data = cursor.fetchone()

                if not db_data:
                    results.append({
                        "product_id": p_id,
                        "status": "error",
                        "message": f"Product ID {p_id} not found."
                    })
                    continue

                gsm = db_data.get('gsm')
                sheets = db_data.get('number_of_sheets')
                expected_weight = db_data.get('item_gross_weight')
                item_name = db_data.get('item_name')

                # 2. LLM Validation
                prompt = f"""
                Analyze Sales Order Item:
                - Item: {item_name}
                - Standard Spec from DB: GSM {gsm}, Sheets {sheets}, Actual Weight {expected_weight}
                - User Input: Qty {qty}, Provided Weight {weight}
                
                Compare user weight ({weight}) with standard actual weight ({expected_weight}).
                If they differ significantly, the message must be in pure English following this pattern: "You provided a weight of {weight}, but the actual weight should be {expected_weight} according to GSM {gsm} and Sheets {sheets}."
                
                Respond ONLY in this JSON format:
                {{"status": "valid/invalid", "message": "your explanation in pure English following the pattern if invalid"}}
                """
                
                llm_response = await llm.generate(prompt)
                
                message = llm_response
                status = "invalid"
                
                try:
                    clean_res = llm_response.strip()
                    if "{" in clean_res and "}" in clean_res:
                        start = clean_res.find("{")
                        end = clean_res.rfind("}") + 1
                        clean_res = clean_res[start:end]
                        parsed = json.loads(clean_res)
                        status = parsed.get("status", "invalid")
                        message = parsed.get("message", llm_response)
                except:
                    pass

                results.append({
                    "product_id": p_id,
                    "user_weight": weight,
                    "actual_weight": float(expected_weight) if expected_weight else None,
                    "gsm": float(gsm) if gsm else None,
                    "sheets": int(sheets) if sheets else None,
                    "status": status,
                    "message": message
                })

            except Exception as e:
                logger.error(f"Validation Service Error for product {p_id}: {e}")
                results.append({"product_id": p_id, "status": "error", "message": str(e)})

        return results
