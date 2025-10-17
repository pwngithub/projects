import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime

# --- Page Configuration ---
# Set the page title and a descriptive icon for the browser tab.
st.set_page_config(
    page_title="Project Dashboard",
    page_icon="🚀",
    layout="wide" # Use the full page width for a better view of the data.
)

# --- Logo and App Title ---
# Replace the URL below with the actual URL of your PBB logo
logo_url_main = "https://images.squarespace-cdn.com/content/v1/651eb4433b13e72c1034f375/369c5df0-5363-4827-b041-1add0367f447/PBB+long+logo.png?format=1500w" 
st.image(logo_url_main)

st.title("🚀 Project Performance Dashboard")

# --- Google Sheet Configuration ---
# IMPORTANT: Manually add your sheet names and their GID here.
# To find the GID: Open your Google Sheet, click on the desired sheet tab,
# and look at the URL in your browser. The GID is the number after "#gid=".
SHEET_ID = "109p39EGYEikgbZT4kSW71_sXJNMM-4Tjjd5q-l9Tx_0"
SHEET_GIDS = {
    "RDOF": "0",  # The first sheet is usually gid=0
    "Smyrna": "YOUR_GID_HERE", # Replace with the actual GID for your second sheet
    # Add more sheets as you create them in your Google Sheet
}


# --- Data Loading Function ---
@st.cache_data(ttl=300) # The ttl argument tells Streamlit to expire the cache after 300 seconds (5 minutes)
def load_data(sheet_id, gid):
    """
    Takes a Google Sheet ID and GID, constructs the CSV export URL,
    and returns the data as a raw Pandas DataFrame without headers.
    """
    try:
        # Construct the URL for the specific sheet
        url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"
        # Load the data without assuming a header row to find metadata
        df = pd.read_csv(url, header=None)
        return df
    except Exception as e:
        st.error(f"Failed to load data for the selected sheet. Error: {e}")
        return None

# --- Data Processing Function ---
def process_data(df):
    """Cleans and processes the dataframe for KPI calculations."""
    df_processed = df.copy()
    # Clean column names
    df_processed.columns = df_processed.columns.str.strip()
    required_cols = ['Type', 'Design', 'As Built']
    if not all(col in df_processed.columns for col in required_cols):
        missing = [col for col in required_cols if col not in df_processed.columns]
        st.warning(f"Missing required columns for KPI calculation: {', '.join(missing)}")
        return None

    df_processed.dropna(subset=['Type'], inplace=True)
    df_processed['Type'] = df_processed['Type'].astype(str).str.replace(':', '', regex=False).str.strip().str.title()
    
    # FIX: Filter out any rows that are likely metadata, like "Last Edited"
    df_processed = df_processed[~df_processed['Type'].str.contains("Last Edited", case=False, na=False)]

    for col in ['Design', 'As Built']:
        df_processed[col] = df_processed[col].astype(str).str.replace(',', '', regex=False)
        df_processed[col] = pd.to_numeric(df_processed[col], errors='coerce').fillna(0)
    
    kpi_summary = df_processed.groupby('Type').agg({
        'Design': 'sum',
        'As Built': 'sum'
    }).reset_index()

    kpi_summary['Completion %'] = 0
    mask = kpi_summary['Design'] > 0
    kpi_summary.loc[mask, 'Completion %'] = (kpi_summary.loc[mask, 'As Built'] / kpi_summary.loc[mask, 'Design']) * 100
    kpi_summary['Completion %'] = kpi_summary['Completion %'].clip(0, 100)
    kpi_summary['Left to be Built'] = kpi_summary['Design'] - kpi_summary['As Built']
    
    return kpi_summary

# --- Sidebar Controls ---
st.sidebar.header("Controls & Filters")

# Add a dropdown to select the sheet
selected_sheet_name = st.sidebar.selectbox("Select Project Sheet:", options=list(SHEET_GIDS.keys()))
selected_gid = SHEET_GIDS[selected_sheet_name]

if st.sidebar.button("🔄 Refresh Data"):
    load_data.clear()
    st.rerun()

# --- Main App Logic ---
raw_dataframe = load_data(SHEET_ID, selected_gid)

if raw_dataframe is not None:
    # --- Extract metadata and prepare the main dataframe ---
    try:
        # Get the "last updated" time from cell A7 (index 6, 0)
        last_updated_string = raw_dataframe.iloc[6, 0]
        st.markdown(f"**Sheet Last Updated:** {last_updated_string}")
    except (IndexError, KeyError):
        st.warning("Could not find the 'Last Updated' time in cell A7.")
        
    try:
        # Find the header row by looking for the 'Type' column header in the first column
        header_row_index = raw_dataframe[raw_dataframe[0] == 'Type'].index[0]
        
        # Create a new dataframe for the main data using the found header row
        dataframe = raw_dataframe.copy()
        
        header_series = dataframe.iloc[header_row_index].fillna('Unnamed Column')
        dataframe.columns = header_series
        
        dataframe = dataframe.iloc[header_row_index + 1:].reset_index(drop=True)
        
        dataframe = dataframe.loc[:, ~dataframe.columns.duplicated()]
        
    except (IndexError, KeyError):
        st.error("Could not find the header row in the Google Sheet. Please ensure a column is named 'Type'.")
        dataframe = None # Set dataframe to None so the rest of the app doesn't run
        
    if dataframe is not None:
        kpi_data = process_data(dataframe)
        
        if kpi_data is not None:
            # --- Filter Options specific to the selected sheet ---
            st.sidebar.header("Filter Options")
            all_types = sorted(kpi_data['Type'].unique())
            selected_types = st.sidebar.multiselect(
                "Select Project Type(s):",
                options=all_types,
                default=all_types,
                key=f"multiselect_{selected_gid}" # Unique key to prevent state issues
            )
            
            filtered_kpi_data = kpi_data[kpi_data['Type'].isin(selected_types)]

            # --- High-Level KPIs ---
            st.header(f"📊 Overall Project Health: {selected_sheet_name}")
            total_design = filtered_kpi_data['Design'].sum()
            total_as_built = filtered_kpi_data['As Built'].sum()
            total_left = filtered_kpi_data['Left to be Built'].sum()
            overall_completion = (total_as_built / total_design * 100) if total_design > 0 else 0
            
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Total Design", f"{total_design:,.0f}")
            col2.metric("Total As Built", f"{total_as_built:,.0f}")
            col3.metric("Left to be Built", f"{total_left:,.0f}")
            col4.metric("Overall Completion", f"{overall_completion:.2f}%")
            
            st.divider()

            # --- Tabbed Navigation for Detailed Views ---
            tab1, tab2 = st.tabs(["📊 KPI Overview", "📄 Detailed Breakdown"])

            with tab1:
                st.header("Completion Percentage by Type")
                if not filtered_kpi_data.empty:
                    # --- Completion Percentage Bar Chart ---
                    chart = alt.Chart(filtered_kpi_data).mark_bar(color='#4A90E2').encode(
                        x=alt.X('Completion %:Q', title='Completion Percentage', scale=alt.Scale(domain=[0, 100])),
                        y=alt.Y('Type:N', sort='-x', title='Project Type'),
                        tooltip=['Type', 'Completion %', 'As Built', 'Design']
                    ).properties(
                        title='Completion Percentage by Type'
                    )
                    
                    text = chart.mark_text(
                        align='left',
                        baseline='middle',
                        dx=3  # Nudges text to right so it doesn't overlap bar
                    ).encode(
                        text=alt.Text('Completion %:Q', format='.2f')
                    )

                    st.altair_chart(chart + text, use_container_width=True)
                else:
                    st.info("No data to display for the selected project types.")

            with tab2:
                st.header("Detailed Breakdown by Project Type")
                if not filtered_kpi_data.empty:
                    # Sort the data to match the chart order before displaying the cards
                    sorted_kpi_data = filtered_kpi_data.sort_values(by='Completion %', ascending=False)
                    
                    # Identify the top performer
                    top_performer_type = sorted_kpi_data.iloc[0]['Type']

                    for index, row in sorted_kpi_data.iterrows():
                        with st.container(border=True):
                            # Add a badge for the top performer
                            if row['Type'] == top_performer_type:
                                st.subheader(f'🏆 Top Performer: {row["Type"]}')
                            else:
                                st.subheader(f'{row["Type"]}')

                            st.progress(int(row['Completion %']))
                            
                            kpi_c1, kpi_c2, kpi_c3 = st.columns(3)
                            kpi_c1.metric("Completion %", f"{row['Completion %']:.2f}%")
                            kpi_c2.metric("As Built", f"{row['As Built']:,.2f}")
                            kpi_c3.metric("Design Target", f"{row['Design']:,.2f}")
                else:
                    st.info("No data to display for the selected project types.")

        # --- Raw Data Table ---
        with st.expander("🔍 View Raw Data Table"):
            if dataframe is not None:
                columns_to_show = [col for col in dataframe.columns if col is not None and not str(col).startswith('Unnamed')]
                display_df = dataframe[columns_to_show]
                st.dataframe(display_df.fillna(''))
else:
    st.warning("Could not display data. Please check the sheet's sharing settings and the URL.")

