from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
import uvicorn
from routers import orders, webhooks

app = FastAPI(title="Core Checkout Engine", version="2026.1.0")


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    """Log validation failures in a readable way before returning a 422."""
    print("\n--- FASTAPI VALIDATION ERROR ---")
    for error in exc.errors():
        print(f"Field location: {error['loc']}")
        print(f"Error message:  {error['msg']}")
        print(f"Error type:     {error['type']}\n")
    return JSONResponse(status_code=422, content={"detail": exc.errors()})

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register the payment and webhook routers on the application.
app.include_router(orders.router)
app.include_router(webhooks.router)

if __name__ == "__main__":
    # Reload is convenient while developing locally.
    uvicorn.run("main:app", host="0.0.0.0", port=5000, reload=True)