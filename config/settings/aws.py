from storages.backends.s3 import S3StaticStorage, S3Storage

from . import TESTING
from .base import env, BASE_DIR

USE_AWS_S3 = env.bool("USE_AWS_S3", default=False)

if TESTING:
    USE_AWS_S3 = False


class TainoStaticFileS3Storage(S3Storage):
    bucket_name = env.str("STATIC_FILE_BUCKET_NAME", "taino-static-bucket")
    custom_domain = env.str("S3_DOMAIN", None)
    endpoint_url = env.str("S3_ENDPOINT_URL", "https://s3.ir-thr-at1.arvanstorage.ir")
    default_acl = "public-read"
    location = "static"
    file_overwrite = False
    querystring_auth = False  # todo change


class ArvanCloudMediaStorage(S3Storage):
    bucket_name = env.str("MEDIA_FILE_BUCKET_NAME", "taino-media-bucket")
    endpoint_url = env.str("S3_MEDIA_ENDPOINT_URL", "https://s3.ir-thr-at1.arvanstorage.com")
    custom_domain = env.str("S3_MEDIA_DOMAIN", None)
    location = "media"
    file_overwrite = False
    default_acl = "public-read"
    querystring_auth = True
    querystring_expire = 3600 * 24 * 7  # 7 days


class TainoPrivateStorage(S3Storage):
    bucket_name = env.str("PRIVATE_BUCKET_NAME", "taino-private-bucket")
    endpoint_url = env.str("PRIVATE_ENDPOINT_URL", "https://s3.ir-thr-at1.arvanstorage.com")
    location = "private"
    file_overwrite = False
    default_acl = "private"
    querystring_auth = True
    querystring_expire = 3600  # 1 hour


class TainoVideoS3Storage(S3Storage):
    bucket_name = env.str("VIDEO_BUCKET_NAME", "s3video-bucket")
    endpoint_url = env.str("VIDEO_ENDPOINT_URL", "https://s3.ir-thr-at1.arvanstorage.com")
    custom_domain = env.str("S3_VIDEO_DOMAIN", None)
    location = "video"
    default_acl = "public-read"
    file_overwrite = False


if USE_AWS_S3:
    DEFAULT_FILE_STORAGE = "storages.backends.s3boto3.S3Boto3Storage"
    # STORAGES = {
    #     "default": {
    #         # "BACKEND": "config.settings.ArvanCloudMediaStorage",
    #         "BACKEND": "storages.backends.s3boto3.S3Boto3Storage",
    #         # "OPTIONS": {},
    #     },
    #     "staticfiles": {
    #         # "BACKEND": "config.settings.TainoStaticFileS3Storage",
    #         "BACKEND": "storages.backends.s3boto3.S3Boto3Storage",
    #         # "BACKEND": "django.core.files.storage.FileSystemStorage",
    #         # "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    #         # "BACKEND": "config.settings.TainoStaticFileS3Storage",
    #     },
    # }

    # AWS_ACCESS_KEY_ID = env.str("AWS_ACCESS_KEY_ID", default="dummykey")
    AWS_S3_ACCESS_KEY_ID = env.str("AWS_S3_ACCESS_KEY_ID", default="dummykey")
    # AWS_SECRET_ACCESS_KEY = env.str("AWS_SECRET_ACCESS_KEY", default="dummykey")
    AWS_S3_SECRET_ACCESS_KEY = env.str("AWS_S3_SECRET_ACCESS_KEY", default="dummykey")
    AWS_S3_FILE_OVERWRITE = False
    AWS_STORAGE_BUCKET_NAME = env.str("AWS_STORAGE_BUCKET_NAME", "taino-bucket")
    # ARVAN_ACCESS_KEY_ID = env.str("ARVAN_ACCESS_KEY_ID")
    # ARVAN_SECRET_ACCESS_KEY = env.str("ARVAN_SECRET_ACCESS_KEY")
    AWS_S3_ENDPOINT_URL = env.str("S3_ENDPOINT_URL", "https://s3.ir-thr-at1.arvanstorage.com")
    # AWS_DEFAULT_ACL = None
    AWS_S3_REGION_NAME = "ir-thr-at1"
    AWS_SERVICE_NAME = "s3"
    AWS_LOCAL_STORAGE = f"{BASE_DIR}/mediafiles/aws/"
    AWS_STORAGE_REGION_NAME = env("AWS_STORAGE_REGION_NAME", cast=str)
    AWS_DEFAULT_ACL = env("AWS_DEFAULT_ACL", cast=str)
    AWS_S3_SIGNATURE_VERSION = 's3v4'


    # AWS_QUERYSTRING_AUTH = True
    # AWS_QUERYSTRING_EXPIRE = 600  # todo
    #
    # AWS_CLOUDFRONT_KEY = env.str("AWS_CLOUDFRONT_KEY", default="dummy", multiline=True)
    # AWS_CLOUDFRONT_KEY_ID = env.str("AWS_CLOUDFRONT_KEY_ID", default="dummy")
