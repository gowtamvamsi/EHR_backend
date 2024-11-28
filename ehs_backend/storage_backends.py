from storages.backends.s3boto3 import S3Boto3Storage
from django.conf import settings

class StaticStorage(S3Boto3Storage):
    location = 'static'
    default_acl = 'public-read'
    file_overwrite = True
    custom_domain = f'{settings.AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com'

class MediaStorage(S3Boto3Storage):
    location = 'media'
    default_acl = 'private'
    file_overwrite = False
    custom_domain = None  # Use signed URLs for private access

    def get_signed_url(self, object_name, expiration=3600):
        """Generate a signed URL for private media files"""
        return self.connection.generate_presigned_url(
            'get_object',
            Params={
                'Bucket': self.bucket_name,
                'Key': self._normalize_name(self._clean_name(object_name)),
            },
            ExpiresIn=expiration
        )