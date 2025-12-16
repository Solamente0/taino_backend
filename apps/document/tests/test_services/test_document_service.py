from django.contrib.contenttypes.models import ContentType
from django.core.files.uploadedfile import SimpleUploadedFile

from apps.document.models import TainoDocument
from apps.document.services.document import DocumentService
from base_utils.base_tests import TainoBaseServiceTestCase


class DocumentServiceTestCase(TainoBaseServiceTestCase):

    def setUp(self):
        super().setUp()
        self.content_type = ContentType.objects.first()
        self.object_id = 123
        self.document_service = DocumentService()

    def test_create_documents(self):
        file1 = SimpleUploadedFile("file1.jpg", b"file_content", content_type="image/jpeg")
        file2 = SimpleUploadedFile("file2.jpg", b"file_content", content_type="image/jpeg")

        uploaded_pid = self.document_service.create_documents(self.user, [file1, file2], self.content_type, self.object_id)

        self.assertEqual(len(uploaded_pid), 2)
        self.assertEqual(TainoDocument.objects.count(), 2)
        self.assertTrue(all(isinstance(pid, str) for pid in uploaded_pid))

    def test_create_video(self):
        file_content = b"Test video content"
        file = SimpleUploadedFile("test_video.mp4", file_content)

        video_document = self.document_service.create_video(self.user, file, self.content_type)

        self.assertIsInstance(video_document, TainoDocument)
        self.assertEqual(TainoDocument.objects.count(), 1)
