import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="BAGUIO SIA Accomplishment",
    layout="wide"
)

st.title("BAGUIO SIA Accomplishment Dashboard")

# --- DATA LOADING ---
SHEET_ID = "1Gh1LYOgacvRs_QwNa7xFHAGyfTzquQ0exqe3VOOYANs"

# CSV Export URLs
CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"
TARGET_CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Target"
DATA_AS_OF_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=dataAsOf"

@st.cache_data(ttl=600)
def load_data():
    try:
        df = pd.read_csv(CSV_URL)
        df.columns = df.columns.astype(str).str.strip()
        
        # Convert Column I (Vaccination Date - 0-indexed column 8) to datetime
        if len(df.columns) > 8:
            date_col = df.columns[8] 
            df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
        
        return df
    except Exception as e:
        st.error(f"Error loading main data from Google Sheets: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=600)
def load_target_data():
    try:
        df_target = pd.read_csv(TARGET_CSV_URL)
        df_target.columns = df_target.columns.astype(str).str.strip()
        return df_target
    except Exception as e:
        try:
            alt_url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&sheet=Target"
            df_target = pd.read_csv(alt_url)
            df_target.columns = df_target.columns.astype(str).str.strip()
            return df_target
        except Exception as alt_e:
            st.warning(f"Note: Could not load 'Target' sheet. Details: {alt_e}")
            return pd.DataFrame()

@st.cache_data(ttl=600)
def load_data_as_of():
    try:
        df_as_of = pd.read_csv(DATA_AS_OF_URL, header=None)
        extract_date = str(df_as_of.iloc[1, 0]).strip() if len(df_as_of) > 1 and len(df_as_of.columns) > 0 else ""
        extract_time = str(df_as_of.iloc[1, 1]).strip() if len(df_as_of) > 1 and len(df_as_of.columns) > 1 else ""
        return extract_date, extract_time
    except Exception:
        try:
            alt_url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&sheet=dataAsOf"
            df_as_of = pd.read_csv(alt_url, header=None)
            extract_date = str(df_as_of.iloc[1, 0]).strip() if len(df_as_of) > 1 and len(df_as_of.columns) > 0 else ""
            extract_time = str(df_as_of.iloc[1, 1]).strip() if len(df_as_of) > 1 and len(df_as_of.columns) > 1 else ""
            return extract_date, extract_time
        except Exception:
            return "", ""

# --- HELPER FUNCTION FOR CSV CONVERSION ---
@st.cache_data
def convert_df_to_csv(df):
    return df.to_csv(index=False).encode('utf-8')

# Safe numeric cleanup (handles formatted strings with commas and empty dataframes)
def clean_numeric_sum(series):
    if series is None or series.empty:
        return 0
    cleaned = series.astype(str).str.replace(",", "").str.strip()
    return pd.to_numeric(cleaned, errors='coerce').fillna(0).sum()

df_raw = load_data()
df_target_raw = load_target_data()
as_of_date, as_of_time = load_data_as_of()

# --- DEBUG EXPANDER ---
with st.expander("🔍 Debug: Inspect Target Sheet Columns & Data"):
    if not df_target_raw.empty:
        st.write("Target Sheet Columns:", df_target_raw.columns.tolist())
        st.dataframe(df_target_raw.head())
    else:
        st.write("Target Sheet is empty or not loaded.")

# --- DATA AS OF REMINDER BANNER ---
timestamp_str = f"{as_of_date} {as_of_time}".strip()
if timestamp_str and timestamp_str != "nan nan":
    st.info(f"📌 **Data as of:** {timestamp_str} | *All data is subject to change without prior notice.*")
else:
    st.info("📌 *All data is subject to change without prior notice.*")

if not df_raw.empty:
    # Identify key columns by position in main sheet
    col_city = df_raw.columns[4]       # Column E (City/Municipality)
    col_bakuna = df_raw.columns[5]     # Column F (Bakuna Center Name)
    col_barangay = df_raw.columns[7]   # Column H (Barangay Name)
    col_date = df_raw.columns[8]       # Column I (Vaccination Date)
    col_response = df_raw.columns[9]   # Column J (Response Type)

    # Specific Columns for MR (Columns K, L, M)
    col_mr_6_12 = df_raw.columns[10]   # Column K (MR 6-12 mos Total)
    col_mr_13_23 = df_raw.columns[11]  # Column L (MR 13-23 mos Total)
    col_mr_24_59 = df_raw.columns[12]  # Column M (MR 24-59 mos Total)

    # Specific Columns for Vit A (Columns Q, R)
    col_vit_6_11 = df_raw.columns[16]   # Column Q (Vit A 6-11 mos Total)
    col_vit_12_59 = df_raw.columns[17]  # Column R (Vit A 12-59 mos Total)

    # List of dose metrics columns (Column K onwards)
    dose_cols = df_raw.columns[10:].tolist()

    # =========================================================
    # --- SIDEBAR LOGO BANNER (4 Columns, 100px Wide) ---
    # =========================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

with st.sidebar:
    col1, col2, col3, col4 = st.columns(4)

    images = [
        (col1, "doh_seal.png"),
        (col2, "doh_car_seal.png"),
        (col3, "baguio_seal.png"),
        (col4, "bagong_pilipinas.png")
    ]

    for col, filename in images:
        img_path = os.path.join(BASE_DIR, filename)
        with col:
            if os.path.exists(img_path):
                st.image(img_path, use_container_width=True)

    # --- SIDEBAR QUICK NAVIGATION LINKS ---
    st.sidebar.header("🧭 Quick Navigation")
    st.sidebar.markdown("""
    - 📊 [Accomplishment Summary](#accomplishment-summary)
    - 📈 [Daily Response Trends](#daily-response-trends)
    - 🔢 [Overall Metric Summary](#overall-metric-summary)
    - 🎯 [Target Population vs Gauges](#target-population-vs-accomplishment-gauges)
    - 🏥 [DHC Accomplishment Data Summary](#dhc-accomplishment-data-summary)
    - 🗺️ [Barangay Table Heatmap](#barangay-accomplishment-table-heatmap)
    - 🥧 [Share by Barangay](#accomplishment-share-by-barangay)
    - ⚠️ [Deferral & Refusal Analysis](#deferral-and-refusal-analysis)
    - 📋 [Barangay Submission Status](#barangay-submission-status)
    """)

    st.sidebar.markdown("---")

    # --- SIDEBAR FILTERS ---
    st.sidebar.header("Filter Options")

    # Filter 1: City/Municipality [Column E]
    cities = sorted(df_raw[col_city].dropna().astype(str).unique().tolist())
    selected_city = st.sidebar.multiselect("City / Municipality", cities)

    # Filter 2: Bakuna Center Name [Column F] (DEPENDENT ON CITY SELECTION)
    if selected_city:
        df_for_bakuna = df_raw[df_raw[col_city].astype(str).isin(selected_city)]
    else:
        df_for_bakuna = df_raw.copy()

    bakuna_centers = sorted(df_for_bakuna[col_bakuna].dropna().astype(str).unique().tolist())
    selected_bakuna = st.sidebar.multiselect("Bakuna Center Name", bakuna_centers)

    # Filter 3: Barangay Name [Column H] (DEPENDENT ON CITY & BAKUNA CENTER SELECTION)
    df_for_barangay = df_for_bakuna.copy()
    if selected_bakuna:
        df_for_barangay = df_for_barangay[df_for_barangay[col_bakuna].astype(str).isin(selected_bakuna)]

    barangays = sorted(df_for_barangay[col_barangay].dropna().astype(str).unique().tolist())
    selected_barangay = st.sidebar.multiselect("Barangay Name", barangays)

    # Filter 4: Vaccination Date Range [Column I] (SAFE FROM NULL/EMPTY ERRS)
    valid_dates = df_raw[col_date].dropna() if col_date in df_raw.columns else pd.Series()
    
    if not valid_dates.empty:
        min_date_val = valid_dates.min()
        max_date_val = valid_dates.max()
        
        if pd.notna(min_date_val) and pd.notna(max_date_val):
            default_start = min_date_val.date()
            default_end = max_date_val.date()
        else:
            default_start = pd.Timestamp.now().date()
            default_end = pd.Timestamp.now().date()
            
        selected_date_range = st.sidebar.date_input(
            "Vaccination Date Range",
            value=(default_start, default_end),
            min_value=default_start,
            max_value=default_end
        )
    else:
        selected_date_range = []

    # --- APPLY FILTERS TO ACCOMPLISHMENT DATA ---
    filtered_df = df_raw.copy()

    if selected_city:
        filtered_df = filtered_df[filtered_df[col_city].astype(str).isin(selected_city)]

    if selected_bakuna:
        filtered_df = filtered_df[filtered_df[col_bakuna].astype(str).isin(selected_bakuna)]

    if selected_barangay:
        filtered_df = filtered_df[filtered_df[col_barangay].astype(str).isin(selected_barangay)]

    # Safe Date Filter Application
    if len(selected_date_range) == 2 and col_date in filtered_df.columns and not filtered_df.empty:
        start_date, end_date = selected_date_range
        if not pd.api.types.is_datetime64_any_dtype(filtered_df[col_date]):
            filtered_df[col_date] = pd.to_datetime(filtered_df[col_date], errors='coerce')
            
        filtered_df = filtered_df[
            filtered_df[col_date].dt.date.notna() & 
            (filtered_df[col_date].dt.date >= start_date) & 
            (filtered_df[col_date].dt.date <= end_date)
        ]

    # --- SIDEBAR RAW DATA DOWNLOAD BUTTON ---
    st.sidebar.markdown("---")
    st.sidebar.header("Data Export")
    raw_csv_data = convert_df_to_csv(filtered_df)
    st.sidebar.download_button(
        label="📥 Download Filtered Raw Data",
        data=raw_csv_data,
        file_name="filtered_raw_accomplishment_data.csv",
        mime="text/csv",
        key="download_filtered_raw"
    )

    # Convert response column safely to string
    response_series = filtered_df[col_response].astype(str) if not filtered_df.empty else pd.Series(dtype=str)

    # --- TARGET COLUMNS SELECTION (Main Sheet) ---
    vit_a_target_cols = [
        c for c in dose_cols 
        if "Vit A" in c and any(age in c for age in ["6-11", "12-59"])
    ]

    mr_dose_cols = [
        c for c in dose_cols 
        if "MR" in c and "Zero" not in c and any(age in c for age in ["6-12", "13-23", "24-59"])
    ]

    mr_zero_cols = [
        c for c in dose_cols 
        if "Zero" in c and any(age in c for age in ["6-12", "13-23", "24-59"])
    ]

    all_mr_cols = mr_dose_cols + mr_zero_cols

    # --- GRAND TOTAL CARDS ---
    st.markdown("### Accomplishment Summary")
    
    col_total_doses = df_raw.columns[18]  # "Grand total doses administered"
    col_zero_doses = df_raw.columns[19]   # "Grand total doses administered (Zero dose)"

    # Base totals
    total_doses = clean_numeric_sum(filtered_df[col_total_doses]) if not filtered_df.empty else 0
    total_zero_doses = clean_numeric_sum(filtered_df[col_zero_doses]) if not filtered_df.empty else 0

    # Response specific filtered dataframes
    vit_a_df = filtered_df[response_series.str.contains("Vitamin A", case=False, na=False)] if not filtered_df.empty else pd.DataFrame()
    mr_df = filtered_df[response_series.str.contains("Measles|MR", case=False, na=False)] if not filtered_df.empty else pd.DataFrame()

    # Calculate Total Vitamin A Response
    vit_a_total = 0
    if vit_a_target_cols and not vit_a_df.empty:
        for c in vit_a_target_cols:
            vit_a_total += clean_numeric_sum(vit_a_df[c])

    # Calculate Total MR Response
    mr_total = 0
    if all_mr_cols and not mr_df.empty:
        for c in all_mr_cols:
            mr_total += clean_numeric_sum(mr_df[c])

    # Render 4 columns for Summary Cards
    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    col_m1.metric("Grand Total Doses", f"{int(total_doses):,}")
    col_m2.metric("Grand Total Zero Doses", f"{int(total_zero_doses):,}")
    col_m3.metric("Vitamin A Total Response", f"{int(vit_a_total):,}")
    col_m4.metric("MR Total Response", f"{int(mr_total):,}")

    st.divider()

    # --- SECTION 1: DAILY RESPONSE TRENDS ---
    st.header("Daily Response Trends")

    daily_vit_a = pd.DataFrame()
    if vit_a_target_cols and not vit_a_df.empty:
        vit_a_df_clean = vit_a_df.dropna(subset=[col_date]).copy()
        if not vit_a_df_clean.empty:
            vit_a_df_clean['Daily_Vit_A_Total'] = vit_a_df_clean[vit_a_target_cols].apply(
                lambda col: pd.to_numeric(col.astype(str).str.replace(",", "").str.strip(), errors='coerce')
            ).sum(axis=1)
            daily_vit_a = vit_a_df_clean.groupby(vit_a_df_clean[col_date].dt.date)['Daily_Vit_A_Total'].sum().reset_index()

    daily_mr = pd.DataFrame()
    if all_mr_cols and not mr_df.empty:
        mr_df_clean = mr_df.dropna(subset=[col_date]).copy()
        if not mr_df_clean.empty:
            mr_df_clean['Daily_MR_Total'] = mr_df_clean[all_mr_cols].apply(
                lambda col: pd.to_numeric(col.astype(str).str.replace(",", "").str.strip(), errors='coerce')
            ).sum(axis=1)
            daily_mr = mr_df_clean.groupby(mr_df_clean[col_date].dt.date)['Daily_MR_Total'].sum().reset_index()

    # --- SAFE MERGE LOGIC ---
    if not daily_vit_a.empty and not daily_mr.empty:
        daily_trend_df = pd.merge(daily_vit_a, daily_mr, on=col_date, how='outer').fillna(0)
    elif not daily_vit_a.empty:
        daily_trend_df = daily_vit_a.copy()
        daily_trend_df['Daily_MR_Total'] = 0
    elif not daily_mr.empty:
        daily_trend_df = daily_mr.copy()
        daily_trend_df['Daily_Vit_A_Total'] = 0
    else:
        daily_trend_df = pd.DataFrame()

    if not daily_trend_df.empty:
        daily_trend_df = daily_trend_df.sort_values(by=col_date)

        daily_melted = daily_trend_df.melt(
            id_vars=[col_date],
            value_vars=['Daily_Vit_A_Total', 'Daily_MR_Total'],
            var_name='Response Type',
            value_name='Total Administered'
        )

        daily_melted['Response Type'] = daily_melted['Response Type'].map({
            'Daily_Vit_A_Total': 'Vitamin A Response',
            'Daily_MR_Total': 'Measles-Rubella (MR) Response'
        })

        fig_line = px.line(
            daily_melted,
            x=col_date,
            y='Total Administered',
            color='Response Type',
            markers=True,
            title='Daily Total Response Over Time',
            color_discrete_map={
                'Vitamin A Response': '#2ca02c',
                'Measles-Rubella (MR) Response': '#1f77b4'
            }
        )
        fig_line.update_layout(
            xaxis_title="Date",
            yaxis_title="Total Administered",
            hovermode="x unified",
            height=380
        )
        st.plotly_chart(fig_line, use_container_width=True)
    else:
        st.info("No daily date data available for the selected filter criteria.")

    st.divider()

    # --- SECTION 2: OVERALL METRIC SUMMARY ---
    st.header("Overall Metric Summary")
    col_summary1, col_summary2, col_summary3 = st.columns(3)

    # 1. Vitamin A Summary Chart
    with col_summary1:
        if vit_a_target_cols:
            vit_a_totals = []
            for col in vit_a_target_cols:
                val = clean_numeric_sum(vit_a_df[col]) if not vit_a_df.empty else 0
                vit_a_totals.append({"Metric": col.replace("Vitamin A ", "").replace(" Total", ""), "Total": int(val)})

            chart_data_vit_a = pd.DataFrame(vit_a_totals)

            fig_vit_a = px.bar(
                chart_data_vit_a,
                x="Metric",
                y="Total",
                color="Metric",
                text="Total",
                title="<b>Vitamin A</b>",
                color_discrete_sequence=px.colors.qualitative.Set2
            )
            fig_vit_a.update_traces(textposition='auto')
            fig_vit_a.update_layout(
                xaxis_title="", 
                yaxis_title="Doses", 
                showlegend=False, 
                height=260,
                margin=dict(l=10, r=10, t=40, b=10)
            )
            st.plotly_chart(fig_vit_a, use_container_width=True)

    # 2. MR Doses Chart
    with col_summary2:
        if mr_dose_cols:
            mr_totals = []
            for col in mr_dose_cols:
                val = clean_numeric_sum(mr_df[col]) if not mr_df.empty else 0
                mr_totals.append({"Age": col.replace("MR ", "").replace(" Total", ""), "Total": int(val)})

            chart_data_mr = pd.DataFrame(mr_totals)

            fig_mr = px.bar(
                chart_data_mr,
                x="Age",
                y="Total",
                color="Age",
                text="Total",
                title="<b>MR Doses</b>",
                color_discrete_sequence=px.colors.qualitative.Pastel
            )
            fig_mr.update_traces(textposition='auto')
            fig_mr.update_layout(
                xaxis_title="", 
                yaxis_title="Doses", 
                showlegend=False, 
                height=260,
                margin=dict(l=10, r=10, t=40, b=10)
            )
            st.plotly_chart(fig_mr, use_container_width=True)

    # 3. MR Zero Doses Chart
    with col_summary3:
        if mr_zero_cols:
            mr_zero_totals = []
            for col in mr_zero_cols:
                val = clean_numeric_sum(mr_df[col]) if not mr_df.empty else 0
                mr_zero_totals.append({"Age": col.replace("MR Zero ", "").replace(" Total", ""), "Total": int(val)})

            chart_data_mr_zero = pd.DataFrame(mr_zero_totals)

            fig_mr_zero = px.bar(
                chart_data_mr_zero,
                x="Age",
                y="Total",
                color="Age",
                text="Total",
                title="<b>MR Zero Doses</b>",
                color_discrete_sequence=px.colors.qualitative.Safe
            )
            fig_mr_zero.update_traces(textposition='auto')
            fig_mr_zero.update_layout(
                xaxis_title="", 
                yaxis_title="Doses", 
                showlegend=False, 
                height=260,
                margin=dict(l=10, r=10, t=40, b=10)
            )
            st.plotly_chart(fig_mr_zero, use_container_width=True)

    st.divider()

    # --- SECTION 3: ACCOMPLISHMENT PERCENTAGE VS TARGET (GAUGE CHARTS) ---
    st.header("Target Population vs Accomplishment Gauges")

    # Helper function to create gauge charts
    def create_gauge_chart(title, accomplishment, target, height=300, font_size=14, is_large=False):
        pct = round((accomplishment / target * 100), 1) if target > 0 else 0
        max_axis_val = max(target, accomplishment) * 1.15 if target > 0 else 100

        fig = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=accomplishment,
            number={'valueformat': ',d', 'font': {'size': 36 if is_large else 28}},
            domain={'x': [0.05, 0.95], 'y': [0.05, 0.70]},
            title={
                'text': f"<b>{title}</b><br><span style='font-size:{0.95 if is_large else 0.85}em;color:#475569'>{pct}% of Target ({target:,})</span>", 
                'font': {'size': font_size},
                'align': 'center'
            },
            delta={
                'reference': target, 
                'relative': False, 
                'valueformat': ',d', 
                'increasing': {'color': "#16a34a"}
            },
            gauge={
                'axis': {
                    'range': [0, max_axis_val], 
                    'tickwidth': 1, 
                    'tickcolor': "#334155",
                    'tickformat': ',d'
                },
                'bar': {'color': "#0284c7"},
                'bgcolor': "white",
                'borderwidth': 1.5,
                'bordercolor': "#cbd5e1",
                'steps': [
                    {'range': [0, target * 0.5], 'color': '#fee2e2'},
                    {'range': [target * 0.5, target * 0.9], 'color': '#fef3c7'},
                    {'range': [target * 0.9, target], 'color': '#dcfce7'},
                    {'range': [target, max_axis_val], 'color': '#bbf7d0'}
                ],
                'threshold': {
                    'line': {'color': "#dc2626", 'width': 4},
                    'thickness': 0.8,
                    'value': target
                }
            }
        ))

        fig.update_layout(
            height=height,
            margin=dict(l=25, r=25, t=50 if not is_large else 60, b=30)
        )
        return fig

    # --- SUB-SECTION 1: MEASLES-RUBELLA (MR) ---
    st.subheader("Response Type: Measles-Rubella (MR)")

    if not df_target_raw.empty:
        # Exact 0-indexed column mappings according to Target Sheet specs
        # Col B (index 1): Barangay
        # Col F (index 5): Target 6 - 59 mos
        # Col I (index 8): Target 6 - 12 mos
        # Col L (index 11): Target 13 - 23 mos
        # Col O (index 14): Target 24 - 59 mos

        def get_col_safe(df, idx):
            return df.columns[idx] if len(df.columns) > idx else None

        t_barangay_col = get_col_safe(df_target_raw, 1)
        t_city_col = next((c for c in df_target_raw.columns if any(k in c.lower() for k in ["city", "muni"])), None)
        t_bakuna_col = next((c for c in df_target_raw.columns if any(k in c.lower() for k in ["bakuna", "dhc", "center", "facility"])), None)

        col_t_6_59 = get_col_safe(df_target_raw, 5)
        col_t_6_12 = get_col_safe(df_target_raw, 8)
        col_t_13_23 = get_col_safe(df_target_raw, 11)
        col_t_24_59 = get_col_safe(df_target_raw, 14)

        gauge_target_df = df_target_raw.copy()

        # Apply sidebar filters to target dataframe
        if selected_barangay and t_barangay_col:
            selected_bgy_clean = [str(b).strip().upper() for b in selected_barangay]
            gauge_target_df = gauge_target_df[
                gauge_target_df[t_barangay_col].astype(str).str.strip().str.upper().isin(selected_bgy_clean)
            ]
        else:
            if selected_city and t_city_col:
                selected_city_clean = [str(c).strip().upper() for c in selected_city]
                gauge_target_df = gauge_target_df[
                    gauge_target_df[t_city_col].astype(str).str.strip().str.upper().isin(selected_city_clean)
                ]
            if selected_bakuna and t_bakuna_col:
                selected_bakuna_clean = [str(b).strip().upper() for b in selected_bakuna]
                gauge_target_df = gauge_target_df[
                    gauge_target_df[t_bakuna_col].astype(str).str.strip().str.upper().isin(selected_bakuna_clean)
                ]

        # Targets per Age Group (using updated column indexes)
        t_val_6_12 = clean_numeric_sum(gauge_target_df[col_t_6_12]) if col_t_6_12 else 0
        t_val_13_23 = clean_numeric_sum(gauge_target_df[col_t_13_23]) if col_t_13_23 else 0
        t_val_24_59 = clean_numeric_sum(gauge_target_df[col_t_24_59]) if col_t_24_59 else 0
        
        if col_t_6_59:
            t_val_6_59 = clean_numeric_sum(gauge_target_df[col_t_6_59])
        else:
            t_val_6_59 = t_val_6_12 + t_val_13_23 + t_val_24_59

        # Accomplishments per Age Group (Raw Data Columns K, L, M)
        acc_val_6_12 = clean_numeric_sum(mr_df[col_mr_6_12]) if (not mr_df.empty and col_mr_6_12) else 0
        acc_val_13_23 = clean_numeric_sum(mr_df[col_mr_13_23]) if (not mr_df.empty and col_mr_13_23) else 0
        acc_val_24_59 = clean_numeric_sum(mr_df[col_mr_24_59]) if (not mr_df.empty and col_mr_24_59) else 0
        acc_val_6_59 = acc_val_6_12 + acc_val_13_23 + acc_val_24_59

        g_row1_col1, g_row1_col2, g_row1_col3 = st.columns(3)

        with g_row1_col1:
            st.plotly_chart(
                create_gauge_chart(
                    "6 - 12 mos Total<br><span style='font-size:0.8em;color:#64748b'>(Acc: Col K | Target: Col I)</span>", 
                    int(acc_val_6_12), 
                    int(t_val_6_12)
                ), 
                use_container_width=True
            )

        with g_row1_col2:
            st.plotly_chart(
                create_gauge_chart(
                    "13 - 23 mos Total<br><span style='font-size:0.8em;color:#64748b'>(Acc: Col L | Target: Col L)</span>", 
                    int(acc_val_13_23), 
                    int(t_val_13_23)
                ), 
                use_container_width=True
            )

        with g_row1_col3:
            st.plotly_chart(
                create_gauge_chart(
                    "24 - 59 mos Total<br><span style='font-size:0.8em;color:#64748b'>(Acc: Col M | Target: Col O)</span>", 
                    int(acc_val_24_59), 
                    int(t_val_24_59)
                ), 
                use_container_width=True
            )

        st.markdown("<br>", unsafe_allow_html=True)
        st.plotly_chart(
            create_gauge_chart(
                "Overall Target: 6 - 59 mos Total<br><span style='font-size:0.75em;color:#64748b'>(Target: Col F)</span>", 
                int(acc_val_6_59), 
                int(t_val_6_59), 
                height=420, 
                font_size=18, 
                is_large=True
            ), 
            use_container_width=True
        )

    else:
        st.info("The 'Target' worksheet could not be loaded or contains no rows.")

    st.markdown("---")

    # --- SUB-SECTION 2: VITAMIN A ---
    st.subheader("Response Type: Vitamin A")

    # Remarks note regarding citywide target aggregation
    st.info("ℹ️ **Note:** Target is for the entire city of Baguio; no disaggregation per DHC or barangay.")

    # Load targetVitA sheet dynamically
    @st.cache_data(ttl=600)
    def load_target_vit_a():
        try:
            url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=targetVitA"
            df_vit = pd.read_csv(url)
            return df_vit
        except Exception:
            try:
                alt_url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&sheet=targetVitA"
                return pd.read_csv(alt_url)
            except Exception as e:
                st.warning(f"Could not load 'targetVitA' sheet: {e}")
                return pd.DataFrame()

    df_target_vit_a = load_target_vit_a()

    # Calculate Accomplishments from rawdata (filtered_df)
    vit_a_acc_6_11 = clean_numeric_sum(filtered_df[col_vit_6_11]) if (not filtered_df.empty and col_vit_6_11) else 0
    vit_a_acc_12_59 = clean_numeric_sum(filtered_df[col_vit_12_59]) if (not filtered_df.empty and col_vit_12_59) else 0
    vit_a_acc_total = vit_a_acc_6_11 + vit_a_acc_12_59

    # Retrieve Targets from targetVitA sheet (A2, B2, C2)
    if not df_target_vit_a.empty and len(df_target_vit_a) >= 1:
        target_vit_6_11 = clean_numeric_sum(pd.Series([df_target_vit_a.iloc[0, 0]])) if len(df_target_vit_a.columns) > 0 else 0
        target_vit_12_59 = clean_numeric_sum(pd.Series([df_target_vit_a.iloc[0, 1]])) if len(df_target_vit_a.columns) > 1 else 0
        target_vit_total = clean_numeric_sum(pd.Series([df_target_vit_a.iloc[0, 2]])) if len(df_target_vit_a.columns) > 2 else 0
    else:
        target_vit_6_11 = 0
        target_vit_12_59 = 0
        target_vit_total = 0

    # Display Vitamin A Gauges
    vg_col1, vg_col2 = st.columns(2)

    with vg_col1:
        st.plotly_chart(
            create_gauge_chart(
                "Vit A 6 - 11 mos<br><span style='font-size:0.8em;color:#64748b'>(Acc: Col Q | Target: targetVitA A2)</span>", 
                int(vit_a_acc_6_11), 
                int(target_vit_6_11)
            ), 
            use_container_width=True
        )

    with vg_col2:
        st.plotly_chart(
            create_gauge_chart(
                "Vit A 12 - 59 mos<br><span style='font-size:0.8em;color:#64748b'>(Acc: Col R | Target: targetVitA B2)</span>", 
                int(vit_a_acc_12_59), 
                int(target_vit_12_59)
            ), 
            use_container_width=True
        )

    st.markdown("<br>", unsafe_allow_html=True)
    st.plotly_chart(
        create_gauge_chart(
            "Overall Vitamin A Target (6 - 59 mos)<br><span style='font-size:0.75em;color:#64748b'>(Acc: Cols Q+R | Target: targetVitA C2)</span>", 
            int(vit_a_acc_total), 
            int(target_vit_total), 
            height=420, 
            font_size=18, 
            is_large=True
        ), 
        use_container_width=True
    )

    st.divider()

    # --- SECTION 4: DHC ACCOMPLISHMENT DATA SUMMARY ---
    st.header("DHC Accomplishment Data Summary")
    
    dhc_col1, dhc_col2 = st.columns(2)

    # 1. Measles-Rubella Table & Chart
    with dhc_col1:
        st.subheader("Measles-Rubella (MR) by Bakuna Center")
        if not mr_df.empty:
            dhc_mr_df = mr_df.copy()
            
            dhc_mr_df['MR_6_12'] = pd.to_numeric(dhc_mr_df[col_mr_6_12].astype(str).str.replace(",", "").str.strip(), errors='coerce').fillna(0)
            dhc_mr_df['MR_13_23'] = pd.to_numeric(dhc_mr_df[col_mr_13_23].astype(str).str.replace(",", "").str.strip(), errors='coerce').fillna(0)
            dhc_mr_df['MR_24_59'] = pd.to_numeric(dhc_mr_df[col_mr_24_59].astype(str).str.replace(",", "").str.strip(), errors='coerce').fillna(0)

            mr_summary = dhc_mr_df.groupby(col_bakuna)[['MR_6_12', 'MR_13_23', 'MR_24_59']].sum().reset_index()
            mr_summary['Total MR'] = mr_summary['MR_6_12'] + mr_summary['MR_13_23'] + mr_summary['MR_24_59']

            mr_summary.columns = [
                'Bakuna Center Name', 
                'MR 6-12mos [col K]', 
                'MR 13-23mos [col L]', 
                'MR 24-59mos [col M]',
                'Total MR'
            ]

            mr_summary = mr_summary.sort_values(by='Total MR', ascending=False)

            total_row = pd.DataFrame([{
                'Bakuna Center Name': 'TOTAL',
                'MR 6-12mos [col K]': mr_summary['MR 6-12mos [col K]'].sum(),
                'MR 13-23mos [col L]': mr_summary['MR 13-23mos [col L]'].sum(),
                'MR 24-59mos [col M]': mr_summary['MR 24-59mos [col M]'].sum(),
                'Total MR': mr_summary['Total MR'].sum()
            }])
            
            mr_summary_final = pd.concat([mr_summary, total_row], ignore_index=True)
            st.dataframe(mr_summary_final, use_container_width=True, hide_index=True)

            st.download_button(
                label="📥 Export MR Table (CSV)",
                data=convert_df_to_csv(mr_summary_final),
                file_name="mr_summary_by_bakuna_center.csv",
                mime="text/csv",
                key="download_mr_summary"
            )

            fig_mr_bar = px.bar(
                mr_summary.sort_values(by='Total MR', ascending=True),
                y='Bakuna Center Name',
                x='Total MR',
                orientation='h',
                text='Total MR',
                title='<b>Total MR Doses by Bakuna Center</b>',
                color_discrete_sequence=['#1f77b4']
            )
            fig_mr_bar.update_traces(textposition='outside')
            fig_mr_bar.update_layout(
                xaxis_title="Total Doses",
                yaxis_title="",
                height=max(350, len(mr_summary) * 30),
                margin=dict(l=10, r=20, t=40, b=20)
            )
            st.plotly_chart(fig_mr_bar, use_container_width=True)

        else:
            st.info("No Measles-Rubella data available for the selected filters.")

    # 2. Vitamin A Table & Chart
    with dhc_col2:
        st.subheader("Vitamin A by Bakuna Center")
        if not vit_a_df.empty:
            dhc_vit_df = vit_a_df.copy()

            dhc_vit_df['Vit_6_11'] = pd.to_numeric(dhc_vit_df[col_vit_6_11].astype(str).str.replace(",", "").str.strip(), errors='coerce').fillna(0)
            dhc_vit_df['Vit_12_59'] = pd.to_numeric(dhc_vit_df[col_vit_12_59].astype(str).str.replace(",", "").str.strip(), errors='coerce').fillna(0)

            vit_summary = dhc_vit_df.groupby(col_bakuna)[['Vit_6_11', 'Vit_12_59']].sum().reset_index()
            vit_summary['Total Vit A'] = vit_summary['Vit_6_11'] + vit_summary['Vit_12_59']

            vit_summary.columns = [
                'Bakuna Center Name', 
                'Vit A 6-11mos [col Q]', 
                'Vit A 12-59mos [col R]',
                'Total Vit A'
            ]

            vit_summary = vit_summary.sort_values(by='Total Vit A', ascending=False)

            total_vit_row = pd.DataFrame([{
                'Bakuna Center Name': 'TOTAL',
                'Vit A 6-11mos [col Q]': vit_summary['Vit A 6-11mos [col Q]'].sum(),
                'Vit A 12-59mos [col R]': vit_summary['Vit A 12-59mos [col R]'].sum(),
                'Total Vit A': vit_summary['Total Vit A'].sum()
            }])

            vit_summary_final = pd.concat([vit_summary, total_vit_row], ignore_index=True)
            st.dataframe(vit_summary_final, use_container_width=True, hide_index=True)

            st.download_button(
                label="📥 Export Vitamin A Table (CSV)",
                data=convert_df_to_csv(vit_summary_final),
                file_name="vit_a_summary_by_bakuna_center.csv",
                mime="text/csv",
                key="download_vit_a_summary"
            )

            fig_vit_bar = px.bar(
                vit_summary.sort_values(by='Total Vit A', ascending=True),
                y='Bakuna Center Name',
                x='Total Vit A',
                orientation='h',
                text='Total Vit A',
                title='<b>Total Vitamin A Doses by Bakuna Center</b>',
                color_discrete_sequence=['#2ca02c']
            )
            fig_vit_bar.update_traces(textposition='outside')
            fig_vit_bar.update_layout(
                xaxis_title="Total Doses",
                yaxis_title="",
                height=max(350, len(vit_summary) * 30),
                margin=dict(l=10, r=20, t=40, b=20)
            )
            st.plotly_chart(fig_vit_bar, use_container_width=True)

        else:
            st.info("No Vitamin A data available for the selected filters.")

    st.divider()

    # --- SECTION 5: BARANGAY ACCOMPLISHMENT TABLE HEATMAP ---
    st.header("Barangay Accomplishment Table Heatmap")

    heatmap_mr_cols = [col_mr_6_12, col_mr_13_23, col_mr_24_59]
    heatmap_vit_cols = [col_vit_6_11, col_vit_12_59]

    bgy_summary_records = []
    heatmap_barangays = selected_barangay if selected_barangay else barangays

    for bgy in heatmap_barangays:
        if not filtered_df.empty:
            bgy_data = filtered_df[filtered_df[col_barangay].astype(str) == bgy]
            
            mr_doses_val = bgy_data[heatmap_mr_cols].apply(
                lambda col: pd.to_numeric(col.astype(str).str.replace(",", "").str.strip(), errors='coerce')
            ).sum().sum() if not bgy_data.empty else 0
            
            vit_a_val = bgy_data[heatmap_vit_cols].apply(
                lambda col: pd.to_numeric(col.astype(str).str.replace(",", "").str.strip(), errors='coerce')
            ).sum().sum() if not bgy_data.empty else 0
        else:
            mr_doses_val = 0
            vit_a_val = 0

        bgy_summary_records.append({
            "Barangay": bgy,
            "MR (Cols K-M)": int(mr_doses_val),
            "Vitamin A (Cols Q-R)": int(vit_a_val),
            "Total Accomplishment": int(mr_doses_val + vit_a_val)
        })

    heatmap_df = pd.DataFrame(bgy_summary_records)
    
    if not heatmap_df.empty and heatmap_df["Total Accomplishment"].sum() > 0:
        heatmap_df = heatmap_df.sort_values(by="Total Accomplishment", ascending=False)
        st.download_button(
            label="📥 Export Barangay Accomplishment Data (CSV)",
            data=convert_df_to_csv(heatmap_df),
            file_name="barangay_accomplishment_summary.csv",
            mime="text/csv",
            key="download_bgy_heatmap_data"
        )

        heatmap_melted = heatmap_df.sort_values(by="Total Accomplishment", ascending=True).melt(
            id_vars=["Barangay"],
            value_vars=["MR (Cols K-M)", "Vitamin A (Cols Q-R)"],
            var_name="Category",
            value_name="Count"
        )

        fig_table_heatmap = px.density_heatmap(
            heatmap_melted,
            x="Category",
            y="Barangay",
            z="Count",
            color_continuous_scale="YlGnBu",
            text_auto=True,
            title="<b>Barangay Accomplishment Heatmap (MR: Cols K-M | Vit A: Cols Q-R)</b>"
        )

        chart_pixel_height = max(450, len(heatmap_df) * 22)
        fig_table_heatmap.update_layout(
            xaxis_title="Vaccination Category",
            yaxis_title="Barangay Name",
            height=chart_pixel_height,
            coloraxis_colorbar=dict(title="Doses"),
            margin=dict(l=10, r=10, t=50, b=20)
        )

        with st.container(height=500):
            st.plotly_chart(fig_table_heatmap, use_container_width=True)
    else:
        st.info("No recorded accomplishments found for the selected barangay(s).")

    st.divider()

    # --- SECTION 6: BARANGAY BREAKDOWN CHARTS (PIE CHARTS) ---
    st.header("Accomplishment Share by Barangay")
    b_left_col, b_right_col = st.columns(2)

    with b_left_col:
        st.subheader("Vitamin A Distribution by Barangay")
        if vit_a_target_cols and not vit_a_df.empty:
            vit_a_bgy_df = vit_a_df.copy()
            vit_a_bgy_df['Total_Vit_A'] = vit_a_bgy_df[vit_a_target_cols].apply(
                lambda col: pd.to_numeric(col.astype(str).str.replace(",", "").str.strip(), errors='coerce')
            ).sum(axis=1)
            
            vit_a_bgy_summary = vit_a_bgy_df.groupby(col_barangay)['Total_Vit_A'].sum().reset_index()
            vit_a_bgy_summary = vit_a_bgy_summary[vit_a_bgy_summary['Total_Vit_A'] > 0]

            if not vit_a_bgy_summary.empty:
                fig_pie_vit_a = px.pie(
                    vit_a_bgy_summary,
                    names=col_barangay,
                    values='Total_Vit_A',
                    title="Vitamin A Share per Barangay",
                    hole=0.4,
                    color_discrete_sequence=px.colors.qualitative.Set2
                )
                fig_pie_vit_a.update_traces(textposition='inside', textinfo='percent+label')
                st.plotly_chart(fig_pie_vit_a, use_container_width=True)
            else:
                st.info("No Vitamin A data recorded for the selected selection.")
        else:
            st.info("No Vitamin A data recorded for the selected selection.")

    with b_right_col:
        st.subheader("Measles-Rubella (MR) Distribution by Barangay")
        if mr_dose_cols and not mr_df.empty:
            mr_bgy_df = mr_df.copy()
            mr_bgy_df['Total_MR_Doses'] = mr_bgy_df[mr_dose_cols].apply(
                lambda col: pd.to_numeric(col.astype(str).str.replace(",", "").str.strip(), errors='coerce')
            ).sum(axis=1)
            
            mr_bgy_summary = mr_bgy_df.groupby(col_barangay)['Total_MR_Doses'].sum().reset_index()
            mr_bgy_summary = mr_bgy_summary[mr_bgy_summary['Total_MR_Doses'] > 0]

            if not mr_bgy_summary.empty:
                fig_pie_mr = px.pie(
                    mr_bgy_summary,
                    names=col_barangay,
                    values='Total_MR_Doses',
                    title="MR Doses Share per Barangay",
                    hole=0.4,
                    color_discrete_sequence=px.colors.qualitative.Pastel
                )
                fig_pie_mr.update_traces(textposition='inside', textinfo='percent+label')
                st.plotly_chart(fig_pie_mr, use_container_width=True)
        else:
            st.info("No MR Doses recorded for the selected selection.")

        if mr_zero_cols and not mr_df.empty:
            mr_zero_bgy_df = mr_df.copy()
            mr_zero_bgy_df['Total_MR_Zero'] = mr_zero_bgy_df[mr_zero_cols].apply(
                lambda col: pd.to_numeric(col.astype(str).str.replace(",", "").str.strip(), errors='coerce')
            ).sum(axis=1)
            
            mr_zero_bgy_summary = mr_zero_bgy_df.groupby(col_barangay)['Total_MR_Zero'].sum().reset_index()
            mr_zero_bgy_summary = mr_zero_bgy_summary[mr_zero_bgy_summary['Total_MR_Zero'] > 0]

            if not mr_zero_bgy_summary.empty:
                fig_pie_mr_zero = px.pie(
                    mr_zero_bgy_summary,
                    names=col_barangay,
                    values='Total_MR_Zero',
                    title="MR Zero Doses Share per Barangay",
                    hole=0.4,
                    color_discrete_sequence=px.colors.qualitative.Safe
                )
                fig_pie_mr_zero.update_traces(textposition='inside', textinfo='percent+label')
                st.plotly_chart(fig_pie_mr_zero, use_container_width=True)

    st.divider()

    # --- SECTION 7: DEFERRAL AND REFUSAL ANALYSIS ---
    st.header("Deferral and Refusal Analysis")

    col_deferrals = df_raw.columns[20] if len(df_raw.columns) > 20 else None
    col_refusals = df_raw.columns[21] if len(df_raw.columns) > 21 else None

    total_deferrals_val = clean_numeric_sum(filtered_df[col_deferrals]) if (not filtered_df.empty and col_deferrals) else 0
    total_refusals_val = clean_numeric_sum(filtered_df[col_refusals]) if (not filtered_df.empty and col_refusals) else 0

    def_col1, def_col2 = st.columns([1, 2])

    with def_col1:
        st.subheader("Summary Totals")
        st.metric("Total Deferrals", f"{int(total_deferrals_val):,}")
        st.metric("Total Refusals", f"{int(total_refusals_val):,}")

    with def_col2:
        def_ref_summary_df = pd.DataFrame([
            {"Category": "Deferrals", "Total Count": int(total_deferrals_val)},
            {"Category": "Refusals", "Total Count": int(total_refusals_val)}
        ])
        fig_def_ref = px.bar(
            def_ref_summary_df,
            x="Category",
            y="Total Count",
            color="Category",
            text="Total Count",
            title="Total Deferrals vs Refusals",
            color_discrete_map={"Deferrals": "#f59e0b", "Refusals": "#ef4444"}
        )
        fig_def_ref.update_traces(textposition='auto')
        fig_def_ref.update_layout(xaxis_title="", yaxis_title="Count", showlegend=False, height=300)
        st.plotly_chart(fig_def_ref, use_container_width=True)

    st.subheader("Reason Breakdown Tables")
    tbl_col1, tbl_col2 = st.columns(2)

    with tbl_col1:
        st.markdown("#### Deferral Reasons")
        def_reason_cols = df_raw.columns[27:41].tolist() if len(df_raw.columns) >= 41 else []
        def_reasons_data = []

        for col in def_reason_cols:
            cnt = clean_numeric_sum(filtered_df[col]) if not filtered_df.empty else 0
            clean_name = str(col).replace("Deferral Reason -", "").replace("Deferral Reason:", "").strip()
            def_reasons_data.append({"Deferral Reason": clean_name, "Count": int(cnt)})

        if def_reasons_data:
            def_reasons_df = pd.DataFrame(def_reasons_data).sort_values(by="Count", ascending=False)
            st.dataframe(def_reasons_df, use_container_width=True, hide_index=True)

            st.download_button(
                label="📥 Export Deferral Reasons (CSV)",
                data=convert_df_to_csv(def_reasons_df),
                file_name="deferral_reasons_summary.csv",
                mime="text/csv",
                key="download_deferral_reasons"
            )
        else:
            st.info("No Deferral Reason columns found (Columns AB:AO).")

    with tbl_col2:
        st.markdown("#### Refusal Reasons")
        ref_reason_cols = df_raw.columns[41:50].tolist() if len(df_raw.columns) >= 50 else []
        ref_reasons_data = []

        for col in ref_reason_cols:
            cnt = clean_numeric_sum(filtered_df[col]) if not filtered_df.empty else 0
            clean_name = str(col).replace("Refusal Reason -", "").replace("Refusal Reason:", "").strip()
            ref_reasons_data.append({"Refusal Reason": clean_name, "Count": int(cnt)})

        if ref_reasons_data:
            ref_reasons_df = pd.DataFrame(ref_reasons_data).sort_values(by="Count", ascending=False)
            st.dataframe(ref_reasons_df, use_container_width=True, hide_index=True)

            st.download_button(
                label="📥 Export Refusal Reasons (CSV)",
                data=convert_df_to_csv(ref_reasons_df),
                file_name="refusal_reasons_summary.csv",
                mime="text/csv",
                key="download_refusal_reasons"
            )
        else:
            st.info("No Refusal Reason columns found (Columns AP:AX).")

    st.divider()

    # --- SECTION 8: PENDING BARANGAY SUBMISSIONS ---
    st.header("Barangay Submission Status")

    if not df_target_raw.empty and len(df_target_raw.columns) > 1:
        # Target Barangays from Column B (index 1)
        target_bgy_col = df_target_raw.columns[1]
        all_target_bgys = df_target_raw[target_bgy_col].dropna().astype(str).str.strip().unique().tolist()
        all_target_bgys = sorted([b for b in all_target_bgys if b and b.upper() != "NAN"])

        if all_target_bgys:
            mr_submitted_bgys = set(
                df_raw[df_raw[col_response].astype(str).str.contains("Measles|MR", case=False, na=False)][col_barangay]
                .dropna().astype(str).str.strip().str.upper().unique()
            )

            vit_a_submitted_bgys = set(
                df_raw[df_raw[col_response].astype(str).str.contains("Vitamin A", case=False, na=False)][col_barangay]
                .dropna().astype(str).str.strip().str.upper().unique()
            )

            status_filter = st.radio(
                "Filter View:",
                ["Show All Target Barangays", "Show Pending Only", "Show Fully Submitted Only"],
                horizontal=True
            )

            submission_records = []
            for bgy in all_target_bgys:
                bgy_upper = bgy.upper()
                has_mr = "Submitted" if bgy_upper in mr_submitted_bgys else "Not Yet Submitted"
                has_vit_a = "Submitted" if bgy_upper in vit_a_submitted_bgys else "Not Yet Submitted"
                
                if has_mr == "Submitted" and has_vit_a == "Submitted":
                    overall_status = "Fully Submitted"
                elif has_mr == "Not Yet Submitted" and has_vit_a == "Not Yet Submitted":
                    overall_status = "Pending (Both)"
                else:
                    overall_status = "Partially Submitted"

                submission_records.append({
                    "Barangay Name": bgy,
                    "Measles-Rubella (MR) Status": has_mr,
                    "Vitamin A Status": has_vit_a,
                    "Overall Status": overall_status
                })

            sub_df = pd.DataFrame(submission_records)

            if status_filter == "Show Pending Only":
                sub_df_display = sub_df[sub_df["Overall Status"] != "Fully Submitted"]
            elif status_filter == "Show Fully Submitted Only":
                sub_df_display = sub_df[sub_df["Overall Status"] == "Fully Submitted"]
            else:
                sub_df_display = sub_df.copy()

            pending_mr_cnt = sum(1 for r in submission_records if r["Measles-Rubella (MR) Status"] == "Not Yet Submitted")
            pending_vit_cnt = sum(1 for r in submission_records if r["Vitamin A Status"] == "Not Yet Submitted")
            fully_sub_cnt = sum(1 for r in submission_records if r["Overall Status"] == "Fully Submitted")

            col_p1, col_p2, col_p3 = st.columns(3)
            col_p1.metric("Pending MR Submissions", pending_mr_cnt)
            col_p2.metric("Pending Vitamin A Submissions", pending_vit_cnt)
            col_p3.metric("Fully Submitted Barangays", fully_sub_cnt)

            st.dataframe(sub_df_display, use_container_width=True, hide_index=True)

            st.download_button(
                label="📥 Export Submission Status Table (CSV)",
                data=convert_df_to_csv(sub_df_display),
                file_name="barangay_submission_status.csv",
                mime="text/csv",
                key="download_submission_status"
            )
        else:
            st.info("No valid Barangay names found in Target sheet Column B.")
    else:
        st.warning("Target sheet is empty or does not contain Column B (Barangay Name).")

else:
    st.warning("Unable to fetch data. Please check the spreadsheet URL or permissions.")
