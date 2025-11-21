
import streamlit as st
import requests

st.set_page_config(layout="wide")

# This is the dashboard page. It will be shown after the user logs in.

# We will use a session state to check if the user is logged in.
# This is a client-side session state, not the server-side session.
if 'user' not in st.session_state:
    st.session_state.user = None

# Check if the user is logged in by making a request to the backend
if st.session_state.user is None:
    try:
        # The user should be logged in at this point, but
        # We need to pass the cookies to the backend
        cookies = st.query_params
        response = requests.get("http://localhost:8000/dashboard", cookies=cookies)

        if response.status_code == 200 and "username" in response.json().get("message", ""):
            st.session_state.user = response.json()["message"]
        else:
            st.switch_page("home.py")

    except requests.exceptions.ConnectionError:
        st.error("Connection to the backend failed. Make sure the backend is running.")
        st.stop()
    except Exception as e:
        st.error(f"An error occurred: {e}")
        st.switch_page("home.py")


st.title(f"Welcome, {st.session_state.user.get('username', '')}!")

st.write("This is your dashboard. You can add your bot's stats and controls here.")

# Display user information
col1, col2 = st.columns(2)
with col1:
    st.image(f"https://cdn.discordapp.com/avatars/{st.session_state.user['id']}/{st.session_state.user['avatar']}.png", width=150)
with col2:
    st.write(f"**Username:** {st.session_state.user['username']}")
    st.write(f"**Email:** {st.session_state.user.get('email', 'N/A')}")

if st.button("Logout"):
    requests.get("http://localhost:8000/logout")
    st.session_state.user = None
    st.switch_page("home.py")

