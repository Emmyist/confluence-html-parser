from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import re
import json

app = FastAPI()

@app.post("/")
async def parse_confluence_data(request: Request):
    try:
        raw_body = await request.body()
        text = raw_body.decode("utf-8", errors="ignore").strip()

        print("🔹 Raw body received:")
        print(text[:400] + "..." if len(text) > 400 else text)

        # If Jira sends JSON, try to parse it
        data = None
        format = "html"
        try:
            body = json.loads(text)
            data = body.get("data")
            format = body.get("format", "html")
        except json.JSONDecodeError:
            # Not JSON → assume it’s raw HTML directly
            data = text

        if not data:
            return JSONResponse({"error": "No data found"}, status_code=400)

        # --- 🧩 Clean HTML and extract table ---
        rows = []
        table_match = re.search(r"<table[\s\S]*?</table>", data)
        if not table_match:
            return JSONResponse({"error": "No <table> found in data"}, status_code=400)

        table_html = table_match.group(0)

        # Find rows
        row_matches = re.findall(r"<tr[^>]*>([\s\S]*?)</tr>", table_html)
        for row in row_matches:
            # Find cells in each row
            cell_matches = re.findall(r"<t[dh][^>]*>([\s\S]*?)</t[dh]>", row)
            cleaned_cells = []
            for c in cell_matches:
                # remove inner tags like <p>, <time>, etc.
                text_value = re.sub(r"<[^>]+>", "", c)
                text_value = re.sub(r"&nbsp;", " ", text_value)
                cleaned_cells.append(text_value.strip())
            if cleaned_cells:
                rows.append(cleaned_cells)

        print("✅ Parsed rows:", rows)

        return JSONResponse({
            "row_count": len(rows),
            "rows": rows
        })

    except Exception as e:
        print("❌ ERROR:", str(e))
        return JSONResponse({"error": str(e)}, status_code=500)
