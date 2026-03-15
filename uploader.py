import os
import json
import asyncio
import time 

FFPROBE = "/usr/bin/ffprobe"
FFMPEG = "/usr/bin/ffmpeg"


# =====================================================
# PEGAR METADATA DO VIDEO
# =====================================================

async def get_video_metadata(filepath):

    duration = 0
    width = 0
    height = 0

    try:

        process = await asyncio.create_subprocess_exec(
            FFPROBE,
            "-v", "error",
            "-print_format", "json",
            "-show_format",
            "-show_streams",
            filepath,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        stdout, _ = await process.communicate()

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

    try:

        process = await asyncio.create_subprocess_exec(
            FFMPEG,
            "-y",
            "-ss", "00:00:03",
            "-i", filepath,
            "-frames:v", "1",
            "-vf", "scale=320:-1",
            thumb,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL
        )

        await process.communicate()

        if os.path.exists(thumb):
            return thumb

    except:
        pass

    return None


# =====================================================
# PROGRESSO UPLOAD
# =====================================================

last_update_time = 0
last_percent = 0


async def progress(current, total, message):

    global last_update_time
    global last_percent

    percent = (current / total) * 100
    now = time.time()

    # atualizar apenas a cada 10%
    if percent - last_percent < 10:
        return

    # atualizar no máximo a cada 3 segundos
    if now - last_update_time < 3:
        return

    last_percent = percent
    last_update_time = now

    try:
        await message.edit_text(
            f"📤 Enviando vídeo...\n{percent:.1f}%"
        )
    except:
        pass


# =====================================================
# UPLOAD VIDEO
# =====================================================

async def upload_video(userbot, filepath, message, storage_chat_id):

    if not os.path.exists(filepath):
        raise Exception("Arquivo não encontrado")

    await message.edit_text("📤 Preparando vídeo...")

    duration, width, height = await get_video_metadata(filepath)

    thumb = await generate_thumbnail(filepath)

    file_name = os.path.basename(filepath)

    # corrigir nome duplicado
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

        progress=progress,

        progress_args=(message,)

    )

    # apagar thumbnail
    if thumb and os.path.exists(thumb):
        os.remove(thumb)

    return sent.id
