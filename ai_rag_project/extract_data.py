import os
import ssl
import urllib3
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from typing import List

from llama_index.core import SimpleDirectoryReader
from llama_index.llms.cohere import Cohere
from llama_index.core.output_parsers import PydanticOutputParser
from llama_index.core.llms import ChatMessage  # הוספנו את זה

# --- 1. הגדרות רשת (נטפרי) ---
load_dotenv()
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
ssl._create_default_https_context = ssl._create_unverified_context
os.environ['CURL_CA_BUNDLE'] = ""

# --- 2. הגדרת המודל ---
llm = Cohere(
    api_key=os.getenv("COHERE_API_KEY"),
    model="command-r-08-2024",
    temperature=0.0
)


# --- 3. הגדרת מבנה הנתונים ---
class Decision(BaseModel):
    id: str = Field(description="מזהה ייחודי קצר")
    title: str = Field(description="כותרת קצרה")
    summary: str = Field(description="תיאור")
    source_file: str = Field(description="נתיב הקובץ")


class Rule(BaseModel):
    id: str = Field(description="מזהה ייחודי")
    rule: str = Field(description="ההנחיה")
    scope: str = Field(description="תחום")
    source_file: str = Field(description="נתיב הקובץ")


class ExtractedData(BaseModel):
    decisions: List[Decision] = Field(default_factory=list)
    rules: List[Rule] = Field(default_factory=list)


# --- 4. המנוע המעודכן ---
def extract_structured_data():
    print("📂 מתחיל לקרוא מסמכים...")

    try:
        documents = SimpleDirectoryReader(input_dir="./docs", required_exts=[".md"], recursive=True).load_data()
        print(f"✅ נטענו {len(documents)} מסמכים.")
    except Exception as e:
        print(f"❌ שגיאה בטעינה: {e}")
        return

    parser = PydanticOutputParser(ExtractedData)
    format_instructions = parser.get_format_string()

    all_decisions = []
    all_rules = []

    for doc in documents:
        file_path = doc.metadata.get('file_path', 'unknown')
        print(f"⏳ מעבד: {file_path}...")

        prompt_str = f"""
        חלץ החלטות טכניות וחוקי פיתוח מהטקסט הבא.
        חובה להחזיר JSON בלבד לפי המבנה הזה:
        {format_instructions}

        נתיב קובץ לשדה source_file: {file_path}
        טקסט: {doc.text}
        """

        try:
            # שימוש ב-CHAT במקום ב-COMPLETE (התיקון הקריטי)
            messages = [ChatMessage(role="user", content=prompt_str)]
            response = llm.chat(messages)

            # שליפת הטקסט מתוך האובייקט החדש
            raw_text = response.message.content

            structured_response = parser.parse(raw_text)
            all_decisions.extend(structured_response.decisions)
            all_rules.extend(structured_response.rules)
            print("   ✅ הצליח!")

        except Exception as e:
            print(f"   ⚠️ שגיאה: {e}")

    final_data = ExtractedData(decisions=all_decisions, rules=all_rules)

    with open("extracted_data.json", "w", encoding="utf-8") as f:
        f.write(final_data.model_dump_json(indent=4))

    print(f"\n🎉 הסתיים! הקובץ extracted_data.json מוכן.")


if __name__ == "__main__":
    extract_structured_data()