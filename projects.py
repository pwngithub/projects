import streamlit as st
import pandas as pd
from datetime import datetime

# --- Page Configuration ---
# Set the page title, icon, and layout. Wide layout gives more space for content.
st.set_page_config(
    page_title="PBB Project Dashboard",
    page_icon="🚀",
    layout="wide"
)

# --- Custom Styling (CSS Injection) ---
# This injects CSS to customize the app's appearance for a more professional and readable look.
st.markdown("""
<style>
    /* Main app background color - changed to clean white */
    .stApp {
        background-color: #FFFFFF;
    }
    /* Sidebar styling - kept dark for contrast */
    [data-testid="stSidebar"] {
        background-color: #1a202c; 
    }
    /* Style for metric labels - darker for better contrast */
    .stMetric .st-ax {
        color: #262730;
    }
    /* Style for metric values */
    [data-testid="stMetricValue"] {
        color: #1a202c;
    }
    /* Custom horizontal rule */
    hr {
        margin-top: 1rem;
        margin-bottom: 1rem;
        border-top: 1px solid #E2E8F0;
    }
    /* Styling for the KPI containers to make them look like cards */
    .st-emotion-cache-z5fcl4 {
        border: 1px solid #E2E8F0;
        border-radius: 0.5rem;
        padding: 1rem;
        box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1);
    }
</style>
""", unsafe_allow_html=True)


# --- Logo and App Title ---
logo_url_main = "https://images.squarespace-cdn.com/content/v1/651eb4433b13e72c1034f375/369c5df0-5363-4827-b041-1add0367f447/PBB+long+logo.png?format=1500w" 
st.image(logo_url_main)

st.title("🚀 Project Performance Dashboard")
st.markdown("An interactive dashboard to monitor project progress from a live Google Sheet.")

# --- Data Loading Function ---
@st.cache_data(ttl=300) # The ttl argument tells Streamlit to expire the cache after 300 seconds (5 minutes)
def load_data(sheet_url):
    """
    Takes a Google Sheet URL, converts it to a CSV export URL,
    and returns the data as a Pandas DataFrame with cleaned column names.
    """
    try:
        csv_url = sheet_url.replace("/edit?usp=sharing", "/export?format=csv")
        df = pd.read_csv(csv_url)
        df.columns = df.columns.str.strip()
        return df, datetime.now() # Return the dataframe and the time it was loaded
    except Exception as e:
        st.error(f"Failed to load data. Please ensure the Google Sheet is public. Error: {e}")
        return None, None

# The public URL of your Google Sheet.
GOOGLE_SHEET_URL = "https://docs.google.com/spreadsheets/d/109p39EGYEikgbZT4kSW71_sXJNMM-4Tjjd5q-l9Tx_0/edit?usp=sharing"

# --- Data Processing Function ---
def process_data(df):
    """Cleans and processes the dataframe for KPI calculations."""
    df_processed = df.copy()
    required_cols = ['Type', 'Design', 'As Built']
    if not all(col in df_processed.columns for col in required_cols):
        missing = [col for col in required_cols if col not in df_processed.columns]
        st.warning(f"Missing required columns for KPI calculation: {', '.join(missing)}")
        return None

    df_processed.dropna(subset=['Type'], inplace=True)
    df_processed['Type'] = df_processed['Type'].astype(str).str.replace(':', '', regex=False).str.strip().str.title()
    
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
    
    return kpi_summary

# --- Main App Logic ---
dataframe, load_time = load_data(GOOGLE_SHEET_URL)

if dataframe is not None:
    kpi_data = process_data(dataframe)
    
    if kpi_data is not None:
        # --- Sidebar ---
        st.sidebar.header("Controls & Filters")
        
        # Add a manual refresh button and last refreshed time
        if st.sidebar.button("🔄 Refresh Data"):
            load_data.clear() # Clear the cached data
            st.rerun() # Rerun the app from the top
        
        if load_time:
            st.sidebar.info(f"Data last refreshed at:\n{load_time.strftime('%I:%M:%S %p')}")

        st.sidebar.header("Filter Options")
        all_types = kpi_data['Type'].unique()
        selected_types = st.sidebar.multelect(
            "Select Project Type(s):",
            options=all_types,
            default=all_types
        )
        
        filtered_kpi_data = kpi_data[kpi_data['Type'].isin(selected_types)]

        # --- High-Level KPIs ---
        st.header("📊 Overall Project Health")
        with st.container():
            total_design = filtered_kpi_data['Design'].sum()
            total_as_built = filtered_kpi_data['As Built'].sum()
            overall_completion = (total_as_built / total_design * 100) if total_design > 0 else 0
            
            col1, col2, col3 = st.columns(3)
            col1.metric("Total Design Scope", f"{total_design:,.0f}")
            col2.metric("Total As Built", f"{total_as_built:,.0f}")
            col3.metric("Overall Completion", f"{overall_completion:.2f}%")

        # --- Detailed KPI Section ---
        st.header("🏗️ Completion by Project Type")
        if not filtered_kpi_data.empty:
            for index, row in filtered_kpi_data.iterrows():
                # Using a container for each type to group elements neatly
                with st.container():
                    st.subheader(f"{row['Type']}")
                    
                    # Custom progress bar with text label inside
                    progress_text = f"{row['Completion %']:.2f}% Complete"
                    st.progress(int(row['Completion %']), text=progress_text)
                    
                    # Metrics displayed in columns for a compact view
                    kpi_col1, kpi_col2, kpi_col3 = st.columns(3)
                    kpi_col1.metric("Completion", f"{row['Completion %']:.2f}%")
                    kpi_col2.metric("As Built", f"{row['As Built']:,.2f}")
                    kpi_col3.metric("Design Target", f"{row['Design']:,.2f}")
        else:
            st.info("No data to display for the selected project types.")

    # --- Raw Data Table ---
    with st.expander("🔍 View Raw Data Table"):
        columns_to_show = [col for col in dataframe.columns if not col.startswith('Unnamed')]
        display_df = dataframe[columns_to_show]
        st.dataframe(display_df)
else:
    st.warning("Could not display data. Please check the sheet's sharing settings and the URL.")

