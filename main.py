from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from bs4 import BeautifulSoup
import json

app = FastAPI()

@app.post("/")
async def parse_confluence_table(request: Request):
    try:
        body = await request.json()
        data = body.get("data")
        fmt = body.get("format", "html")

        if not data:
            return JSONResponse({"error": "No data received"}, status_code=400)

        rows = []

        # ✅ HTML parsing
        if fmt == "html":
            soup = BeautifulSoup(data, "html.parser")
            table = soup.find("table")
            if not table:
                return JSONResponse({"error": "No <table> found in HTML"}, status_code=400)

            for tr in table.find_all("tr"):
                cells = []
                for cell in tr.find_all(["td", "th"]):
                    # Clean text or <time> tag
                    time_tag = cell.find("time")
                    if time_tag and time_tag.get("datetime"):
                        cells.append(time_tag["datetime"])
                    else:
                        text = cell.get_text(strip=True)
                        cells.append(text)
                if cells:
                    rows.append(cells)

        # ✅ ADF parsing
        elif fmt == "adf":
            adf = json.loads(data) if isinstance(data, str) else data
            table_block = next((c for c in adf.get("content", []) if c.get("type") == "table"), None)
            if not table_block:
                return JSONResponse({"error": "No table found in ADF"}, status_code=400)

            for row in table_block.get("content", []):
                row_data = []
                for cell in row.get("content", []):
                    try:
                        paragraph = cell["content"][0]["content"]
                        text_parts = []
                        for p in paragraph:
                            if p["type"] == "date":
                                text_parts.append(p["attrs"]["timestamp"])
                            elif "text" in p:
                                text_parts.append(p["text"])
                        row_data.append(" ".join(text_parts).strip())
                    except Exception:
                        row_data.append("")
                rows.append(row_data)

        else:
            return JSONResponse({"error": f"Unknown format '{fmt}'"}, status_code=400)

        return JSONResponse({"rows": rows})

    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)
