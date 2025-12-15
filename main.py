# main.py
import os, tempfile, base64, json
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML
import streamlit as st
from openai import OpenAI

# --- AI client ---
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# --- Templates ---
TEMPLATE_DIR = "templates"
os.makedirs(TEMPLATE_DIR, exist_ok=True)

TEMPLATES = {
    "modern_sidebar.html": __MODERN_TEMPLATE__,
    "classic_minimal.html": __CLASSIC_TEMPLATE__,
    "ats_friendly.html": __ATS_TEMPLATE__,
}
for fname, content in TEMPLATES.items():
    with open(os.path.join(TEMPLATE_DIR, fname), "w", encoding="utf-8") as f:
        f.write(content.strip())

PALETTES = {
    "Neutral": "#374151", "Blue": "#2b6cb0", "Green": "#059669",
    "Warm": "#b45309", "Monochrome": "#111827", "High Contrast": "#000000"
}

def file_to_base64(file) -> str:
    return base64.b64encode(file.read()).decode("utf-8")


# Function for rendering PDF
def render_pdf(data, template_name, accent):
    env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))
    tpl = env.get_template(template_name)
    html = tpl.render(data=data, accent=accent)
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    HTML(string=html).write_pdf(tmp.name)
    return tmp.name, html


# Function to improve text using AI
def improve_text(text, style="concise", language="nl"):
    if not text.strip(): return []
    prompt = f"Verbeter deze CV-tekst zodat hij {style}, ATS-vriendelijk en in {language} is. Geef drie varianten."
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role":"user","content":prompt + "\n\nTekst:\n" + text}],
        max_tokens=400, temperature=0.6
    )
    content = resp.choices[0].message.content
    try:
        parsed = json.loads(content)
        if isinstance(parsed, list): return parsed
    except Exception:
        return [p.strip() for p in content.split("\n") if p.strip()]
    return []


# --- Streamlit UI ---
st.set_page_config(page_title="Creatieve CV Maker", layout="wide")
st.title("Creatieve CV Maker")

template_choice = st.sidebar.selectbox("Kies template", list(TEMPLATES.keys()))
accent_choice = st.sidebar.selectbox("Kleurpalet", list(PALETTES.keys())+["Custom"])
accent = st.sidebar.color_picker("Kies accentkleur", "#2b6cb0") if accent_choice=="Custom" else PALETTES[accent_choice]
uploaded_photo = st.sidebar.file_uploader("Upload profielfoto", type=["jpg","jpeg","png"])

data = {
    "name": st.text_input("Naam"),
    "address": st.text_input("Adres"),
    "email": st.text_input("E-mail"),
    "summary": st.text_area("Persoonlijk profiel", height=100),
    "experience": st.text_area("Ervaring", height=150),
    "education": st.text_area("Opleiding", height=100),
    "skills": [s.strip() for s in st.text_input("Skills (komma-gescheiden)").split(",") if s.strip()]
}
if uploaded_photo: data["photo"] = file_to_base64(uploaded_photo)

st.subheader("AI Tekstsuggesties")
user_text = st.text_area("Tekst voor verbetering", value=data.get("experience",""))
style = st.selectbox("Stijl", ["concise","formal","creative"])
language = st.selectbox("Taal", ["nl","en"])
if st.button("Genereer suggesties"):
    suggestions = improve_text(user_text, style=style, language=language)
    st.write("### AI suggesties")
    for i,s in enumerate(suggestions,1):
        st.markdown(f"**Variant {i}:** {s}")
    if suggestions and st.button("Gebruik eerste suggestie"):
        data["experience"] = suggestions[0]

st.subheader("Live preview")
pdf_path, html_preview = render_pdf(data, template_choice, accent)
st.components.v1.html(html_preview, height=700, scrolling=True)
if st.button("Download PDF"):
    with open(pdf_path,"rb") as f:
        st.download_button("Download CV als PDF", f, file_name="cv_output.pdf")
