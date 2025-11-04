# dashboard.py
import os
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from google.cloud import bigquery
import google.generativeai as genai
from dotenv import load_dotenv

# ---------------- PAGE SETUP ----------------
st.set_page_config(page_title="AI-Powered Governance Dashboard", layout="wide")

# ---------------- ENV SETUP ----------------
load_dotenv()

GOOGLE_CREDENTIALS = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
GENAI_API_KEY = os.getenv("GOOGLE_API_KEY")

# Configure APIs
if not GENAI_API_KEY:
    st.error("❌ Missing Gemini API key. Please set GOOGLE_API_KEY in .env file.")
else:
    genai.configure(api_key=GENAI_API_KEY)

if GOOGLE_CREDENTIALS and os.path.exists(GOOGLE_CREDENTIALS):
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = GOOGLE_CREDENTIALS
else:
    st.warning("⚠️ Google credentials file not found. Will try local CSV instead.")

# ---------------- PAGE HEADER ----------------
st.title("🏛️ AI-Powered Governance Dashboard")
st.write("Transforming Citizen Service Delivery with Predictive Insights")

# ---------------- BIGQUERY CONFIG ----------------
PROJECT_ID = "second-sandbox-477217-h7"
DATASET_ID = "governance_data"
TABLE_ID = "predicted_priorities"

# ---------------- LOAD DATA ----------------
try:
    st.info(f"🔄 Fetching data from BigQuery table `{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}` ...")
    client = bigquery.Client(project=PROJECT_ID)
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

# ---------------- DASHBOARD SECTIONS ----------------

# 1️⃣ Summary
st.header("📋 Service Request Summary")
st.dataframe(data)

# 2️⃣ Priority Distribution
st.subheader("🔍 Priority Breakdown")

if "priority_score" in data.columns:
    priority_counts = data["priority_score"].value_counts()

    # Smaller and neater chart
    fig1, ax1 = plt.subplots(figsize=(2, 2))  # 👈 reduced size here
    ax1.pie(
        priority_counts,
        labels=priority_counts.index,
        autopct="%1.1f%%",
        startangle=90,
        textprops={'fontsize': 8}  # 👈 smaller text for readability
    )
    ax1.axis("equal")  # Keeps pie chart circular
    st.pyplot(fig1)

else:
    st.info("Column 'priority_score' not found in data.")


# 3️⃣ Department-wise Pending Issues
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

# 4️⃣ Key Insights
st.subheader("💡 Key Insights")
if "priority_score" in data.columns:
    data["priority_score"] = data["priority_score"].astype(str)
    high_priority = data[data["priority_score"].str.lower().str.contains("high")]
    st.markdown(f"🚨 **Total High Priority Cases:** {len(high_priority)}")
    if "department" in high_priority.columns:
        st.markdown("**Departments with Most High Priority Issues:**")
        st.table(high_priority["department"].value_counts().head())

# 5️⃣ Severity Level
if "severity" in data.columns:
    st.subheader("🔥 Severity Level Breakdown")
    severity_counts = data["severity"].value_counts()
    st.bar_chart(severity_counts)

# 6️⃣ Gemini AI Summary
st.subheader("🤖 Gemini AI Summary of Citizen Feedback")

if st.button("Generate AI Summary"):
    try:
        text_summary = data.head(50).to_string(index=False)
        prompt = f"Summarize key trends and citizen issues based on this service dataset:\n{text_summary}"

        # ✅ Use the correct model name (without 'models/')
        # I've updated it to use the current best model for this task.
        model = genai.GenerativeModel("gemini-2.5-flash") 
        response = model.generate_content(prompt)

        st.success("✅ Gemini AI Summary Generated")
        st.write(response.text)

    except Exception as e:
        st.error(f"Gemini summarization failed: {e}")


st.info("✅ Dashboard ready and running successfully!")
