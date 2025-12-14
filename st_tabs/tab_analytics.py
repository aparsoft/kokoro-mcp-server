import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path
from datetime import datetime
import sys
import warnings

# Suppress warnings from PyTorch and other libraries
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=FutureWarning)

# Add project to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import error handling utilities
from streamlit_utils import (
    extract_voices_from_history,
    normalize_voice_column,
)

from st_utils.helper import (
    get_current_engine,
    add_to_history,
    get_history_df,
    get_history_summary,
)


# ==========================================
# TAB 9: ANALYTICS
# ==========================================
def render_tab_analytics():
    """Render the Analytics & History tab"""
    st.markdown("## 📊 Analytics & History")
    st.markdown("Track and analyze your TTS generation activity")

    if not st.session_state.generation_history:
        st.info("📭 No generation history yet. Start generating audio to see analytics!")

    else:
        df = get_history_df()

        # Summary metrics
        st.markdown("### 📈 Summary Metrics")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.markdown(
                """
            <div class='metric-card'>
                <h3>{}</h3>
                <p>Total Generations</p>
            </div>
            """.format(
                    len(df)
                ),
                unsafe_allow_html=True,
            )

        with col2:
            total_duration = df["duration"].sum() if "duration" in df.columns else 0
            st.markdown(
                """
            <div class='metric-card'>
                <h3>{:.1f}s</h3>
                <p>Total Audio Duration</p>
            </div>
            """.format(
                    total_duration
                ),
                unsafe_allow_html=True,
            )

        with col3:
            avg_gen_time = df["generation_time"].mean() if "generation_time" in df.columns else 0
            st.markdown(
                """
            <div class='metric-card'>
                <h3>{:.2f}s</h3>
                <p>Avg Generation Time</p>
            </div>
            """.format(
                    avg_gen_time
                ),
                unsafe_allow_html=True,
            )

        with col4:
            # Calculate unique voices using utility function
            voice_data = extract_voices_from_history(df)
            unique_voices = len(set(voice_data))

            st.markdown(
                """
            <div class='metric-card'>
                <h3>{}</h3>
                <p>Voices Used</p>
            </div>
            """.format(
                    unique_voices
                ),
                unsafe_allow_html=True,
            )

        st.markdown("---")

        # Charts
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### 📊 Generations by Type")

            type_counts = df["type"].value_counts()

            fig = px.pie(
                values=type_counts.values,
                names=type_counts.index,
                title="Generation Type Distribution",
                color_discrete_sequence=px.colors.sequential.Purples_r,
            )

            st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.markdown("### 🎤 Voice Usage")

            # Extract voices from history (handles both single and multi-voice)
            voice_data = extract_voices_from_history(df)

            if voice_data:
                voice_counts = pd.Series(voice_data).value_counts()

                fig = px.bar(
                    x=voice_counts.index,
                    y=voice_counts.values,
                    title="Voice Usage Count",
                    labels={"x": "Voice", "y": "Count"},
                    color=voice_counts.values,
                    color_continuous_scale="Purples",
                )

                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No voice data available yet")

        # Timeline
        st.markdown("### 📅 Generation Timeline")

        timeline_df = df.copy()
        timeline_df["date"] = timeline_df["timestamp"].dt.date
        daily_counts = timeline_df.groupby("date").size().reset_index(name="count")

        fig = px.line(
            daily_counts,
            x="date",
            y="count",
            title="Daily Generation Activity",
            labels={"date": "Date", "count": "Generations"},
            markers=True,
        )

        fig.update_traces(line_color="#667eea")

        st.plotly_chart(fig, use_container_width=True)

        # Recent History Table
        st.markdown("### 📜 Recent History")

        # Select columns that exist in the dataframe
        available_cols = [
            "timestamp",
            "type",
            "voice",
            "voices_used",
            "duration",
            "generation_time",
        ]
        display_cols = [col for col in available_cols if col in df.columns]

        if display_cols:
            recent_df = df[display_cols].tail(10).sort_values("timestamp", ascending=False)

            # Normalize voice columns for display
            display_df = normalize_voice_column(recent_df)

            st.dataframe(display_df, width="stretch", hide_index=True)
        else:
            st.info("No history data available")

        # Export options
        st.markdown("---")
        st.markdown("### 📤 Export Data")

        col1, col2, col3 = st.columns(3)

        with col1:
            csv = df.to_csv(index=False)
            st.download_button(
                label="📥 Download as CSV",
                data=csv,
                file_name=f"tts_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                width="stretch",
            )

        with col2:
            json_data = df.to_json(orient="records", indent=2)
            st.download_button(
                label="📥 Download as JSON",
                data=json_data,
                file_name=f"tts_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
                width="stretch",
            )

        with col3:
            if st.button("🗑️ Clear All History", width="stretch"):
                st.session_state.generation_history = []
                st.session_state.total_generations = 0
                st.rerun()
