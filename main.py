from fastapi import FastAPI, UploadFile, File, Form, BackgroundTasks, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import shutil
import json
import uuid

# Internal imports
from report_utils import generate_docx_report
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
REPORT_DIR = "reports"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(REPORT_DIR, exist_ok=True)

# Schema for the download request
class ReportRequest(BaseModel):
    content: str

# Helper to clean up files after download
def remove_file(path: str):
    if os.path.exists(path):
        os.remove(path)

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

@app.post("/download-report")
async def download_report(request: ReportRequest, background_tasks: BackgroundTasks):
    """
    Takes AI-generated text and returns a formatted Word Document.
    """
    try:
        # Generate a unique filename to handle concurrent users
        unique_id = uuid.uuid4().hex
        output_filename = f"TenderLens_Report_{unique_id}.docx"
        output_path = os.path.join(REPORT_DIR, output_filename)

        # Generate the DOCX file using the utility function
        generate_docx_report(request.content, output_path)

        # Schedule the file to be deleted after the response is sent
        background_tasks.add_task(remove_file, output_path)

        return FileResponse(
            path=output_path,
            filename="TenderLens_Analysis_Report.docx",
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Report generation failed: {str(e)}")    return {"status": "TenderLens is running"}


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
