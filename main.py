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
    initial_sidebar_state="expanded"  # <--- HIERMEE STAAT HIJ STANDAARD OPEN
)

# --- CSS STYLING ---
st.markdown("""
    <style>
    /* Algemene kleuren (Dark Mode force) */
    .stApp { background-color: #0e1117; color: #c9d1d9; }
    
    /* Input velden mooier maken */
    .stTextInput>div>div>input { background-color: #161b22; color: white; border: 1px solid #30363d; }
    
    /* Alleen de footer verbergen, NIET de header (zodat je het menu ziet) */
    footer { visibility: hidden; }
    
    /* De typbalk vastzetten onderaan (Mobile Native feel) */
    .stChatInput { position: fixed; bottom: 0; padding-bottom: 20px; background-color: #0e1117; z-index: 100; }
    </style>
""", unsafe_allow_html=True)

# --- GEHEUGEN ---
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Aphex II Online. Klaar voor input."}]
if "cost" not in st.session_state:
    st.session_state.cost = 0.0000

# --- SIDEBAR SETTINGS (HET MENU) ---
with st.sidebar:
    st.title("⚙️ CONFIGURATIE")
    
    # API KEY
    api_key = st.text_input("OpenAI API Key", type="password", placeholder="sk-...")
    if api_key:
        openai.api_key = api_key
    
    # MODEL KEUZE
    model_display = st.selectbox("Kies Model", 
        ["GPT-5", "GPT-5-mini", "GPT-4o-mini",
    
    # Mapping
    real_model = "GPT-5-mini"
    if "GPT-5" in model_display: real_model = "gpt-5"
    if "GPT-5-mini" in model_display: real_model = "GPT-5-mini"
    if "GPT-4o-mini" in model_display: real_model = "GPT-4o-mini"
    
    st.markdown("---")
    st.caption("TOOLS & KENNIS")
    
    # TOOLS
    use_internet = st.toggle("🌍 Live Internet (DuckDuckGo)", value=False)
    gdoc_link = st.text_input("📄 Google Doc Link", placeholder="https://docs.google.com/...")
    manual_context = st.text_area("📝 Eigen Kennis / Context", placeholder="Plak hier tekst die de AI moet weten...", height=100)
    
    st.markdown("---")
    
    # PERSONA
    persona = st.text_area("🎭 Persona / Rol", value="Je bent Aphex II. Antwoord direct, intelligent en in het Nederlands.")
    
    st.markdown("---")
    
    # STATS & NOODREM
    st.metric("Sessie Kosten", f"${st.session_state.cost:.4f}")
    
    if st.button("☢️ RESET GEHEUGEN", type="primary"):
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

# 1. Chat Historie Weergeven
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# 2. Input Verwerking
if prompt := st.chat_input("Typ een bericht..."):
    # Gebruiker bericht tonen
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # AI Antwoord Genereren
    with st.chat_message("assistant"):
        # De 'Status' container (Chain of Thought)
        with st.status("🧠 Aphex is aan het denken...", expanded=True) as status:
            context_text = ""
            
            # Kennis Ophalen
            if manual_context:
                status.write("📚 Eigen Context lezen...")
                context_text += f"\n[MANUAL CONTEXT]:\n{manual_context}\n"
            
            if gdoc_link:
                status.write("📄 Google Docs ophalen...")
                doc = get_google_doc(gdoc_link)
                if doc: 
                    context_text += f"\n[DOCS]:\n{doc}\n"
                    status.write("✅ Doc succesvol geladen")
                else:
                    status.write("⚠️ Doc fout (check link).")
            
            if use_internet:
                status.write(f"🌍 Zoeken op het web naar: '{prompt}'...")
                web = search_web(prompt)
                if web: 
                    context_text += f"\n[WEB SEARCH]:\n{web}\n"
                    status.write("✅ Web resultaten gevonden")
                else:
                    status.write("⚠️ Geen resultaten gevonden.")

            status.write("🤖 Antwoord formuleren...")
            
            # Check API Key
            if not api_key:
                st.error("⚠️ **LET OP:** Geen API Key ingevuld in het menu links! Ik kan nu niet antwoorden.")
                st.stop()
            
            try:
                # Prompt samenstellen
                sys_msg = persona
                if context_text: sys_msg += f"\n\nGEBRUIK DEZE CONTEXT:\n{context_text}"
                
                # OpenAI Call
                stream = openai.chat.completions.create(
                    model=real_model,
                    messages=[{"role": "system", "content": sys_msg}, *st.session_state.messages],
                    stream=True
                )
                
                # Antwoord streamen
                response = st.write_stream(stream)
                
                # Kosten bijwerken (Schatting)
                st.session_state.cost += 0.002
                status.update(label="Klaar", state="complete", expanded=False)
                
                # Opslaan in historie
                st.session_state.messages.append({"role": "assistant", "content": response})
                
            except Exception as e:
                st.error(f"Error: {e}")
