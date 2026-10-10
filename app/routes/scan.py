"""
endpoint الفحص - يستقبل صورة عربية ويرجّع النتايج.

الرحلة:
    صورة → تحقق → inference → رفع على Supabase → حفظ في DB → رد
"""

from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.config import settings
from app.cv.detector import CarDamageDetector
from app.db.supabase_client import get_supabase
from app.schemas import Detection, ScanResponse


# Router

router = APIRouter(
    prefix="/scan",
    tags=["Scan"],
)

# POST /scan

@router.post(
    "",
    response_model=ScanResponse,
    summary="تحليل صورة عربية",
    description="""
    يستقبل صورة عربية ويعمل عليها inference باستخدام YOLOv8.
    
    **الخطوات:**
    1. رفع الصورة
    2. كشف العيوب (خدش، انبعاج، إلخ)
    3. رفع الصورة على Supabase Storage
    4. حفظ النتايج في Database
    5. إرجاع الرد
    """,
)
async def scan_car(file: UploadFile = File(...)) -> ScanResponse:
    """
    Args:
        file: الصورة اللي المستخدم رفعها (multipart/form-data)
    
    Returns:
        ScanResponse: فيه الـ detections + معلومات الفحص
    """
    
    # 1. تحقق من نوع الملف

    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=400,
            detail="الملف لازم يكون صورة (jpg, png, webp)",
        )
    
    # 2. اقرا محتوى الملف
    
    content = await file.read()
    
    size_mb = len(content) / (1024 * 1024)
    if size_mb > settings.MAX_IMAGE_SIZE_MB:
        raise HTTPException(
            status_code=413,
            detail=f"الصورة كبيرة جدًا ({size_mb:.1f}MB). الحد: {settings.MAX_IMAGE_SIZE_MB}MB",
        )
    
    # 3. شغل الموديل (Inference)

    detector = CarDamageDetector.get_instance(
        settings.MODEL_PATH,
        conf=settings.CONFIDENCE_THRESHOLD,
        iou=settings.IOU_THRESHOLD,
    )
    
    try:
        raw_detections = detector.predict_file(content)
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=f"الملف مش صورة صحيحة: {str(e)}",
        )
    
    detections = [Detection(**d) for d in raw_detections]
    
    # 4. ارفع الصورة على Supabase Storage

    sb = get_supabase()
    scan_id = str(uuid4())
    
    # خد الامتداد من اسم الملف الأصلي
    ext = "jpg"
    if file.filename and "." in file.filename:
        ext = file.filename.rsplit(".", 1)[-1].lower()
    
    storage_path = f"scans/{scan_id}.{ext}"
    
    try:
        sb.storage.from_(settings.SUPABASE_BUCKET).upload(
            path=storage_path,
            file=content,
            file_options={"content-type": file.content_type},
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"فشل رفع الصورة: {str(e)}",
        )
    
    # هات الـ public URL
    image_url = sb.storage.from_(
        settings.SUPABASE_BUCKET
    ).get_public_url(storage_path)
    
    # 5. ابني Summary

    summary: dict = {}
    for d in detections:
        key = d.class_name_ar
        summary[key] = summary.get(key, 0) + 1
    
    # 6. احفظ في Database

    created_at = datetime.now(timezone.utc)
    
    row = {
        "id": scan_id,
        "image_path": storage_path,
        "image_url": image_url,
        "detections": [d.model_dump() for d in detections],
        "damage_count": len(detections),
        "summary": summary,
        "created_at": created_at.isoformat(),
    }
    
    try:
        sb.table("scans").insert(row).execute()
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"فشل حفظ النتايج: {str(e)}",
        )
    
    # 7. ابني الرد

    return ScanResponse(
        scan_id=scan_id,
        image_url=image_url,
        detections=detections,
        damage_count=len(detections),
        summary=summary,
        created_at=created_at,
    )