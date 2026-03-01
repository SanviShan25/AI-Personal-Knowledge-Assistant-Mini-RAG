import streamlit as st
import requests

BACKEND_URL = "http://127.0.0.1:8000"

st.set_page_config(page_title="AI Knowledge Assistant", layout="wide")

st.title("📚 AI Knowledge Assistant")
st.markdown("Upload a document and chat with it.")

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
        f"{BACKEND_URL}/login",
        data={"username": email, "password": password},
    )

    if response.status_code == 200:
        st.session_state.token = response.json()["access_token"]
        st.sidebar.success("Logged in successfully!")
    else:
        st.sidebar.error("Login failed")

# ---------------- UPLOAD ----------------

st.header("📤 Upload Document")

uploaded_file = st.file_uploader("Upload a PDF", type=["pdf"])

if uploaded_file and st.session_state.token:
    headers = {
        "Authorization": f"Bearer {st.session_state.token}"
    }

    response = requests.post(
        f"{BACKEND_URL}/upload",
        files={"file": uploaded_file},
        headers=headers
    )

    if response.status_code == 200:
        st.success("Document processed successfully!")
    else:
        st.error("Upload failed")

# ---------------- CHAT SECTION ----------------

st.header("💬 Chat with Your Document")

if not st.session_state.token:
    st.warning("Please login first.")
else:

    # Display previous messages
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Chat input
    user_input = st.chat_input("Ask something about your document...")

    if user_input:

        # Show user message
        st.session_state.chat_history.append(
            {"role": "user", "content": user_input}
        )

        with st.chat_message("user"):
            st.markdown(user_input)

        # Call backend
        headers = {
            "Authorization": f"Bearer {st.session_state.token}"
        }

        response = requests.post(
            f"{BACKEND_URL}/query",
            json={
                "question": user_input,
                "chat_history": st.session_state.chat_history
        },
            headers=headers
        )

        if response.status_code == 200:
            data = response.json()
            answer = data["answer"]

            # Append assistant answer
            st.session_state.chat_history.append(
                {"role": "assistant", "content": answer}
            )

            with st.chat_message("assistant"):
                st.markdown(answer)

                # Expandable sources
                with st.expander("Sources"):
                    for src in data["sources"]:
                        st.write(src)

        else:
            st.error("Query failed")




