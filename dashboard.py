import os
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from google.cloud import bigquery
from google.oauth2 import service_account
import google.generativeai as genai
from dotenv import load_dotenv

st.set_page_config(page_title="AI-Powered Governance Dashboard", layout="wide")

load_dotenv()
GENAI_API_KEY = os.getenv("GOOGLE_API_KEY")

if not GENAI_API_KEY:
    st.error("❌ Missing Gemini API key. Please set GOOGLE_API_KEY in your environment or Streamlit secrets.")
else:
    genai.configure(api_key=GENAI_API_KEY)

st.title("🏛️ AI-Powered Governance Dashboard")
st.write("Transforming Citizen Service Delivery with Predictive Insights")

PROJECT_ID = "second-sandbox-477217-h7"
DATASET_ID = "governance_data"
TABLE_ID = "predicted_priorities"

try:
    service_account_info = st.secrets["bigquery_service_account"]
    credentials = service_account.Credentials.from_service_account_info(service_account_info)
    client = bigquery.Client(credentials=credentials, project=service_account_info["project_id"])

    query = f"SELECT * FROM `{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}` LIMIT 1000"
    data = client.query(query).to_dataframe()
    st.success("✅ Data loaded from BigQuery successfully!")

except Exception as e:
    st.warning(f"⚠️ BigQuery not configured — using local CSV file. Error: {e}")
    try:
        data = pd.read_csv("predicted_priorities.csv")
        st.success("✅ Local CSV file loaded successfully.")
    except FileNotFoundError:
        st.error("❌ No BigQuery connection and no local CSV found. Please check configuration.")
        st.stop()

st.header("📋 Service Request Summary")
st.dataframe(data)

st.subheader("🔍 Priority Breakdown")
if "priority_score" in data.columns:
    priority_counts = data["priority_score"].value_counts()
    fig1, ax1 = plt.subplots(figsize=(2, 2))
    ax1.pie(
        priority_counts,
        labels=priority_counts.index,
        autopct="%1.1f%%",
        startangle=90,
        textprops={'fontsize': 8}
    )
    ax1.axis("equal")
    st.pyplot(fig1)
else:
    st.info("Column 'priority_score' not found in data.")

st.subheader("🏢 Department-wise Pending Issues")
if "resolved" in data.columns and "department" in data.columns:
    data["resolved"] = data["resolved"].astype(str).str.strip().str.lower()
    unresolved_filter = data["resolved"].isin(["no", "false", "0"])
    unresolved = data[unresolved_filter]["department"].value_counts()
    if not unresolved.empty:
        st.bar_chart(unresolved)
    else:
        st.info("✅ No unresolved issues found.")
else:
    st.info("⚠️ Columns 'resolved' or 'department' not found in data.")

st.subheader("💡 Key Insights")
if "priority_score" in data.columns:
    data["priority_score"] = data["priority_score"].astype(str)
    high_priority = data[data["priority_score"].str.lower().str.contains("high")]
    st.markdown(f"🚨 **Total High Priority Cases:** {len(high_priority)}")
    if "department" in high_priority.columns:
        st.markdown("**Departments with Most High Priority Issues:**")
        st.table(high_priority["department"].value_counts().head())

if "severity" in data.columns:
    st.subheader("🔥 Severity Level Breakdown")
    severity_counts = data["severity"].value_counts()
    st.bar_chart(severity_counts)

st.subheader("🤖 Gemini AI Summary of Citizen Feedback")
if st.button("Generate AI Summary"):
    try:
        text_summary = data.head(50).to_string(index=False)
        prompt = f"Summarize key trends and citizen issues based on this service dataset:\n{text_summary}"

        model = genai.GenerativeModel("gemini-2.0-flash")
        response = model.generate_content(prompt)

        st.success("✅ Gemini AI Summary Generated")
        st.write(response.text)

    except Exception as e:
        st.error(f"Gemini summarization failed: {e}")

st.info("✅ Dashboard ready and running successfully!")
