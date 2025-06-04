# Create the Streamlit-compatible version of the script
streamlit_script = """
# streamlit_app.py
import streamlit as st
import pandas as pd
import io

st.title("TriNetX Table Formatter for Journal Submission")

uploaded_file = st.file_uploader("Upload your TriNetX CSV file", type="csv")

def extract_clean_table(df):
    # Locate start of data
    for i, row in df.iterrows():
        if "Characteristic" in str(row[0]):
            data_start_index = i
            break
    # Extract and clean
    df_clean = df.iloc[data_start_index:].reset_index(drop=True)
    df_clean.columns = df_clean.iloc[0]
    df_clean = df_clean[1:].reset_index(drop=True)
    return df_clean

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    cleaned_df = extract_clean_table(df)

    st.sidebar.header("Display Options")
    show_gridlines = st.sidebar.checkbox("Show Gridlines", value=True)
    bold_headers = st.sidebar.checkbox("Bold Headers", value=True)
    decimals = st.sidebar.slider("Decimal Places", 0, 5, 2)

    df_display = cleaned_df.copy()
    for col in df_display.columns:
        try:
            df_display[col] = df_display[col].astype(float).round(decimals)
        except:
            pass

    st.markdown("### Preview of Formatted Table")
    if bold_headers:
        st.write(f"<style>thead th {{ font-weight: bold; }}</style>", unsafe_allow_html=True)

    if show_gridlines:
        st.dataframe(df_display.style.set_table_styles(
            [{'selector': 'td, th', 'props': [('border', '1px solid black')]}]
        ).set_properties(**{'border': '1px solid black'}))
    else:
        st.dataframe(df_display)

    csv = df_display.to_csv(index=False).encode('utf-8')
    st.download_button("Download Cleaned Table as CSV", csv, "formatted_table.csv", "text/csv")
"""

# Save the Streamlit script
streamlit_script_path = "/mnt/data/triNetX_streamlit_app.py"
with open(streamlit_script_path, "w") as f:
    f.write(streamlit_script)

streamlit_script_path
