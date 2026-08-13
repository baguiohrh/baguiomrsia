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

df_raw = load_data()
df_target_raw = load_target_data()
as_of_date, as_of_time = load_data_as_of()

# --- DATA AS OF REMINDER BANNER ---
timestamp_str = f"{as_of_date} {as_of_time}".strip()
if timestamp_str and timestamp_str != "nan nan":
    st.info(f"📌 **Data as of:** {timestamp_str} | *All data is subject to change without prior notice.*")
else:
    st.info("📌 *All data is subject to change without prior notice.*")

if not df_raw.empty:
    # Identify key columns by position in main sheet
    col_bakuna = df_raw.columns[5]    # Column F (Bakuna Center Name)
    col_barangay = df_raw.columns[7]  # Column H (Barangay Name)
    col_date = df_raw.columns[8]      # Column I (Vaccination Date)
    col_response = df_raw.columns[9]  # Column J (Response Type)

    # Specific Columns for MR (Columns K, L, M)
    col_mr_6_12 = df_raw.columns[10]   # Column K (MR 6-12 mos Total)
    col_mr_13_23 = df_raw.columns[11]  # Column L (MR 13-23 mos Total)
    col_mr_24_59 = df_raw.columns[12]  # Column M (MR 24-59 mos Total)

    # Specific Columns for Vit A (Columns Q, R)
    col_vit_6_11 = df_raw.columns[16]   # Column Q (Vit A 6-11 mos Total)
    col_vit_12_59 = df_raw.columns[17]  # Column R (Vit A 12-59 mos Total)

    # List of dose metrics columns (Column K onwards)
    dose_cols = df_raw.columns[10:].tolist()

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
    """)

    st.sidebar.markdown("---")

    # --- SIDEBAR FILTERS ---
    st.sidebar.header("Filter Options")

    # Filter 1: Bakuna Center Name [Column F]
    bakuna_centers = sorted(df_raw[col_bakuna].dropna().astype(str).unique().tolist())
    selected_bakuna = st.sidebar.multiselect("Bakuna Center Name", bakuna_centers)

    # Filter 2: Barangay Name [Column H] (DEPENDENT ON BAKUNA CENTER SELECTION)
    if selected_bakuna:
        available_barangays_df = df_raw[df_raw[col_bakuna].astype(str).isin(selected_bakuna)]
        barangays = sorted(available_barangays_df[col_barangay].dropna().astype(str).unique().tolist())
    else:
        barangays = sorted(df_raw[col_barangay].dropna().astype(str).unique().tolist())

    selected_barangay = st.sidebar.multiselect("Barangay Name", barangays)

    # Filter 3: Vaccination Date Range [Column I]
    min_date = df_raw[col_date].min()
    max_date = df_raw[col_date].max()
    
    if pd.notnull(min_date) and pd.notnull(max_date):
        selected_date_range = st.sidebar.date_input(
            "Vaccination Date Range",
            value=(min_date.date(), max_date.date()),
            min_value=min_date.date(),
            max_value=max_date.date()
        )
    else:
        selected_date_range = []

    # --- APPLY FILTERS TO ACCOMPLISHMENT DATA ---
    filtered_df = df_raw.copy()

    if selected_bakuna:
        filtered_df = filtered_df[filtered_df[col_bakuna].astype(str).isin(selected_bakuna)]

    if selected_barangay:
        filtered_df = filtered_df[filtered_df[col_barangay].astype(str).isin(selected_barangay)]

    if len(selected_date_range) == 2:
        start_date, end_date = selected_date_range
        filtered_df = filtered_df[
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

    # --- APPLY FILTERS TO TARGET DATA ---
    filtered_target_df = df_target_raw.copy()
    if not filtered_target_df.empty:
        t_bakuna_col = next((c for c in filtered_target_df.columns if "bakuna" in c.lower()), None)
        t_barangay_col = next((c for c in filtered_target_df.columns if "barangay" in c.lower() and "code" not in c.lower()), None)

        if selected_bakuna and t_bakuna_col:
            filtered_target_df = filtered_target_df[filtered_target_df[t_bakuna_col].astype(str).isin(selected_bakuna)]
        if selected_barangay and t_barangay_col:
            filtered_target_df = filtered_target_df[filtered_target_df[t_barangay_col].astype(str).isin(selected_barangay)]

    # Convert response column safely to string
    response_series = filtered_df[col_response].astype(str)

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

    # Combine MR Doses and MR Zero Doses
    all_mr_cols = mr_dose_cols + mr_zero_cols

    # --- GRAND TOTAL CARDS ---
    st.markdown("### Accomplishment Summary")
    
    col_total_doses = df_raw.columns[18]  # "Grand total doses administered"
    col_zero_doses = df_raw.columns[19]   # "Grand total doses administered (Zero dose)"

    # Base totals
    total_doses = pd.to_numeric(filtered_df[col_total_doses], errors='coerce').sum()
    total_zero_doses = pd.to_numeric(filtered_df[col_zero_doses], errors='coerce').sum()

    # Response specific filtered dataframes
    vit_a_df = filtered_df[response_series.str.contains("Vitamin A", case=False, na=False)]
    mr_df = filtered_df[response_series.str.contains("Measles|MR", case=False, na=False)]

    # Calculate Total Vitamin A Response
    vit_a_total = 0
    if vit_a_target_cols:
        for c in vit_a_target_cols:
            vit_a_total += pd.to_numeric(vit_a_df[c], errors='coerce').sum()

    # Calculate Total MR Response
    mr_total = 0
    if all_mr_cols:
        for c in all_mr_cols:
            mr_total += pd.to_numeric(mr_df[c], errors='coerce').sum()

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
        vit_a_df_clean['Daily_Vit_A_Total'] = vit_a_df_clean[vit_a_target_cols].apply(
            pd.to_numeric, errors='coerce'
        ).sum(axis=1)
        daily_vit_a = vit_a_df_clean.groupby(vit_a_df_clean[col_date].dt.date)['Daily_Vit_A_Total'].sum().reset_index()

    daily_mr = pd.DataFrame()
    if all_mr_cols and not mr_df.empty:
        mr_df_clean = mr_df.dropna(subset=[col_date]).copy()
        mr_df_clean['Daily_MR_Total'] = mr_df_clean[all_mr_cols].apply(
            pd.to_numeric, errors='coerce'
        ).sum(axis=1)
        daily_mr = mr_df_clean.groupby(mr_df_clean[col_date].dt.date)['Daily_MR_Total'].sum().reset_index()

    if not daily_vit_a.empty or not daily_mr.empty:
        daily_trend_df = pd.merge(daily_vit_a, daily_mr, on=col_date, how='outer').fillna(0)
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
        st.info("No daily date data available to render line chart trends.")

    st.divider()

    # --- SECTION 2: OVERALL METRIC SUMMARY ---
    st.header("Overall Metric Summary")
    col_summary1, col_summary2, col_summary3 = st.columns(3)

    # 1. Vitamin A Summary Chart
    with col_summary1:
        if vit_a_target_cols:
            vit_a_totals = []
            for col in vit_a_target_cols:
                val = pd.to_numeric(vit_a_df[col], errors='coerce').sum()
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
                val = pd.to_numeric(mr_df[col], errors='coerce').sum()
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
                val = pd.to_numeric(mr_df[col], errors='coerce').sum()
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

    if not filtered_target_df.empty:
        def safe_get_target_col(df, pos_idx, preferred_name_keyword):
            if len(df.columns) > pos_idx and preferred_name_keyword.lower() in df.columns[pos_idx].lower():
                return df.columns[pos_idx]
            matched = [c for c in df.columns if preferred_name_keyword.lower() in c.lower()]
            return matched[0] if matched else None

        col_t_6_59 = safe_get_target_col(filtered_target_df, 5, "6 - 59")
        col_t_6_12 = safe_get_target_col(filtered_target_df, 8, "6 - 12")
        col_t_13_23 = safe_get_target_col(filtered_target_df, 11, "13 - 23")
        col_t_24_59 = safe_get_target_col(filtered_target_df, 14, "24 - 59")

        t_val_6_12 = pd.to_numeric(filtered_target_df[col_t_6_12], errors='coerce').sum() if col_t_6_12 else 0
        t_val_13_23 = pd.to_numeric(filtered_target_df[col_t_13_23], errors='coerce').sum() if col_t_13_23 else 0
        
        # Target totals override logic
        if len(filtered_target_df) == len(df_target_raw):
            t_val_24_59 = 16910
            t_val_6_59 = 25335
        else:
            raw_t_24_59 = pd.to_numeric(df_target_raw[col_t_24_59], errors='coerce').sum() if col_t_24_59 else 1
            filter_t_24_59 = pd.to_numeric(filtered_target_df[col_t_24_59], errors='coerce').sum() if col_t_24_59 else 0
            t_val_24_59 = int(round((filter_t_24_59 / raw_t_24_59) * 16910)) if raw_t_24_59 > 0 else 16910

            raw_t_6_59 = pd.to_numeric(df_target_raw[col_t_6_59], errors='coerce').sum() if col_t_6_59 else 1
            filter_t_6_59 = pd.to_numeric(filtered_target_df[col_t_6_59], errors='coerce').sum() if col_t_6_59 else 0
            t_val_6_59 = int(round((filter_t_6_59 / raw_t_6_59) * 25335)) if raw_t_6_59 > 0 else 25335

        cols_acc_6_12 = [c for c in dose_cols if any(kw in c for kw in ["6-12", "6 - 12", "6-11", "6 - 11"])]
        cols_acc_13_23 = [c for c in dose_cols if any(kw in c for kw in ["13-23", "13 - 23", "12-23"])]
        cols_acc_24_59 = [c for c in dose_cols if any(kw in c for kw in ["24-59", "24 - 59"])]

        acc_val_6_12 = filtered_df[cols_acc_6_12].apply(pd.to_numeric, errors='coerce').sum().sum() if cols_acc_6_12 else 0
        acc_val_13_23 = filtered_df[cols_acc_13_23].apply(pd.to_numeric, errors='coerce').sum().sum() if cols_acc_13_23 else 0
        acc_val_24_59 = filtered_df[cols_acc_24_59].apply(pd.to_numeric, errors='coerce').sum().sum() if cols_acc_24_59 else 0
        acc_val_6_59 = acc_val_6_12 + acc_val_13_23 + acc_val_24_59

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

        # Row 1: Age Brackets (6-12 mos, 13-23 mos, 24-59 mos side-by-side)
        g_row1_col1, g_row1_col2, g_row1_col3 = st.columns(3)

        with g_row1_col1:
            st.plotly_chart(
                create_gauge_chart("6 - 12 mos Total [Col I]", acc_val_6_12, int(t_val_6_12)), 
                use_container_width=True
            )

        with g_row1_col2:
            st.plotly_chart(
                create_gauge_chart("13 - 23 mos Total [Col L]", acc_val_13_23, int(t_val_13_23)), 
                use_container_width=True
            )

        with g_row1_col3:
            st.plotly_chart(
                create_gauge_chart("24 - 59 mos Total [Col O]", acc_val_24_59, int(t_val_24_59)), 
                use_container_width=True
            )

        # Row 2: Larger overall summary chart (6-59 mos)
        st.markdown("<br>", unsafe_allow_html=True)
        st.plotly_chart(
            create_gauge_chart(
                "Overall Target: 6 - 59 mos Total [Col F]", 
                acc_val_6_59, 
                int(t_val_6_59), 
                height=420, 
                font_size=18, 
                is_large=True
            ), 
            use_container_width=True
        )

    else:
        st.info("The 'Target' worksheet could not be loaded or contains no rows.")

    st.divider()

    # --- SECTION 4: DHC ACCOMPLISHMENT DATA SUMMARY ---
    st.header("DHC Accomplishment Data Summary")
    
    dhc_col1, dhc_col2 = st.columns(2)

    # 1. Measles-Rubella Table & Chart
    with dhc_col1:
        st.subheader("Measles-Rubella (MR) by Bakuna Center")
        if not mr_df.empty:
            dhc_mr_df = mr_df.copy()
            
            dhc_mr_df['MR_6_12'] = pd.to_numeric(dhc_mr_df[col_mr_6_12], errors='coerce').fillna(0)
            dhc_mr_df['MR_13_23'] = pd.to_numeric(dhc_mr_df[col_mr_13_23], errors='coerce').fillna(0)
            dhc_mr_df['MR_24_59'] = pd.to_numeric(dhc_mr_df[col_mr_24_59], errors='coerce').fillna(0)

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

            # Export Button for MR Summary
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
            st.info("No Measles-Rubella data available for table aggregation.")

    # 2. Vitamin A Table & Chart
    with dhc_col2:
        st.subheader("Vitamin A by Bakuna Center")
        if not vit_a_df.empty:
            dhc_vit_df = vit_a_df.copy()

            dhc_vit_df['Vit_6_11'] = pd.to_numeric(dhc_vit_df[col_vit_6_11], errors='coerce').fillna(0)
            dhc_vit_df['Vit_12_59'] = pd.to_numeric(dhc_vit_df[col_vit_12_59], errors='coerce').fillna(0)

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

            # Export Button for Vitamin A Summary
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
            st.info("No Vitamin A data available for table aggregation.")

    st.divider()

    # --- SECTION 5: BARANGAY ACCOMPLISHMENT TABLE HEATMAP ---
    st.header("Barangay Accomplishment Table Heatmap")

    # Define exact columns requested:
    heatmap_mr_cols = [col_mr_6_12, col_mr_13_23, col_mr_24_59]
    heatmap_vit_cols = [col_vit_6_11, col_vit_12_59]

    bgy_summary_records = []
    
    # Use the filtered barangay list so heatmap stays aligned with filters
    heatmap_barangays = selected_barangay if selected_barangay else barangays

    for bgy in heatmap_barangays:
        bgy_data = filtered_df[filtered_df[col_barangay].astype(str) == bgy]
        
        mr_doses_val = bgy_data[heatmap_mr_cols].apply(pd.to_numeric, errors='coerce').sum().sum()
        vit_a_val = bgy_data[heatmap_vit_cols].apply(pd.to_numeric, errors='coerce').sum().sum()

        bgy_summary_records.append({
            "Barangay": bgy,
            "MR (Cols K-M)": int(mr_doses_val),
            "Vitamin A (Cols Q-R)": int(vit_a_val),
            "Total Accomplishment": int(mr_doses_val + vit_a_val)
        })

    heatmap_df = pd.DataFrame(bgy_summary_records)
    heatmap_df = heatmap_df.sort_values(by="Total Accomplishment", ascending=False)

    if not heatmap_df.empty:
        # Export Button for Barangay Accomplishment Heatmap Data
        st.download_button(
            label="📥 Export Barangay Accomplishment Data (CSV)",
            data=convert_df_to_csv(heatmap_df),
            file_name="barangay_accomplishment_summary.csv",
            mime="text/csv",
            key="download_bgy_heatmap_data"
        )

        # Melt DataFrame for Plotly Heatmap
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

        dynamic_height = max(500, len(heatmap_df) * 22)
        fig_table_heatmap.update_layout(
            xaxis_title="Vaccination Category",
            yaxis_title="Barangay Name",
            height=dynamic_height,
            coloraxis_colorbar=dict(title="Doses"),
            margin=dict(l=10, r=10, t=50, b=20)
        )
        st.plotly_chart(fig_table_heatmap, use_container_width=True)
    else:
        st.info("No barangay accomplishment data available to render table heatmap.")

    st.divider()

    # --- SECTION 6: BARANGAY BREAKDOWN CHARTS (PIE CHARTS) ---
    st.header("Accomplishment Share by Barangay")
    b_left_col, b_right_col = st.columns(2)

    with b_left_col:
        st.subheader("Vitamin A Distribution by Barangay")
        if vit_a_target_cols and not vit_a_df.empty:
            vit_a_bgy_df = vit_a_df.copy()
            vit_a_bgy_df['Total_Vit_A'] = vit_a_bgy_df[vit_a_target_cols].apply(
                pd.to_numeric, errors='coerce'
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
                st.info("No Vitamin A data recorded for the selected barangays.")

    with b_right_col:
        st.subheader("Measles-Rubella (MR) Distribution by Barangay")
        if mr_dose_cols and not mr_df.empty:
            mr_bgy_df = mr_df.copy()
            mr_bgy_df['Total_MR_Doses'] = mr_bgy_df[mr_dose_cols].apply(
                pd.to_numeric, errors='coerce'
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

        if mr_zero_cols and not mr_df.empty:
            mr_zero_bgy_df = mr_df.copy()
            mr_zero_bgy_df['Total_MR_Zero'] = mr_zero_bgy_df[mr_zero_cols].apply(
                pd.to_numeric, errors='coerce'
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

    total_deferrals_val = pd.to_numeric(filtered_df[col_deferrals], errors='coerce').sum() if col_deferrals else 0
    total_refusals_val = pd.to_numeric(filtered_df[col_refusals], errors='coerce').sum() if col_refusals else 0

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
            cnt = pd.to_numeric(filtered_df[col], errors='coerce').sum()
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
            cnt = pd.to_numeric(filtered_df[col], errors='coerce').sum()
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

else:
    st.warning("Unable to fetch data. Please check the spreadsheet URL or permissions.")
