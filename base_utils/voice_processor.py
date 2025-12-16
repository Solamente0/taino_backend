# apps/ai_chat/utils/voice_processor.py
import logging
from mutagen import File as MutagenFile
from mutagen.mp3 import MP3
from mutagen.mp4 import MP4
from mutagen.oggvorbis import OggVorbis
from mutagen.wave import WAVE
import tempfile
import os

logger = logging.getLogger(__name__)


class VoiceProcessor:
    """Utility class for processing voice files"""
    
    SUPPORTED_FORMATS = {
        'audio/mpeg': MP3,
        'audio/mp3': MP3,
        'audio/mp4': MP4,
        'audio/m4a': MP4,
        'audio/ogg': OggVorbis,
        'audio/webm': None,  # WebM requires special handling
        'audio/wav': WAVE,
        'audio/wave': WAVE,
    }
    
    @staticmethod
    def get_audio_duration(file_obj, content_type: str) -> int:
        """
        Extract audio duration from uploaded file
        
        Args:
            file_obj: Django UploadedFile object
            content_type: MIME type of the file
            
        Returns:
            Duration in seconds (rounded up)
        """
        try:
            # Create a temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix=VoiceProcessor._get_extension(content_type)) as tmp_file:
                # Write uploaded file to temp file
                for chunk in file_obj.chunks():
                    tmp_file.write(chunk)
                tmp_file_path = tmp_file.name
            
            try:
                # Reset file pointer for later use
                file_obj.seek(0)
                
                # Try to get duration based on content type
                duration = VoiceProcessor._extract_duration(tmp_file_path, content_type)
                
                if duration is None:
                    logger.warning(f"Could not extract duration from {content_type}, defaulting to 0")
                    return 0
                
                # Round up to nearest second
                import math
                duration_seconds = math.ceil(duration)
                
                logger.info(f"✅ Extracted audio duration: {duration_seconds} seconds from {content_type}")
                return duration_seconds
                
            finally:
                # Clean up temp file
                if os.path.exists(tmp_file_path):
                    os.unlink(tmp_file_path)
                    
        except Exception as e:
            logger.error(f"Error extracting audio duration: {e}", exc_info=True)
            # Return 0 instead of failing - we'll use frontend value as fallback
            return 0
    
    @staticmethod
    def _extract_duration(file_path: str, content_type: str) -> float:
        """Extract duration using mutagen"""
        try:
            # First try with generic mutagen File
            audio = MutagenFile(file_path)
            
            if audio and hasattr(audio.info, 'length'):
                return audio.info.length
            
            # If that fails, try specific format
            if content_type in VoiceProcessor.SUPPORTED_FORMATS:
                format_class = VoiceProcessor.SUPPORTED_FORMATS[content_type]
                if format_class:
                    audio = format_class(file_path)
                    if audio and hasattr(audio.info, 'length'):
                        return audio.info.length
            
            # Special handling for WebM (uses generic approach)
            if 'webm' in content_type:
                audio = MutagenFile(file_path)
                if audio and hasattr(audio.info, 'length'):
                    return audio.info.length
            
            return None
            
        except Exception as e:
            logger.error(f"Mutagen extraction failed: {e}")
            return None
    
    @staticmethod
    def _get_extension(content_type: str) -> str:
        """Get file extension from content type"""
        extensions = {
            'audio/mpeg': '.mp3',
            'audio/mp3': '.mp3',
            'audio/mp4': '.m4a',
            'audio/m4a': '.m4a',
            'audio/ogg': '.ogg',
            'audio/webm': '.webm',
            'audio/wav': '.wav',
            'audio/wave': '.wav',
        }
        return extensions.get(content_type, '.tmp')
    
    @staticmethod
    def validate_voice_file(file_obj, max_duration_seconds: int = None) -> tuple[bool, str, int]:
        """
        Validate voice file and return duration
        
        Args:
            file_obj: Uploaded file
            max_duration_seconds: Maximum allowed duration
            
        Returns:
            (is_valid, error_message, duration_seconds)
        """
        # Check file size (50MB max)
        max_size = 50 * 1024 * 1024  # 50MB
        if file_obj.size > max_size:
            return False, f"فایل صوتی بیش از حد بزرگ است. حداکثر: {max_size // (1024*1024)}MB", 0
        
        # Check content type
        content_type = file_obj.content_type
        if not content_type or not content_type.startswith('audio/'):
            return False, "فرمت فایل صوتی معتبر نیست", 0
        
        # Extract duration
        duration = VoiceProcessor.get_audio_duration(file_obj, content_type)
        
        # Validate duration against max
        if max_duration_seconds and duration > max_duration_seconds:
            return False, f"مدت زمان صدا بیش از حد مجاز است. حداکثر: {max_duration_seconds} ثانیه", duration
        
        return True, "", duration
