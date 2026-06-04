from abc import ABC, abstractmethod
from shared_lib.core.config import settings
import smtplib
from email.message import EmailMessage

class EmailTemplate(ABC):
    @abstractmethod
    def subject(self) -> str:
        pass
    @abstractmethod
    def body(self) -> str:
        pass

class VerificationEmail(EmailTemplate):

    def __init__(self, token: str):
        self.token = token

    def subject(self):
        return "Verify your account"

    def body(self):
        verification_link = (
            f"{settings.CLIENT_URL}/verify?token={self.token}"
        )

        return f"""
        <!DOCTYPE html>
        <html>
        <body style="font-family: Arial, sans-serif; background:#f4f4f4; padding:40px;">
            <div style="
                max-width:600px;
                margin:auto;
                background:white;
                padding:40px;
                border-radius:12px;
                box-shadow:0 2px 10px rgba(0,0,0,0.1);
            ">
                <h2 style="color:#222;">
                    Verify your email address
                </h2>

                <p>
                    Welcome! Thanks for creating an account.
                </p>

                <p>
                    Please verify your email address to activate your account.
                </p>

                <div style="margin:30px 0;">
                    <a
                        href="{verification_link}"
                        style="
                            background:#2563eb;
                            color:white;
                            text-decoration:none;
                            padding:12px 24px;
                            border-radius:8px;
                            display:inline-block;
                        "
                    >
                        Verify Email
                    </a>
                </div>

                <p style="color:#666;">
                    If you didn't create this account, you can safely ignore this email.
                </p>

                <hr>

                <p style="font-size:12px;color:#888;">
                    This verification link may expire after 15 minutes.
                </p>
            </div>
        </body>
        </html>
        """

class ForgotPasswordEmail(EmailTemplate):

    def __init__(self, token: str):
        self.token = token

    def subject(self):
        return "Reset your password"

    def body(self):
        reset_link = (
            f"{settings.CLIENT_URL}/reset-password?token={self.token}"
        )

        return f"""
        <!DOCTYPE html>
        <html>
        <body style="font-family: Arial, sans-serif; background:#f4f4f4; padding:40px;">
            <div style="
                max-width:600px;
                margin:auto;
                background:white;
                padding:40px;
                border-radius:12px;
                box-shadow:0 2px 10px rgba(0,0,0,0.1);
            ">
                <h2 style="color:#222;">
                    Password Reset Request
                </h2>

                <p>
                    We received a request to reset your password.
                </p>

                <p>
                    Click the button below to create a new password.
                </p>

                <div style="margin:30px 0;">
                    <a
                        href="{reset_link}"
                        style="
                            background:#dc2626;
                            color:white;
                            text-decoration:none;
                            padding:12px 24px;
                            border-radius:8px;
                            display:inline-block;
                        "
                    >
                        Reset Password
                    </a>
                </div>

                <p style="color:#666;">
                    If you didn't request a password reset, you can safely ignore this email.
                </p>

                <hr>

                <p style="font-size:12px;color:#888;">
                    For security reasons, this link will expire shortly.
                </p>
            </div>
        </body>
        </html>
        """

class SMTPEmailSender:

    def send(self, recipient: str, email_template: EmailTemplate):

        msg = EmailMessage()
        msg["Subject"] = email_template.subject()
        msg["From"] = settings.SMTP_USERNAME
        msg["To"] = recipient

        msg.set_content("Please use an HTML-compatible email client.")
        msg.add_alternative(
            email_template.body(),
            subtype="html"
        )

        with smtplib.SMTP_SSL(
            "smtp.gmail.com",
            465
        ) as smtp:
            smtp.login(
                settings.SMTP_USERNAME,
                settings.SMTP_PASSWORD
            )

            smtp.send_message(msg)