from datetime import datetime
from src.utils.database import get_db_cursor
from src.utils import logger
import asyncio
from src.utils.redis import update_state, append_chunk

class PerformanceService:
    @staticmethod
    def get_grn_data(grn_number: str):
        with get_db_cursor() as cursor:
            # Step 1: Get GRN header info
            query = "SELECT id, expected_delivery_date, actual_receipt_date FROM grns WHERE grn_no = %s"
            cursor.execute(query, (grn_number,))
            grn = cursor.fetchone()
            
            if not grn:
                return None
            
            grn_id = grn['id']
            
            # Step 2: Get GRN items info
            query = "SELECT po_quantity, received_quantity, damaged_quantity FROM grn_items WHERE grn_id = %s"
            cursor.execute(query, (grn_id,))
            items = cursor.fetchall()
            
            return {
                "header": grn,
                "items": items
            }

    @staticmethod
    async def generate_performance_report(report_id: str, grn_number: str):
        try:
            logger.info(f"Generating performance report for GRN: {grn_number}, Report ID: {report_id}")
            await update_state(report_id, "processing")
            
            # Start with a title and timestamp
            await append_chunk(report_id, f"# 📊 Performance Analytics Report\n")
            await append_chunk(report_id, f"**GRN Number:** `{grn_number}`  \n")
            await append_chunk(report_id, f"**Generated on:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            await append_chunk(report_id, "---\n\n")
            
            await asyncio.sleep(0.3)
            
            data = PerformanceService.get_grn_data(grn_number)
            
            if not data:
                await append_chunk(report_id, f"❌ **Error:** GRN `{grn_number}` was not found in the system.\n")
                await update_state(report_id, "error", error="GRN not found")
                return

            header = data['header']
            items = data['items']
            
            # --- Section 1: Delivery Analysis ---
            await append_chunk(report_id, "### 🕒 Delivery Timeline Analysis\n")
            expected = header['expected_delivery_date']
            actual = header['actual_receipt_date']
            
            timeline_status = ""
            timeline_icon = ""
            if actual <= expected:
                timeline_status = "On-time delivery"
                timeline_icon = "✅"
            else:
                delay = (actual - expected).days
                timeline_status = f"Delayed by {delay} days"
                timeline_icon = "⚠️"
            
            await append_chunk(report_id, f"| Metric | Details |\n| :--- | :--- |\n")
            await append_chunk(report_id, f"| **Expected Date** | {expected} |\n")
            await append_chunk(report_id, f"| **Actual Receipt** | {actual} |\n")
            await append_chunk(report_id, f"| **Delivery Status** | {timeline_icon} {timeline_status} |\n\n")
            
            await asyncio.sleep(0.5)

            # --- Section 2: Quantity & Quality Breakdown ---
            await append_chunk(report_id, "### 📦 Item-level Breakdown\n")
            await append_chunk(report_id, "| # | PO Qty | Rec. Qty | Dmg. Qty | Fulfillment | Quality |\n")
            await append_chunk(report_id, "| :--- | :--- | :--- | :--- | :--- | :--- |\n")
            
            total_po = 0
            total_received = 0
            total_damaged = 0
            
            for idx, item in enumerate(items, 1):
                po = float(item['po_quantity'] or 0)
                rec = float(item['received_quantity'] or 0)
                dmg = float(item['damaged_quantity'] or 0)
                
                total_po += po
                total_received += rec
                total_damaged += dmg
                
                fulfillment = (rec / po * 100) if po > 0 else 0
                quality_status = "OK" if dmg == 0 else "🚨 DAMAGED"
                
                await append_chunk(report_id, f"| {idx} | {po:,.2f} | {rec:,.2f} | {dmg:,.2f} | {fulfillment:.1f}% | {quality_status} |\n")
            
            await asyncio.sleep(0.5)

            # --- Section 3: Executive Summary ---
            await append_chunk(report_id, "\n### 📈 Executive Summary\n")
            
            overall_fulfillment = (total_received / total_po * 100) if total_po > 0 else 0
            overall_quality = ((total_received - total_damaged) / total_received * 100) if total_received > 0 else 100
            
            summary_points = []
            if total_po == 0:
                summary_points.append("- ⚠️ **Alert:** No PO quantity found for this order.")
            
            if total_damaged > 0:
                summary_points.append(f"- 🚨 **Quality Issue:** {total_damaged:,.2f} items were reported as damaged.")
            
            if total_received < total_po:
                diff = total_po - total_received
                summary_points.append(f"- 📉 **Shortage:** Order is short by {diff:,.2f} units ({overall_fulfillment:.1f}% fulfillment).")
            elif total_received > total_po:
                diff = total_received - total_po
                summary_points.append(f"- 📈 **Excess:** Received {diff:,.2f} additional units beyond PO.")
            else:
                summary_points.append("- ✅ **Quantity:** All ordered units were received.")

            if actual > expected:
                summary_points.append(f"- ⏳ **Late Arrival:** The shipment arrived after the expected delivery date.")

            await append_chunk(report_id, "\n".join(summary_points) + "\n\n")

            # --- Section 4: Final Assessment ---
            await append_chunk(report_id, "### 🎯 Final Assessment\n")
            if actual <= expected and total_damaged == 0 and total_received == total_po:
                 await append_chunk(report_id, "> 🌟 **EXCELLENT:** This order meets all performance and quality standards.\n")
            elif actual <= expected and total_damaged == 0 and total_received > 0:
                 await append_chunk(report_id, "> 👍 **GOOD:** The order was on time and undamaged, though quantities vary from PO.\n")
            else:
                 await append_chunk(report_id, "> 🔍 **NEEDS REVIEW:** Issues with timing, quantity, or quality were detected. Follow-up recommended.\n")

            await update_state(report_id, "done")
            logger.info(f"Report {report_id} generated successfully")
            
        except Exception as e:
            logger.error(f"Error generating report {report_id}: {e}")
            await update_state(report_id, "error", error=str(e))
            await append_chunk(report_id, f"\n\n**Error during generation**: {str(e)}")
