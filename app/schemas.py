"""
Schemas المشروع - تحدد شكل البيانات الداخلة والخارجة من الـ API.

الـ FastAPI بيستخدم الملف ده لـ:
1. التحقق من صحة البيانات
2. توثيق تلقائي (Swagger)
3. تحويل تلقائي بين Python و JSON
"""

from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


# Detection: كشف واحد

class Detection(BaseModel):
    """
    يمثل كشف واحد (عيب واحد في العربية).
    """
    class_id: int = Field(
        ..., description="رقم الكلاس (0-5)"
    )
    class_name: str = Field(
        ..., description="اسم الكلاس بالإنجليزي"
    )
    class_name_ar: str = Field(
        ..., description="اسم الكلاس بالعربي"
    )
    confidence: float = Field(
        ..., ge=0.0, le=1.0,
        description="درجة الثقة (0-1)"
    )
    bbox: List[float] = Field(
        ..., description="إحداثيات البوكس [x1, y1, x2, y2]"
    )
    area: float = Field(
        ..., ge=0.0,
        description="مساحة البوكس بالبكسل"
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "class_id": 1,
                "class_name": "dent",
                "class_name_ar": "انبعاج",
                "confidence": 0.89,
                "bbox": [120.5, 230.0, 340.2, 450.8],
                "area": 48560.5,
            }
        }
    }


# ScanResponse: الرد الكامل لـ /scan

class ScanResponse(BaseModel):
    """
    الرد الكامل من endpoint الفحص.
    """
    scan_id: str = Field(
        ..., description="معرف فريد للفحص"
    )
    image_url: str = Field(
        ..., description="رابط الصورة الأصلية"
    )
    detections: List[Detection] = Field(
        default_factory=list,
        description="قائمة العيوب المكتشفة"
    )
    damage_count: int = Field(
        ..., ge=0,
        description="عدد العيوب"
    )
    summary: Dict[str, int] = Field(
        default_factory=dict,
        description="ملخص: كل نوع عيب وكم مرة ظهر"
    )
    created_at: datetime = Field(
        ..., description="وقت الفحص"
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "scan_id": "abc-123-def-456",
                "image_url": "https://...supabase.co/storage/...",
                "detections": [
                    {
                        "class_id": 1,
                        "class_name": "dent",
                        "class_name_ar": "انبعاج",
                        "confidence": 0.89,
                        "bbox": [120.5, 230.0, 340.2, 450.8],
                        "area": 48560.5,
                    }
                ],
                "damage_count": 1,
                "summary": {"انبعاج": 1},
                "created_at": "2026-10-10T12:00:00Z",
            }
        }
    }


# HealthResponse: للـ health check

class HealthResponse(BaseModel):
    """
    رد الـ /health endpoint.
    """
    status: str = "ok"
    app_name: str
    version: str = "1.0.0"


# ScanListItem: عنصر في قائمة الفحوصات

class ScanListItem(BaseModel):
    """
    نسخة مختصرة من الفحص - تستخدم في GET /scans.
    """
    scan_id: str = Field(..., description="معرف الفحص")
    image_url: str = Field(..., description="رابط الصورة")
    damage_count: int = Field(..., ge=0, description="عدد العيوب")
    summary: Dict[str, int] = Field(
        default_factory=dict,
        description="ملخص العيوب"
    )
    created_at: datetime = Field(..., description="وقت الفحص")


# ScanListResponse: رد GET /scans

class ScanListResponse(BaseModel):
    """
    رد قائمة الفحوصات - فيه معلومات الصفحات.
    """
    total: int = Field(..., ge=0, description="إجمالي عدد الفحوصات")
    limit: int = Field(..., ge=1, description="عدد العناصر في الصفحة")
    offset: int = Field(..., ge=0, description="من كام بدأنا")
    items: List[ScanListItem] = Field(
        default_factory=list,
        description="عناصر الصفحة الحالية"
    )


# StatsResponse: رد GET /stats

class StatsResponse(BaseModel):
    """
    إحصائيات عامة عن كل الفحوصات.
    """
    total_scans: int = Field(..., ge=0, description="إجمالي الفحوصات")
    total_damages: int = Field(..., ge=0, description="إجمالي العيوب")
    scans_with_damage: int = Field(..., ge=0, description="فحوصات فيها عيوب")
    scans_clean: int = Field(..., ge=0, description="فحوصات نضيفة")
    average_damages_per_scan: float = Field(
        ..., ge=0.0, description="متوسط العيوب لكل فحص"
    )
    most_common_damage: Optional[str] = Field(
        None, description="أكثر عيب متكرر (بالعربي)"
    )
    damage_breakdown: Dict[str, int] = Field(
        default_factory=dict,
        description="عدد مرات ظهور كل نوع عيب"
    )


# DeleteResponse: رد DELETE /scans/{id}

class DeleteResponse(BaseModel):
    """
    رد حذف فحص.
    """
    scan_id: str = Field(..., description="معرف الفحص المحذوف")
    deleted: bool = Field(True, description="هل تم الحذف؟")
    message: str = Field("Scan deleted successfully")