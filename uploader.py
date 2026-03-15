import os
import asyncio
from pyrogram.types import InputMediaVideo


# =====================================
# EXTRAIR INFO DO VÍDEO
# =====================================

async def get_video_info(filepath):

    cmd = [
        "ffprobe",
        "-v", "error",
        "-select_streams", "v:0",
        "-show_entries",
        "stream=width,height:format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        filepath
    ]

    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )

    stdout, _ = await process.communicate()

    output = stdout.decode().split("\n")

    width = int(float(output[0])) if output[0] else 1280
    height = int(float(output[1])) if output[1] else 720
    duration = int(float(output[2])) if output[2] else 0

    return width, height, duration


# =====================================
# GERAR THUMBNAIL
# =====================================

async def generate_thumbnail(filepath):

    thumb_path = filepath + ".jpg"

    cmd = [
        "ffmpeg",
        "-ss", "00:00:03",
        "-i", filepath,
        "-frames:v", "1",
        "-q:v", "2",
        "-y",
        thumb_path
    ]

    process = await asyncio.create_subprocess_exec(*cmd)
    await process.wait()

    if os.path.exists(thumb_path):
        return thumb_path

    return None


# =====================================
# UPLOAD PROFISSIONAL
# =====================================

async def upload_video(userbot, filepath, message, storage_chat_id):

    filename = os.path.basename(filepath)

    await message.edit_text("🎞 Extraindo informações...")

    width, height, duration = await get_video_info(filepath)
    thumb = await generate_thumbnail(filepath)

    await message.edit_text("📤 Enviando vídeo...")

    sent = await userbot.send_video(
        chat_id=storage_chat_id,
        video=filepath,
        caption=filename,
        width=width,
        height=height,
        duration=duration,
        thumb=thumb,
        supports_streaming=True
    )

    # Remove thumbnail depois
    if thumb and os.path.exists(thumb):
        os.remove(thumb)

    return sent.id
