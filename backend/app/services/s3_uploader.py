"""
S3/MinIO Backup Uploader (PDCA #23 - Enhancement)

Uploads backups to S3-compatible storage for offsite redundancy.

Features:
- S3/MinIO upload
- Automatic bucket creation
- Retention policy in cloud
- Encryption at rest
- Multi-part upload for large files
"""

import logging
import asyncio
from typing import Optional, Dict, Any
from pathlib import Path
from datetime import datetime, timedelta
import boto3
from botocore.exceptions import ClientError
from botocore.config import Config

logger = logging.getLogger(__name__)


class S3Uploader:
    """
    Uploads backups to S3/MinIO for offsite storage.

    Supports both AWS S3 and MinIO (S3-compatible).
    """

    def __init__(
        self,
        endpoint_url: str = "http://minio:9000",
        access_key: str = "optiflow",
        secret_key: str = "optiflow_secret",
        bucket_name: str = "optiflow-backups",
        region: str = "us-east-1"
    ):
        self.bucket_name = bucket_name

        # Configure S3 client
        self.s3_client = boto3.client(
            's3',
            endpoint_url=endpoint_url,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region,
            config=Config(
                signature_version='s3v4',
                s3={'addressing_style': 'path'}
            )
        )

        logger.info(f"S3 uploader initialized (endpoint: {endpoint_url}, bucket: {bucket_name})")

    async def ensure_bucket_exists(self):
        """Create bucket if it doesn't exist."""
        try:
            self.s3_client.head_bucket(Bucket=self.bucket_name)
            logger.debug(f"Bucket {self.bucket_name} exists")

        except ClientError as e:
            error_code = e.response['Error']['Code']

            if error_code == '404':
                # Bucket doesn't exist, create it
                logger.info(f"Creating bucket: {self.bucket_name}")

                try:
                    self.s3_client.create_bucket(Bucket=self.bucket_name)
                    logger.info(f"✅ Bucket {self.bucket_name} created")

                    # Enable versioning
                    self.s3_client.put_bucket_versioning(
                        Bucket=self.bucket_name,
                        VersioningConfiguration={'Status': 'Enabled'}
                    )

                    # Set lifecycle policy for retention
                    await self._set_lifecycle_policy()

                except ClientError as create_error:
                    logger.error(f"Failed to create bucket: {create_error}")
                    raise

            else:
                logger.error(f"Error checking bucket: {e}")
                raise

    async def _set_lifecycle_policy(self):
        """Set lifecycle policy for backup retention."""
        try:
            lifecycle_policy = {
                'Rules': [
                    {
                        'ID': 'DeleteOldBackups',
                        'Status': 'Enabled',
                        'Filter': {'Prefix': ''},
                        'Expiration': {
                            'Days': 365  # Keep for 1 year
                        },
                        'Transitions': [
                            {
                                'Days': 30,
                                'StorageClass': 'GLACIER'  # Move to cold storage after 30 days
                            }
                        ]
                    }
                ]
            }

            self.s3_client.put_bucket_lifecycle_configuration(
                Bucket=self.bucket_name,
                LifecycleConfiguration=lifecycle_policy
            )

            logger.info("✅ Lifecycle policy set on bucket")

        except ClientError as e:
            logger.warning(f"Could not set lifecycle policy (may not be supported): {e}")

    async def upload_backup(
        self,
        local_path: Path,
        service: str,
        metadata: Optional[Dict[str, str]] = None
    ) -> bool:
        """
        Upload backup file to S3/MinIO.

        Args:
            local_path: Path to local backup file
            service: Service name (postgresql, influxdb, etc.)
            metadata: Optional metadata to attach

        Returns:
            True if upload successful
        """
        try:
            await self.ensure_bucket_exists()

            # Generate S3 key (path in bucket)
            timestamp = datetime.utcnow().strftime("%Y/%m/%d")
            s3_key = f"{service}/{timestamp}/{local_path.name}"

            logger.info(f"Uploading {local_path.name} to s3://{self.bucket_name}/{s3_key}")

            # Prepare metadata
            upload_metadata = {
                'service': service,
                'backup_date': datetime.utcnow().isoformat(),
                'source_host': 'optiflow-backend'
            }

            if metadata:
                upload_metadata.update(metadata)

            # Upload with multipart for files > 100MB
            file_size = local_path.stat().st_size

            if file_size > 100 * 1024 * 1024:  # 100MB
                logger.info(f"Using multipart upload for {file_size / 1024 / 1024:.2f}MB file")
                await self._multipart_upload(local_path, s3_key, upload_metadata)
            else:
                # Simple upload
                with open(local_path, 'rb') as f:
                    self.s3_client.put_object(
                        Bucket=self.bucket_name,
                        Key=s3_key,
                        Body=f,
                        Metadata=upload_metadata,
                        ServerSideEncryption='AES256'  # Encrypt at rest
                    )

            logger.info(f"✅ Upload completed: {s3_key}")
            return True

        except Exception as e:
            logger.error(f"Upload failed: {e}", exc_info=True)
            return False

    async def _multipart_upload(
        self,
        local_path: Path,
        s3_key: str,
        metadata: Dict[str, str]
    ):
        """Perform multipart upload for large files."""
        # Initiate multipart upload
        response = self.s3_client.create_multipart_upload(
            Bucket=self.bucket_name,
            Key=s3_key,
            Metadata=metadata,
            ServerSideEncryption='AES256'
        )

        upload_id = response['UploadId']

        try:
            parts = []
            part_size = 100 * 1024 * 1024  # 100MB parts
            part_number = 1

            with open(local_path, 'rb') as f:
                while True:
                    data = f.read(part_size)

                    if not data:
                        break

                    # Upload part
                    part_response = self.s3_client.upload_part(
                        Bucket=self.bucket_name,
                        Key=s3_key,
                        PartNumber=part_number,
                        UploadId=upload_id,
                        Body=data
                    )

                    parts.append({
                        'PartNumber': part_number,
                        'ETag': part_response['ETag']
                    })

                    logger.debug(f"Uploaded part {part_number}")
                    part_number += 1

            # Complete multipart upload
            self.s3_client.complete_multipart_upload(
                Bucket=self.bucket_name,
                Key=s3_key,
                UploadId=upload_id,
                MultipartUpload={'Parts': parts}
            )

            logger.info(f"Multipart upload completed ({len(parts)} parts)")

        except Exception as e:
            # Abort multipart upload on error
            self.s3_client.abort_multipart_upload(
                Bucket=self.bucket_name,
                Key=s3_key,
                UploadId=upload_id
            )

            logger.error(f"Multipart upload failed: {e}")
            raise

    async def list_backups(self, service: Optional[str] = None) -> list:
        """
        List backups in S3/MinIO.

        Args:
            service: Filter by service name (None = all)

        Returns:
            List of backup objects
        """
        try:
            prefix = f"{service}/" if service else ""

            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix
            )

            backups = []

            if 'Contents' in response:
                for obj in response['Contents']:
                    backups.append({
                        'key': obj['Key'],
                        'size': obj['Size'],
                        'last_modified': obj['LastModified'].isoformat(),
                        'storage_class': obj.get('StorageClass', 'STANDARD')
                    })

            return backups

        except Exception as e:
            logger.error(f"Failed to list backups: {e}")
            return []

    async def download_backup(self, s3_key: str, local_path: Path) -> bool:
        """
        Download backup from S3/MinIO.

        Args:
            s3_key: S3 object key
            local_path: Local path to save file

        Returns:
            True if download successful
        """
        try:
            logger.info(f"Downloading s3://{self.bucket_name}/{s3_key} to {local_path}")

            with open(local_path, 'wb') as f:
                self.s3_client.download_fileobj(
                    Bucket=self.bucket_name,
                    Key=s3_key,
                    Fileobj=f
                )

            logger.info(f"✅ Download completed")
            return True

        except Exception as e:
            logger.error(f"Download failed: {e}", exc_info=True)
            return False

    def get_stats(self) -> Dict[str, Any]:
        """Get S3/MinIO statistics."""
        try:
            # Get bucket size
            response = self.s3_client.list_objects_v2(Bucket=self.bucket_name)

            total_size = 0
            total_objects = 0

            if 'Contents' in response:
                for obj in response['Contents']:
                    total_size += obj['Size']
                    total_objects += 1

            return {
                "bucket_name": self.bucket_name,
                "total_objects": total_objects,
                "total_size_bytes": total_size,
                "total_size_gb": total_size / 1024 / 1024 / 1024
            }

        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return {
                "bucket_name": self.bucket_name,
                "error": str(e)
            }


# Global instance
_s3_uploader: Optional[S3Uploader] = None


def get_s3_uploader() -> S3Uploader:
    """Get global S3 uploader instance."""
    global _s3_uploader

    if _s3_uploader is None:
        _s3_uploader = S3Uploader()

    return _s3_uploader
