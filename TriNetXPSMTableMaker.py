# Create a streamlined Streamlit script that skips preview and focuses on export only
export_only_script = """
# streamlit_app.py
import streamlit as st
import pandas as pd
from io import BytesIO
from docx import Document
from docx.shared import Pt
from fpdf import FPDF

st.title("TriNetX Table Formatter: Export Only")

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

def generate_word(df, font_size=10, align="left"):
    doc = Document()
    doc.add_heading('Formatted Table', level=1)
    table = doc.add_table(rows=1, cols=len(df.columns))
    table.style = 'Table Grid'

    hdr_cells = table.rows[0].cells
    for i, col in enumerate(df.columns):
        hdr_cells[i].text = str(col)
        run = hdr_cells[i].paragraphs[0].runs[0]
        run.font.size = Pt(font_size)
        hdr_cells[i].paragraphs[0].alignment = {"left": 0, "center": 1, "right": 2}.get(align, 0)

    for _, row in df.iterrows():
        row_cells = table.add_row().cells
        for i, cell in enumerate(row):
            row_cells[i].text = str(cell)
            run = row_cells[i].paragraphs[0].runs[0]
            run.font.size = Pt(font_size)
            row_cells[i].paragraphs[0].alignment = {"left": 0, "center": 1, "right": 2}.get(align, 0)

    buf = BytesIO()
    doc.save(buf)
    buf.seek(0)
    return buf

def generate_pdf(df, font_size=8, align="L"):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=font_size)
    col_width = pdf.w / (len(df.columns) + 1)
    row_height = font_size + 2

    for col in df.columns:
        pdf.cell(col_width, row_height, str(col), border=1, align=align)
    pdf.ln(row_height)

    for _, row in df.iterrows():
        for item in row:
            pdf.cell(col_width, row_height, str(item), border=1, align=align)
        pdf.ln(row_height)

    buf = BytesIO()
    pdf.output(buf)
    buf.seek(0)
    return buf

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    cleaned_df = extract_clean_table(df)

    st.sidebar.header("Export Options")
    decimals = st.sidebar.slider("Decimal Places", 0, 5, 2)

    word_font_size = st.sidebar.slider("Word Font Size", 6, 14, 10)
    word_align = st.sidebar.selectbox("Word Text Alignment", ["left", "center", "right"])

    pdf_font_size = st.sidebar.slider("PDF Font Size", 6, 14, 8)
    pdf_align = st.sidebar.selectbox("PDF Text Alignment", ["L", "C", "R"])

    df_export = cleaned_df.copy()
    for col in df_export.columns:
        try:
            df_export[col] = df_export[col].astype(float).round(decimals)
        except:
            pass

    # Export buttons
    csv = df_export.to_csv(index=False).encode('utf-8')
    st.download_button("Download CSV", csv, "formatted_table.csv", "text/csv")

    word_file = generate_word(df_export, font_size=word_font_size, align=word_align)
    st.download_button("Download as Word", word_file, "formatted_table.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")

    pdf_file = generate_pdf(df_export, font_size=pdf_font_size, align=pdf_align)
    st.download_button("Download as PDF", pdf_file, "formatted_table.pdf", "application/pdf")
"""

# Save the streamlined export-only script
export_only_path = "/mnt/data/streamlit_app_export_only.py"
with open(export_only_path, "w") as f:
    f.write(export_only_script)

export_only_path
