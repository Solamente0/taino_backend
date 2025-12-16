from django.db import models
from django.utils.translation import gettext_lazy as _

from base_utils.base_models import TimeStampModel, ActivableModel, StaticalIdentifier, DescriptiveModel


class ServiceCategory(TimeStampModel, ActivableModel, StaticalIdentifier, DescriptiveModel):
    """
    Hierarchical service category model for categorizing services
    """

    icon = models.ForeignKey(
        verbose_name="آیکون",
        to="document.TainoDocument",
        related_name="service_category_icons",
        on_delete=models.CASCADE,
        default=None,
        null=True,
        blank=True,
    )
    order = models.IntegerField(default=0, verbose_name="ترتیب")
    soon = models.BooleanField(default=False, verbose_name="به زودی")

    frontend_route = models.CharField(default=None, null=True, verbose_name=_("آدرس فرانت"))
    roles = models.ManyToManyField("authentication.UserType", verbose_name=_("نقش کاربر"))

    # Parent-child relationship
    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        related_name="children",
        null=True,
        blank=True,
        default=None,
        verbose_name=_("دسته‌بندی والد")
    )

    class Meta:
        verbose_name = _("دسته‌بندی سرویس")
        verbose_name_plural = _("دسته‌بندی‌های سرویس")
        ordering = ["order"]

    def __str__(self):
        if self.parent:
            return f"{self.parent.name} > {self.name}"
        return self.name

    def get_all_children(self, include_self=False):
        """
        Recursively get all children categories
        """
        children = list(self.children.filter(is_active=True))
        all_children = children.copy()

        for child in children:
            all_children.extend(child.get_all_children())

        if include_self:
            return [self] + all_children
        return all_children

    def get_ancestors(self):
        """
        Get all parent categories up to root
        """
        ancestors = []
        current = self.parent

        while current:
            ancestors.append(current)
            current = current.parent

        return ancestors

    @property
    def is_root(self):
        """Check if this is a root category"""
        return self.parent is None

    @property
    def level(self):
        """Get the depth level of this category (0 for root)"""
        return len(self.get_ancestors())


class ServiceItem(TimeStampModel, ActivableModel, StaticalIdentifier, DescriptiveModel):
    """
    Model for defining application services
    """

    category = models.ForeignKey(
        verbose_name="دسته‌بندی",
        to=ServiceCategory,
        related_name="service_items",
        on_delete=models.CASCADE,
        default=None,
        null=True,
        blank=True,
    )
    icon = models.ForeignKey(
        verbose_name="آیکون",
        to="document.TainoDocument",
        related_name="service_item_icons",
        on_delete=models.CASCADE,
        default=None,
        null=True,
        blank=True,
    )
    order = models.IntegerField(default=0, verbose_name="ترتیب")
    soon = models.BooleanField(default=False, verbose_name="به زودی")

    frontend_route = models.CharField(default=None, null=True, verbose_name=_("آدرس فرانت"))

    roles = models.ManyToManyField("authentication.UserType", verbose_name=_("نقش کاربر"))

    class Meta:
        verbose_name = _("سرویس")
        verbose_name_plural = _("سرویس‌ها")
        ordering = ["order"]

    def __str__(self):
        return self.name
