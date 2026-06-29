import logging
from qdrant_client import QdrantClient

# Configure professional logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

class ClinicalRetriever:
    def __init__(self):
        self.qdrant_client = QdrantClient("http://localhost:6333")
        self.collection_name = "aml_literature"
        
        # We must use the exact same model we used for ingestion
        self.qdrant_client.set_model("sentence-transformers/all-MiniLM-L6-v2")

    
    def search(self, user_query, top_k=3):
        logger.info(f"Executing semantic search for: '{user_query}'")
        
        try:
            search_results = self.qdrant_client.query(
                collection_name=self.collection_name,
                query_text=user_query,
                limit=top_k
            )

            print("\n" + "="*80)
            print(f"🔍 QUERY: {user_query}")
            print("="*80)

            if not search_results:
                print("No relevant clinical context found in the database.")
                return

            for i, result in enumerate(search_results, 1):
                print(f"\n--- MATCH {i} (Confidence Score: {result.score:.4f}) ---")
                print(f"Title: {result.metadata.get('title')}")
                print(f"PMID:  {result.metadata.get('pmid')}")
                
                # FIX: We grab the text directly from the document attribute!
                excerpt = result.document[:400].replace('\n', ' ') if result.document else "No text found."
                print(f"Excerpt: {excerpt}...\n")

        except Exception as e:
            logger.error(f"Retrieval failed: {str(e)}")

if __name__ == "__main__":
    retriever = ClinicalRetriever()
    
    # Test Query 1: Broad clinical concept
    retriever.search("What are the outcomes of pediatric acute myeloid leukemia?", top_k=2)
    
    # Test Query 2: Hyper-specific biological marker (Testing the vector engine's precision)
    retriever.search("How does DNA methylation or epigenomics affect chemotherapy toxicity?", top_k=2)
