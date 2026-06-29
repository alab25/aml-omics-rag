import os
import logging
from minio import Minio
from minio.error import S3Error

# Configure professional logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

class DataLakeUploader:
    def __init__(self):
        # Connect to your local Docker MinIO instance
        self.client = Minio(
            "localhost:9000",
            access_key="admin",
            secret_key="supersecretpassword",
            secure=False # Set to True in production with HTTPS
        )
        self.bucket_name = "lamba-lab-raw-data"
        self.local_dir = "../../data/raw_pdfs"

    def setup_bucket(self):
        try:
            if not self.client.bucket_exists(self.bucket_name):
                self.client.make_bucket(self.bucket_name)
                logger.info(f"Created new data lake bucket: {self.bucket_name}")
            else:
                logger.info(f"Bucket '{self.bucket_name}' already exists.")
        except S3Error as err:
            logger.error(f"MinIO Error: {err}")

    def sync_files(self):
        logger.info(f"Scanning local directory: {self.local_dir}")
        uploaded_count = 0

        for filename in os.listdir(self.local_dir):
            if filename.endswith(".json") or filename.endswith(".pdf"):
                file_path = os.path.join(self.local_dir, filename)
                
                try:
                    # Upload the file to the MinIO bucket
                    self.client.fput_object(
                        self.bucket_name, 
                        filename, 
                        file_path
                    )
                    logger.info(f"Successfully uploaded: {filename}")
                    uploaded_count += 1
                except S3Error as err:
                    logger.error(f"Failed to upload {filename}. Error: {err}")

        logger.info(f"Sync complete. {uploaded_count} files moved to the Data Lake.")

if __name__ == "__main__":
    uploader = DataLakeUploader()
    uploader.setup_bucket()
    uploader.sync_files()
