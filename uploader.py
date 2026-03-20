import os
import json
import asyncio

FFPROBE = "/usr/bin/ffprobe"
FFMPEG = "/usr/bin/ffmpeg"

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
        
        # Se não houver saída do FFPROBE, retorna os padrões
        if not stdout:
            return duration, width, height

        data = json.loads(stdout.decode())

        # Captura a duração de forma mais segura para evitar KeyError
        if "format" in data and "duration" in data["format"]:
            duration = int(float(data["format"]["duration"]))

        # Captura largura e altura garantindo que sejam números inteiros
        for stream in data.get("streams", []):
            if stream.get("codec_type") == "video":
                width = int(stream.get("width", width))
                height = int(stream.get("height", height))
                break

    except Exception as e:
        print("Erro ao obter metadados:", e)

    return duration, width, height


async def generate_thumb(file, duration):
    thumb = file + ".jpg"

    # Se o vídeo for menor que 3 segundos, pega o frame do segundo 1 (ou 0 se for muito curto)
    ss_time = "00:00:01" if duration > 1 else "00:00:00"

    try:
        process = await asyncio.create_subprocess_exec(
            FFMPEG,
            "-ss", ss_time,
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

        # Verifica se o arquivo existe E se não está vazio (tamanho > 0)
        if os.path.exists(thumb) and os.path.getsize(thumb) > 0:
            return thumb

    except Exception as e:
        print("Erro ao gerar thumbnail:", e)

    return None


async def upload_video(userbot, filepath, message, storage_chat_id):
    if not os.path.exists(filepath):
        raise Exception("Arquivo não encontrado")

    await message.edit_text("📤 Preparando vídeo...")

    # Extrai os metadados primeiro
    duration, width, height = await get_video_metadata(filepath)
    
    # Passa a duração para gerar a thumbnail de forma inteligente
    thumb = await generate_thumb(filepath, duration)

    name = os.path.basename(filepath)
    caption = name.rsplit(".", 1)[0]

    try:
        # IMPORTANTE: Se você estiver usando uma versão recente da biblioteca (Pyrogram v2+), 
        # o parâmetro 'thumb' pode precisar ser trocado por 'thumbnail'
        # ou passá-lo como um arquivo aberto, mas normalmente o caminho em string funciona.
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
        return sent.id
        
    finally:
        # O bloco 'finally' garante que a capa seja apagada da sua máquina
        # mesmo se o upload dar erro (ex: flood wait do Telegram)
        if thumb and os.path.exists(thumb):
            os.remove(thumb)
