# Log 2025-12-15 09:51
# full_cv_maker.py
import os, tempfile, base64, json, re
import streamlit as st
import pdfplumber
from weasyprint import HTML
from openai import OpenAI
from jinja2 import Environment, FileSystemLoader

# --- AI client ---
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# --- Templates ---
TEMPLATE_DIR = "templates"
os.makedirs(TEMPLATE_DIR, exist_ok=True)

TEMPLATES = {
    "modern_sidebar.html": """<!doctype html><html><head><meta charset="utf-8"/>
<style>
:root { --accent: {{ accent }}; --accent-contrast:#fff; --text:#111827; }
body { font-family: Inter, Arial, sans-serif; margin:0; color:var(--text); }
.layout { display:flex; min-height:100vh; }
.sidebar { width:30%; background:var(--accent); color:var(--accent-contrast); padding:20px; }
.sidebar img { width:120px; height:120px; border-radius:60px; margin-bottom:20px; }
.main { flex:1; padding:40px; }
h2 { color:var(--accent); border-bottom:1px solid #e5e7eb; padding-bottom:4px; }
</style></head><body>
<div class="layout">
  <div class="sidebar">
    {% if data.photo %}<img src="data:image/png;base64,{{ data.photo }}"/>{% endif %}
    <h2>{{ data.name }}</h2>
    <p>{{ data.address }}</p><p>{{ data.email }}</p>
    <h3>Skills</h3><ul>{% for s in data.skills %}<li>{{ s }}</li>{% endfor %}</ul>
  </div>
  <div class="main">
    <h2>Profiel</h2><div>{{ data.summary }}</div>
    <h2>Ervaring</h2><div>{{ data.experience | replace('\\n','<br/>') | safe }}</div>
    <h2>Opleiding</h2><div>{{ data.education }}</div>
  </div>
</div></body></html>""",
    "classic_minimal.html": """<!doctype html><html><head><meta charset="utf-8"/>
<style>:root { --accent: {{ accent }}; }
body { font-family: "Times New Roman", serif; margin:40px; }
h2 { color:var(--accent); border-bottom:1px solid #ccc; }
</style></head><body>
<h1>{{ data.name }}</h1><p>{{ data.address }}</p><p>{{ data.email }}</p>
<h2>Profiel</h2><div>{{ data.summary }}</div>
<h2>Ervaring</h2><div>{{ data.experience | replace('\\n','<br/>') | safe }}</div>
<h2>Opleiding</h2><div>{{ data.education }}</div>
<h2>Skills</h2><p>{{ data.skills | join(', ') }}</p>
</body></html>""",
    "ats_friendly.html": """<!doctype html><html><head><meta charset="utf-8"/>
<style>body { font-family: Arial, sans-serif; margin:40px; }
h1 { font-size:20px; } h2 { font-size:14px; margin-top:12px; }</style></head><body>
<h1>{{ data.name }}</h1><p>{{ data.address }}</p><p>{{ data.email }}</p>
<h2>Profiel</h2><div>{{ data.summary }}</div>
<h2>Ervaring</h2><div>{{ data.experience | replace('\\n','<br/>') | safe }}</div>
<h2>Opleiding</h2><div>{{ data.education }}</div>
<h2>Skills</h2><ul>{% for s in data.skills %}<li>{{ s }}</li>{% endfor %}</ul>
</body></html>"""
}
for fname, content in TEMPLATES.items():
    with open(os.path.join(TEMPLATE_DIR, fname), "w", encoding="utf-8") as f:
        f.write(content.strip())

PALETTES = {
    "Neutral": "#374151","Blue": "#2b6cb0","Green": "#059669",
    "Warm": "#b45309","Monochrome": "#111827","High Contrast": "#000000"
}

def file_to_base64(file) -> str:
    return base64.b64encode(file.read()).decode("utf-8")

def render_pdf(data, template_name, accent):
    env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))
    tpl = env.get_template(template_name)
    html = tpl.render(data=data, accent=accent)
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    HTML(string=html).write_pdf(tmp.name)
    return tmp.name, html

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

# --- Extra: schrijf Dockerfile en GitHub Actions workflow ---
DOCKERFILE = """FROM python:3.11-slim
RUN apt-get update && apt-get install -y \\
    libpango-1.0-0 libpangoft2-1.0-0 libcairo2 libgdk-pixbuf2.0-0 fonts-dejavu-core \\
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY . .
RUN pip install --no-cache-dir streamlit pdfplumber weasyprint openai jinja2
EXPOSE 8501
CMD ["streamlit", "run", "cv_maker_app.py", "--server.port=8501", "--server.address=0.0.0.0"]
"""

WORKFLOW = """name: Autodeploy CV Maker
on:
  push: