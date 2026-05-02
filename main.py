from fastapi import FastAPI, UploadFile, File, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import shutil
import json

# Import Person A's functions
from ai_engine import extract_criteria, evaluate_bidder

app = FastAPI(title="TenderLens API")

# Allow the frontend to talk to the backend without browser security errors
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve the frontend folder as static files
app.mount("/frontend", StaticFiles(directory="frontend"), name="frontend")

# All uploaded files go here
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@app.get("/")
def serve_homepage():
    """Serves the main HTML page when someone opens the app in browser."""
    with open("frontend/index.html", "r") as f:
        return HTMLResponse(content=f.read())


@app.get("/health")
def health_check():
    """Simple check to confirm the server is running."""
    return {"status": "TenderLens is running"}


@app.post("/upload-tender")
async def upload_tender(file: UploadFile = File(...)):
    """
    Receives the tender PDF from the frontend.
    Saves it to disk.
    Calls extract_criteria() to get all eligibility criteria.
    Returns the criteria list back to the frontend.
    """
    # Save the uploaded file
    save_path = os.path.join(UPLOAD_DIR, f"tender_{file.filename}")
    with open(save_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Call AI engine to extract criteria
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
    """
    Receives a bidder's PDF submission from the frontend.
    Saves it to disk.
    Calls evaluate_bidder() to check against all criteria.
    Returns the full evaluation result back to the frontend.
    """
    # Save the bidder's file with their name in the filename
    safe_name = bidder_name.replace(" ", "_")
    save_path = os.path.join(UPLOAD_DIR, f"bidder_{safe_name}_{file.filename}")
    with open(save_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Parse the criteria JSON string sent from the frontend
    try:
        criteria_list = json.loads(criteria)
    except json.JSONDecodeError:
        return JSONResponse(
            status_code=400,
            content={"success": False, "error": "Invalid criteria format"}
        )

    # Call AI engine to evaluate the bidder
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
