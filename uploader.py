import os
import json
import asyncio

FFPROBE = "/usr/bin/ffprobe"
FFMPEG = "/usr/bin/ffmpeg"


# =====================================================
# METADATA
# =====================================================

async def get_video_metadata(file):

    duration = 0
    width = 1280
    height = 720

    try:

        process = await asyncio.create_subprocess_exec(
            FFPROBE,
            "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            "-show_streams",
            file,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        stdout, _ = await process.communicate()

        data = json.loads(stdout.decode())

        if "format" in data:
            duration = int(float(data["format"]["duration"]))

        for stream in data.get("streams", []):

            if stream.get("codec_type") == "video":

                width = stream.get("width", width)
                height = stream.get("height", height)

                break

    except Exception as e:
        print("Metadata error:", e)

    return duration, width, height


# =====================================================
# THUMBNAIL
# =====================================================

async def generate_thumb(file):

    thumb = file + ".jpg"

    try:

        process = await asyncio.create_subprocess_exec(
            FFMPEG,
            "-ss", "00:00:03",
            "-i", file,
            "-vframes", "1",
            "-vf", "scale=320:-1",
            "-q:v", "2",
            thumb,
            "-y",
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL
        )

        await process.communicate()

        if os.path.exists(thumb):
            return thumb

    except Exception as e:
        print("Thumb error:", e)

    return None


# =====================================================
# UPLOAD VIDEO
# =====================================================

async def upload_video(userbot, filepath, message, storage_chat_id):

    if not os.path.exists(filepath):
        raise Exception("Arquivo não encontrado")

    await message.edit_text("📤 Preparando vídeo...")

    duration, width, height = await get_video_metadata(filepath)

    thumb = await generate_thumb(filepath)

    name = os.path.basename(filepath)

    caption = name.rsplit(".", 1)[0]

    sent = await userbot.send_video(

        chat_id=storage_chat_id,

        video=filepath,

        caption=f"🎬 {caption}",

        duration=duration,

        width=width,

        height=height,

        thumb=thumb,

        supports_streaming=True

    )

    if thumb and os.path.exists(thumb):
        os.remove(thumb)

    return sent.id
