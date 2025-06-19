import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

st.set_page_config(layout="wide", page_title="Coffee Shop Sales Analysis")

st.markdown("""
    <style>
        body {
            font-family: 'Inter', sans-serif;
            background-color: #0F172A;
            color: #F1F5F9;
        }
        .stApp {
            background-color: #1E293B;
        }
        .main-content {
            background-color: #334155;
            padding: 20px;
            border-radius: 12px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
            margin: 10px;
        }
        .metric-container {
            background-color: #475569;
            border: 2px solid #64748B;
            border-radius: 8px;
            padding: 15px;
            margin: 5px;
        }
        .plot-container {
            background-color: #334155;
            border: 2px solid #64748B;
            border-radius: 8px;
            padding: 10px;
            margin: 10px 0;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
        }
        h1 {
            color: #F1F5F9;
            text-align: center;
            font-weight: bold;
        }
        h2, h3 {
            color: #E2E8F0;
            font-weight: bold;
        }
        .sidebar .sidebar-content {
            background-color: #475569;
            border: 2px solid #64748B;
            border-radius: 8px;
        }
    </style>
""", unsafe_allow_html=True)

st.title("☕ Coffee Shop Sales Dashboard 📊")

# --- Data Loading with file uploader ---
@st.cache_data
def load_data(uploaded_file):
    try:
        if uploaded_file.name.endswith('.xlsx'):
            # For Excel files, try to load "Transactions" sheet first
            excel_file = pd.ExcelFile(uploaded_file)
            st.info(f"Available sheets: {excel_file.sheet_names}")
            
            # Check if "Transactions" sheet exists
            if "Transactions" in excel_file.sheet_names:
                data = pd.read_excel(uploaded_file, sheet_name="Transactions")
                st.success("Data loaded successfully from Transactions sheet!")
            else:
                # Load the first sheet if Transactions doesn't exist
                data = pd.read_excel(uploaded_file, sheet_name=excel_file.sheet_names[0])
                st.success(f"Data loaded successfully from {excel_file.sheet_names[0]} sheet!")
        
        elif uploaded_file.name.endswith('.csv'):
            data = pd.read_csv(uploaded_file)
            st.success("CSV data loaded successfully!")
        
        else:
            st.error("Please upload an Excel (.xlsx) or CSV (.csv) file")
            return pd.DataFrame()
        
        st.info(f"Data shape: {data.shape}")
        st.info(f"Column names: {list(data.columns)}")
        
        return data
    except Exception as e:
        st.error(f"Error loading file: {e}")
        return pd.DataFrame()

# File uploader
uploaded_file = st.file_uploader(
    "Upload your Coffee Shop Sales data",
    type=['xlsx', 'csv'],
    help="Upload an Excel file (.xlsx) or CSV file (.csv) containing coffee shop sales data"
)

# Load data if file is uploaded
if uploaded_file is not None:
    data = load_data(uploaded_file)
else:
    st.info("👆 Please upload a data file to get started")
    data = pd.DataFrame()

# Only proceed if data was loaded successfully and is not empty
if not data.empty:
    # Display first few rows to understand the data structure
    with st.expander("📊 Data Preview", expanded=False):
        st.write(data.head())
    
    # --- Data Preprocessing with better error handling ---
    try:
        # Find relevant columns
        date_cols = [col for col in data.columns if 'date' in col.lower()]
        time_cols = [col for col in data.columns if 'time' in col.lower()]
        location_cols = [col for col in data.columns if 'location' in col.lower() or 'store' in col.lower()]
        category_cols = [col for col in data.columns if 'category' in col.lower() or 'product' in col.lower()]
        amount_cols = [col for col in data.columns if 'bill' in col.lower() or 'total' in col.lower() or 'amount' in col.lower() or 'price' in col.lower()]
        
        with st.expander("🔍 Column Detection", expanded=False):
            st.write("Detected columns:")
            st.write(f"📅 Date columns: {date_cols}")
            st.write(f"⏰ Time columns: {time_cols}")
            st.write(f"📍 Location columns: {location_cols}")
            st.write(f"🏷️ Category columns: {category_cols}")
            st.write(f"💰 Amount columns: {amount_cols}")
        
        # Use detected columns or fallback to defaults
        date_col = date_cols[0] if date_cols else data.columns[0]
        time_col = time_cols[0] if time_cols else (data.columns[1] if len(data.columns) > 1 else data.columns[0])
        location_col = location_cols[0] if location_cols else (data.columns[2] if len(data.columns) > 2 else data.columns[0])
        category_col = category_cols[0] if category_cols else (data.columns[3] if len(data.columns) > 3 else data.columns[0])
        bill_col = amount_cols[0] if amount_cols else data.columns[-1]
        
        st.success(f"✅ Using columns - Date: **{date_col}**, Time: **{time_col}**, Location: **{location_col}**, Category: **{category_col}**, Amount: **{bill_col}**")
        
        # Convert date column
        if date_col in data.columns:
            data['transaction_date'] = pd.to_datetime(data[date_col], dayfirst=True, errors='coerce')
            data['weekday'] = data['transaction_date'].dt.day_name()
        else:
            st.error(f"Date column '{date_col}' not found in data")
            st.stop()
        
        # Extract hour from time column
        if time_col in data.columns:
            data['Hour'] = data[time_col].apply(lambda x: int(str(x).split(':')[0]) if pd.notna(x) and ':' in str(x) else 12)
        else:
            st.warning(f"Time column '{time_col}' not found, using default hour 12")
            data['Hour'] = 12
        
        # Correcting anomaly if the amount column exists
        if bill_col in data.columns:
            data.loc[data[bill_col] == 360, bill_col] = 36
        
        # Create Day Name and Month Name
        data['Day Name'] = data['weekday']
        data['Month Name'] = data['transaction_date'].dt.month_name()

        weekly_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        data["Day Name"] = pd.Categorical(data["Day Name"], categories=weekly_order, ordered=True)

        month_order = ["January", "February", "March", "April", "May", "June"]
        data["Month Name"] = pd.Categorical(data["Month Name"], categories=month_order, ordered=True)

    except Exception as e:
        st.error(f"Error in data preprocessing: {e}")
        with st.expander("🐛 Debug Information", expanded=True):
            st.write("Data types:")
            st.write(data.dtypes)
            st.write("Sample of data:")
            st.write(data.head())
        st.stop()

    # --- Streamlit Widgets for Filters ---
    st.sidebar.header("🎛️ Dashboard Filters")
    
    selected_location = st.sidebar.selectbox(
        "📍 Filter by Store Location:",
        options=['All Locations'] + sorted(data[location_col].unique().tolist())
    )
    selected_hour = st.sidebar.slider(
        "⏰ Filter by Hour of the Day:",
        min_value=int(data['Hour'].min()),
        max_value=int(data['Hour'].max()),
        value=12,
        step=1
    )
    selected_category = st.sidebar.selectbox(
        "🏷️ Filter by Product Category:",
        options=['All Categories'] + sorted(data[category_col].unique().tolist())
    )

    # --- Filtering Logic based on Streamlit Widgets ---
    # Filter for Daily Revenue Plot
    filtered_daily_data = data.copy()
    if selected_location != "All Locations":
        filtered_daily_data = filtered_daily_data[filtered_daily_data[location_col] == selected_location]
    filtered_daily_data = filtered_daily_data[filtered_daily_data['Hour'] == selected_hour]

    # Group by date and sum bill for the line plot
    daily_sums = filtered_daily_data.groupby('transaction_date')[bill_col].sum().reset_index()

    # Filter for Bar Charts
    filtered_bar_data = data.copy()
    if selected_location != "All Locations":
        filtered_bar_data = filtered_bar_data[filtered_bar_data[location_col] == selected_location]
    if selected_category != "All Categories":
        filtered_bar_data = filtered_bar_data[filtered_bar_data[category_col] == selected_category]

    # Group for Location Plot
    current_location_sales = filtered_bar_data.groupby(location_col)[bill_col].sum().reset_index().sort_values(by=bill_col, ascending=False)

    # Group for Category Plot
    current_category_sales = filtered_bar_data.groupby(category_col)[bill_col].sum().reset_index().sort_values(by=bill_col, ascending=False)

    # --- Create Plotly Charts ---
    # Plot 1: Daily Revenue Trend
    fig1 = go.Figure()
    
    if not daily_sums.empty:
        fig1.add_trace(go.Scatter(
            x=daily_sums['transaction_date'],
            y=daily_sums[bill_col],
            mode='lines+markers',
            line=dict(color='#1E40AF', width=4),
            marker=dict(color='#1E40AF', size=8),
            name='Daily Revenue'
        ))
    
    fig1.update_layout(
        title=f"📈 Daily Revenue Trend (Hour: {selected_hour})",
        xaxis_title="Date",
        yaxis_title="Total Revenue ($)",
        height=400,
        plot_bgcolor='#334155',
        paper_bgcolor='#334155',
        font=dict(color='#F1F5F9', size=12),
        title_font=dict(size=18, color='#F1F5F9'),
        xaxis=dict(gridcolor='#64748B'),
        yaxis=dict(gridcolor='#64748B', tickformat='$,.0f')
    )

    # Plot 2: Sales by Store Location
    fig2 = go.Figure()
    
    if not current_location_sales.empty:
        fig2.add_trace(go.Bar(
            x=current_location_sales[location_col],
            y=current_location_sales[bill_col],
            marker_color='#059669',
            marker_line=dict(color='white', width=2),
            name='Location Sales'
        ))
    
    fig2.update_layout(
        title="🏪 Total Sales by Store Location",
        xaxis_title="Store Location",
        yaxis_title="Total Revenue ($)",
        height=350,
        plot_bgcolor='#334155',
        paper_bgcolor='#334155',
        font=dict(color='#F1F5F9', size=12),
        title_font=dict(size=16, color='#F1F5F9'),
        xaxis=dict(tickangle=45),
        yaxis=dict(gridcolor='#64748B', tickformat='$,.0f')
    )

    # Plot 3: Sales by Product Category
    fig3 = go.Figure()
    
    if not current_category_sales.empty:
        colors = ["#1E40AF", "#DC2626", "#059669", "#D97706", "#7C3AED", "#BE185D", "#0891B2", "#65A30D"]
        fig3.add_trace(go.Bar(
            x=current_category_sales[category_col],
            y=current_category_sales[bill_col],
            marker_color=colors[:len(current_category_sales)],
            marker_line=dict(color='white', width=2),
            name='Category Sales'
        ))
    
    fig3.update_layout(
        title="📦 Total Sales by Product Category",
        xaxis_title="Product Category",
        yaxis_title="Total Revenue ($)",
        height=350,
        plot_bgcolor='#334155',
        paper_bgcolor='#334155',
        font=dict(color='#F1F5F9', size=12),
        title_font=dict(size=16, color='#F1F5F9'),
        xaxis=dict(tickangle=45),
        yaxis=dict(gridcolor='#64748B', tickformat='$,.0f')
    )

    # --- Display Plots in Streamlit ---
    st.markdown('<div class="plot-container">', unsafe_allow_html=True)
    st.plotly_chart(fig1, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Create two columns for the bar charts
    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<div class="plot-container">', unsafe_allow_html=True)
        st.plotly_chart(fig2, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    with col2:
        st.markdown('<div class="plot-container">', unsafe_allow_html=True)
        st.plotly_chart(fig3, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # --- Display Summary Statistics ---
    st.markdown("---")
    st.subheader("📊 Summary Statistics")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown('<div class="metric-container">', unsafe_allow_html=True)
        st.metric("Total Revenue", f"${data[bill_col].sum():,.2f}")
        st.markdown('</div>', unsafe_allow_html=True)
    with col2:
        st.markdown('<div class="metric-container">', unsafe_allow_html=True)
        st.metric("Total Transactions", len(data))
        st.markdown('</div>', unsafe_allow_html=True)
    with col3:
        st.markdown('<div class="metric-container">', unsafe_allow_html=True)
        st.metric("Average Transaction", f"${data[bill_col].mean():.2f}")
        st.markdown('</div>', unsafe_allow_html=True)
    with col4:
        st.markdown('<div class="metric-container">', unsafe_allow_html=True)
        st.metric("Date Range", f"{data['transaction_date'].min().date()} to {data['transaction_date'].max().date()}")
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("---")
    st.subheader("📋 Explore Data Details")
    st.dataframe(data, use_container_width=True)

elif uploaded_file is not None:
    st.error("❌ No data available to display. Please check your uploaded file.")
    st.markdown("---")
    st.subheader("Summary Statistics")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Revenue", f"${data[bill_col].sum():,.2f}")
    with col2:
        st.metric("Total Transactions", len(data))
    with col3:
        st.metric("Average Transaction", f"${data[bill_col].mean():.2f}")
    with col4:
        st.metric("Date Range", f"{data['transaction_date'].min().date()} to {data['transaction_date'].max().date()}")

    st.markdown("---")
    st.subheader("📋 Explore Data Details")
    st.dataframe(data, use_container_width=True)

elif uploaded_file is not None:
    st.error("❌ No data available to display. Please check your uploaded file.")
