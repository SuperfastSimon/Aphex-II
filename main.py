import streamlit as st
import pdfplumber, base64, tempfile, re, os, json
from openai import OpenAI
from jinja2 import Environment, FileSystemLoader
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

# --- AI client ---
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# --- Automatische mappen en templates ---
TEMPLATE_DIR = "templates"
os.makedirs(TEMPLATE_DIR, exist_ok=True)

TEMPLATE_FILES = {
    "modern.html": """<!doctype html><html><head><meta charset=\"utf-8\"/>
<style>
:root { --accent: {{ accent }}; --text:#111827; --bg:#ffffff; }
body { font-family: Inter, Arial, sans-serif; margin:40px; color:var(--text); }
.header { display:flex; align-items:center; gap:20px; margin-bottom:20px; }
.photo { width:110px; height:110px; border-radius:55px; object-fit:cover; border:4px solid var(--accent); }
.name { font-size:28px; font-weight:700; }
h2 { color:var(--accent); font-size:16px; margin:8px 0; }
</style></head><body>
<div class=\"header\">
{% if data.photo %}<img src=\"data:image/png;base64,{{ data.photo }}\" class=\"photo\"/>{% endif %}
<div><div class=\"name\">{{ data.name }}</div><div>{{ data.education }}</div></div>
</div>
<h2>Ervaring</h2><div>{{ data.experience | replace('\\n','<br/>') | safe }}</div>
<h2>Skills</h2><ul>{% for s in data.skills %}<li>{{ s }}</li>{% endfor %}</ul>
</body></html>""",
    "classic.html": """<!doctype html><html><head><meta charset=\"utf-8\"/>
<style>
:root { --accent: {{ accent }}; }
body { font-family: \"Times New Roman\", serif; margin:40px; }
.name { font-size:30px; font-weight:700; }
h2 { font-size:14px; color:var(--accent); margin-bottom:6px; }
</style></head><body>
<div class=\"name\">{{ data.name }}</div><div>{{ data.education }}</div>
<h2>Ervaring</h2><div>{{ data.experience | replace('\\n','<br/>') | safe }}</div>
<h2>Skills</h2><p>{{ data.skills | join(', ') }}</p>
</body></html>""",
    "ats.html": """<!doctype html><html><head><meta charset=\"utf-8\"/>
<style>
body { font-family: Arial, sans-serif; margin:40px; }
h1 { font-size:20px; } h2 { font-size:14px; margin-top:12px; }
</style></head><body>
<h1>{{ data.name }}</h1><p>{{ data.education }}</p>
<h2>Ervaring</h2><div>{{ data.experience | replace('\\n','<br/>') | safe }}</div>
<h2>Skills</h2><ul>{% for s in data.skills %}<li>{{ s }}</li>{% endfor %}</ul>
</body></html>"""
}

# Schrijf templates naar bestanden
for fname, content in TEMPLATE_FILES.items():
    fpath = os.path.join(TEMPLATE_DIR, fname)
    if not os.path.exists(fpath):
        with open(fpath, "w", encoding="utf-8") as f:
            f.write(content.strip())

# --- Paletten ---
PALETTES = {
    "Neutral": "#374151","Blue": "#2b6cb0","Green": "#059669",
    "Warm": "#b45309","Monochrome": "#111827","High Contrast": "#000000"
}

# --- Helpers ---
def file_to_base64(file) -> str:
    return base64.b64encode(file.read()).decode("utf-8")

def extract_cv_data(file_obj):
    text = ""
    try:
        with pdfplumber.open(file_obj) as pdf:
            pages = [p.extract_text() for p in pdf.pages]
            text = " ".join([p for p in pages if p])
    except Exception:
        try: text = file_obj.read().decode("utf-8", errors="ignore")
        except Exception: text = ""
    data = {"name":"","experience":"","education":"","skills":[]}
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    if lines: data["name"] = lines[0]
    skills_keywords = ["Python","JavaScript","SQL","Docker","Kubernetes","AWS","Git"]
    data["skills"] = [k for k in skills_keywords if k.lower() in text.lower()]
    exp_match = re.search(r"(Experience|Ervaring)(.*?)(Education|Opleiding|Skills|$)", text, re.S|re.I)
    if exp_match: data["experience"] = exp_match.group(2).strip()
    edu_match = re.search(r"(Education|Opleiding)(.*?)(Skills|$)", text, re.S|re.I)
    if edu_match: data["education"] = edu_match.group(2).strip()
    return data

def render_pdf_reportlab(data, accent):
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    c = canvas.Canvas(tmp.name, pagesize=A4)
    width, height = A4
    c.setFont("Helvetica-Bold", 20)
    c.drawString(50, height-50, data.get("name",""))
    c.setFont("Helvetica", 12)
    c.drawString(50, height-80, f"Opleiding: {data.get('education','')}")
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, height-120, "Ervaring:")
    c.setFont("Helvetica", 12)
    c.drawString(50, height-140, data.get("experience",""))
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, height-180, "Skills:")
    c.setFont("Helvetica", 12)
    c.drawString(50, height-200, ", ".join(data.get("skills",[])))
    c.save()
    return tmp.name

def improve_text(text, style="concise", language="nl", template="modern.html"):
    if not text.strip(): return []
    prompt = (
        f"Verbeter deze CV-tekst zodat hij {style}, ATS-vriendelijk en in {language} is. "
        f"Template: {template}. Geef drie varianten: formeel, neutraal, creatief.\n\n"
        f"Tekst:\n{text}\n\nAntwoord in JSON array."
    )
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role":"user","content":prompt}],
        max_tokens=400, temperature=0.6
    )
    content = resp.choices[0].message.content
    try:
        parsed = json.loads(content)
        if isinstance(parsed, list): return parsed
    except Exception:
        return [p.strip() for p in content.split("\n") if p.strip()][:3]
    return []

# --- Streamlit UI ---
st.set_page_config(page_title="CV Maker", layout="wide")
st.title("CV Maker App")

st.sidebar.header("Instellingen")
template_choice = st.sidebar.selectbox("Kies template", list(TEMPLATE_FILES.keys()))
palette_choice = st.sidebar.selectbox("Kleurpalet", list(PALETTES.keys())+["Custom"])
accent = st.sidebar.color_picker("Kies accentkleur", "#2b6cb0") if palette_choice=="Custom" else PALETTES[palette_choice]
uploaded_pdf = st.sidebar.file_uploader("Upload bestaande CV (PDF)", type="pdf")
uploaded_photo = st.sidebar.file_uploader("Upload profielfoto", type=["jpg","jpeg","png"])

if uploaded_pdf:
    parsed = extract_cv_data(uploaded_pdf)
    data = {"name": parsed.get("name",""),"experience": parsed.get("experience",""),
            "education": parsed.get("education",""),"skills": parsed.get("skills",[])}
    st.success("CV data geïmporteerd uit PDF")
else:
    data = {"name": st.text_input("Naam"),
            "experience": st.text_area("Ervaring", height=150),
            "education": st.text_area("Opleiding", height=100),
            "skills": [s.strip() for s in st.text_input("Skills (komma-gescheiden)").split(",") if s.strip()]}

if uploaded_photo: data["photo"] = file_to_base64(uploaded_photo)

st.subheader("AI Tekstsuggesties")
user_text = st.text_area("Tekst voor verbetering", value=data.get("experience",""))
style = st.selectbox("Stijl", ["concise","formal","creative"])
language = st.selectbox("Taal", ["nl","en"])
if st.button("Genereer suggesties"):
    suggestions = improve_text(user_text, style=style, language=language, template=template_choice)
    for i, suggestion in enumerate(suggestions):
        st.text_area(f"Suggestie {i+1}", value=suggestion, height=100, key=f"suggestion_{i}")

st.subheader("CV Preview")

template_env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))
template = template_env.get_template(template_choice)

output_html = template.render(data=data, accent=accent)
st.components.v1.html(output_html, height=500, scrolling=True)

download_button = st.button("Download CV als PDF")
if download_button:
    pdf_file_path = render_pdf_reportlab(data, accent)
    with open(pdf_file_path, "rb") as pdf_file:
        pdf_data = pdf_file.read()
    st.download_button(label="Download PDF", data=pdf_data, file_name="CV.pdf", mime="application/pdf")
    os.remove(pdf_file_path)