import streamlit as st
import pandas as pd
import plotly.express as px

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="BAGUIO SIA Accomplishment",
    layout="wide"
)

st.title("BAGUIO SIA Accomplishment Dashboard")

# --- DATA LOADING ---
SHEET_ID = "1Gh1LYOgacvRs_QwNa7xFHAGyfTzquQ0exqe3VOOYANs"
CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"

@st.cache_data(ttl=600)
def load_data():
    try:
        df = pd.read_csv(CSV_URL)
        # Fix: Ensure all column headers are strings before stripping spaces
        df.columns = df.columns.astype(str).str.strip()
        
        # Convert Column I (Vaccination Date - 0-indexed column 8) to datetime
        date_col = df.columns[8] 
        df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
        
        return df
    except Exception as e:
        st.error(f"Error loading data from Google Sheets: {e}")
        return pd.DataFrame()

df_raw = load_data()

if not df_raw.empty:
    # Identify key columns by position
    col_bakuna = df_raw.columns[5]    # Column F (Bakuna Center Name)
    col_barangay = df_raw.columns[7]  # Column H (Barangay Name)
    col_date = df_raw.columns[8]      # Column I (Vaccination Date)
    col_response = df_raw.columns[9]  # Column J (Response Type)

    # List of dose metrics columns (Column K onwards)
    dose_cols = df_raw.columns[10:].tolist()

    # --- SIDEBAR FILTERS ---
    st.sidebar.header("Filter Options")

    # Filter 1: Bakuna Center Name [Column F]
    bakuna_centers = sorted(df_raw[col_bakuna].dropna().astype(str).unique().tolist())
    selected_bakuna = st.sidebar.multiselect("Bakuna Center Name", bakuna_centers)

    # Filter 2: Barangay Name [Column H]
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

    # --- APPLY FILTERS ---
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

    # Convert response column safely to string
    response_series = filtered_df[col_response].astype(str)

    # --- TARGET COLUMNS SELECTION ---
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

    # Combine MR Doses and MR Zero Doses into one complete MR metric list
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

    # Calculate Total MR Response (MR Doses + MR Zero Doses)
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

    # --- SECTION 1: OVERALL METRIC SUMMARY CHARTS ---
    st.header("Overall Metric Summary")
    left_col, right_col = st.columns(2)

    # LEFT COLUMN: Vitamin A
    with left_col:
        st.subheader("Vitamin A Response")

        if vit_a_target_cols:
            vit_a_totals = []
            for col in vit_a_target_cols:
                val = pd.to_numeric(vit_a_df[col], errors='coerce').sum()
                vit_a_totals.append({"Metric": col, "Total Administered": int(val)})

            chart_data_vit_a = pd.DataFrame(vit_a_totals)

            fig_vit_a = px.bar(
                chart_data_vit_a,
                x="Metric",
                y="Total Administered",
                color="Metric",
                text="Total Administered",
                title="Vitamin A Coverage",
                color_discrete_sequence=px.colors.qualitative.Set2
            )
            fig_vit_a.update_layout(xaxis_title="", yaxis_title="Total Administered", showlegend=False)
            st.plotly_chart(fig_vit_a, use_container_width=True)
        else:
            st.info("No Vitamin A columns found.")

    # RIGHT COLUMN: Measles-Rubella (MR)
    with right_col:
        st.subheader("Measles-Rubella (MR) Response")

        if mr_dose_cols:
            mr_totals = []
            for col in mr_dose_cols:
                val = pd.to_numeric(mr_df[col], errors='coerce').sum()
                mr_totals.append({"Age Group": col, "Total Administered": int(val)})

            chart_data_mr = pd.DataFrame(mr_totals)

            fig_mr = px.bar(
                chart_data_mr,
                x="Age Group",
                y="Total Administered",
                color="Age Group",
                text="Total Administered",
                title="MR Doses Administered by Age Group",
                color_discrete_sequence=px.colors.qualitative.Pastel
            )
            fig_mr.update_layout(xaxis_title="", yaxis_title="Total Administered", showlegend=False)
            st.plotly_chart(fig_mr, use_container_width=True)

        if mr_zero_cols:
            mr_zero_totals = []
            for col in mr_zero_cols:
                val = pd.to_numeric(mr_df[col], errors='coerce').sum()
                mr_zero_totals.append({"Age Group": col, "Total Administered": int(val)})

            chart_data_mr_zero = pd.DataFrame(mr_zero_totals)

            fig_mr_zero = px.bar(
                chart_data_mr_zero,
                x="Age Group",
                y="Total Administered",
                color="Age Group",
                text="Total Administered",
                title="MR Zero Doses Administered by Age Group",
                color_discrete_sequence=px.colors.qualitative.Safe
            )
            fig_mr_zero.update_layout(xaxis_title="", yaxis_title="Total Administered", showlegend=False)
            st.plotly_chart(fig_mr_zero, use_container_width=True)

    st.divider()

    # --- SECTION 2: BARANGAY BREAKDOWN CHARTS ---
    st.header("Accomplishment by Barangay")
    b_left_col, b_right_col = st.columns(2)

    # BARANGAY - LEFT COLUMN: Vitamin A
    with b_left_col:
        st.subheader("Vitamin A by Barangay")
        if vit_a_target_cols and not vit_a_df.empty:
            vit_a_bgy = vit_a_df.groupby(col_barangay)[vit_a_target_cols].apply(
                lambda x: x.apply(pd.to_numeric, errors='coerce').sum()
            ).reset_index()

            vit_a_bgy_melted = vit_a_bgy.melt(
                id_vars=[col_barangay],
                value_vars=vit_a_target_cols,
                var_name="Age Group",
                value_name="Total Administered"
            )

            fig_bgy_vit_a = px.bar(
                vit_a_bgy_melted,
                x=col_barangay,
                y="Total Administered",
                color="Age Group",
                barmode="group",
                text="Total Administered",
                title="Vitamin A Coverage per Barangay",
                color_discrete_sequence=px.colors.qualitative.Set2
            )
            fig_bgy_vit_a.update_layout(xaxis_title="Barangay", yaxis_title="Total Administered")
            st.plotly_chart(fig_bgy_vit_a, use_container_width=True)

    # BARANGAY - RIGHT COLUMN: Measles-Rubella (MR)
    with b_right_col:
        st.subheader("Measles-Rubella (MR) by Barangay")
        if mr_dose_cols and not mr_df.empty:
            mr_bgy = mr_df.groupby(col_barangay)[mr_dose_cols].apply(
                lambda x: x.apply(pd.to_numeric, errors='coerce').sum()
            ).reset_index()

            mr_bgy_melted = mr_bgy.melt(
                id_vars=[col_barangay],
                value_vars=mr_dose_cols,
                var_name="Age Group",
                value_name="Total Administered"
            )

            fig_bgy_mr = px.bar(
                mr_bgy_melted,
                x=col_barangay,
                y="Total Administered",
                color="Age Group",
                barmode="group",
                text="Total Administered",
                title="MR Doses Administered per Barangay",
                color_discrete_sequence=px.colors.qualitative.Pastel
            )
            fig_bgy_mr.update_layout(xaxis_title="Barangay", yaxis_title="Total Administered")
            st.plotly_chart(fig_bgy_mr, use_container_width=True)

        if mr_zero_cols and not mr_df.empty:
            mr_zero_bgy = mr_df.groupby(col_barangay)[mr_zero_cols].apply(
                lambda x: x.apply(pd.to_numeric, errors='coerce').sum()
            ).reset_index()

            mr_zero_bgy_melted = mr_zero_bgy.melt(
                id_vars=[col_barangay],
                value_vars=mr_zero_cols,
                var_name="Age Group",
                value_name="Total Administered"
            )

            fig_bgy_mr_zero = px.bar(
                mr_zero_bgy_melted,
                x=col_barangay,
                y="Total Administered",
                color="Age Group",
                barmode="group",
                text="Total Administered",
                title="MR Zero Doses Administered per Barangay",
                color_discrete_sequence=px.colors.qualitative.Safe
            )
            fig_bgy_mr_zero.update_layout(xaxis_title="Barangay", yaxis_title="Total Administered")
            st.plotly_chart(fig_bgy_mr_zero, use_container_width=True)

    st.divider()

    # --- SECTION 3: DAILY RESPONSE TRENDS (LINE CHART) ---
    st.header("Daily Response Trends")

    # Group Vitamin A data by Date
    daily_vit_a = pd.DataFrame()
    if vit_a_target_cols and not vit_a_df.empty:
        vit_a_df_clean = vit_a_df.dropna(subset=[col_date]).copy()
        vit_a_df_clean['Daily_Vit_A_Total'] = vit_a_df_clean[vit_a_target_cols].apply(
            pd.to_numeric, errors='coerce'
        ).sum(axis=1)
        daily_vit_a = vit_a_df_clean.groupby(vit_a_df_clean[col_date].dt.date)['Daily_Vit_A_Total'].sum().reset_index()

    # Group MR data by Date
    daily_mr = pd.DataFrame()
    if all_mr_cols and not mr_df.empty:
        mr_df_clean = mr_df.dropna(subset=[col_date]).copy()
        mr_df_clean['Daily_MR_Total'] = mr_df_clean[all_mr_cols].apply(
            pd.to_numeric, errors='coerce'
        ).sum(axis=1)
        daily_mr = mr_df_clean.groupby(mr_df_clean[col_date].dt.date)['Daily_MR_Total'].sum().reset_index()

    # Merge Daily Totals into a single DataFrame for Plotly
    if not daily_vit_a.empty or not daily_mr.empty:
        daily_trend_df = pd.merge(daily_vit_a, daily_mr, on=col_date, how='outer').fillna(0)
        daily_trend_df = daily_trend_df.sort_values(by=col_date)

        # Melt data for Plotly multi-line rendering
        daily_melted = daily_trend_df.melt(
            id_vars=[col_date],
            value_vars=['Daily_Vit_A_Total', 'Daily_MR_Total'],
            var_name='Response Type',
            value_name='Total Administered'
        )

        # Map clean display names for the legend
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
                'Vitamin A Response': '#2ca02c',          # Green line
                'Measles-Rubella (MR) Response': '#1f77b4'  # Blue line
            }
        )
        fig_line.update_layout(
            xaxis_title="Date",
            yaxis_title="Total Administered",
            hovermode="x unified"
        )
        st.plotly_chart(fig_line, use_container_width=True)
    else:
        st.info("No daily date data available to render line chart trends.")

else:
    st.warning("Unable to fetch data. Please check the spreadsheet URL or permissions.")
