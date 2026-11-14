from fpdf import FPDF
from datetime import date

def invoice_pdf(db_invoice, db_job, db_client,db_business):
    pdf=FPDF(orientation="P", format="A4", unit="mm")
    pdf.set_margin(16)
    pdf.add_page()
    pdf.set_text_color(0,0,0)
    pdf.set_font("Helvetica", "B", 32)
    pdf.cell(0,12,"Invoice", ln=True, align="C")
    pdf.set_font("Helvetica",size=10)
    pdf.cell(0,7, f"Invoice Number: {db_invoice.invoice_number}", align="C", border="B", ln=True)
    pdf.ln(2)
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(100, 16 , "Invoice Details", align="L", ln=True)
    pdf.ln(1)
    pdf.set_font("Helvetica",size=10)
    pdf.cell(90,7, f"GSTIN: {db_business.gst_number}", align="L")
    pdf.cell(0,7, f"Invoice Date: {date.today()}", align="R",ln=True)
    pdf.cell(0,0,border="B", ln=True)
    pdf.ln(8)
    pdf.set_font("Helvetica", "B", 18)
    pdf.cell(0,8, "BILL TO",align="C",ln=True)
    pdf.set_font("Helvetica", size=11)
    pdf.cell(0,6, f"Name: {db_client.name}", ln=True)
    pdf.multi_cell(0,6, f"Address: {db_client.address_line1} {db_client.city} ", ln=True)
    pdf.cell(90,6, f"Phone: {db_client.phone}", align="L")
    pdf.cell(0,6, f"Email: {db_client.email}", ln=True, align="R")
    pdf.ln(2)
    
    pdf.cell(0,0,border="B", ln=True)
    pdf.ln(8)
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 8, "JOB DETAILS", ln=True, align="C")
    pdf.set_font("Helvetica", size=10)
    pdf.cell(0,7, f"Title: {db_job.title}", ln=True)
    pdf.multi_cell(0,7, f"Description: {db_job.work} ", ln=True)
    pdf.ln(2)
    
    pdf.cell(0,0,border="B", ln=True)
    
    pdf.ln(4)
    
    pdf.set_font("Helvetica", "B",size=16)
    pdf.cell(0,8, 'Payment', ln=True, align="C")
    pdf.set_font("Helvetica","B", size=12)
    
    pdf.cell(100,9, "Description", align="L")
    pdf.cell(0,9, "Amount" , align="R", ln=True)
    pdf.set_font("Helvetica",size=11)
    pdf.cell(100, 11, "Subtotal", align="L")
    pdf.cell(0, 11, f"{db_invoice.total}", align="R", ln=True)
    
    pdf.cell(100, 11, "Discount", align="L")
    pdf.cell(0, 11, f"{db_invoice.discount}", align="R", ln=True)
    
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(100, 11, "Grand Total", align="L")
    pdf.cell(0, 11, f"{db_invoice.total - db_invoice.discount}", align="R", ln=True)
        
    return pdf.output()



def quotation_pdf(db_quotation, db_job, db_client,db_business):
    pdf=FPDF(orientation="P", format="A4", unit="mm")
    pdf.set_margin(16)
    pdf.add_page()
    pdf.set_text_color(0,0,0)
    pdf.set_font("Helvetica", "B", 32)
    pdf.cell(0,12,"Quotation", ln=True, align="C")
    pdf.set_font("Helvetica",size=10)
    pdf.cell(0,7, f"Quotation Number: {db_quotation.id}", align="C", border="B", ln=True)
    pdf.ln(2)
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(100, 16 , "Quotation Details", align="L", ln=True)
    pdf.ln(1)
    pdf.set_font("Helvetica",size=10)
    pdf.cell(90,7, f"GSTIN: {db_business.gst_number}", align="L")
    pdf.cell(0,7, f"Quotation Date: {date.today()}", align="R",ln=True)
    pdf.cell(0,0,border="B", ln=True)
    pdf.ln(8)
    pdf.set_font("Helvetica", "B", 18)
    pdf.cell(0,8, "Quotation TO",align="C",ln=True)
    pdf.set_font("Helvetica", size=11)
    pdf.cell(0,6, f"Name: {db_client.name}", ln=True)
    pdf.multi_cell(0,6, f"Address: {db_client.address_line1} {db_client.city} ", ln=True)
    pdf.cell(90,6, f"Phone: {db_client.phone}", align="L")
    pdf.cell(0,6, f"Email: {db_client.email}", ln=True, align="R")
    pdf.ln(2)
    
    pdf.cell(0,0,border="B", ln=True)
    pdf.ln(8)
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 8, "JOB DETAILS", ln=True, align="C")
    pdf.set_font("Helvetica", size=10)
    pdf.cell(0,7, f"Title: {db_job.title}", ln=True)
    pdf.multi_cell(0,7, f"Description: {db_job.work} ", ln=True)
    pdf.ln(2)
    
    pdf.cell(0,0,border="B", ln=True)
    
    pdf.ln(4)
    
    pdf.set_font("Helvetica", "B",size=16)
    pdf.cell(0,8, 'Payment', ln=True, align="C")
    pdf.set_font("Helvetica","B", size=12)
    
    pdf.cell(100,9, "Description", align="L")
    pdf.cell(0,9, "Amount" , align="R", ln=True)
    pdf.set_font("Helvetica",size=11)
    pdf.cell(100, 11, "Subtotal", align="L")
    pdf.cell(0, 11, f"{db_quotation.total}", align="R", ln=True)
    
    pdf.cell(100, 11, "Discount", align="L")
    pdf.cell(0, 11, f"{db_quotation.discount}", align="R", ln=True)
    
    pdf.set_font("Helvetica", "B", 12)
    
    pdf.cell(100, 11, "Grand Total", align="L")
    pdf.cell(0, 11, f"{db_quotation.total - db_quotation.discount}", align="R", ln=True)
        
    return pdf.output()
