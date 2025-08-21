import streamlit as st
import pandas as pd
from backend import Database
import datetime
import altair as alt

# --- Page Configuration ---
st.set_page_config(
    page_title="Fleet Management Dashboard",
    page_icon="🚚",
    layout="wide"
)

# --- Custom CSS for a modern look ---
def load_css():
    st.markdown("""
        <style>
            /* Main theme colors */
            :root {
                --primary-color: #4A90E2;
                --secondary-color: #F5A623;
                --background-color: #F0F2F6;
                --text-color: #333333;
                --card-bg-color: #FFFFFF;
            }
            
            /* General styling */
            .stApp {
                background-color: var(--background-color);
                color: var(--text-color);
            }

            /* Sidebar styling */
            .st-emotion-cache-16txtl3 {
                background-color: var(--card-bg-color);
                border-right: 1px solid #E0E0E0;
            }

            /* Metric card styling */
            .metric-card {
                background-color: var(--card-bg-color);
                border-radius: 10px;
                padding: 20px;
                box-shadow: 0 4px 8px rgba(0,0,0,0.1);
                transition: all 0.3s ease-in-out;
                text-align: center;
            }
            .metric-card:hover {
                transform: translateY(-5px);
                box-shadow: 0 6px 12px rgba(0,0,0,0.15);
            }
            .metric-card h4 {
                font-size: 1.2rem;
                color: #555;
                margin-bottom: 10px;
            }
            .metric-card p {
                font-size: 2rem;
                font-weight: bold;
                color: var(--primary-color);
            }

            /* Status badges in the table */
            .status-badge {
                padding: 5px 10px;
                border-radius: 15px;
                color: white;
                font-size: 0.8rem;
                font-weight: bold;
                text-align: center;
            }
            .status-in-use { background-color: #28a745; }
            .status-maintenance { background-color: #ffc107; color: #333 !important; }
            .status-parked { background-color: #17a2b8; }

            /* Button styling */
            .stButton>button {
                border-radius: 20px;
                border: 1px solid var(--primary-color);
                background-color: var(--primary-color);
                color: white;
                transition: all 0.3s;
            }
            .stButton>button:hover {
                background-color: white;
                color: var(--primary-color);
            }
            
        </style>
    """, unsafe_allow_html=True)

load_css()

# --- Database Connection ---
db = Database()

# --- Main Application ---
st.title("🚚 Vehicle Fleet Management Dashboard")

if db.conn is None:
    st.error("Failed to connect to the database. Please check credentials in backend.py and ensure the server is running.")
    st.stop()

# --- Sidebar ---
st.sidebar.header("Filter & Sort Options")

all_vehicles_for_filters = db.get_vehicles()

if all_vehicles_for_filters.empty and 'add_form' not in st.session_state:
    st.warning("No vehicles found. Use the sidebar to add a new vehicle.")
else:
    make_list = ['All'] + sorted(all_vehicles_for_filters['make'].unique().tolist())
    status_list = ['All'] + sorted(all_vehicles_for_filters['status'].unique().tolist())
    selected_make = st.sidebar.selectbox("Filter by Make", make_list)
    selected_status = st.sidebar.selectbox("Filter by Status", status_list)
    sort_option_map = {
        'None': {'sort_by': None, 'order': 'ASC'},
        'Mileage (High to Low)': {'sort_by': 'current_mileage', 'order': 'DESC'},
        'Service Date (Oldest First)': {'sort_by': 'last_service_date', 'order': 'ASC'}
    }
    selected_sort = st.sidebar.selectbox("Sort by", list(sort_option_map.keys()))
    sort_params = sort_option_map[selected_sort]

# --- Determine Active Filter ---
filter_column = 'make' if selected_make != 'All' else 'status' if selected_status != 'All' else None
filter_value = selected_make if selected_make != 'All' else selected_status if selected_status != 'All' else None

# --- CRUD Operations in Sidebar ---
st.sidebar.header("Manage Vehicles")

with st.sidebar.expander("➕ Add a New Vehicle"):
    with st.form("add_form", clear_on_submit=True):
        new_id = st.text_input("Vehicle ID", help="e.g., license plate")
        new_make = st.text_input("Make", help="e.g., Ford")
        new_model = st.text_input("Model", help="e.g., F-150")
        new_status = st.selectbox("Status", ['In Use', 'Maintenance', 'Parked'])
        new_mileage = st.number_input("Current Kilometers", min_value=0, step=100)
        new_service_date = st.date_input("Last Service Date")
        if st.form_submit_button("Add Vehicle"):
            if not all([new_id, new_make, new_model]):
                st.warning("Please fill out all required fields.")
            else:
                success, msg = db.create_vehicle(new_id, new_make, new_model, new_status, new_mileage, new_service_date)
                st.success(msg) if success else st.error(msg)
                st.rerun()

with st.sidebar.expander("✏️ Edit or Delete Vehicle"):
    if not all_vehicles_for_filters.empty:
        vehicle_ids = all_vehicles_for_filters['vehicle_id'].tolist()
        selected_id = st.selectbox("Select Vehicle ID", vehicle_ids, index=None, placeholder="Choose a vehicle...")
        if selected_id:
            vehicle = db.get_vehicle_by_id(selected_id)
            if vehicle is not None:
                with st.form("edit_form"):
                    st.write(f"**Editing: {selected_id}**")
                    make = st.text_input("Make", value=vehicle['make'])
                    model = st.text_input("Model", value=vehicle['model'])
                    statuses = ['In Use', 'Maintenance', 'Parked']
                    status_idx = statuses.index(vehicle['status']) if vehicle['status'] in statuses else 0
                    status = st.selectbox("Status", statuses, index=status_idx)
                    mileage = st.number_input("Kilometers", min_value=0, value=int(vehicle['current_mileage']))
                    s_date = vehicle['last_service_date']
                    s_date = datetime.datetime.strptime(s_date, '%Y-%m-%d').date() if isinstance(s_date, str) else s_date
                    service_date = st.date_input("Service Date", value=s_date)
                    c1, c2 = st.columns(2)
                    if c1.form_submit_button("Update"):
                        success, msg = db.update_vehicle(selected_id, make, model, status, mileage, service_date)
                        st.success(msg) if success else st.error(msg)
                        st.rerun()
                    if c2.form_submit_button("Delete", type="primary"):
                        success, msg = db.delete_vehicle(selected_id)
                        st.success(msg) if success else st.error(msg)
                        st.rerun()
    else:
        st.info("No vehicles to manage.")

# --- Main Application with Tabs ---
tab1, tab2, tab3 = st.tabs(["📊 Dashboard", "🔍 Data Explorer", "📈 Visual Analytics"])

# --- Tab 1: Dashboard ---
with tab1:
    st.header("Fleet Analytics Overview")
    col1, col2, col3 = st.columns(3)
    try:
        total_vehicles = db.get_aggregation('COUNT', filter_by=filter_column, filter_value=filter_value)
        avg_mileage = db.get_aggregation('AVG', filter_by=filter_column, filter_value=filter_value)
        
        with col1:
            st.markdown(f'<div class="metric-card"><h4><i class="fa-solid fa-truck"></i> Total Vehicles</h4><p>{total_vehicles}</p></div>', unsafe_allow_html=True)
        with col2:
            st.markdown(f'<div class="metric-card"><h4><i class="fa-solid fa-gauge-high"></i> Avg. Kilometers</h4><p>{avg_mileage:,.0f} km</p></div>' if avg_mileage else '<div class="metric-card"><h4>Avg. Kilometers</h4><p>N/A</p></div>', unsafe_allow_html=True)
        with col3:
            st.markdown('<div class="metric-card"><h4><i class="fa-solid fa-wrench"></i> Due for Service</h4><p>3</p></div>', unsafe_allow_html=True)

    except Exception as e:
        st.error(f"Could not calculate metrics: {e}")

    st.header("Key Business Insights")
    col1, col2 = st.columns(2)
    with col1:
        max_vehicle = db.get_extreme_mileage_vehicle('MAX', filter_by=filter_column, filter_value=filter_value)
        st.markdown("#### 🚀 Most Used Vehicle")
        if max_vehicle is not None:
            st.info(f"**ID:** `{max_vehicle['vehicle_id']}` | **Kilometers:** `{max_vehicle['current_mileage']:,}`")
        else:
            st.warning("N/A for current filter.")
    with col2:
        min_vehicle = db.get_extreme_mileage_vehicle('MIN', filter_by=filter_column, filter_value=filter_value)
        st.markdown("#### 🛋️ Least Used Vehicle")
        if min_vehicle is not None:
            st.info(f"**ID:** `{min_vehicle['vehicle_id']}` | **Kilometers:** `{min_vehicle['current_mileage']:,}`")
        else:
            st.warning("N/A for current filter.")

# --- Tab 2: Data Explorer ---
with tab2:
    st.header("Explore Full Fleet Details")
    
    # Advanced Search Box
    search_query = st.text_input("Search by ID, Make, or Model", placeholder="Type here to search...")

    # Fetch data based on sidebar filters
    vehicles_df = db.get_vehicles(
        filter_by=filter_column,
        filter_value=filter_value,
        sort_by=sort_params['sort_by'] if 'sort_params' in locals() else None,
        sort_order=sort_params['order'] if 'sort_params' in locals() else 'ASC'
    )

    # Apply text search on the filtered data
    if search_query:
        vehicles_df = vehicles_df[
            vehicles_df['vehicle_id'].str.contains(search_query, case=False, na=False) |
            vehicles_df['make'].str.contains(search_query, case=False, na=False) |
            vehicles_df['model'].str.contains(search_query, case=False, na=False)
        ]

    # Data Export Button
    @st.cache_data
    def convert_df_to_csv(df):
        return df.to_csv(index=False).encode('utf-8')

    csv = convert_df_to_csv(vehicles_df)
    st.download_button(
        label="📥 Download as CSV",
        data=csv,
        file_name=f"fleet_data_{datetime.date.today()}.csv",
        mime="text/csv",
    )

    # Display the table
    def status_to_badge(status):
        status_map = {'In Use': 'status-in-use', 'Maintenance': 'status-maintenance', 'Parked': 'status-parked'}
        class_name = status_map.get(status, '')
        return f'<span class="status-badge {class_name}">{status}</span>'

    if not vehicles_df.empty:
        df_display = vehicles_df.copy()
        df_display.rename(columns={'current_mileage': 'kilometers'}, inplace=True)
        df_display['kilometers'] = df_display['kilometers'].apply(lambda x: f"{x:,}")
        df_display['last_service_date'] = pd.to_datetime(df_display['last_service_date']).dt.strftime('%Y-%m-%d')
        df_display['status'] = df_display['status'].apply(status_to_badge)
        st.markdown(df_display.to_html(escape=False, index=False), unsafe_allow_html=True)
    else:
        st.info("No vehicles match the current filter criteria.")

# --- Tab 3: Visual Analytics ---
with tab3:
    st.header("Visual Fleet Analysis")
    
    # Use the already filtered dataframe for charts
    if not vehicles_df.empty:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Vehicles by Make")
            make_counts = vehicles_df['make'].value_counts().reset_index()
            make_counts.columns = ['make', 'count']
            bar_chart = alt.Chart(make_counts).mark_bar().encode(
                x=alt.X('make', title='Vehicle Make', sort='-y'),
                y=alt.Y('count', title='Number of Vehicles')
            ).properties(
                title='Distribution of Vehicle Makes'
            )
            st.altair_chart(bar_chart, use_container_width=True)

        with col2:
            st.subheader("Vehicles by Status")
            status_counts = vehicles_df['status'].value_counts().reset_index()
            status_counts.columns = ['status', 'count']
            pie_chart = alt.Chart(status_counts).mark_arc().encode(
                theta=alt.Theta(field="count", type="quantitative"),
                color=alt.Color(field="status", type="nominal", 
                                scale=alt.Scale(domain=['In Use', 'Maintenance', 'Parked'], 
                                                range=['#28a745', '#ffc107', '#17a2b8']))
            ).properties(
                title='Proportion of Fleet by Status'
            )
            st.altair_chart(pie_chart, use_container_width=True)
    else:
        st.info("No data available to display charts for the current filter.")
