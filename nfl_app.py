import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import os

# ============================================================
# CONFIG
# ============================================================
st.set_page_config(
    page_title="NFL Game Pass International Survey",
    page_icon="🏈",
    layout="wide",
    initial_sidebar_state="expanded"
)

MARKET_COLORS = {
    "Global Average": "#2c3e50",
    "Australia": "#27ae60",
    "Brazil": "#f1c40f",
    "DACH": "#e74c3c",
    "France": "#3498db",
    "Italy": "#2ecc71",
    "Japan": "#e91e63",
    "Mexico": "#00897b",
    "RoW": "#95a5a6",
    "Spain": "#ff5722",
    "United Kingdom": "#9b59b6"
}


# ============================================================
# DATA LOADING
# ============================================================
@st.cache_data
def load_data(file):
    if isinstance(file, str):
        if file.endswith(".xlsx"):
            df = pd.read_excel(file, skiprows=2)
        else:
            df = pd.read_csv(file, skiprows=2)
    else:
        if file.name.endswith(".xlsx"):
            df = pd.read_excel(file, skiprows=2)
        else:
            df = pd.read_csv(file, skiprows=2)

    df.columns = df.columns.str.strip()

    col_lower = {c.lower(): c for c in df.columns}

    question_col = None
    response_col = None

    for key, val in col_lower.items():
        if "question" in key:
            question_col = val
        if "response" in key:
            response_col = val

    if question_col is None:
        question_col = df.columns[0]
    if response_col is None:
        response_col = df.columns[1]

    df = df.rename(columns={question_col: "Question", response_col: "Response"})

    df["Question"] = df["Question"].ffill()

    df = df.dropna(subset=["Response"], how="all")
    df = df[df["Response"].notna()]
    df["Response"] = df["Response"].astype(str).str.strip()

    df = df[df["Response"].str.lower() != "base (answered)"]

    market_cols = [c for c in df.columns if "%" in c and "total" not in c.lower()]

    for col in market_cols:
        df[col] = df[col].astype(str).str.replace("%", "").str.strip()
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df["Question"] = df["Question"].astype(str).str.strip()

    market_display = {}
    for col in market_cols:
        clean_name = col.replace(" %", "").replace("%", "").strip()
        market_display[col] = clean_name

    return df, market_cols, market_display


# ============================================================
# HELPER FUNCTIONS
# ============================================================
def calculate_nps(df, market_cols, market_display):
    nps_q = df[df["Response"].isin(["Detractor", "Passive", "Promoter"])]

    if len(nps_q) == 0:
        return None

    recommend_q = nps_q[nps_q["Question"].str.lower().str.contains("recommend", na=False)]
    if len(recommend_q) == 0:
        recommend_q = nps_q

    nps_scores = {}
    for col in market_cols:
        promoter = recommend_q[recommend_q["Response"] == "Promoter"][col].values
        detractor = recommend_q[recommend_q["Response"] == "Detractor"][col].values
        if len(promoter) > 0 and len(detractor) > 0:
            if pd.notna(promoter[0]) and pd.notna(detractor[0]):
                nps_scores[market_display.get(col, col)] = round(promoter[0] - detractor[0], 1)

    return nps_scores


def calculate_csat(df, market_cols, market_display):
    sat_q = df[df["Question"].str.lower().str.contains("satisfied", na=False)]
    sat_categorical = sat_q[sat_q["Response"].isin(["Detractor", "Passive", "Promoter"])]

    if len(sat_categorical) == 0:
        return None

    csat_scores = {}
    for col in market_cols:
        promoter = sat_categorical[sat_categorical["Response"] == "Promoter"][col].values
        detractor = sat_categorical[sat_categorical["Response"] == "Detractor"][col].values
        if len(promoter) > 0 and len(detractor) > 0:
            if pd.notna(promoter[0]) and pd.notna(detractor[0]):
                csat_scores[market_display.get(col, col)] = round(promoter[0] - detractor[0], 1)

    return csat_scores


def get_market_nps(df, col):
    recommend_q = df[df["Question"].str.lower().str.contains("recommend", na=False)]
    categorical = recommend_q[recommend_q["Response"].isin(["Detractor", "Passive", "Promoter"])]
    if len(categorical) == 0:
        return None
    promoter = categorical[categorical["Response"] == "Promoter"][col].values
    detractor = categorical[categorical["Response"] == "Detractor"][col].values
    if len(promoter) > 0 and len(detractor) > 0:
        if pd.notna(promoter[0]) and pd.notna(detractor[0]):
            return round(promoter[0] - detractor[0], 1)
    return None


def get_market_csat(df, col):
    sat_q = df[df["Question"].str.lower().str.contains("satisfied", na=False)]
    categorical = sat_q[sat_q["Response"].isin(["Detractor", "Passive", "Promoter"])]
    if len(categorical) == 0:
        return None
    promoter = categorical[categorical["Response"] == "Promoter"][col].values
    detractor = categorical[categorical["Response"] == "Detractor"][col].values
    if len(promoter) > 0 and len(detractor) > 0:
        if pd.notna(promoter[0]) and pd.notna(detractor[0]):
            return round(promoter[0] - detractor[0], 1)
    return None


# ============================================================
# SIDEBAR & DATA LOADING
# ============================================================
st.sidebar.title("🏈 NFL GPI Survey")
st.sidebar.markdown("---")

DATA_FILE = "NFL Survey Data.xlsx"

if os.path.exists(DATA_FILE):
    df, market_cols, market_display = load_data(DATA_FILE)
else:
    uploaded_file = st.sidebar.file_uploader("Upload Survey Data", type=["csv", "xlsx"])
    if uploaded_file is None:
        st.title("🏈 NFL Game Pass International Survey Dashboard")
        st.info("👈 Upload your survey CSV or Excel file in the sidebar to get started.")
        st.stop()
    df, market_cols, market_display = load_data(uploaded_file)

available_markets = [market_display[col] for col in market_cols]
display_to_col = {v: k for k, v in market_display.items()}

st.sidebar.markdown("---")
questions_list = df["Question"].unique().tolist()
st.sidebar.markdown(f"**Questions loaded:** {len(questions_list)}")
st.sidebar.markdown(f"**Markets available:** {len(available_markets)}")


# ============================================================
# TABS
# ============================================================
st.title("🏈 NFL Game Pass International Survey")
st.markdown("*Insights from NFL GPI subscriber survey across global markets*")

tab_names = ["📊 All Markets"] + [f"🌍 {m}" for m in available_markets if "global" not in m.lower()]
tabs = st.tabs(tab_names)


# ============================================================
# TAB 1: ALL MARKETS
# ============================================================
with tabs[0]:
    st.markdown("---")

    selected_market_names = st.multiselect(
        "Select Markets to Compare",
        options=available_markets,
        default=available_markets,
        key="all_markets_filter"
    )
    selected_cols = [display_to_col[m] for m in selected_market_names if m in display_to_col]

    # NPS & CSAT Overview
    nps_scores = calculate_nps(df, market_cols, market_display)
    csat_scores = calculate_csat(df, market_cols, market_display)

    col_nps, col_csat = st.columns(2)

    with col_nps:
        if nps_scores:
            st.header("📊 NPS — Likelihood to Recommend")
            filtered_nps = {k: v for k, v in nps_scores.items() if k in selected_market_names}

            if filtered_nps:
                nps_df = pd.DataFrame([
                    {"Market": k, "NPS": v} for k, v in filtered_nps.items()
                ]).sort_values("NPS", ascending=True)

                fig_nps = px.bar(
                    nps_df, x="NPS", y="Market", orientation="h",
                    color="NPS",
                    color_continuous_scale=["#e74c3c", "#f39c12", "#2ecc71"],
                    color_continuous_midpoint=0
                )
                fig_nps.update_traces(texttemplate='%{x:.1f}', textposition='outside', textfont_size=10)
                fig_nps.update_layout(
                    margin=dict(t=20, b=20),
                    yaxis_title="", xaxis_title="Net Promoter Score",
                    coloraxis_showscale=False,
                    height=400
                )
                fig_nps.add_vline(x=0, line_dash="dash", line_color="gray")
                st.plotly_chart(fig_nps, use_container_width=True, key="all_nps_overview")

    with col_csat:
        if csat_scores:
            st.header("⭐ CSAT — Overall Satisfaction")
            filtered_csat = {k: v for k, v in csat_scores.items() if k in selected_market_names}

            if filtered_csat:
                csat_df = pd.DataFrame([
                    {"Market": k, "CSAT": v} for k, v in filtered_csat.items()
                ]).sort_values("CSAT", ascending=True)

                fig_csat = px.bar(
                    csat_df, x="CSAT", y="Market", orientation="h",
                    color="CSAT",
                    color_continuous_scale=["#e74c3c", "#f39c12", "#2ecc71"],
                    color_continuous_midpoint=0
                )
                fig_csat.update_traces(texttemplate='%{x:.1f}', textposition='outside', textfont_size=10)
                fig_csat.update_layout(
                    margin=dict(t=20, b=20),
                    yaxis_title="", xaxis_title="CSAT Score (Promoter % - Detractor %)",
                    coloraxis_showscale=False,
                    height=400
                )
                fig_csat.add_vline(x=0, line_dash="dash", line_color="gray")
                st.plotly_chart(fig_csat, use_container_width=True, key="all_csat_overview")

    st.markdown("---")

    # Fandom Profile
    st.header("🏟️ Fandom Profile")

    fandom_keywords = ["how much of a fan", "how long have you been", "how closely you follow"]
    fandom_questions = df[df["Question"].str.lower().apply(
        lambda x: any(kw in x for kw in fandom_keywords)
    )]["Question"].unique().tolist()

    if len(fandom_questions) > 0:
        selected_fandom_q = st.selectbox(
            "Select Fandom Question",
            options=fandom_questions,
            key="all_fandom_q"
        )

        q_data = df[df["Question"] == selected_fandom_q].copy()

        melted = q_data.melt(
            id_vars=["Response"],
            value_vars=selected_cols,
            var_name="Market_Col",
            value_name="Percentage"
        )
        melted["Market"] = melted["Market_Col"].map(market_display)
        melted = melted.dropna(subset=["Percentage"])

        fig_fandom = px.bar(
            melted, x="Response", y="Percentage", color="Market",
            barmode="group",
            color_discrete_map=MARKET_COLORS,
            height=600
        )
        if len(selected_market_names) <= 4:
            fig_fandom.update_traces(texttemplate='%{y:.1f}%', textposition='outside', textfont_size=9)
        fig_fandom.update_layout(
            xaxis_title="", yaxis_title="Percentage (%)",
            xaxis_tickangle=-45, margin=dict(t=40, b=100),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5)
        )
        st.plotly_chart(fig_fandom, use_container_width=True, key="all_fandom_chart")

    st.markdown("---")

    # Heatmap
    st.header("🔥 Market Heatmap")
    st.markdown("*Compare responses across all markets at a glance — darker = higher %*")

    selected_question_heat = st.selectbox(
        "Select Question for Heatmap",
        options=questions_list,
        key="all_heatmap_q"
    )

    heat_data = df[df["Question"] == selected_question_heat].copy()
    if len(heat_data) > 0 and len(selected_cols) > 0:
        heat_matrix = heat_data.set_index("Response")[selected_cols].copy()
        heat_matrix.columns = [market_display.get(c, c) for c in heat_matrix.columns]
        heat_matrix = heat_matrix.dropna(how="all")

        if len(heat_matrix) > 0:
            fig_heat = px.imshow(
                heat_matrix.values,
                x=heat_matrix.columns.tolist(),
                y=heat_matrix.index.tolist(),
                color_continuous_scale="YlOrRd",
                aspect="auto",
                text_auto=".1f"
            )
            fig_heat.update_layout(
                margin=dict(t=20, b=20),
                xaxis_title="", yaxis_title="",
                height=max(300, len(heat_matrix) * 45)
            )
            st.plotly_chart(fig_heat, use_container_width=True, key="all_heatmap_chart")

    st.markdown("---")

    # Market Comparison
    st.header("📈 Market Comparison")
    st.markdown("*Deep dive into any question — compare markets side by side*")

    selected_question_comp = st.selectbox(
        "Select Question",
        options=questions_list,
        key="all_compare_q"
    )

    comp_data = df[df["Question"] == selected_question_comp].copy()

    if len(comp_data) > 0 and len(selected_cols) > 0:
        melted_comp = comp_data.melt(
            id_vars=["Response"],
            value_vars=selected_cols,
            var_name="Market_Col",
            value_name="Percentage"
        )
        melted_comp["Market"] = melted_comp["Market_Col"].map(market_display)
        melted_comp = melted_comp.dropna(subset=["Percentage"])

        chart_type = st.radio(
            "Chart Type", ["Grouped Bar", "Stacked Bar", "Radar"],
            horizontal=True, key="all_chart_type"
        )

        if chart_type == "Grouped Bar":
            fig_comp = px.bar(
                melted_comp, x="Response", y="Percentage", color="Market",
                barmode="group",
                color_discrete_map=MARKET_COLORS,
                height=600
            )
            if len(selected_market_names) <= 4:
                fig_comp.update_traces(texttemplate='%{y:.1f}%', textposition='outside', textfont_size=9)
            fig_comp.update_layout(
                xaxis_title="", yaxis_title="Percentage (%)",
                xaxis_tickangle=-45, margin=dict(t=40, b=100),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5)
            )
            st.plotly_chart(fig_comp, use_container_width=True, key="all_comp_grouped")

        elif chart_type == "Stacked Bar":
            fig_comp_stacked = px.bar(
                melted_comp, x="Market", y="Percentage", color="Response",
                barmode="stack",
                color_discrete_sequence=px.colors.qualitative.Set3,
                height=600
            )
            fig_comp_stacked.update_layout(
                xaxis_title="", yaxis_title="Percentage (%)",
                margin=dict(t=40, b=20),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5)
            )
            st.plotly_chart(fig_comp_stacked, use_container_width=True, key="all_comp_stacked")

        elif chart_type == "Radar":
            responses = comp_data["Response"].unique().tolist()
            fig_radar = go.Figure()

            for market in selected_market_names[:5]:
                col = display_to_col.get(market)
                if col and col in comp_data.columns:
                    values = comp_data[col].tolist()
                    values.append(values[0])

                    fig_radar.add_trace(go.Scatterpolar(
                        r=values,
                        theta=responses + [responses[0]],
                        fill='toself',
                        name=market,
                        line_color=MARKET_COLORS.get(market, "#333"),
                        opacity=0.6
                    ))

            fig_radar.update_layout(
                polar=dict(radialaxis=dict(visible=True)),
                margin=dict(t=40, b=40),
                height=500,
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5)
            )
            st.plotly_chart(fig_radar, use_container_width=True, key="all_comp_radar")

        with st.expander("📋 View Data Table"):
            display_data = comp_data[["Response"] + selected_cols].copy()
            display_data.columns = ["Response"] + [market_display.get(c, c) for c in selected_cols]
            st.dataframe(display_data, use_container_width=True, hide_index=True)

    st.markdown("---")

    # NPS Deep Dive
    st.header("🎯 NPS Deep Dive")

    nps_questions = df[df["Question"].str.lower().str.contains("recommend", na=False)]
    nps_numeric = nps_questions[nps_questions["Response"].apply(
        lambda x: x.replace(".", "").replace("-", "").isdigit()
    )]

    if len(nps_numeric) > 0:
        st.subheader("Score Distribution (0-10)")

        nps_melted = nps_numeric.melt(
            id_vars=["Response"],
            value_vars=selected_cols,
            var_name="Market_Col",
            value_name="Percentage"
        )
        nps_melted["Market"] = nps_melted["Market_Col"].map(market_display)
        nps_melted["Score"] = pd.to_numeric(nps_melted["Response"], errors="coerce")
        nps_melted = nps_melted.sort_values("Score")
        nps_melted = nps_melted.dropna(subset=["Percentage", "Score"])

        def nps_category(score):
            if score <= 6:
                return "Detractor (0-6)"
            elif score <= 8:
                return "Passive (7-8)"
            else:
                return "Promoter (9-10)"

        nps_melted["Category"] = nps_melted["Score"].apply(nps_category)

        global_col_name = None
        for m in selected_market_names:
            if "global" in m.lower():
                global_col_name = m
                break

        if global_col_name:
            single_market_nps = nps_melted[nps_melted["Market"] == global_col_name]
            if len(single_market_nps) > 0:
                fig_nps_dist = px.bar(
                    single_market_nps,
                    x="Score", y="Percentage", color="Category",
                    color_discrete_map={
                        "Detractor (0-6)": "#e74c3c",
                        "Passive (7-8)": "#f39c12",
                        "Promoter (9-10)": "#2ecc71"
                    },
                    height=450,
                    title=f"NPS Distribution — {global_col_name}"
                )
                fig_nps_dist.update_traces(texttemplate='%{y:.1f}%', textposition='outside', textfont_size=9)
                fig_nps_dist.update_layout(
                    xaxis_title="Score", yaxis_title="Percentage (%)",
                    margin=dict(t=40, b=20),
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5)
                )
                st.plotly_chart(fig_nps_dist, use_container_width=True, key="all_nps_dist_single")

        st.subheader("NPS Score Distribution — All Selected Markets")
        fig_nps_all = px.bar(
            nps_melted, x="Score", y="Percentage", color="Market",
            barmode="group",
            color_discrete_map=MARKET_COLORS,
            height=600
        )
        if len(selected_market_names) <= 4:
            fig_nps_all.update_traces(texttemplate='%{y:.1f}%', textposition='outside', textfont_size=9)
        fig_nps_all.update_layout(
            xaxis_title="Score (0-10)", yaxis_title="Percentage (%)",
            margin=dict(t=40, b=20),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5)
        )
        st.plotly_chart(fig_nps_all, use_container_width=True, key="all_nps_dist_all")

    st.markdown("---")

    # Key Insights / Outlier Detection
    st.header("💡 Key Insights & Market Outliers")
    st.markdown("*Responses where a market significantly differs from the Global Average*")

    threshold = st.slider("Difference threshold (percentage points)", 5, 30, 15, key="all_threshold")

    global_col = None
    for col in market_cols:
        if "global" in col.lower() or "average" in col.lower():
            global_col = col
            break

    outliers = []
    if global_col and global_col in df.columns:
        for _, row in df.iterrows():
            for col in selected_cols:
                if col == global_col:
                    continue
                if pd.notna(row.get(col)) and pd.notna(row.get(global_col)):
                    diff = row[col] - row[global_col]
                    if abs(diff) >= threshold:
                        outliers.append({
                            "Question": str(row["Question"])[:80],
                            "Response": row["Response"],
                            "Market": market_display.get(col, col),
                            "Market %": round(row[col], 1),
                            "Global Avg %": round(row[global_col], 1),
                            "Difference (pp)": round(diff, 1)
                        })

    if outliers:
        outlier_df = pd.DataFrame(outliers).sort_values("Difference (pp)", key=abs, ascending=False)
        st.dataframe(outlier_df.head(30), use_container_width=True, hide_index=True)
        st.markdown(f"*Showing top outliers where market differs from global average by ≥{threshold} percentage points*")
    else:
        st.info("No significant outliers found at this threshold. Try lowering it.")

    st.markdown("---")

    # Question Explorer
    st.header("🔍 Question Explorer")
    st.markdown("*Browse all questions and responses*")

    selected_q_explore = st.selectbox(
        "Select a Question",
        options=questions_list,
        key="all_explore_q"
    )

    explore_data = df[df["Question"] == selected_q_explore].copy()

    if len(explore_data) > 0 and len(selected_cols) > 0:
        display_explore = explore_data[["Response"] + selected_cols].copy()
        display_explore.columns = ["Response"] + [market_display.get(c, c) for c in selected_cols]
        st.dataframe(display_explore, use_container_width=True, hide_index=True)

        melted_explore = explore_data.melt(
            id_vars=["Response"],
            value_vars=selected_cols,
            var_name="Market_Col",
            value_name="Percentage"
        )
        melted_explore["Market"] = melted_explore["Market_Col"].map(market_display)
        melted_explore = melted_explore.dropna(subset=["Percentage"])

        fig_explore = px.bar(
            melted_explore, x="Response", y="Percentage", color="Market",
            barmode="group",
            color_discrete_map=MARKET_COLORS,
            height=600
        )
        if len(selected_market_names) <= 4:
            fig_explore.update_traces(texttemplate='%{y:.1f}%', textposition='outside', textfont_size=9)
        fig_explore.update_layout(
            xaxis_title="", yaxis_title="Percentage (%)",
            xaxis_tickangle=-45, margin=dict(t=40, b=100),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5)
        )
        st.plotly_chart(fig_explore, use_container_width=True, key="all_explorer_chart")


# ============================================================
# INDIVIDUAL MARKET TABS
# ============================================================
non_global_markets = [m for m in available_markets if "global" not in m.lower()]

for tab_idx, market_name in enumerate(non_global_markets):
    with tabs[tab_idx + 1]:
        market_col = display_to_col[market_name]
        market_color = MARKET_COLORS.get(market_name, "#3498db")

        global_col = None
        for col in market_cols:
            if "global" in col.lower() or "average" in col.lower():
                global_col = col
                break

        st.header(f"🌍 {market_name} — Market Deep Dive")
        st.markdown("---")

        market_nps = get_market_nps(df, market_col)
        market_csat = get_market_csat(df, market_col)
        global_nps = get_market_nps(df, global_col) if global_col else None
        global_csat = get_market_csat(df, global_col) if global_col else None

        kpi1, kpi2, kpi3, kpi4 = st.columns(4)

        with kpi1:
            if market_nps is not None:
                delta = round(market_nps - global_nps, 1) if global_nps else None
                st.metric("NPS Score", f"{market_nps:+.1f}", delta=f"{delta:+.1f} vs Global" if delta else None)

        with kpi2:
            if market_csat is not None:
                delta = round(market_csat - global_csat, 1) if global_csat else None
                st.metric("CSAT Score", f"{market_csat:+.1f}", delta=f"{delta:+.1f} vs Global" if delta else None)

        with kpi3:
            fan_q = df[df["Question"].str.lower().str.contains("how much of a fan", na=False)]
            huge_fan = fan_q[fan_q["Response"].str.lower().str.contains("huge", na=False)]
            if len(huge_fan) > 0 and market_col in huge_fan.columns:
                huge_fan_pct = huge_fan[market_col].values[0]
                if pd.notna(huge_fan_pct):
                    global_huge = huge_fan[global_col].values[0] if global_col and global_col in huge_fan.columns else None
                    delta = round(huge_fan_pct - global_huge, 1) if global_huge and pd.notna(global_huge) else None
                    st.metric("Huge Fans", f"{huge_fan_pct:.1f}%", delta=f"{delta:+.1f}pp vs Global" if delta else None)

        with kpi4:
            tenure_q = df[df["Question"].str.lower().str.contains("how long have you been", na=False)]
            long_fan = tenure_q[tenure_q["Response"].str.contains("10", na=False)]
            if len(long_fan) > 0 and market_col in long_fan.columns:
                long_fan_pct = long_fan[market_col].values[0]
                if pd.notna(long_fan_pct):
                    global_long = long_fan[global_col].values[0] if global_col and global_col in long_fan.columns else None
                    delta = round(long_fan_pct - global_long, 1) if global_long and pd.notna(global_long) else None
                    st.metric("10+ Year Fans", f"{long_fan_pct:.1f}%", delta=f"{delta:+.1f}pp vs Global" if delta else None)

        st.markdown("---")

        st.subheader(f"📊 {market_name} vs Global Average")

        selected_q_market = st.selectbox(
            "Select Question",
            options=questions_list,
            key=f"market_q_{tab_idx}"
        )

        q_market_data = df[df["Question"] == selected_q_market].copy()

        if len(q_market_data) > 0:
            compare_cols = [market_col]
            if global_col and global_col in q_market_data.columns:
                compare_cols = [market_col, global_col]

            melted_market = q_market_data.melt(
                id_vars=["Response"],
                value_vars=compare_cols,
                var_name="Market_Col",
                value_name="Percentage"
            )
            melted_market["Market"] = melted_market["Market_Col"].map(market_display)
            melted_market = melted_market.dropna(subset=["Percentage"])

            fig_market = px.bar(
                melted_market, x="Response", y="Percentage", color="Market",
                barmode="group",
                color_discrete_map=MARKET_COLORS,
                height=500
            )
            fig_market.update_traces(texttemplate='%{y:.1f}%', textposition='outside', textfont_size=10)
            fig_market.update_layout(
                xaxis_title="", yaxis_title="Percentage (%)",
                xaxis_tickangle=-45, margin=dict(t=40, b=100),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5)
            )
            st.plotly_chart(fig_market, use_container_width=True, key=f"market_chart_{tab_idx}")

            with st.expander("📋 View Data Table"):
                display_market = q_market_data[["Response"] + compare_cols].copy()
                display_market.columns = ["Response"] + [market_display.get(c, c) for c in compare_cols]
                st.dataframe(display_market, use_container_width=True, hide_index=True)

        st.markdown("---")

        st.subheader(f"💡 {market_name} — Biggest Differences vs Global Average")

        market_outliers = []
        if global_col and global_col in df.columns and market_col in df.columns:
            for _, row in df.iterrows():
                if pd.notna(row.get(market_col)) and pd.notna(row.get(global_col)):
                    diff = row[market_col] - row[global_col]
                    if abs(diff) >= 10:
                        market_outliers.append({
                            "Question": str(row["Question"])[:80],
                            "Response": row["Response"],
                            f"{market_name} %": round(row[market_col], 1),
                            "Global Avg %": round(row[global_col], 1),
                            "Difference (pp)": round(diff, 1)
                        })

        if market_outliers:
            market_outlier_df = pd.DataFrame(market_outliers).sort_values("Difference (pp)", key=abs, ascending=False)
            st.dataframe(market_outlier_df.head(20), use_container_width=True, hide_index=True)
        else:
            st.info(f"No responses where {market_name} differs from Global Average by ≥10 percentage points.")


st.markdown("---")
st.caption("NFL Game Pass International Survey Dashboard | Built with Streamlit")