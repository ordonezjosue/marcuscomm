import streamlit as st
import pandas as pd
import numpy as np
from reportlab.lib.pagesizes import LETTER
from reportlab.pdfgen import canvas
from datetime import datetime
from dateutil.relativedelta import relativedelta
import io

st.set_page_config(page_title="Marcus Commission Calculator", layout="wide")
st.title("\U0001F4CA Marcus Commission Calculator")

st.markdown("""
Upload your monthly sales CSV to automatically evaluate key performance metrics for Marcus.

### \U0001F4C2 How to Export Your Sales CSV from Power BI:
1. Log into **Power BI**  
2. Go to **WZ Sales Analysis**  
3. Scroll to the bottom and select **KPI Details**  
4. At the top, click **Employee**  
5. Click the **three dots (\u22EF)** next to "More Options"  
6. Select **Export data**  
7. Choose **Summarized data**  
8. Select **.CSV** as the file format and save it to your computer  
9. Upload the CSV file below ⬇️
""")

# Upload sales CSV
uploaded_file = st.file_uploader("\U0001F4C1 Upload your sales CSV file", type=["csv"])

# KPI Thresholds
thresh_gp = 25000
thresh_vmp = 55
thresh_gp_per_smt = 460
thresh_vhi_fios = 8

def generate_filled_pdf_from_scratch(gp_amount, commission_rate, draws=1800, num_draws=3):
    output = io.BytesIO()
    c = canvas.Canvas(output, pagesize=LETTER)
    width, height = LETTER

    # Calculate future statement month
    future_date = datetime.today() + relativedelta(months=2)
    month_label = future_date.strftime("%B %Y")

    # Title & Header
    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(width / 2, height - 60, f"MARCUS ALTMAN {month_label.upper()} COMMISSION SETTLEMENT STATEMENT")
    c.setFont("Helvetica", 11)
    c.drawString(50, height - 100, "Dear Marcus Altman,")
    c.drawString(50, height - 120, "Elypse Systems and Solutions Inc presents to you your commission statement per")
    c.drawString(50, height - 135, "the compensation structure and your results for the reporting period.")

    # Data section
    y = height - 180
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "MARCUS ALTMAN TOTAL BREAKDOWN")
    c.setFont("Helvetica", 11)
    y -= 20
    c.drawString(50, y, f"TOTAL GP EARNED")
    c.drawString(300, y, f"${gp_amount:,.2f}")
    y -= 20
    c.drawString(50, y, "DRAWS & RATES")
    c.drawString(300, y, f"{int(commission_rate)}%")

    # Commission calculation
    net_commission = gp_amount * (commission_rate / 100)
    paid_total = net_commission - draws

    y -= 30
    c.drawString(50, y, f"NET COMMISSION")
    c.drawString(300, y, f"${net_commission:,.2f}")
    y -= 20
    c.drawString(50, y, f"PAID TOTAL Draw (${draws:,.2f}) {num_draws} Draws")
    y -= 20
    c.drawString(50, y, f"Paid Total Commission")
    c.drawString(300, y, f"${paid_total:,.2f}")

    # Footer
    y -= 50
    c.drawString(50, y, f"Keep in mind there is no draw for this upcoming week. Total owed to you is ${paid_total:,.2f}.")
    y -= 20
    c.drawString(50, y, f"Chargebacks may still apply and can show up in future settlements up to 180 days.")
    y -= 40
    c.drawString(50, y, f"Please reply via e-mail to accept this statement as final or to dispute within 1 business day.")
    y -= 30
    c.drawString(50, y, f"Thank you,")
    y -= 20
    c.drawString(50, y, f"- Wiguen")

    c.showPage()
    c.save()
    output.seek(0)
    return output, future_date.strftime("%B_%Y")

if uploaded_file is not None:
    try:
        df = pd.read_csv(uploaded_file)
        df.columns = [col.strip() for col in df.columns]
        df['Employee Full Name'] = df['Employee Full Name'].astype(str).fillna('')

        marcus_df = df[df['Employee Full Name'].str.lower().str.contains("marcus")].copy()

        if marcus_df.empty:
            st.warning("No records found for Marcus. Please check the CSV file.")
        else:
            marcus_df['GP'] = pd.to_numeric(marcus_df['GP'].astype(str).str.replace(r'[$,]', '', regex=True), errors='coerce')
            marcus_df['VZ Perks Rate'] = pd.to_numeric(marcus_df['VZ Perks Rate'].astype(str).str.replace('%', ''), errors='coerce')
            marcus_df['GP Per SMT'] = pd.to_numeric(marcus_df['GP Per SMT'].astype(str).str.replace(r'[$,]', '', regex=True), errors='coerce')
            marcus_df['VZ FWA GA'] = pd.to_numeric(marcus_df['VZ FWA GA'], errors='coerce')
            marcus_df['VZ FIOS GA'] = pd.to_numeric(marcus_df['VZ FIOS GA'], errors='coerce')

            marcus = marcus_df.iloc[-1]

            met_gp = marcus['GP'] >= thresh_gp if not pd.isna(marcus['GP']) else False
            met_vmp = marcus['VZ Perks Rate'] >= thresh_vmp if not pd.isna(marcus['VZ Perks Rate']) else False
            met_gp_per_smt = marcus['GP Per SMT'] >= thresh_gp_per_smt if not pd.isna(marcus['GP Per SMT']) else False
            vhi_fios_total = (marcus['VZ FWA GA'] or 0) + (marcus['VZ FIOS GA'] or 0)
            met_vhi_fios = vhi_fios_total >= thresh_vhi_fios

            all_targets_met = all([met_gp, met_vmp, met_gp_per_smt, met_vhi_fios])
            commission_rate = 0.30 if all_targets_met else 0.25
            commission_earned = marcus['GP'] * commission_rate if not pd.isna(marcus['GP']) else 0

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

            st.subheader("\U0001F4CB Marcus Performance Summary")
            st.dataframe(summary_df, use_container_width=True)

            st.subheader("\U0001F4B0 Commission Calculator")
            st.markdown(f"**Commission Rate:** {'30%' if all_targets_met else '25%'}")
            st.markdown(f"**Commission Earned:** ${commission_earned:,.2f}")

            pdf_bytes, month_label = generate_filled_pdf_from_scratch(
                gp_amount=marcus['GP'],
                commission_rate=int(commission_rate * 100),
                draws=1800,
                num_draws=3
            )

            st.download_button(
                "\U0001F4E5 Download Settlement Statement",
                data=pdf_bytes,
                file_name=f"Marcus_Settlement_{month_label}.pdf",
                mime="application/pdf"
            )

            st.markdown("---")
            st.subheader("\U0001F4D8 Commission Structure Explained")
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
