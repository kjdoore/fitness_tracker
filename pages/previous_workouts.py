import streamlit as st
import datetime
import duckdb
from numpy import nan
from pandas._libs.missing import NAType

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
        SELECT exercise, weight, reps, set, rpe, super_set, rep_range_min, rep_range_max FROM fitness_data
        WHERE username = '{data['username']}'
        AND date = DATE '{data['date']}'
        """
    ).fetchdf()

    # Check the max number of sets performed
    max_sets = workout['set'].max()
    # If any sets are performed, create a table
    if max_sets is not nan:
        workout['description'] = (
            workout['weight'].astype(str) + 'lb x '
            + workout['reps'].astype(str) + ' reps at '
            + workout['rpe'].astype(str) + ' RPE'
        )

        table = f"| Exercise | Rep Range | Super Set | {' | '.join([f'Set {i}' for i in range(1, workout['set'].max() + 1)])} |\n"
        table += f"| -------- | --------- | --------- | {' | '.join([f'-----' for i in range(1, workout['set'].max() + 1)])} |\n"

        for exercise, set_info in workout.groupby('exercise'):
            temp = f"| {exercise} "
            temp += f"| {set_info['rep_range_min'].unique()[0]}-{set_info['rep_range_max'].unique()[0]} "
            temp += f"| {'' if isinstance(set_info['super_set'].unique()[0], NAType) else set_info['super_set'].unique()[0]} "
            temp += f"| {' | '.join([
                f"{row['description']}" for _, row in set_info.set_index('set').iterrows()
            ])} |"
            temp += ' |' * (max_sets - (temp.count('|') - 4))
            table += f"{temp}\n"

        st.markdown(table)

        # Include dataframe output in case we like the look of the other more.
        # workout_pivot = workout.pivot(index=['exercise', 'super_set'], columns='set', values='description')
        # workout_pivot.columns = [f"Set {i}" for i in workout_pivot.columns]
        # st.dataframe(workout_pivot.reset_index(), hide_index=True)
    else:
        st.warning(f"No workout for {data['username']} on {data['date'].strftime('%Y/%m/%d')}.")

    # Reset flag so it doesn't rerun on every refresh
    st.session_state.submitted = False
