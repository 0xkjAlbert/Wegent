# SPDX-FileCopyrightText: 2025 Weibo, Inc.
#
# SPDX-License-Identifier: Apache-2.0

"""
Voice recognition endpoints using OpenAI Whisper
"""
import io
import tempfile
import os
from typing import Optional
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from pydantic import BaseModel
import whisper
from app.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()

# Global model cache
_whisper_model: Optional[whisper.Whisper] = None


class VoiceRecognitionResponse(BaseModel):
    """Response model for voice recognition"""
    text: str
    language: Optional[str] = None


def get_whisper_model() -> whisper.Whisper:
    """
    Get or load Whisper model (cached globally)

    Uses 'small' model (244MB) which balances accuracy and speed:
    - small: ~244MB, good accuracy, fast inference
    - base: ~142MB, lower accuracy
    - medium: ~769MB, better accuracy, slower
    - large: ~1550MB, best accuracy, slowest
    """
    global _whisper_model

    if _whisper_model is None:
        logger.info("Loading Whisper small model...")
        try:
            # Load model with FP16 for faster inference
            _whisper_model = whisper.load_model("small", device="cpu")
            logger.info("Whisper model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load Whisper model: {e}")
            raise HTTPException(
                status_code=500,
                detail="Failed to load voice recognition model"
            )

    return _whisper_model


@router.post("/voice/recognize", response_model=VoiceRecognitionResponse)
async def recognize_voice(
    audio_file: UploadFile = File(...),
    language: Optional[str] = None
):
    """
    Recognize speech from audio file using Whisper

    Args:
        audio_file: Audio file in WAV, MP3, M4A, or other formats supported by ffmpeg
        language: Optional language code (e.g., 'zh', 'en'). If not specified,
                  Whisper will auto-detect the language.

    Returns:
        VoiceRecognitionResponse: Recognized text and detected language

    Raises:
        HTTPException: If recognition fails
    """
    # Validate file type
    if not audio_file.content_type or not audio_file.content_type.startswith(
        ("audio/", "video/")
    ):
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Please upload an audio file."
        )

    try:
        # Read audio data
        audio_data = await audio_file.read()

        # Create temporary file for Whisper
        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=os.path.splitext(audio_file.filename or "")[1] or ".wav"
        ) as temp_file:
            temp_file.write(audio_data)
            temp_file_path = temp_file.name

        try:
            # Get Whisper model
            model = get_whisper_model()

            # Prepare transcription options
            options = {
                "fp16": False,  # Use FP32 for CPU inference
                "verbose": False,
            }

            # Add language if specified
            if language:
                # Whisper uses ISO 639-1 codes (zh, en, etc.)
                options["language"] = language

            # Transcribe audio
            logger.info(f"Transcribing audio: {temp_file_path}")
            result = model.transcribe(temp_file_path, **options)

            # Extract recognized text and language
            recognized_text = result["text"].strip()
            detected_language = result.get("language")

            if not recognized_text:
                raise HTTPException(
                    status_code=400,
                    detail="No speech detected in audio file"
                )

            logger.info(
                f"Transcription completed. "
                f"Language: {detected_language}, "
                f"Text length: {len(recognized_text)} chars"
            )

            return VoiceRecognitionResponse(
                text=recognized_text,
                language=detected_language
            )

        finally:
            # Clean up temporary file
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Voice recognition failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Voice recognition failed: {str(e)}"
        )


@router.get("/voice/health")
async def voice_health_check():
    """
    Health check endpoint for voice recognition service

    Returns status of Whisper model loading
    """
    try:
        model = get_whisper_model()
        return {
            "status": "healthy",
            "model_loaded": True,
            "model_dimensions": model.dims
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "model_loaded": False,
            "error": str(e)
        }
