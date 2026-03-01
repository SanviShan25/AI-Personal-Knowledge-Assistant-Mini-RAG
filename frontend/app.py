import streamlit as st
import requests

API_URL = "http://127.0.0.1:8000"

st.set_page_config(page_title="AI Knowledge Assistant", layout="wide")

st.title("📚 AI Knowledge Assistant")
st.markdown("Upload one or more documents and chat with them.")

# ---------------- SESSION STATE ----------------

if "token" not in st.session_state:
    st.session_state.token = None

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# ---------------- LOGIN ----------------

st.sidebar.header("🔐 Login")

email = st.sidebar.text_input("Email")
password = st.sidebar.text_input("Password", type="password")

if st.sidebar.button("Login"):
    response = requests.post(
        f"{API_URL}/login",
        data={"username": email, "password": password},
    )

    if response.status_code == 200:
        st.session_state.token = response.json()["access_token"]
        st.sidebar.success("Logged in successfully!")
    else:
        st.sidebar.error("Login failed")

# ---------------- UPLOAD SECTION ----------------

st.header("📤 Upload Document(s)")

uploaded_files = st.file_uploader(
    "Upload PDF(s)",
    type=["pdf"],
    accept_multiple_files=True
)

if uploaded_files:

    if not st.session_state.token:
        st.error("Please login first.")
    else:
        for uploaded_file in uploaded_files:

            files = {
                "file": (
                    uploaded_file.name,
                    uploaded_file.getvalue(),
                    "application/pdf"
                )
            }

            response = requests.post(
                f"{API_URL}/upload",
                headers={
                    "Authorization": f"Bearer {st.session_state.token}"
                },
                files=files
            )

            if response.status_code == 200:
                st.success(f"{uploaded_file.name} uploaded successfully!")
            else:
                st.error(f"Upload failed for {uploaded_file.name}")

# ---------------- CHAT SECTION ----------------

st.header("💬 Chat with Your Documents")

if not st.session_state.token:
    st.warning("Please login first.")
else:

    # Show previous messages
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    user_input = st.chat_input("Ask something about your document...")

    if user_input:

        # Show user message
        st.session_state.chat_history.append(
            {"role": "user", "content": user_input}
        )

        with st.chat_message("user"):
            st.markdown(user_input)

        headers = {
            "Authorization": f"Bearer {st.session_state.token}"
        }

        response = requests.post(
            f"{API_URL}/query",
            json={
                "question": user_input,
                "chat_history": st.session_state.chat_history
            },
            headers=headers
        )

        if response.status_code == 200:
            data = response.json()
            answer = data["answer"]

            st.session_state.chat_history.append(
                {"role": "assistant", "content": answer}
            )

            with st.chat_message("assistant"):
                st.markdown(answer)

                with st.expander("Sources"):
                    for src in data["sources"]:
                        st.write(src)

        else:
            st.error("Query failed")