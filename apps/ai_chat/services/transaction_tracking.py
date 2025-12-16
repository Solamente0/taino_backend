# apps/ai_chat/services/transaction_tracking.py
"""
Service for tracking AI usage transactions
This ensures every message or token usage is properly recorded
"""
import logging
from decimal import Decimal
from typing import Dict, Optional
from django.db import transaction
from django.contrib.auth import get_user_model

logger = logging.getLogger(__name__)
User = get_user_model()


class AITransactionTracker:
    """Track and record AI usage transactions"""

    @staticmethod
    @transaction.atomic
    def record_message_charge(
        ai_session, message_pid: str, cost: float, success: bool = True, error_message: Optional[str] = None
    ) -> Dict:
        """
        Record a message-based charge transaction

        Args:
            ai_session: The AI session
            message_pid: The PID of the message
            cost: The cost charged
            success: Whether the charge was successful
            error_message: Error message if charge failed

        Returns:
            dict with transaction details
        """
        from apps.wallet.services.wallet import WalletService

        transaction_info = {
            "session_pid": str(ai_session.pid),
            "message_pid": message_pid,
            "pricing_type": "message_based",
            "cost": cost,
            "success": success,
            "timestamp": None,
        }

        if not success:
            transaction_info["error"] = error_message
            logger.error(f"Failed to charge for message {message_pid} " f"in session {ai_session.pid}: {error_message}")
            return transaction_info

        try:
            # Create unique reference ID
            reference_id = f"ai_msg_{ai_session.pid}_{message_pid}"

            # Check balance first
            balance = WalletService.get_wallet_coin_balance(ai_session.user)
            if balance < cost:
                transaction_info["success"] = False
                transaction_info["error"] = "Insufficient balance"
                logger.error(f"Insufficient balance for message {message_pid}: " f"required {cost}, available {balance}")
                return transaction_info

            # Perform the charge
            WalletService.use_coins(
                user=ai_session.user,
                coin_amount=cost,
                description=f"پیام {ai_session.ai_config.name}",
                reference_id=reference_id,
            )

            # Update session cost
            ai_session.add_message_based_cost(cost)

            transaction_info["reference_id"] = reference_id
            transaction_info["timestamp"] = str(ai_session.updated_at)

            logger.info(f"Successfully charged {cost} coins for message {message_pid} " f"in session {ai_session.pid}")

        except Exception as e:
            transaction_info["success"] = False
            transaction_info["error"] = str(e)
            logger.error(f"Error recording message charge for {message_pid}: {e}", exc_info=True)

        return transaction_info

    @staticmethod
    @transaction.atomic
    def record_token_charge(
        ai_session,
        message_pid: str,
        input_tokens: int,
        output_tokens: int,
        cost: float,
        success: bool = True,
        error_message: Optional[str] = None,
    ) -> Dict:
        """
        Record a token-based charge transaction

        Args:
            ai_session: The AI session
            message_pid: The PID of the message (for reference)
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            cost: The cost charged
            success: Whether the charge was successful
            error_message: Error message if charge failed

        Returns:
            dict with transaction details
        """
        transaction_info = {
            "session_pid": str(ai_session.pid),
            "message_pid": message_pid,
            "pricing_type": "token_based",
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": input_tokens + output_tokens,
            "cost": cost,
            "success": success,
            "timestamp": None,
        }

        if not success:
            transaction_info["error"] = error_message
            logger.error(f"Failed to charge for tokens in message {message_pid}: {error_message}")
            return transaction_info

        try:
            # Token usage is already tracked by add_token_usage
            # which also updates the cost
            transaction_info["reference_id"] = f"ai_tokens_{ai_session.pid}_{message_pid}"
            transaction_info["timestamp"] = str(ai_session.updated_at)

            logger.info(
                f"Successfully charged {cost} coins for {input_tokens + output_tokens} tokens "
                f"(message {message_pid} in session {ai_session.pid})"
            )

        except Exception as e:
            transaction_info["success"] = False
            transaction_info["error"] = str(e)
            logger.error(f"Error recording token charge for {message_pid}: {e}", exc_info=True)

        return transaction_info

    @staticmethod
    def get_session_transaction_summary(ai_session) -> Dict:
        """
        Get transaction summary for a session

        Args:
            ai_session: The AI session

        Returns:
            dict with transaction summary
        """
        return {
            "session_pid": str(ai_session.pid),
            "pricing_type": ai_session.ai_config.pricing_type if ai_session.ai_config else "unknown",
            "total_messages": ai_session.total_messages,
            "total_cost_coins": float(ai_session.total_cost_coins),
            "total_input_tokens": ai_session.total_input_tokens,
            "total_output_tokens": ai_session.total_output_tokens,
            "total_tokens_used": ai_session.total_tokens_used,
            "average_cost_per_message": (
                float(ai_session.total_cost_coins) / ai_session.total_messages if ai_session.total_messages > 0 else 0
            ),
        }

    @staticmethod
    def pre_charge_validation(ai_session, message_pid: Optional[str] = None) -> tuple[bool, str]:
        """
        Validate before charging

        Args:
            ai_session: The AI session
            message_pid: Optional message PID for logging

        Returns:
            tuple: (is_valid, error_message)
        """
        from apps.wallet.services.wallet import WalletService

        # Check if session is readonly
        if ai_session.is_readonly:
            return False, f"Session is readonly: {ai_session.readonly_reason}"

        # Check if config exists
        if not ai_session.ai_config:
            return False, "No AI config found for session"

        # Check pricing type and balance
        if ai_session.ai_config.is_message_based_pricing():
            cost = float(ai_session.ai_config.cost_per_message)
            if cost <= 0:
                return True, ""  # Free message

            balance = WalletService.get_wallet_coin_balance(ai_session.user)
            if balance < cost:
                return False, f"Insufficient balance: required {cost}, available {balance}"

        return True, ""
