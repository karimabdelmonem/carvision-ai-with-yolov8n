"""
Endpoints إدارة الفحوصات - قراءة، حذف، إحصائيات.

الفرق بينه وبين scan.py:
    - scan.py: عملية الفحص نفسها (POST /scan)
    - scans.py: إدارة الفحوصات المخزّنة (GET/DELETE/GET stats)
"""

from fastapi import APIRouter, HTTPException, Query

from app.config import settings
from app.db.supabase_client import get_supabase
from app.schemas import (
    DeleteResponse,
    ScanListItem,
    ScanListResponse,
    ScanResponse,
    StatsResponse,
)


router = APIRouter(
    prefix="/scans",
    tags=["Scans"],
)


# GET /scans - قائمة الفحوصات

@router.get(
    "",
    response_model=ScanListResponse,
    summary="قائمة كل الفحوصات",
    description="ترجع الفحوصات مرتبة من الأحدث للأقدم، مع Pagination.",
)
async def list_scans(
    limit: int = Query(20, ge=1, le=100, description="عدد العناصر في الصفحة"),
    offset: int = Query(0, ge=0, description="من كام نبدأ"),
) -> ScanListResponse:
    sb = get_supabase()

    # 1. العدد الإجمالي
    count_resp = (
        sb.table("scans")
        .select("id", count="exact")
        .execute()
    )
    total = count_resp.count or 0

    # 2. الصفحة المطلوبة
    resp = (
        sb.table("scans")
        .select("id, image_url, damage_count, summary, created_at")
        .order("created_at", desc=True)
        .range(offset, offset + limit - 1)
        .execute()
    )

    items = [
        ScanListItem(
            scan_id=row["id"],
            image_url=row["image_url"],
            damage_count=row["damage_count"],
            summary=row.get("summary") or {},
            created_at=row["created_at"],
        )
        for row in resp.data
    ]

    return ScanListResponse(
        total=total,
        limit=limit,
        offset=offset,
        items=items,
    )


# GET /scans/stats - إحصائيات

# ⚠️ مهم جدًا: لازم يتسجل قبل /{scan_id}
# عشان FastAPI ميفهمش "stats" على إنها scan_id

@router.get(
    "/stats",
    response_model=StatsResponse,
    summary="إحصائيات الفحوصات",
)
async def get_stats() -> StatsResponse:
    sb = get_supabase()

    resp = (
        sb.table("scans")
        .select("damage_count, summary")
        .execute()
    )
    rows = resp.data or []

    total_scans = len(rows)
    total_damages = sum(r.get("damage_count", 0) for r in rows)
    scans_clean = sum(1 for r in rows if r.get("damage_count", 0) == 0)
    scans_with_damage = total_scans - scans_clean

    # تجميع الـ breakdown
    breakdown: dict = {}
    for r in rows:
        for damage_name, count in (r.get("summary") or {}).items():
            breakdown[damage_name] = breakdown.get(damage_name, 0) + count

    # أكثر عيب متكرر
    most_common = None
    if breakdown:
        most_common = max(breakdown.items(), key=lambda x: x[1])[0]

    avg = (total_damages / total_scans) if total_scans > 0 else 0.0

    return StatsResponse(
        total_scans=total_scans,
        total_damages=total_damages,
        scans_with_damage=scans_with_damage,
        scans_clean=scans_clean,
        average_damages_per_scan=round(avg, 2),
        most_common_damage=most_common,
        damage_breakdown=breakdown,
    )


# GET /scans/{scan_id} - تفاصيل فحص واحد

@router.get(
    "/{scan_id}",
    response_model=ScanResponse,
    summary="تفاصيل فحص واحد",
)
async def get_scan(scan_id: str) -> ScanResponse:
    sb = get_supabase()

    resp = (
        sb.table("scans")
        .select("*")
        .eq("id", scan_id)
        .execute()
    )

    if not resp.data:
        raise HTTPException(
            status_code=404,
            detail=f"الفحص '{scan_id}' غير موجود",
        )

    row = resp.data[0]

    return ScanResponse(
        scan_id=row["id"],
        image_url=row["image_url"],
        detections=row.get("detections") or [],
        damage_count=row["damage_count"],
        summary=row.get("summary") or {},
        created_at=row["created_at"],
    )


# DELETE /scans/{scan_id} - حذف فحص

@router.delete(
    "/{scan_id}",
    response_model=DeleteResponse,
    summary="حذف فحص",
)
async def delete_scan(scan_id: str) -> DeleteResponse:
    sb = get_supabase()

    # 1. نتأكد إن الفحص موجود ونجيب مسار الصورة
    resp = (
        sb.table("scans")
        .select("id, image_path")
        .eq("id", scan_id)
        .execute()
    )

    if not resp.data:
        raise HTTPException(
            status_code=404,
            detail=f"الفحص '{scan_id}' غير موجود",
        )

    image_path = resp.data[0]["image_path"]

    # 2. امسح الصورة من Storage
    # لو فشل الحذف هنا، مش مشكلة كبيرة - نكمل ونمسح من DB
    try:
        sb.storage.from_(settings.SUPABASE_BUCKET).remove([image_path])
    except Exception:
        pass

    # 3. امسح من Database
    try:
        sb.table("scans").delete().eq("id", scan_id).execute()
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"فشل حذف الفحص: {str(e)}",
        )

    return DeleteResponse(
        scan_id=scan_id,
        deleted=True,
        message="تم حذف الفحص بنجاح",
    )