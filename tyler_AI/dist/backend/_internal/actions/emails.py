import smtplib
import imaplib
import email
from bs4 import BeautifulSoup
from email.header import decode_header
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


import configs

class Emails:
    def clean_html(self,html_text):

        soup = BeautifulSoup(html_text, 'html.parser')
        return soup.get_text(separator='\n', strip=True)

    def send_email(self,txt,receiver_email,sender_email,smtp_server,password,subject = '',port = 587):
        message = MIMEMultipart()
        message['Subject'] = subject
        message['From'] = sender_email
        message['To'] = receiver_email

        text = MIMEText(txt)
        message.attach(text)
        try:
            server = smtplib.SMTP(smtp_server, port)
            server.starttls()
            server.login(sender_email, password)
            server.sendmail(sender_email, receiver_email, message.as_string())
            print("Письмо отправлено!")
        except Exception as e:
            print(f"Ошибка: {e}")
        finally:
            server.quit()
    def check_for_emails(self,sender_email,smtp_server,password,port = 587):
        mail = imaplib.IMAP4_SSL(smtp_server,993)
        mail.login(sender_email,password)
        mail.select("INBOX")
        status,messages = mail.search(None,"ALL")
        messages = messages[0].split()

        emails = []

        for msg_id in messages[-10:]:
            status, data = mail.fetch(msg_id, '(RFC822)')
            raw_email=data[0][1]
            msg = email.message_from_bytes(raw_email)
            subject = decode_header(msg['Subject'])[0][0]
            if isinstance(subject, bytes):
                subject = subject.decode()

            # Отправитель
            from_ = msg.get('From')

            # Дата
            date = msg.get('Date')

            # Тело письма
            body = ""
            if msg.is_multipart():
                for part in msg.walk():
                    content_type = part.get_content_type()
                    content_disposition = str(part.get("Content-Disposition"))

                    if content_type == "text/plain" and "attachment" not in content_disposition:
                        body = part.get_payload(decode=True).decode(errors='ignore')
                        break

                    elif content_type == "text/html" and "attachment" not in content_disposition and not body:
                        html_body = part.get_payload(decode=True).decode(errors='ignore')
                        body = self.clean_html(html_body)
            else:
                content_type = msg.get_content_type()
                body = msg.get_payload(decode=True).decode(errors='ignore')
                if content_type == "text/html":
                    body = self.clean_html(body)

            emails.append({
                'id': msg_id.decode(),
                'subject': subject,
                'from': from_,
                'date': date,
                'body': body[:500]  # Только первые 500 символов
            })

            # Пометить как прочитанное (опционально)
            mail.store(msg_id, '+FLAGS', '\\Seen')

        mail.close()
        mail.logout()
        for x in range(len(emails)):
            print("Вам пришло сообщение на почту")
            print(f"От {emails[x]['from']}")
            print(f"Дата {emails[x]['date'][:-6]}")
            print(f"Тема {emails[x]['subject']}")
            print( emails[x]["body"])


    def run(self, params, chat_id: str):
        action = params.get("action")
        your_email = configs.USER_EMAIL
        receiver_email = params.get("receiver_email")
        password = configs.EMAIL_PASSWORD
        text = params.get("text")
        subject = params.get("subject")
        smtp_server = f"smtp.{your_email.split('@')[1]}"
        em = Emails()
        if action == "send_email":
            em.send_email(text,receiver_email,your_email,smtp_server,password,subject)
        if action == "check_for_emails":
            em.check_for_emails(your_email,smtp_server,password)
