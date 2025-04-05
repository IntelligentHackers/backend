from fastapi import Request, FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pymongo.errors import OperationFailure
from routers import (
    users_router,
    sessions_router,
    selections_router,
)
from database import close_mongo_connection, connect_to_mongo
from fastapi.middleware.cors import CORSMiddleware
from database import db
from sockets import socket
import connections


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "https://v4.gensync.site",
        "https://v4-netlify.gensync.site",
        "https://deploy-preview-64--gensync.netlify.app",
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/socket.io", socket)

async def mark_all_tasks_failed():
    await db.gensync.tasks.update_many(
        {"status": {"$ne": "completed"}},
        {"$set": {"status": "failed", "errmsg": "Program interrupted unexpectedly"}},
    )


# Register events
app.add_event_handler("startup", connect_to_mongo)
app.add_event_handler("shutdown", close_mongo_connection)

# Register routes
app.include_router(users_router.router, prefix="/api/users", tags=["users"])
app.include_router(sessions_router.router, prefix="/api/sessions", tags=["sessions"])
app.include_router(
    selections_router.router, prefix="/api/selections", tags=["selections"]
)


@app.router.get("/api/")
async def home():
    return {}


@app.get("/api/cert")
async def get_cert():
    return {
        "status": "ok",
        "code": 200,
        "data": open("./rsa_public_key.pem", "r").read(),
    }


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_: Request, exc: RequestValidationError):
    """Convert Pydantic errors to a readable string for frontend display."""
    errors = exc.errors()
    formatted_errors = []

    for error in errors:
        field = " → ".join(map(str, error["loc"]))  # Format location as "body → field"
        message = error["msg"]
        formatted_errors.append(f"{field}: {message}")

    error_string = "\n".join(formatted_errors)  # Combine into a single string
    return JSONResponse(content={"detail": error_string}, status_code=422)


@app.exception_handler(Exception)
async def generic_exception_handler():
    """Catch-all exception handler to return a generic error message."""
    return JSONResponse(
        content={"detail": "An internal server error occurred"}, status_code=500
    )


@app.exception_handler(OperationFailure)
async def operation_failure_exception_handler(_: Request, exc: OperationFailure):
    """Catch-all exception handler to return a generic error message."""
    return JSONResponse(content={"detail": exc.details["errmsg"]}, status_code=400)


@app.get("/api/version")
async def get_version():
    return {"status": "ok", "code": 200, "data": "0.1.0-alpha.1"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app=app, host="0.0.0.0", port=8000)
