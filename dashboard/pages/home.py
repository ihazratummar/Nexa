import streamlit as st
import requests

# This is the landing page. It will have a login button.

st.set_page_config(layout="wide")

st.title("Welcome to the Nexa Bot Dashboard")

st.markdown("""
    <style>
    .stButton>button {
        background-color: #7289da;
        color: white;
        font-size: 20px;
        height: 3em;
        width: 15em;
        border-radius: 10px;
    }
    </style>
""", unsafe_allow_html=True)

# We will use a session state to check if the user is logged in.
# This is a client-side session state, not the server-side session.
if 'user' not in st.session_state:
    st.session_state.user = None

# Check if the user is logged in by making a request to the backend
if st.session_state.user is None:
    try:
        response = requests.get("http://localhost:8000/", cookies=st.query_params)
        if response.status_code == 200 and "username" in response.json().get("message", ""):
            st.session_state.user = response.json()["message"]
    except requests.exceptions.ConnectionError:
        st.error("Connection to the backend failed. Make sure the backend is running.")
        st.stop()

if st.session_state.user:
    st.switch_page("dashboard_page.py")
else:
    st.write("Please login to continue.")
    if st.button("Login with Discord"):
        # Redirect to the FastAPI login URL
        st.markdown('<meta http-equiv="refresh" content="0; url=/login">', unsafe_allow_html=True)