import streamlit as st
import pandas as pd
import altair as alt

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
    and returns the data as a Pandas DataFrame with cleaned column names.
    """
    try:
        # The URL is modified to point to a CSV export of the sheet.
        csv_url = sheet_url.replace("/edit?usp=sharing", "/export?format=csv")
        df = pd.read_csv(csv_url)
        # Clean column names by stripping leading/trailing whitespace
        df.columns = df.columns.str.strip()
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
    # --- KPI Graphs ---
    st.header("KPI: Completion Percentage by Type")
    try:
        # Create a copy to avoid modifying the cached dataframe
        df_kpi = dataframe.copy()
        
        # Ensure required columns exist for the calculation
        required_cols = ['Type', 'Design', 'As Built']
        for col in required_cols:
            if col not in df_kpi.columns:
                raise KeyError(f"Required column '{col}' not found for KPI calculation.")
        
        # --- Data Cleaning for Robust Grouping ---
        # Clean the 'Type' column to handle inconsistencies like whitespace or capitalization.
        df_kpi['Type'] = df_kpi['Type'].astype(str).str.strip().str.title()
        
        # Convert columns to numeric, filling errors/blanks with 0
        df_kpi['Design'] = pd.to_numeric(df_kpi['Design'], errors='coerce').fillna(0)
        df_kpi['As Built'] = pd.to_numeric(df_kpi['As Built'], errors='coerce').fillna(0)

        # Group by 'Type' and sum the values
        kpi_summary = df_kpi.groupby('Type').agg({
            'Design': 'sum',
            'As Built': 'sum'
        }).reset_index()

        # Calculate completion percentage, handling cases where Design is 0 to avoid division errors
        kpi_summary['Completion %'] = 0
        mask = kpi_summary['Design'] > 0
        kpi_summary.loc[mask, 'Completion %'] = (kpi_summary.loc[mask, 'As Built'] / kpi_summary.loc[mask, 'Design']) * 100
        
        # Ensure percentage does not exceed 100%
        kpi_summary['Completion %'] = kpi_summary['Completion %'].clip(0, 100)
        
        # Create an Altair bar chart for visualization
        chart = alt.Chart(kpi_summary).mark_bar().encode(
            x=alt.X('Type:N', title='Project Type', sort='-y'), # Sort bars from highest to lowest
            y=alt.Y('Completion %:Q', title='Completion Percentage', scale=alt.Scale(domain=[0, 100])),
            color=alt.Color('Type:N', legend=None), # Color each bar by its type
            tooltip=['Type', alt.Tooltip('Completion %', format='.2f'), 'As Built', 'Design']
        ).properties(
            title='Project Completion Percentage'
        )
        
        st.altair_chart(chart, use_container_width=True)

    except KeyError as e:
        st.warning(f"Could not generate KPI graph. {e}")
    except Exception as e:
        st.error(f"An error occurred while creating the KPI graph: {e}")

    # --- Filter out unwanted columns ---
    # Get a list of columns that do not start with 'Unnamed'
    columns_to_show = [col for col in dataframe.columns if not col.startswith('Unnamed')]
    
    # Create a new view of the dataframe with only the desired columns
    display_df = dataframe[columns_to_show]

    # --- Display Data Table ---
    st.header("Project Data Table")
    
    # Display the filtered DataFrame as an interactive table in the app.
    st.dataframe(display_df)
else:
    st.warning("Could not display data. Please check the sheet's sharing settings and the URL.")

