import smtplib

from masonite.drivers.BaseMailDriver import BaseMailDriver

from email.message import EmailMessage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


class MailSmtpDriver(BaseMailDriver):
    """
    Mail smtp driver
    """
    def send(self, message_contents=None):
        config = self.config.DRIVERS['smtp']

        message = MIMEMultipart('alternative')

        if not message_contents:
            message_contents = self.message_body

        message_contents = MIMEText(message_contents, 'html')

        message['Subject'] = self.message_subject
        message['From'] = '{0} <{1}>'.format(self.config.FROM['name'], self.config.FROM['address'])
        message['To'] = self.to_address
        message.attach(message_contents)

        # Send the message via our own SMTP server.
        s = smtplib.SMTP('{0}:{1}'.format(config['host'], config['port']))
        s.login(config['username'], config['password'])

        # s.send_message(message)
        s.sendmail(self.config.FROM['name'], self.to_address, message.as_string())
        s.quit()
