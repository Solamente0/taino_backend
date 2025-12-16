from rest_framework import serializers

from apps.case.models import CaseDocument, Case, Session, Assessment
from apps.document.services.query import TainoDocumentQuery
from base_utils.serializers.base import TainoBaseModelSerializer


class CaseDocumentSerializer(TainoBaseModelSerializer):
    """
    سریالایزر اسناد پرونده
    """
    case_number = serializers.CharField(source='case.case_number', read_only=True)
    document_type_display = serializers.CharField(source='get_document_type_display', read_only=True)
    file_url = serializers.SerializerMethodField()
    uploaded_by_name = serializers.CharField(source='uploaded_by.get_full_name', read_only=True, allow_null=True)
    
    class Meta:
        model = CaseDocument
        fields = [
            'pid',
            'case_number',
            'document_type',
            'document_type_display',
            'title',
            'description',
            'file_url',
            'uploaded_by_name',
            'tags',
            'is_confidential',
            'created_at',
        ]
        read_only_fields = fields
    
    def get_file_url(self, obj):
        if obj.file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.file.url)
            return obj.file.url
        return None


class CaseDocumentCreateSerializer(TainoBaseModelSerializer):
    """
    سریالایزر ایجاد سند پرونده
    """
    case = serializers.SlugRelatedField(
        queryset=Case.objects.all(),
        slug_field='pid'
    )
    file = serializers.SlugRelatedField(
        queryset=TainoDocumentQuery.get_visible_for_create_update(),
        slug_field='pid'
    )
    session = serializers.SlugRelatedField(
        queryset=Session.objects.all(),
        slug_field='pid',
        required=False,
        allow_null=True
    )
    assessment = serializers.SlugRelatedField(
        queryset=Assessment.objects.all(),
        slug_field='pid',
        required=False,
        allow_null=True
    )
    
    class Meta:
        model = CaseDocument
        fields = [
            'case',
            'document_type',
            'title',
            'description',
            'file',
            'session',
            'assessment',
            'tags',
            'is_confidential',
        ]
    
    def create(self, validated_data):
        validated_data['uploaded_by'] = self.context['request'].user
        return super().create(validated_data)
    
    def to_representation(self, instance):
        return CaseDocumentSerializer(instance, context=self.context).data
