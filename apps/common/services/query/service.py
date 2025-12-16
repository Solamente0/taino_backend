from django.db.models import QuerySet

from apps.common.models import ServiceItem, ServiceCategory
from base_utils.services import AbstractBaseQuery


class ServiceCategoryQuery(AbstractBaseQuery):
    @staticmethod
    def get_active_categories(base_queryset: QuerySet[ServiceCategory] = None) -> QuerySet[ServiceCategory]:
        """
        Get all active service categories ordered by their display order
        """
        if not base_queryset:
            base_queryset = ServiceCategory.objects.all()

        return base_queryset.filter(is_active=True).order_by("order")

    @staticmethod
    def get_root_categories(base_queryset: QuerySet[ServiceCategory] = None) -> QuerySet[ServiceCategory]:
        """
        Get only root-level categories (categories without parent)
        """
        if not base_queryset:
            base_queryset = ServiceCategory.objects.all()

        return base_queryset.filter(is_active=True, parent=None).order_by("order")

    @staticmethod
    def get_category_by_static_name(static_name: str) -> ServiceCategory:
        """
        Get a category by its static name
        """
        try:
            return ServiceCategory.objects.get(static_name=static_name, is_active=True)
        except ServiceCategory.DoesNotExist:
            return None

    @staticmethod
    def get_category_with_children(static_name: str) -> tuple[ServiceCategory, list]:
        """
        Get a category and all its children (recursive)
        Returns: (category, list_of_children)
        """
        try:
            category = ServiceCategory.objects.get(static_name=static_name, is_active=True)
            children = category.get_all_children()
            return category, children
        except ServiceCategory.DoesNotExist:
            return None, []

    @staticmethod
    def get_children_of_category(category: ServiceCategory) -> QuerySet[ServiceCategory]:
        """
        Get immediate children of a category
        """
        return category.children.filter(is_active=True).order_by("order")


class ServiceItemQuery(AbstractBaseQuery):
    @staticmethod
    def get_active_services(base_queryset: QuerySet[ServiceItem] = None) -> QuerySet[ServiceItem]:
        """
        Get all active services ordered by their display order
        """
        if not base_queryset:
            base_queryset = ServiceItem.objects.all()

        return base_queryset.filter(is_active=True).order_by("order")

    @staticmethod
    def get_service_by_static_name(static_name: str) -> ServiceItem:
        """
        Get a service by its static name
        """
        try:
            return ServiceItem.objects.get(static_name=static_name, is_active=True)
        except ServiceItem.DoesNotExist:
            return None

    @staticmethod
    def get_services_by_category(category_static_name: str, include_children: bool = False) -> QuerySet[ServiceItem]:
        """
        Get all active services in a specific category

        Args:
            category_static_name: Static name of the category
            include_children: If True, include services from all child categories
        """
        try:
            category = ServiceCategory.objects.get(static_name=category_static_name, is_active=True)

            if include_children:
                # Get services from this category and all children
                category_ids = [category.id]
                category_ids.extend([child.id for child in category.get_all_children()])

                return ServiceItem.objects.filter(category_id__in=category_ids, is_active=True).order_by("order")
            else:
                # Get services only from this specific category
                return ServiceItem.objects.filter(category=category, is_active=True).order_by("order")

        except ServiceCategory.DoesNotExist:
            return ServiceItem.objects.none()

    @staticmethod
    def get_services_by_category_object(category: ServiceCategory, include_children: bool = False) -> QuerySet[ServiceItem]:
        """
        Get services by category object instead of static name
        """
        if include_children:
            category_ids = [category.id]
            category_ids.extend([child.id for child in category.get_all_children()])

            return ServiceItem.objects.filter(category_id__in=category_ids, is_active=True).order_by("order")
        else:
            return ServiceItem.objects.filter(category=category, is_active=True).order_by("order")
