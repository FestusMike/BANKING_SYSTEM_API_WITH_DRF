from django.utils import timezone
from io import BytesIO
from sib_api_v3_sdk.rest import ApiException
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Image, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.units import inch
from pathlib import Path
from datetime import datetime
import os
import sib_api_v3_sdk


def generate_ledger_pdf(ledger_entries, user, start_date, end_date):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()

    elements = []

    root_dir = Path(__file__).resolve().parent.parent
    logo_path = root_dir / "2-lane 2-way ahead.jpg"
    img = Image(logo_path, 2 * inch, 1 * inch)
    img.hAlign = "CENTER"
    elements.append(img)

    elements.append(Spacer(1, 12))
    elements.append(Paragraph("Account Statement", styles["Title"]))

    if isinstance(start_date, datetime) and isinstance(end_date, datetime):
        formatted_start_date = start_date.strftime("%d %B, %Y")
        formatted_end_date = end_date.strftime("%d %B, %Y")
        elements.append(Paragraph(f"Statement Period: {formatted_start_date} to {formatted_end_date}", styles["Heading3"]))
    else:
        elements.append(Paragraph("Statement Period: Complete History", styles["Heading3"]))

    for account in user.accounts.all():
        current_balance = account.current_balance
        elements.append(Paragraph(f"Current Balance: {current_balance}", styles["Heading3"]))
        elements.append(Paragraph("Currency: Naira", styles["BodyText"]))

        account_info = f"Account Number: {account.account_number}"
        elements.append(Paragraph(account_info, styles["BodyText"]))

        total_credit = sum(
            entry.transaction.amount
            for entry in ledger_entries
            if entry.transaction.transaction_type == "CREDIT"
            and entry.account == account
        )
        total_debit = sum(
            entry.transaction.amount
            for entry in ledger_entries
            if entry.transaction.transaction_type == "DEBIT"
            and entry.account == account
        )
        elements.append(Paragraph(f"Total Credit: {total_credit}", styles["BodyText"]))
        elements.append(Paragraph(f"Total Debit: {total_debit}", styles["BodyText"]))

        account_type = "Savings"
        num_credits = sum(
            1 for entry in ledger_entries if entry.transaction.transaction_type == "CREDIT" and entry.account == account
        )
        num_debits = sum(
            1 for entry in ledger_entries if entry.transaction.transaction_type == "DEBIT" and entry.account == account
        )
        elements.append(Paragraph(f"Account Type: {account_type}", styles["BodyText"]))
        elements.append(Paragraph(f"Credit Count: {num_credits}", styles["BodyText"]))
        elements.append(Paragraph(f"Debit Count: {num_debits}", styles["BodyText"]))

    elements.append(Paragraph(f"Statement Printed: {timezone.localtime().strftime('%d %B, %Y')}", styles["BodyText"]))
    elements.append(Spacer(1, 15))

    data = [
        ["Date", "Transaction ID", "Type", "Description", "Amount", "Balance After Transaction"]
    ]
    for entry in ledger_entries:
        data.append([
            entry.transaction.timestamp.strftime("%Y-%m-%d"),
            entry.transaction.transaction_id,
            entry.transaction.transaction_type,
            entry.transaction.description,
            entry.transaction.amount,
            entry.balance_after_transaction,
        ])

    table = Table(data)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.white),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
        ("BACKGROUND", (0, 1), (-1, -1), colors.white),
        ("GRID", (0, 0), (-1, -1), 1, colors.green),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
    ]))

    elements.append(table)
    doc.build(elements)
    pdf = buffer.getvalue()
    buffer.close()
    return pdf


def send_attachment_email(to, reply_to, html_content, sender, subject, attachment):
    try:
        configuration = sib_api_v3_sdk.Configuration()
        configuration.api_key["api-key"] = os.getenv("EMAIL_API_KEY")
        api_instance = sib_api_v3_sdk.TransactionalEmailsApi(
            sib_api_v3_sdk.ApiClient(configuration)
        )
        send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
            to=to,
            reply_to=reply_to,
            html_content=html_content,
            sender=sender,
            subject=subject,
            attachment=attachment
        )
        api_response = api_instance.send_transac_email(send_smtp_email)

        print("Email sent successfully:", api_response)

        return "Success"

    except ApiException as e:
        print("Exception when calling SMTPApi->send_transac_email:", e)
        return "Fail"
