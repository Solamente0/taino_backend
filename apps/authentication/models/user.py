from random import randint

from django.contrib.auth.models import AbstractUser
from django.db import models
from rest_framework.exceptions import ValidationError

from apps.authentication.managers import TainoUserManager
from base_utils.base_models import BaseModel
from base_utils.clean import DataSanitizer
from django.utils.translation import gettext_lazy as _


def gen_vekalat_id():
    code = None
    unique = False
    while not unique:
        new_code = ""
        new_code += str(randint(1111111111, 9999999999))
        if not TainoUser.objects.filter(vekalat_id=new_code):
            code = new_code
            unique = True
    return code


class TainoUser(BaseModel, AbstractUser):
    is_admin = models.BooleanField(default=False)

    username_validator = None
    username = None

    email = models.EmailField("ایمیل", unique=True, null=True, db_index=True, blank=True)

    vekalat_id = models.CharField("شناسه وکالت آنلاین", max_length=10, editable=False, unique=True, db_index=True, blank=True)
    phone_number = models.CharField("شماره تلفن", unique=True, max_length=17, null=True, db_index=True)
    national_code = models.CharField("کد ملی", max_length=12, blank=True, null=True, default="", unique=False, db_index=True)
    language = models.CharField("زبان", default="fa", null=True, blank=True)
    currency = models.CharField(verbose_name="ارز", default="IRR", null=True, blank=True)

    is_subscribe = models.BooleanField("آیا مشترک خبر نامه است؟", default=False, blank=True)
    has_premium_account = models.BooleanField("اشتراک ویژه دارد؟", default=False, blank=True)
    is_email_verified = models.BooleanField("آیا ایمیل تایید شده است؟", default=False, blank=True)
    is_phone_number_verified = models.BooleanField("آیا شماره تلفن تایید شده؟", default=False, blank=True)

    birth_date = models.DateField(_("birth date"), default=None, null=True, blank=True)
    age = models.PositiveSmallIntegerField(default=0)

    phone_country = models.ForeignKey(
        verbose_name="کشور شماره تلفن",
        to="country.Country",
        related_name="users",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        default=None,
    )

    country = models.ForeignKey(
        verbose_name="کشور",
        to="country.Country",
        related_name="users_default",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        default=None,
    )

    avatar = models.ForeignKey(
        verbose_name="آواتار",
        to="document.TainoDocument",
        related_name="user_avatars",
        on_delete=models.CASCADE,
        default=None,
        null=True,
        blank=True,
    )

    role = models.ForeignKey(
        to="UserType", on_delete=models.SET_NULL, related_name="users", null=True, blank=True, default=None
    )

    provider = models.ForeignKey(
        to="barlawyer.Bar",
        on_delete=models.SET_NULL,
        related_name="provided_users",
        null=True,
        blank=True,
        default=None,
        verbose_name="کانون ارائه‌دهنده",
        help_text="کانونی که این کاربر را ارائه داده است",
    )

    USERNAME_FIELD = "pid"
    REQUIRED_FIELDS = []

    objects = TainoUserManager()

    @property
    def avatar_url(self):
        return self.avatar.url

    @property
    def has_password(self) -> bool:
        return self.has_usable_password()

    def __str__(self):
        if self.first_name:
            return f"{self.get_full_name()}, VID: {self.vekalat_id}"
        else:
            return f"{self.get_username()}, VID: {self.vekalat_id}"

    def validate_bypass_subscription(self):
        from apps.setting.models import GeneralSetting
        from apps.subscription.services.subscription import SubscriptionService

        # If user already has active subscription, no bypass needed
        if SubscriptionService.has_active_subscription(self):
            return

        # Default to no premium access
        self.has_premium_account = False

        # Check if user has a role that qualifies for bypass
        if not self.role:
            return

        role_name = self.role.static_name
        bypass_setting_key = f"subscription.disable_subscription_for_{role_name}"

        # Check if bypass is enabled for this role
        if GeneralSetting.objects.filter(key=bypass_setting_key, value="1").exists():
            self.has_premium_account = True

    def save(self, *args, **kwargs):

        if not self.vekalat_id:
            self.vekalat_id = gen_vekalat_id()

        # چک کردن یکتا بودن national_code اگر مقدار داشته باشد
        if self.national_code:
            # برای آپدیت، باید خودش را از چک خارج کند
            existing = TainoUser.objects.filter(national_code=self.national_code)
            if self.pk:  # اگر آپدیت است
                existing = existing.exclude(pk=self.pk)

            if existing.exists():
                raise ValidationError({"national_code": "کاربری با این کد ملی قبلاً ثبت شده است."})

        # if self.phone_number  :
        #     self.phone_number = DataSanitizer.clean_phone_number(self.phone_number)
        instance = super(TainoUser, self).save(*args, **kwargs)
        self.validate_bypass_subscription()

        return instance

    class Meta:
        verbose_name = "کاربر سایت"
        verbose_name_plural = "کاربران سایت"
