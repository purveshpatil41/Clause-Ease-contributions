# pages/summarizer.py
import os

import streamlit as st
from backend_module import list_documents, save_document, summarize_text


st.markdown(
    """
    <style>
    .title {font-size: 32px; font-weight: bold; margin-bottom: 20px;}
    .subtitle {font-size: 20px; margin-bottom: 15px; color: #555;}
    .card {background-color: #f9f9f9; padding: 15px; border-radius: 10px; margin-bottom: 15px;}
    textarea {width: 100%;}
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="title">Text Summarizer</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="subtitle">Generate a Qwen summary based on your compression ratio</div>',
    unsafe_allow_html=True,
)

text_input = st.text_area("Paste text here...", height=200)

uploaded_file = st.file_uploader(
    "Or upload a TXT/DOCX/PDF file",
    type=["txt", "docx", "pdf"],
)
extracted_text = ""
selected_doc_text = ""

if uploaded_file:
    try:
        ext = os.path.splitext(uploaded_file.name)[1].lower()
        if ext == ".txt":
            extracted_text = uploaded_file.read().decode("utf-8")
        elif ext == ".docx":
            from docx import Document

            doc = Document(uploaded_file)
            extracted_text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
        elif ext == ".pdf":
            from PyPDF2 import PdfReader

            reader = PdfReader(uploaded_file)
            pages = []
            for page in reader.pages:
                pages.append(page.extract_text() or "")
            extracted_text = "\n".join(pages)
    except Exception as e:
        st.error(f"Failed to read file: {e}")

if "user" in st.session_state and st.session_state.user:
    saved_docs = list_documents(st.session_state.user["id"])
    if saved_docs:
        doc_options = {
            f"#{doc['id']} - {doc['filename'] or 'Untitled'}": doc
            for doc in saved_docs
        }
        selected_doc = st.selectbox(
            "Or choose a saved document from your library",
            ["None"] + list(doc_options.keys()),
        )
        if selected_doc != "None":
            selected_doc_text = doc_options[selected_doc]["content"]
    else:
        st.info("No saved documents found in your library yet.")

input_sources = []
if text_input.strip():
    input_sources.append(("pasted text", text_input.strip()))
if extracted_text.strip():
    input_sources.append(("uploaded document", extracted_text.strip()))
if selected_doc_text.strip():
    input_sources.append(("document library", selected_doc_text.strip()))

has_input_conflict = len(input_sources) > 1
if has_input_conflict:
    selected_sources = ", ".join(source_name for source_name, _ in input_sources)
    st.warning(
        f"You can use only one input source at a time. You are currently using: {selected_sources}. "
        "Please clear the other input options before summarizing."
    )

final_text = input_sources[0][1] if len(input_sources) == 1 else ""

compression_ratio = st.slider("Compression ratio", 0.1, 1.0, 0.4, 0.05)

if st.button("Generate Summary"):
    if has_input_conflict:
        st.warning("Please keep only one input source active before summarizing.")
    elif final_text:
        with st.spinner("Generating summary..."):
            summary = summarize_text(
                final_text,
                compression_ratio=compression_ratio,
            )

        st.session_state.summary_result = {
            "original": final_text,
            "output": summary,
            "compression_ratio": compression_ratio,
        }
    else:
        st.warning("Please provide text, upload a file, or choose a saved document to summarize.")

if "summary_result" in st.session_state:
    result = st.session_state.summary_result

    st.markdown('<div class="subtitle">Original Text</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="card">{result["original"]}</div>', unsafe_allow_html=True)

    st.markdown('<div class="subtitle">Summary</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="card">{result["output"]}</div>', unsafe_allow_html=True)

    if "user" in st.session_state and st.session_state.user:
        if st.button("Save Summary to Document Library"):
            save_document(
                st.session_state.user["id"],
                result["output"],
                filename=f"summary_{int(result['compression_ratio'] * 100)}pct.txt",
                mime="text/plain",
            )
            st.success("Summary saved to your document library.")
    else:
        st.info("Log in to save this summary to your document library.")
