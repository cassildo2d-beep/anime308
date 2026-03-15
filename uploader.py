import os
import json
import asyncio

FFPROBE = "/usr/bin/ffprobe"
FFMPEG = "/usr/bin/ffmpeg"


async def get_video_metadata(file):

    duration = 0
    width = 0
    height = 0

    try:

        process = await asyncio.create_subprocess_exec(
            FFPROBE,
            "-v", "error",
            "-show_entries", "format=duration",
            "-show_streams",
            "-of", "json",
            file,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        stdout, _ = await process.communicate()

        data = json.loads(stdout)

        duration = int(float(data["format"]["duration"]))

        for stream in data["streams"]:

            if stream["codec_type"] == "video":

                width = stream.get("width", 0)
                height = stream.get("height", 0)

                break

    except:
        pass

    return duration, width, height


async def generate_thumb(file):

    thumb = file + ".jpg"

    try:

        process = await asyncio.create_subprocess_exec(
            FFMPEG,
            "-ss", "00:00:02",
            "-i", file,
            "-frames:v", "1",
            "-q:v", "2",
            "-vf", "scale=320:-1",
            thumb,
            "-y",
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL
        )

        await process.communicate()

        if os.path.exists(thumb):
            return thumb

    except:
        pass

    return None


async def upload_video(userbot, filepath, message, storage_chat_id):

    await message.edit_text("📤 Preparando vídeo...")

    duration, width, height = await get_video_metadata(filepath)

    thumb = await generate_thumb(filepath)

    file_name = os.path.basename(filepath)

    caption_name = file_name.rsplit(".", 1)[0]

    sent = await userbot.send_video(

        chat_id=storage_chat_id,

        video=filepath,

        duration=duration,

        width=width,

        height=height,

        thumb=thumb,

        caption=f"🎬 {caption_name}",

        supports_streaming=True

    )

    if thumb and os.path.exists(thumb):
        os.remove(thumb)

    return sent.id
