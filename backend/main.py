import datetime
import random
from fastapi import FastAPI, UploadFile, File, BackgroundTasks, Body
import asyncio
from typing import List, Dict
import uuid

app = FastAPI()

# Store progress by session ID
progress: Dict[str, Dict] = {}

data_locations = ["Bad Schandau P+R", "Bad Schandau Elbbrücke", "Schmilka"]


# Background task to simulate process steps
async def simulate_process(session_id: str):
    steps = [
        ("preprocessed", "Preprocessing complete"),
        ("main_process", "Main processing complete"),
        ("postprocess", "Postprocessing complete"),
        ("done", "All steps completed")
    ]

    for i, (key, message) in enumerate(steps, start=1):
        await asyncio.sleep(4)
        progress[session_id]["status"] = key
        progress[session_id]["message"] = message


@app.post("/upload/")
async def upload_file(file: UploadFile = File(...), background_tasks: BackgroundTasks = None):
    session_id = str(uuid.uuid4())
    filepath = f"/tmp/{session_id}_{file.filename}"

    with open(filepath, "wb") as f:
        f.write(await file.read())

    # Initialize progress
    progress[session_id] = {"status": "starting", "message": "Load ..."}

    # Launch background task
    background_tasks.add_task(simulate_process, session_id)

    return {"session_id": session_id}


@app.get("/progress/{session_id}")
async def get_progress(session_id: str):
    if session_id not in progress:
        return {"error": "Session not found"}

    return progress[session_id]


@app.get("/locations", response_model=list[str])
def get_locations():
    """Get all available locations"""
    return data_locations

@app.post("/prognose", response_model=Dict[str, List[int]])
def get_prognose(
    locations: List[str] = Body(data_locations),
    date: datetime.date = Body(default=datetime.date.today())
):
    print(f"PROGNOSE for {date}")
    data = {}
    for location in locations:
        if location in data_locations:
            r = random.randint(20, 90)
            data[location] = [r, r + random.randint(3, 9)]
    return data

@app.post("/prognose_range", response_model=dict[str, dict[datetime.date,list[int]]])
def get_prognose_range(
        locations: List[str] = Body(data_locations),
        start: datetime.date = Body(default=datetime.date.today()- datetime.timedelta(days=4)),
        end: datetime.date = Body(default=datetime.date.today())
):
    print(f"PROGNOSE form {start} to {end}")
    data = {}
    s = start
    for location in locations:
        if location in data_locations:
            data[location] = {}
            for day in range((end - start).days + 1):
                r = random.randint(20, 90)
                data[location][s + datetime.timedelta(days=day)] = [r, r + random.randint(3, 9)]
    return data
