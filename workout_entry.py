import streamlit as st
import duckdb
import datetime
import numpy as np

st.title("Workout Entry Sheet")
st.set_page_config(page_icon="🏋️")

# Connect to DuckDB (creates file if it doesn't exist)
conn = duckdb.connect("fitness_data.ddb")
# Create tables if it doesn't exist
# We need to check if all required tables exist, as we will need them
conn.execute("""
    CREATE TABLE IF NOT EXISTS fitness_data (
        username TEXT,
        date DATE,
        exercise TEXT,
        weight INTEGER,
        reps INTEGER,
        set INTEGER,
        rpe INTEGER,
        super_set INTEGER,
    )
""")
conn.execute("""
    CREATE TABLE IF NOT EXISTS exercises (
        muscle_group TEXT,
        exercise TEXT
    )
""")
conn.execute("""
    CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY
    )
""")

# Get the list of exercises grouped by muscle type
# This will be used to limit exercise selection
exercises = (
    conn
    .execute("SELECT * FROM exercises")
    .fetchdf()
    .groupby('muscle_group')['exercise']
    .apply(lambda x: sorted([i for i in x]))
    .sort_index()
    .to_dict()
)
# Get the list of users
usernames = conn.execute("SELECT username FROM users").fetchdf()["username"].tolist()

# Create the selectboxes outside of form to allow for dependence
# of exercise on muscle group.
# As streamlit does not allow for selectboxes with empty lists
# to have a placeholder value, let's make a proxy to do that.
if usernames:
     username = st.selectbox("Select username", usernames)
else:
    st.selectbox("Select username", ["No Users in System"], index=0, disabled=True)
    username = None
date = st.date_input("Date", value=datetime.date.today())
if exercises:
    muscle_group = st.selectbox("Select exercise muscle group", list(exercises.keys()))
    exercise = st.selectbox("Select exercise", exercises[muscle_group] if len(list(exercises.keys())) > 0 else [])
else:
    st.selectbox("Select exercise muscle group", ["No Exercises in System"], index=0, disabled=True)
    st.selectbox("Select exercise", ["No Exercises in System"], index=0, disabled=True)
    exercise = None

set_num = st.number_input("Set", min_value=1)
column2 = st.columns(2)
with column2[0]:
    super_set = st.checkbox("Super Set")
with column2[1]:
    # We only want a super set value if it is a super set
    if super_set:
        super_set_num = st.number_input("Super Set", min_value=1)
    else:
        super_set_num = None

column3 = st.columns(3)
with column3[0]:
    # Do weight steps in 5 lb intervals. Can still type any integer,
    # but make the +/- buttons go in increments of 5.
    weight = st.number_input("Weight (lbs)", min_value=0, step=5)
with column3[1]:
    reps = st.number_input("Reps", min_value=1)
with column3[2]:
    rpe = st.number_input("RPE", min_value=1, max_value=10)


# Initialize session state
if "needs_confirmation" not in st.session_state:
    st.session_state.needs_confirmation = False
if "submitted" not in st.session_state:
    st.session_state.submitted = False

# Create form
with st.form("entry_form", border=False):
    submit = st.form_submit_button("Submit Entry")

    if submit:
        st.session_state.submitted = True
        st.session_state.form_data = {
            'username': username,
            'date': date,
            'exercise': exercise,
            'weight': weight,
            'reps': reps,
            'set_num': set_num,
            'rpe': rpe,
            'super_set_num': super_set_num,
        }

# Run logic after form submission
if st.session_state.get("submitted"):
    data = st.session_state.form_data
    # Check if workout and set entry exists in table
    exists = conn.execute(f"""
        SELECT 1 FROM fitness_data
        WHERE username = '{data['username']}'
        AND date = DATE '{data['date']}'
        AND exercise = '{data['exercise']}'
        AND set = {data['set_num']}
        """
    ).fetchone()


    if not exists and data['username'] and data['exercise']:
        conn.execute(f"""
            INSERT INTO fitness_data (username, date, exercise, weight, reps, set, rpe, super_set)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [data['username'], data['date'], data['exercise'],
             data['weight'], data['reps'], data['set_num'],
             data['rpe'], data['super_set_num']]
        )
        st.success("Entry added!")
    elif exists:
        st.session_state.needs_confirmation = True
    elif not data['username']:
        st.warning("Select a User.")
    elif not data['exercise']:
        st.warning("Select an exercise.")

    # Reset flag so it doesn't rerun on every refresh
    st.session_state.submitted = False

if st.session_state.needs_confirmation:
    st.warning("Set entry already exists.")
    # Show a confirmation button
    if st.button("Confirm Override"):
        data = st.session_state.form_data
        conn.execute(f"""
            DELETE FROM fitness_data
            WHERE username = '{data['username']}'
            AND date = DATE '{data['date']}'
            AND exercise = '{data['exercise']}'
            AND set = {data['set_num']}
        """)
        conn.execute(f"""
            INSERT INTO fitness_data (username, date, exercise, weight, reps, set, rpe, super_set)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [data['username'], data['date'], data['exercise'],
             data['weight'], data['reps'], data['set_num'],
             data['rpe'], data['super_set_num']]
        )
        st.success("Entry overridden successfully.")

        st.session_state.needs_confirmation = False

# View most recent 20 entries
if st.checkbox("Show 20 most recent entries"):
    df = conn.execute("SELECT * FROM fitness_data ORDER BY date DESC LIMIT 20").fetchdf()
    st.dataframe(df, hide_index=True)
