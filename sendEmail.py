import smtplib, ssl
from email.mime.text import MIMEText
from datetime import date

def sendEmail(message):
    """
    sends email with given user and password using smtp. takes message as string or
    html in docstring
    """
    sender = '********@gmail.com'
    receivers = ['********', '********']
    body_of_email = message

    msg = MIMEText(body_of_email, 'html')
    msg['Subject'] = 'Profitable shoes as of {}'.format(date.today())
    msg['From'] = sender
    msg['To'] = ','.join(receivers)

    s = smtplib.SMTP_SSL(host = 'smtp.gmail.com', port = 465)
    s.login(user = '***********', password = '*********')
    s.sendmail(sender, receivers, msg.as_string())
    s.quit()
