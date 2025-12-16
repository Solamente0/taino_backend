from django.db import models

from apps.document.models import TainoDocument
from base_utils.base_models import TimeStampModel, ActivableModel


class HomePage(TimeStampModel, ActivableModel):
    # Header section
    header_title = models.CharField(max_length=255, blank=True, null=True)
    header_sub_title = models.CharField(max_length=255, blank=True, null=True)

    # Why section
    why = models.TextField(blank=True, null=True)
    why_point1 = models.CharField(max_length=255, blank=True, null=True)
    why_point2 = models.CharField(max_length=255, blank=True, null=True)
    why_point3 = models.CharField(max_length=255, blank=True, null=True)
    why_point4 = models.CharField(max_length=255, blank=True, null=True)

    # How to file tax section
    how_to_file_tax_title = models.CharField(max_length=255, blank=True, null=True)
    how_to_file_tax_short_description = models.TextField(blank=True, null=True)

    # Corporate strategy
    corporate_strategy_img = models.ForeignKey(
        TainoDocument, on_delete=models.SET_NULL, null=True, related_name="corporate_strategy_image"
    )
    corporate_strategy_title = models.CharField(max_length=255, blank=True, null=True)
    corporate_strategy_description = models.TextField(blank=True, null=True)
    corporate_strategy_section1 = models.CharField(max_length=255, blank=True, null=True)
    corporate_strategy_section1_des = models.TextField(blank=True, null=True)
    corporate_strategy_section2 = models.CharField(max_length=255, blank=True, null=True)
    corporate_strategy_section2_des = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = "تنظیمات صفحه خانه"
        verbose_name_plural = "تنظیمات صفحه خانه"


class HeroSectionImage(TimeStampModel):
    home_page = models.ForeignKey(HomePage, on_delete=models.CASCADE, related_name="hero_section_images")
    image = models.ForeignKey(TainoDocument, on_delete=models.CASCADE)
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ["order"]
        verbose_name = "تنظیمات بخش هیرو"
        verbose_name_plural = "تنظیمات بخش هیرو"


class PartnerShip(TimeStampModel):
    home_page = models.ForeignKey(HomePage, on_delete=models.CASCADE, related_name="partnerships")
    image = models.ForeignKey(TainoDocument, on_delete=models.CASCADE)
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ["order"]
        verbose_name = "تنظیمات بخش همکاران"
        verbose_name_plural = "تنظیمات بخش همکاران"


class WayToFileTax(TimeStampModel, ActivableModel):
    home_page = models.ForeignKey(HomePage, on_delete=models.CASCADE, related_name="way_to_file_tax")
    title = models.CharField(max_length=255)
    description = models.TextField()
    image = models.ForeignKey(TainoDocument, on_delete=models.CASCADE)
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ["order"]
        verbose_name = "تنظیمات بخش چگونه ارتباط بگیرید"
        verbose_name_plural = "تنظیمات بخش چگونه ارتباط بگیرید"


class Service(TimeStampModel, ActivableModel):
    home_page = models.ForeignKey(HomePage, on_delete=models.CASCADE, related_name="services")
    title = models.CharField(max_length=255)
    description = models.TextField()
    logo = models.ForeignKey(TainoDocument, on_delete=models.CASCADE)
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ["order"]
        verbose_name = "سرویس"
        verbose_name_plural = "سرویس"


class TeamMember(TimeStampModel, ActivableModel):
    TEAM_TYPE_CHOICES = (
        ("executive_team", "Executive Team"),
        ("accounting_affiliates", "Accounting Affiliates"),
    )

    team_type = models.CharField(max_length=30, choices=TEAM_TYPE_CHOICES)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    title = models.CharField(max_length=100)
    university = models.CharField(max_length=255, blank=True, null=True)
    short_brief = models.TextField(blank=True, null=True)
    image = models.ForeignKey(TainoDocument, on_delete=models.SET_NULL, null=True)
    linkedin = models.URLField(blank=True, null=True)
    twitter = models.URLField(blank=True, null=True)
    facebook = models.URLField(blank=True, null=True)
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ["team_type", "order"]
        verbose_name = "عضو تیم"
        verbose_name_plural = "اعضای تیم"


class Testimonial(TimeStampModel, ActivableModel):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    role = models.CharField(max_length=100)
    city = models.CharField(max_length=100, blank=True, null=True)
    profile_img = models.ForeignKey(TainoDocument, on_delete=models.SET_NULL, null=True)
    rating = models.PositiveSmallIntegerField(default=5)
    comment = models.TextField()

    class Meta:
        ordering = ["-created_at"]
