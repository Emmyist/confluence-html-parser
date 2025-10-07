from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import json
from bs4 import BeautifulSoup

app = FastAPI()

@app.post("/parse-table")
async def parse_table(request: Request):
    try:
        # Step 1: Read the raw text body
        raw_body = await request.body()
        raw_text = raw_body.decode("utf-8")

        print("=== RAW BODY RECEIVED ===")
        print(raw_text[:1000])  # Print first 1000 chars for inspection

        # Step 2: Try parsing JSON safely
        try:
            data = json.loads(raw_text)
        except json.JSONDecodeError as e:
            return JSONResponse(status_code=400, content={"error": f"Invalid JSON: {str(e)}"})

        # Step 3: Extract the HTML from known keys
        html_content = (
            data.get("body", {}).get("body", {}).get("storage", {}).get("value") or
            data.get("body", {}).get("storage", {}).get("value")
        )

        if not html_content:
            return JSONResponse(status_code=400, content={"error": "No HTML found in body"})

        # Step 4: Parse HTML with BeautifulSoup
        soup = BeautifulSoup(html_content, "html.parser")
        rows = []
        for row in soup.select("table tr"):
            cols = [col.get_text(strip=True) for col in row.find_all(["th", "td"])]
            if cols:
                rows.append(cols)

        return {"success": True, "rows": rows}

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
