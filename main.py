from fastapi import FastAPI, UploadFile, File, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import shutil
import json

from ai_engine import extract_criteria, evaluate_bidder

app = FastAPI(title="TenderLens API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/frontend", StaticFiles(directory="frontend"), name="frontend")

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@app.get("/")
def serve_homepage():
    with open("frontend/index.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())


@app.get("/health")
def health_check():
    return {"status": "TenderLens is running"}


@app.post("/upload-tender")
async def upload_tender(file: UploadFile = File(...)):
    save_path = os.path.join(UPLOAD_DIR, f"tender_{file.filename}")
    with open(save_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    try:
        result = await extract_criteria(save_path)
        return JSONResponse(content={
            "success": True,
            "tender_path": save_path,
            "criteria": result
        })
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )


@app.post("/upload-bidder")
async def upload_bidder(
    file: UploadFile = File(...),
    bidder_name: str = Form(...),
    tender_path: str = Form(...),
    criteria: str = Form(...)
):
    safe_name = bidder_name.replace(" ", "_")
    save_path = os.path.join(UPLOAD_DIR, f"bidder_{safe_name}_{file.filename}")
    with open(save_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    try:
        criteria_list = json.loads(criteria)
    except json.JSONDecodeError:
        return JSONResponse(
            status_code=400,
            content={"success": False, "error": "Invalid criteria format"}
        )
    try:
        result = await evaluate_bidder(
            bidder_path=save_path,
            bidder_name=bidder_name,
            criteria=criteria_list,
            tender_path=tender_path
        )
        return JSONResponse(content={"success": True, "evaluation": result})
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )