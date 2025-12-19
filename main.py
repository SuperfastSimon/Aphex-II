import streamlit as st
import openai
from duckduckgo_search import DDGS
import requests
import time
from datetime import datetime

# --- 1. PAGINA CONFIGURATIE ---
st.set_page_config(
    page_title="Aphex II",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. CSS STYLING ---
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: #c9d1d9; }
    .stTextInput>div>div>input { background-color: #161b22; color: white; border: 1px solid #30363d; }
    .stTextArea>div>div>textarea { background-color: #161b22; color: white; border: 1px solid #30363d; }
    footer { visibility: hidden; }
    .stChatInput { position: fixed; bottom: 0; padding-bottom: 20px; background-color: #0e1117; z-index: 100; }
    .main { padding-bottom: 80px; }
    </style>
""", unsafe_allow_html=True)

# --- 3. GEHEUGEN ---
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Aphex II Online. GPT-5 Ready."}]
if "cost" not in st.session_state:
    st.session_state.cost = 0.0000

# --- 4. SIDEBAR MENU ---
with st.sidebar:
    st.title("⚙️ CONFIGURATIE")
    
    with st.form("config_form"):
        api_key_input = st.text_input("OpenAI API Key", type="password", placeholder="sk-...")
        
        st.markdown("---")
        
        # MODEL SELECTIE (PUUR)
        # Deze strings gaan direct naar de API zonder aanpassingen
        model_options = ["gpt-5", "gpt-5-mini", "gpt-4o", "gpt-4o-mini", "Custom / Eigen Model"]
        selected_option = st.selectbox("Kies Model", model_options)
        
        custom_model_input = ""
        if selected_option == "Custom / Eigen Model":
            custom_model_input = st.text_input("Vul exact Model ID in", placeholder="bv. o1-preview")
        
        st.markdown("---")
        st.caption("KENNIS")
        
        use_internet = st.toggle("🌍 Live Internet (DuckDuckGo)", value=False)
        gdoc_link = st.text_input("📄 Google Doc Link", placeholder="https://docs.google.com/...")
        manual_context = st.text_area("📝 Eigen Kennis / Context", placeholder="Plak hier tekst...", height=100)
        
        st.markdown("---")
        
        persona_input = st.text_area("🎭 Persona", value="Je bent Aphex II.")
        
        # APPLY KNOP
        submitted = st.form_submit_button("✅ TOEPASSEN")

    # --- LOGICA (PUUR) ---
    if api_key_input:
        openai.api_key = api_key_input
    
    # KIES HET MODEL (Geen fallback naar 4o meer)
    if selected_option == "Custom / Eigen Model":
        real_model = custom_model_input if custom_model_input else "gpt-4o"
    else:
        # Dit stuurt keihard 'gpt-5' of 'gpt-5-mini' als je dat kiest
        real_model = selected_option
        
    if submitted:
        st.toast(f"Model actief: {real_model}", icon="🚀")

    st.markdown("---")
    
    st.metric("Sessie Kosten", f"${st.session_state.cost:.4f}")
    
    # Download Chat
    chat_log_text = ""
    for msg in st.session_state.messages:
        chat_log_text += f"[{msg['role'].upper()}]: {msg['content']}\n\n"
    
    st.download_button(
        label="💾 DOWNLOAD CHAT (.txt)",
        data=chat_log_text,
        file_name=f"aphex_chat_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
        mime="text/plain"
    )
    
    if st.button("☢️ WIS GEHEUGEN", type="primary"):
        st.session_state.messages = []
        st.session_state.cost = 0.0
        st.rerun()

# --- 5. HULP FUNCTIES ---
def get_google_doc(url):
    try:
        if "/edit" in url: url = url.split("/edit")[0] + "/export?format=txt"
        response = requests.get(url)
        if response.status_code == 200: return response.text[:3000]
    except: return None
    return None

def search_web(query):
    try:
        results = DDGS().text(query, max_results=3)
        return "\n".join([f"- {r['title']}: {r['body']}" for r in results])
    except: return None

# --- 6. CHAT UI ---
st.title("APHEX II")

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Typ een bericht..."):
    
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.status(f"🧠 Request naar {real_model}...", expanded=True) as status:
            context_text = ""
            
            if manual_context:
                status.write("📚 Context lezen...")
                context_text += f"\n[CONTEXT]:\n{manual_context}\n"
            
            if gdoc_link:
                status.write("📄 Docs ophalen...")
                doc = get_google_doc(gdoc_link)
                if doc: 
                    context_text += f"\n[DOCS]:\n{doc}\n"
                    status.write("✅ Doc geladen")
            
            if use_internet:
                status.write(f"🌍 Zoeken: '{prompt}'...")
                web = search_web(prompt)
                if web: 
                    context_text += f"\n[WEB]:\n{web}\n"
                    status.write("✅ Web resultaten")

            status.write("🤖 Antwoord genereren...")
            
            if not api_key_input:
                st.error("⚠️ Geen API Key!")
                st.stop()
            
            try:
                sys_msg = persona_input
                if context_text: sys_msg += f"\n\nCONTEXT:\n{context_text}"
                
                # ECHTE API CALL (Puur)
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
                # Hier zie je de harde error als de API het model niet pakt
                st.error(f"❌ API Fout: {e}")
