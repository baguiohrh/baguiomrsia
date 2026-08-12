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

# Main accomplishments sheet CSV URL
CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"
# Target sheet CSV URL (using gviz endpoint for reliable tab name export)
TARGET_CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Target"

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
        # Fallback to secondary URL parameter format
        try:
            alt_url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&sheet=Target"
            df_target = pd.read_csv(alt_url)
            df_target.columns = df_target.columns.astype(str).str.strip()
            return df_target
        except Exception as alt_e:
            st.warning(f"Note: Could not load 'Target' sheet. Details: {alt_e}")
            return pd.DataFrame()

df_raw = load_data()
df_target_raw = load_target_data()

if not df_raw.empty:
    # Identify key columns by position in main sheet
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

    # --- SECTION 1: DAILY RESPONSE TRENDS (MOVED TO FIRST PART) ---
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

    # --- SECTION 2: OVERALL METRIC SUMMARY (COMPACT SINGLE-ROW VIEW) ---
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
            if len(df.columns) > pos_idx:
                return df.columns[pos_idx]
            matched = [c for c in df.columns if preferred_name_keyword.lower() in c.lower()]
            return matched[0] if matched else None

        col_t_6_59 = safe_get_target_col(filtered_target_df, 5, "6 - 59 months Total")
        col_t_6_12 = safe_get_target_col(filtered_target_df, 8, "6 - 12 months Total")
        col_t_13_23 = safe_get_target_col(filtered_target_df, 11, "13 - 23 months Total")
        col_t_24_59 = safe_get_target_col(filtered_target_df, 14, "24 - 59 months Total")

        t_val_6_12 = pd.to_numeric(filtered_target_df[col_t_6_12], errors='coerce').sum() if col_t_6_12 else 0
        t_val_13_23 = pd.to_numeric(filtered_target_df[col_t_13_23], errors='coerce').sum() if col_t_13_23 else 0
        t_val_24_59 = pd.to_numeric(filtered_target_df[col_t_24_59], errors='coerce').sum() if col_t_24_59 else 0
        t_val_6_59 = pd.to_numeric(filtered_target_df[col_t_6_59], errors='coerce').sum() if col_t_6_59 else 0

        cols_acc_6_12 = [c for c in dose_cols if any(kw in c for kw in ["6-12", "6 - 12", "6-11", "6 - 11"])]
        cols_acc_13_23 = [c for c in dose_cols if any(kw in c for kw in ["13-23", "13 - 23", "12-23"])]
        cols_acc_24_59 = [c for c in dose_cols if any(kw in c for kw in ["24-59", "24 - 59"])]

        acc_val_6_12 = filtered_df[cols_acc_6_12].apply(pd.to_numeric, errors='coerce').sum().sum() if cols_acc_6_12 else 0
        acc_val_13_23 = filtered_df[cols_acc_13_23].apply(pd.to_numeric, errors='coerce').sum().sum() if cols_acc_13_23 else 0
        acc_val_24_59 = filtered_df[cols_acc_24_59].apply(pd.to_numeric, errors='coerce').sum().sum() if cols_acc_24_59 else 0
        acc_val_6_59 = acc_val_6_12 + acc_val_13_23 + acc_val_24_59

        target_summary_data = [
            {"Title": "6 - 12 mos Total [Col I]", "Target": int(t_val_6_12), "Accomplishment": int(acc_val_6_12)},
            {"Title": "13 - 23 mos Total [Col L]", "Target": int(t_val_13_23), "Accomplishment": int(acc_val_13_23)},
            {"Title": "24 - 59 mos Total [Col O]", "Target": int(t_val_24_59), "Accomplishment": int(acc_val_24_59)},
            {"Title": "6 - 59 mos Total [Col F]", "Target": int(t_val_6_59), "Accomplishment": int(acc_val_6_59)},
        ]

        def create_gauge_chart(title, accomplishment, target):
            pct = round((accomplishment / target * 100), 1) if target > 0 else 0
            max_axis_val = max(target, accomplishment) * 1.15 if target > 0 else 100

            fig = go.Figure(go.Indicator(
                mode="gauge+number+delta",
                value=accomplishment,
                number={'valueformat': ',d'},
                domain={'x': [0.05, 0.95], 'y': [0.05, 0.70]},
                title={
                    'text': f"<b>{title}</b><br><span style='font-size:0.85em;color:#475569'>{pct}% of Target ({target:,})</span>", 
                    'font': {'size': 14},
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
                height=320,
                margin=dict(l=35, r=35, t=60, b=40)
            )
            return fig

        g_col1, g_col2 = st.columns(2, gap="large")
        
        with g_col1:
            st.plotly_chart(
                create_gauge_chart(target_summary_data[0]["Title"], target_summary_data[0]["Accomplishment"], target_summary_data[0]["Target"]), 
                use_container_width=True
            )
            st.markdown("<br>", unsafe_allow_html=True)
            st.plotly_chart(
                create_gauge_chart(target_summary_data[2]["Title"], target_summary_data[2]["Accomplishment"], target_summary_data[2]["Target"]), 
                use_container_width=True
            )

        with g_col2:
            st.plotly_chart(
                create_gauge_chart(target_summary_data[1]["Title"], target_summary_data[1]["Accomplishment"], target_summary_data[1]["Target"]), 
                use_container_width=True
            )
            st.markdown("<br>", unsafe_allow_html=True)
            st.plotly_chart(
                create_gauge_chart(target_summary_data[3]["Title"], target_summary_data[3]["Accomplishment"], target_summary_data[3]["Target"]), 
                use_container_width=True
            )

    else:
        st.info("The 'Target' worksheet could not be loaded or contains no rows. Ensure the Google Sheet tab is named 'Target' and is shared publicly.")

    st.divider()

    # --- SECTION 4: BARANGAY BREAKDOWN CHARTS (PIE CHARTS) ---
    st.header("Accomplishment by Barangay")
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

else:
    st.warning("Unable to fetch data. Please check the spreadsheet URL or permissions.")
