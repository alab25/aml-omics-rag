import os
import json
import logging
from datetime import datetime
from Bio import Entrez

# Configure professional logging format
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Entrez requires an email to monitor API usage thresholds
Entrez.email = "aatg2021@gmail.com"  # CHANGE THIS TO YOUR EMAIL

class PubMedHarvester:
    def __init__(self, search_query, max_results=20):
        self.search_query = search_query
        self.max_results = max_results
        self.output_dir = "../../data/raw_pdfs"
        os.makedirs(self.output_dir, exist_ok=True)

    def search_pubmed(self):
        logger.info(f"Initiating PubMed search for query: {self.search_query}")
        try:
            handle = Entrez.esearch(db="pubmed", sort="pub date", retmax=self.max_results, term=self.search_query)
            results = Entrez.read(handle)
            handle.close()
            
            id_list = results.get("IdList", [])
            logger.info(f"Search successful. Retrieved {len(id_list)} publication IDs.")
            return id_list
        except Exception as e:
            logger.error(f"Failed to execute PubMed search: {str(e)}")
            return []

    def fetch_details(self, id_list):
        if not id_list:
            logger.warning("No publication IDs provided for fetching metadata.")
            return

        try:
            ids = ",".join(id_list)
            handle = Entrez.efetch(db="pubmed", retmode="xml", id=ids)
            papers = Entrez.read(handle)
            handle.close()

            for paper in papers.get('PubmedArticle', []):
                medline = paper['MedlineCitation']
                article = medline['Article']
                title = article['ArticleTitle']
                pmid = str(medline['PMID'])
                
                abstract_text = ""
                if 'Abstract' in article:
                    abstract_text = " ".join(
                        [str(text) for text in article['Abstract']['AbstractText']]
                    )

                filename = os.path.join(self.output_dir, f"PMID_{pmid}.json")
                metadata = {
                    "pmid": pmid,
                    "title": title,
                    "abstract": abstract_text,
                    "ingestion_date": datetime.now().isoformat()
                }
                
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(metadata, f, indent=4)
                
                logger.info(f"Successfully processed and stored metadata for PMID: {pmid}")
                
        except Exception as e:
            logger.error(f"Error fetching detailed records from PubMed: {str(e)}")

if __name__ == "__main__":
    target_query = '("Lamba J"[Author] OR "Lamba Jatinder"[Author]) AND ("AML" OR "Leukemia" OR "Pharmacogenomics")'
    harvester = PubMedHarvester(search_query=target_query, max_results=10)
    
    publication_ids = harvester.search_pubmed()
    if publication_ids:
        harvester.fetch_details(publication_ids)
        logger.info("Ingestion pipeline execution finished successfully.")
