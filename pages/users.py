import streamlit as st
import duckdb

st.title("Manage Users")
st.set_page_config(page_icon="🏋️")

# Connect to database
conn = duckdb.connect("fitness_data.ddb")
# Create table if it doesn't exist
conn.execute("""
    CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY
    )
""")

# Initialize session state
if "submitted" not in st.session_state:
    st.session_state.submitted = False

# Create form
with st.form("user_form", clear_on_submit=True):
    new_user = st.text_input("Enter new username")
    submit = st.form_submit_button("Add User")

    if submit:
        st.session_state.submitted = True
        st.session_state.form_data = {
            "new_user": new_user,
        }

# Run logic after form submission
if st.session_state.get("submitted"):
    data = st.session_state.form_data
    # Check if entry exists in table
    exists = conn.execute(f"""
        SELECT 1 FROM users
        WHERE username = '{data['new_user']}'
        """
    ).fetchone()

    if not exists and data['new_user'].strip():
        conn.execute(
            "INSERT INTO users VALUES (?)",
            [data['new_user'],]
        )
        st.success("User added!")
    elif exists:
        st.warning("User already exists.")
    elif not data['new_user'].strip():
        st.warning("Enter a non-blank User.")

    # Reset flag so it doesn't rerun on every refresh
    st.session_state.submitted = False

st.markdown("---")
st.subheader("Current Users")

# Load users
df_users = conn.execute("SELECT * FROM users").fetchdf()

# Create functions to prevent double click requirements
def click_delete(username):
    st.session_state[f"confirm_delete_{username}"] = True

def confirm_delete(username):
    conn.execute("DELETE FROM users WHERE username = ?", (username,))
    st.success(f"Deleted user '{username}'")
    st.session_state[f"confirm_delete_{username}"] = False

def confirm_cancel(username):
    st.session_state[f"confirm_delete_{username}"] = False

if df_users.empty:
    st.info("No users found.")
else:
    # Create buttons to delete users
    for i, row in df_users.iterrows():
        username = row["username"]
        col1, col2 = st.columns([2, 2])
        with col1:
            st.write(f"**{username}**")
        with col2:
            confirm_key = f"confirm_delete_{username}"
    
            if confirm_key not in st.session_state:
                st.session_state[confirm_key] = False
    
            if not st.session_state[confirm_key]:
                if st.button("🗑️ Delete", key=f"delete_{username}", on_click=click_delete, args=(username,)):
                    st.session_state[confirm_key] = True
            else:
                st.warning(f"Are you sure you want to delete '{username}'?")
                col_yes, col_no = st.columns([1, 1])
                with col_yes:
                    st.button("✅ Yes", key=f"yes_delete_{username}", on_click=confirm_delete, args=(username,))
                with col_no:
                    if st.button("❌ Cancel", key=f"cancel_delete_{username}", on_click=confirm_cancel, args=(username,)):
                        st.session_state[confirm_key] = False
