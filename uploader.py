import os
import json
import asyncio

# =====================================================
# METADATA DO VIDEO
# =====================================================

async def get_video_metadata(filepath):

    cmd = [
        "ffprobe",
        "-v", "error",
        "-print_format", "json",
        "-show_streams",
        "-show_format",
        filepath
    ]

    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )

    stdout, _ = await process.communicate()

    duration = 0
    width = 0
    height = 0

    try:

        data = json.loads(stdout.decode())

        raw_duration = data.get("format", {}).get("duration")

        if raw_duration:
            duration = int(float(raw_duration))

        for stream in data.get("streams", []):

            if stream.get("codec_type") == "video":

                width = stream.get("width") or 0
                height = stream.get("height") or 0

                break

    except:
        pass

    return duration, width, height


# =====================================================
# GERAR THUMBNAIL
# =====================================================

async def generate_thumbnail(filepath):

    thumb = filepath + ".jpg"

    cmd = [
        "ffmpeg",
        "-y",
        "-ss", "00:00:03",
        "-i", filepath,
        "-vframes", "1",
        "-vf", "scale=320:-1",
        thumb
    ]

    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.DEVNULL,
        stderr=asyncio.subprocess.DEVNULL
    )

    await process.communicate()

    if os.path.exists(thumb):
        return thumb

    return None


# =====================================================
# PROGRESSO UPLOAD
# =====================================================

async def upload_progress(current, total, message):

    percent = (current / total) * 100

    try:
        await message.edit_text(
            f"📤 Enviando vídeo...\n{percent:.0f}%"
        )
    except:
        pass


# =====================================================
# UPLOAD PRINCIPAL
# =====================================================

async def upload_video(userbot, filepath, message, storage_chat_id):

    if not os.path.exists(filepath):
        raise Exception("Arquivo não encontrado")

    await message.edit_text("📤 Preparando upload...")

    duration, width, height = await get_video_metadata(filepath)

    thumb = await generate_thumbnail(filepath)

    file_name = os.path.basename(filepath)

    # limpar nome
    if file_name.endswith(".mp4.mp4"):
        file_name = file_name.replace(".mp4.mp4", ".mp4")

    caption_name = file_name.rsplit(".", 1)[0]

    sent = await userbot.send_video(

        chat_id=storage_chat_id,

        video=filepath,

        caption=f"🎬 {caption_name}",

        file_name=file_name,

        duration=duration,

        width=width,

        height=height,

        thumb=thumb,

        supports_streaming=True,

        progress=upload_progress,

        progress_args=(message,)

    )

    if thumb and os.path.exists(thumb):
        os.remove(thumb)

    return sent.id
