# app.py

import streamlit as st
import requests

# === Backend base URL ===
BACKEND_BASE = "http://127.0.0.1:8000"

st.set_page_config(
    page_title="AI Summarizer + Blog Generator",
    page_icon="🧠",
    layout="centered"
)

st.title("🧠 AI Summarizer + Blog Generator")
st.write("Paste any YouTube or website link below to summarize and optionally generate a blog post.")

# --- Input Section ---
url = st.text_input("Enter YouTube or Website URL:")
lang = st.selectbox("Choose transcript language (for YouTube):", ["en", "hi", "es", "fr"], index=0)
generate_blog = st.checkbox("Also generate a blog post from this summary")

# --- Run Button ---
if st.button("Run"):
    if not url.strip():
        st.warning("⚠️ Please enter a valid URL.")
    else:
        with st.spinner("⏳ Processing... please wait."):
            try:
                summary = None
                blog_data = {}

                # Detect YouTube or Web
                if "youtube.com" in url or "youtu.be" in url:
                    # --- Step 1: Get summary ---
                    summary_res = requests.get(
                        f"{BACKEND_BASE}/summarize/youtube",
                        params={"url": url, "lang": lang}
                    )
                    summary_res.raise_for_status()
                    summary = summary_res.json().get("summary", "")

                    # --- Step 2: Optionally generate blog ---
                    if generate_blog:
                        blog_res = requests.get(
                            f"{BACKEND_BASE}/generate-blog/youtube",
                            params={"url": url, "summary": summary, "lang": lang}
                        )
                        blog_res.raise_for_status()
                        blog_data = blog_res.json()

                else:
                    # Web URL
                    summary_res = requests.get(
                        f"{BACKEND_BASE}/summarize/web",
                        params={"url": url}
                    )
                    summary_res.raise_for_status()
                    summary = summary_res.json().get("summary", "")

                    if generate_blog:
                        blog_res = requests.get(
                            f"{BACKEND_BASE}/generate-blog/web",
                            params={"url": url, "summary": summary}
                        )
                        blog_res.raise_for_status()
                        blog_data = blog_res.json()

                # --- Display Summary ---
                st.subheader("📝 Summary")
                st.write(summary or "No summary returned.")

                # --- Display Blog ---
                if generate_blog:
                    st.subheader("📖 Generated Blog Post")
                    blog_post_text = blog_data.get("response", "No blog returned.")
                    st.markdown(blog_post_text)

                    # --- Download button ---
                    if blog_post_text != "No blog returned.":
                        st.download_button(
                            label="💾 Download Blog",
                            data=blog_post_text,
                            file_name="generated_blog.md",
                            mime="text/markdown"
                        )

            except requests.exceptions.RequestException as e:
                st.error(f"🚨 API request failed: {e}")
            except Exception as e:
                st.error(f"🚨 Unexpected error: {e}")
