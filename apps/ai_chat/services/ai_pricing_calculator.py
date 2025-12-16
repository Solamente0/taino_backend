# apps/ai_chat/services/ai_pricing_calculator.py
import logging
from decimal import Decimal
from typing import Dict, Optional, Tuple
from django.contrib.auth import get_user_model

from apps.ai_chat.models import ChatAIConfig
from apps.subscription.services.subscription import SubscriptionService

User = get_user_model()
logger = logging.getLogger(__name__)


class AIPricingCalculator:
    """
    سرویس محاسبه قیمت پیشرفته برای هوش مصنوعی
    """

    @staticmethod
    def get_ai_config(static_name: str) -> Optional[ChatAIConfig]:
        """دریافت کانفیگ هوش مصنوعی"""
        print(f"Getting AI config for: {static_name}", flush=True)
        try:
            config = (
                ChatAIConfig.objects.filter(static_name=static_name, is_active=True).select_related("general_config").first()
            )
            print(f"AI config found: {config is not None}", flush=True)
            if config:
                print(
                    f"Config details - name: {config.name}, model: {config.model_name}, strength: {config.strength}",
                    flush=True,
                )
            return config
        except Exception as e:
            logger.error(f"Error getting AI config: {e}")
            print(f"Error getting AI config: {e}", flush=True)
            return None

    @staticmethod
    def calculate_voice_cost(ai_config: ChatAIConfig, duration_seconds: int) -> dict:
        """
        محاسبه هزینه فایل صوتی

        Args:
            ai_config: کانفیگ AI
            duration_seconds: مدت زمان صدا به ثانیه

        Returns:
            dict حاوی اطلاعات هزینه
        """
        print(f"🎙️ Calculating voice cost...", flush=True)

        if not ai_config.cost_per_minute:
            print("   No cost_per_minute configured, returning 0", flush=True)
            return {
                "voice_cost": 0,
                "duration_seconds": duration_seconds,
                "duration_minutes": 0,
                "billable_minutes": 0,
                "free_minutes": 0,
                "cost_per_minute": 0,
            }

        cost_per_minute = float(ai_config.cost_per_minute)
        free_minutes = ai_config.free_minutes or 0
        max_minutes = ai_config.max_minutes_per_request or float("inf")

        # Ctainoert seconds to minutes (round up)
        import math

        total_minutes = math.ceil(duration_seconds / 60)

        print(f"   Duration: {duration_seconds} seconds = {total_minutes} minutes", flush=True)

        # Check max limit
        if total_minutes > max_minutes:
            raise ValueError(f"حداکثر {max_minutes} دقیقه صدا قابل ضبط است")

        # Calculate billable minutes
        billable_minutes = max(0, total_minutes - free_minutes)
        voice_cost = billable_minutes * cost_per_minute

        print(f"💰 Voice Cost Calculation:", flush=True)
        print(f"   Total minutes: {total_minutes}", flush=True)
        print(f"   Free minutes: {free_minutes}", flush=True)
        print(f"   Billable minutes: {billable_minutes}", flush=True)
        print(f"   Cost per minute: {cost_per_minute}", flush=True)
        print(f"   Voice cost: {voice_cost}", flush=True)
        print(f"   Formula: ({total_minutes} - {free_minutes}) × {cost_per_minute} = {voice_cost}", flush=True)

        return {
            "voice_cost": math.ceil(voice_cost),
            "duration_seconds": duration_seconds,
            "duration_minutes": total_minutes,
            "billable_minutes": billable_minutes,
            "free_minutes": free_minutes,
            "cost_per_minute": cost_per_minute,
        }

    @staticmethod
    def calculate_file_cost(ai_config: ChatAIConfig, files: list) -> dict:
        """
        محاسبه هزینه فایل‌ها (تصاویر و PDF)

        Args:
            ai_config: کانفیگ AI
            files: لیست فایل‌های آپلود شده

        Returns:
            dict حاوی اطلاعات هزینه
        """
        from base_utils.file_processor import FileProcessorService

        total_pages = 0
        file_details = []

        for file in files:
            file_type = FileProcessorService.get_file_type(file)

            if file_type == "image":
                # هر تصویر = 1 صفحه
                pages = 1
                file_details.append({"name": file.name, "type": "image", "pages": pages, "size": file.size})

            elif file_type == "document":
                # شمارش صفحات PDF

                is_valid, error, pages = FileProcessorService.validate_pdf(file, max_pages=ai_config.max_pages_per_request)

                if not is_valid:
                    raise ValueError(error)

                file_details.append({"name": file.name, "type": "pdf", "pages": pages, "size": file.size})
            else:
                raise ValueError(f"فرمت فایل {file.name} پشتیبانی نمی‌شود")

            total_pages += pages

        # محاسبه هزینه کل
        cost_per_page = float(ai_config.cost_per_page)
        free_pages = ai_config.free_pages
        billable_pages = max(0, total_pages - free_pages)
        total_cost = billable_pages * cost_per_page

        print(f"📄 File cost calculation:", flush=True)
        print(f"   Total files: {len(files)}", flush=True)
        print(f"   Total pages: {total_pages}", flush=True)
        print(f"   Free pages: {free_pages}", flush=True)
        print(f"   Billable pages: {billable_pages}", flush=True)
        print(f"   Cost per page: {cost_per_page}", flush=True)
        print(f"   Total file cost: {total_cost}", flush=True)

        return {
            "total_pages": total_pages,
            "free_pages": free_pages,
            "billable_pages": billable_pages,
            "cost_per_page": cost_per_page,
            "total_file_cost": total_cost,
            "file_details": file_details,
        }

    @staticmethod
    def calculate_complete_cost(
        user,
        ai_config_static_name: str,
        character_count: int,
        files: list = None,
        max_tokens_requested: int = None,
        voice_duration_seconds: int = None,
    ) -> dict:
        """
        محاسبه کامل هزینه شامل متن و فایل‌ها

        Returns:
            dict با اطلاعات کامل هزینه
        """
        print(f"=== Complete cost calculation ===", flush=True)

        ai_config = AIPricingCalculator.get_ai_config(ai_config_static_name)
        if not ai_config:
            return {"success": False, "error": "پیکربندی هوش مصنوعی یافت نشد"}

        # محاسبه هزینه متن
        text_cost = AIPricingCalculator.calculate_with_bypass(
            user=user,
            ai_config_static_name=ai_config_static_name,
            character_count=character_count,
            max_tokens_requested=max_tokens_requested,
        )

        if not text_cost.get("success"):
            return text_cost

        # محاسبه هزینه فایل‌ها (ALWAYS calculate, regardless of pricing type)
        file_cost_info = {
            "total_file_cost": 0,
            "total_pages": 0,
            "billable_pages": 0,
            "free_pages": 0,
            "file_details": [],
            "cost_per_page": 0,
        }

        if files and len(files) > 0:
            try:
                file_cost_info = AIPricingCalculator.calculate_file_cost(ai_config, files)
                print(
                    f"✅ File cost calculated: {file_cost_info['total_file_cost']} coins for {file_cost_info['billable_pages']} billable pages",
                    flush=True,
                )
            except Exception as e:
                logger.error(f"Error calculating file cost: {e}")
                print(f"⚠️ File cost calculation failed: {e}, using 0", flush=True)
                file_cost_info = {
                    "total_file_cost": 0,
                    "total_pages": 0,
                    "billable_pages": 0,
                    "free_pages": 0,
                    "file_details": [],
                    "cost_per_page": 0,
                    "error": str(e),
                }

        # ✅ محاسبه هزینه صدا
        voice_cost_info = {
            "voice_cost": 0,
            "duration_seconds": 0,
            "duration_minutes": 0,
            "billable_minutes": 0,
            "free_minutes": 0,
            "cost_per_minute": 0,
        }

        if voice_duration_seconds and voice_duration_seconds > 0:
            try:
                voice_cost_info = AIPricingCalculator.calculate_voice_cost(ai_config, voice_duration_seconds)
                print(f"✅ Voice cost calculated: {voice_cost_info['voice_cost']} coins", flush=True)
            except Exception as e:
                logger.error(f"Error calculating voice cost: {e}")
                print(f"⚠️ Voice cost calculation failed: {e}, using 0", flush=True)
                voice_cost_info["error"] = str(e)

        # جمع کل
        text_total = text_cost.get("total_cost", 0)
        if ai_config.is_message_based_pricing():
            text_total = text_cost.get("cost", 0)
            print(f"💵 Message-based pricing: {text_total} coins", flush=True)

        file_total = file_cost_info.get("total_file_cost", 0)
        voice_total = voice_cost_info.get("voice_cost", 0)
        grand_total = text_total + file_total + voice_total

        print(f"💰 Cost breakdown:", flush=True)
        print(f"   Text cost: {text_total} coins", flush=True)
        print(f"   File cost: {file_total} coins", flush=True)
        print(f"   Voice cost: {voice_total} coins", flush=True)
        print(f"   Grand total: {grand_total} coins", flush=True)

        return {
            "success": True,
            "is_free": text_cost.get("is_free", False),
            "bypass_reason": text_cost.get("bypass_reason"),
            # هزینه متن
            "text_cost": text_total,
            "character_count": character_count,
            # هزینه فایل
            "file_cost": file_total,
            "total_pages": file_cost_info.get("total_pages", 0),
            "billable_pages": file_cost_info.get("billable_pages", 0),
            "free_pages": file_cost_info.get("free_pages", 0),
            "cost_per_page": file_cost_info.get("cost_per_page", 0),
            "file_details": file_cost_info.get("file_details", []),
            # ✅ هزینه صدا
            "voice_cost": voice_total,
            "duration_seconds": voice_cost_info.get("duration_seconds", 0),
            "duration_minutes": voice_cost_info.get("duration_minutes", 0),
            "billable_minutes": voice_cost_info.get("billable_minutes", 0),
            "free_voice_minutes": voice_cost_info.get("free_minutes", 0),
            "cost_per_minute": voice_cost_info.get("cost_per_minute", 0),
            # جمع کل
            "total_cost": grand_total,
            "ai_config": text_cost.get("ai_config"),
            "pricing_type": text_cost.get("pricing_type") or ai_config.pricing_type,
        }

    @staticmethod
    def count_characters(text: str) -> int:
        """
        شمارش دقیق کاراکترها

        Args:
            text: متن ورودی

        Returns:
            تعداد کاراکترها
        """
        if not text:
            print("Empty text provided for character counting", flush=True)
            return 0

        # حذف فضای خالی اضافی و شمارش
        # در اینجا می‌توانیم منطق دقیق‌تری اعمال کنیم
        char_count = len(text.strip())
        print(f"Character count: {char_count} for text: {text[:50]}...", flush=True)
        return char_count

    @staticmethod
    def check_bypass_conditions(user: User, ai_config: ChatAIConfig) -> Tuple[bool, Optional[str]]:
        """
        بررسی شرایط بای‌پس پرداخت

        Returns:
            Tuple of (should_bypass, reason)
        """
        print(f"=== Checking bypass conditions ===", flush=True)
        print(f"User: {user}", flush=True)
        print(f"AI Config strength: {ai_config.strength}", flush=True)

        # بررسی اشتراک پریمیوم
        print(f"AI Config strength -> {ai_config.strength}", flush=True)
        has_premium = SubscriptionService.has_premium_access(user)
        print(f"IF User has premium access -> {has_premium}", flush=True)

        if has_premium:
            # چک کنید آیا این کانفیگ برای پریمیوم رایگان است
            if ai_config.strength == "medium":
                print("Bypass granted: Premium user with medium strength config", flush=True)
                return True, "premium_subscription"
            else:
                print(f"Premium user but config strength is {ai_config.strength}, no bypass", flush=True)
        else:
            print("User does not have premium access", flush=True)

        # سایر شرایط بای‌پس
        # مثلاً: کاربران ادمین، تست‌های رایگان و ...

        print("No bypass conditions met", flush=True)
        return False, None

    @staticmethod
    def preview_cost(ai_config_static_name: str, character_count: int, max_tokens_requested: int = None) -> Dict:
        """
        پیش‌نمایش هزینه قبل از ارسال درخواست

        Args:
            ai_config_static_name: نام استاتیک کانفیگ
            character_count: تعداد کاراکترهای ورودی
            max_tokens_requested: مقدار max_tokens درخواستی (برای هیبریدی)

        Returns:
            dict با اطلاعات هزینه
        """
        print(f"=== Preview cost calculation ===", flush=True)
        print(
            f"Config: {ai_config_static_name}, Characters: {character_count}, Max tokens: {max_tokens_requested}", flush=True
        )

        ai_config = AIPricingCalculator.get_ai_config(ai_config_static_name)

        if not ai_config:
            print("AI config not found for preview", flush=True)
            return {"success": False, "error": "پیکربندی هوش مصنوعی یافت نشد"}

        # اطلاعات پایه
        result = {
            "success": True,
            "ai_config": {
                "static_name": ai_config.static_name,
                "name": ai_config.name,
                "model_name": ai_config.model_name,
                "strength": ai_config.strength,
                "pricing_type": ai_config.pricing_type,
            },
            "character_count": character_count,
        }

        # محاسبه بر اساس نوع قیمت‌گذاری
        if ai_config.is_message_based_pricing():
            print("Using message-based pricing", flush=True)
            # قیمت ثابت
            cost_info = ai_config.calculate_message_cost()
            result.update(cost_info)
            print(f"Message-based cost: {cost_info}", flush=True)

        elif ai_config.is_advanced_hybrid_pricing():
            print("Using advanced hybrid pricing", flush=True)
            # قیمت هیبریدی پیشرفته
            if max_tokens_requested is None:
                max_tokens_requested = ai_config.hybrid_tokens_min
                print(f"Using default max_tokens: {max_tokens_requested}", flush=True)

            # اعتبارسنجی max_tokens
            valid, error, corrected = ai_config.validate_max_tokens(max_tokens_requested)
            print(f"Token validation - valid: {valid}, error: {error}, corrected: {corrected}", flush=True)

            if not valid:
                result["warning"] = error
                max_tokens_requested = corrected
                print(f"Token validation failed, using corrected value: {corrected}", flush=True)

            cost_info = ai_config.calculate_advanced_hybrid_cost(
                character_count=character_count, max_tokens_requested=max_tokens_requested
            )
            result.update(cost_info)
            print(f"Hybrid cost info: {cost_info}", flush=True)

        print(f"Final preview result: {result}", flush=True)
        return result

    @staticmethod
    def calculate_with_bypass(
        user: User, ai_config_static_name: str, character_count: int, max_tokens_requested: int = None
    ) -> Dict:
        """
        محاسبه هزینه با بررسی شرایط بای‌پس

        Returns:
            dict با اطلاعات هزینه و وضعیت بای‌پس
        """
        print(f"=== Calculate with bypass ===", flush=True)
        print(
            f"User: {user}, Config: {ai_config_static_name}, Chars: {character_count}, Tokens: {max_tokens_requested}",
            flush=True,
        )

        ai_config = AIPricingCalculator.get_ai_config(ai_config_static_name)

        if not ai_config:
            print("AI config not found for bypass calculation", flush=True)
            return {"success": False, "error": "پیکربندی هوش مصنوعی یافت نشد"}

        # بررسی بای‌پس
        should_bypass, bypass_reason = AIPricingCalculator.check_bypass_conditions(user, ai_config)
        print(f"Bypass check result: should_bypass={should_bypass}, reason={bypass_reason}", flush=True)

        if should_bypass:
            print("Bypass granted, returning free result", flush=True)
            return {
                "success": True,
                "is_free": True,
                "bypass_reason": bypass_reason,
                "ai_config": {
                    "static_name": ai_config.static_name,
                    "name": ai_config.name,
                    "model_name": ai_config.model_name,
                    "strength": ai_config.strength,
                },
                "total_cost": 0,
                "message": "این سرویس برای شما رایگان است",
            }

        # محاسبه عادی
        print("No bypass, calculating normal cost", flush=True)
        preview = AIPricingCalculator.preview_cost(
            ai_config_static_name=ai_config_static_name,
            character_count=character_count,
            max_tokens_requested=max_tokens_requested,
        )

        preview["is_free"] = False
        print(f"Final calculation result: {preview}", flush=True)
        return preview

    @staticmethod
    def validate_and_charge(
        user,
        ai_config_static_name: str,
        character_count_frontend: int,
        character_count_backend: int,
        max_tokens_requested: int = None,
        description: str = None,
    ) -> Tuple[bool, str, Dict]:
        """
        اعتبارسنجی و شارژ با مدیریت خطاهای بهتر

        Returns:
            Tuple: (success, message, details)
        """
        from apps.ai_chat.services.pricing_exceptions import (
            ConfigNotFoundError,
            CharacterMismatchError,
            InsufficientBalanceError,
            InvalidTokenRangeError,
        )

        print(f"=== Validate and charge ===", flush=True)
        print(f"User: {user}, Config: {ai_config_static_name}", flush=True)
        print(f"Chars - Frontend: {character_count_frontend}, Backend: {character_count_backend}", flush=True)
        print(f"Max tokens: {max_tokens_requested}, Description: {description}", flush=True)

        try:
            # دریافت کانفیگ
            ai_config = AIPricingCalculator.get_ai_config(ai_config_static_name)
            if not ai_config:
                print("Config not found, raising error", flush=True)
                raise ConfigNotFoundError(ai_config_static_name)

            # اعتبارسنجی تطابق کاراکترها
            is_valid, error_msg = AIPricingCalculator.validate_request(
                ai_config_static_name=ai_config_static_name,
                character_count_frontend=character_count_frontend,
                character_count_backend=character_count_backend,
                max_tokens_requested=max_tokens_requested,
            )

            print(f"Character validation result: valid={is_valid}, error={error_msg}", flush=True)

            if not is_valid:
                diff = abs(character_count_frontend - character_count_backend)
                print(f"Character mismatch detected, diff: {diff}", flush=True)
                raise CharacterMismatchError(character_count_frontend, character_count_backend, tolerance=10)

            # اعتبارسنجی توکن‌ها (برای هیبریدی)
            if ai_config.is_advanced_hybrid_pricing() and max_tokens_requested:
                print("Validating token range for hybrid pricing", flush=True)
                valid, error, corrected = ai_config.validate_max_tokens(max_tokens_requested)
                if not valid:
                    print(f"Token validation failed: {error}", flush=True)
                    raise InvalidTokenRangeError(
                        max_tokens_requested, ai_config.hybrid_tokens_min, ai_config.hybrid_tokens_max
                    )

            # شارژ کاربر
            print("Proceeding to charge user", flush=True)
            success, message, details = AIPricingCalculator.charge_user(
                user=user,
                ai_config_static_name=ai_config_static_name,
                character_count=character_count_backend,
                max_tokens_requested=max_tokens_requested,
                description=description,
            )

            print(f"Charge result: success={success}, message={message}", flush=True)
            return success, message, details

        except ConfigNotFoundError as e:
            logger.error(f"Config not found: {e}")
            print(f"ConfigNotFoundError: {e}", flush=True)
            return False, str(e), e.details

        except CharacterMismatchError as e:
            logger.warning(f"Character mismatch: {e}")
            print(f"CharacterMismatchError: {e}", flush=True)
            return False, str(e), e.details

        except InsufficientBalanceError as e:
            logger.info(f"Insufficient balance: {e}")
            print(f"InsufficientBalanceError: {e}", flush=True)
            return False, str(e), e.details

        except InvalidTokenRangeError as e:
            logger.warning(f"Invalid token range: {e}")
            print(f"InvalidTokenRangeError: {e}", flush=True)
            return False, str(e), e.details

        except Exception as e:
            logger.error(f"Unexpected error in validate_and_charge: {e}", exc_info=True)
            print(f"Unexpected error in validate_and_charge: {e}", flush=True)
            return False, f"خطای غیرمنتظره: {str(e)}", {}

    @staticmethod
    def charge_user(
        user: User,
        ai_config_static_name: str,
        character_count: int,
        max_tokens_requested: int = None,
        description: str = None,
    ) -> Tuple[bool, str, Dict]:
        """
        شارژ کاربر برای استفاده از هوش مصنوعی

        Args:
            user: کاربر
            ai_config_static_name: نام استاتیک کانفیگ
            character_count: تعداد کاراکترهای ورودی
            max_tokens_requested: مقدار max_tokens درخواستی
            description: توضیحات تراکنش

        Returns:
            Tuple: (success, message, details)
        """
        from apps.wallet.services.wallet import WalletService

        print(f"=== Charge user ===", flush=True)
        print(f"User: {user}, Config: {ai_config_static_name}, Chars: {character_count}", flush=True)

        ai_config = AIPricingCalculator.get_ai_config(ai_config_static_name)

        if not ai_config:
            print("AI config not found for charging", flush=True)
            return False, "پیکربندی هوش مصنوعی یافت نشد", {}

        # بررسی بای‌پس
        should_bypass, bypass_reason = AIPricingCalculator.check_bypass_conditions(user, ai_config)
        print(f"Bypass check for charging: should_bypass={should_bypass}, reason={bypass_reason}", flush=True)

        if should_bypass:
            print("Charging bypassed - free usage", flush=True)
            return (
                True,
                f"استفاده رایگان: {bypass_reason}",
                {"is_free": True, "bypass_reason": bypass_reason, "total_cost": 0},
            )

        # محاسبه هزینه
        print("Calculating cost for charging", flush=True)
        cost_calculation = AIPricingCalculator.preview_cost(
            ai_config_static_name=ai_config_static_name,
            character_count=character_count,
            max_tokens_requested=max_tokens_requested,
        )

        if not cost_calculation.get("success"):
            print(f"Cost calculation failed: {cost_calculation.get('error')}", flush=True)
            return False, cost_calculation.get("error", "خطا در محاسبه هزینه"), {}

        total_cost = cost_calculation.get("total_cost", 0)
        print(f"Total cost calculated: {total_cost}", flush=True)

        # بررسی موجودی
        coin_balance = WalletService.get_wallet_coin_balance(user)
        print(f"User coin balance: {coin_balance}, Required: {total_cost}", flush=True)

        if coin_balance < total_cost:
            shortage = total_cost - float(coin_balance)
            print(f"Insufficient balance. Shortage: {shortage}", flush=True)
            return (
                False,
                "موجودی سکه کافی نیست",
                {
                    "required_coins": total_cost,
                    "current_balance": float(coin_balance),
                    "shortage": shortage,
                },
            )

        # شارژ کاربر
        try:
            print(f"Attempting to charge user {total_cost} coins", flush=True)
            WalletService.use_coins(
                user=user,
                coin_amount=total_cost,
                description=description or f"استفاده از {ai_config.name}",
                reference_id=f"ai_usage_{ai_config.static_name}",
            )

            print("User charged successfully", flush=True)
            return True, "پرداخت موفق", {"is_free": False, "charged_amount": total_cost, **cost_calculation}
        except Exception as e:
            logger.error(f"Error charging user: {e}")
            print(f"Error charging user: {e}", flush=True)
            return False, str(e), {}

    @staticmethod
    def get_step_options(ai_config_static_name: str) -> Dict:
        """
        دریافت گزینه‌های استپ برای نمایش در فرانت‌اند

        Returns:
            dict حاوی اطلاعات گزینه‌ها
        """
        print(f"Getting step options for: {ai_config_static_name}", flush=True)

        ai_config = AIPricingCalculator.get_ai_config(ai_config_static_name)

        if not ai_config:
            print("AI config not found for step options", flush=True)
            return {"success": False, "error": "پیکربندی هوش مصنوعی یافت نشد"}

        if not ai_config.is_advanced_hybrid_pricing():
            print("Config is not hybrid pricing", flush=True)
            return {"success": False, "error": "این کانفیگ از قیمت‌گذاری هیبریدی استفاده نمی‌کند"}

        options = ai_config.get_step_options()
        print(f"Step options retrieved: {options}", flush=True)

        return {
            "success": True,
            "min_tokens": ai_config.hybrid_tokens_min,
            "max_tokens": ai_config.hybrid_tokens_max,
            "step_size": ai_config.hybrid_tokens_step,
            "cost_per_step": float(ai_config.hybrid_cost_per_step),
            "options": options,
        }

    @staticmethod
    def validate_request(
        ai_config_static_name: str,
        character_count_frontend: int,
        character_count_backend: int,
        max_tokens_requested: int = None,
        tolerance: int = 10,
    ) -> Tuple[bool, str]:
        """
        اعتبارسنجی درخواست (چک کردن تطابق فرانت و بک)

        Args:
            ai_config_static_name: نام استاتیک کانفیگ
            character_count_frontend: تعداد کاراکترهای گزارش شده از فرانت
            character_count_backend: تعداد کاراکترهای شمارش شده در بک
            max_tokens_requested: مقدار max_tokens درخواستی
            tolerance: حد تحمل اختلاف (پیش‌فرض 10 کاراکتر)

        Returns:
            Tuple: (is_valid, error_message)
        """
        print(f"=== Validate request ===", flush=True)
        print(f"Config: {ai_config_static_name}", flush=True)
        print(f"Frontend chars: {character_count_frontend}, Backend chars: {character_count_backend}", flush=True)
        print(f"Max tokens: {max_tokens_requested}, Tolerance: {tolerance}", flush=True)

        ai_config = AIPricingCalculator.get_ai_config(ai_config_static_name)

        if not ai_config:
            print("AI config not found for validation", flush=True)
            return False, "پیکربندی هوش مصنوعی یافت نشد"

        # بررسی تطابق تعداد کاراکترها
        diff = abs(character_count_frontend - character_count_backend)
        print(f"Character count difference: {diff}", flush=True)

        if diff > tolerance:
            logger.warning(
                f"Character count mismatch: frontend={character_count_frontend}, "
                f"backend={character_count_backend}, diff={diff}"
            )
            print(f"Character count mismatch exceeds tolerance ({tolerance})", flush=True)
            return False, (
                f"عدم تطابق تعداد کاراکترها. " f"فرانت: {character_count_frontend}, " f"بک: {character_count_backend}"
            )

        # اعتبارسنجی max_tokens در صورت هیبریدی بودن
        if ai_config.is_advanced_hybrid_pricing() and max_tokens_requested:
            print("Validating max_tokens for hybrid pricing", flush=True)
            valid, error, _ = ai_config.validate_max_tokens(max_tokens_requested)
            print(f"Token validation result: valid={valid}, error={error}", flush=True)
            if not valid:
                return False, error

        print("Request validation successful", flush=True)
        return True, ""
