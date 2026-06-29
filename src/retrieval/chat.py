import logging
import sys
from qdrant_client import QdrantClient
from langchain_ollama import OllamaLLM
from langchain_core.prompts import PromptTemplate

# Suppress debug logs for a cleaner chat interface
logging.getLogger("httpx").setLevel(logging.WARNING)

class ClinicalRAGCopilot:
    def __init__(self):
        self.qdrant_client = QdrantClient("http://localhost:6333")
        self.collection_name = "aml_literature"
        self.qdrant_client.set_model("sentence-transformers/all-MiniLM-L6-v2")
        
        # Using the modern, non-deprecated LangChain package
        self.llm = OllamaLLM(model="llama3")

    def retrieve_context(self, user_query):
        search_results = self.qdrant_client.query(
            collection_name=self.collection_name,
            query_text=user_query,
            limit=3
        )
        
        context_block = ""
        citations = []
        for result in search_results:
            if result.document:
                context_block += f"{result.document}\n\n"
                citations.append(f"PMID: {result.metadata.get('pmid')} - {result.metadata.get('title')}")
                
        return context_block, citations

    def chat(self, user_query):
        print("\n" + "="*80)
        print("🧠 Lamba Lab AI Copilot is thinking...")
        print("="*80)
        
        context, citations = self.retrieve_context(user_query)
        
        if not context:
            print("I don't have enough information in my database to answer that.")
            return

        template = """
        You are a highly intelligent clinical research assistant for the Lamba Lab at the University of Florida. 
        Your goal is to answer questions about pediatric Acute Myeloid Leukemia (AML) and pharmacogenomics.
        
        Use ONLY the following context retrieved from Dr. Lamba's research to answer the question. 
        If the answer cannot be found in the context, do not guess. Simply state that the data is not available.
        
        CONTEXT:
        {context}
        
        QUESTION: {question}
        
        ANSWER:
        """
        
        prompt = PromptTemplate(template=template, input_variables=["context", "question"])
        final_prompt = prompt.format(context=context, question=user_query)

        print("\n💡 AI ANSWER:\n")
        
        # This streams the text to the terminal token-by-token
        try:
            for chunk in self.llm.stream(final_prompt):
                print(chunk, end="", flush=True)
        except Exception as e:
            print(f"\n[Error communicating with local LLM: {str(e)}]")
        
        print("\n\n📚 CITED SOURCES:")
        for citation in citations:
            print(f"- {citation}")

if __name__ == "__main__":
    copilot = ClinicalRAGCopilot()
    
    print("Welcome to the AML Multi-Omics RAG Copilot (Local Instance)")
    while True:
        query = input("\nAsk a question (or type 'exit'): ")
        if query.lower() == 'exit':
            break
        copilot.chat(query)