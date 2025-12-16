# apps/chat/services/ai_service.py
import logging

from typing import Optional, List, Dict, Any
from openai import AsyncOpenAI
from channels.db import database_sync_to_async

from django.utils import timezone
from django.contrib.auth import get_user_model

from apps.ai_chat.models import AISession, AIMessage, ChatAIConfig, AIMessageTypeEnum
from apps.ai_chat.services.chat_service import ChatService
from apps.ai_chat.services.transaction_tracking import AITransactionTracker
from base_utils.services import AbstractBaseService

User = get_user_model()
logger = logging.getLogger(__name__)


class ChatBackendAIService(AbstractBaseService):
    """
    Service for interacting with Deepseek Chat API
    """

    @staticmethod
    def format_messages(messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Format messages to ensure they're in the correct format for Deepseek API.
        For Deepseek Reasoner model:
        1. The first message after any system messages MUST be a user message
        2. The last message MUST be a user message
        """
        if not messages:
            return []

        formatted_messages = []

        # Extract system messages and other messages
        system_messages = [msg for msg in messages if msg.get("role") == "system" and msg.get("content")]
        user_messages = [msg for msg in messages if msg.get("role") == "user" and msg.get("content")]
        assistant_messages = [msg for msg in messages if msg.get("role") == "assistant" and msg.get("content")]

        # Add system messages first
        formatted_messages.extend(system_messages)

        # If no user messages, we have a problem
        if not user_messages:
            logger.warning("No user messages found in ctainoersation - this will cause an error")
            return formatted_messages

        # Ensure we have at least one user message
        last_user_message = user_messages[-1]

        # If we only have one user message, it's simple
        if len(user_messages) == 1:
            formatted_messages.append(user_messages[0])
            return formatted_messages

        # Start with a user message after system messages
        formatted_messages.append(user_messages[0])

        # Now build the ctainoersation with alternating messages
        # For each assistant message, add it followed by a user message
        for i in range(min(len(assistant_messages), len(user_messages) - 1)):
            # Add assistant response
            formatted_messages.append(assistant_messages[i])
            # Add next user message (but not the last one yet)
            if i < len(user_messages) - 2:
                formatted_messages.append(user_messages[i + 1])

        # Always ensure the last message is from a user
        # Add the last user message
        formatted_messages.append(last_user_message)

        # Log the message sequence
        roles = [msg["role"] for msg in formatted_messages]
        logger.info(f"Final message sequence: {roles}")

        # Verification: First non-system must be user & last message must be user
        non_system_messages = [msg for msg in formatted_messages if msg["role"] != "system"]

        if not non_system_messages:
            logger.warning("No non-system messages found")
            if user_messages:
                formatted_messages.append(user_messages[0])
        else:
            # Verify first non-system is user
            if non_system_messages[0]["role"] != "user":
                logger.warning("First non-system message is not from user, fixing...")
                # Find the system messages
                sys_msgs = [msg for msg in formatted_messages if msg["role"] == "system"]
                # Start with user message
                formatted_messages = sys_msgs + [user_messages[0]] + non_system_messages[1:]

            # Verify last message is user
            if formatted_messages[-1]["role"] != "user":
                logger.warning("Last message is not from user, fixing...")
                formatted_messages.append(last_user_message)

        return formatted_messages

    @staticmethod
    @database_sync_to_async
    def get_default_ai_config() -> Optional[ChatAIConfig]:
        return ChatAIConfig.objects.filter(is_active=True, is_default=True).first()

    @staticmethod
    @database_sync_to_async
    def check_session_readonly(ai_session):
        """Check if session is readonly - wrapped for async"""
        return ai_session.check_and_update_readonly()

    @staticmethod
    @database_sync_to_async
    def get_ai_config_data(ai_session):
        """Get AI config data safely for async context"""
        if not ai_session.ai_config:
            return None

        # Access all needed attributes in sync context
        return {
            "pid": ai_session.ai_config.pid,
            "static_name": ai_session.ai_config.static_name,
            "name": ai_session.ai_config.name,
            "model_name": ai_session.ai_config.model_name,
            "api_key": ai_session.ai_config.api_key,
            "base_url": ai_session.ai_config.base_url,
            "default_temperature": ai_session.ai_config.default_temperature,
            "default_max_tokens": ai_session.ai_config.default_max_tokens,
            "combined_system_prompt": ai_session.ai_config.get_combined_system_prompt(),
        }

    @staticmethod
    @database_sync_to_async
    def get_session_parameters(ai_session):
        """Get session-specific parameters"""
        return {
            "temperature": ai_session.temperature,
            "max_tokens": ai_session.max_tokens,
            "ai_context": ai_session.ai_context,
        }

    @staticmethod
    @database_sync_to_async
    def update_ai_session_context(ai_session, usage):
        if not ai_session.ai_context:
            ai_session.ai_context = {}
        ai_session.ai_context["last_interaction"] = timezone.now().isoformat()
        ai_session.ai_context["usage"] = usage
        ai_session.save(update_fields=["ai_context"])

    @staticmethod
    @database_sync_to_async
    def get_previous_messages(ai_session: AISession, user_message: AIMessage) -> list:
        """
        Get previous messages with sender info, safely for async context.
        """
        # Get at most the last 10 messages in chronological order (oldest first)
        messages = (
            AIMessage.objects.filter(ai_session=ai_session, created_at__lt=user_message.created_at)
            .select_related("sender")  # avoids lazy loading
            .order_by("-created_at")[:10]  # Get last 10 messages in reverse order
        )

        # Ctainoert to list and reverse to get chronological order
        message_list = list(reversed(messages))

        result = []
        for msg in message_list:
            # Determine message role based on sender
            if msg.is_ai:
                role = "assistant"
            elif msg.is_system:
                role = "system"
            else:
                role = "user"

            result.append({"role": role, "content": msg.content})

        # Add the current user message
        result.append({"role": "user", "content": user_message.content})

        # Log the message structure
        logger.info(f"Message sequence before formatting: {[msg['role'] for msg in result]}")

        return result

    @staticmethod
    @database_sync_to_async
    def get_ai_config_from_session(ai_session: AISession) -> Optional[ChatAIConfig]:
        """
        Get the appropriate AI config based on chat session context
        """
        if ai_session.ai_context and "chat_type" in ai_session.ai_context:
            chat_type = ai_session.ai_context.get("chat_type")
            # Try to get config by static_name
            config = ChatAIConfig.objects.filter(static_name=chat_type, is_active=True).first()
            if config:
                return config

        # Fallback to default config
        return ChatAIConfig.objects.filter(is_active=True, is_default=True).first()

    @staticmethod
    @database_sync_to_async
    def create_ai_message(ai_session, content, message_type=AIMessageTypeEnum.TEXT, is_ai=True, is_system=False):
        """Create AI message in database"""
        return AIMessage.objects.create(
            ai_session=ai_session,
            sender=ai_session.user,
            content=content,
            message_type=message_type,
            is_ai=is_ai,
            is_system=is_system,
        )

    @staticmethod
    @database_sync_to_async
    def add_token_usage_to_session(ai_session, prompt_tokens, completion_tokens):
        """Add token usage to session"""
        ai_session.add_token_usage(prompt_tokens, completion_tokens)

    @staticmethod
    @database_sync_to_async
    def charge_for_tokens(ai_session, input_tokens, output_tokens):
        """Charge user for token usage"""
        ChatBackendAIService._charge_for_tokens_v2(ai_session, input_tokens, output_tokens)

    @staticmethod
    async def generate_response(
        ai_session: AISession,
        user_message: AIMessage,
    ) -> Optional[AIMessage]:
        """Generate AI response using OpenAI-compatible API with both pricing types"""

        # Check if session is readonly
        is_readonly, reason = await ChatBackendAIService.check_session_readonly(ai_session)
        if is_readonly:
            error_msg = f"این چت به حداکثر محدودیت خود رسیده است: {reason}"
            return await ChatBackendAIService.create_ai_message(
                ai_session=ai_session,
                content=error_msg,
                message_type=AIMessageTypeEnum.TEXT,
                is_ai=True,
                is_system=True,
            )

        # Get AI config data
        ai_config_data = await ChatBackendAIService.get_ai_config_data(ai_session)
        if not ai_config_data:
            logger.error("No AI configuration found for session")
            return None

        try:
            # PRE-CHARGE VALIDATION
            is_valid, error_msg = await database_sync_to_async(AITransactionTracker.pre_charge_validation)(
                ai_session, str(user_message.pid)
            )

            if not is_valid:
                logger.error(f"Pre-charge validation failed: {error_msg}")
                return await ChatBackendAIService.create_ai_message(
                    ai_session=ai_session,
                    content=f"خطا: {error_msg}",
                    message_type=AIMessageTypeEnum.TEXT,
                    is_ai=True,
                    is_system=True,
                )

            # Get ctainoersation history
            previous_messages = await ChatBackendAIService.get_previous_messages(ai_session, user_message)

            # Get combined system prompt
            combined_prompt = ai_config_data["combined_system_prompt"]

            # Format messages
            formatted_messages = [{"role": "system", "content": combined_prompt}]
            formatted_messages.extend(previous_messages)
            formatted_messages = ChatBackendAIService.format_messages(formatted_messages)

            # Get session parameters
            session_params = await ChatBackendAIService.get_session_parameters(ai_session)
            temperature = session_params["temperature"] or ai_config_data["default_temperature"]
            max_tokens = session_params["max_tokens"] or ai_config_data["default_max_tokens"]

            # Set up client
            client = AsyncOpenAI(
                api_key=ai_config_data["api_key"],
                base_url=ai_config_data["base_url"] or "https://api.deepseek.com/v1",
            )

            # Call API
            response = await client.chat.completions.create(
                model=ai_config_data["model_name"],
                messages=formatted_messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )

            # Extract response and usage
            ai_response = response.choices[0].message.content.strip()
            usage = response.usage

            # Create AI message FIRST (so we have the message PID)
            ai_message = await ChatBackendAIService.create_ai_message(
                ai_session=ai_session,
                content=ai_response,
                message_type=AIMessageTypeEnum.TEXT,
                is_ai=True,
            )

            # Update token usage (for tracking, even in message-based pricing)
            await ChatBackendAIService.add_token_usage_to_session(ai_session, usage.prompt_tokens, usage.completion_tokens)

            # CHARGE USER WITH TRANSACTION TRACKING
            if ai_session.ai_config.is_message_based_pricing():
                # Message-based: charge fixed amount
                cost = float(ai_session.ai_config.cost_per_message)

                transaction_info = await database_sync_to_async(AITransactionTracker.record_message_charge)(
                    ai_session=ai_session,
                    message_pid=str(ai_message.pid),
                    cost=cost,
                )

                if not transaction_info["success"]:
                    logger.error(f"Message charge failed: {transaction_info.get('error')}")
                    # Optionally: mark message as failed or add system message

            else:
                # Token-based: charge based on usage
                cost_info = ai_session.ai_config.calculate_token_cost(usage.prompt_tokens, usage.completion_tokens)

                transaction_info = await database_sync_to_async(AITransactionTracker.record_token_charge)(
                    ai_session=ai_session,
                    message_pid=str(ai_message.pid),
                    input_tokens=usage.prompt_tokens,
                    output_tokens=usage.completion_tokens,
                    cost=cost_info["total_cost"],
                )

                if not transaction_info["success"]:
                    logger.error(f"Token charge failed: {transaction_info.get('error')}")

            return ai_message

        except Exception as e:
            logger.error(f"AI API error: {str(e)}", exc_info=True)
            return await ChatBackendAIService.create_ai_message(
                ai_session=ai_session,
                content="متاسفانه، به مشکلی برخوردیم. لطفا دوباره تلاش کنید!",
                message_type=AIMessageTypeEnum.TEXT,
                is_ai=True,
                is_system=True,
            )

    @staticmethod
    @database_sync_to_async
    def charge_for_message(ai_session, message_pid):
        """
        Charge user for a single message (message-based pricing)

        Args:
            ai_session: The AI session
            message_pid: The PID of the message being charged for (for unique reference)
        """
        if not ai_session.ai_config or not ai_session.ai_config.is_message_based_pricing():
            return

        from apps.wallet.services.wallet import WalletService

        try:
            cost_info = ai_session.ai_config.calculate_message_cost()
            cost = cost_info["cost"]

            if cost > 0:
                # Use unique reference ID for each message
                WalletService.use_coins(
                    user=ai_session.user,
                    coin_amount=cost,
                    description=f"استفاده از {ai_session.ai_config.name} (پیام)",
                    # CRITICAL: Use session + message for unique reference
                    reference_id=f"ai_msg_{ai_session.pid}_{message_pid}",
                )

                logger.info(
                    f"Charged {cost} coins for message {message_pid} " f"in session {ai_session.pid} (message-based pricing)"
                )

        except Exception as e:
            logger.error(f"Error charging for message: {e}")

    @staticmethod
    def _charge_for_message_or_tokens(ai_session, input_tokens=0, output_tokens=0, message_pid=None):
        """
        Charge user based on the pricing type of the AI config

        Args:
            ai_session: The AI session
            input_tokens: Number of input tokens (for token-based)
            output_tokens: Number of output tokens (for token-based)
            message_pid: The PID of the message (for message-based unique reference)
        """
        if not ai_session.ai_config:
            return

        from apps.wallet.services.wallet import WalletService

        try:
            # Check pricing type
            if ai_session.ai_config.is_message_based_pricing():
                # Message-based pricing - charge fixed amount per message
                cost_info = ai_session.ai_config.calculate_message_cost()
                cost = cost_info["cost"]

                if cost > 0:
                    # Check balance
                    coin_balance = WalletService.get_wallet_coin_balance(ai_session.user)
                    if coin_balance < cost:
                        logger.error(f"Insufficient balance for message-based pricing: {cost} coins required")
                        return

                    # Charge the fixed message cost with unique reference
                    reference_id = f"ai_msg_{ai_session.pid}"
                    if message_pid:
                        reference_id = f"{reference_id}_{message_pid}"

                    WalletService.use_coins(
                        user=ai_session.user,
                        coin_amount=cost,
                        description=f"استفاده از {ai_session.ai_config.name} (پیام)",
                        reference_id=reference_id,
                    )

                    logger.info(
                        f"Charged {cost} coins for message-based pricing "
                        f"(session: {ai_session.pid}, message: {message_pid})"
                    )

            elif ai_session.ai_config.is_token_based_pricing():
                # Token-based pricing - use the existing token-based charging
                from apps.ai_chat.services.ai_pricing_calculator import AIPricingCalculator

                success, message, details = AIPricingCalculator.charge_for_usage(
                    user=ai_session.user,
                    ai_config_static_name=ai_session.ai_config.static_name,
                    actual_input_tokens=input_tokens,
                    actual_output_tokens=output_tokens,
                    description=f"استفاده از {ai_session.ai_config.name}",
                )

                if not success:
                    logger.error(f"Failed to charge for tokens: {message}")
                else:
                    logger.info(
                        f"Successfully charged: {details.get('charged_amount', 0)} coins for "
                        f"{input_tokens + output_tokens} tokens. Free: {details.get('is_free', False)}"
                    )

        except Exception as e:
            logger.error(f"Error charging for AI usage: {e}")

    @staticmethod
    def _charge_for_tokens_v2(ai_session, input_tokens, output_tokens):
        """
        Charge user for token usage using the new AI pricing calculator
        """
        if not ai_session.ai_config:
            return

        from apps.ai_chat.services.ai_pricing_calculator import AIPricingCalculator

        try:
            # Use the AI config's static_name for charging
            success, message, details = AIPricingCalculator.charge_for_usage(
                user=ai_session.user,
                ai_config_static_name=ai_session.ai_config.static_name,
                actual_input_tokens=input_tokens,
                actual_output_tokens=output_tokens,
                description=f"استفاده از {ai_session.ai_config.name}",
            )

            if not success:
                logger.error(f"Failed to charge for tokens: {message}")
            else:
                logger.info(
                    f"Successfully charged: {details.get('charged_amount', 0)} coins for "
                    f"{input_tokens + output_tokens} tokens. Free: {details.get('is_free', False)}"
                )

        except Exception as e:
            logger.error(f"Error charging for tokens: {e}")

    @staticmethod
    def _charge_for_tokens(ai_session, input_tokens, output_tokens):
        """Charge user for token usage using the pricing service"""
        if not ai_session.ai_config:
            return

        # from apps.pricing.services.pricing_service import PricingService

        # Determine feature from ai_config
        general_config = ai_session.ai_config.general_config
        feature = general_config.static_name if general_config else "general_chat"

        # Get strength
        strength = ai_session.ai_config.strength

        try:
            # Calculate and charge using pricing service
            # success, message, details = PricingService.charge_user_for_tokens(
            #     user=ai_session.user,
            #     feature=feature,
            #     input_tokens=input_tokens,
            #     output_tokens=output_tokens,
            #     strength=strength,
            #     description=f"استفاده از {ai_session.ai_config.name}",
            # )

            message = f"استفاده از {ai_session.ai_config.name}"

            details = dict(user=ai_session.user, feature=feature, input_tokens=input_tokens, output_tokens=output_tokens)

            success = True

            if not success:
                logger.error(f"Failed to charge for tokens: {message}")
            else:
                logger.info(
                    f"Successfully charged {details.get('final_cost')} coins for {input_tokens + output_tokens} tokens"
                )

        except Exception as e:
            logger.error(f"Error charging for tokens: {e}")

    @staticmethod
    def calculate_ai_chat_cost(ai_session: AISession) -> float:
        """
        Calculate the cost of an AI chat session
        """
        if not ai_session.ai_context or not ai_session.ai_context.get("usage"):
            return 0.0

        # Get default AI config for pricing
        ai_config = ChatAIConfig.objects.filter(is_active=True, is_default=True).first()
        if not ai_config:
            return 0.0

        usage = ai_session.ai_context.get("usage", {})

        prompt_tokens = usage.get("prompt_tokens", 0)
        completion_tokens = usage.get("completion_tokens", 0)

        # Calculate cost
        # prompt_cost = (prompt_tokens / 1000) * float(ai_config.cost)
        prompt_cost = 10  # just for test
        completion_cost = 11  # just for test
        # completion_cost = (completion_tokens / 1000) * float(ai_config.cost_per_1k_tokens_output)

        total_cost = prompt_cost + completion_cost

        return total_cost

    @staticmethod
    def get_default_ai_config_sync():
        """
        Get default AI config synchronously (for celery tasks)
        """
        return ChatAIConfig.objects.filter(is_active=True, is_default=True).first()

    @staticmethod
    def generate_direct_response(prompt, ai_config):
        """
        Generate AI response directly using the OpenAI client
        This is a synchronous version for use in Celery tasks
        """
        try:
            from openai import OpenAI

            # Format the message for Deepseek API
            messages = [{"role": "system", "content": ai_config.system_prompt}, {"role": "user", "content": prompt}]

            # Set up client with API key and base URL
            base_url = ai_config.base_url or "https://api.deepseek.com/v1"

            client = OpenAI(
                api_key=ai_config.api_key,
                base_url=base_url,
            )

            # Call API
            response = client.chat.completions.create(
                model=ai_config.model_name,
                messages=messages,
                temperature=ai_config.temperature,
                max_tokens=ai_config.max_tokens,
            )

            # Extract the response text
            ai_response = response.choices[0].message.content.strip()

            return ai_response

        except Exception as e:
            logger.error(f"AI API direct response error: {str(e)}", exc_info=True)
            return None
