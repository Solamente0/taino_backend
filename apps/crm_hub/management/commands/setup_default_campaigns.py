"""
apps/crm_hub/management/commands/setup_default_campaigns.py
Management command to set up default CRM campaigns
"""
from django.core.management.base import BaseCommand
from apps.crm_hub.models import CRMCampaign, CRMCampaignType, NotificationChannel


class Command(BaseCommand):
    help = 'Set up default CRM campaigns'

    def handle(self, *args, **kwargs):
        campaigns = [
            {
                'static_name': 'zero_day_email',
                'name': 'ایمیل خوش‌آمدگویی',
                'description': 'ایمیل خوش‌آمدگویی به کاربران جدید',
                'campaign_type': CRMCampaignType.WELCOME,
                'trigger_days': 0,
                'channels': [NotificationChannel.EMAIL, NotificationChannel.IN_APP],
                'email_subject': 'به {user_name} خوش آمدید!',
                'email_template': '''
سلام {first_name} عزیز،

به سامانه وکالت آنلاین خوش آمدید! ما خوشحالیم که شما را در جمع خود داریم.

برای شروع، می‌توانید:
- پروفایل خود را تکمیل کنید
- با امکانات سیستم آشنا شوید
- اولین پرونده خود را ایجاد کنید

تیم پشتیبانی ما همیشه در خدمت شماست.

با احترام،
تیم وکالت آنلاین
                ''',
                'push_title': 'خوش آمدید!',
                'push_body': 'به سامانه وکالت آنلاین خوش آمدید',
                'priority': 1,
            },
            {
                'static_name': 'day_3_thank_you_email',
                'name': 'ایمیل تشکر روز سوم',
                'description': 'تشکر از کاربران برای استفاده از سیستم',
                'campaign_type': CRMCampaignType.ENGAGEMENT,
                'trigger_days': 3,
                'channels': [NotificationChannel.EMAIL],
                'email_subject': 'از استفاده شما سپاسگزاریم',
                'email_template': '''
سلام {first_name} عزیز،

{days} روز از عضویت شما در سامانه می‌گذرد و ما از همراهی شما سپاسگزاریم.

تا به حال {activities_count} فعالیت در سیستم داشته‌اید.

اگر سوالی دارید یا به راهنمایی نیاز دارید، تیم ما آماده کمک است.

با تشکر،
تیم وکالت آنلاین
                ''',
                'priority': 3,
            },
            {
                'static_name': 'day_7_engagement_email',
                'name': 'ایمیل افزایش تعامل روز ۷',
                'description': 'ترغیب کاربران غیرفعال به بازگشت',
                'campaign_type': CRMCampaignType.RETENTION,
                'trigger_days': 7,
                'channels': [NotificationChannel.EMAIL, NotificationChannel.PUSH],
                'require_no_activity': True,
                'email_subject': 'دلتان برای ما تنگ نشده؟',
                'email_template': '''
سلام {first_name} عزیز،

{days} روز است که شما را ندیده‌ایم. دلمان برای شما تنگ شده!

ویژگی‌های جدیدی به سیستم اضافه کرده‌ایم که ممکن است برای شما مفید باشد:
- مدیریت بهتر پرونده‌ها
- اعلان‌های هوشمند
- تقویم یکپارچه

منتظر بازگشت شما هستیم!

با احترام،
تیم وکالت آنلاین
                ''',
                'push_title': 'دلمان برای شما تنگ شده',
                'push_body': 'بیایید و ویژگی‌های جدید را ببینید',
                'priority': 4,
            },
            {
                'static_name': 'day_10_sms_reengagement',
                'name': 'پیامک بازگشت روز ۱۰',
                'description': 'پیامک برای کاربران غیرفعال',
                'campaign_type': CRMCampaignType.REACTIVATION,
                'trigger_days': 10,
                'channels': [NotificationChannel.SMS],
                'require_no_activity': True,
                'sms_template': '''
سلام {first_name}، 

{days} روز است که شما را ندیده‌ایم. برای بازگشت شما هدیه ویژه‌ای داریم!

وکالت آنلاین
                ''',
                'priority': 5,
            },
            {
                'static_name': 'subscription_80_percent_email',
                'name': 'یادآوری تمدید اشتراک ۸۰٪',
                'description': 'یادآوری تمدید اشتراک در ۸۰٪ مصرف',
                'campaign_type': CRMCampaignType.SUBSCRIPTION,
                'trigger_days': 0,
                'channels': [NotificationChannel.EMAIL, NotificationChannel.SMS, NotificationChannel.PUSH],
                'subscription_expire_threshold': 20,  # 20% remaining = 80% used
                'email_subject': 'اشتراک شما رو به پایان است',
                'email_template': '''
سلام {first_name} عزیز،

اشتراک شما {subscription_days_remaining} روز دیگر به پایان می‌رسد.

برای ادامه استفاده بدون وقفه از خدمات، پیشنهاد می‌کنیم اشتراک خود را تمدید کنید.

با تمدید زودهنگام، از تخفیف ویژه برخوردار خواهید شد!

تیم وکالت آنلاین
                ''',
                'sms_template': 'سلام {first_name}، اشتراک شما {subscription_days_remaining} روز دیگر به پایان می‌رسد. برای تمدید اقدام کنید.',
                'push_title': 'یادآوری تمدید اشتراک',
                'push_body': 'اشتراک شما به زودی به پایان می‌رسد',
                'priority': 2,
            },
        ]

        created_count = 0
        updated_count = 0

        for campaign_data in campaigns:
            campaign, created = CRMCampaign.objects.update_or_create(
                static_name=campaign_data['static_name'],
                defaults=campaign_data
            )
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Created campaign: {campaign.name}')
                )
            else:
                updated_count += 1
                self.stdout.write(
                    self.style.WARNING(f'⟳ Updated campaign: {campaign.name}')
                )

        self.stdout.write(
            self.style.SUCCESS(
                f'\nDone! Created: {created_count}, Updated: {updated_count}'
            )
        )
