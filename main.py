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
    /* Dark Mode kleuren */
    .stApp { background-color: #0e1117; color: #c9d1d9; }
    
    /* Input velden styling */
    .stTextInput>div>div>input { background-color: #161b22; color: white; border: 1px solid #30363d; }
    .stTextArea>div>div>textarea { background-color: #161b22; color: white; border: 1px solid #30363d; }
    
    /* Footer verbergen */
    footer { visibility: hidden; }
    
    /* Inputbalk vastzetten onderaan (Mobile Native feel) */
    .stChatInput { position: fixed; bottom: 0; padding-bottom: 20px; background-color: #0e1117; z-index: 100; }
    
    /* Marges voor leesbaarheid */
    .main { padding-bottom: 80px; }
    </style>
""", unsafe_allow_html=True)

# --- 3. GEHEUGEN ---
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Aphex II Online. Configureer mij in het menu en druk op 'Toepassen'."}]
if "cost" not in st.session_state:
    st.session_state.cost = 0.0000

# --- 4. SIDEBAR MENU (MET FORMULIER) ---
with st.sidebar:
    st.title("⚙️ CONFIGURATIE")
    
    # We gebruiken een FORM zodat de pagina niet steeds herlaadt tijdens het typen
    with st.form("config_form"):
        # A. API KEY
        api_key_input = st.text_input("OpenAI API Key", type="password", placeholder="sk-...")
        
        st.markdown("---")
        
        # B. MODEL SELECTIE
        model_options = ["gpt-5", "gpt-5-mini", "gpt-4o", "gpt-4o-mini", "Custom / Eigen Model"]
        selected_option = st.selectbox("Kies Model", model_options)
        
        # Custom model veld
        custom_model_input = ""
        if selected_option == "Custom / Eigen Model":
            custom_model_input = st.text_input("Vul model ID in", placeholder="bv. o1-preview")
        
        st.markdown("---")
        st.caption("KENNIS & ZINTUIGEN")
        
        # C. TOOLS
        use_internet = st.toggle("🌍 Live Internet (DuckDuckGo)", value=False)
        gdoc_link = st.text_input("📄 Google Doc Link", placeholder="https://docs.google.com/...")
        manual_context = st.text_area("📝 Eigen Kennis / Context", placeholder="Plak hier tekst...", height=100)
        
        st.markdown("---")
        
        # D. PERSONA
        persona_input = st.text_area("🎭 Persona", value="Je bent Aphex II. Antwoord direct, intelligent en in het Nederlands.")
        
        # DE APPLY KNOP
        submitted = st.form_submit_button("✅ INSTELLINGEN TOEPASSEN")

    # --- LOGICA NA HET DRUKKEN OP TOEPASSEN ---
    # We stellen de variabelen in die we in het script gebruiken
    if api_key_input:
        openai.api_key = api_key_input
    
    # Model logica bepalen
    if selected_option == "Custom / Eigen Model":
        real_model = custom_model_input if custom_model_input else "gpt-4o"
    elif "gpt-5" in selected_option:
        real_model = "gpt-4o" # Fallback/Simulatie
        if submitted: st.toast("GPT-5 simulatie actief (via GPT-4o)", icon="ℹ️")
    else:
        real_model = selected_option
        
    if submitted:
        st.toast("Instellingen opgeslagen!", icon="✅")

    st.markdown("---")
    
    # E. KOSTEN & DOWNLOAD (Buiten het formulier voor directe actie)
    st.metric("Sessie Kosten", f"${st.session_state.cost:.4f}")
    
    # Chat Log downloaden
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

# --- 6. HOOFDSCHERM (CHAT UI) ---
st.title("APHEX II")

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- 7. INPUT LOGICA ---
if prompt := st.chat_input("Typ een bericht..."):
    
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.status("🧠 Aphex is aan het denken...", expanded=True) as status:
            context_text = ""
            
            # Kennis Ophalen (Gebruikt de variabelen uit het formulier)
            if manual_context:
                status.write("📚 Eigen Context lezen...")
                context_text += f"\n[CONTEXT]:\n{manual_context}\n"
            
            if gdoc_link:
                status.write("📄 Docs ophalen...")
                doc = get_google_doc(gdoc_link)
                if doc: 
                    context_text += f"\n[DOCS]:\n{doc}\n"
                    status.write("✅ Doc geladen")
                else:
                    status.write("⚠️ Doc fout (check link).")
            
            if use_internet:
                status.write(f"🌍 Zoeken: '{prompt}'...")
                web = search_web(prompt)
                if web: 
                    context_text += f"\n[WEB]:\n{web}\n"
                    status.write("✅ Web resultaten")
                else:
                    status.write("⚠️ Geen resultaten.")

            status.write(f"🤖 Antwoord formuleren ({real_model})...")
            
            if not api_key_input:
                st.error("⚠️ Geen API Key! Vul in menu in en druk op TOEPASSEN.")
                st.stop()
            
            try:
                sys_msg = persona_input
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

