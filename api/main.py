from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from langgraph_workflow.graph import build_workflow

app = FastAPI()

# CORS for local frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/run-workflow")
async def run_workflow():
    workflow = build_workflow()
    initial_state = {
        "raw_text": None,
        "rewritten_text": None,
        "reviewed_text": None,
        "final_text": None,
        "retrieval_results": None,
        "screenshot_path": None
    }

    final_state = await workflow.ainvoke(initial_state)
    
    return {
        "final_text": final_state["final_text"],
        "screenshot_url": f"/screenshot?path={final_state['screenshot_path']}"
    }

@app.post("/submit-final")
async def submit_final(request: Request):
    body = await request.json()
    final_text = body.get("final_text")
    # Here you can write to file or DB
    with open("final_output.txt", "w", encoding="utf-8") as f:
        f.write(final_text)
    return {"message": "Final version saved!"}

from fastapi.responses import FileResponse
@app.get("/screenshot")
def get_screenshot(path: str):
    return FileResponse(path)