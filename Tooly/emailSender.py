import smtplib
from email.mime.text import MIMEText

to = ["natutaylor@gmail.com"]
APP_PASS = "feeg fhhr haxn eabn"
sender = "toolyrobot@gmail.com"
password = "iamarobottooly"




def sendEmail(msg):
    msg["Subject"] = "Message of Tooly Robot"
    msg["From"] = sender
    msg["To"] =  ','.join(to)
    smtpServer = smtplib.SMTP_SSL('smtp.gmail.com',465)
    smtpServer.login(sender,APP_PASS)
    smtpServer.sendmail(sender,to,msg.as_string())
    smtpServer.quit()
    print("email send!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")



