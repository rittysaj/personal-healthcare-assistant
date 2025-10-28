import os
import pickle
import pandas as pd
import streamlit as st
from streamlit_option_menu import option_menu

# ===================== Page Setup =====================
st.set_page_config(
    page_title="Personal Health Care Assistant",
    layout="wide",
    page_icon="🧑‍⚕️",
)

# ---------- Config: tagline (banner only) ----------
TAGLINE = "Personalized screening. Informed health. Better outcomes."

# ===================== Styles + Banner =====================
st.markdown(f"""
<style>
  .stApp {{ background:#f5f8fa; font-family: "Inter","Helvetica Neue",Arial,sans-serif; }}

  .topbar {{ position:sticky; top:0; z-index:999; background:#fff; border-bottom:1px solid #e5e7eb; }}
  .topbar-inner {{
      max-width:1200px; margin:0 auto; padding:10px 16px;
      display:grid; grid-template-columns:auto 1fr auto; gap:12px; align-items:center;
  }}
  .brand .title {{ font-weight:800; font-size:18px; color:#0f172a; line-height:1.1; }}
  .brand .sub {{ font-size:12px; color:#64748b; margin-top:2px; }}
  .top-cta a {{
      display:inline-block; background:#2563eb; color:#fff; text-decoration:none;
      border-radius:8px; padding:8px 12px; font-weight:700; border:1px solid #1e40af;
  }}
  .top-cta a:hover {{ background:#1e40af; }}

  .stTextInput > div > div > input {{
      background:#fff; border:1px solid #cbd5e1; border-radius:8px; padding:6px 10px;
  }}
  .stTextInput > div > div > input:focus {{
      border:1px solid #2563eb; box-shadow:0 0 0 1px #2563eb;
  }}

  .stButton > button {{
      background:#2563eb; color:#fff; font-weight:600; border-radius:8px; border:none; padding:.6rem 1.2rem;
  }}
  .stButton > button:hover {{ background:#1e40af; }}

  .card {{ background:#fff; border-radius:12px; padding:18px; box-shadow:0 2px 6px rgba(0,0,0,.08); margin-top:10px; }}
  .result-pill {{ display:inline-block; padding:6px 14px; border-radius:999px; font-weight:700; margin-top:8px; }}
  .result-yes {{ background:#dcfce7; color:#166534; }}
  .result-no  {{ background:#fee2e2; color:#991b1b; }}

  h1, h2, h3 {{ color:#1e3a8a; font-weight:700; }}
</style>

<div class="topbar">
  <div class="topbar-inner">
    <div class="brand">
      <div>
        <div class="title">🧑‍⚕️ Your Personal Health Care Assistant</div>
        <div class="sub">{TAGLINE}</div>
      </div>
    </div>
    <div></div>
    <div class="top-cta"><a href="#predict">Start Screening</a></div>
  </div>
</div>
""", unsafe_allow_html=True)

# ===================== Minimal parser =====================
def to_float(s: str) -> float:
    try:
        return float(s.strip())
    except Exception:
        return 0.0

# ===================== Care Plans =====================
PLANS = {
    "Diabetes": {
        True: {
            "title": "Immediate Care & Next Steps",
            "points": [
                "Confirm with a clinician and set A1C / fasting-glucose targets.",
                "Diet: more vegetables, lean proteins, whole grains; limit refined sugars.",
                "Activity: ~150 minutes/week moderate exercise + 2× strength training.",
                "Monitoring: discuss home glucometer routine and thresholds.",
                "Medications: review options (e.g., metformin) and adhere to dosing.",
                "Risk checks: annual eye & kidney screening; foot care; control BP & lipids.",
                "Urgent care if very high glucose, confusion, vomiting, or dehydration."
            ]
        },
        False: {
            "title": "Prevention & Healthy Habits",
            "points": [
                "Maintain a healthy weight and waist circumference.",
                "Fiber-rich meals; fewer sugary drinks; portion control.",
                "Exercise most days (e.g., brisk walk 30 min/day).",
                "Annual screening if risk factors exist (family history, BMI, BP).",
                "Sleep 7–8 hours; manage stress consistently."
            ]
        }
    },
    "Heart Disease": {
        True: {
            "title": "What to Do Now",
            "points": [
                "Arrange cardiology follow-up for ECG/echo and labs.",
                "DASH-style diet; lower sodium and trans-fats; avoid tobacco.",
                "Exercise after clinician clearance; start gradually; track symptoms.",
                "Take prescribed meds (antiplatelets, statins, BP meds) reliably.",
                "Keep a home BP log; common target <130/80 mmHg if advised.",
                "Emergency signs (chest pain, breathlessness, fainting) → urgent care."
            ]
        },
        False: {
            "title": "Keep Your Heart Healthy",
            "points": [
                "Plant-forward diet; limit processed meats and sugary snacks.",
                "150 min/week moderate activity + 2× resistance sessions.",
                "Know your numbers: BP, lipids, fasting glucose — check annually.",
                "Avoid smoking; limit alcohol; build a stress-reduction routine."
            ]
        }
    },
    "Parkinson's": {
        True: {
            "title": "Early Management & Support",
            "points": [
                "Neurology referral for confirmation and a tailored treatment plan.",
                "Physical therapy for balance, gait, and flexibility.",
                "Speech therapy for voice/swallowing; occupational therapy for daily tasks.",
                "Discuss medication timing (e.g., levodopa) to optimize symptom control.",
                "Home safety: reduce fall risks; ensure lighting; install support bars.",
                "Caregiver education and local support groups can be very helpful."
            ]
        },
        False: {
            "title": "Brain & Movement Health Tips",
            "points": [
                "Regular aerobic + balance + strength training.",
                "Cognitive engagement: learn new skills, puzzles, social activity.",
                "Good sleep hygiene; manage stress.",
                "Report new tremor, slowness, balance, or speech changes to a clinician."
            ]
        }
    }
}

def show_result_card(disease: str, positive: bool) -> None:
    pill_class = "result-yes" if positive else "result-no"
    label = "YES — Condition detected" if positive else "NO — Condition not detected"
    st.markdown(f"<div class='card'><div class='result-pill {pill_class}'>{label}</div>", unsafe_allow_html=True)
    data = PLANS[disease][positive]
    st.subheader(data["title"])
    for p in data["points"]:
        st.markdown(f"- {p}")
    st.caption("This app is educational and not a medical diagnosis. Please consult a licensed clinician.")
    st.markdown("</div>", unsafe_allow_html=True)

# ===================== Model Loading =====================
try:
    diabetes_model = pickle.load(open(
        "C:/Users/Laptops Garage/OneDrive/Desktop/Personal Health Assistant/Saved Models/diabetes_model.sav", "rb"
    ))
except Exception as e:
    st.error(f"Failed to load diabetes model: {e}")
    diabetes_model = None

try:
    heart_disease_model = pickle.load(open(
        "C:/Users/Laptops Garage/OneDrive/Desktop/Personal Health Assistant/Saved Models/heart_disease_model.sav", "rb"
    ))
except Exception as e:
    st.error(f"Failed to load heart disease model: {e}")
    heart_disease_model = None

try:
    parkinsons_model = pickle.load(open(
        "C:/Users/Laptops Garage/OneDrive/Desktop/Personal Health Assistant/Saved Models/parkinsons_model.sav", "rb"
    ))
except Exception as e:
    st.error(f"Failed to load Parkinson's model: {e}")
    parkinsons_model = None

def predict_diabetes_from_raw(raw_vals, model_obj) -> int:
    try:
        if isinstance(model_obj, dict) and all(k in model_obj for k in ("classifier", "scaler", "feature_order")):
            FEATURE_ORDER = model_obj["feature_order"]
            SCALER = model_obj["scaler"]
            CLF = model_obj["classifier"]
            COLS_WITH_ZERO = model_obj.get("cols_with_zero", [])
            MEDIANS = model_obj.get("medians", {})

            row = pd.DataFrame([raw_vals], columns=FEATURE_ORDER).copy()
            for c in COLS_WITH_ZERO:
                try:
                    if float(row.loc[0, c]) == 0.0 and c in MEDIANS:
                        row.loc[0, c] = MEDIANS[c]
                except Exception:
                    pass
            x_scaled = SCALER.transform(row.values)
            return int(CLF.predict(x_scaled)[0])
        else:
            return int(model_obj.predict([raw_vals])[0])
    except Exception as e:
        st.error(f"Diabetes prediction failed: {e}")
        return 0

# ===================== Sidebar (only title, bigger font) =====================
with st.sidebar:
    st.markdown(
        "<div style='font-size:24px; font-weight:800; color:#0f172a; margin-bottom:12px;'>"
        " Personal Health Care Assistant</div>",
        unsafe_allow_html=True
    )

    selected = option_menu(
        "Health Checks",
        ["Diabetes Prediction", "Heart Disease Prediction", "Parkinsons Prediction"],
        icons=["activity", "heart", "person"],
        menu_icon="hospital-fill",
        default_index=0,
        styles={
            "container": {"padding": "6px", "background-color": "#ffffff", "border-radius": "14px"},
            "icon": {"color": "#2563eb", "font-size": "18px"},
            "nav-link": {
                "font-size": "15px",
                "margin": "6px 0",
                "--hover-color": "#e8f0fe",
                "color": "#0f172a",
                "padding": "10px 12px",
                "border-radius": "10px",
            },
            "nav-link-selected": {"background-color": "#2563eb", "color": "white"},
        },
    )

st.markdown("<div id='predict'></div>", unsafe_allow_html=True)

# ===================== Pages (plain text inputs; blank by default) =====================
if selected == "Diabetes Prediction":
    st.header("Diabetes Prediction")
    Pregnancies = st.text_input('Number of Pregnancies', value="")
    Glucose = st.text_input('Glucose Level', value="")
    BloodPressure = st.text_input('Blood Pressure value', value="")
    SkinThickness = st.text_input('Skin Thickness value', value="")
    Insulin = st.text_input('Insulin Level', value="")
    BMI = st.text_input('BMI value', value="")
    DiabetesPedigreeFunction = st.text_input('Diabetes Pedigree Function value', value="")
    Age = st.text_input('Age of the Person', value="")

    if st.button("Diabetes Test Result", disabled=(diabetes_model is None)):
        vals = list(map(to_float, [
            Pregnancies, Glucose, BloodPressure, SkinThickness, Insulin, BMI, DiabetesPedigreeFunction, Age
        ]))
        label = predict_diabetes_from_raw(vals, diabetes_model)
        show_result_card("Diabetes", label == 1)

elif selected == "Heart Disease Prediction":
    st.header("Heart Disease Prediction")
    age = st.text_input('Age', value="")
    sex = st.text_input('Sex (1=male, 0=female)', value="")
    cp = st.text_input('Chest Pain type (0-3)', value="")
    trestbps = st.text_input('Resting Blood Pressure', value="")
    chol = st.text_input('Serum Cholesterol (mg/dl)', value="")
    fbs = st.text_input('Fasting Blood Sugar > 120 mg/dl (1/0)', value="")
    restecg = st.text_input('Resting ECG (0-2)', value="")
    thalach = st.text_input('Max Heart Rate achieved', value="")
    exang = st.text_input('Exercise Induced Angina (1/0)', value="")
    oldpeak = st.text_input('ST depression induced by exercise', value="")
    slope = st.text_input('Slope of the peak exercise ST (0-2)', value="")
    ca = st.text_input('Major vessels colored by fluoroscopy (0-3)', value="")
    thal = st.text_input('Thal (1=normal, 2=fixed, 3=reversible)', value="")

    if st.button("Heart Disease Test Result", disabled=(heart_disease_model is None)):
        try:
            vals = list(map(to_float, [
                age, sex, cp, trestbps, chol, fbs, restecg, thalach, exang, oldpeak, slope, ca, thal
            ]))
            label = int(heart_disease_model.predict([vals])[0])
            show_result_card("Heart Disease", label == 1)
        except Exception as e:
            st.error(f"Heart prediction failed: {e}")

elif selected == "Parkinsons Prediction":
    st.header("Parkinson's Disease Prediction")
    fo = st.text_input('MDVP:Fo(Hz)', value="")
    fhi = st.text_input('MDVP:Fhi(Hz)', value="")
    flo = st.text_input('MDVP:Flo(Hz)', value="")
    Jitter_percent = st.text_input('MDVP:Jitter(%)', value="")
    Jitter_Abs = st.text_input('MDVP:Jitter(Abs)', value="")
    RAP = st.text_input('MDVP:RAP', value="")
    PPQ = st.text_input('MDVP:PPQ', value="")
    DDP = st.text_input('Jitter:DDP', value="")
    Shimmer = st.text_input('MDVP:Shimmer', value="")
    Shimmer_dB = st.text_input('MDVP:Shimmer(dB)', value="")
    APQ3 = st.text_input('Shimmer:APQ3', value="")
    APQ5 = st.text_input('Shimmer:APQ5', value="")
    APQ = st.text_input('MDVP:APQ', value="")
    DDA = st.text_input('Shimmer:DDA', value="")
    NHR = st.text_input('NHR', value="")
    HNR = st.text_input('HNR', value="")
    RPDE = st.text_input('RPDE', value="")
    DFA = st.text_input('DFA', value="")
    spread1 = st.text_input('spread1', value="")
    spread2 = st.text_input('spread2', value="")
    D2 = st.text_input('D2', value="")
    PPE = st.text_input('PPE', value="")

    if st.button("Parkinson's Test Result", disabled=(parkinsons_model is None)):
        try:
            vals = list(map(to_float, [
                fo, fhi, flo, Jitter_percent, Jitter_Abs, RAP, PPQ, DDP,
                Shimmer, Shimmer_dB, APQ3, APQ5, APQ, DDA, NHR, HNR,
                RPDE, DFA, spread1, spread2, D2, PPE
            ]))
            label = int(parkinsons_model.predict([vals])[0])
            show_result_card("Parkinson's", label == 1)
        except Exception as e:
            st.error(f"Parkinson's prediction failed: {e}")
