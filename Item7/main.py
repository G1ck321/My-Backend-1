from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError # <-- Add this import
from fastapi.responses import JSONResponse            # <-- Add this import
import uvicorn
from routers import orders, webhooks

app = FastAPI(title="Core Checkout Engine", version="2026.1.0")

# 🚨 TEMPORARY DEBUGGER: Prints exactly what field failed Pydantic validation
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    print("\n🚨 --- FASTAPI VALIDATION ERROR --- 🚨")
    for error in exc.errors():
        print(f"❌ Field Location: {error['loc']}")
        print(f"❌ Error Message:  {error['msg']}")
        print(f"❌ Error Type:     {error['type']}\n")
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors()}
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(orders.router)
app.include_router(webhooks.router)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=5000, reload=True)