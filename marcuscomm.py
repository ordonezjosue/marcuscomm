import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
from dateutil.relativedelta import relativedelta
from reportlab.lib.pagesizes import LETTER
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
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

# --- KPI Thresholds ---
thresh_gp = 25000
thresh_vmp = 55
thresh_gp_per_smt = 460
thresh_vhi_fios = 8

# --- PDF Generator Function ---
def generate_filled_pdf_from_scratch(gp_amount, commission_rate, draws=1800, num_draws=3):
    buffer = io.BytesIO()
    future_date = datetime.today() + relativedelta(months=2)
    month_label = future_date.strftime("%B %Y")
    file_label = future_date.strftime("%B_%Y")

    doc = SimpleDocTemplate(buffer, pagesize=LETTER, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
    styles = getSampleStyleSheet()
    elements = []

    title_style = ParagraphStyle(
        'TitleStyle', fontSize=14, alignment=1,
        textColor=colors.white, backColor=colors.lightblue,
        spaceAfter=12, spaceBefore=12
    )
    elements.append(Paragraph(f"MARCUS ALTMAN {month_label.upper()} COMMISSION SETTLEMENT STATEMENT", title_style))

    body_text = f"""
    Dear Marcus Altman,<br/><br/>
    <b>Elypse</b> Systems and Solutions Inc presents to you your commission statement per the compensation structure and your results in {month_label.split()[0]}. You will be paid tier 3 at {commission_rate}%, this is in accordance to your performance and compensation structure.
    """
    elements.append(Paragraph(body_text, styles['Normal']))
    elements.append(Spacer(1, 20))
    elements.append(Paragraph("Here is the details and breakdown:", styles['Normal']))
    elements.append(Spacer(1, 10))

    net_commission = gp_amount * (commission_rate / 100)
    paid_total = net_commission - draws

    table_data = [
        ["MARCUS ALTMAN", "TOTAL BREAKDOWN", "Draws & Rates"],
        ["GROSS PROFIT", f"${gp_amount:,.2f}", f"{commission_rate}%"],
        ["NET COMMISSION", f"${net_commission:,.2f}", ""],
        ["PAID TOTAL Draw", "", ""],
        ["Paid Total Commission", f"${paid_total:,.2f}", ""]
    ]

    table = Table(table_data, colWidths=[160, 200, 160])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.black),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('ALIGN', (1,1), (2,2), 'RIGHT'),
        ('ALIGN', (1,4), (2,4), 'RIGHT'),
        ('BACKGROUND', (0,4), (-1,4), colors.green),
        ('TEXTCOLOR', (0,4), (-1,4), colors.white),
        ('FONTNAME', (0,4), (-1,4), 'Helvetica-Bold')
    ]))

    elements.append(table)
    elements.append(Spacer(1, 20))

    footer_text = f"""
    Keep in mind there is no draw for this upcoming week pay date. Total owed to you is <b>${paid_total:,.2f}</b>. Any chargebacks for {month_label.split()[0]} may appear in future settlements within 180 days. If you accept this statement as final, please reply via e-mail. For any questions or disputes, respond within one business day. You can reach me at <a href='mailto:Thimotee.Wiguen@wireless-zone.com'>Thimotee.Wiguen@wireless-zone.com</a>.
    <br/><br/>Thank you.<br/><br/><font color='red'><i>-Wiguen</i></font>
    """
    elements.append(Paragraph(footer_text, styles['Normal']))

    doc.build(elements)
    buffer.seek(0)
    return buffer, file_label

# --- Main App Logic ---
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

            st.subheader("📋 Marcus Performance Summary")
            summary_df = pd.DataFrame({
                "Metric": ["Gross Profit", "VMP (VZ Perks Rate)", "GP Per Smartphone", "VHI/FIOS Activations"],
                "Value": [
                    f"${marcus['GP']:,.2f}",
                    f"{marcus['VZ Perks Rate']:.2f}%",
                    f"${marcus['GP Per SMT']:,.2f}",
                    f"{int(vhi_fios_total)}"
                ],
                "Threshold": [
                    f">= ${thresh_gp:,}", f">= {thresh_vmp}%", f">= ${thresh_gp_per_smt}", f">= {thresh_vhi_fios}"
                ],
                "Met?": [
                    "Yes" if met_gp else "No",
                    "Yes" if met_vmp else "No",
                    "Yes" if met_gp_per_smt else "No",
                    "Yes" if met_vhi_fios else "No"
                ]
            })
            st.dataframe(summary_df, use_container_width=True)

            st.subheader("💰 Commission Calculator")
            st.markdown(f"**Commission Rate:** {'30%' if all_targets_met else '25%'}")
            st.markdown(f"**Commission Earned:** ${commission_earned:,.2f}")

            pdf_bytes, month_label = generate_filled_pdf_from_scratch(
                gp_amount=marcus['GP'],
                commission_rate=int(commission_rate * 100),
                draws=1800,
                num_draws=3
            )

            st.download_button(
                "📥 Download Settlement Statement",
                data=pdf_bytes,
                file_name=f"Marcus_Settlement_{month_label}.pdf",
                mime="application/pdf"
            )

    except Exception as e:
        st.error(f"❌ Error processing file: {e}")
