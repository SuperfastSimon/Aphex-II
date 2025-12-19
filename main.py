# main.py
import os, tempfile, base64, json
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML

# ======================================================
# 🚀 APHEX II: STREAMLIT EDITION (Ultimate Mobile)
# ======================================================
import os, subprocess, time

# 1. SETUP & INSTALLATIE
print("⚙️  SYSTEM BOOT: Installing Streamlit & Dependencies...")
os.system('pip install streamlit openai duckduckgo-search requests > /dev/null 2>&1')
os.system('npm install -g localtunnel > /dev/null 2>&1')

# IP OPHALEN (JE WACHTWOORD)
try:
    public_ip = subprocess.check_output("curl -s ipv4.icanhazip.com", shell=True).decode("utf-8").strip()
except:
    public_ip = "UNKNOWN"

print("\n" + "▓"*60)
print(f"🔑 WACHTWOORD VOOR TUNNEL: {public_ip}")
print("▓"*60 + "\n")

# ======================================================
# 2. DE STREAMLIT APPLICATIE (Wordt weggeschreven naar app.py)
# ======================================================
app_code = """
import streamlit as st
import openai
from duckduckgo_search import DDGS
import requests
import time

# --- PAGINA CONFIGURATIE (Dark Mode & Mobile) ---
st.set_page_config(
    page_title="Aphex II",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="collapsed" # Menu standaard dicht op mobiel
)

# Custom CSS voor de 'Hacker' look en verbergen van footer
st.markdown(\"\"\"
    <style>
    .stApp { background-color: #0e1117; color: #c9d1d9; }
    .stTextInput>div>div>input { background-color: #161b22; color: white; border: 1px solid #30363d; }
    header { visibility: hidden; }
    footer { visibility: hidden; }
    .stChatInput { position: fixed; bottom: 0; }
    </style>
\"\"\", unsafe_allow_html=True)

# --- SESSIE STATUS (Geheugen) ---
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Aphex II Online. Klaar voor input."}]
if "cost" not in st.session_state:
    st.session_state.cost = 0.0000

# --- ZIJBALK (INSTELLINGEN) ---
with st.sidebar:
    st.title("⚙️ CONFIGURATIE")
    
    # 1. API Key
    api_key = st.text_input("OpenAI API Key", type="password", placeholder="sk-...")
    if api_key:
        openai.api_key = api_key
    
    # 2. Model Keuze
    model_display = st.selectbox("Kies Model", 
        ["GPT-5-Mini (Simulated)", "GPT-5 (Simulated)", "GPT-4o", "GPT-4o-mini", "Claude 3.5 (Simulated)"])
    
    # Mapping naar echte API modellen om crashes te voorkomen
    real_model = "gpt-4o-mini" # Default fallback
    if "GPT-4o" in model_display: real_model = "gpt-4o"
    if "GPT-5" in model_display: real_model = "gpt-4o" # Mappen naar beste beschikbaar
    
    # 3. Kennis & Tools
    st.markdown("---")
    st.caption("KENNIS & ZINTUIGEN")
    
    use_internet = st.toggle("🌍 Live Internet (DuckDuckGo)", value=False)
    gdoc_link = st.text_input("📄 Google Doc Link", placeholder="https://docs.google.com/...")
    manual_context = st.text_area("📝 Kennis Context", placeholder="Plak hier tekst/data...", height=100)
    
    # 4. Persona
    st.markdown("---")
    persona = st.text_area("🎭 Persona / Systeemrol", value="Je bent Aphex II. Antwoord direct, intelligent en in het Nederlands.")
    
    # 5. Stats & Kill Switch
    st.markdown("---")
    st.metric("Sessie Kosten", f"${st.session_state.cost:.4f}")
    
    if st.button("☢️ NOODREM / RESET", type="primary"):
        st.session_state.messages = []
        st.session_state.cost = 0.0
        st.rerun()

# --- LOGICA FUNCTIES ---
def get_google_doc(url):
    try:
        if "/edit" in url: url = url.split("/edit")[0] + "/export?format=txt"
        response = requests.get(url)
        if response.status_code == 200:
            return response.text[:2000] # Limiet voor veiligheid
    except:
        return None
    return None

def search_web(query):
    try:
        results = DDGS().text(query, max_results=3)
        return "\\n".join([f"- {r['title']}: {r['body']}" for r in results])
    except:
        return None

# --- HOOFDSCHERM (CHAT) ---
st.title("APHEX II")

# Toon historie
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- INPUT VERWERKING ---
if prompt := st.chat_input("Typ een bericht..."):
    # 1. Toon gebruikersbericht
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 2. AI Denkt (Chain of Thought Visualisatie)
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        
        # 'Expander' laat gedachtes zien zonder de chat te vervuilen
        with st.status("🧠 Aphex is aan het denken...", expanded=True) as status:
            
            context_text = ""
            
            # A. Check Manual Context
            if manual_context:
                status.write("📚 Handmatige kennis laden...")
                context_text += f"\\n[CONTEXT]:\\n{manual_context}\\n"
            
            # B. Check Google Doc
            if gdoc_link:
                status.write("📄 Google Doc ophalen...")
                doc_content = get_google_doc(gdoc_link)
                if doc_content:
                    context_text += f"\\n[DOCS]:\\n{doc_content}...\\n"
                    status.write("✅ Doc gelezen.")
                else:
                    status.write("⚠️ Doc fout (check link/rechten).")
            
            # C. Check Internet
            if use_internet:
                status.write(f"🌍 Zoeken op DuckDuckGo naar: '{prompt}'...")
                web_results = search_web(prompt)
                if web_results:
                    context_text += f"\\n[WEB]:\\n{web_results}\\n"
                    status.write("✅ Web resultaten gevonden.")
                else:
                    status.write("⚠️ Geen resultaten.")
            
            # D. Call OpenAI
            status.write(f"🤖 Antwoord genereren met {real_model}...")
            
            if not api_key:
                full_response = "⚠️ **LET OP:** Geen API Key ingevuld in het menu linksboven (☰). Ik kan nu niet antwoorden."
                status.update(label="❌ Geen sleutel", state="error")
            else:
                try:
                    # System prompt samenstellen
                    sys_msg = persona
                    if context_text:
                        sys_msg += f"\\n\\nGEBRUIK DEZE CONTEXT:\\n{context_text}"
                    
                    stream = openai.chat.completions.create(
                        model=real_model,
                        messages=[
                            {"role": "system", "content": sys_msg},
                            *st.session_state.messages
                        ],
                        stream=True
                    )
                    
                    # Stream het antwoord naar het scherm
                    full_response = st.write_stream(stream)
                    
                    # Update kosten (Schatting)
                    st.session_state.cost += 0.002 
                    status.update(label="✅ Klaar", state="complete", expanded=False)
                    
                except Exception as e:
                    full_response = f"❌ API Fout: {str(e)}"
                    status.update(label="Error", state="error")

    # 3. Sla antwoord op in historie
    st.session_state.messages.append({"role": "assistant", "content": full_response})
    st.rerun() # Refresh om kosten update in sidebar te tonen
"""

# Schrijf de app code naar een bestand
with open("app.py", "w", encoding='utf-8') as f:
    f.write(app_code)

# ======================================================
# 3. STARTEN
# ======================================================
print("🚀 Streamlit Server wordt gestart...")

# 1. Start Streamlit op de achtergrond
subprocess.Popen(["streamlit", "run", "app.py", "--server.port", "8501"])
time.sleep(3)

# 2. Start Tunnel
print("🔗 Tunnel wordt opgezet...")
process = subprocess.Popen(['npx', 'localtunnel', '--port', '8501'], stdout=subprocess.PIPE)

while True:
    line = process.stdout.readline()
    if line:
        decoded = line.decode("utf-8").strip()
        if "your url is" in decoded.lower():
            url = decoded.split("is: ")[1].strip()
            print(f"\n⚡ APHEX II STREAMLIT LINK: {url}")
            print(f"🔑 WACHTWOORD: {public_ip}")
            print("\n(Klik op de link en vul het IP in bij 'Tunnel Password')")
            break
            
