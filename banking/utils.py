from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from sib_api_v3_sdk.rest import ApiException
import os
import sib_api_v3_sdk


def generate_ledger_pdf(ledger_entries):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    elements = []
    elements.append(Paragraph("Statement of Account", styles["Title"]))

    data = [
        [
            "Date",
            "Transaction ID",
            "Type",
            "Description",
            "Amount",
            "Balance After Transaction",
        ]
    ]
    for entry in ledger_entries:
        data.append(
            [
                entry.transaction.timestamp.strftime("%Y-%m-%d"),
                str(entry.transaction.transaction_id),
                entry.transaction.transaction_type,
                entry.transaction.description,
                f"{entry.transaction.amount:.2f}",
                f"{entry.balance_after_transaction:.2f}",
            ]
        )

    table = Table(data)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
                ("GRID", (0, 0), (-1, -1), 1, colors.black),
            ]
        )
    )

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
