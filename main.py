from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
import traceback, os
from app.routers import ingest, query

app = FastAPI(title="RAG Pipeline API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    tb = traceback.format_exc()
    print("\n" + "="*60)
    print("ERROR on:", request.method, request.url)
    print(tb)
    print("="*60 + "\n")
    return JSONResponse(status_code=500, content={"detail": str(exc)})

app.include_router(ingest.router, prefix="/api/v1/ingest", tags=["Ingestion"])
app.include_router(query.router, prefix="/api/v1/query", tags=["Query"])

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.get("/", response_class=HTMLResponse)
def serve_frontend():
    path = os.path.join(os.path.dirname(__file__), "app", "static", "index.html")
    with open(path, "r", encoding="utf-8") as f:
        return HTMLResponse(f.read())