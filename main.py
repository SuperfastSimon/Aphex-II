import streamlit as st
import openai
from duckduckgo_search import DDGS
import requests
import time

# --- PAGINA CONFIGURATIE ---
st.set_page_config(
    page_title="Aphex II",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- CSS STYLING ---
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: #c9d1d9; }
    .stTextInput>div>div>input { background-color: #161b22; color: white; border: 1px solid #30363d; }
    header { visibility: hidden; }
    footer { visibility: hidden; }
    /* Fix voor input balk onderaan */
    .stChatInput { position: fixed; bottom: 0; padding-bottom: 20px; background-color: #0e1117; z-index: 100; }
    </style>
""", unsafe_allow_html=True)

# --- GEHEUGEN ---
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Aphex II Online. Klaar voor input."}]
if "cost" not in st.session_state:
    st.session_state.cost = 0.0000

# --- SIDEBAR SETTINGS ---
with st.sidebar:
    st.title("⚙️ CONFIGURATIE")
    
    api_key = st.text_input("OpenAI API Key", type="password", placeholder="sk-...")
    if api_key:
        openai.api_key = api_key
    
    model_display = st.selectbox("Kies Model", 
        ["GPT-4o", "GPT-4o-mini", "GPT-4-Turbo", "GPT-3.5-Turbo"])
    
    # Mapping
    real_model = "gpt-4o-mini"
    if "GPT-4o" in model_display: real_model = "gpt-4o"
    if "GPT-4-Turbo" in model_display: real_model = "gpt-4-turbo"
    if "GPT-3.5" in model_display: real_model = "gpt-3.5-turbo"
    
    st.markdown("---")
    st.caption("TOOLS")
    use_internet = st.toggle("🌍 Live Internet (DuckDuckGo)", value=False)
    gdoc_link = st.text_input("📄 Google Doc Link", placeholder="https://docs.google.com/...")
    manual_context = st.text_area("📝 Context", placeholder="Plak tekst...", height=100)
    
    st.markdown("---")
    persona = st.text_area("🎭 Persona", value="Je bent Aphex II. Antwoord direct en intelligent.")
    
    st.markdown("---")
    st.metric("Kosten", f"${st.session_state.cost:.4f}")
    
    if st.button("☢️ RESET", type="primary"):
        st.session_state.messages = []
        st.session_state.cost = 0.0
        st.rerun()

# --- FUNCTIES ---
def get_google_doc(url):
    try:
        if "/edit" in url: url = url.split("/edit")[0] + "/export?format=txt"
        response = requests.get(url)
        if response.status_code == 200:
            return response.text[:2000]
    except:
        return None
    return None

def search_web(query):
    try:
        results = DDGS().text(query, max_results=3)
        return "\n".join([f"- {r['title']}: {r['body']}" for r in results])
    except:
        return None

# --- HOOFDSCHERM ---
st.title("APHEX II")

# Chat Historie Weergeven
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Input Verwerking
if prompt := st.chat_input("Typ een bericht..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.status("🧠 Denken...", expanded=True) as status:
            context_text = ""
            
            if manual_context:
                status.write("📚 Context lezen...")
                context_text += f"\n[MANUAL]:\n{manual_context}\n"
            
            if gdoc_link:
                status.write("📄 Docs ophalen...")
                doc = get_google_doc(gdoc_link)
                if doc: 
                    context_text += f"\n[DOCS]:\n{doc}\n"
                    status.write("✅ Doc geladen")
            
            if use_internet:
                status.write("🌍 Web doorzoeken...")
                web = search_web(prompt)
                if web: 
                    context_text += f"\n[WEB]:\n{web}\n"
                    status.write("✅ Web resultaten")

            status.write("🤖 Antwoord formuleren...")
            
            if not api_key:
                st.error("Geen API Key! Vul deze in het menu in.")
                st.stop()
            
            try:
                sys_msg = persona
                if context_text: sys_msg += f"\n\nCONTEXT:\n{context_text}"
                
                stream = openai.chat.completions.create(
                    model=real_model,
                    messages=[{"role": "system", "content": sys_msg}, *st.session_state.messages],
                    stream=True
                )
                response = st.write_stream(stream)
                st.session_state.cost += 0.002
                status.update(label="Klaar", state="complete", expanded=False)
                st.session_state.messages.append({"role": "assistant", "content": response})
                
            except Exception as e:
                st.error(f"Error: {e}")
