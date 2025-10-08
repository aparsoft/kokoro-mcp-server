# streamlit_utils.py

"""Streamlit utility functions for error handling and debugging"""

import streamlit as st
import traceback
import logging
from functools import wraps
from typing import Callable, Any
from datetime import datetime

# Setup logging
logging.basicConfig(
    filename="streamlit_app.log",
    level=logging.ERROR,
    format="%(asctime)s - %(levelname)s - %(message)s",
)


def streamlit_error_handler(show_traceback: bool = True, log_to_file: bool = True):
    """Decorator for comprehensive error handling in Streamlit functions

    Args:
        show_traceback: Show expandable traceback in UI (default: True)
        log_to_file: Log errors to streamlit_app.log (default: True)

    Usage:
        @streamlit_error_handler()
        def my_function():
            # Your code here
            pass
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # Get error details
                error_type = type(e).__name__
                error_msg = str(e)

                # Log to file if enabled
                if log_to_file:
                    logging.error(f"{func.__name__} failed: {error_msg}", exc_info=True)

                # Display user-friendly error
                st.error(f"❌ {error_type}: {error_msg}")

                # Show full traceback in expander if enabled
                if show_traceback:
                    with st.expander("🔍 Debug Info (Full Traceback)"):
                        st.code(traceback.format_exc(), language="python")

                return None

        return wrapper

    return decorator


def show_exception(e: Exception, context: str = ""):
    """Display exception with full details in Streamlit

    Args:
        e: The exception to display
        context: Additional context about where error occurred

    Usage:
        try:
            risky_operation()
        except Exception as e:
            show_exception(e, "Failed during config save")
    """
    error_type = type(e).__name__
    error_msg = str(e)

    # Main error message
    if context:
        st.error(f"❌ {context}: {error_msg}")
    else:
        st.error(f"❌ {error_type}: {error_msg}")

    # Detailed traceback
    with st.expander("🔍 Full Error Details"):
        st.code(traceback.format_exc(), language="python")

        # Additional debug info
        st.markdown("**Error Type:**")
        st.code(error_type)

        st.markdown("**Error Message:**")
        st.code(error_msg)


def safe_json_serialize(obj: Any) -> dict:
    """Convert object to JSON-safe dictionary

    Handles Path, datetime, and other non-serializable types

    Args:
        obj: Object to serialize (dict, Pydantic model, etc.)

    Returns:
        JSON-serializable dictionary

    Usage:
        config_dict = safe_json_serialize(custom_config)
        json.dump(config_dict, f, indent=2)
    """
    from pathlib import Path
    from datetime import datetime, date
    from pydantic import BaseModel

    if isinstance(obj, BaseModel):
        # Pydantic models
        return safe_json_serialize(obj.model_dump())
    elif isinstance(obj, dict):
        return {k: safe_json_serialize(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [safe_json_serialize(item) for item in obj]
    elif isinstance(obj, (Path,)):
        return str(obj)
    elif isinstance(obj, (datetime, date)):
        return obj.isoformat()
    elif isinstance(obj, (int, float, str, bool, type(None))):
        return obj
    else:
        # Fallback: convert to string
        return str(obj)


def extract_voices_from_history(df) -> list:
    """Extract all voices used from history dataframe.

    Handles both single voice entries and multi-voice podcast entries.

    Args:
        df: Pandas DataFrame with history entries

    Returns:
        List of all voices used

    Usage:
        voices = extract_voices_from_history(history_df)
    """
    import pandas as pd

    voice_data = []

    # Check if columns exist
    has_voice = "voice" in df.columns
    has_voices_used = "voices_used" in df.columns

    for idx, row in df.iterrows():
        # Handle single voice column
        if has_voice:
            try:
                voice_val = row["voice"]
                # Safely check if value is not null and not empty
                if voice_val is not None and str(voice_val).strip():
                    voice_data.append(str(voice_val))
                    continue  # Skip to next row
            except (KeyError, TypeError, AttributeError):
                pass

        # Handle voices_used column (podcast entries)
        if has_voices_used:
            try:
                voices_val = row["voices_used"]

                # Handle Series/array edge case
                if isinstance(voices_val, pd.Series):
                    voices_val = voices_val.iloc[0] if len(voices_val) > 0 else None

                # Check if value exists and is not null
                if voices_val is not None:
                    if isinstance(voices_val, list):
                        voice_data.extend(voices_val)
                    elif str(voices_val).strip():  # Not empty string/value
                        voice_data.append(str(voices_val))
            except (KeyError, TypeError, AttributeError):
                pass

    return voice_data


def normalize_voice_column(df):
    """Normalize voice columns in history dataframe for display.

    Merges 'voice' and 'voices_used' columns into a single 'voice' column.

    Args:
        df: Pandas DataFrame with history entries

    Returns:
        DataFrame with normalized voice column

    Usage:
        display_df = normalize_voice_column(history_df.copy())
    """
    import pandas as pd

    display_df = df.copy()

    has_voice = "voice" in display_df.columns
    has_voices_used = "voices_used" in display_df.columns

    # Merge voice and voices_used into single column
    if has_voice and has_voices_used:
        # Both columns exist - merge them
        def merge_voices(row):
            try:
                voice_val = row["voice"]
                voices_used_val = row["voices_used"]

                # Handle Series/array edge cases
                if isinstance(voice_val, pd.Series):
                    voice_val = voice_val.iloc[0] if len(voice_val) > 0 else None
                if isinstance(voices_used_val, pd.Series):
                    voices_used_val = voices_used_val.iloc[0] if len(voices_used_val) > 0 else None

                # Safer null checks
                if voice_val is not None and str(voice_val).strip():
                    return str(voice_val)
                elif voices_used_val is not None:
                    if isinstance(voices_used_val, list):
                        return ", ".join(str(v) for v in voices_used_val)
                    else:
                        return str(voices_used_val)
                else:
                    return ""
            except (KeyError, TypeError, AttributeError):
                return ""

        display_df["voice"] = display_df.apply(merge_voices, axis=1)
        display_df = display_df.drop(columns=["voices_used"])

    elif has_voices_used:
        # Only voices_used exists - convert to voice
        def convert_voices_used(val):
            try:
                # Handle Series/array edge case
                if isinstance(val, pd.Series):
                    val = val.iloc[0] if len(val) > 0 else None

                # Safer null check
                if val is not None:
                    if isinstance(val, list):
                        return ", ".join(str(v) for v in val)
                    else:
                        return str(val)
                return ""
            except (TypeError, AttributeError):
                return ""

        display_df["voice"] = display_df["voices_used"].apply(convert_voices_used)
        display_df = display_df.drop(columns=["voices_used"])

    return display_df


# Example usage in your Streamlit app
if __name__ == "__main__":
    st.title("Error Handler Demo")

    # Example 1: Using decorator
    @streamlit_error_handler()
    def risky_function():
        result = 1 / 0  # This will raise ZeroDivisionError
        return result

    if st.button("Test Decorator"):
        risky_function()

    # Example 2: Using show_exception
    if st.button("Test Exception Handler"):
        try:
            x = {"key": Path("/some/path")}
            import json

            json.dumps(x)  # Will fail - Path not serializable
        except Exception as e:
            show_exception(e, "JSON serialization failed")

    # Example 3: Using safe_json_serialize
    if st.button("Test Safe Serialization"):
        from pathlib import Path

        data = {
            "path": Path("/home/user/file.txt"),
            "nested": {"another_path": Path("/another/path"), "timestamp": datetime.now()},
        }

        safe_data = safe_json_serialize(data)
        st.json(safe_data)
        st.success("✅ Successfully serialized!")
