import streamlit as st
import pandas as pd
import numpy as np
import fitz  # PyMuPDF
import io

st.set_page_config(page_title="Marcus Commission Calculator", layout="wide")
st.title("📊 Marcus Commission Calculator")

st.markdown("""
Upload your monthly sales CSV to automatically evaluate key performance metrics for Marcus.

### 📂 How to Export Your Sales CSV from Power BI:
1. Log into **Power BI**  
2. Go to **WZ Sales Analysis**  
3. Scroll to the bottom and select **KPI Details**  
4. At the top, click **Employee**  
5. Click the **three dots (⋯)** next to "More Options"  
6. Select **Export data**  
7. Choose **Summarized data**  
8. Select **.CSV** as the file format and save it to your computer  
9. Upload the CSV file below ⬇️
""")

uploaded_file = st.file_uploader("📁 Upload your sales CSV file", type=["csv"])
uploaded_pdf = st.file_uploader("📄 Upload Marcus Settlement Template (PDF)", type=["pdf"])

# --- KPI Thresholds ---
thresh_gp = 25000
thresh_vmp = 55
thresh_gp_per_smt = 460
thresh_vhi_fios = 8

def generate_filled_pdf(template_bytes, gp_amount, commission_rate):
    doc = fitz.open(stream=template_bytes, filetype="pdf")
    page = doc[0]

    # --- Step 1: White-out below GP ---
    whiteout_gp_section = fitz.Rect(0, 290, page.rect.width, page.rect.height)
    page.draw_rect(whiteout_gp_section, fill=(1, 1, 1), color=(1, 1, 1))

    # --- Step 2: White-out Draws area except % box ---
    page.draw_rect(fitz.Rect(0, 310, 360, page.rect.height), fill=(1, 1, 1))
    page.draw_rect(fitz.Rect(420, 310, page.rect.width, page.rect.height), fill=(1, 1, 1))

    # --- Step 3: Insert fresh values ---
    gp_coords = (145, 280)
    percent_coords = (370, 280)

    page.insert_text(gp_coords, f"${gp_amount:,.2f}", fontsize=12, fontname="helv", fill=(0, 0, 0))
    page.insert_text(percent_coords, f"{commission_rate}%", fontsize=12, fontname="helv", fill=(0, 0, 0))

    output = io.BytesIO()
    doc.save(output)
    doc.close()
    output.seek(0)
    return output

if uploaded_file is not None:
    try:
        df = pd.read_csv(uploaded_file)
        df.columns = [col.strip() for col in df.columns]
        df['Employee Full Name'] = df['Employee Full Name'].astype(str).fillna('')

        marcus_df = df[df['Employee Full Name'].str.lower().str.contains("marcus")].copy()

        if marcus_df.empty:
            st.warning("No records found for Marcus. Please check the CSV file.")
        else:
            # --- Clean data ---
            marcus_df['GP'] = pd.to_numeric(marcus_df['GP'].astype(str).str.replace(r'[$,]', '', regex=True), errors='coerce')
            marcus_df['VZ Perks Rate'] = pd.to_numeric(marcus_df['VZ Perks Rate'].astype(str).str.replace('%', ''), errors='coerce')
            marcus_df['GP Per SMT'] = pd.to_numeric(marcus_df['GP Per SMT'].astype(str).str.replace(r'[$,]', '', regex=True), errors='coerce')
            marcus_df['VZ FWA GA'] = pd.to_numeric(marcus_df['VZ FWA GA'], errors='coerce')
            marcus_df['VZ FIOS GA'] = pd.to_numeric(marcus_df['VZ FIOS GA'], errors='coerce')

            marcus = marcus_df.iloc[-1]  # Latest record

            # --- KPI checks ---
            met_gp = marcus['GP'] >= thresh_gp if not pd.isna(marcus['GP']) else False
            met_vmp = marcus['VZ Perks Rate'] >= thresh_vmp if not pd.isna(marcus['VZ Perks Rate']) else False
            met_gp_per_smt = marcus['GP Per SMT'] >= thresh_gp_per_smt if not pd.isna(marcus['GP Per SMT']) else False
            vhi_fios_total = (marcus['VZ FWA GA'] or 0) + (marcus['VZ FIOS GA'] or 0)
            met_vhi_fios = vhi_fios_total >= thresh_vhi_fios

            all_targets_met = all([met_gp, met_vmp, met_gp_per_smt, met_vhi_fios])
            commission_rate = 0.30 if all_targets_met else 0.25
            commission_earned = marcus['GP'] * commission_rate if not pd.isna(marcus['GP']) else 0

            # --- Show Summary ---
            summary_df = pd.DataFrame({
                "Metric": [
                    "Gross Profit", "VMP (VZ Perks Rate)", "GP Per Smartphone", "VHI/FIOS Activations"
                ],
                "Value": [
                    f"${marcus['GP']:,.2f}", f"{marcus['VZ Perks Rate']:.2f}%", f"${marcus['GP Per SMT']:,.2f}", f"{int(vhi_fios_total)}"
                ],
                "Threshold": [
                    f">= ${thresh_gp:,}", f">= {thresh_vmp}%", f">= ${thresh_gp_per_smt}", f">= {thresh_vhi_fios}"
                ],
                "Met?": [
                    "Yes" if met_gp else "No", "Yes" if met_vmp else "No",
                    "Yes" if met_gp_per_smt else "No", "Yes" if met_vhi_fios else "No"
                ]
            })

            st.subheader("📋 Marcus Performance Summary")
            st.dataframe(summary_df, use_container_width=True)

            st.subheader("💰 Commission Calculator")
            st.markdown(f"**Commission Rate:** {'30%' if all_targets_met else '25%'}")
            st.markdown(f"**Commission Earned:** ${commission_earned:,.2f}")

            if uploaded_pdf:
                pdf_bytes = uploaded_pdf.read()
                filled_pdf = generate_filled_pdf(pdf_bytes, marcus['GP'], int(commission_rate * 100))
                st.download_button("📥 Download Settlement PDF", data=filled_pdf, file_name="Marcus_Settlement.pdf", mime="application/pdf")
            else:
                st.info("⬆️ Upload the settlement template PDF to generate the completed statement.")

            st.markdown("---")
            st.subheader("📘 Commission Structure Explained")
            st.markdown("""
Your commission is based on whether you meet or exceed **four key performance thresholds** for the month:

1. **Gross Profit (GP)** must be at least **$25,000**  
2. **VZ Perks Rate (VMP)** must be **55% or higher**  
3. **Gross Profit Per Smartphone (GP/SMT)** must be **$460 or more**  
4. **VHI/FIOS Activations** (combined total of FWA GA + FIOS GA) must be **8 or more**

### 💸 Commission Payout Logic:
- If **all 4 metrics are met**, your commission rate is **30% of your total GP**  
- If **any metric is missed**, your commission rate is **25% of your total GP**

This tool automatically checks all metrics, calculates your commission, and generates a PDF settlement statement.
""")

    except Exception as e:
        st.error(f"❌ Error processing file: {e}")
