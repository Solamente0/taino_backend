from rest_framework import serializers

from apps.common.models import ServiceItem, ServiceCategory
from base_utils.serializers.base import TainoBaseModelSerializer


class ServiceCategorySerializer(TainoBaseModelSerializer):
    icon = serializers.FileField(source="icon.file", read_only=True, required=False)
    parent = serializers.SerializerMethodField()
    children = serializers.SerializerMethodField()
    ancestors = serializers.SerializerMethodField()
    level = serializers.IntegerField(read_only=True)
    is_root = serializers.BooleanField(read_only=True)

    class Meta:
        model = ServiceCategory
        fields = [
            "pid",
            "static_name",
            "name",
            "description",
            "icon",
            "created_at",
            "updated_at",
            "is_active",
            "soon",
            "frontend_route",
            "parent",
            "children",
            "ancestors",
            "level",
            "is_root",
        ]
        read_only_fields = fields

    def get_parent(self, obj):
        """Return parent category basic info"""
        if obj.parent:
            return {
                "pid": obj.parent.pid,
                "static_name": obj.parent.static_name,
                "name": obj.parent.name,
            }
        return None

    def get_children(self, obj):
        """
        Return immediate children categories
        Only include if explicitly requested via context
        """
        if self.context.get('include_children', False):
            children = obj.children.filter(is_active=True).order_by('order')
            # Apply role filtering if user is provided
            user = self.context.get('request').user if self.context.get('request') else None
            if user and user.is_authenticated and hasattr(user, 'role') and user.role:
                from django.db.models import Q, Count
                children = children.annotate(role_count=Count('roles')).filter(
                    Q(role_count=0) | Q(roles=user.role)
                ).distinct()
            else:
                from django.db.models import Count
                children = children.annotate(role_count=Count('roles')).filter(role_count=0)

            return ServiceCategorySerializer(children, many=True, context=self.context).data
        return []

    def get_ancestors(self, obj):
        """Return all ancestor categories (breadcrumb trail)"""
        if self.context.get('include_ancestors', False):
            ancestors = obj.get_ancestors()
            return [
                {
                    "pid": ancestor.pid,
                    "static_name": ancestor.static_name,
                    "name": ancestor.name,
                }
                for ancestor in reversed(ancestors)  # Root first
            ]
        return []


class ServiceItemSerializer(TainoBaseModelSerializer):
    icon = serializers.FileField(source="icon.file", read_only=True, required=False)
    category = ServiceCategorySerializer(read_only=True)

    class Meta:
        model = ServiceItem
        fields = [
            "pid",
            "category",
            "static_name",
            "name",
            "description",
            "icon",
            "created_at",
            "updated_at",
            "is_active",
            "soon",
            "frontend_route",
        ]
        read_only_fields = fields
