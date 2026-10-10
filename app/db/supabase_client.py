"""
الاتصال بـ Supabase.

الفكرة:
- نفتح اتصال واحد بس (Singleton) — زي الموديل بالظبط
- نوفر دوال مساعدة للعمليات الشائعة (upload, insert, select)
"""

from typing import Optional
from supabase import create_client, Client

from app.config import settings


# Singleton: اتصال واحد لكل التطبيق
_client: Optional[Client] = None

def get_supabase() -> Client:
    """
    يرجّع اتصال Supabase (نفس الكائن في كل مرة).

    الاستخدام:
        from app.db.supabase_client import get_supabase
        sb = get_supabase()
        sb.table("scans").select("*").execute()
    """
    global _client

    if _client is None:
        _client = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_KEY,
        )

    return _client


# Helper: اختبار الاتصال

def test_connection() -> dict:
    """
    يتأكد إن الاتصال بـ Supabase شغال.
    يرجّع معلومات عن الاتصال.
    """
    sb = get_supabase()

    # نحاول نقرا من الـ Storage bucket
    try:
        buckets = sb.storage.list_buckets()
        bucket_names = [b.name for b in buckets]

        return {
            "status": "ok",
            "url": settings.SUPABASE_URL,
            "buckets": bucket_names,
            "target_bucket_exists": settings.SUPABASE_BUCKET in bucket_names,
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
        }