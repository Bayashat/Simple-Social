"""ImageKit server-side upload client. See https://imagekit.io/docs/integration/python"""

import os

from dotenv import load_dotenv
from imagekitio import AsyncImageKit

load_dotenv()

# Media library folder; override with IMAGEKIT_UPLOAD_FOLDER=/your/path
IMAGEKIT_UPLOAD_FOLDER: str = os.environ.get("IMAGEKIT_UPLOAD_FOLDER", "/posts")

# Optional: used when building transformed URLs client-side (`helper.build_url`); not required for uploads.
URL_ENDPOINT: str | None = os.environ.get("IMAGEKIT_URL_ENDPOINT") or os.environ.get("IMAGEKIT_URL") or None

async_imagekit = AsyncImageKit(private_key=os.environ.get("IMAGEKIT_PRIVATE_KEY"))
