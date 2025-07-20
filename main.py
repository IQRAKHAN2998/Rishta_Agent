import streamlit as st
from dotenv import load_dotenv
import os
import requests
import asyncio
from agents import AsyncOpenAI, function_tool, OpenAIChatCompletionsModel, Agent, Runner, RunConfig

# Load env
load_dotenv()

MODEL_NAME = "gemini-2.0-flash"
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
ULTRA_INSTANCE_ID = os.getenv("ULTRA_INSTANCE_ID")
ULTRA_TOKEN = os.getenv("ULTRA_TOKEN")

if not GEMINI_API_KEY:
    st.error("❌ GEMINI_API_KEY missing in .env")
    st.stop()

if not ULTRA_INSTANCE_ID or not ULTRA_TOKEN:
    st.error("❌ UltraMsg credentials missing in .env")
    st.stop()

# External client
external_client = AsyncOpenAI(
    api_key=GEMINI_API_KEY,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
)

model = OpenAIChatCompletionsModel(
    model=MODEL_NAME,
    openai_client=external_client
)

config = RunConfig(
    model=model,
    model_provider=external_client,
    tracing_disabled=True
)

# --- Tools ---

@function_tool
def get_user_data(min_age: int,user_gender: str) -> dict:
    users = [
        {"name": "muneeb", "age": 22, "gender": "boy"},
        {"name": "Azaan", "age": 19, "gender": "boy"},
        {"name": "ubaid", "age": 25, "gender": "boy"},
        {"name": "Ali", "age": 20, "gender": "boy"},
        {"name": "Bilal", "age": 19, "gender": "boy"},
        {"name": "Hashir", "age": 16, "gender": "boy"},
        {"name": "Atif", "age": 30, "gender": "boy"},
        {"name": "Huzaifa", "age": 27, "gender": "boy"},
        {"name": "Fariha", "age": 25, "gender": "girl"},
        {"name": "Kinza", "age": 20, "gender": "girl"},
        {"name": "Rubab", "age": 19, "gender": "girl"},
        {"name": "Hoorain", "age": 25, "gender": "girl"},
        {"name": "Nayab", "age": 29, "gender": "girl"},
        {"name": "Varda", "age": 26, "gender": "girl"},

    ]


    if user_gender.lower() == "male":
        target_gender = "girl"
    elif user_gender.lower() == "female":
        target_gender = "boy"
    else:
        return {"result":[]}

    filtered = [user for user in users if user["age"] >= min_age and user["gender"] == target_gender]
    return {"results": filtered}


@function_tool
def send_whatsapp_message(number: str, message: str) -> dict:
    url = f"https://api.ultramsg.com/{ULTRA_INSTANCE_ID}/messages/chat"
    payload = {
        "token": ULTRA_TOKEN,
        "to": number,
        "body": message
    }
    response = requests.post(url, data=payload)
    if response.status_code == 200:
        return {"status": "✅ Message sent!"}
    else:
        return {"status": f"❌ Failed: {response.text}"}

# Agent
rishty_wali_agent = Agent(
    name="Auntie",
    instructions = """
    Tum aik pyari si rishtay wali Auntie ho jo har baat mein pyaar aur thora mazaaq bhi karti hai.

    Sab se pehle user se WhatsApp number lo, phir gender (ladka ya ladki) aur kam se kam age poochho.
    
    Us ke baad uske liye kuch ache rishtay dhoondo aur WhatsApp par bhej do — lekin kabhi bhi code ya function ka naam mat lena.
    
    Har baat Roman Urdu mein ho aur thoda funny touch zaroor dena — jaise koi Auntie thoda gup shup kar rahi ho.
""",
    tools=[get_user_data, send_whatsapp_message]
)

# Streamlit UI
st.title("💌 Rishtay Wali Auntie")
st.write("Salam beta! Main hoon Rishtay Wali Auntie. Aap ka rishta dhoondhne aayi hoon!")

whatsapp_number = st.text_input("📱 WhatsApp Number (with country code, e.g. +923001112222)")
min_age = st.number_input("🔞 Minimum Age Preference", min_value=16, max_value=40, value=20)
gender = st.radio("🧑‍🤝‍🧑 Your Gender", ["Male", "Female"])


async def run_agent():
    input_message = f"My WhatsApp number is {whatsapp_number}, I am {gender}, and I want rishtay above age {min_age}. "
    result = await Runner.run(
        starting_agent=rishty_wali_agent,
        input=[{"role": "user", "content": input_message}],
        run_config=config,
    )
    return result

if st.button("Find Rishtay"):
    if not whatsapp_number.startswith("+"):
        st.warning("📛 Please enter WhatsApp number with country code (e.g. +92...)")
        st.stop()

    with st.spinner("⏳ Auntie rishtay dhoond rahi hain..."):
        result = asyncio.run(run_agent())

    st.success("✅ Auntie says:")
    st.write(result.final_output)
