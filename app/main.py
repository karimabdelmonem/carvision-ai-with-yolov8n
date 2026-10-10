"""
نقطة البداية لتطبيق CarScan.

الفكرة:
    - ننشئ FastAPI app
    - نضيف CORS
    - نضم كل الـ routers (حاليًا scan بس)
    - نضيف endpoints بسيطة للتأكد إن السيرفر شغال
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.config import settings
from app.routes.scan import router as scan_router
from app.routes.scans import router as scans_router


# 1) إنشاء التطبيق

app = FastAPI(
    title="CarScan API",
    description="كشف أضرار العربيات بالـ AI من صورة واحدة.",
    version="0.1.0",
)


# 2) CORS

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 3) ضم الـ routers

app.include_router(scan_router)
app.include_router(scans_router)

# 4) Endpoints بسيطة

@app.get("/", tags=["Root"])
async def root():
    return {
        "app": "CarScan API",
        "version": "0.1.0",
        "docs": "/docs",
    }


@app.get("/health", tags=["Root"])
async def health():
    return {"status": "ok"}

# 6) تقديم الفرونت إند (Static Files)

app.mount(
    "/app",
    StaticFiles(directory="app/static", html=True),
    name="frontend",
)


# لو حبيت تشغّل بـ `python -m app.main` بدل uvicorn

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=True,
    )