from google import genai
from google.genai import types
from youtube_transcript_api import YouTubeTranscriptApi
from urllib.parse import urlparse, parse_qs
import re
from config import API_KEY, MODEL_NAME

# Create Gemini client
client = genai.Client(api_key=API_KEY)


def create_chat(temperature, top_p, top_k, max_tokens):
    """
    Create a new Gemini chat session.
    """

    config = types.GenerateContentConfig(
        temperature=temperature,
        top_p=top_p,
        top_k=top_k,
        max_output_tokens=max_tokens,
    )

    chat = client.chats.create(
        model=MODEL_NAME,
        config=config,
        history=[],
    )

    return chat

def get_video_id(url):
    if "youtu.be" in url:
        return url.split("/")[-1].split("?")[0]

    parsed = urlparse(url)
    return parse_qs(parsed.query).get("v", [None])[0]


from youtube_transcript_api import YouTubeTranscriptApi

def get_transcript(url):
    video_id = get_video_id(url)

    ytt_api = YouTubeTranscriptApi()

    transcript_list = ytt_api.list(video_id)

    transcript = next(iter(transcript_list))

    fetched = transcript.fetch()

    return " ".join(snippet.text for snippet in fetched)

def stream_response(chat, prompt, image=None, video=None):
    """
    Stream Gemini response.
    Supports:
    - Text
    - Image
    - Video
    """

    try:

        # ---------- TEXT ----------
        # ---------- TEXT ----------
        if image is None and video is None:

            youtube_pattern = r'https?://(?:www\.)?(?:youtube\.com/watch\?v=[^\s&]+|youtu\.be/[^\s?&]+)'

            match = re.search(youtube_pattern, prompt)

            if match:
                url = match.group(0)

                transcript = get_transcript(url)

                prompt = f"""
                You are an AI assistant.

                The user has provided a YouTube video. The transcript below is only your source of information.

                Follow these rules:
                - Detect the language requested by the user.
                - If the user explicitly asks for Hindi, answer in Hindi.
                - If the user explicitly asks for English, answer in English.
                - If the user explicitly asks for any other language, answer in that language.
                - If the user does not specify a language, ALWAYS answer in English.
                - Never choose the response language based on the transcript language.
                - Do not say "According to the transcript" or mention that you used a transcript unless the user asks.

                User Request:
                {prompt}

                Transcript:
                {transcript}
                """

            stream = chat.send_message_stream(prompt)

        # ---------- IMAGE ----------
        elif image is not None:

            uploaded_image = client.files.upload(file=image)

            stream = chat.send_message_stream(
                [
                    prompt,
                    uploaded_image,
                ]
            )

        # ---------- VIDEO ----------
        else:

            uploaded_video = client.files.upload(file=video)

            stream = chat.send_message_stream(
                [
                    prompt,
                    uploaded_video,
                ]
            )

        for chunk in stream:
            if chunk.text:
                yield chunk.text

    except Exception as e:
        raise RuntimeError(f"Gemini API Error: {e}")