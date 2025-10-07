import streamlit as st
import pandas as pd

# --- Page Configuration ---
# Set the page title and a descriptive icon for the browser tab.
st.set_page_config(
    page_title="Google Sheet Viewer",
    page_icon="📊",
    layout="wide" # Use the full page width for a better view of the data.
)

# --- App Title and Description ---
st.title("📊 Google Sheet Data Viewer")
st.markdown("This application reads data directly from a public Google Sheet and displays it in an interactive table.")

# --- Data Loading Function ---
# We use st.cache_data to store the data in memory after the first load.
# This makes the app faster because it won't re-download the data every time you interact with it.
@st.cache_data
def load_data(sheet_url):
    """
    Takes a Google Sheet URL, converts it to a CSV export URL,
    and returns the data as a Pandas DataFrame.
    """
    try:
        # The URL is modified to point to a CSV export of the sheet.
        csv_url = sheet_url.replace("/edit?usp=sharing", "/export?format=csv")
        df = pd.read_csv(csv_url)
        return df
    except Exception as e:
        # Display a user-friendly error message if the sheet can't be accessed.
        st.error(f"Failed to load data. Please ensure the Google Sheet is public. Error: {e}")
        return None

# The public URL of your Google Sheet.
GOOGLE_SHEET_URL = "https://docs.google.com/spreadsheets/d/109p39EGYEikgbZT4kSW71_sXJNMM-4Tjjd5q-l9Tx_0/edit?usp=sharing"

# --- Main App Logic ---
# Load the data using the function defined above.
dataframe = load_data(GOOGLE_SHEET_URL)

# Only attempt to display the data if it was loaded successfully.
if dataframe is not None:
    # --- Summary Metrics ---
    st.header("Project Progress Summary")

    try:
        # Convert relevant columns to numeric, coercing errors to NaN and filling with 0
        # This prevents errors if the columns contain non-numeric data or are empty.
        design_col = pd.to_numeric(dataframe['Design'], errors='coerce').fillna(0)
        build_col = pd.to_numeric(dataframe['Build'], errors='coerce').fillna(0)
        left_col = pd.to_numeric(dataframe['Left to be build'], errors='coerce').fillna(0)
        
        # Calculate the totals
        total_design = int(design_col.sum())
        total_build = int(build_col.sum())
        total_left = int(left_col.sum())

        # Display metrics in columns for a clean layout
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Design", f"{total_design:,}")
        col2.metric("Total Completed (Build)", f"{total_build:,}")
        col3.metric("Left to Build", f"{total_left:,}")

    except KeyError as e:
        st.error(f"A required column is missing from the sheet: {e}. Please check your Google Sheet for 'Design', 'Build', and 'Left to be build' columns.")
    except Exception as e:
        st.error(f"An error occurred during metric calculation: {e}")


    # --- Display Data Table ---
    st.header("Project Data Table")
    
    # Display the entire DataFrame as an interactive table in the app.
    st.dataframe(dataframe)
else:
    st.warning("Could not display data. Please check the sheet's sharing settings and the URL.")

