from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils.translation import gettext_lazy as _


class SecretaryViewMixin:
    """
    Mixin to add secretary-related functionality to viewsets
    """

    def get_queryset(self):
        """Override to include resources related to lawyer if user is a secretary"""
        queryset = super().get_queryset()

        # If this is a secretary accessing lawyer resources
        if hasattr(self.request, "is_secretary_request") and self.request.is_secretary_request:
            # Identify the model's lawyer field (could be 'lawyer', 'owner', etc.)
            lawyer_field = None
            if hasattr(queryset.model, "lawyer"):
                lawyer_field = "lawyer"
            elif hasattr(queryset.model, "owner"):
                lawyer_field = "owner"

            if lawyer_field:
                # Expand queryset to include lawyer's resources
                lawyer_filter = {f"{lawyer_field}": self.request.acting_as_lawyer}
                expanded_queryset = queryset.model.objects.filter(**lawyer_filter)
                queryset = queryset.union(expanded_queryset)

        return queryset

    @action(detail=False, methods=["GET"])
    def lawyer_resources(self, request):
        """
        View endpoint to explicitly get resources belonging to the lawyer
        (for secretaries who need to see what the lawyer has)
        """
        if not (hasattr(request, "is_secretary_request") and request.is_secretary_request):
            return Response(
                {"detail": _("Only secretaries can access lawyer resources directly")}, status=status.HTTP_403_FORBIDDEN
            )

        # Get the lawyer
        lawyer = request.acting_as_lawyer

        # Identify the model's lawyer field
        lawyer_field = None
        model = self.get_queryset().model
        if hasattr(model, "lawyer"):
            lawyer_field = "lawyer"
        elif hasattr(model, "owner"):
            lawyer_field = "owner"

        if not lawyer_field:
            return Response(
                {"detail": _("Cannot determine lawyer field for this resource")}, status=status.HTTP_400_BAD_REQUEST
            )

        # Get resources belonging to lawyer
        lawyer_filter = {f"{lawyer_field}": lawyer}
        queryset = model.objects.filter(**lawyer_filter)

        # Apply any filtering, pagination, etc.
        queryset = self.filter_queryset(queryset)
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
