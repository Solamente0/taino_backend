from rest_framework import serializers

from apps.case.models import Session, Case
from apps.ai_chat.models import AISession
from base_utils.serializers.base import TainoBaseModelSerializer


class SessionListSerializer(TainoBaseModelSerializer):
    """
    سریالایزر لیست جلسات
    """
    case_number = serializers.CharField(source='case.case_number', read_only=True)
    session_type_display = serializers.CharField(source='get_session_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Session
        fields = [
            'pid',
            'case_number',
            'session_number',
            'session_type',
            'session_type_display',
            'status',
            'status_display',
            'scheduled_datetime',
            'duration_minutes',
            'summary',
            'key_topics',
            'client_rating',
            'created_at',
        ]
        read_only_fields = fields


class SessionDetailSerializer(TainoBaseModelSerializer):
    """
    سریالایزر جزئیات جلسه
    """
    case_number = serializers.CharField(source='case.case_number', read_only=True)
    session_type_display = serializers.CharField(source='get_session_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    audio_file_url = serializers.SerializerMethodField()
    video_file_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Session
        fields = [
            'pid',
            'case_number',
            'session_number',
            'session_type',
            'session_type_display',
            'status',
            'status_display',
            'scheduled_datetime',
            'actual_start_datetime',
            'actual_end_datetime',
            'duration_minutes',
            'summary',
            'key_topics',
            'chat_transcript',
            'audio_file_url',
            'video_file_url',
            'counselor_notes',
            'homework_assigned',
            'client_rating',
            'client_feedback',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'pid',
            'session_number',
            'duration_minutes',
            'created_at',
            'updated_at',
        ]
    
    def get_audio_file_url(self, obj):
        if obj.audio_file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.audio_file.url)
            return obj.audio_file.url
        return None
    
    def get_video_file_url(self, obj):
        if obj.video_file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.video_file.url)
            return obj.video_file.url
        return None


class SessionCreateSerializer(TainoBaseModelSerializer):
    """
    سریالایزر ایجاد جلسه
    """
    case = serializers.SlugRelatedField(
        queryset=Case.objects.all(),
        slug_field='pid'
    )
    ai_chat_session = serializers.SlugRelatedField(
        queryset=AISession.objects.all(),
        slug_field='pid',
        required=False,
        allow_null=True
    )
    
    class Meta:
        model = Session
        fields = [
            'case',
            'session_type',
            'scheduled_datetime',
            'ai_chat_session',
        ]
    
    def to_representation(self, instance):
        return SessionDetailSerializer(instance, context=self.context).data


class SessionUpdateSerializer(TainoBaseModelSerializer):
    """
    سریالایزر بروزرسانی جلسه
    """
    class Meta:
        model = Session
        fields = [
            'status',
            'actual_start_datetime',
            'actual_end_datetime',
            'summary',
            'key_topics',
            'chat_transcript',
            'counselor_notes',
            'homework_assigned',
            'client_rating',
            'client_feedback',
        ]
    
    def to_representation(self, instance):
        return SessionDetailSerializer(instance, context=self.context).data
