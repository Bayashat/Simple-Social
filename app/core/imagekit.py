"""ImageKit async client. See https://imagekit.io/docs/integration/python"""

from imagekitio import AsyncImageKit

from app.core.config import get_settings

_s = get_settings()

async_imagekit = AsyncImageKit(private_key=_s.imagekit_private_key)
IMAGEKIT_UPLOAD_FOLDER: str = _s.imagekit_upload_folder
URL_ENDPOINT: str | None = _s.imagekit_public_url_base
