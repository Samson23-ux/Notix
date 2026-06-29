import resend


class Email:
    def __init__(self, api_key: str):
        self._api_key = api_key
        resend.api_key = self._api_key

    def send(self, sender: str, recipient: str, subject: str, body: str):
        resend.Emails.send(
            {
                "from": sender,
                "to": recipient,
                "subject": subject,
                "html": body,
            }
        )
