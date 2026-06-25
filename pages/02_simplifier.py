import os

import streamlit as st
from backend_module import list_documents, save_document, simplify_text


st.set_page_config(
    page_title="Text Simplifier",
    layout="wide",
)

st.markdown(
    """
    <style>
        .main {background-color: #f8fafc; padding: 2rem;}
        .stTextArea textarea {font-size: 1rem !important; line-height: 1.6;}
        .output-box {background-color: #ffffff; border-radius: 12px; padding: 20px; box-shadow: 0 2px 6px rgba(0,0,0,0.1); min-height: 400px;}
        .title {font-size: 1.8rem; font-weight: 600; color: #1e293b; margin-bottom: 0.5rem;}
        .subheader {color: #475569; font-size: 1rem;}
        .stButton>button {background-color: #2563eb; color: white; border-radius: 8px; padding: 0.5rem 1rem; border: none; transition: all 0.3s;}
        .stButton>button:hover {background-color: #1d4ed8;}
    </style>
    """,
    unsafe_allow_html=True,
)

st.sidebar.title("Simplification Menu")
level = st.sidebar.radio(
    "Select Simplification Level",
    ["Basic", "Intermediate", "Advanced"],
    index=1,
)
st.sidebar.markdown("---")
st.sidebar.info("Choose a level and click Simplify Text to view results.")

st.title("Text Simplifier")
st.markdown(
    "Simplify complex legal or professional text into more readable forms. "
    "Choose a simplification level to control how deep the rewriting goes."
)

st.markdown("### Input Options")

text_input = st.text_area(
    "Paste or type your text below:",
    placeholder="Enter your text here...",
    height=200,
)

uploaded_file = st.file_uploader(
    "Or upload a TXT / DOCX / PDF document",
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
            extracted_text = "\n".join([p.text for p in doc.paragraphs])
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
        "Please clear the other input options before simplifying."
    )

final_text = input_sources[0][1] if len(input_sources) == 1 else ""

if st.button("Simplify Text"):
    if has_input_conflict:
        st.warning("Please keep only one input source active before simplifying.")
    elif final_text:
        with st.spinner("Simplifying... Please wait"):
            simplified_output = simplify_text(final_text, level)

        st.session_state.simplifier_result = {
            "original": final_text,
            "output": simplified_output,
            "level": level,
        }
    else:
        st.warning("Please enter text, upload a document, or choose a saved document before simplifying.")

if "simplifier_result" in st.session_state:
    result = st.session_state.simplifier_result
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("<div class='title'>Original Text</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='output-box'>{result['original']}</div>", unsafe_allow_html=True)

    with col2:
        st.markdown(
            f"<div class='title'>Simplified Text ({result['level']} Level)</div>",
            unsafe_allow_html=True,
        )
        st.markdown(f"<div class='output-box'>{result['output']}</div>", unsafe_allow_html=True)

    if "user" in st.session_state and st.session_state.user:
        if st.button("Save Simplification to Document Library"):
            save_document(
                st.session_state.user["id"],
                result["output"],
                filename=f"simplification_{result['level'].lower()}.txt",
                mime="text/plain",
            )
            st.success("Simplification saved to your document library.")
    else:
        st.info("Log in to save this simplification to your document library.")
