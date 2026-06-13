import os
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorGridFSBucket

load_dotenv()

MONGO_URI: str = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
DB_NAME: str = os.getenv("DB_NAME", "jeevakosha")

client = AsyncIOMotorClient(MONGO_URI)
db = client[DB_NAME]

# GridFS bucket — stores raw file binaries (images / PDFs)
fs_bucket = AsyncIOMotorGridFSBucket(db, bucket_name="medical_files")

# Collections
hospitals_col = db["hospitals"]
documents_col = db["documents"]


async def create_indexes() -> None:
    """Create MongoDB indexes on first startup."""
    await hospitals_col.create_index("slug", unique=True)
    await documents_col.create_index(
        [("hospital_id", 1), ("folder", 1), ("stored_filename", 1)],
        unique=True,
    )
    await documents_col.create_index(
        [("hospital_id", 1), ("folder", 1), ("upload_date", -1)]
    )
    await documents_col.create_index("ocr_status")
