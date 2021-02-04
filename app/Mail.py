import smtplib, ssl
import yagmail

port = 465  # For SSL

class Email(object):
    def __init__(self, config, receiver, body):
        self.config = config
        self.receiver = receiver
        self.body = body
        self.sender = self.config.get('QMServer', 'SendMail')

    def sendMail(self):
        # Create a secure SSL context
        # context = ssl.create_default_context()
        # with smtplib.SMTP_SSL("smtp.gmail.com", port, context=context) as server:
        #     server.login(self.sender, self.config.get('QMServer', 'SecKey'))
        #     server.sendmail(from_addr=self.sender, to_addrs=self.receiver, msg=self.body)
        receiver = self.receiver
        body = self.body

        yag = yagmail.SMTP("dungdm91@gmail.com", "dungngo0")
        yag.send(
            to=receiver,
            subject="Yagmail test with attachment",
            contents=body
        )




