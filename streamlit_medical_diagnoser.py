import streamlit as st
import numpy as np
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Symptom Checker — Medical Diagnostic (Demo)", layout="wide")
st.title("🩺 Symptom Checker — Simple Diagnostic Demo")
st.markdown(
    "This demo app finds likely diseases by matching your symptoms to known disease symptom sets. *Not medical advice.* See the disclaimer at the bottom."
)

# --- Knowledge base (example/demo only) ---
# Each disease maps to a set/list of common symptoms. This is a small demo dataset — replace with your dataset or model for production.
DISEASE_SYMPTOMS = {
    "Common Cold": ["cough", "sore throat", "runny nose", "congestion", "sneezing", "mild fever"],
    "Influenza (Flu)": ["high fever", "body aches", "chills", "fatigue", "cough", "headache", "sore throat"],
    "COVID-19": ["fever", "dry cough", "fatigue", "loss of taste", "loss of smell", "shortness of breath"],
    "Gastroenteritis": ["nausea", "vomiting", "diarrhea", "stomach pain", "dehydration"],
    "Migraine": ["severe headache", "nausea", "sensitivity to light", "visual aura"],
    "Urinary Tract Infection": ["painful urination", "frequent urination", "lower abdominal pain", "cloudy urine"],
    "Hypertension (high BP)": ["headache", "dizziness", "nosebleed", "shortness of breath"],
}

# Example disease info (descriptions, common meds / steps). Replace with your own content or source.
DISEASE_INFO = {
    "Common Cold": {
        "description": "A mild viral respiratory infection. Symptoms are usually mild and self-limiting.",
        "advice": "Rest, fluids, OTC cold remedies. See doctor if high fever or symptoms worsen.",
    },
    "Influenza (Flu)": {
        "description": "A contagious respiratory illness caused by influenza viruses. Can be serious for some groups.",
        "advice": "Antiviral medication if prescribed, rest, fluids. Seek medical care for breathing problems or persistent fever.",
    },
    "COVID-19": {
        "description": "Respiratory illness caused by SARS-CoV-2. Symptoms range from mild to severe.",
        "advice": "Test for COVID-19 if appropriate, isolate if positive, seek care for breathing difficulty.",
    },
    "Gastroenteritis": {
        "description": "Inflammation of the stomach and intestines, often causing vomiting and diarrhea.",
        "advice": "Oral rehydration, rest. Seek care for signs of severe dehydration.",
    },
    "Migraine": {
        "description": "A neurological condition characterized by intense headaches and other symptoms.",
        "advice": "Rest in a dark quiet room, prescribed migraine medications, and consult a neurologist for recurrent attacks.",
    },
    "Urinary Tract Infection": {
        "description": "Infection of the urinary tract, commonly causing burning urination and frequency.",
        "advice": "See a clinician for urine testing and antibiotics if indicated.",
    },
    "Hypertension (high BP)": {
        "description": "Elevated blood pressure which may be asymptomatic or cause headaches/dizziness.",
        "advice": "Measure BP, lifestyle changes, and consult a doctor for long-term management.",
    },
}

# Build a master symptom list
all_symptoms = sorted({s.lower() for symptoms in DISEASE_SYMPTOMS.values() for s in symptoms})

# --- Sidebar inputs ---
with st.sidebar:
    st.header("How to use")
    st.write("Pick symptoms from the list or type your own (comma-separated). The app will score diseases by symptom overlap.")
    selected = st.multiselect("Select symptoms (pick from known list)", all_symptoms)
    free_text = st.text_area("Or type symptoms (comma separated)", value="", help="e.g. fever, cough, headache")
    show_all = st.checkbox("Show full knowledge base (for debugging)", value=False)
    run = st.button("Check")

# Helper: normalize list of symptoms provided by user
def normalize_symptoms(text_list, selected_list):
    user_set = set()
    # from multiselect
    for s in selected_list:
        if s and isinstance(s, str):
            user_set.add(s.strip().lower())
    # from free text
    if text_list:
        parts = [p.strip().lower() for p in text_list.split(',') if p.strip()]
        for p in parts:
            user_set.add(p)
    return sorted(user_set)

# Scoring function: simple overlap score
def score_diseases(user_symptoms):
    scores = []
    for disease, symptoms in DISEASE_SYMPTOMS.items():
        set_sym = {s.lower() for s in symptoms}
        match = set_sym.intersection(user_symptoms)
        # confidence = matched symptoms / total disease symptoms (as %)
        confidence = len(match) / max(1, len(set_sym))
        scores.append({
            'disease': disease,
            'matched_symptoms': sorted(list(match)),
            'match_count': len(match),
            'disease_symptom_count': len(set_sym),
            'confidence': confidence,
        })
    # sort by confidence then by match_count
    return sorted(scores, key=lambda x: (x['confidence'], x['match_count']), reverse=True)

# Main logic when user clicks Check
if run:
    user_symptoms = normalize_symptoms(free_text, selected)
    if not user_symptoms:
        st.warning("Please select or enter at least one symptom.")
    else:
        st.subheader("Your symptoms")
        st.write(", ".join(user_symptoms))

        scores = score_diseases(set(user_symptoms))
        top = [s for s in scores if s['match_count'] > 0]

        if not top:
            st.info("No strong matches found in the demo knowledge base. Consider adding more specific symptoms or consult a clinician.")
        else:
            # show top 5
            top_n = top[:5]
            df = pd.DataFrame([
                {
                    'Disease': t['disease'],
                    'Matched Symptoms': ", ".join(t['matched_symptoms']),
                    'Match Count': t['match_count'],
                    'Total Disease Symptoms': t['disease_symptom_count'],
                    'Confidence (%)': round(t['confidence'] * 100, 1),
                }
                for t in top_n
            ])

            st.subheader("Top matches")
            st.table(df)

            # Bar chart of confidences for top diseases
            st.subheader("Confidence scores")
            chart_df = pd.DataFrame({
                'disease': [t['disease'] for t in top_n],
                'confidence': [t['confidence'] for t in top_n],
            })
            st.bar_chart(chart_df.set_index('disease'))

            # Detailed info for the top-most disease
            best = top_n[0]
            st.subheader(f"Most likely: {best['disease']} — {round(best['confidence']*100,1)}% match")
            info = DISEASE_INFO.get(best['disease'], {})
            if info:
                st.markdown(f"**Description:** {info.get('description','N/A')}")
                st.markdown(f"**Advice / next steps:** {info.get('advice','N/A')}")

            # Allow download of results
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button("Download results (CSV)", data=csv, file_name=f"symptom_check_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")

# Optional: show full KB
if show_all:
    st.markdown("---")
    st.subheader("Knowledge base (demo)")
    kb = pd.DataFrame([
        {'Disease': d, 'Symptoms': ', '.join(s)} for d, s in DISEASE_SYMPTOMS.items()
    ])
    st.dataframe(kb)

# Footer / disclaimer
st.markdown("---")
st.warning("**Disclaimer:** This application is a simple demo and not a substitute for professional medical diagnosis. If you are experiencing serious or life-threatening symptoms (chest pain, difficulty breathing, severe bleeding, confusion, fainting), seek emergency medical care immediately.")
