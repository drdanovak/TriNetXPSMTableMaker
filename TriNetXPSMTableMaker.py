# Updated Streamlit app script with export options to Word and PDF
from textwrap import dedent

export_script = dedent("""
# streamlit_app.py
import streamlit as st
import pandas as pd
from io import BytesIO
from docx import Document
from docx.shared import Inches
from fpdf import FPDF

st.title("TriNetX Table Formatter for Journal Submission")

uploaded_file = st.file_uploader("Upload your TriNetX CSV file", type="csv")

def extract_clean_table(df):
    for i, row in df.iterrows():
        if "Characteristic" in str(row[0]):
            data_start_index = i
            break
    df_clean = df.iloc[data_start_index:].reset_index(drop=True)
    df_clean.columns = df_clean.iloc[0]
    df_clean = df_clean[1:].reset_index(drop=True)
    return df_clean

def generate_word(df):
    doc = Document()
    doc.add_heading('Formatted Table', level=1)
    table = doc.add_table(rows=1, cols=len(df.columns))
    hdr_cells = table.rows[0].cells
    for i, col in enumerate(df.columns):
        hdr_cells[i].text = str(col)
    for index, row in df.iterrows():
        row_cells = table.add_row().cells
        for i, cell in enumerate(row):
            row_cells[i].text = str(cell)
    buf = BytesIO()
    doc.save(buf)
    buf.seek(0)
    return buf

def generate_pdf(df):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=8)
    col_width = pdf.w / (len(df.columns) + 1)
    row_height = 6

    # Add header
    for col in df.columns:
        pdf.cell(col_width, row_height, str(col), border=1)
    pdf.ln(row_height)

    # Add data rows
    for _, row in df.iterrows():
        for item in row:
            pdf.cell(col_width, row_height, str(item), border=1)
        pdf.ln(row_height)

    buf = BytesIO()
    pdf.output(buf)
    buf.seek(0)
    return buf

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
        styled = df_display.style.set_table_styles(
            [{'selector': 'td, th', 'props': [('border', '1px solid black')]}]
        ).set_properties(**{'border': '1px solid black'})
        st.write(styled)
    else:
        st.write(df_display)

    csv = df_display.to_csv(index=False).encode('utf-8')
    st.download_button("Download CSV", csv, "formatted_table.csv", "text/csv")

    word_file = generate_word(df_display)
    st.download_button("Download as Word", word_file, "formatted_table.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")

    pdf_file = generate_pdf(df_display)
    st.download_button("Download as PDF", pdf_file, "formatted_table.pdf", "application/pdf")
""")

# Save the export-enabled Streamlit app
export_script_path = "/mnt/data/streamlit_app_with_export.py"
with open(export_script_path, "w") as f:
    f.write(export
