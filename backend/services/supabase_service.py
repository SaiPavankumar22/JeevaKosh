"""
Supabase Storage integration for portfolio PDF files.

Handles:
- Bucket provisioning  (creates 'portfolios' bucket if absent)
- PDF upload
- Direct authenticated download (used to proxy the file to the viewer)
- Signed-URL generation (optional fallback)
- File deletion
"""

import os

import httpx
from dotenv import load_dotenv

load_dotenv()

BUCKET = "portfolios"


def _url() -> str:
    return os.getenv("SUPABASE_URL", "").rstrip("/")


def _key() -> str:
    return os.getenv("SUPABASE_KEY", "")


def _headers() -> dict:
    key = _key()
    return {
        "apikey": key,
        "Authorization": f"Bearer {key}",
    }


async def ensure_bucket_exists() -> None:
    """Create the 'portfolios' bucket if it doesn't exist yet."""
    base = _url()
    if not base:
        return
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.post(
                f"{base}/storage/v1/bucket",
                headers={**_headers(), "Content-Type": "application/json"},
                json={"id": BUCKET, "name": BUCKET, "public": False},
            )
            # 200/201 = created, 409 = already exists — both are fine
            if resp.status_code not in (200, 201, 409):
                print(f"[supabase] bucket create warning: {resp.status_code} {resp.text[:200]}")
    except Exception as exc:
        print(f"[supabase] bucket check warning: {exc}")


async def upload_pdf(path: str, pdf_bytes: bytes) -> str:
    """
    Upload *pdf_bytes* to Supabase Storage at *path* inside the portfolios bucket.
    Returns the storage path on success.
    Raises RuntimeError on failure.
    """
    base = _url()
    if not base or not _key():
        raise RuntimeError("SUPABASE_URL / SUPABASE_KEY not configured.")

    async with httpx.AsyncClient(timeout=120) as client:
        resp = await client.post(
            f"{base}/storage/v1/object/{BUCKET}/{path}",
            headers={
                **_headers(),
                "Content-Type": "application/pdf",
                "x-upsert": "true",
            },
            content=pdf_bytes,
        )

    if resp.status_code not in (200, 201):
        raise RuntimeError(
            f"Supabase upload failed ({resp.status_code}): {resp.text[:400]}"
        )
    return path


async def download_file(path: str) -> bytes:
    """
    Download a file from Supabase Storage using service-role auth.
    This is the most reliable way to fetch private files — no signed-URL expiry.
    Raises RuntimeError on failure.
    """
    base = _url()
    if not base:
        raise RuntimeError("SUPABASE_URL not configured.")

    # Try authenticated object endpoint first
    endpoints = [
        f"{base}/storage/v1/object/authenticated/{BUCKET}/{path}",
        f"{base}/storage/v1/object/{BUCKET}/{path}",
    ]
    last_error = ""
    async with httpx.AsyncClient(timeout=120, follow_redirects=True) as client:
        for endpoint in endpoints:
            resp = await client.get(endpoint, headers=_headers())
            if resp.status_code == 200:
                return resp.content
            last_error = f"({resp.status_code}) {resp.text[:200]}"

    raise RuntimeError(f"Supabase download failed: {last_error}")


async def create_signed_url(path: str, expires_in_seconds: int) -> str:
    """
    Create a signed URL for *path* valid for *expires_in_seconds* seconds.
    Returns the full signed URL string.
    Raises RuntimeError on failure.
    """
    base = _url()
    async with httpx.AsyncClient(timeout=20) as client:
        resp = await client.post(
            f"{base}/storage/v1/object/sign/{BUCKET}/{path}",
            headers={**_headers(), "Content-Type": "application/json"},
            json={"expiresIn": expires_in_seconds},
        )

    if resp.status_code not in (200, 201):
        raise RuntimeError(
            f"Signed URL creation failed ({resp.status_code}): {resp.text[:300]}"
        )

    data = resp.json()
    signed_path = (
        data.get("signedURL")
        or data.get("signedUrl")
        or data.get("url")
        or ""
    )
    if not signed_path:
        raise RuntimeError(f"No signedURL in response: {data}")
    if signed_path.startswith("http"):
        return signed_path
    return f"{base}{signed_path}"


async def delete_portfolio_file(path: str) -> None:
    """Remove a file from Supabase Storage (best-effort)."""
    base = _url()
    if not base:
        return
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            await client.delete(
                f"{base}/storage/v1/object/{BUCKET}/{path}",
                headers=_headers(),
            )
    except Exception as exc:
        print(f"[supabase] delete warning: {exc}")
