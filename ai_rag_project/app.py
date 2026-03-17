import gradio as gr
import os
import ssl
import urllib3
import json
import asyncio
from dotenv import load_dotenv
from pinecone import Pinecone

from llama_index.core import VectorStoreIndex, Settings
from llama_index.core.llms import ChatMessage
from llama_index.core.workflow import Event, StartEvent, StopEvent, Workflow, step
from llama_index.embeddings.cohere import CohereEmbedding
from llama_index.llms.cohere import Cohere
from llama_index.vector_stores.pinecone import PineconeVectorStore
from llama_index.core.memory import ChatMemoryBuffer
from llama_index.core.schema import NodeWithScore, TextNode

# --- 1. שחזור כלי הציור של ה-Workflow ---
try:
    from llama_index.utils.workflow import draw_all_possible_flows
except ImportError:
    try:
        from llama_index.core.workflow.utils import draw_all_possible_flows
    except ImportError:
        draw_all_possible_flows = None

# --- הגדרות רשת (נטפרי) ---
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

# טמפרטורה נמוכה ו max_tokens גבוה כדי שה-JSON ייצא תקין ורחב
Settings.llm = Cohere(
    api_key=os.getenv("COHERE_API_KEY"),
    model="command-r-08-2024",
    temperature=0.0,
    max_tokens=1000
)

# --- חיבור ל-Pinecone ---
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"), ssl_verify=False)
pinecone_index = pc.Index("rag-index")
vector_store = PineconeVectorStore(pinecone_index=pinecone_index)
global_index = VectorStoreIndex.from_vector_store(vector_store=vector_store)


# --- הגדרת אירועים (Events) משודרגת לשלב ג' ---
class ValidationEvent(Event):
    query: str


class RouterEvent(Event):
    query: str
    source: str  # 'PINECONE' or 'JSON'
    data_type: str = None  # 'rules' or 'decisions'


class RetrievalEvent(Event):
    nodes: list
    query: str


# --- 2. ה-Workflow המשודרג עם הנתב המוטמע ---
class ChefRAGWorkflow(Workflow):
    def __init__(self, timeout=180, *args, **kwargs):
        super().__init__(timeout=timeout, *args, **kwargs)
        # סימילריות גבוהה כדי לקבל כמה שיותר חוקים רלוונטיים מ-Pinecone
        self.retriever = global_index.as_retriever(similarity_top_k=4)
        # זיכרון מספיק גדול כדי לזכור את כל הרשימה שחילצנו
        self.memory = ChatMemoryBuffer.from_defaults(token_limit=1500)

    @step
    async def validate_input(self, ev: StartEvent) -> ValidationEvent | StopEvent:
        """צעד א': בדיקת תקינות הקלט. אם לא תקין, יוצאים עם StopEvent."""
        query = ev.query.strip() if ev.query else ""
        if len(query) < 2:
            return StopEvent(result="אשמח לעזור. אנא כתוב שאלה ברורה.")
        return ValidationEvent(query=query)

    @step
    async def router(self, ev: ValidationEvent) -> RouterEvent:
        """צעד הנתב (הלב של שלב ג'): מחליט אם המשתמש מחפש רשימות חוקים או חיפוש סמנטי."""
        router_prompt = (
            "אתה נתב חכם למערכת Chef-AI. תפקידך לנתח את כוונת המשתמש.\n"
            "אם המשתמש מבקש:\n"
            "1. רשימה של חוקים, הנחיות, דרישות או כללים הקשורים לפיתוח, עיצוב או קוד -> ענה 'JSON_RULES'.\n"
            "2. רשימה של החלטות טכנולוגיות, בחירות ארכיטקטוניות, כלים או פלטפורמות שנבחרו -> ענה 'JSON_DECISIONS'.\n"
            "3. שאלה כללית על המערכת, הסברים של 'איך' או 'למה', או שאלה שלא כוללת בקשת רשימה -> ענה 'PINECONE'.\n\n"
            f"השאלה: {ev.query}\n"
            "ענה במילה אחת בלבד."
        )

        # הקוד החדש והתקין:
        messages = [ChatMessage(role="user", content=router_prompt)]
        response = await Settings.llm.achat(messages)
        intent = response.message.content.strip().upper()

        # אנחנו מדפיסים לקונסול כדי שנדע מה הנתב החליט
        if "JSON_RULES" in intent:
            print(f"📊 הנתב החליט: השאלה היא על חוקים (JSON).")
            return RouterEvent(query=ev.query, source="JSON", data_type="rules")
        elif "JSON_DECISIONS" in intent:
            print(f"📊 הנתב החליט: השאלה היא על החלטות (JSON).")
            return RouterEvent(query=ev.query, source="JSON", data_type="decisions")
        else:
            print("🔍 הנתב החליט: השאלה היא כללית (PINECONE).")
            return RouterEvent(query=ev.query, source="PINECONE")

    @step
    async def retrieve_info(self, ev: RouterEvent) -> RetrievalEvent:
        """שלב שליפת המידע: מחליט מאיפה להביא את הנתונים על סמך החלטת הנתב."""
        if ev.source == "JSON":
            print(f"📂 שולף נתונים מקובץ ה-JSON (סוג: {ev.data_type})...")
            try:
                # קריאה מהירה של הקובץ שייצרת בעזרת ה extract_data
                with open("extracted_data.json", "r", encoding="utf-8") as f:
                    data = json.load(f)

                # שליפת הרשימה המתאימה מהקובץ
                items = data.get(ev.data_type, [])
                if not items:
                    print(f"⚠️ אזהרה: לא נמצאו נתונים מסוג {ev.data_type} ב-JSON.")
                    return RetrievalEvent(nodes=[], query=ev.query)

                # בניית טקסט אחד ארוך ומובנה שיהווה את ההקשר (Context)
                context = f"להלן רשימה מלאה של ה-{ev.data_type} המופיעים במסמכים:\n"
                for item in items:
                    if ev.data_type == "rules":
                        context += f"- חוק {item['id']}: {item['rule']} (תחום: {item['scope']})\n"
                    else:
                        context += f"- החלטה {item['id']}: {item['title']} - {item['summary']}\n"

                # עטיפה ב-Node עם ציון 1.0 כי זה ידע מובנה ומדויק
                node = NodeWithScore(node=TextNode(text=context), score=1.0)
                return RetrievalEvent(nodes=[node], query=ev.query)

            except Exception as e:
                print(f"❌ שגיאה חמורה בקריאת JSON: {e}")
                # אם ה-JSON נכשל, ננסה כגיבוי ב-Pinecone (שזה מה שהיה עובד עד עכשיו)
                nodes = await self.retriever.aretrieve(ev.query)
                return RetrievalEvent(nodes=nodes, query=ev.query)

        else:
            print("🔍 מבצע חיפוש סמנטי ב-Pinecone...")
            nodes = await self.retriever.aretrieve(ev.query)
            return RetrievalEvent(nodes=nodes, query=ev.query)

    @step
    async def synthesize_response(self, ev: RetrievalEvent) -> StopEvent:
        """השלב הסופי: יצירת התשובה והזיכרון. זהו השלב שסוגר את ה-Workflow."""
        # סינון לפי רמת רלוונטיות (מלבד מקרי JSON שקיבלו ציון 1.0)
        relevant_nodes = [n for n in ev.nodes if n.score > 0.25]

        if not relevant_nodes:
            return StopEvent(result="המידע אינו מופיע במסמכי המערכת.")

        context_str = "\n---\n".join([n.node.get_content() for n in relevant_nodes])
        # שליפת היסטוריית השיחה
        history = self.memory.get_all()

        system_instruction = (
            "אתה עוזר AI טכני, חכם, נעים וידידותי של מערכת Chef-AI. "
            "המטרה היחידה שלך היא לענות על שאלות המשתמש **אך ורק** מתוך 'הקשר מהמסמכים' המצורף.\n\n"

            "כלל הברזל (היחיד והמוחלט):\n"
            "קרא את השאלה, וחפש את התשובה בטקסט המצורף.\n"
            "1. אם המידע נמצא שם: ענה בצורה מקצועית, מדויקת, ובשפה נעימה וטבעית (בעברית). תרגם מונחים מאנגלית לעברית, למעט מונחים טכניים (כמו CSS, API).\n"
            "2. אם המידע לא נמצא שם (כולל בקשות למתכונים, ידע כללי מבחוץ, או שאלות לא קשורות): חל איסור מוחלט להמציא! פשוט תענה בחיוך ובנימוס משהו כמו: 'סליחה, אבל המידע הזה לא מופיע במסמכים שלי' או 'היי, אני עוזר טכני ואין לי נתונים על זה'.\n\n"

            "סגנון ואישיות:\n"
            "דבר כמו קולגה לצוות. היה טבעי, אנושי וזורם. אל תהיה רובוטי בשום צורה, ואל תשתמש במשפטי פתיחה קבועים כמו 'בהחלט, להלן התשובה'. פשוט פתח בטבעיות (למשל 'בשמחה!', או ישר לעניין)."
        )

        user_prompt = f"הקשר מהמסמכים:\n{context_str}\n\nשאלה: {ev.query}\nתשובה:"

        messages = [
            ChatMessage(role="system", content=system_instruction),
            *history,
            ChatMessage(role="user", content=user_prompt)
        ]

        response = await Settings.llm.achat(messages=messages)
        final_answer = response.message.content.strip()

        # עדכון הזיכרון בתשובה החדשה לשמירה להודעה הבאה
        self.memory.put(ChatMessage(role="user", content=ev.query))
        self.memory.put(ChatMessage(role="assistant", content=final_answer))

        return StopEvent(result=final_answer)


# --- ממשק Gradio ---
# יצירת ה-Workflow מחוץ לפונקציה כדי לשמור על הזיכרון הפנימי (State)
chef_workflow = ChefRAGWorkflow()


async def chat_fn(message, history):
    try:
        # הפעלת ה-Workflow המשודרג
        result = await chef_workflow.run(query=message)
        return str(result).strip()
    except Exception as e:
        return f"היתה שגיאה בטעינת התשובה, נסה שנית"


with gr.Blocks(title="Chef-AI") as demo:
    gr.HTML("<div style='text-align: center;'><h1>👨‍🍳 Chef-AI Expert Assistant</h1></div>")
    gr.ChatInterface(
        fn=chat_fn,
        chatbot=gr.Chatbot(rtl=True, avatar_images=(None, "https://cdn-icons-png.flaticon.com/512/1830/1830839.png")),
        textbox=gr.Textbox(placeholder="שאל אותי על חוקים, החלטות או ארכיטקטורה...", container=False, scale=7)
    )

# --- 3. שחזור ושדרוג הציור בהפעלה ---
if __name__ == "__main__":
    if draw_all_possible_flows:
        try:
            # אנחנו מציירים את ה-Workflow כדי לראות את ה-Router החדש
            wf_to_draw = ChefRAGWorkflow()
            draw_all_possible_flows(wf_to_draw, filename="workflow_design.html")
            print("✅ תרשים ה-Workflow נוצר בהצלחה (עם ה-Router החדש!): workflow_design.html")
        except Exception as e:
            print(f"⚠️ הערה: לא ניתן היה לצייר את ה-Workflow: {e}")

    demo.launch(share=False, theme="soft")