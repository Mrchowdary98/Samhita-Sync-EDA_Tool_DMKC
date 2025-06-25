import streamlit as st
import hashlib

# Function to hash passwords
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# User credentials
users = {
    "dmkc@Samhita.com": hash_password("Sync@1998")
}

# Login UI
def login():
    st.title("🔐 Welcome to Samhita Sync")
    username = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if username in users and users[username] == hash_password(password):
            st.session_state["logged_in"] = True
            st.session_state["username"] = username
            st.experimental_rerun()
        else:
            st.error("Invalid email or password")

# Logout button
def logout():
    st.session_state["logged_in"] = False
    st.experimental_rerun()

# Welcome Screen after login
def show_welcome():
    st.title("👋 Welcome to Samhita Sync!")
    st.markdown("""
    ### 🔍 Explore your data with ease  
    Here's what you can do in **Samhita Sync**:

    - 📁 **Upload datasets** (.csv, .xlsx, .json, etc.)
    - 📊 **Descriptive statistics** and **data quality** reports
    - 📈 **Interactive visualizations** for patterns and distributions
    - 🧪 **Hypothesis testing** (T-test, Chi-square, Normality)
    - 🛠️ **Feature engineering** tools
    - ⏱️ **Time series** insights and trends

    ---
    """)
    st.info("Scroll down to start exploring your dataset!")
    st.markdown("---")

# Main logic
def main():
    if "logged_in" not in st.session_state:
        st.session_state["logged_in"] = False

    if not st.session_state["logged_in"]:
        login()
    else:
        st.sidebar.success(f"Logged in as: {st.session_state['username']}")
        if st.sidebar.button("Logout"):
            logout()
        else:
            # 👋 Show welcome screen first
            show_welcome()

            # 🔁 Load original EDA tool (unchanged)
            with open("app.py", "r", encoding="utf-8") as f:
                code = f.read()
                exec(code, globals())

if __name__ == "__main__":
    main()
