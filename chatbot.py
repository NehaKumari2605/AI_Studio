import streamlit as st
import os
import re
import time
from urllib.parse import urlparse, parse_qs
import requests
from google import genai
from google.genai import types
from youtube_transcript_api import YouTubeTranscriptApi
from openpyxl import load_workbook

from config import API_KEY

client = genai.Client(api_key=API_KEY)

MODEL_MAP = {
    "Gemini 3.1 Flash Lite": "gemini-3.1-flash-lite",
    "Gemini 2.5 Pro": "gemini-2.5-pro",
    "Gemini 2.5 Flash Lite": "gemini-2.5-flash-lite",
    "Gemini 2.5 Flash": "gemini-2.5-flash",
}


def build_gemini_history(messages):
    if not messages:
        return []

    history = []
    last_role = None

    for msg in messages:
        role = "user" if msg["role"] == "user" else "model"
        text = msg["message"]

        # Clean tags like [IMAGE]path, [DOCUMENT]name::path, etc.
        clean_text = re.sub(r'\[(IMAGE|VIDEO|DOCUMENT)\].*?(\n|$)', '', text).strip()
        clean_text = re.sub(r'\[URL\]', '', clean_text).strip()

        if not clean_text:
            clean_text = "(attachment)"

        if role == last_role:
            if history:
                prev_text = history[-1].parts[0].text
                history[-1] = types.Content(
                    role=role,
                    parts=[types.Part.from_text(text=f"{prev_text}\n\n{clean_text}")]
                )
        else:
            history.append(
                types.Content(
                    role=role,
                    parts=[types.Part.from_text(text=clean_text)]
                )
            )
            last_role = role

    return history


def create_chat(
    model_name,
    temperature,
    top_p,
    top_k,
    max_tokens,
    web_search=False,
    messages=None,
    **kwargs,
):

    config = types.GenerateContentConfig(
        temperature=temperature,
        top_p=top_p,
        top_k=top_k,
        max_output_tokens=max_tokens,
    )

    if web_search:

        config.tools = [
            types.Tool(
                google_search=types.GoogleSearch()
            )
        ]

    history = build_gemini_history(messages) if messages else []

    return client.chats.create(
        model=MODEL_MAP[model_name],
        config=config,
        history=history,
    )

def change_chat():
    st.session_state.chat = create_chat(
        model_name=st.session_state.selected_model,
        temperature=st.session_state.temperature,
        top_p=st.session_state.top_p,
        top_k=st.session_state.top_k,
        max_tokens=st.session_state.max_tokens,
        web_search=st.session_state.web_search,
    )

    st.toast(
        f"✅ Model changed to {st.session_state.selected_model}",
        icon="🎉"
    )
# ================= URL helpers =================
YOUTUBE_PATTERN = (
    r'https?://(?:www\.|m\.)?'
    r'(?:youtube\.com/(?:watch\?v=|shorts/|embed/|live/)[^\s&?]+'
    r'|youtu\.be/[^\s?&]+)'
)
GENERIC_URL_PATTERN = r'https?://\S+'

# FIX: a naive `\S+` URL match swallows trailing punctuation the user
# typed right after the link (e.g. "check https://example.com."), so
# the request went to ".../.com." which 404s. Every URL match gets
# stripped of trailing punctuation before use.
_TRAILING_PUNCT = ").,!?]}\"'"


def _clean_url(url):
    return url.rstrip(_TRAILING_PUNCT)


def get_video_id(url):
    if "youtu.be" in url:
        return url.split("/")[-1].split("?")[0]

    parsed = urlparse(url)

    if any(seg in parsed.path for seg in ("/shorts/", "/embed/", "/live/")):
        return parsed.path.rstrip("/").split("/")[-1]

    return parse_qs(parsed.query).get("v", [None])[0]


def get_transcript(url):
    video_id = get_video_id(url)

    if not video_id:
        raise ValueError(f"Could not extract a YouTube video ID from: {url}")

    api = YouTubeTranscriptApi()

    try:
        transcript = api.fetch(video_id, languages=["hi", "en"])
    except Exception:
        transcript = api.fetch(video_id)

    return " ".join(part.text for part in transcript)


def fetch_url_content(url, max_chars=6000):
    """Fetch a page and return readable text.

    Gemini has no browser - pasting a bare URL into the prompt only lets
    it guess at the page's contents. This actually downloads the page
    and strips it down to text so the model has something real to work
    with. If the page is a JS-rendered app with no server-side text (the
    fetched body ends up too short to be useful), we say so honestly
    instead of pretending we read it.
    """
    url = _clean_url(url)

    try:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        }
        resp = requests.get(url, headers=headers, timeout=12, allow_redirects=True)
        resp.raise_for_status()

        html = resp.text
        html = re.sub(r"<script.*?</script>", " ", html, flags=re.S | re.I)
        html = re.sub(r"<style.*?</style>", " ", html, flags=re.S | re.I)
        text = re.sub(r"<[^>]+>", " ", html)
        text = re.sub(r"&nbsp;|&amp;|&quot;|&#39;", " ", text)
        text = re.sub(r"\s+", " ", text).strip()

        # A JS-only page (React/Vue shell with no server-rendered text)
        # usually leaves us with almost nothing after stripping tags -
        # be honest about that rather than feeding the model scraps.
        if len(text) < 200:
            return None

        return text[:max_chars]

    except Exception:
        return None


# ================= document reading =================
def read_document_as_text(path, max_chars=15000):
    """Extract readable text from an uploaded document.

    FIX (document not being read): Gemini's document *vision* only
    reliably/meaningfully understands PDFs - per Google's own docs,
    other formats are "technically" accepted by the Files API but not
    properly understood, and DOCX/XLS/XLSX uploads frequently fail
    outright with an "Unknown mime type" error. That's why a document
    upload often produced an answer that clearly hadn't actually read
    the file. Instead of relying on Gemini to open DOCX/XLSX/CSV/TXT
    files itself, we extract their text here in Python and hand Gemini
    the full content directly as text, so it's guaranteed to have
    actually "read" it. PDFs are still sent through Gemini's native
    file understanding, since that's the one format it handles well.
    """
    ext = os.path.splitext(path)[1].lower()

    try:
        if ext in (".txt", ".md", ".json", ".csv"):
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                text = f.read()

        elif ext == ".docx":
            from docx import Document as DocxDocument

            doc = DocxDocument(path)
            parts = [p.text for p in doc.paragraphs if p.text]

            for table in doc.tables:
                for row in table.rows:
                    parts.append(" | ".join(cell.text for cell in row.cells))

            text = "\n".join(parts)

        elif ext in (".xlsx", ".xls"):

            wb = load_workbook(path, data_only=True)
            lines = []

            for sheet in wb.worksheets:
                lines.append(f"Sheet: {sheet.title}")
                for row in sheet.iter_rows(values_only=True):
                    lines.append(
                        ", ".join("" if c is None else str(c) for c in row)
                    )

            text = "\n".join(lines)

        else:
            return None

    except Exception:
        return None

    text = text.strip()

    if not text:
        return None

    return text[:max_chars]


# ================= file upload (image / video / pdf) =================
def _upload_and_wait(file_path, mime_type=None, timeout=120):
    """Upload a file to Gemini and block until it's actually usable.

    FIX (video upload: "File is not in an ACTIVE state"): the previous
    version only kept waiting while the state was *exactly* "PROCESSING"
    (`while state == "PROCESSING"`). Right after upload the file can
    briefly be in another transient/empty state before settling into
    PROCESSING, so that loop could exit immediately - before the file
    was ACTIVE - and the very next generate call failed with exactly
    this FAILED_PRECONDITION error. The fix (matching Google's own
    example code) is to keep waiting until the state *is* "ACTIVE",
    not just until it stops being "PROCESSING".
    """
    kwargs = {"file": file_path}
    if mime_type:
        kwargs["config"] = dict(mime_type=mime_type)

    uploaded = client.files.upload(**kwargs)

    waited = 0
    state_name = getattr(uploaded.state, "name", uploaded.state)

    while not state_name or state_name != "ACTIVE":
        if state_name == "FAILED":
            raise RuntimeError("Gemini failed to process the uploaded file.")

        if waited >= timeout:
            raise RuntimeError(
                "Timed out waiting for the file to finish processing on Gemini's side."
            )

        time.sleep(2)
        waited += 2
        uploaded = client.files.get(name=uploaded.name)
        state_name = getattr(uploaded.state, "name", uploaded.state)

    return uploaded


def stream_response(
    chat,
    prompt,
    image=None,
    video=None,
    document=None,
):

    try:
        if image or video:
            uploaded = _upload_and_wait(image or video)
            stream = chat.send_message_stream([prompt, uploaded])

        elif document:
            ext = os.path.splitext(document)[1].lower()

            if ext == ".pdf":
                # PDFs are the one document format Gemini's file
                # understanding handles natively and well.
                uploaded = _upload_and_wait(document, mime_type="application/pdf")
                stream = chat.send_message_stream([prompt, uploaded])

            else:
                doc_text = read_document_as_text(document)

                if doc_text:
                    prompt = f"""
                    You are an AI assistant.

                    The following is the full text content of the document the user uploaded.

                    Document content:
                    {doc_text}

                    User Request:
                    {prompt}

                    Answer using the document content above. If the user asks for a
                    summary, cover the document fully rather than just the first part.
                    """
                else:
                    prompt += (
                        "\n\n(Note: I could not read the content of this document - "
                        "let the user know instead of guessing.)"
                    )

                stream = chat.send_message_stream(prompt)

        else:
            yt_match = re.search(YOUTUBE_PATTERN, prompt)

            if yt_match:
                transcript = get_transcript(_clean_url(yt_match.group(0)))

                prompt = f"""
                You are an AI assistant.

                The following is the transcript of the YouTube video.

                Transcript:
                {transcript}

                User Request:
                {prompt}

                Answer the user's request using only the information in the transcript.
                If the user doesn't specify a language, answer in English.
                """

            else:
                url_match = re.search(GENERIC_URL_PATTERN, prompt)

                if url_match:
                    page_text = fetch_url_content(url_match.group(0))

                    if page_text:
                        prompt = f"""
                        You are an AI assistant.

                        The following is the text content fetched from the URL the user shared.

                        Page content:
                        {page_text}

                        User Request:
                        {prompt}

                        Answer the user's request using the page content above.
                        If the content doesn't contain enough information, say so honestly
                        instead of guessing.
                        """
                    else:
                        prompt += (
                            "\n\n(Note: I could not fetch or read the content of that URL "
                            "- it may require JavaScript or block automated requests. "
                            "Tell the user this instead of guessing what the page says.)"
                        )

            stream = chat.send_message_stream(prompt)

        for chunk in stream:
            if chunk.text:
                yield chunk.text

    except Exception as e:
        raise RuntimeError(
            f"Gemini API Error: {e}"
        )


def generate_chat_title(chat, prompt):
    title_prompt = f"""
Generate a very short title (maximum 5 words) for the following conversation.

Rules:
- Return ONLY the title.
- No quotes.
- No punctuation.
- Maximum 5 words.

User Message:
{prompt}
"""

    title = ""

    for chunk in stream_response(chat, title_prompt):
        title += chunk

    return title.strip()

