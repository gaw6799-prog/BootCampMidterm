"""
Trump Oil Market Manipulation Forensics — Interactive Dashboard
Run with: streamlit run app.py
"""
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.patches as mpatches
import numpy as np
import os

st.set_page_config(
    page_title="Trump Oil Manipulation Forensics",
    page_icon="🛢️",
    layout="wide"
)

# --- Data Loading ---
@st.cache_data
def load_data():
    data = {}
    base = 'data/processed'

    for name, filename in [
        ('scores', 'manipulation_scores.csv'),
        ('master', 'master_dataset.csv'),
        ('gemini', 'gemini_classifications.csv'),
        ('fabrication', 'fabrication_evidence.csv'),
        ('posts', 'posts_cleaned.csv'),
    ]:
        path = os.path.join(base, filename)
        if os.path.exists(path):
            df = pd.read_csv(path)
            for col in df.columns:
                if 'date' in col.lower():
                    df[col] = pd.to_datetime(df[col], errors='coerce')
            data[name] = df
        else:
            data[name] = pd.DataFrame()

    return data

data = load_data()
scores = data['scores']
gemini = data['gemini']
fabrication = data['fabrication']
posts = data['posts']

# --- Key Dates ---
KEY_DATES = [
    {'date': '2026-03-23', 'label': 'Iran Fabrication\n("productive conversations")', 'color': '#d62728'},
    {'date': '2026-03-09', 'label': '$38 Intraday Swing\n(Largest crude range ever)', 'color': '#ff7f0e'},
    {'date': '2025-04-09', 'label': 'Tariff Pause\n("GREAT TIME TO BUY")', 'color': '#9467bd'},
    {'date': '2025-02-01', 'label': 'Liberation Day\n(Ultimatum → Reversal)', 'color': '#8c564b'},
]

# --- Vector 8: Weekend/Monday Timing Pattern ---
def compute_timing_scores(posts_df):
    """
    Score each Monday based on the weekend threat → Monday reversal pattern.
    Uses direction_keyword column. Cross-date: checks weekend before each Monday.
    """
    if posts_df.empty or 'timestamp' not in posts_df.columns:
        return pd.Series(dtype=float)

    df = posts_df.copy()
    if not pd.api.types.is_datetime64_any_dtype(df['timestamp']):
        df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
    df = df.dropna(subset=['timestamp'])
    df['weekday'] = df['timestamp'].dt.weekday  # 0=Mon, 5=Sat, 6=Sun
    df['hour'] = df['timestamp'].dt.hour
    df['date'] = df['timestamp'].dt.date
    df['direction_keyword'] = df.get('direction_keyword', pd.Series('neutral', index=df.index))

    # Precompute weekend escalation days and monday premarket de-escalation days
    weekend_esc = df[
        df['weekday'].isin([5, 6]) & (df['direction_keyword'] == 'escalation')
    ]['date'].unique()

    monday_deesc = df[
        (df['weekday'] == 0) & (df['hour'] < 10) & (df['direction_keyword'] == 'de_escalation')
    ]['date'].unique()

    monday_any_premarket = df[
        (df['weekday'] == 0) & (df['hour'] < 10)
    ]['date'].unique()

    scores_by_date = {}

    # Score each Monday that has pre-market activity
    for monday in monday_any_premarket:
        score = 0
        monday_ts = pd.Timestamp(monday)

        # Check if the preceding Saturday or Sunday had escalation posts
        sat = (monday_ts - pd.Timedelta(days=2)).date()
        sun = (monday_ts - pd.Timedelta(days=1)).date()
        had_weekend_escalation = sat in weekend_esc or sun in weekend_esc

        if had_weekend_escalation:
            score += 40  # Weekend escalation before this Monday

        if monday in monday_deesc:
            score += 30  # Monday pre-market de-escalation

        # Full sequence bonus
        if had_weekend_escalation and monday in monday_deesc:
            score += 30

        if score > 0:
            scores_by_date[str(monday)] = min(score, 100)

    return pd.Series(scores_by_date)

timing_scores = compute_timing_scores(posts)

COLORS = {
    'escalation': '#d62728',
    'de_escalation': '#2ca02c',
    'neutral': '#7f7f7f',
    'fabrication': '#ff7f0e',
    'oil_price': '#1f77b4',
    'high': '#d62728',
    'elevated': '#ff7f0e',
    'low': '#2ca02c'
}

# --- Sidebar ---
st.sidebar.title("Filters")

if len(scores) > 0 and 'date' in scores.columns:
    min_date = scores['date'].min().date()
    max_date = scores['date'].max().date()
    date_range = st.sidebar.date_input(
        "Date Range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )

    score_threshold = st.sidebar.slider("Min Manipulation Score", 0, 100, 0)

    # Apply filters
    if len(date_range) == 2:
        mask = (scores['date'].dt.date >= date_range[0]) & (scores['date'].dt.date <= date_range[1])
        filtered = scores[mask]
    else:
        filtered = scores

    if score_threshold > 0:
        filtered = filtered[filtered['manipulation_score'] >= score_threshold]
else:
    filtered = scores
    st.sidebar.warning("No data loaded. Run notebooks 01-06 first.")

# --- Main Content ---
st.title("Trump Oil Market Manipulation Forensics")
st.markdown("*Forensic analysis of Truth Social posts and oil price movements during the March 2026 Iran crisis*")

tab1, tab2, tab3, tab4 = st.tabs(["Overview", "Timeline", "Evidence", "Methodology"])

# --- Tab 1: Overview ---
with tab1:
    if len(scores) > 0:
        col1, col2, col3, col4 = st.columns(4)

        peak_score = scores['manipulation_score'].max()
        peak_date = scores.loc[scores['manipulation_score'].idxmax(), 'date']
        high_days = (scores['verdict'] == 'HIGH').sum()

        col1.metric("Peak Score", f"{peak_score:.0f}/100",
                     f"{peak_date.strftime('%b %d, %Y')}")
        col2.metric("HIGH Days", str(high_days))
        col3.metric("ELEVATED Days", str((scores['verdict'] == 'ELEVATED').sum()))

        if 'brent_pct_change' in scores.columns:
            max_swing = scores['brent_pct_change'].abs().max()
            col4.metric("Max Daily Oil Move", f"{max_swing:.1f}%")

        # Hero chart
        st.subheader("Oil Price & Manipulation Score")

        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 8),
                                         gridspec_kw={'height_ratios': [2, 1]},
                                         sharex=True)

        trading = filtered[filtered['brent_close'].notna()]
        ax1.plot(trading['date'], trading['brent_close'],
                 color=COLORS['oil_price'], linewidth=1.5)

        for direction, color, marker in [
            ('escalation', COLORS['escalation'], '^'),
            ('de_escalation', COLORS['de_escalation'], 'v'),
        ]:
            mask = trading['dominant_direction'] == direction
            subset = trading[mask]
            if len(subset) > 0:
                ax1.scatter(subset['date'], subset['brent_close'],
                           color=color, s=25, alpha=0.7, marker=marker,
                           label=direction.replace('_', '-').title())

        # Key date vertical lines
        price_max = trading['brent_close'].max() if 'brent_close' in trading.columns else 100
        for kd in KEY_DATES:
            kd_ts = pd.Timestamp(kd['date'])
            if trading['date'].min() <= kd_ts <= trading['date'].max():
                ax1.axvline(kd_ts, color=kd['color'], linestyle='--', alpha=0.7, linewidth=1.2)
                ax1.text(kd_ts, price_max, kd['label'], rotation=90, fontsize=6,
                         color=kd['color'], va='top', ha='right', alpha=0.85)

        ax1.set_ylabel('Brent Crude ($/barrel)')
        ax1.legend(fontsize=8)

        bar_colors = filtered['verdict'].map(
            {'HIGH': COLORS['high'], 'ELEVATED': COLORS['elevated'], 'LOW': COLORS['low']}
        ).fillna('#cccccc')
        ax2.bar(filtered['date'], filtered['manipulation_score'],
                color=bar_colors, width=1, alpha=0.7)
        ax2.axhline(70, color='red', linestyle='--', alpha=0.3)
        ax2.axhline(50, color='orange', linestyle='--', alpha=0.3)
        ax2.set_ylabel('Manipulation Score')
        ax2.set_ylim(0, 105)

        plt.tight_layout()
        st.pyplot(fig)
        plt.close()

        # Top suspicious days table
        st.subheader("Top Suspicious Trading Days")
        top = scores.nlargest(10, 'manipulation_score').copy()
        top['date'] = top['date'].dt.strftime('%b %d, %Y')
        display_cols = ['date', 'brent_pct_change', 'oil_post_count',
                        'manipulation_score', 'verdict']
        available = [c for c in display_cols if c in top.columns]
        st.dataframe(top[available], use_container_width=True, hide_index=True)
        # Vector 8: Weekend/Monday Timing Pattern
        if len(timing_scores) > 0:
            st.subheader("Vector 8: Weekend/Monday Timing Pattern")
            st.markdown(
                "Detects the **threat-on-weekend → reversal-on-Monday-premarket** pump-and-dump sequence. "
                "Score >0 indicates suspicious timing alignment."
            )

            timing_df = timing_scores.reset_index()
            timing_df.columns = ['date', 'timing_score']
            timing_df['date'] = pd.to_datetime(timing_df['date'])
            timing_high = timing_df[timing_df['timing_score'] > 0].copy()

            if len(timing_high) > 0:
                col1, col2 = st.columns(2)
                col1.metric("Days with Suspicious Timing", str(len(timing_high)))
                col2.metric("Max Timing Score", f"{timing_high['timing_score'].max():.0f}/100")

                fig3, ax = plt.subplots(figsize=(14, 3))
                ax.bar(timing_df['date'], timing_df['timing_score'],
                       color=['#d62728' if s >= 70 else '#ff7f0e' if s >= 40 else '#aec7e8'
                              for s in timing_df['timing_score']], width=1, alpha=0.8)
                ax.axhline(70, color='red', linestyle='--', alpha=0.4, label='HIGH threshold')
                ax.set_ylabel('Timing Score')
                ax.set_ylim(0, 105)
                ax.set_title('Weekend Threat → Monday Reversal Pattern Score')
                plt.tight_layout()
                st.pyplot(fig3)
                plt.close()
            else:
                st.info("No suspicious timing patterns detected in current date range.")
    else:
        st.info("No data available. Run notebooks 01-06 to generate analysis data.")

# --- Tab 2: Timeline ---
with tab2:
    st.subheader("Interactive Date Explorer")

    if len(scores) > 0:
        dates_with_posts = scores[scores['oil_post_count'] > 0]['date'].sort_values(ascending=False)

        if len(dates_with_posts) > 0:
            selected_date = st.selectbox(
                "Select a date with oil-related posts:",
                dates_with_posts.dt.strftime('%Y-%m-%d').tolist()
            )

            sel = pd.Timestamp(selected_date)
            day_data = scores[scores['date'].dt.date == sel.date()]

            if len(day_data) > 0:
                row = day_data.iloc[0]

                col1, col2, col3 = st.columns(3)
                col1.metric("Oil Posts", int(row.get('oil_post_count', 0)))
                col2.metric("Oil Price Change",
                           f"{row.get('brent_pct_change', 0):+.2f}%"
                           if pd.notna(row.get('brent_pct_change')) else 'N/A')
                col3.metric("Manipulation Score",
                           f"{row.get('manipulation_score', 0):.0f}",
                           row.get('verdict', ''))

                # Show score breakdown
                st.markdown("**Score Breakdown:**")
                score_cols = ['oscillation_score', 'fabrication_score', 'causality_score',
                             'intent_score', 'beneficiary_score']
                weights = [0.20, 0.25, 0.25, 0.15, 0.15]
                labels = ['Oscillation (20%)', 'Fabrication (25%)', 'Causality (25%)',
                          'Intent (15%)', 'Beneficiary (15%)']

                for label, col, weight in zip(labels, score_cols, weights):
                    if col in row.index:
                        val = row[col]
                        weighted = val * weight
                        st.progress(min(val / 100, 1.0), text=f"{label}: {val:.0f} (weighted: {weighted:.1f})")

                # Show Gemini classifications for that day
                if len(gemini) > 0:
                    day_gemini = gemini[gemini['date'].dt.date == sel.date()]
                    if len(day_gemini) > 0:
                        st.markdown("**AI Classifications (Gemini):**")
                        for _, g in day_gemini.iterrows():
                            text = str(g.get('post_text', ''))[:150]
                            cat = g.get('category', 'UNKNOWN')
                            reasoning = g.get('reasoning', g.get('overall_reasoning', ''))
                            st.markdown(f"- **{cat}**: \"{text}...\" — *{reasoning}*")

                            # Show per-dimension scores if new prompt schema is present
                            new_fields = ['escalation_intent', 'de_escalation_intent',
                                          'fabrication_risk', 'market_mover_probability',
                                          'timing_suspicion']
                            if all(f in g.index and pd.notna(g[f]) for f in new_fields):
                                with st.expander("Dimension scores"):
                                    for field, label in [
                                        ('escalation_intent', 'Escalation Intent'),
                                        ('de_escalation_intent', 'De-escalation Intent'),
                                        ('fabrication_risk', 'Fabrication Risk'),
                                        ('market_mover_probability', 'Market Mover Probability'),
                                        ('timing_suspicion', 'Timing Suspicion'),
                                    ]:
                                        val = g[field]
                                        reason_key = field.replace('_intent', '_reasoning').replace('_probability', '_reasoning').replace('_suspicion', '_reasoning').replace('_risk', '_reasoning')
                                        reason = g.get(reason_key, '')
                                        st.progress(min(val / 100, 1.0),
                                                    text=f"{label}: {val:.0f}/100 — {reason}")

# --- Tab 3: Evidence ---
with tab3:
    st.subheader("Exhibit A: The March 23 Fabrication")

    st.markdown("""
    **The strongest evidence of deliberate market manipulation:**

    1. **Trump's Claim**: Posted about "productive conversations" with Iran,
       implying de-escalation and imminent resolution
    2. **Market Reaction**: Oil prices dropped 13%+ as markets priced in peace
    3. **Iran's Denial**: Iranian Foreign Ministry explicitly denied any talks took place
    4. **The Accusation**: Iran called Trump's post "fake news" used to
       "manipulate the financial and oil markets"
    """)

    if len(fabrication) > 0:
        st.subheader("All Documented Fabrications")
        fab_display = fabrication.copy()
        if 'date' in fab_display.columns:
            fab_display['date'] = fab_display['date'].dt.strftime('%b %d, %Y')
        st.dataframe(fab_display, use_container_width=True, hide_index=True)

    st.subheader("The Oscillation Pattern")
    st.markdown("""
    Trump's posts follow a systematic pump-and-dump cycle:

    ```
    ESCALATION POST (threats, bombing, war)
           ↓
    Oil price SPIKES (fear premium)
           ↓
    DE-ESCALATION POST (talks, peace, deals — often fabricated)
           ↓
    Oil price CRASHES (relief)
           ↓
    REPEAT
    ```

    This pattern is consistent with intentional volatility creation for profit.
    """)

# --- Tab 4: Methodology ---
with tab4:
    st.subheader("Five Detection Vectors")

    st.markdown("""
    Our analysis uses five independent detection vectors, each scored 0-100,
    combined into a weighted composite Manipulation Score.

    | Vector | Weight | What It Measures |
    |--------|--------|-----------------|
    | **Oscillation** | 20% | Does the post direction reverse within 48 hours? (Pump-and-dump pattern) |
    | **Fabrication** | 25% | Is the claim provably false? Did an official source deny it? |
    | **Causality** | 25% | Did the post come BEFORE the price move? (Proves intent) |
    | **Intent** | 15% | AI (Gemini) analysis of manipulation intent, ALL CAPS, threats |
    | **Beneficiary** | 15% | Did Trump/associates benefit? (DJT stock, insider sales) |

    **Thresholds:**
    - **>70**: HIGH manipulation probability
    - **50-70**: ELEVATED suspicion
    - **<50**: LOW suspicion

    **Data Sources:**
    - Trump posts: trumpstruth.org (scraped)
    - Oil prices: FRED (Brent & WTI daily)
    - DJT stock: Yahoo Finance
    - AI classification: Google Gemini API
    - Fabrication evidence: Iranian Foreign Ministry denials
    """)

# --- Footer ---
st.markdown("---")
st.markdown("*NYU Data Bootcamp Midterm Project — Forensic Detection of Market Manipulation via Social Media*")
