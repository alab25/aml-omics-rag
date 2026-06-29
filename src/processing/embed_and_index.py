import os
import json
import logging
from minio import Minio
from qdrant_client import QdrantClient

# Configure professional logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

class VectorIndexingPipeline:
    def __init__(self):
        self.minio_client = Minio(
            "localhost:9000",
            access_key="admin",
            secret_key="supersecretpassword",
            secure=False
        )
        self.bucket_name = "lamba-lab-raw-data"
        self.qdrant_client = QdrantClient("http://localhost:6333")
        self.collection_name = "aml_literature"

    def process_and_index(self):
        logger.info("Starting processing pipeline from Data Lake to Vector DB...")
        
        try:
            # 1. Bruteforce wipe the old collection (ignore if it doesn't exist)
            try:
                self.qdrant_client.delete_collection(self.collection_name)
                logger.info(f"Cleared old collection '{self.collection_name}' for a fresh sync.")
            except Exception:
                pass # Collection didn't exist, which is perfectly fine

            # 2. Tell Qdrant to use our local model for automatic embedding
            self.qdrant_client.set_model("sentence-transformers/all-MiniLM-L6-v2")

            # 3. List all documents inside the raw bucket
            objects = self.minio_client.list_objects(self.bucket_name, recursive=True)
            
            documents = []
            metadata = []
            ids = []
            idx = 1

            for obj in objects:
                if not obj.object_name.endswith(".json"):
                    continue
                
                response = self.minio_client.get_object(self.bucket_name, obj.object_name)
                data = json.loads(response.read().decode('utf-8'))
                response.close()
                response.release_conn()

                if not data.get('abstract') or data['abstract'] == "No abstract available":
                    continue

                text_to_embed = f"Title: {data['title']}\nAbstract: {data['abstract']}"
                
                documents.append(text_to_embed)
                metadata.append({
                    "pmid": data["pmid"],
                    "title": data["title"],
                    "ingestion_date": data["ingestion_date"]
                })
                ids.append(idx)
                idx += 1

            if documents:
                # 4. The .add() method automatically creates the perfectly formatted collection!
                self.qdrant_client.add(
                    collection_name=self.collection_name,
                    documents=documents,
                    metadata=metadata,
                    ids=ids
                )
                logger.info(f"Successfully embedded and indexed {len(documents)} documents into Qdrant.")
            else:
                logger.warning("No valid text documents found to index.")

        except Exception as e:
            logger.error(f"Pipeline execution failed: {str(e)}")

if __name__ == "__main__":
    pipeline = VectorIndexingPipeline()
    pipeline.process_and_index()