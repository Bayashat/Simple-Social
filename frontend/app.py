import streamlit as st
import requests
import base64
import urllib.parse
from datetime import datetime, timedelta, timezone

st.set_page_config(page_title="Simple Social", layout="wide")

# Backend classifies uploads by MIME: image/* → image, video/* → video, everything else → file (PDF, ZIP, …).
_UPLOAD_HELP = (
    "**Supported files** (matches API): "
    "**images** (`image/*`), **videos** (`video/*`), and **any other MIME** treated as generic file "
    "(e.g. PDF, GIF, ZIP). No extension whitelist on the server."
)

# API PostRead.storage: imagekit | s3 (from PostStorage enum)
_STORAGE_LABEL = {"imagekit": "ImageKit", "s3": "AWS S3"}


def storage_label(storage: object) -> str:
    key = str(storage or "").lower().strip()
    return _STORAGE_LABEL.get(key, str(storage) if storage else "?")


def format_created_display_utc_plus_5(iso_str: str) -> str:
    """Show full wall-clock time in UTC+5 (same instant as stored ISO UTC / offset-aware)."""
    utc_plus_5 = timezone(timedelta(hours=5))
    s = (iso_str or "").strip().replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(s)
    except ValueError:
        return iso_str[:19] if len(iso_str) >= 19 else iso_str
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(utc_plus_5).strftime("%Y-%m-%d %H:%M:%S UTC+5")


for key, default in (("token", None), ("user", None)):
    if key not in st.session_state:
        st.session_state[key] = default


def get_headers():
    """Get authorization headers with token."""
    if st.session_state.token:
        return {"Authorization": f"Bearer {st.session_state.token}"}
    return {}


def login_page():
    st.title("🚀 Welcome to Simple Social")

    email = st.text_input("Email:")
    password = st.text_input("Password:", type="password")

    if email and password:
        col1, col2 = st.columns(2)

        with col1:
            if st.button("Login", type="primary", use_container_width=True):
                login_data = {"username": email, "password": password}
                response = requests.post("http://localhost:8000/auth/jwt/login", data=login_data)

                if response.status_code == 200:
                    token_data = response.json()
                    st.session_state.token = token_data["access_token"]

                    user_response = requests.get("http://localhost:8000/users/me", headers=get_headers())
                    if user_response.status_code == 200:
                        st.session_state.user = user_response.json()
                        st.rerun()
                    else:
                        st.error("Failed to get user info")
                else:
                    st.error("Invalid email or password!")

        with col2:
            if st.button("Sign Up", type="secondary", use_container_width=True):
                signup_data = {"email": email, "password": password}
                response = requests.post("http://localhost:8000/auth/register", json=signup_data)

                if response.status_code == 201:
                    st.toast("Account created — you can log in now.", icon="✅")
                else:
                    error_detail = response.json().get("detail", "Registration failed")
                    st.error(f"Registration failed: {error_detail}")
    else:
        st.info("Enter your email and password above")


def upload_page():
    st.title("📸 Share Something")

    uploaded_file = st.file_uploader(
        "Choose a file",
        type=None,
        help="Browse any file types your browser allows. The backend classifies images, videos, and other files.",
    )
    st.caption(_UPLOAD_HELP)

    caption = st.text_area("Caption:", placeholder="What's on your mind?")

    storage = st.radio(
        "Where to upload:",
        ("imagekit", "s3"),
        format_func=lambda value: {"imagekit": "ImageKit", "s3": "AWS S3"}[value],
        horizontal=True,
        help="Must match backend configuration (.env credentials for ImageKit vs S3).",
    )

    share = st.button("Share", type="primary")
    if share and uploaded_file is None:
        st.warning("Pick a file first.")

    if uploaded_file and share:
        with st.spinner("Uploading..."):
            files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
            data = {"caption": caption, "storage": storage}
            response = requests.post(
                "http://localhost:8000/upload",
                files=files,
                data=data,
                headers=get_headers(),
            )

            if response.status_code == 200:
                # Cannot assign session_state.sidebar_nav after the widget is drawn;
                # apply _pending_sidebar_nav at start of authenticated block next run.
                st.session_state["_pending_sidebar_nav"] = "🏠 Feed"
                st.session_state.post_upload_flash = True
                st.rerun()
            else:
                try:
                    detail = response.json().get("detail", response.text or "unknown")
                except requests.exceptions.JSONDecodeError:
                    detail = response.text or "unknown"
                st.error(f"Upload failed: {detail}")


def encode_text_for_overlay(text):
    """Encode text for ImageKit overlay - base64 then URL encode."""
    if not text:
        return ""
    base64_text = base64.b64encode(text.encode("utf-8")).decode("utf-8")
    return urllib.parse.quote(base64_text)


def create_transformed_url(original_url, transformation_params, caption=None):
    if caption:
        encoded_caption = encode_text_for_overlay(caption)
        text_overlay = f"l-text,ie-{encoded_caption},ly-N20,lx-20,fs-100,co-white,bg-000000A0,l-end"
        transformation_params = text_overlay

    if not transformation_params:
        return original_url

    parts = original_url.split("/")
    file_path = "/".join(parts[4:])
    base_url = "/".join(parts[:4])
    return f"{base_url}/tr:{transformation_params}/{file_path}"


def feed_page():
    st.title("🏠 Feed")

    if st.session_state.pop("post_deleted_flash", False):
        st.toast("Post deleted.", icon="🗑️")

    if msg := st.session_state.pop("post_delete_failed_message", None):
        st.toast(f"Delete failed: {msg}", icon="❌")

    response = requests.get("http://localhost:8000/posts", headers=get_headers())
    if response.status_code == 200:
        posts = response.json()["posts"]

        if not posts:
            st.info("No posts yet! Be the first to share something.")
            return

        for post in posts:
            st.markdown("---")

            ts = format_created_display_utc_plus_5(post["created_at"])
            where = storage_label(post.get("storage"))
            col1, col2 = st.columns([4, 1])
            with col1:
                st.markdown(f"**{post['email']}** • `{ts}` • **Storage:** {where}")
            with col2:
                if post.get("is_owner", False):
                    if st.button("🗑️", key=f"delete_{post['id']}", help="Delete post"):
                        del_resp = requests.delete(
                            f"http://localhost:8000/posts/{post['id']}",
                            headers=get_headers(),
                        )
                        if del_resp.status_code == 200:
                            st.session_state.post_deleted_flash = True
                            st.rerun()
                        else:
                            try:
                                detail = del_resp.json().get("detail", del_resp.text or "Unknown error")
                            except requests.exceptions.JSONDecodeError:
                                detail = del_resp.text or "Unknown error"
                            st.session_state.post_delete_failed_message = str(detail)
                            st.rerun()

            caption = post.get("caption", "")
            use_transforms = post.get("storage") == "imagekit"
            ft = post["file_type"]

            if ft == "image":
                img_url = create_transformed_url(post["url"], "", caption) if use_transforms else post["url"]
                st.image(img_url, width=300)
                if not use_transforms and caption:
                    st.caption(caption)
            elif ft == "video":
                if use_transforms:
                    uniform_video_url = create_transformed_url(post["url"], "w-400,h-200,cm-pad_resize,bg-blurred")
                    st.video(uniform_video_url, width=300)
                else:
                    st.video(post["url"], width=300)
                if caption:
                    st.caption(caption)
            else:
                st.markdown(f"[⬇ Download / open attachment]({post['url']}) — `{post.get('file_name', 'file')}`")
                if caption:
                    st.caption(caption)

            st.markdown("")
    else:
        st.error("Failed to load feed")


# Main app
if st.session_state.user is None:
    login_page()
else:
    if st.session_state.pop("post_upload_flash", False):
        st.toast(
            "Posted! Switched to Feed. Large files may take a moment to load.",
            icon="✅",
        )

    if pn := st.session_state.pop("_pending_sidebar_nav", None):
        st.session_state.sidebar_nav = pn

    st.sidebar.title(f"👋 Hi {st.session_state.user['email']}!")

    if st.sidebar.button("Logout"):
        st.session_state.user = None
        st.session_state.token = None
        st.session_state.sidebar_nav = "🏠 Feed"
        st.rerun()

    st.sidebar.markdown("---")
    if "sidebar_nav" not in st.session_state:
        st.session_state.sidebar_nav = "🏠 Feed"
    page = st.sidebar.radio(
        "Navigate:",
        ["🏠 Feed", "📸 Upload"],
        key="sidebar_nav",
    )

    if page == "🏠 Feed":
        feed_page()
    else:
        upload_page()
