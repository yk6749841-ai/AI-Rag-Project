import os
import ssl
import urllib3
from dotenv import load_dotenv
from pinecone import Pinecone
from llama_index.core import SimpleDirectoryReader, StorageContext, Settings, VectorStoreIndex
from llama_index.core.node_parser import MarkdownNodeParser
from llama_index.embeddings.cohere import CohereEmbedding
from llama_index.vector_stores.pinecone import PineconeVectorStore

# --- 1. אתחול והגדרות רשת (נטפרי) ---
load_dotenv()
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
ssl._create_default_https_context = ssl._create_unverified_context
os.environ['CURL_CA_BUNDLE'] = ""

# --- 2. הגדרות מודלים ---
# חשוב: input_type="search_document" מיועד לשלב שמירת המסמכים בבסיס הנתונים
Settings.embed_model = CohereEmbedding(
    cohere_api_key=os.getenv("COHERE_API_KEY"),
    model_name="embed-multilingual-v3.0",
    input_type="search_document"
)


def clear_pinecone_index(index_name):
    """מנסה לנקות את האינדקס בבטחה מבלי לקרוס אם הוא כבר ריק"""
    try:
        pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"), ssl_verify=False)
        index = pc.Index(index_name)
        print(f"🔄 מנסה לנקות נתונים ישנים מהאינדקס '{index_name}'...")
        index.delete(delete_all=True)
        print("✅ האינדקס נוקה.")
    except Exception as e:
        # אם ה-Namespace לא קיים, Pinecone מחזיר 404 - אנחנו נתעלם מזה ונמשיך
        if "404" in str(e) or "not found" in str(e).lower():
            print("ℹ️ האינדקס כבר ריק או שלא נמצא Namespace. ממשיך בהעלאה...")
        else:
            print(f"⚠️ הערה (לא קריטית): {e}")


def start_ingestion(directory_path="./docs", index_name="rag-index"):
    # א. ניקוי בסיס הנתונים
    clear_pinecone_index(index_name)

    # ב. טעינת קבצי ה-MD
    print(f"📂 סורק קבצים בתיקיית {directory_path} (כולל תתי-תיקיות)...")

    if not os.path.exists(directory_path):
        print(f"❌ שגיאה קריטית: התיקייה '{directory_path}' לא קיימת במחשב שלך.")
        return

    # הגדרת הסורק: מחפש רק קבצי MD וסורק לעומק (recursive)
    reader = SimpleDirectoryReader(
        input_dir=directory_path,
        required_exts=[".md"],
        recursive=True
    )
    documents = reader.load_data()

    if not documents:
        print("⚠️ אזהרה: לא נמצאו קבצי Markdown בתיקייה שצוינה.")
        return

    print(f"📄 נטענו {len(documents)} קבצים בהצלחה.")

    # ג. פיצול חכם לפי מבנה Markdown (כותרות, פסקאות)
    print("✂️ מפרק את המסמכים לצמתים (Nodes) חכמים...")
    parser = MarkdownNodeParser()
    nodes = parser.get_nodes_from_documents(documents)
    print(f"✅ נוצרו {len(nodes)} צמתים.")

    # ד. חיבור ל-Pinecone והעלאה
    pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"), ssl_verify=False)
    pinecone_index = pc.Index(index_name)
    vector_store = PineconeVectorStore(pinecone_index=pinecone_index)
    storage_context = StorageContext.from_defaults(vector_store=vector_store)

    print(f"🚀 מעלה {len(nodes)} וקטורים ל-Pinecone...")
    VectorStoreIndex(
        nodes,
        storage_context=storage_context,
        show_progress=True
    )
    print("\n✨ תהליך ה-Ingestion הסתיים! המידע מוכן לשימוש ב-APP וב-MAIN.")


if __name__ == "__main__":
    start_ingestion()
