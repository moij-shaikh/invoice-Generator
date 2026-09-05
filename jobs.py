async def send_verification_email(otp,email):
    import smtplib
    from email.message import EmailMessage

    msg=EmailMessage()
    msg["From"]=""
    msg["To"]=email
    msg["Subject"]="Account Verification by MS"
    msg.add_alternative(f"<a href=''>Click</a>",subtype="html")
    with smtplib.SMTP_SSL("smtp.gmail.com",465) as smtp:
        smtp.login("sender","pass")