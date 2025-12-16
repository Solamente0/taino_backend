# apps/ai_support/services/ai_service.py
import logging
import time
from typing import Optional, List, Dict
from openai import OpenAI

from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.ai_support.models import SupportSession, SupportMessage, SupportAIConfig
from base_utils.services import AbstractBaseService

User = get_user_model()
logger = logging.getLogger(__name__)


class OpenRouterAIService(AbstractBaseService):
    """Service for OpenRouter AI integration with database configuration"""
    
    @staticmethod
    def get_config() -> Optional[SupportAIConfig]:
        """Get active AI configuration from database"""
        config = SupportAIConfig.get_active_config()
        
        if not config:
            logger.error("No active AI configuration found in database")
            return None
        
        return config
    
    @staticmethod
    def get_client(config: SupportAIConfig) -> OpenAI:
        """Get OpenRouter client with config"""
        if not config.api_key:
            raise Exception("API key is not configured")
        
        return OpenAI(
            api_key=config.api_key,
            base_url=config.base_url
        )
    
    @staticmethod
    def get_ctainoersation_history(
        session: SupportSession,
        config: SupportAIConfig
    ) -> List[Dict]:
        """Get recent ctainoersation history based on config limit"""
        limit = config.ctainoersation_history_limit
        
        messages = SupportMessage.objects.filter(
            session=session,
            is_deleted=False
        ).order_by("-created_at")[:limit]
        
        history = []
        for msg in reversed(messages):
            role = "assistant" if msg.is_ai else "user"
            history.append({
                "role": role,
                "content": msg.content
            })
        
        return history
    
    @staticmethod
    def generate_response(
        session: SupportSession,
        user_message: str
    ) -> Optional[str]:
        """
        Generate AI response using OpenRouter with database configuration
        This is the synchronous version for Celery tasks
        """
        config = OpenRouterAIService.get_config()
        
        if not config:
            logger.error("No active configuration found")
            return "متاسفانه در حال حاضر سیستم پشتیبانی در دسترس نیست."
        
        try:
            # Update usage stats
            config.increment_usage()
            
            # Add artificial delay if configured
            if config.response_delay_seconds > 0:
                time.sleep(config.response_delay_seconds)
            
            client = OpenRouterAIService.get_client(config)
            
            # Get ctainoersation history
            history = OpenRouterAIService.get_ctainoersation_history(session, config)
            
            # Build messages
            messages = [
                {"role": "system", "content": config.system_prompt}
            ]
            messages.extend(history)
            messages.append({"role": "user", "content": user_message})
            
            # Call API with config parameters
            response = client.chat.completions.create(
                model=config.model_name,
                messages=messages,
                temperature=config.temperature,
                max_tokens=config.max_tokens
            )
            
            ai_response = response.choices[0].message.content.strip()
            
            # Update last used timestamp
            config.last_used_at = timezone.now()
            config.save(update_fields=["last_used_at"])
            
            return ai_response
            
        except Exception as e:
            logger.error(f"OpenRouter AI error: {str(e)}", exc_info=True)
            
            # Increment error counter
            config.increment_errors()
            
            # Return fallback message from config
            return config.fallback_message
    
    @staticmethod
    def test_config(config: SupportAIConfig) -> bool:
        """
        Test an AI configuration with a simple request
        Returns True if successful, False otherwise
        """
        try:
            client = OpenRouterAIService.get_client(config)
            
            # Simple test message
            test_messages = [
                {"role": "system", "content": config.system_prompt},
                {"role": "user", "content": "سلام"}
            ]
            
            response = client.chat.completions.create(
                model=config.model_name,
                messages=test_messages,
                temperature=config.temperature,
                max_tokens=50  # Short response for testing
            )
            
            # If we get here, the config works
            result = response.choices[0].message.content.strip()
            logger.info(f"Config test successful: {result[:50]}...")
            return True
            
        except Exception as e:
            logger.error(f"Config test failed: {str(e)}", exc_info=True)
            return False
