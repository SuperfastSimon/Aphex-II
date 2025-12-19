import streamlit as st
import openai
from duckduckgo_search import DDGS
import requests
import time
from datetime import datetime

# --- PAGINA CONFIGURATIE ---
st.set_page_config(
    page_title="Aphex II",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CSS STYLING ---
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: #c9d1d9; }
    .stTextInput>div>div>input { background-color: #161b22; color: white; border: 1px solid #30363d; }
    footer { visibility: hidden; }
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
    
    # 1. API KEY
    api_key = st.text_input("OpenAI API Key", type="password", placeholder="sk-...")
    if api_key: openai.api_key = api_key
    
    st.markdown("---")
    
    # 2. MODEL KEUZE
    model_options = ["gpt-5", "gpt-5-mini", "gpt-4o", "gpt-4o-mini", "Custom / Eigen Model"]
    selected_option = st.selectbox("Kies Model", model_options)
    
    if selected_option == "Custom / Eigen Model":
        real_model = st.text_input("Vul modelnaam in", placeholder="bv. o1-preview")
        if not real_model: real_model = "gpt-4o"
    else:
        real_model = selected_option
    
    st.caption(f"Actief: {real_model}")
    
    st.markdown("---")
    
    # 3. TOOLS
    use_internet = st.toggle("🌍 Live Internet", value=False)
    gdoc_link = st.text_input("📄 Google Doc Link", placeholder="https://docs.google.com/...")
    manual_context = st.text_area("📝 Eigen Kennis", placeholder="Plak hier tekst...", height=100)
    
    st.markdown("---")
    
    # 4. PERSONA
    persona = st.text_area("🎭 Persona", value="Je bent Aphex II. Antwoord direct, intelligent en in het Nederlands.")
    
    st.markdown("---")
    
    # 5. OPSLAAN & RESET
    st.metric("Sessie Kosten", f"${st.session_state.cost:.4f}")
    
    # LOGICA VOOR DOWNLOADEN CHAT
    chat_log = ""
    for msg in st.session_state.messages:
        role = msg["role"].upper()
        content = msg["content"]
        chat_log += f"[{role}]: {content}\n\n{'-'*20}\n\n"
    
    # De Download Knop
    st.download_button(
        label="💾 DOWNLOAD CHAT (.txt)",
        data=chat_log,
        file_name=f"aphex_chat_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
        mime="text/plain"
    )
    
    if st.button("☢️ WIS ALLES", type="primary"):
        st.session_state.messages = []
        st.session_state.cost = 0.0
        st.rerun()

# --- FUNCTIES ---
def get_google_doc(url):
    try:
        if "/edit" in url: url = url.split("/edit")[0] + "/export?format=txt"
        response = requests.get(url)
        if response.status_code == 200: return response.text[:2000]
    except: return None
    return None

def search_web(query):
    try:
        results = DDGS().text(query, max_results=3)
        return "\n".join([f"- {r['title']}: {r['body']}" for r in results])
    except: return None

# --- HOOFDSCHERM ---
st.title("APHEX II")

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Typ een bericht..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.status("🧠 Aphex is aan het denken...", expanded=True) as status:
            context_text = ""
            
            if manual_context:
                status.write("📚 Eigen Context lezen...")
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

            status.write(f"🤖 Antwoord formuleren ({real_model})...")
            
            if not api_key:
                st.error("⚠️ Geen API Key! Vul in menu in.")
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

