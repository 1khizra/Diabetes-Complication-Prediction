# ================= IMPORTS =================
import streamlit as st
import hashlib
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from datetime import datetime, timedelta
import os
import joblib
from database import create_table, get_patients, add_patient, delete_patient
from auth_db import create_user_table, create_default_users, login_user
from database import get_patients
from database import get_appointments, add_appointment, update_appointment_status, delete_appointment
import streamlit.components.v1 as components
from auth_db import conn, hash_password
import google.generativeai as genai   
GEMINI_API_KEY =your_gemini_api_key_here

genai.configure(api_key=GEMINI_API_KEY)

model = genai.GenerativeModel("gemini-2.5-flash")

create_user_table()
create_default_users()


# ================= LOAD ML MODELS =================
model1 = joblib.load("ml_models/step1.pkl")
model2 = joblib.load("ml_models/step2.pkl")
model3 = joblib.load("ml_models/step3.pkl")

# ================= FEATURE ALIGN HELPER =================
def align_features(data, model):
    df = pd.DataFrame([data])
    df = df.apply(pd.to_numeric, errors='coerce').fillna(0)
    df = df.reindex(columns=model.feature_names_in_, fill_value=0)
    return df

# ================= PAGE CONFIG =================
st.set_page_config(
    page_title="DiabetesCare AI System",
    layout="wide",
    initial_sidebar_state="expanded"
)
from database import create_table, add_patient, get_patients, delete_patient

create_table()



# ================= SESSION =================
if "patients" not in st.session_state:
    st.session_state.patients = get_patients()

if "patient_data" not in st.session_state:
    st.session_state.patient_data = {}

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "role" not in st.session_state:
    st.session_state.role = None

# ================= CUSTOM CSS =================
st.markdown("""
<style>

/* ================= MAIN ================= */
header[data-testid="stHeader"]{
    display:none;
}

section[data-testid="stSidebar"]{
    top:0;
}

.block-container{
    padding-top:0rem !important;
    margin-top: 0rem !important;
}


.stApp{
    background:#F5F7FA;
    font-family:Arial;
    margin-top: -35px !important;
}

/* ================= SIDEBAR ================= */

section[data-testid="stSidebar"]{
    background:linear-gradient(180deg,#062E57,#0D3B66);
    width:255px !important;
}

section[data-testid="stSidebar"] *{
    color:white !important;
}

/* ================= LOGO ================= */

.logo-box{
    text-align:center;
    padding:25px 10px;
}

.logo-title{
    font-size:28px;
    font-weight:bold;
}

.logo-sub{
    color:#CBD5E1;
    font-size:13px;
}

/* ================= MENU ================= */

div[data-testid="stRadio"] label{
    padding:12px;
    border-radius:12px;
    margin-bottom:5px;
    transition:0.3s;
}

div[data-testid="stRadio"] label:hover{
    background:#1565C0;
}

/* ================= TITLES ================= */

.main-title{
    font-size:34px;
    font-weight:bold;
    color:#263238;
}

.sub-title{
    color:#64748B;
    margin-top:-5px;
    margin-bottom:25px;
}

/* ================= DATE CARD ================= */

.date-card{
    background:white;
    padding:15px;
    border-radius:16px;
    text-align:center;
    box-shadow:0 4px 12px rgba(0,0,0,0.08);
}

/* ================= METRIC CARD ================= */

.metric-card{
    background:white;
    padding:22px;
    border-radius:20px;
    box-shadow:0 4px 12px rgba(0,0,0,0.08);
    transition:0.3s;
}

.metric-card:hover{
    transform:translateY(-3px);
}

.metric-card div{
    line-height:1.4;
}

.metric-title{
    color:#64748B;
    font-size:14px;
    margin-bottom:10px;
}

.metric-value{
    font-size:34px;
    font-weight:700;
    margin-top:5px;
}

.metric-growth{
    color:#16A34A;
    font-size:13px;
    margin-top:6px;
}

/* ================= PANEL ================= */

.panel{
    background:white;
    padding:22px;
    border-radius:20px;
    box-shadow:0 4px 12px rgba(0,0,0,0.08);
}

/* ================= TABLE ================= */

div[data-testid="stDataFrame"]{
    background:white;
    padding:10px;
    border-radius:18px;
    box-shadow:0 4px 12px rgba(0,0,0,0.08);
}

/* ================= BUTTON ================= */

.stButton>button{
    background:#1E3A8A !important;   /* DARK BLUE */
    color:white !important;
    border:none;
    border-radius:12px;
    padding:10px 18px;
    font-weight:700;
    transition:0.3s;
}

.stButton>button:hover{
    background:#172554 !important;   /* EVEN DARKER BLUE */
    transform:translateY(-2px);
}

.stButton>button:hover{
    background:#1D4ED8 !important;
    transform:translateY(-2px);
}

.stButton>button:hover{
    background:#14B8A6;
    transform:translateY(-2px);
}

/* ================= INPUTS ================= */

.stTextInput input,
.stNumberInput input,
.stSelectbox div{
    border-radius:12px !important;
}


/* ================= QUICK BOX ================= */

.quick-box{
    background:white;
    padding:20px;
    border-radius:18px;
    box-shadow:0 4px 12px rgba(0,0,0,0.08);
}

</style>
""", unsafe_allow_html=True)

st.markdown("""
<style>

/* REMOVE STREAMLIT TOP GAP */
.block-container {
    padding-top: 0.5rem !important;
    padding-bottom: 1rem !important;
}

/* REMOVE EXTRA MAIN WRAPPER GAP */
section.main > div {
    padding-top: 0rem !important;
}

/* REMOVE DEFAULT PAGE MARGIN */
div[data-testid="stAppViewContainer"] {
    padding-top: 0rem !important;
}

/* OPTIONAL CLEAN BACKGROUND FIX */
.stApp {
    margin: 0;
}

</style>
""", unsafe_allow_html=True)

# ================= ADVANCED HELPERS (ML RULE ENGINE) =================

def get_stage(data):

    hba1c = data.get("HbA1c", data.get("HbAIc", 0))
    fbs = data.get("FBS", 0)
    gtt = data.get("GTT", data.get("GTT2Hr", 0))

    if hba1c >= 6.5 or fbs >= 126 or gtt >= 200:
        return "Diabetes Mellitus"

    elif (5.7 <= hba1c < 6.5) or (100 <= fbs < 126) or (140 <= gtt < 200):
        return "Prediabetes"

    return "Normal"




def analyze_values(data):

    report = []

    if data.get("FBS", 0) >= 126:
        report.append(("FBS", "High", "Poor glucose control"))

    elif data.get("FBS", 0) < 70:
        report.append(("FBS", "Low", "Hypoglycemia risk"))

    if data.get("HbA1c", data.get("HbAIc", 0)) >= 6.5:
        report.append(("HbA1c", "High", "Diabetes range"))

    if data.get("LDL", 0) > 160:
        report.append(("LDL", "High", "Heart risk"))

    if data.get("HDL", 0) < 40:
        report.append(("HDL", "Low", "Poor heart protection"))

    if data.get("Triglycerides", 0) > 200:
        report.append(("Triglycerides", "High", "Metabolic risk"))

    if data.get("Creatinine", 0) > 1.3:
        report.append(("Creatinine", "High", "Kidney stress"))

    if data.get("EGFR", 100) < 60:
        report.append(("EGFR", "Low", "Kidney issue"))

    if data.get("SystolicBP", 0) > 140:
        report.append(("Blood Pressure", "High", "Hypertension"))

    if data.get("DiastolicBP", 0) > 90:
        report.append(("Blood Pressure", "High", "Hypertension"))

    return report


def predict_complications(data):

    risks = []

    if data.get("HbA1c", data.get("HbAIc", 0)) > 7:
        risks.append("Neuropathy")

    if data.get("Creatinine", 0) > 1.5:
        risks.append("Nephropathy")

    if data.get("LDL", 0) > 160:
        risks.append("Cardiovascular Disease")

    if data.get("FBS", 0) > 180:
        risks.append("Retinopathy")

    return risks


def give_recommendations(issues):

    recommendations = []

    if not issues:
        return ["Maintain healthy lifestyle"]

    for issue in issues:

        name = issue[0]

        if name in ["FBS", "HbA1c", "HbAIc"]:
            recommendations.append("Control blood sugar with diet & exercise")

        elif name in ["LDL", "Triglycerides"]:
            recommendations.append("Reduce oily and fast foods")

        elif name == "HDL":
            recommendations.append("Increase physical activity")

        elif name in ["Creatinine", "EGFR"]:
            recommendations.append("Monitor kidney function regularly")

        elif name == "Blood Pressure":
            recommendations.append("Control blood pressure")

    return list(set(recommendations))

def build_ml_input(data, model):
    df = pd.DataFrame([data])

    # sirf model ke features rakho
    for col in model.feature_names_in_:
        if col not in df:
            df[col] = 0

    df = df[model.feature_names_in_]

    # convert ALL to numeric (VERY IMPORTANT)
    df = df.apply(pd.to_numeric, errors='coerce').fillna(0)

    return df

    # ================= ML STEP 1 (DIABETES DETECTION) =================

def ml_predict_stage(data):

    import pandas as pd

    df = pd.DataFrame([data])

    # ================= ENCODING =================
    if "Gender" in df.columns:
        df["Gender"] = df["Gender"].map({
            "Male": 1,
            "Female": 0
        })

    # ================= NUMERIC SAFETY =================
    df = df.apply(pd.to_numeric, errors="coerce").fillna(0)

    # ================= FEATURE ALIGNMENT =================
    df = df.reindex(
        columns=model1.feature_names_in_,
        fill_value=0
    )

    # ================= PREDICTION =================
    pred = model1.predict(df)[0]

    # ================= LABEL HANDLING =================
    if isinstance(pred, str):
        return pred

    stages = {
        0: "Normal",
        1: "Prediabetes",
        2: "Diabetes Mellitus"
    }

    return stages.get(pred, "Normal")

# ================= ML STEP 2 (TYPE PREDICTION) =================
def enhance_features(df):

    df = df.copy()

    # Strong pregnancy signal (fix for Gestational miss)
    df["Pregnancy_Risk_Score"] = (
        df["Pregnant"].fillna(0) * 3 +
        df["HistoryOfGDM"].fillna(0) * 2
    )

    # metabolic risk support
    df["Metabolic_Risk"] = (
        df["BMI"].fillna(0) +
        df["FBS"].fillna(0) / 50
    )

    return df
def ml_predict_type(data):

    import pandas as pd

    df = pd.DataFrame([data])

    # binary fix
    binary_cols = ["Pregnant", "HistoryOfGDM", "AntiGad", "IA2A", "ICA", "Smoker"]
    for col in binary_cols:
        if col in df.columns:
            df[col] = df[col].astype(int)

    # numeric safe conversion
    df = df.apply(pd.to_numeric, errors='coerce').fillna(0)

    # 🔥 ADD ENGINEERED FEATURES
    df = enhance_features(df)

    # align features
    df = df.reindex(columns=model2.feature_names_in_, fill_value=0)

    # prediction
    pred = model2.predict(df)[0]

    return pred
# ================= ML STEP 3 (COMPLICATIONS) =================
def ml_predict_complications(data):

    df = pd.DataFrame([data])

    if "Gender" in df.columns:
        df["Gender"] = df["Gender"].map({"Male": 1, "Female": 0})

    df = df.apply(pd.to_numeric, errors='coerce').fillna(0)

    df = df.reindex(columns=model3.feature_names_in_, fill_value=0)

    results = {}

    targets = ["Retinopathy","Nephropathy","Neuropathy","Cardiovascular","FootUlcer"]

    for i, est in enumerate(model3.estimators_):
        prob = est.predict_proba(df)[0][1]
        results[targets[i]] = {
            "probability": round(prob * 100, 2),
            "prediction": int(prob >= 0.55)
        }

    return results

    # ================= FIX 1: CATEGORICAL ENCODING =================
    if "Gender" in df.columns:
        df["Gender"] = df["Gender"].map({"Male": 1, "Female": 0})

    if "Pregnant" in df.columns:
        df["Pregnant"] = df["Pregnant"].astype(int)

    if "Smoker" in df.columns:
        df["Smoker"] = df["Smoker"].astype(int)

    if "AntiGad" in df.columns:
        df["AntiGad"] = df["AntiGad"].astype(int)

    if "IA2A" in df.columns:
        df["IA2A"] = df["IA2A"].astype(int)

    if "ICA" in df.columns:
        df["ICA"] = df["ICA"].astype(int)

    # ================= SAFE NUMERIC CONVERSION =================
    df = df.apply(pd.to_numeric, errors='coerce').fillna(0)

    # ================= ALIGN FEATURES =================
    feature_cols = model3.feature_names_in_
    df = df.reindex(columns=feature_cols, fill_value=0)

    results = {}

    threshold = 0.55

    targets = [
        "Retinopathy",
        "Nephropathy",
        "Neuropathy",
        "Cardiovascular",
        "FootUlcer"
    ]

    for i, est in enumerate(model3.estimators_):

        prob = est.predict_proba(df)[0][1]

        results[targets[i]] = {
            "probability": round(prob * 100, 2),
            "prediction": int(prob >= threshold)
        }

    return results

# ================= GEMINI CONTEXT BUILDER =================

def build_patient_context(patient):

    return f"""
PATIENT DIABETES REPORT

Basic Information:
Name: {patient.get('Name', 'N/A')}
Age: {patient.get('Age', 'N/A')}
Gender: {patient.get('Gender', 'N/A')}

Diagnosis:
Stage: {patient.get('Stage', 'N/A')}
Type: {patient.get('Type', 'N/A')}

Step 1 Values:
FBS: {patient.get('FBS', 'N/A')}
HbA1c: {patient.get('HbA1c', 'N/A')}
BMI: {patient.get('BMI', 'N/A')}
GTT2Hr: {patient.get('GTT2Hr', 'N/A')}
LDL: {patient.get('LDL', 'N/A')}
HDL: {patient.get('HDL', 'N/A')}
FamilyHistory: {patient.get('FamilyHistory', 'N/A')}

Step 2 Values:
Pregnant: {patient.get('Pregnant', 'N/A')}
HistoryOfGDM: {patient.get('HistoryOfGDM', 'N/A')}
InsulinTotalUnits: {patient.get('InsulinTotalUnits', 'N/A')}
Triglycerides: {patient.get('Triglycerides', 'N/A')}
DMDuration: {patient.get('DMDuration', 'N/A')}
DMonSetAge: {patient.get('DMonSetAge', 'N/A')}
AntiGad: {patient.get('AntiGad', 'N/A')}
IA2A: {patient.get('IA2A', 'N/A')}
ICA: {patient.get('ICA', 'N/A')}
Smoker: {patient.get('Smoker', 'N/A')}
Urea: {patient.get('Urea', 'N/A')}
Creatinine: {patient.get('Creatinine', 'N/A')}

Step 3 Values:
EGFR: {patient.get('EGFR', 'N/A')}
SystolicBP: {patient.get('SystolicBP', 'N/A')}
DiastolicBP: {patient.get('DiastolicBP', 'N/A')}

Complications:
{patient.get('Complications', 'None')}

Recommendations:
{patient.get('Recommendations', 'None')}
"""

# ================= GEMINI AI FUNCTION =================

def ask_gemini(patient, question):

    try:
        context = build_patient_context(patient)

        prompt = f"""
You are a professional medical AI assistant for diabetes patients.

You MUST answer ONLY based on patient data.

PATIENT DATA:
{context}

USER QUESTION:
{question}

Rules:
- Be simple and medical
- Do not give random information
- Always relate answer to patient report
"""

        response = model.generate_content(prompt)

        return response.text

    except Exception as e:
        return f"AI Error: {str(e)}"

# ================= LOGIN PAGE =================
# ================= LOGIN PAGE =================
# ================= LOGIN PAGE =================
if not st.session_state.logged_in:

    st.markdown("""
    <style>

    .stApp{
        background: url("https://i.ytimg.com/vi/AxYgzie4x2E/maxresdefault.jpg");
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
    }

    .stApp::before{
        display:none;
    }

    div[data-testid="stAppViewContainer"]{
        min-height:100vh;
    }

    section.main > div{
        width:100%;
    }

    .login-card{
        width:300px;
        background: rgba(0,0,0,0.65);
        padding:28px;
        border-radius:18px;
        box-shadow:0 10px 25px rgba(0,0,0,0.4);
        border:1px solid rgba(255,255,255,0.15);
        backdrop-filter: blur(8px);
    }

    .login-title{
        text-align:center;
        font-size:26px;
        font-weight:800;
        color:white;
        margin-bottom:6px;
    }

    .login-sub{
        text-align:center;
        color:white;
        font-weight:500;
        margin-bottom:18px;
        opacity:0.9;
    }

    .stTextInput label{
        color:white !important;
        font-weight:600;
    }

    .stTextInput input{
        height:42px;
        border-radius:10px !important;
        background:rgba(255,255,255,0.12) !important;
        color:white !important;
        border:1px solid rgba(255,255,255,0.25) !important;
    }

    .stButton > button{
        width:100%;
        height:42px;
        border:none;
        border-radius:10px;
        background:#2563EB;
        color:white;
        font-size:14px;
        font-weight:700;
    }

    .stButton > button:hover{
        background:#1D4ED8;
    }

    </style>
    """, unsafe_allow_html=True)

    # ================= FIXED POSITION CONTROL =================

    # FORCE TOP SPACE
    st.markdown("""
    <div style="height:120px;"></div>
    """, unsafe_allow_html=True)

# YOUR COLUMNS
    left, mid, right, bottom = st.columns([0.05, 0.5, 1.2, 0.05])

    with mid:


    

        username = st.text_input("Username")
        password = st.text_input("Password", type="password")

        if st.button("Login"):

            role = login_user(username, password)

            if role:
                st.session_state.logged_in = True
                st.session_state.role = role
                st.session_state.username = username
                st.rerun()
            else:
                st.error("Invalid username or password")

        st.markdown("</div></div>", unsafe_allow_html=True)

    st.stop()
# ================= SIDEBAR =================
st.sidebar.markdown("""
<div class="logo-box">
    <div class="logo-title">DiabetesCare</div>
    <div class="logo-sub">ML Prediction System</div>
</div>
""", unsafe_allow_html=True)

role = st.session_state.role

if role == "admin":
    menu = st.sidebar.radio(
        "",
        [
            "Dashboard",
            "Patients",
            "New Prediction",
            "Reports",
            "Analytics",
            "Appointments",
            "Users",
        ]
    )

elif role == "patient":
    menu = st.sidebar.radio(
        "",
        [
            "Dashboard",
            "AI Assistant",
            "My Report"
        ]
    )
if st.sidebar.button("Logout"):
    st.session_state.logged_in = False
    st.session_state.role = None
    st.session_state.username = None
    st.rerun()    
role = st.session_state.get("role", "").strip()    

st.markdown("""
<style>

/* REMOVE SIDEBAR TOP GAP */
section[data-testid="stSidebar"] {
    padding-top: 0px !important;
}

/* REMOVE INNER EMPTY SPACING */
section[data-testid="stSidebar"] > div {
    padding-top: 0px !important;
}

/* LOGO FIX ALIGNMENT */
.logo-box{
    text-align:center;
    padding:5px 5px 5px 5px;  /* reduced top padding */
    margin-top:40px;
}

/* REMOVE DEFAULT STREAMLIT BLOCK GAP */
div[data-testid="stSidebarNav"] {
    padding-top: 0px !important;
    margin-top: 0px !important;
}

</style>
""", unsafe_allow_html=True)

import streamlit as st

# ================= SESSION =================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "page" not in st.session_state:
    st.session_state.page = "Dashboard"


def login_user(username, password):
    return "admin" if username == "admin" and password == "123" else None


def set_page(page):
    st.session_state.page = page


# ================= LOGIN =================
if not st.session_state.logged_in:

    st.markdown("""
    <style>

    /* BACKGROUND */
    .stApp{
        background: url("https://i.ytimg.com/vi/AxYgzie4x2E/maxresdefault.jpg");
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
    }

    /* REMOVE OVERLAY */
    .stApp::before{
        display:none;
    }

    /* TOP NAVBAR */
    .navbar{
        position:fixed;
        top:0;
        left:0;
        width:100%;
        height:60px;
        background:rgba(255,255,255,0.85);
        backdrop-filter: blur(10px);
        display:flex;
        justify-content:space-between;
        align-items:center;
        padding:0 30px;
        box-shadow:0 2px 10px rgba(0,0,0,0.08);
        z-index:999;
    }

    .logo{
        font-size:18px;
        font-weight:800;
        color:#2563EB;
    }

    .nav{
        display:flex;
        gap:20px;
        font-size:14px;
        font-weight:600;
        color:#334155;
    }

    .nav span{
        cursor:pointer;
        padding:6px 10px;
        border-radius:8px;
    }

    .nav span:hover{
        background:#EEF2FF;
        color:#2563EB;
    }

    /* LOGIN CENTER */
    .login-wrapper{
        display:flex;
        justify-content:center;
        align-items:center;
        min-height:100vh;
    }

    /* LOGIN CARD */
    .login-card{
        width:320px;
        background:rgba(255,255,255,0.95);
        padding:35px;
        border-radius:18px;
        box-shadow:0 15px 35px rgba(0,0,0,0.15);
        border:1px solid #E2E8F0;
    }

    .login-title{
        text-align:center;
        font-size:26px;
        font-weight:800;
        color:#0F172A;
    }

    .login-sub{
        text-align:center;
        color:#64748B;
        margin-bottom:20px;
    }

    .stTextInput label{
        color:#334155 !important;
        font-weight:600;
    }

    .stTextInput input{
        border-radius:10px !important;
        border:1px solid #CBD5E1 !important;
        height:42px;
    }

    .stButton > button{
        width:100%;
        background:#2563EB;
        color:white;
        font-weight:700;
        border-radius:10px;
        height:42px;
    }

    /* FOOTER */
    .footer{
        position:fixed;
        bottom:0;
        width:100%;
        text-align:center;
        padding:10px;
        font-size:12px;
        background:rgba(255,255,255,0.85);
        backdrop-filter: blur(10px);
        color:#64748B;
    }

    </style>
    """, unsafe_allow_html=True)

    # NAVBAR
    st.markdown("""
    <div class="navbar">
        <div class="logo">🏥 DiabetesCare AI</div>
        <div class="nav">
            <span>Home</span>
            <span>About</span>
            <span>Contact</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # LOGIN UI
    st.markdown("<div class='login-wrapper'>", unsafe_allow_html=True)

    st.markdown("<div class='login-card'>", unsafe_allow_html=True)

    st.markdown("<div class='login-title'>Welcome Back</div>", unsafe_allow_html=True)
    st.markdown("<div class='login-sub'>AI Medical Prediction System</div>", unsafe_allow_html=True)

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):

        role = login_user(username, password)

        if role:
            st.session_state.logged_in = True
            st.session_state.role = role
            st.session_state.username = username
            st.rerun()
        else:
            st.error("Invalid credentials")

    st.markdown("</div></div>", unsafe_allow_html=True)

    # FOOTER
    st.markdown("""
    <div class="footer">
        © 2026 DiabetesCare AI System • Built for Healthcare Intelligence
    </div>
    """, unsafe_allow_html=True)

    st.stop()


# ================= DASHBOARD =================
st.markdown("""
<style>
.page-title{
    font-size:26px;
    font-weight:800;
    margin-top:20px;
    color:#0F172A;
}
.card{
    padding:20px;
    background:white;
    border-radius:12px;
    box-shadow:0 4px 15px rgba(0,0,0,0.08);
}
</style>
""", unsafe_allow_html=True)

# ================= PROFESSIONAL NAVBAR =================
import streamlit as st

# ================= SESSION =================
if "page" not in st.session_state:
    st.session_state.page = "Dashboard"


def set_page(p):
    st.session_state.page = p


# ================= NAVBAR CSS =================
st.markdown("""
<style>

/* ===== NAVBAR ===== */
.navbar {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 65px;
    background: rgba(255,255,255,0.95);
    backdrop-filter: blur(14px);
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 40px;
    border-bottom: 1px solid #E2E8F0;
    box-shadow: 0 2px 12px rgba(0,0,0,0.06);
    z-index: 999;
}

/* LOGO */
.nav-left {
    font-size: 18px;
    font-weight: 800;
    color: #2563EB;
}

/* CENTER NAV */
.nav-center {
    display: flex;
    gap: 10px;
}

/* NAV BUTTONS */
.nav-btn button {
    background: transparent;
    border: 1px solid transparent;
    padding: 8px 14px;
    border-radius: 20px;
    font-size: 14px;
    font-weight: 600;
    color: #334155;
    transition: 0.2s;
}

.nav-btn button:hover {
    background: #EEF2FF;
    color: #2563EB;
    border-color: #BFDBFE;
    transform: translateY(-1px);
}

/* ACTIVE TITLE */
.page-title {
    font-size: 26px;
    font-weight: 800;
    margin-top: 90px;
    color: #0F172A;
}

/* CONTENT CARD */
.card {
    background: white;
    padding: 20px;
    border-radius: 14px;
    box-shadow: 0 4px 15px rgba(0,0,0,0.08);
    margin-top: 20px;
}

</style>
""", unsafe_allow_html=True)




# ================= DASHBOARD =================


if menu == "Dashboard"and role == "admin":

    left,right = st.columns([6,1])

    with left:

        st.markdown(
            '<div class="main-title">Dashboard</div>',
            unsafe_allow_html=True
        )

        st.markdown(
            '<div class="sub-title">Welcome, Dr</div>',
            unsafe_allow_html=True
        )

    with right:

        current_date = datetime.now().strftime("%d %b %Y")

        st.markdown(
            f"""
            <div class="date-card">
                📅<br>
                <b>{current_date}</b>
            </div>
            """,
            unsafe_allow_html=True
        )

    # ================= COUNTS =================

    total_patients = len(st.session_state.patients)

    positive = len([
        p for p in st.session_state.patients
        if p.get("Stage") == "Diabetes Mellitus"
    ])

    negative = len([
        p for p in st.session_state.patients
        if p.get("Stage") == "Normal"
    ])

    risk = len([
        p for p in st.session_state.patients
        if p.get("Stage") == "Prediabetes"
    ])

    reports = total_patients

    # ================= METRIC CARDS =================

    c1,c2,c3,c4 = st.columns(4)

    with c1:

        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-title">👨‍⚕️ Total Patients</div>
                <div class="metric-value" style="color:#0D9488;">{total_patients}</div>
                <div class="metric-growth">↑ Active Records</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with c2:

        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-title">🔵 Predictions Today</div>
                <div class="metric-value" style="color:#2563EB;">{positive + negative + risk}</div>
                <div class="metric-growth">↑ Today's Analysis</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with c3:

        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-title">🔴 Positive Cases</div>
                <div class="metric-value" style="color:#EF4444;">{positive}</div>
                <div class="metric-growth">↑ High Risk</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with c4:

        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-title">🟣 Reports Generated</div>
                <div class="metric-value" style="color:#9333EA;">{reports}</div>
                <div class="metric-growth">↑ PDF Ready</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.write("")

    # ================= TABLE + CHART =================

    col1, gap, col2 = st.columns([1.7, 0.2, 1])

    with col1:

        st.markdown("### Recent Patients")

        if st.session_state.patients:

            df = pd.DataFrame(st.session_state.patients)

            # SAFE FIX FOR OLD DATA
            if "Type" not in df.columns:
                df["Type"] = "N/A"

            if "Stage" not in df.columns:
                df["Stage"] = "N/A"

            st.dataframe(
                df[[
                    "ID",
                    "Name",
                    "Age",
                    "Gender",
                    "Stage",
                    "Type"
                ]],
                use_container_width=True,
                hide_index=True
            )

        else:
            st.info("No Patients Added Yet")

    with gap:
        st.write("")

    with col2:

        st.markdown("### Prediction Overview")

        fig = go.Figure(data=[go.Pie(
            labels=["Positive","Negative","Prediabetes"],
            values=[positive,negative,risk],
            hole=.70,
            marker=dict(colors=["#EF4444", "#2563EB", "#22C55E"])  # RED / BLUE / GREEN
        )])

        fig.update_layout(
            height=420,
            
            paper_bgcolor="white"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )
        
# ================= NEW PREDICTION =================
# ================= NEW PREDICTION =================

elif menu == "New Prediction" and role == "admin":

    # ================= SESSION STEP =================

    if "prediction_step" not in st.session_state:
        st.session_state.prediction_step = 1

    step = st.session_state.prediction_step

    # ================= EXTRA CSS =================

    st.markdown("""
    <style>

    .prediction-card{
        background:white;
        padding:10px;
        border-radius:20px;
        box-shadow:0 4px 12px rgba(0,0,0,0.08);
        border-top:5px solid #1565C0;
        margin-bottom:40px;
    }

    .section-title{
        font-size:28px;
        font-weight:700;
        color:#263238;
        margin-bottom:5px;
    }

    .section-sub{
        color:#64748B;
        margin-bottom:25px;
    }

    .step-wrap{
        display:flex;
        align-items:center;
        justify-content:space-between;
        margin-bottom:35px;
    }

    .step-box{
        text-align:center;
        flex:1;
    }

    .step-circle{
        width:45px;
        height:45px;
        border-radius:50%;
        display:flex;
        align-items:center;
        justify-content:center;
        margin:auto;
        color:white;
        font-weight:bold;
        font-size:18px;
    }

    .active-step{
        background:#1565C0;
    }

    .inactive-step{
        background:#B0BEC5;
    }

    .complete-step{
        background:#2E7D32;
    }

    .step-text{
        margin-top:10px;
        font-size:15px;
        font-weight:600;
        color:#263238;
    }

    .step-subtext{
        font-size:13px;
        color:#64748B;
        margin-top:3px;
    }

    .line{
        height:4px;
        background:#D1D5DB;
        flex:1;
        margin:0 10px;
        margin-top:-25px;
    }

    .result-box{
        background:#F8FAFC;
        padding:18px;
        border-radius:16px;
        margin-top:12px;
        border-left:5px solid #1565C0;
    }
   
    </style>
    """, unsafe_allow_html=True)

    # ================= TITLE =================

    st.markdown(
    '<div class="main-title">New Prediction</div>',
    unsafe_allow_html=True
)

    st.markdown(
        f'<div class="sub-title">Step {st.session_state.prediction_step} of 3</div>',
        unsafe_allow_html=True
    )

    # ================= PROGRESS BAR =================

    c1, c2, c3, c4, c5 = st.columns([1,0.5,1,0.5,1])

    with c1:

        if step > 1:
            cls = "complete-step"
            icon = "✓"
        else:
            cls = "active-step"

            icon = "1"

        st.markdown(f"""
        <div class="step-box">
            <div class="step-circle {cls}">{icon}</div>
            <div class="step-text">Detect Diabetes</div>
            <div class="step-subtext">Patient Details</div>
        </div>
        """, unsafe_allow_html=True)

    with c2:
        st.markdown('<div class="line"></div>', unsafe_allow_html=True)

    with c3:

        if step > 2:
            cls = "complete-step"
            icon = "✓"

        elif step == 2:
            cls = "active-step"
            icon = "2"

        else:
            cls = "inactive-step"
            icon = "2"

        st.markdown(f"""
        <div class="step-box">
            <div class="step-circle {cls}">{icon}</div>
            <div class="step-text">Etiological Type</div>
            <div class="step-subtext">Patient Details</div>
        </div>
        """, unsafe_allow_html=True)

    with c4:
        st.markdown('<div class="line"></div>', unsafe_allow_html=True)

    with c5:

        if step == 3:
            cls = "active-step"
        else:
            cls = "inactive-step"

        st.markdown(f"""
        <div class="step-box">
            <div class="step-circle {cls}">3</div>
            <div class="step-text">Detect Complications</div>
            <div class="step-subtext">Patient Details</div>
        </div>
        """, unsafe_allow_html=True)

    st.write("")

    # =========================================================
    # ================= STEP 1 =================
    # =========================================================
    

    if step == 1:

        st.markdown("""
        <div class="prediction-card">

        <div class="section-title">
        Patient Details
        </div>

        <div class="section-sub">
        Enter patient information for diabetes detection
        </div>

        </div>
        """, unsafe_allow_html=True)

        left,right = st.columns(2)

        with left:

            st.markdown("**Patient Name**")
            name = st.text_input(
                "",
                placeholder="Enter patient name",
                label_visibility="collapsed"
            )

            st.markdown("**Age**")
            st.caption("Range: 1 - 120 Years")

            age = st.number_input(
                "",
                min_value=1,
                max_value=120,
                step=1,
                label_visibility="collapsed"
            )

            st.markdown("**BMI**")
            st.caption("Range: 10.00 - 60.00 | Example: 28.50")

            bmi = st.number_input(
                "",
                min_value=10.00,
                max_value=60.00,
                format="%.2f",
                label_visibility="collapsed"
            )

            st.markdown("**Fasting Blood Sugar (FBS)**")
            st.caption("Range: 50.00 - 500.00 mg/dL | Example: 126.00")

            fbs = st.number_input(
                "",
                min_value=50.00,
                max_value=500.00,
                format="%.2f",
                label_visibility="collapsed"
            )

            st.markdown("**HbA1c (%)**")
            st.caption("Range: 3.00 - 20.00 | Example: 6.80")

            hba1c = st.number_input(
                "",
                min_value=3.00,
                max_value=20.00,
                format="%.2f",
                label_visibility="collapsed"
            )

            st.markdown("**Contact Number**")
            st.caption("Format: 03XX-XXXXXXX")

            contact = st.text_input(
                "",
                placeholder="03XX-XXXXXXX",
                label_visibility="collapsed"
            )

        with right:

            st.markdown("**Gender**")

            gender = st.selectbox(
                "",
                ["Male", "Female"],
                label_visibility="collapsed"
            )

            st.markdown("**Family History of Diabetes**")

            family_history = st.selectbox(
                "",
                ["Yes", "No"],
                label_visibility="collapsed"
            )

            st.markdown("**2-Hour Glucose (GTT2Hr)**")
            st.caption("Range: 50.00 - 600.00 mg/dL | Example: 180.00")

            gtt = st.number_input(
                "",
                min_value=50.00,
                max_value=600.00,
                format="%.2f",
                label_visibility="collapsed"
            )

            st.markdown("**LDL Cholesterol**")
            st.caption("Range: 20.00 - 300.00 mg/dL | Example: 120.00")

            ldl = st.number_input(
                "",
                min_value=20.00,
                max_value=300.00,
                format="%.2f",
                label_visibility="collapsed"
            )

            st.markdown("**HDL Cholesterol**")
            st.caption("Range: 10.00 - 150.00 mg/dL | Example: 45.00")

            hdl = st.number_input(
                "",
                min_value=10.00,
                max_value=150.00,
                format="%.2f",
                label_visibility="collapsed"
            )
       

        # ================= STEP 1 BUTTON =================
        # ================= STEP 1 BUTTON =================
        
        # ================= STEP 1 BUTTON =================
        if st.button("Get prediction →"):

            if name.strip() == "" or age <= 0 or bmi <= 0 or fbs <= 0 or hba1c <= 0:

                st.error("⚠ Please fill complete patient information")

            else:

                # ================= PATIENT OBJECT =================
                patient = {
                    "Name": name,
                    "Contact": contact,
                    "Age": age,
                    "Gender": 1 if gender == "Male" else 0,
                    "BMI": bmi,
                    "FBS": fbs,
                    "GTT2Hr": gtt,
                    "HbA1c": hba1c,
                    "LDL": ldl,
                    "HDL": hdl,
                    "FamilyHistory": 1 if family_history == "Yes" else 0
                }

                # ================= ML PREDICTION (STEP 1) =================
                stage = ml_predict_stage(patient)
                patient["Stage"] = stage

                # ================= RISK SCORE =================
                import pandas as pd

                df = pd.DataFrame([patient])
                df = df.apply(pd.to_numeric, errors='coerce').fillna(0)

                df = df.reindex(columns=model1.feature_names_in_, fill_value=0)

                proba = model1.predict_proba(df)[0]
                risk_score = (proba[1] + proba[2]) * 100

                # ================= SESSION =================
                st.session_state.patient_data = patient
                st.session_state.stage = stage
                st.session_state.risk_score = risk_score
                st.session_state.show_result = True

                # ======================================================
                # SAVE ONLY NORMAL + PREDIABETES HERE
                # ======================================================

                if stage != "Diabetes Mellitus":

                    try:

                        add_patient(patient)
                        st.session_state.patients = get_patients()

                        # ================= AUTO APPOINTMENT =================

                        appointments = get_appointments()

                        doctor = "Dr. Ali Raza"
                        room = "Room 202"

                        appointment_date = (
                            datetime.now() + timedelta(days=30)
                        ).strftime("%d %b %Y")

                        same_day_doctor = [
                            a for a in appointments
                            if a[2] == doctor and a[4] == appointment_date
                        ]

                        slots = [
                            "09:00 AM",
                            "09:30 AM",
                            "10:00 AM",
                            "10:30 AM",
                            "11:00 AM",
                            "11:30 AM",
                            "12:00 PM"
                        ]

                        slot_index = len(same_day_doctor)

                        if slot_index >= len(slots):
                            appointment_date = (
                                datetime.now() + timedelta(days=31)
                            ).strftime("%d %b %Y")
                            slot_index = 0

                        appointment_time = slots[slot_index]

                        add_appointment(
                            patient["Name"],
                            doctor,
                            "Follow-up",
                            appointment_date,
                            appointment_time,
                            "Upcoming",
                            patient.get("Contact", ""),
                            room
                        )

                        st.success("Patient saved successfully ✔")

                    except Exception as e:

                        st.error(f"DB Error: {e}")


        # ================= RESULT DISPLAY =================
        if st.session_state.get("show_result", False):

            stage = st.session_state.stage
            risk_score = st.session_state.get("risk_score", 0)

            # ================= RISK BAR =================
            st.markdown(f"### Risk Score: {risk_score:.1f}%")
            st.progress(int(risk_score))

            # ================= RESULT LOGIC =================

            if stage == "Normal":

                color = "#10B981"
                bg = "#ECFDF5"

                title = "✅ NORMAL"
                subtitle = f"Risk Score: {risk_score:.1f}%"

                recommendations = [
                    "Maintain healthy diet",
                    "Exercise regularly",
                    "Annual diabetes screening",
                    "Avoid excessive sugar intake"
                ]

            elif stage == "Prediabetes":

                color = "#F59E0B"
                bg = "#FFFBEB"

                title = "⚠ PREDIABETES"
                subtitle = f"Risk Score: {risk_score:.1f}%"

                recommendations = [
                    "Reduce sugar intake",
                    "Daily walking recommended",
                    "Weight management required",
                    "Monitor glucose regularly"
                ]

            else:

                color = "#EF4444"
                bg = "#FEF2F2"

                title = "🚨 DIABETES MELLITUS"
                subtitle = f"Risk Score: {risk_score:.1f}%"

                recommendations = [
                    "Immediate doctor consultation",
                    "HbA1c monitoring required",
                    "Strict diabetic diet",
                    "Medical treatment required"
                ]

            # ================= CARD =================
            with st.container():

                

                # TITLE
                st.markdown(
                    f"""
                    <h2 style="
                        color:{color};
                        margin-bottom:8px;
                        font-size:30px;
                        font-weight:800;
                    ">
                        {title}
                    </h2>
                    """,
                    unsafe_allow_html=True
                )

                # SUBTITLE
                st.markdown(
                    f"""
                    <div style="
                        color:#475569;
                        font-size:16px;
                        margin-bottom:20px;
                    ">
                        {subtitle}
                    </div>
                    """,
                    unsafe_allow_html=True
                )

                # RECOMMENDATION TITLE
                st.markdown(
                    """
                    <h3 style="
                        color:#0F172A;
                        margin-bottom:15px;
                    ">
                        🩺 Recommendations
                    </h3>
                    """,
                    unsafe_allow_html=True
                )

                # RECOMMENDATIONS
                for rec in recommendations:

                    st.markdown(
                        f"""
                        <div style="
                            background:white;
                            padding:12px 16px;
                            border-radius:12px;
                            margin-bottom:10px;
                            border:1px solid #E2E8F0;
                            color:#334155;
                            font-weight:500;
                        ">
                            ✔ {rec}
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

                st.markdown("</div>", unsafe_allow_html=True)
                    
            # ================= STEP 2 =================
            if stage == "Diabetes Mellitus":

                if st.button("Continue to Step 2 ➡"):

                    st.session_state.prediction_step = 2
                    st.rerun()
    # =========================================================
    # ================= STEP 2 ================================
    # =========================================================

    elif step == 2:

        st.markdown("""
        <div class="prediction-card">

        <div class="section-title">
        Patient Details
        </div>

        <div class="section-sub">
        Enter patient information for etiological type detection
        </div>

        </div>
        
        """, unsafe_allow_html=True)

        left,right = st.columns(2)

        with left:

            st.markdown("**Pregnant (0/1)**")
            pregnant = st.number_input(
                "",
                min_value=0,
                max_value=1,
                step=1,
                key="pregnant",
                label_visibility="collapsed"
            )

            st.markdown("**History of GDM (0/1)**")
            history_gdm = st.number_input(
                "",
                min_value=0,
                max_value=1,
                step=1,
                key="history_gdm",
                label_visibility="collapsed"
            )

            st.markdown("**Insulin Total Units**")
            st.caption("Range: 0 - 500 | Example: 35.50")
            insulin = st.number_input(
                "",
                min_value=0.0,
                max_value=500.0,
                step=0.1,
                format="%.2f",
                key="insulin",
                label_visibility="collapsed"
            )

            st.markdown("**Triglycerides**")
            st.caption("Range: 0 - 1000 mg/dL | Example: 150.75")
            triglycerides = st.number_input(
                "",
                min_value=0.0,
                max_value=1000.0,
                step=0.1,
                format="%.2f",
                key="triglycerides",
                label_visibility="collapsed"
            )

            st.markdown("**DM Duration**")
            st.caption("Range: 0 - 80 years | Example: 8.50")
            dm_duration = st.number_input(
                "",
                min_value=0.0,
                max_value=80.0,
                step=0.1,
                format="%.2f",
                key="dm_duration",
                label_visibility="collapsed"
            )

            st.markdown("**DM Onset Age**")
            st.caption("Range: 1 - 120 years | Example: 25.00")
            onset_age = st.number_input(
                "",
                min_value=1.0,
                max_value=120.0,
                step=0.1,
                format="%.2f",
                key="onset_age",
                label_visibility="collapsed"
            )


        with right:

            st.markdown("**AntiGAD (0/1)**")
            antigad = st.number_input(
                "",
                min_value=0,
                max_value=1,
                step=1,
                key="antigad",
                label_visibility="collapsed"
            )

            st.markdown("**IA2A (0/1)**")
            ia2a = st.number_input(
                "",
                min_value=0,
                max_value=1,
                step=1,
                key="ia2a",
                label_visibility="collapsed"
            )

            st.markdown("**ICA (0/1)**")
            ica = st.number_input(
                "",
                min_value=0,
                max_value=1,
                step=1,
                key="ica",
                label_visibility="collapsed"
            )

            st.markdown("**Smoker (0/1)**")
            smoker = st.number_input(
                "",
                min_value=0,
                max_value=1,
                step=1,
                key="smoker",
                label_visibility="collapsed"
            )

            st.markdown("**Urea**")
            st.caption("Range: 0 - 300 mg/dL | Example: 28.50")
            urea = st.number_input(
                "",
                min_value=0.0,
                max_value=300.0,
                step=0.1,
                format="%.2f",
                key="urea",
                label_visibility="collapsed"
            )

            st.markdown("**Creatinine**")
            st.caption("Range: 0 - 20 mg/dL | Example: 1.20")
            creatinine = st.number_input(
                "",
                min_value=0.0,
                max_value=20.0,
                step=0.01,
                format="%.2f",
                key="creatinine",
                label_visibility="collapsed"
            )
        

        # ================= STEP 2 BUTTONS =================

        col_back, col_next = st.columns([1,1])

        with col_back:

            if st.button("⬅ Back"):

                st.session_state.prediction_step = 1
                st.rerun()

        with col_next:

            if st.button("Next ➡"):

                missing_fields = []

                if insulin <= 0:
                    missing_fields.append("Insulin")
                if triglycerides <= 0:
                    missing_fields.append("Triglycerides")
                if dm_duration <= 0:
                    missing_fields.append("DM Duration")
                if onset_age <= 0:
                    missing_fields.append("DM Onset Age")
                if urea <= 0:
                    missing_fields.append("Urea")
                if creatinine <= 0:
                    missing_fields.append("Creatinine")

                if missing_fields:
                    st.error("⚠ Please fill all required fields: " + ", ".join(missing_fields))

                else:

                    st.session_state.patient_data.update({

                        "Pregnant": pregnant,
                        "HistoryOfGDM": history_gdm,
                        "InsulinTotalUnits": insulin,
                        "Triglycerides": triglycerides,
                        "DMDuration": dm_duration,
                        "DMonSetAge": onset_age,
                        "AntiGad": antigad,
                        "IA2A": ia2a,
                        "ICA": ica,
                        "Smoker": smoker,
                        "Urea": urea,
                        "Creatinine": creatinine
                    })

                    patient = st.session_state.patient_data
                    patient["Type"] = ml_predict_type(patient)

                    st.session_state.prediction_step = 3
                    st.rerun()

    # =========================================================
    # ================= STEP 3 ================================
    # =========================================================

    elif step == 3:

        st.markdown("""
        <div class="prediction-card">

        <div class="section-title">
        Patient Details
        </div>

        <div class="section-sub">
        Enter patient information for detect complications
        </div>

        </div>
        """, unsafe_allow_html=True)

        patient = st.session_state.patient_data

        left, right = st.columns(2)

        with left:

            st.markdown("**EGFR**")
            st.caption("Range: 0 - 200 mL/min/1.73m²")
            egfr = st.number_input(
                "",
                min_value=0.0,
                max_value=200.0,
                value=90.0,
                step=0.1,
                format="%.2f",
                label_visibility="collapsed"
            )

            st.markdown("**Systolic BP**")
            st.caption("Range: 50 - 250 mmHg")
            systolic = st.number_input(
                "",
                min_value=50.0,
                max_value=250.0,
                value=120.0,
                step=1.0,
                format="%.2f",
                label_visibility="collapsed"
            )

            st.markdown("**Diastolic BP**")
            st.caption("Range: 30 - 150 mmHg")
            diastolic = st.number_input(
                "",
                min_value=30.0,
                max_value=150.0,
                value=80.0,
                step=1.0,
                format="%.2f",
                label_visibility="collapsed"
            )
            if "show_summary" not in st.session_state:
                st.session_state.show_summary = False

            st.markdown("### 👤 Patient Summary")

            if st.button("Show / Hide Summary"):
                st.session_state.show_summary = not st.session_state.show_summary
                st.rerun()

            if st.session_state.show_summary:

                st.markdown(f"""
                <div class="result-box">

                <b>Name:</b> {patient['Name']}<br><br>
                <b>Age:</b> {patient['Age']}<br><br>
                <b>BMI:</b> {patient['BMI']}<br><br>
                <b>FBS:</b> {patient['FBS']}<br><br>
                <b>HbA1c:</b> {patient['HbA1c']}<br><br>
                <b>LDL:</b> {patient['LDL']}<br><br>
                <b>HDL:</b> {patient['HDL']}

                </div>
                """, unsafe_allow_html=True)

            if st.button("⬅ Back"):
                st.session_state.prediction_step = 2
                st.rerun()

        with right:

            st.markdown("### 📊 Prediction Preview")

            if st.button("Generate Final Prediction"):

                missing_fields = []

                if egfr <= 0:
                    missing_fields.append("EGFR")
                if systolic <= 0:
                    missing_fields.append("Systolic BP")
                if diastolic <= 0:
                    missing_fields.append("Diastolic BP")

                if missing_fields:
                    st.error("⚠ Please fill: " + ", ".join(missing_fields))

                else:

                    # ================= GET DATA =================
                    patient = st.session_state.patient_data.copy()

                    patient["EGFR"] = egfr
                    patient["SystolicBP"] = systolic
                    patient["DiastolicBP"] = diastolic

                    # ================= COMPPLICATIONS =================
                    comp_data = ml_predict_complications(patient)

                    complications = [
                        k for k, v in comp_data.items()
                        if v["prediction"] == 1
                    ]

                    patient["Complications"] = ", ".join(complications) if complications else ""

                    # ================= STAGE =================
                    stage = st.session_state.get("stage")

                    # ================= RECOMMENDATIONS =================
                    if stage == "Diabetes Mellitus":
                        recommendations = [
                            "Immediate doctor consultation",
                            "HbA1c monitoring required",
                            "Strict diabetic diet",
                            "Regular insulin monitoring",
                            "Daily exercise recommended"
                        ]

                    elif stage == "Prediabetes":
                        recommendations = [
                            "Reduce sugar intake",
                            "Weight management required",
                            "Regular glucose monitoring",
                            "Daily walking recommended"
                        ]

                    else:
                        recommendations = [
                            "Maintain healthy lifestyle",
                            "Annual diabetes screening",
                            "Balanced diet",
                            "Regular exercise"
                        ]

                    # IMPORTANT FIX: string convert for DB
                    patient["Recommendations"] = ", ".join(recommendations)

                    # ================= SAVE =================
                    st.session_state.patient_data = patient
                    add_patient(patient)
                    st.session_state.patients = get_patients()
                    appointments = get_appointments()

                    doctor = "Dr. Sarah Khan"
                    room = "Room 203"

                    appointment_date = (
                        datetime.now() + timedelta(days=7)
                    ).strftime("%d %b %Y")

                    same_day_doctor = [
                        a for a in appointments
                        if a[2] == doctor and a[4] == appointment_date
                    ]

                    slots = [
                        "10:00 AM",
                        "10:30 AM",
                        "11:00 AM",
                        "11:30 AM",
                        "12:00 PM",
                        "12:30 PM",
                        "01:00 PM",
                        "01:30 PM",
                        "02:00 PM",
                        "02:30 PM",
                        "03:00 PM"
                    ]

                    slot_index = len(same_day_doctor)

                    if slot_index >= len(slots):
                        appointment_date = (
                            datetime.now() + timedelta(days=8)
                        ).strftime("%d %b %Y")
                        slot_index = 0

                    appointment_time = slots[slot_index]

                    add_appointment(
                        patient["Name"],
                        doctor,
                        "Consultation",
                        appointment_date,
                        appointment_time,
                        "Upcoming",
                        patient.get("Contact", ""),
                        room
                    )

                    dtype = patient.get("Type", "N/A")
                    risk_score = st.session_state.get("risk_score", 0)
                    if stage == "Diabetes Mellitus":
                        
                        result_text = "POSITIVE"
                        result_color = "#EF4444"
                        risk_text = "High Risk"

                    elif stage == "Prediabetes":
                        
                        result_text = "PRE-DIABETES"
                        result_color = "#F59E0B"
                        risk_text = "Moderate Risk"

                    else:
                        
                        result_text = "NEGATIVE"
                        result_color = "#10B981"
                        risk_text = "Low Risk"

                    complications_text = patient.get("Complications", "None")

                    recommendations_html = "".join(
                        f"<li>{r}</li>" for r in recommendations
                    )

                    html_code = f"""
                    <style>
                    .wrapper {{ width:100%; font-family: Arial; }}
                    .result-main {{
                        background:white;
                        padding:20px;
                        border-radius:20px;
                        box-shadow:0 4px 14px rgba(0,0,0,0.08);
                    }}
                    .result-grid {{
                        display:grid;
                        grid-template-columns:repeat(auto-fit, minmax(220px, 1fr));
                        gap:15px;
                    }}
                    .result-card {{
                        background:#F8FAFC;
                        padding:18px;
                        border-radius:16px;
                        border:1px solid #E2E8F0;
                    }}
                    .risk-bar {{
                        height:10px;
                        background:#E5E7EB;
                        border-radius:20px;
                        overflow:hidden;
                    }}
                    .risk-fill {{
                        height:100%;
                        width:{risk_score}%;
                        background:#EF4444;
                    }}
                    </style>

                    <div class="wrapper">
                    <div class="result-main">

                    <div class="result-grid">

                        <div class="result-card">
                            <b>Prediction:</b>
                            <div style="color:{result_color};font-size:20px;">
                                {result_text}
                            </div>
                            <div>{risk_text}</div>
                        </div>

                        <div class="result-card">
                            <b>Type:</b><br>{dtype}
                        </div>

                        <div class="result-card">
                            <b>Stage:</b><br>{stage}
                        </div>

                        <div class="result-card">
                            <b>Risk Score:</b>
                            <div>{risk_score}%</div>
                            <div class="risk-bar">
                                <div class="risk-fill"></div>
                            </div>
                        </div>

                        <div class="result-card">
                            <b>Complications:</b><br>
                            {complications_text}
                        </div>

                        <div class="result-card">
                            <b>Recommendations:</b>
                            <ul>{recommendations_html}</ul>
                        </div>

                    </div>
                    </div>
                    </div>
                    """

                    import streamlit.components.v1 as components
                    components.html(html_code, height=700)

                    st.success("Prediction Generated Successfully ✔")
                
# ================= PATIENTS =================

# ================= PATIENTS =================

if menu == "Patients" and role == "admin":
    st.markdown("""
<div style="margin-bottom:10px;">
    <div style="font-size:32px;font-weight:700;color:#111827;">
        Patients
    </div>
    <div style="font-size:14px;color:#6B7280;margin-top:4px;">
        Manage all registered patients and their medical records
    </div>
</div>
""", unsafe_allow_html=True)

    import math
    import pandas as pd
    from database import delete_patient, get_patients

    # ================= ALWAYS FRESH DATA =================
    st.session_state.patients = get_patients()

    df = pd.DataFrame(st.session_state.patients)

    if df.empty:
        st.info("No patients found")
        st.stop()

    df = df.fillna("N/A")

    # ================= FORCE COLUMN ORDER =================
    cols_order = [
        "ID","Name","Age","Gender","Contact",
        "Stage","Type","BMI","FBS","HbA1c","LDL","HDL",
        "Pregnant","HistoryOfGDM","Insulin","Triglycerides",
        "DMDuration","OnsetAge","AntiGad","IA2A","ICA",
        "Smoker","Urea","Creatinine",
        "EGFR","SystolicBP","DiastolicBP",
        "Complications","Date"
    ]

    for c in cols_order:
        if c not in df.columns:
            df[c] = "N/A"

    df = df[cols_order]

    # ================= STATUS =================
    def status_map(stage):
        if stage == "Diabetes Mellitus":
            return "Positive"
        elif stage == "Prediabetes":
            return "At Risk"
        return "Negative"

    df["Status"] = df["Stage"].apply(status_map)

    # ================= FILTERS =================
    c1, c2, c3 = st.columns([3, 2, 2])

    search = c1.text_input("🔍 Search patient")
    status_filter = c2.selectbox("Status", ["All", "Positive", "Negative", "At Risk"])
    gender_filter = c3.selectbox("Gender", ["All", "Male", "Female"])

    filtered = df.copy()

    if search:
        filtered = filtered[filtered["Name"].astype(str).str.contains(search, case=False)]

    if status_filter != "All":
        filtered = filtered[filtered["Status"] == status_filter]

    if gender_filter != "All":
        filtered = filtered[filtered["Gender"] == gender_filter]

    # ================= PAGINATION =================
    ROWS = 8
    total_pages = max(1, math.ceil(len(filtered) / ROWS))

    page = st.session_state.get("current_page", 1)

    start = (page - 1) * ROWS
    end = start + ROWS

    page_df = filtered.iloc[start:end].reset_index(drop=True)

    # ================= TABLE =================
    st.markdown('<div class="patient-table">', unsafe_allow_html=True)

    headers = [
        "ID","Name","Age","Gender","Contact",
        "Date","Complications","Status","Action"
    ]

    cols = st.columns(len(headers))

    for i, h in enumerate(headers):
        cols[i].markdown(f"**{h}**")

    for i, (_, row) in enumerate(page_df.iterrows()):

        cols = st.columns(len(headers))

        # ================= FIXED ID NUMBERING =================
        pid = start + i + 1

        cols[0].markdown(f"""
        <div style="
            background:#1E3A8A;
            color:#FFFFFF;
            padding:12px 10px;
            border-radius:11px;
            font-weight:800;
            text-align:center;
            display:inline-block;
            min-width:50px;
            font-size:13px;">
            {pid}
        </div>
        """, unsafe_allow_html=True)
        cols[1].write(row["Name"])
        cols[2].write(row["Age"])
        cols[3].write(row["Gender"])
        cols[4].write(row["Contact"])
        cols[5].write(row["Date"])

        # ================= CLEAN TEXT =================
        comp = str(row["Complications"])
        if comp in ["nan", "None", "N/A"]:
            comp = "N/A"

        cols[6].write(comp)

        # ================= STATUS BADGE =================
        status = row["Status"]

        if status == "Positive":
            color = "#EF4444"
            bg = "#FEE2E2"
        elif status == "At Risk":
            color = "#F59E0B"
            bg = "#FEF3C7"
        else:
            color = "#10B981"
            bg = "#D1FAE5"

        cols[7].markdown(f"""
        <div style="
            background:{bg};
            color:{color};
            padding:6px 10px;
            border-radius:12px;
            font-weight:600;
            text-align:center;
            font-size:13px;">
            {status}
        </div>
        """, unsafe_allow_html=True)

        # ================= DELETE =================
        if cols[8].button("🗑", key=f"del_{row['ID']}_{row.name}"):
            delete_patient(row["ID"])
            st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)

    # ================= PAGINATION =================
    c1, c2, c3 = st.columns([1, 2, 1])

    with c1:
        if st.button("⬅ Prev"):
            st.session_state.current_page = max(1, page - 1)
            st.rerun()

    with c2:
        st.markdown(f"<center><b>Page {page} of {total_pages}</b></center>", unsafe_allow_html=True)

    with c3:
        if st.button("Next ➡"):
            st.session_state.current_page = min(total_pages, page + 1)
            st.rerun()

# ================= REPORTS =================

elif menu == "Reports":

    import pandas as pd
    import math
    from datetime import datetime

    if "selected_patient" not in st.session_state:
        st.session_state.selected_patient = None

    if "report_page" not in st.session_state:
        st.session_state.report_page = 1

    st.markdown('<div class="main-title">Reports</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">View and manage all generated reports</div>', unsafe_allow_html=True)

    # ================= DATA =================
    if st.session_state.patients:

        df = pd.DataFrame(st.session_state.patients)

        defaults = {
            "Type": "-",
            "Stage": "Normal",
            "Date": datetime.now().strftime("%d %b %Y"),
            "Recommendations": "-",
            "Complications": "-",
            "FBS": "-",
            "HbA1c": "-",
            "BMI": "-",
            "SystolicBP": "-",
            "DiastolicBP": "-",
            "LDL": "-",
        }

        for k, v in defaults.items():
            if k not in df.columns:
                df[k] = v

        def report_status(stage):
            if stage == "Diabetes Mellitus":
                return "Positive"
            elif stage == "Prediabetes":
                return "At Risk"
            return "Negative"

        df["Result"] = df["Stage"].apply(report_status)

        # ================= DETAIL VIEW =================
        if st.session_state.selected_patient is not None:

            patient = dict(st.session_state.selected_patient)

            recs = patient.get("Recommendations", "-")
            rec_list = [r.strip() for r in str(recs).split(",") if r.strip()]

            st.markdown("""
            <style>
            .profile-icon{
                width:120px;
                height:120px;
                border-radius:50%;
                display:flex;
                align-items:center;
                justify-content:center;
                font-size:55px;
                color:white;
                margin:auto;
                box-shadow:0 6px 18px rgba(30,58,138,0.4);
            }

            .patient-name{
            text-align:center;
            font-size:28px;
            font-weight:600;
            margin-top:14px;
            color:#111827;
            }

            .rec-box{
                background:white;
                padding:18px;
                border-radius:16px;
                box-shadow:0 4px 12px rgba(0,0,0,0.06);
                margin-top:15px;
            }

            .rec-title{
                font-size:18px;
                font-weight:700;
                margin-bottom:10px;
                color:#111827;
            }

            .rec-item{
                background:#F3F4F6;
                padding:10px 12px;
                border-radius:10px;
                margin-bottom:8px;
                border-left:4px solid #1E3A8A;
                font-size:14px;
            }
            </style>
            """, unsafe_allow_html=True)

            if st.button("⬅ Back to Reports"):
                st.session_state.selected_patient = None
                st.rerun()

            left, right = st.columns([1, 2])

            with left:

                st.markdown("<div class='profile-icon'>👤</div>", unsafe_allow_html=True)
                st.markdown(
                f"<div class='patient-name'>{patient.get('Name','-')}</div>",
                unsafe_allow_html=True
                )
                st.markdown(f"**Patient ID:** {patient.get('ID','-')}")
                st.markdown(f"**Age:** {patient.get('Age','-')}")
                st.markdown(f"**Gender:** {patient.get('Gender','-')}")
                st.markdown(f"**Stage:** {patient.get('Stage','-')}")
                st.markdown(f"**Type:** {patient.get('Type','-')}")
                st.markdown(f"**Result:** {patient.get('Result','Negative')}")
                st.markdown(f"**Date:** {patient.get('Date','-')}")

            with right:

                st.subheader("Prediction History")

                st.dataframe(pd.DataFrame([{
                    "Date": patient.get("Date","-"),
                    "Result": patient.get("Result","-"),
                    "Stage": patient.get("Stage","-"),
                    "Type": patient.get("Type","-")
                }]), use_container_width=True, hide_index=True)

                st.subheader("Lab Results")

                st.dataframe(pd.DataFrame([{
                    "FBS": patient.get("FBS","-"),
                    "HbA1c": patient.get("HbA1c","-"),
                    "BMI": patient.get("BMI","-"),
                    "BP": f"{patient.get('SystolicBP','-')}/{patient.get('DiastolicBP','-')}",
                    "LDL": patient.get("LDL","-")
                }]), use_container_width=True, hide_index=True)

                st.subheader("Recommendations")

                if rec_list:
                    for r in rec_list:
                        st.markdown(f"""
                        <div style="
                            background:#EEF2FF;
                            padding:10px;
                            margin-bottom:8px;
                            border-radius:10px;
                            border-left:4px solid #1E3A8A;
                        ">
                        ✔ {r}
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.info("No recommendations")

        # ================= TABLE VIEW =================
        else:

            headers = ["ID","Name","Result","Type","Stage","Date","Action"]

            ROWS_PER_PAGE = 10

            total_pages = max(1, math.ceil(len(df) / ROWS_PER_PAGE))

            page = st.session_state.report_page

            start = (page - 1) * ROWS_PER_PAGE
            end = start + ROWS_PER_PAGE

            page_df = df.iloc[start:end].reset_index(drop=True)

            cols = st.columns(len(headers))
            for i, h in enumerate(headers):
                cols[i].markdown(f"**{h}**")

            for i, row in enumerate(page_df.iterrows()):

                cols = st.columns(len(headers))

                actual_row = row[1]

                # ================= FIXED ID (SYNC WITH PATIENTS PAGE) =================
                pid = start + i + 1

                if cols[0].button(str(pid), key=f"id_{pid}"):

                    st.session_state.selected_patient = actual_row.to_dict()
                    st.rerun()

                cols[1].write(actual_row.get("Name","-"))

                res = str(actual_row.get("Result","Negative")).strip()

                if res == "Positive":
                    cols[2].markdown("<div style='background:#FEE2E2;color:#EF4444;padding:4px 10px;border-radius:12px;font-weight:600;text-align:center'>Positive</div>", unsafe_allow_html=True)

                elif res == "At Risk":
                    cols[2].markdown("<div style='background:#FEF3C7;color:#D97706;padding:4px 10px;border-radius:12px;font-weight:600;text-align:center'>At Risk</div>", unsafe_allow_html=True)

                else:
                    cols[2].markdown("<div style='background:#DCFCE7;color:#16A34A;padding:4px 10px;border-radius:12px;font-weight:600;text-align:center'>Negative</div>", unsafe_allow_html=True)

                cols[3].write(actual_row.get("Type","-"))
                cols[4].write(actual_row.get("Stage","-"))
                cols[5].write(actual_row.get("Date","-"))

                if cols[6].button("⬇", key=f"action_{pid}"):

                    st.download_button(
                        "Download Report",
                        data=f"""
Name: {actual_row.get('Name')}
Result: {actual_row.get('Result')}
Stage: {actual_row.get('Stage')}
Date: {actual_row.get('Date')}
Recommendations: {actual_row.get('Recommendations')}
""",
                        file_name=f"{actual_row.get('Name','patient')}.txt"
                    )

            # ================= PAGINATION =================
            c1, c2, c3 = st.columns([1,2,1])

            with c1:
                if st.button("⬅ Prev"):
                    st.session_state.report_page = max(1, page - 1)
                    st.rerun()

            with c2:
                st.markdown(f"<center><b>Page {page} of {total_pages}</b></center>", unsafe_allow_html=True)

            with c3:
                if st.button("Next ➡"):
                    st.session_state.report_page = min(total_pages, page + 1)
                    st.rerun()

    else:
        st.info("No reports available")
        

# =============================================
# ================= ANALYTICS =================
# =============================================

# ================= ANALYTICS =================
elif menu == "Analytics" and role == "admin":

    st.markdown(
        '<div class="main-title">Analytics</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="sub-title">Insights and analytics overview</div>',
        unsafe_allow_html=True
    )

    if st.session_state.patients:

        import pandas as pd
        import plotly.graph_objects as go

        df = pd.DataFrame(st.session_state.patients)

        # ================= COUNTS =================
        total_patients = len(df)
        positive = len(df[df["Stage"] == "Diabetes Mellitus"])
        negative = len(df[df["Stage"] == "Normal"])
        risk = len(df[df["Stage"] == "Prediabetes"])

        # ================= TOP CARDS =================
        c1,c2,c3,c4 = st.columns(4)

        with c1:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-title">Total Patients</div>
                <div class="metric-value" style="color:#2563EB;">
                {total_patients}
                </div>
            </div>
            """, unsafe_allow_html=True)

        with c2:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-title">Positive Cases</div>
                <div class="metric-value" style="color:#EF4444;">
                {positive}
                </div>
            </div>
            """, unsafe_allow_html=True)

        with c3:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-title">At Risk</div>
                <div class="metric-value" style="color:#F59E0B;">
                {risk}
                </div>
            </div>
            """, unsafe_allow_html=True)

        with c4:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-title">Negative Cases</div>
                <div class="metric-value" style="color:#0D9488;">
                {negative}
                </div>
            </div>
            """, unsafe_allow_html=True)

        st.write("")

        # ================= FIXED TREND (ONLY CHANGE) =================
        if "Date" in df.columns:
            df["Date"] = pd.to_datetime(df["Date"], errors="coerce")

            # month nikaal rahe hain (Day nahi)
            df["Month"] = df["Date"].dt.strftime("%b")
        else:
            df["Month"] = "Unknown"

        trend_df = df.groupby("Month")["Stage"].value_counts().unstack().fillna(0)

        # correct month order
        month_order = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]

        trend_df = trend_df.reindex(month_order).dropna(how="all")

        for col in ["Diabetes Mellitus", "Normal", "Prediabetes"]:
            if col not in trend_df.columns:
                trend_df[col] = 0

        trend_df = trend_df.fillna(0).reset_index()
        

        # ================= CHARTS =================
        left,right = st.columns(2)

        # ================= LINE CHART =================
        with left:

            st.markdown("### Prediction Trend")

            fig = go.Figure()

            fig.add_trace(go.Scatter(
                x=trend_df["Month"],
                y=trend_df["Diabetes Mellitus"],
                mode='lines+markers',
                name='Positive'
            ))

            fig.add_trace(go.Scatter(
                x=trend_df["Month"],
                y=trend_df["Normal"],
                mode='lines+markers',
                name='Negative'
            ))

            fig.add_trace(go.Scatter(
                x=trend_df["Month"],
                y=trend_df["Prediabetes"],
                mode='lines+markers',
                name='At Risk'
            ))

            fig.update_layout(
                height=400,
                paper_bgcolor="white",
                plot_bgcolor="white",
                margin=dict(l=20,r=20,t=30,b=20)
            )

            st.plotly_chart(fig, use_container_width=True)

        # ================= DONUT CHART =================
        with right:

            st.markdown("### Gender Distribution")

            male = len(df[df["Gender"] == "Male"])
            female = len(df[df["Gender"] == "Female"])

            fig2 = go.Figure(data=[go.Pie(
                labels=["Male","Female"],
                values=[male,female],
                hole=.65
            )])

            fig2.update_layout(
                height=400,
                paper_bgcolor="white"
            )

            st.plotly_chart(fig2, use_container_width=True)

    else:
        st.info("No analytics data available")

# ================================================
# ================= APPOINTMENTS =================
# ================================================

elif menu == "Appointments" and role == "admin":

    import math

    # ================= SESSION =================
    if "show_add_appointment" not in st.session_state:
        st.session_state.show_add_appointment = False

    if "selected_appointment" not in st.session_state:
        st.session_state.selected_appointment = 0

    if "appointment_page" not in st.session_state:
        st.session_state.appointment_page = 1

    # ================= LOAD FROM DATABASE =================
    appointments = get_appointments()

    # ================= HEADER =================
    col1, col2 = st.columns([5, 2])

    with col1:
        st.markdown(
        '<div class="main-title">Appointments</div>',
        unsafe_allow_html=True
    )
        st.caption("Schedule and manage patient appointments")

    with col2:
        if st.button("➕ New Appointment"):
            st.session_state.show_add_appointment = not st.session_state.show_add_appointment

    st.write("")

    # ================= ADD FORM =================
    if st.session_state.show_add_appointment:

        st.subheader("➕ Add Appointment")

        c1, c2 = st.columns(2)

        with c1:
            patient_name = st.text_input("Patient Name")
            doctor = st.selectbox("Doctor", ["Dr. Sarah Khan", "Dr. Ali Raza", "Dr. Ahmed"])
            appoint_type = st.selectbox("Type", ["Consultation", "Follow-up", "Checkup"])

        with c2:
            appoint_date = st.date_input("Date")
            appoint_time = st.time_input("Time")
            phone = st.text_input("Phone")

        if st.button("Save Appointment"):

            if patient_name.strip() == "":
                st.error("Patient name required")

            else:
                add_appointment(
                    patient_name,
                    doctor,
                    appoint_type,
                    appoint_date.strftime("%d %b %Y"),
                    appoint_time.strftime("%I:%M %p"),
                    "Upcoming",
                    phone,
                    "Room 203"
                )

                st.success("Appointment Added ✔")
                st.session_state.show_add_appointment = False
                st.rerun()

    # ================= TOP CARDS =================
    total = len(appointments)
    upcoming = len([a for a in appointments if a[6] == "Upcoming"])
    completed = len([a for a in appointments if a[6] == "Completed"])
    cancelled = len([a for a in appointments if a[6] == "Cancelled"])

    def card(icon, title, value, color):

        components.html(f"""
        <div style="
            background:white;
            padding:22px;
            border-radius:22px;
            box-shadow:0 4px 14px rgba(0,0,0,0.06);
            border-left:5px solid {color};
            font-family:Arial;
            height:120px;
            box-sizing:border-box;
        ">
            <div style="font-size:26px;">{icon}</div>
            <div style="color:#64748B;font-size:13px;font-weight:600;">{title}</div>
            <div style="font-size:32px;font-weight:800;color:#0F172A;">{value}</div>
        </div>
        """, height=160)

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        card(" ", "Today's Appointments", total, "#2563EB")

    with c2:
        card(" ", "Upcoming", upcoming, "#16A34A")

    with c3:
        card(" ", "Completed", completed, "#7C3AED")

    with c4:
        card(" ", "Cancelled", cancelled, "#DC2626")

    st.write("")

    # ================= MAIN LAYOUT =================
    left, right = st.columns([2, 1])

    # ================= LEFT SIDE =================
    with left:

        st.subheader("Appointments List")

        search = st.text_input("🔍 Search patient")

        filtered = appointments

        if search:
            filtered = [a for a in appointments if search.lower() in a[1].lower()]

        # ================= PAGINATION =================
        ROWS_PER_PAGE = 5

        total_pages = max(1, math.ceil(len(filtered) / ROWS_PER_PAGE))

        page = st.session_state.appointment_page

        start = (page - 1) * ROWS_PER_PAGE
        end = start + ROWS_PER_PAGE

        page_data = filtered[start:end]

        # ================= LIST =================
        for i, a in enumerate(page_data):

            if st.button(f"👤 {a[1]}", key=f"select_{i}"):

                st.session_state.selected_appointment = i

            components.html(f"""
            <div style="
                background:#F8FAFC;
                padding:16px;
                border-radius:16px;
                border-left:5px solid #2563EB;
                margin-bottom:10px;
                font-family:Arial;
            ">
                <div style="font-size:18px;font-weight:700;color:#0F172A;">
                    👤 {a[1]}
                </div>

                <div style="color:#64748B;font-size:13px;margin-top:4px;">
                    👨‍⚕️ {a[2]} • 📋 {a[3]} • ⏰ {a[5]}
                </div>

                <div style="
                    margin-top:8px;
                    display:inline-block;
                    padding:4px 10px;
                    border-radius:20px;
                    font-size:12px;
                    font-weight:700;
                    background:
                    {'#DBEAFE' if a[6]=='Upcoming' else '#DCFCE7' if a[6]=='Completed' else '#FEE2E2'};
                    color:
                    {'#2563EB' if a[6]=='Upcoming' else '#16A34A' if a[6]=='Completed' else '#DC2626'};
                ">
                    {a[6]}
                </div>
            </div>
            """, height=120)

            c1, c2, c3 = st.columns(3)

            with c1:
                if st.button("✔ Done", key=f"c{i}"):
                    update_appointment_status(a[0], "Completed")
                    st.rerun()

            with c2:
                if st.button("✖ Cancel", key=f"x{i}"):
                    update_appointment_status(a[0], "Cancelled")
                    st.rerun()

            with c3:
                if st.button("🗑", key=f"d{i}"):
                    delete_appointment(a[0])
                    st.rerun()

        # ================= PAGINATION UI =================
        c1, c2, c3 = st.columns([1, 2, 1])

        with c1:
            if st.button("⬅ Prev"):
                st.session_state.appointment_page = max(1, page - 1)
                st.rerun()

        with c2:
            st.markdown(f"<center><b>Page {page} of {total_pages}</b></center>", unsafe_allow_html=True)

        with c3:
            if st.button("Next ➡"):
                st.session_state.appointment_page = min(total_pages, page + 1)
                st.rerun()

    # ================= RIGHT SIDE =================
    with right:

        if appointments:

            selected_index = min(st.session_state.selected_appointment, len(appointments)-1)
            a = appointments[selected_index]

            components.html(f"""
            <div style="
                background:white;
                padding:20px;
                border-radius:18px;
                box-shadow:0 4px 14px rgba(0,0,0,0.08);
                border-left:5px solid #2563EB;
                font-family:Arial;
                min-height:360px;
                box-sizing:border-box;
            ">

                <div style="
                    font-size:20px;
                    font-weight:700;
                    color:#0F172A;
                    margin-bottom:14px;
                ">
                    Appointment Details
                </div>

                <div style="color:#334155;font-size:14px;line-height:2;">
                    👤 <b>{a[1]}</b><br>
                    👨‍⚕️ {a[2]}<br>
                    📋 {a[3]}<br>
                    📅 {a[4]}<br>
                    ⏰ {a[5]}<br>
                    📞 {a[7]}<br>
                    📍 {a[8]}<br>
                    📌 {a[6]}
                </div>

            </div>
            """, height=380)

# =========================================  
# ================= Users =================          
# ========================================= 
from auth_db import create_user, conn, change_password


# ================= SECURITY =================
if role == "admin" and menu == "Users":

    st.markdown("""
    <style>

    .user-title{
        font-size:32px;
        font-weight:700;
        color:#0F172A;
    }

    .user-sub{
        color:#64748B;
        margin-bottom:20px;
    }

    </style>
    """, unsafe_allow_html=True)

    st.markdown(
        '<div class="user-title">Users Management</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="user-sub">Manage system login users</div>',
        unsafe_allow_html=True
    )

    # =========================================
    # ============== LOAD PATIENTS ============
    # =========================================

    patients = get_patients()

    patient_names = [
        p["Name"] for p in patients
    ] if patients else []

    # =========================================
    # ================= TABS ==================
    # =========================================

    tab1, tab2, tab3 = st.tabs([
        "➕ Create User",
        "📋 All Users",
        "🔐 Change Password"
    ])

    # =====================================================
    # ➕ CREATE USER
    # =====================================================

    with tab1:

        st.subheader("➕ Create New User")

        use_patient = st.checkbox(
            "Link user with patient record"
        )

        username = ""

        # =========================================
        # ===== SELECT FROM PATIENT DATABASE ======
        # =========================================

        if use_patient:

            if patient_names:

                username = st.selectbox(
                    "Select Patient",
                    patient_names
                )

            else:
                st.warning(
                    "No patients available"
                )

        # =========================================
        # ===== MANUAL USERNAME ===================
        # =========================================

        else:

            username = st.text_input(
                "Username"
            )

        # =========================================
        # ===== PASSWORD + ROLE ===================
        # =========================================

        password = st.text_input(
            "Password",
            type="password"
        )

        new_role = st.selectbox(
            "Role",
            [
                "admin",
                "doctor",
                "patient"
            ]
        )

        # =========================================
        # ===== CREATE BUTTON =====================
        # =========================================

        if st.button("Create User"):

            if (
                username.strip() == ""
                or
                password.strip() == ""
            ):

                st.warning(
                    "⚠ Please fill all fields"
                )

            else:

                success = create_user(
                    username,
                    password,
                    new_role
                )

                if success:

                    st.success(
                        f"✔ User '{username}' created successfully"
                    )

                else:

                    st.error(
                        "⚠ Username already exists"
                    )

    # =====================================================
    # 📋 VIEW USERS
    # =====================================================

    with tab2:

        st.subheader("📋 All Users")

        db = conn()

        df = pd.read_sql_query(
            """
            SELECT
                id,
                username,
                role
            FROM users
            """,
            db
        )

        db.close()

        if df.empty:

            st.info(
                "No users found"
            )

        else:

            st.dataframe(
                df,
                use_container_width=True,
                hide_index=True
            )

    # =====================================================
    # 🔐 CHANGE PASSWORD
    # =====================================================

    with tab3:

        st.subheader("🔐 Change User Password")

        db = conn()

        users_df = pd.read_sql_query(
            """
            SELECT username
            FROM users
            """,
            db
        )

        db.close()

        usernames = users_df[
            "username"
        ].tolist()

        if usernames:

            selected_user = st.selectbox(
                "Select User",
                usernames
            )

            new_password = st.text_input(
                "New Password",
                type="password"
            )

            if st.button("Update Password"):

                if new_password.strip() == "":

                    st.warning(
                        "⚠ Enter new password"
                    )

                else:

                    change_password(
                        selected_user,
                        new_password
                    )

                    st.success(
                        f"✔ Password updated for '{selected_user}'"
                    )

        else:

            st.info(
                "No users available"
            )



# ================= PATIENT DASHBOARD =================

# ================= PATIENT DASHBOARD =================

if role == "patient" and menu == "Dashboard":

    import pandas as pd

    st.markdown("""
    <style>

    .title{
        font-size:34px;   /* same feel as My Report */
        font-weight:700;
        margin-bottom:15px;
        color:#111827;
    }

    .card{
        background:white;
        border-radius:16px;
        padding:18px;
        box-shadow:0 4px 14px rgba(0,0,0,0.08);
        border-left:5px solid #2563EB;
    }

    .card h4{
        margin:0;
        font-size:13px;
        color:gray;
    }

    .card h2{
        margin:5px 0 0 0;
        font-size:22px;
        color:#111827;
    }

    .insight-box{
        background:linear-gradient(135deg,#EEF2FF,#FFFFFF);
        padding:18px;
        border-radius:16px;
        margin-top:20px;
        border:1px solid #E5E7EB;
    }

    .footer{
        margin-top:25px;
        text-align:center;
        font-size:12px;
        color:gray;
        padding:10px;
    }

    </style>
    """, unsafe_allow_html=True)

    # ✅ ONLY TITLE CHANGED + SIZE MATCHED
    st.markdown("<div class='title'>My Dashboard</div>", unsafe_allow_html=True)

    username = st.session_state.username
    data = [p for p in st.session_state.patients if p.get("Name") == username]

    if not data:
        st.info("No records found")
        st.stop()

    latest = data[-1]

    # ================= CARDS =================
    c1, c2, c3 = st.columns(3)

    with c1:
        st.markdown(f"""
        <div class='card'>
            <h4>Fasting Blood Sugar</h4>
            <h2>{latest.get("FBS","N/A")}</h2>
        </div>
        """, unsafe_allow_html=True)

    with c2:
        st.markdown(f"""
        <div class='card'>
            <h4>Body Mass Index</h4>
            <h2>{latest.get("BMI","N/A")}</h2>
        </div>
        """, unsafe_allow_html=True)

    with c3:
        st.markdown(f"""
        <div class='card'>
            <h4>HbA1c Level</h4>
            <h2>{latest.get("HbA1c","N/A")}</h2>
        </div>
        """, unsafe_allow_html=True)

    # ================= CHART =================
    st.subheader("Health Progress Overview")

    chart_data = data[-6:]

    st.bar_chart(pd.DataFrame({
        "FBS": [float(p.get("FBS",0) or 0) for p in chart_data],
        "BMI": [float(p.get("BMI",0) or 0) for p in chart_data],
        "HbA1c": [float(p.get("HbA1c",0) or 0) for p in chart_data],
    }))

    # ================= INSIGHT BOX =================
    st.markdown("""
    <div class='insight-box'>
        <h3>Health Insights</h3>
        <ul>
            <li>FBS trend indicates glucose control status</li>
            <li>BMI reflects weight management</li>
            <li>HbA1c shows long-term diabetes control</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

    # ================= STATUS =================
    st.subheader("Current Status")

    col1, col2 = st.columns(2)

    with col1:
        st.success(f"Stage: {latest.get('Stage','N/A')}")

    with col2:
        st.info(f"Type: {latest.get('Type','N/A')}")

    # ================= FOOTER =================
    st.markdown("""
    <div class='footer'>
        DiabetesCare AI • Patient Monitoring System • Secure Health Analytics
    </div>
    """, unsafe_allow_html=True)


# ================= AI ASSISTANT =================
# ================= AI ASSISTANT =================
# ================= AI ASSISTANT =================

elif role == "patient" and menu == "AI Assistant":

    import streamlit as st

    # ================= UI STYLE =================
    st.markdown("""
    <style>

    .assistant-title{
        font-size:34px;
        font-weight:700;
        color:#0F172A;
        margin-bottom:18px;
    }

    .user-msg{
        background:#DBEAFE;
        padding:12px 14px;
        border-radius:12px;
        margin:8px 0;
        color:#1E3A8A;
        font-weight:500;
        white-space:pre-wrap;
    }

    .ai-msg{
        background:#F8FAFC;
        padding:12px 14px;
        border-radius:12px;
        margin:8px 0;
        border:1px solid #E2E8F0;
        color:#334155;
        font-weight:500;
        white-space:pre-wrap;
    }

    </style>
    """, unsafe_allow_html=True)

    st.markdown(
        "<div class='assistant-title'>AI Diabetes Health Assistant</div>",
        unsafe_allow_html=True
    )

    # ================= GET PATIENT =================
    username = st.session_state.get("username")

    patient_list = [
        p for p in st.session_state.get("patients", [])
        if p.get("Name") == username
    ]

    if not patient_list:
        st.warning("No patient data found.")
        st.stop()

    patient = patient_list[-1]

    # ================= CHAT SESSION =================
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    # ================= SAFE FUNCTION =================
    def safe(v):
        if v is None or v == "" or v == "NULL":
            return 0
        return v

    # ================= QUICK ACTION FUNCTION =================
    def run_query(question):
        try:
            return ask_gemini(patient, question)
        except:
            return "AI temporarily unavailable. Please try again."

    # ================= QUICK BUTTONS =================
    st.subheader("Quick Actions")

    col1, col2, col3, col4 = st.columns(4)

    if col1.button("Report"):
        q = "Explain my full diabetes report"
        reply = run_query(q)

        st.session_state.chat_history.append(("user", q))
        st.session_state.chat_history.append(("ai", reply))
        st.rerun()

    if col2.button("Risk"):
        q = "Analyze my diabetes risk"
        reply = run_query(q)

        st.session_state.chat_history.append(("user", q))
        st.session_state.chat_history.append(("ai", reply))
        st.rerun()

    if col3.button("Diet"):
        q = "Give me a personalized diabetes diet plan"
        reply = run_query(q)

        st.session_state.chat_history.append(("user", q))
        st.session_state.chat_history.append(("ai", reply))
        st.rerun()

    if col4.button("Exercise"):
        q = "Give me a personalized exercise plan"
        reply = run_query(q)

        st.session_state.chat_history.append(("user", q))
        st.session_state.chat_history.append(("ai", reply))
        st.rerun()

    st.divider()

    # ================= CHAT DISPLAY =================
    st.markdown("### 💬 Chat History")

    for role_msg, msg in st.session_state.chat_history[-20:]:

        if role_msg == "user":
            st.markdown(f"<div class='user-msg'>🧑 {msg}</div>", unsafe_allow_html=True)

        else:
            st.markdown(f"<div class='ai-msg'>🤖 {msg}</div>", unsafe_allow_html=True)

    # ================= INPUT =================
    user_input = st.chat_input("Ask anything about your diabetes report...")

    if user_input:

        st.session_state.chat_history.append(("user", user_input))

        with st.spinner("Analyzing your medical report..."):

            reply = run_query(user_input)

        st.session_state.chat_history.append(("ai", reply))
        st.rerun()

    # ================= CONTEXT =================
    with st.expander("📊 Patient Data (AI Context)"):
        st.json(patient)

    # ================= CLEAR CHAT =================
    if st.button("🗑 Clear Chat"):
        st.session_state.chat_history = []
        st.rerun()

    # ================= FOOTER =================
    st.markdown("""
    <hr>
    <center style='color:gray;font-size:12px'>
    AI Assistant is for educational guidance only. Always consult doctor for medical decisions.
    </center>
    """, unsafe_allow_html=True)


# ================= MY REPORT =================

if role == "patient" and menu == "My Report":

    import pandas as pd

    st.markdown("""
    <style>

    .report-title{
        font-size:34px;
        font-weight:700;
        color:#111827;
    }

    .report-sub{
        color:#6B7280;
        margin-bottom:25px;
    }

    

    .profile-img{
        width:120px;
        height:120px;
        border-radius:50%;
        
        display:flex;
        align-items:center;
        justify-content:center;
        font-size:58px;
        color:white;
        margin:auto;
        box-shadow:0 6px 18px rgba(30,58,138,0.35);
    }

    .patient-name{
        text-align:center;
        font-size:28px;
        font-weight:700;
        margin-top:14px;
        color:#111827;
    }

    .patient-id{
        text-align:center;
        color:#6B7280;
        margin-bottom:25px;
    }

    .detail-row{
        padding:10px 0;
        border-bottom:1px solid #F1F5F9;
        font-size:15px;
    }

    .detail-label{
        font-weight:700;
        color:#374151;
    }

    .card-box{
        background:white;
        padding:22px;
        border-radius:20px;
        box-shadow:0 4px 14px rgba(0,0,0,0.06);
        margin-bottom:20px;
    }

    .rec-box{
        background:white;
        padding:22px;
        border-radius:20px;
        box-shadow:0 4px 14px rgba(0,0,0,0.06);
    }

    .rec-item{
        background:#F8FAFC;
        padding:12px 14px;
        border-radius:12px;
        margin-bottom:10px;
        border-left:4px solid #2563EB;
        font-size:14px;
        color:#374151;
    }

    .status-positive{
        background:#FEE2E2;
        color:#DC2626;
        padding:6px 12px;
        border-radius:10px;
        font-weight:600;
        display:inline-block;
    }

    .status-negative{
        background:#DCFCE7;
        color:#16A34A;
        padding:6px 12px;
        border-radius:10px;
        font-weight:600;
        display:inline-block;
    }

    .status-risk{
        background:#FEF3C7;
        color:#D97706;
        padding:6px 12px;
        border-radius:10px;
        font-weight:600;
        display:inline-block;
    }

    </style>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="report-title">My Report</div>
    <div class="report-sub">
    View your complete medical report
    </div>
    """, unsafe_allow_html=True)

    username = st.session_state.username

    data = [
        p for p in st.session_state.patients
        if p.get("Name") == username
    ]

    if not data:

        st.info("No report available")

    else:

        p = data[-1]

        result = p.get("Stage", "Normal")

        status_class = "status-negative"

        if result == "Diabetes Mellitus":
            status_class = "status-positive"

        elif result == "Prediabetes":
            status_class = "status-risk"

        left, right = st.columns([1,2])

        # ================= LEFT SIDE =================

        with left:

            st.markdown("""
            <div class="patient-box">

            <div class="profile-img">
                👤
            </div>

            """, unsafe_allow_html=True)

            st.markdown(
                f"<div class='patient-name'>{p.get('Name','N/A')}</div>",
                unsafe_allow_html=True
            )

            st.markdown(
                f"<div class='patient-id'>Patient Medical Report</div>",
                unsafe_allow_html=True
            )

            st.markdown(f"""
            <div class="detail-row">
            <span class="detail-label">Age:</span>
            {p.get('Age','N/A')}
            </div>
            """, unsafe_allow_html=True)

            st.markdown(f"""
            <div class="detail-row">
            <span class="detail-label">Gender:</span>
            {p.get('Gender','N/A')}
            </div>
            """, unsafe_allow_html=True)

            st.markdown(f"""
            <div class="detail-row">
            <span class="detail-label">BMI:</span>
            {p.get('BMI','N/A')}
            </div>
            """, unsafe_allow_html=True)

            st.markdown(f"""
            <div class="detail-row">
            <span class="detail-label">Type:</span>
            {p.get('Type','N/A')}
            </div>
            """, unsafe_allow_html=True)

            st.markdown(f"""
            <div class="detail-row">
            <span class="detail-label">Date:</span>
            {p.get('Date','N/A')}
            </div>
            """, unsafe_allow_html=True)

            st.markdown(f"""
            <div class="detail-row">
            <span class="detail-label">Result:</span>
            <span class="{status_class}">
            {p.get('Stage','N/A')}
            </span>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("</div>", unsafe_allow_html=True)
            from reportlab.lib.pagesizes import A4
            from reportlab.pdfgen import canvas
            import io

        def generate_pdf(data):
            buffer = io.BytesIO()
            pdf = canvas.Canvas(buffer, pagesize=A4)

            pdf.setFont("Helvetica-Bold", 14)
            pdf.drawString(50, 800, "Patient Medical Report")

            pdf.setFont("Helvetica", 11)

            y = 760
            for key, value in data.items():
                pdf.drawString(50, y, f"{key}: {value}")
                y -= 25

            pdf.save()
            buffer.seek(0)
            return buffer


        # ================= DOWNLOAD BUTTON =================
        report_data = {
            "Name": p.get("Name"),
            "Age": p.get("Age"),
            "Gender": p.get("Gender"),
            "BMI": p.get("BMI"),
            "FBS": p.get("FBS"),
            "HbA1c": p.get("HbA1c"),
            "Stage": p.get("Stage"),
            "Type": p.get("Type"),
            "Complications": p.get("Complications"),
            "Recommendations": p.get("Recommendations"),
            "Date": p.get("Date")
        }

        pdf_file = generate_pdf(report_data)

        st.download_button(
            label="⬇ Download PDF Report",
            data=pdf_file,
            file_name=f"{p.get('Name','report')}_medical_report.pdf",
            mime="application/pdf"
        )

        # ================= RIGHT SIDE =================

        with right:

            # ================= LAB RESULTS =================

            

            st.subheader("Lab Results")

            lab_df = pd.DataFrame([{
                "FBS": p.get("FBS","-"),
                "HbA1c": p.get("HbA1c","-"),
                "BMI": p.get("BMI","-"),
                "LDL": p.get("LDL","-"),
                "HDL": p.get("HDL","-"),
                "BP":
                f"{p.get('SystolicBP','-')}/{p.get('DiastolicBP','-')}"
            }])

            st.dataframe(
                lab_df,
                use_container_width=True,
                hide_index=True
            )

            st.markdown("</div>", unsafe_allow_html=True)

            # ================= COMPLICATIONS =================

            

            st.subheader("Complications")

            complications = p.get("Complications","None")

            st.markdown(f"""
            <div class="rec-item">
            {complications}
            </div>
            """, unsafe_allow_html=True)

            st.markdown("</div>", unsafe_allow_html=True)

            # ================= RECOMMENDATIONS =================

            

            st.subheader("Recommendations")

            recs = str(
                p.get("Recommendations","")
            ).split(",")

            if recs:

                for r in recs:

                    if r.strip():

                        st.markdown(
                            f"""
                            <div class="rec-item">
                            ✔ {r.strip()}
                            </div>
                            """,
                            unsafe_allow_html=True
                        )

            else:

                st.info("No recommendations available")

            st.markdown("</div>", unsafe_allow_html=True)   
                