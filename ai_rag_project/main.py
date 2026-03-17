import os
import ssl
import urllib3
from dotenv import load_dotenv
from pinecone import Pinecone
from llama_index.core import VectorStoreIndex, Settings, PromptTemplate
from llama_index.embeddings.cohere import CohereEmbedding
from llama_index.llms.cohere import Cohere
from llama_index.vector_stores.pinecone import PineconeVectorStore

# --- הגדרות רשת ---
load_dotenv()
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
ssl._create_default_https_context = ssl._create_unverified_context
os.environ['CURL_CA_BUNDLE'] = ""

# --- הגדרות מודלים ---
Settings.embed_model = CohereEmbedding(
    cohere_api_key=os.getenv("COHERE_API_KEY"),
    model_name="embed-multilingual-v3.0",
    input_type="search_query"
)

Settings.llm = Cohere(
    api_key=os.getenv("COHERE_API_KEY"),
    model="command-r-08-2024",
    temperature=0.2
)


def get_chef_index():
    pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"), ssl_verify=False)
    pinecone_index = pc.Index("rag-index")
    vector_store = PineconeVectorStore(pinecone_index=pinecone_index)
    return VectorStoreIndex.from_vector_store(vector_store=vector_store)


if __name__ == "__main__":
    try:
        index = get_chef_index()

        qa_prompt = PromptTemplate(
            "ענה על השאלה בעברית על בסיס ההקשר בלבד.\n\nהקשר:\n{context_str}\n\nשאלה: {query_str}\nתשובה:"
        )

        query_engine = index.as_query_engine(
            similarity_top_k=4,
            text_qa_template=qa_prompt
        )

        question = "למה בחרנו ב-MongoDB?"
        print(f"\n🔍 בודק: {question}")
        response = query_engine.query(question)
        print(f"\nתשובה:\n{response}")

        print("\n📚 מקורות:")
        for node in response.source_nodes:
            print(f"- [Score: {node.score:.4f}] {node.node.get_content()[:80]}...")

    except Exception as e:
        print(f"❌ שגיאה: {e}")
