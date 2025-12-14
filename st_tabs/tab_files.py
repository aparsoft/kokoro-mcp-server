import streamlit as st
from pathlib import Path
from datetime import datetime
import sys
import warnings

# Suppress warnings from PyTorch and other libraries
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=FutureWarning)

# Add project to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from st_utils.helper import get_audio_stats
from aparsoft_tts.utils.audio import format_duration


# ==========================================
# TAB 7: AUDIO FILE MANAGER
# ==========================================
def render_tab_files():
    """Render the Audio File Manager tab"""
    st.markdown("## 📁 Audio File Manager")
    st.markdown("Browse, play, and manage your generated audio files")

    # List all output directories
    output_dirs = {
        "Single Generations": "outputs/single",
        "Batch Generations": "outputs/batch",
        "Scripts": "outputs/scripts",
        "Podcasts": "outputs/podcasts",
        "Voice Comparisons": "outputs/voice_comparison",
        "Voice Samples": "outputs/voice_samples",
    }

    # Statistics
    total_files = 0
    total_size = 0

    for dir_path in output_dirs.values():
        dir_path = Path(dir_path)
        if dir_path.exists():
            files = list(dir_path.glob("*.*"))
            total_files += len(files)
            total_size += sum(f.stat().st_size for f in files)

    # Display stats
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Files", total_files)
    with col2:
        st.metric("Total Size", f"{total_size / (1024 * 1024):.1f} MB")
    with col3:
        st.metric("Directories", len([d for d in output_dirs.values() if Path(d).exists()]))

    st.markdown("---")

    # Bulk actions
    st.markdown("### 🧹 Bulk Actions")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("📥 Export All as ZIP", use_container_width=True):
            st.info("🚧 ZIP export feature coming soon!")

    with col2:
        if st.button("🗑️ Clear All Files", use_container_width=True, type="secondary"):
            if st.session_state.get("confirm_delete_all"):
                deleted_count = 0
                for dir_path in output_dirs.values():
                    dir_path = Path(dir_path)
                    if dir_path.exists():
                        for file in dir_path.glob("*.*"):
                            file.unlink()
                            deleted_count += 1
                st.success(f"✅ Deleted {deleted_count} files!")
                st.session_state["confirm_delete_all"] = False
                st.rerun()
            else:
                st.session_state["confirm_delete_all"] = True
                st.warning("⚠️ Click again to confirm deletion of ALL files!")

    with col3:
        if st.button("🔄 Refresh", use_container_width=True):
            st.rerun()

    st.markdown("---")

    # File browser by directory
    st.markdown("### 📂 File Browser")

    for category, dir_path in output_dirs.items():
        dir_path = Path(dir_path)

        if dir_path.exists():
            files = sorted(
                list(dir_path.glob("*.*")), key=lambda x: x.stat().st_mtime, reverse=True
            )

            if files:
                with st.expander(f"📁 {category} ({len(files)} files)", expanded=False):
                    for file in files:
                        file_stat = file.stat()
                        size_mb = file_stat.st_size / (1024 * 1024)
                        modified = datetime.fromtimestamp(file_stat.st_mtime).strftime(
                            "%Y-%m-%d %H:%M:%S"
                        )

                        col1, col2, col3, col4, col5 = st.columns([3, 1, 1, 1, 1])

                        with col1:
                            st.text(file.name)

                        with col2:
                            st.text(f"{size_mb:.2f} MB")

                        with col3:
                            st.text(modified)

                        with col4:
                            # Play button
                            if file.suffix.lower() in [".wav", ".mp3", ".flac"]:
                                st.audio(str(file), format=f"audio/{file.suffix[1:]}")

                        with col5:
                            # Delete button
                            if st.button("🗑️", key=f"delete_{file.stem}_{file.parent.name}"):
                                file.unlink()
                                st.rerun()

                        # Download button for each file
                        with open(file, "rb") as f:
                            st.download_button(
                                label=f"📥 Download {file.name}",
                                data=f,
                                file_name=file.name,
                                mime=f"audio/{file.suffix[1:]}",
                                key=f"download_{file.stem}_{file.parent.name}",
                            )

                        st.markdown("---")
            else:
                with st.expander(f"📁 {category} (0 files)"):
                    st.info("📦 No files in this directory")
        else:
            with st.expander(f"📁 {category} (directory not created yet)"):
                st.info("📍 Directory will be created when you generate audio")
