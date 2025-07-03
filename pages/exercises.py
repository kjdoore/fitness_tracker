import streamlit as st
import duckdb

st.title("Exercise List")
st.set_page_config(page_icon="🏋️")

# Connect to DuckDB (creates file if it doesn't exist)
conn = duckdb.connect("fitness_data.ddb")

# Read in premade list of muscle groups
with open("muscle_groups.txt", "r") as file:
    muscles_groups = [line.strip() for line in file]

# Initialize session state
if "submitted" not in st.session_state:
    st.session_state.submitted = False

# Create form
with st.form("exercise_form", clear_on_submit=True):
    muscle_group = st.selectbox("Muscle Group", muscles_groups)
    exercise = st.text_input("Exercise")
    submit = st.form_submit_button("Add Exercise")

    if submit:
        st.session_state.submitted = True
        st.session_state.form_data = {
            "muscle_group": muscle_group,
            "exercise": exercise,
        }

# Run logic after form submission
if st.session_state.get("submitted"):
    data = st.session_state.form_data
    # Check if entry exists in table
    exists = conn.execute(f"""
        SELECT 1 FROM exercises
        WHERE muscle_group = '{data['muscle_group']}'
        AND exercise = '{data['exercise']}'
        """
    ).fetchone()

    if not exists and data['exercise'].strip():
        conn.execute(
            "INSERT INTO exercises (muscle_group, exercise) VALUES (?, ?)",
            [data['muscle_group'], data['exercise']]
        )
        st.success("Exercise added!")
    elif exists:
        st.warning("Exercise already exists.")
    elif not data['exercise'].strip():
        st.warning("Enter a non-blank exercise.")

    # Reset flag so it doesn't rerun on every refresh
    st.session_state.submitted = False

# View entries
if st.checkbox("Show all entries", value=True):
    df = conn.execute("SELECT * FROM exercises").fetchdf()
    st.dataframe(df.sort_values(['muscle_group', 'exercise']), hide_index=True)
