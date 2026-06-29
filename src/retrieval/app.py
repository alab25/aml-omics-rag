import streamlit as st
import logging
from qdrant_client import QdrantClient
from langchain_ollama import OllamaLLM
from langchain_core.prompts import PromptTemplate

# Suppress debug logs
logging.getLogger("httpx").setLevel(logging.WARNING)

# 1. Page Config for a Sleek UI
st.set_page_config(page_title="Lamba Lab Copilot", page_icon="🧬", layout="centered")

# 2. Cache the heavy backend so it doesn't reload on every chat message
@st.cache_resource
def load_backend():
    qdrant = QdrantClient("http://localhost:6333")
    qdrant.set_model("sentence-transformers/all-MiniLM-L6-v2")
    llm = OllamaLLM(model="llama3")
    return qdrant, llm

qdrant_client, llm = load_backend()

# 3. Define the Retrieval Function
def retrieve_context(user_query):
    search_results = qdrant_client.query(
        collection_name="aml_literature",
        query_text=user_query,
        limit=3
    )
    
    context_block = ""
    citations = []
    for result in search_results:
        if result.document:
            context_block += f"{result.document}\n\n"
            citations.append(f"PMID: {result.metadata.get('pmid')} - {result.metadata.get('title')}")
            
    # Deduplicate citations just in case
    return context_block, list(set(citations))

# 4. Streamlit UI Setup
st.title("🧬 AML Multi-Omics AI Copilot")
st.markdown("An offline-first clinical research assistant querying Dr. Lamba's lab publications.")

# Initialize chat history in session state
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Welcome to the Lamba Lab AI Copilot. What clinical data can I help you find today?"}
    ]

# Display chat history on rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 5. Chat Input and Generation
if user_query := st.chat_input("Ask a question about pediatric AML..."):
    # Display user message instantly
    st.session_state.messages.append({"role": "user", "content": user_query})
    with st.chat_message("user"):
        st.markdown(user_query)

    # Generate Assistant Response
    with st.chat_message("assistant"):
        context, citations = retrieve_context(user_query)
        
        if not context:
            response_text = "I don't have enough information in my database to answer that."
            st.markdown(response_text)
            st.session_state.messages.append({"role": "assistant", "content": response_text})
        else:
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

            # We use a generator to stream the text and the citations seamlessly together
            def generate_stream():
                for chunk in llm.stream(final_prompt):
                    yield chunk
                
                if citations:
                    yield "\n\n**📚 CITED SOURCES:**\n"
                    for c in citations:
                        yield f"- {c}\n"

            # Stream to UI and automatically save the completed string to history
            full_response = st.write_stream(generate_stream())
            st.session_state.messages.append({"role": "assistant", "content": full_response})
