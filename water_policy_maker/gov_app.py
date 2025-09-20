import streamlit as st
import re, os
from gov_crew import crew

st.set_page_config(page_title="🏛 Policy Crew", page_icon="📑", layout="wide")

st.title("🏛 Government Policy Maker Assistant")
st.markdown("Upload datasets and documents, describe a policy problem, and let the AI crew research, draft, and critique a policy for you.")


uploaded_files = st.file_uploader(
    "📂 Upload files (CSV, XLSX, TXT)",
    type=["csv", "xlsx", "xls", "txt"],
    accept_multiple_files=True
)


policy_problem = st.text_area(
    "📝 Policy Problem",
    placeholder="e.g., Reduce groundwater depletion in Rajasthan",
    height=100
)


if st.button("🚀 Run Policy Crew"):
    if not policy_problem.strip():
        st.error("❌ Please enter a policy problem.")
    else:
        # Save uploaded files temporarily
        file_paths = []
        for f in uploaded_files:
            file_path = os.path.join("temp", f.name)
            os.makedirs("temp", exist_ok=True)
            with open(file_path, "wb") as out_file:
                out_file.write(f.read())
            file_paths.append(file_path)

        st.info("⏳ Running Policy Crew... this may take a while.")

        inputs = {"policy_problem": policy_problem, "files": file_paths}
        result = crew.kickoff(inputs=inputs)
        text = str(result)

        # Show result
        st.subheader("📑 Final Policy Output")
        st.text_area("Output", text, height=400)

        # Save to file
        fname = re.sub(r"[^\w\d-]", "_", policy_problem)[:50] + ".md"
        with open(fname, "w", encoding="utf-8") as f:
            f.write(text)

        st.download_button("📥 Download Result", data=text, file_name=fname, mime="text/markdown")

        # Cleanup temp files
        for fp in file_paths:
            os.remove(fp)
