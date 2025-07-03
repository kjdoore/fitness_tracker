import streamlit as st
import datetime
import duckdb
from numpy import nan

st.title("Previous Workout")
st.set_page_config(page_icon="🏋️")

# Connect to DuckDB (creates file if it doesn't exist)
conn = duckdb.connect("fitness_data.ddb")

# Get the list of users
usernames = conn.execute("SELECT username FROM users").fetchdf()["username"].tolist()

# Initialize session state
if "submitted" not in st.session_state:
    st.session_state.submitted = False

# Create form
with st.form("entry_form", border=False):
    # As streamlit does not allow for selectboxes with empty lists
    # to have a placeholder value, let's make a proxy to do that.
    if usernames:
         username = st.selectbox("Select username", usernames)
    else:
        st.selectbox("Select username", ["No Users in System"], index=0, disabled=True)
        username = None
    date = st.date_input("Date", value=datetime.date.today())
    
    submit = st.form_submit_button("Get Workout")

    if submit:
        st.session_state.submitted = True
        st.session_state.form_data = {
            'username': username,
            'date': date,
        }

# Run logic after form submission
if st.session_state.get("submitted"):
    data = st.session_state.form_data
    # Get the workout
    workout = conn.execute(f"""
        SELECT exercise, weight, reps, set FROM fitness_data
        WHERE username = '{data['username']}'
        AND date = DATE '{data['date']}'
        """
    ).fetchdf()

    # Check the max number of sets performed
    max_sets = workout['set'].max()
    # If any sets are performed, create a table
    if max_sets is not nan:
        workout['description'] = workout['weight'].astype(str) + 'lb for ' + workout['reps'].astype(str)
        workout_pivot = workout.pivot(index='exercise', columns='set', values='description')
        workout_pivot.columns = [f"Set {i}" for i in workout_pivot.columns]

        st.markdown(workout_pivot)
        # Include dataframe output in case we like the look of the other more.
        # st.dataframe(workout_pivot, hide_index=False)
    else:
        st.warning(f"No workout for {data['username']} on {data['date'].strftime('%Y/%m/%d')}.")

    # Reset flag so it doesn't rerun on every refresh
    st.session_state.submitted = False
