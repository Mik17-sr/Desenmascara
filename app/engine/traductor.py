"""Revisión 1 · El traductor: text from screenshots (OCR) and voice notes (Whisper).

Files are checked by their real bytes, never by their name, and processed in memory: the
audio is gone as soon as it becomes text (guide section 18).
"""

import asyncio
import io
import logging
import threading

from app.core.config import settings

logger = logging.getLogger(__name__)

MAX_IMAGE_BYTES = 5 * 1024 * 1024
MAX_AUDIO_BYTES = 10 * 1024 * 1024
MAX_AUDIO_SECONDS = 180
_lock = threading.Lock()
_ocr = None
_whisper = None


class ArchivoInvalido(ValueError):
    """The upload is not an image or audio we accept; the message is safe to show to the person."""


def _image_kind(data: bytes) -> str | None:
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    if data.startswith(b"\xff\xd8\xff"):
        return "jpeg"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "webp"
    return None


def _audio_kind(data: bytes) -> str | None:
    if data.startswith(b"OggS"):
        return "ogg"
    if data[:4] == b"RIFF" and data[8:12] == b"WAVE":
        return "wav"
    if data.startswith(b"ID3") or data[:2] in (b"\xff\xfb", b"\xff\xf3", b"\xff\xf2"):
        return "mp3"
    if data[4:8] == b"ftyp":
        return "m4a"
    return None


def _get_ocr():
    global _ocr
    with _lock:
        if _ocr is None:
            from rapidocr_onnxruntime import RapidOCR

            _ocr = RapidOCR()
    return _ocr


def _get_whisper():
    global _whisper
    with _lock:
        if _whisper is None:
            from faster_whisper import WhisperModel

            _whisper = WhisperModel(settings.WHISPER_MODEL, device="cpu", compute_type="int8")
    return _whisper


def _read_image_sync(data: bytes) -> str:
    import cv2
    import numpy as np

    image = cv2.imdecode(np.frombuffer(data, dtype=np.uint8), cv2.IMREAD_COLOR)
    if image is None:
        raise ArchivoInvalido("No pude abrir la imagen. Envíala como foto (JPG o PNG).")
    result, _ = _get_ocr()(image)
    return "\n".join(line[1] for line in (result or []))


def _decode_audio(data: bytes):
    """16 kHz mono float32. Decoded here because faster-whisper's own decoder breaks on PyAV 19."""
    import av
    import numpy as np

    chunks = []
    with av.open(io.BytesIO(data)) as container:
        resampler = av.AudioResampler(format="s16", layout="mono", rate=16000)
        for frame in container.decode(audio=0):
            for out in resampler.resample(frame):
                chunks.append(out.to_ndarray().reshape(-1))
        for out in resampler.resample(None):
            chunks.append(out.to_ndarray().reshape(-1))
    if not chunks:
        raise ArchivoInvalido("La nota de voz está vacía.")
    audio = np.concatenate(chunks).astype(np.float32) / 32768.0
    if len(audio) > MAX_AUDIO_SECONDS * 16000:
        raise ArchivoInvalido("La nota de voz es muy larga. Cuéntame la llamada en menos de 3 minutos.")
    return audio


def _transcribe_sync(data: bytes) -> str:
    audio = _decode_audio(data)
    segments, _ = _get_whisper().transcribe(audio, language="es", beam_size=1, vad_filter=True)
    return " ".join(segment.text.strip() for segment in segments)


async def read_image(data: bytes) -> str:
    if len(data) > MAX_IMAGE_BYTES:
        raise ArchivoInvalido("La imagen pesa más de 5 MB.")
    if not _image_kind(data):
        raise ArchivoInvalido("Por ahora reviso capturas en JPG, PNG o WEBP.")
    return await asyncio.to_thread(_read_image_sync, data)


async def transcribe(data: bytes) -> str:
    if len(data) > MAX_AUDIO_BYTES:
        raise ArchivoInvalido("La nota de voz pesa más de 10 MB.")
    if not _audio_kind(data):
        raise ArchivoInvalido("Por ahora reviso notas de voz de Telegram o audios OGG, MP3, M4A o WAV.")
    try:
        return await asyncio.to_thread(_transcribe_sync, data)
    except ArchivoInvalido:
        raise
    except Exception as exc:
        logger.warning("Audio decoding failed: %r", exc)
        raise ArchivoInvalido("No pude escuchar la nota de voz. Intenta grabarla de nuevo.") from exc


async def warm_up_models() -> None:
    """Load OCR and Whisper in the background so the first screenshot or voice note is not slow."""
    try:
        await asyncio.to_thread(_get_ocr)
        await asyncio.to_thread(_get_whisper)
    except Exception as exc:
        logger.warning("OCR/Whisper warm-up failed: %r", exc)
