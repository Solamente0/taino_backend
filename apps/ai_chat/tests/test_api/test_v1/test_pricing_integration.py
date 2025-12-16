# apps/ai_chat/tests/test_pricing_integration.py
"""
تست‌های یکپارچگی برای سیستم قیمت‌گذاری
"""
from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model

from apps.ai_chat.models import ChatAIConfig, GeneralChatAIConfig, AISession
from apps.ai_chat.services.ai_pricing_calculator import AIPricingCalculator
from apps.wallet.services.wallet import WalletService

User = get_user_model()


class MessageBasedPricingTest(TestCase):
    """تست قیمت‌گذاری ثابت"""
    
    def setUp(self):
        # ایجاد کاربر
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        
        # شارژ کیف پول
        WalletService.add_coins(
            user=self.user,
            coin_amount=1000,
            description='تست اولیه'
        )
        
        # ایجاد General Config
        self.general_config = GeneralChatAIConfig.objects.create(
            name='تست عمومی',
            static_name='test_general',
            description='تست',
            system_instruction='شما یک دستیار هستید',
            max_messages_per_chat=100,
            max_tokens_per_chat=50000
        )
        
        # ایجاد AI Config با قیمت ثابت
        self.ai_config = ChatAIConfig.objects.create(
            general_config=self.general_config,
            name='تست ثابت',
            static_name='test_message_based',
            strength='medium',
            description='تست قیمت ثابت',
            model_name='test-model',
            api_key='test-key',
            pricing_type='message_based',
            cost_per_message=Decimal('10.00'),  # 10 سکه به ازای هر پیام
            is_active=True
        )
    
    def test_message_based_preview(self):
        """تست پیش‌نمایش قیمت ثابت"""
        result = AIPricingCalculator.preview_cost(
            ai_config_static_name='test_message_based',
            character_count=500,  # بی‌تاثیر در قیمت ثابت
            max_tokens_requested=None
        )
        
        self.assertTrue(result['success'])
        self.assertEqual(result['cost'], 10.00)
        self.assertEqual(result['pricing_type'], 'message_based')
    
    def test_message_based_charge(self):
        """تست شارژ برای قیمت ثابت"""
        initial_balance = WalletService.get_wallet_coin_balance(self.user)
        
        success, message, details = AIPricingCalculator.charge_user(
            user=self.user,
            ai_config_static_name='test_message_based',
            character_count=500,
            description='تست شارژ'
        )
        
        self.assertTrue(success)
        self.assertEqual(details['charged_amount'], 10.00)
        
        # بررسی کاهش موجودی
        new_balance = WalletService.get_wallet_coin_balance(self.user)
        self.assertEqual(float(new_balance), float(initial_balance) - 10.00)
    
    def test_insufficient_balance(self):
        """تست موجودی ناکافی"""
        # خالی کردن کیف پول
        WalletService.use_coins(
            user=self.user,
            coin_amount=995,
            description='خالی کردن'
        )
        
        success, message, details = AIPricingCalculator.charge_user(
            user=self.user,
            ai_config_static_name='test_message_based',
            character_count=100,
            description='تست'
        )
        
        self.assertFalse(success)
        self.assertIn('shortage', details)


class HybridPricingTest(TestCase):
    """تست قیمت‌گذاری هیبریدی"""
    
    def setUp(self):
        # ایجاد کاربر
        self.user = User.objects.create_user(
            email='hybrid@example.com',
            password='testpass123',
            first_name='Hybrid',
            last_name='User'
        )
        
        # شارژ کیف پول
        WalletService.add_coins(
            user=self.user,
            coin_amount=1000,
            description='تست اولیه'
        )
        
        # ایجاد General Config
        self.general_config = GeneralChatAIConfig.objects.create(
            name='تست هیبریدی',
            static_name='test_hybrid_general',
            description='تست',
            system_instruction='شما یک دستیار هستید',
            max_messages_per_chat=100,
            max_tokens_per_chat=50000
        )
        
        # ایجاد AI Config با قیمت هیبریدی
        self.ai_config = ChatAIConfig.objects.create(
            general_config=self.general_config,
            name='تست هیبریدی',
            static_name='test_hybrid',
            strength='very_strong',
            description='تست قیمت هیبریدی',
            model_name='test-model',
            api_key='test-key',
            pricing_type='advanced_hybrid',
            # قیمت پایه
            hybrid_base_cost=Decimal('5.00'),
            # قیمت کاراکتر
            hybrid_char_per_coin=2500,
            hybrid_free_chars=5000,
            # قیمت توکن
            hybrid_tokens_min=1000,
            hybrid_tokens_max=8000,
            hybrid_tokens_step=500,
            hybrid_cost_per_step=Decimal('1.00'),
            is_active=True
        )
    
    def test_hybrid_free_chars_only(self):
        """تست با کاراکترهای رایگان"""
        result = AIPricingCalculator.preview_cost(
            ai_config_static_name='test_hybrid',
            character_count=3000,  # کمتر از 5000
            max_tokens_requested=1000  # حداقل
        )
        
        self.assertTrue(result['success'])
        # فقط هزینه پایه
        self.assertEqual(result['total_cost'], 5.00)
        self.assertEqual(result['char_cost'], 0)
        self.assertEqual(result['step_cost'], 0)
    
    def test_hybrid_with_char_cost(self):
        """تست با هزینه کاراکتر"""
        result = AIPricingCalculator.preview_cost(
            ai_config_static_name='test_hybrid',
            character_count=10000,  # 5000 بیشتر از رایگان
            max_tokens_requested=1000
        )
        
        self.assertTrue(result['success'])
        # 5000 / 2500 = 2 سکه
        self.assertEqual(result['char_cost'], 2.00)
        # جمع: 5 (پایه) + 2 (کاراکتر) = 7
        self.assertEqual(result['total_cost'], 7.00)
    
    def test_hybrid_with_step_cost(self):
        """تست با هزینه استپ"""
        result = AIPricingCalculator.preview_cost(
            ai_config_static_name='test_hybrid',
            character_count=3000,  # رایگان
            max_tokens_requested=2000  # 2 استپ بالاتر از 1000
        )
        
        self.assertTrue(result['success'])
        # (2000 - 1000) / 500 = 2 استپ = 2 سکه
        self.assertEqual(result['step_cost'], 2.00)
        # جمع: 5 (پایه) + 2 (استپ) = 7
        self.assertEqual(result['total_cost'], 7.00)
    
    def test_hybrid_full_calculation(self):
        """تست محاسبه کامل هیبریدی"""
        result = AIPricingCalculator.preview_cost(
            ai_config_static_name='test_hybrid',
            character_count=10000,  # 5000 بیشتر = 2 سکه
            max_tokens_requested=3000  # 4 استپ = 4 سکه
        )
        
        self.assertTrue(result['success'])
        # پایه: 5
        # کاراکتر: 2
        # استپ: 4
        # جمع: 11
        self.assertEqual(result['total_cost'], 11.00)
    
    def test_character_validation(self):
        """تست اعتبارسنجی تطابق کاراکترها"""
        is_valid, error = AIPricingCalculator.validate_request(
            ai_config_static_name='test_hybrid',
            character_count_frontend=1000,
            character_count_backend=1005,  # 5 کاراکتر اختلاف
            max_tokens_requested=2000,
            tolerance=10
        )
        
        self.assertTrue(is_valid)
        
        # اختلاف بیش از حد
        is_valid, error = AIPricingCalculator.validate_request(
            ai_config_static_name='test_hybrid',
            character_count_frontend=1000,
            character_count_backend=1050,  # 50 کاراکتر اختلاف
            max_tokens_requested=2000,
            tolerance=10
        )
        
        self.assertFalse(is_valid)
        self.assertIn('عدم تطابق', error)


class SessionIntegrationTest(TestCase):
    """تست یکپارچگی با AISession"""
    
    def setUp(self):
        # ایجاد کاربر
        self.user = User.objects.create_user(
            email='session@example.com',
            password='testpass123',
            first_name='Session',
            last_name='User'
        )
        
        # شارژ کیف پول
        WalletService.add_coins(
            user=self.user,
            coin_amount=1000,
            description='تست اولیه'
        )
        
        # ایجاد configs
        self.general_config = GeneralChatAIConfig.objects.create(
            name='تست جلسه',
            static_name='test_session',
            description='تست',
            system_instruction='شما یک دستیار هستید',
            max_messages_per_chat=10,
            max_tokens_per_chat=5000
        )
        
        self.ai_config = ChatAIConfig.objects.create(
            general_config=self.general_config,
            name='تست ثابت جلسه',
            static_name='test_session_config',
            strength='medium',
            description='تست',
            model_name='test-model',
            api_key='test-key',
            pricing_type='message_based',
            cost_per_message=Decimal('5.00'),
            is_active=True
        )
        
        # ایجاد جلسه
        self.session = AISession.objects.create(
            user=self.user,
            ai_config=self.ai_config,
            title='جلسه تست',
            status='active'
        )
    
    def test_session_message_charge_tracking(self):
        """تست ردیابی هزینه در جلسه"""
        initial_cost = self.session.total_cost_coins
        
        # شارژ برای 3 پیام
        for i in range(3):
            self.session.add_message_based_cost(5.00)
        
        # بررسی افزایش هزینه
        self.session.refresh_from_db()
        self.assertEqual(
            float(self.session.total_cost_coins),
            float(initial_cost) + 15.00
        )
    
    def test_session_readonly_on_limit(self):
        """تست قفل شدن جلسه در رسیدن به محدودیت"""
        # ارسال 10 پیام (محدودیت)
        for i in range(10):
            self.session.total_messages += 1
            self.session.save()
        
        # بررسی readonly
        is_readonly, reason = self.session.check_and_update_readonly()
        
        self.assertTrue(is_readonly)
        self.assertEqual(reason, 'حداکثر تعداد پیام‌ها')
