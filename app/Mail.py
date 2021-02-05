import smtplib, ssl
import yagmail
import logging

port = 25  # For SSL

class Email(object):
    def __init__(self, config, receiver, body, subject):
        self.config = config
        self.receiver = receiver
        self.body = body
        self.sender = self.config.get('QMServer', 'SendMail')
        self.subject = subject

    def sendMail(self):
        # Create a secure SSL context
        # context = ssl.create_default_context()
        # with smtplib.SMTP_SSL("smtp-relay.gmail.com", port, context=context) as server:
        #     try:
        #         server.login(self.sender, self.config.get('QMServer', 'SecKey'))
        #         server.sendmail(from_addr=self.sender, to_addrs=self.receiver, msg=self.body)
        #         logging.info('email is sended')
        #     except:
        #         logging.info('email is not sended')
        receiver = self.receiver
        body = self.body

        yag = yagmail.SMTP(self.config.get('QMServer', 'SendMail'), self.config.get('QMServer', 'SecKey'))
        yag.send(
            to=receiver,
            subject=self.subject,
            contents=body
        )




