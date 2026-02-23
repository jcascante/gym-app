"""
Email service for sending transactional emails.

Supports both SMTP and mock (development) email sending modes.
For production, configure SMTP settings in environment variables.
"""
import logging
from typing import Optional, List
from pathlib import Path
from app.core.config import settings

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending transactional emails."""

    @staticmethod
    async def send_welcome_email(
        recipient_email: str,
        recipient_name: str,
        temporary_password: Optional[str] = None,
        login_url: str = "https://app.example.com/login",
    ) -> bool:
        """
        Send welcome email to new client.

        Args:
            recipient_email: Email address to send to
            recipient_name: Recipient's name
            temporary_password: Temporary password (if provided)
            login_url: URL to login page

        Returns:
            True if email sent successfully, False otherwise
        """
        subject = "Welcome to Gym App!"
        body = f"""
        <html>
            <body>
                <h2>Welcome to Gym App, {recipient_name}!</h2>
                <p>Your account has been created and you're ready to start your fitness journey.</p>
                
                <p><strong>Login Details:</strong></p>
                <ul>
                    <li>Email: {recipient_email}</li>
                    {f'<li>Temporary Password: {temporary_password}</li>' if temporary_password else ''}
                </ul>
                
                <p><a href="{login_url}">Login to your account</a></p>
                
                <p>If you have any questions, please contact support.</p>
                
                <p>Best regards,<br>The Gym App Team</p>
            </body>
        </html>
        """

        return await EmailService._send_email(
            to_email=recipient_email,
            subject=subject,
            body=body,
            is_html=True,
        )

    @staticmethod
    async def send_password_reset_email(
        recipient_email: str,
        recipient_name: str,
        reset_token: str,
        reset_url: Optional[str] = None,
    ) -> bool:
        """
        Send password reset email.

        Args:
            recipient_email: Email address to send to
            recipient_name: Recipient's name
            reset_token: Reset token for the link
            reset_url: Base URL for reset link (defaults to app URL)

        Returns:
            True if email sent successfully, False otherwise
        """
        if reset_url is None:
            reset_url = f"{settings.FRONTEND_URL}/reset-password"

        reset_link = f"{reset_url}?token={reset_token}"

        subject = "Reset Your Password"
        body = f"""
        <html>
            <body>
                <h2>Password Reset Request</h2>
                <p>Hi {recipient_name},</p>
                
                <p>We received a request to reset your password. Click the link below to create a new password:</p>
                
                <p><a href="{reset_link}">Reset Your Password</a></p>
                
                <p><strong>Note:</strong> This link will expire in 1 hour.</p>
                
                <p>If you didn't request this, you can safely ignore this email.</p>
                
                <p>Best regards,<br>The Gym App Team</p>
            </body>
        </html>
        """

        return await EmailService._send_email(
            to_email=recipient_email,
            subject=subject,
            body=body,
            is_html=True,
        )

    @staticmethod
    async def send_program_assigned_notification(
        recipient_email: str,
        recipient_name: str,
        program_name: str,
        coach_name: str,
        start_date: str,
    ) -> bool:
        """
        Send notification that a program has been assigned.

        Args:
            recipient_email: Client's email
            recipient_name: Client's name
            program_name: Name of the assigned program
            coach_name: Coach's name
            start_date: Program start date

        Returns:
            True if email sent successfully, False otherwise
        """
        subject = f"New Program Assigned: {program_name}"
        body = f"""
        <html>
            <body>
                <h2>New Program Assigned</h2>
                <p>Hi {recipient_name},</p>
                
                <p><strong>{coach_name}</strong> has assigned you a new program:</p>
                
                <p><strong>{program_name}</strong></p>
                
                <p><strong>Start Date:</strong> {start_date}</p>
                
                <p>Log in to your account to view the program details and start tracking your workouts!</p>
                
                <p>Best regards,<br>The Gym App Team</p>
            </body>
        </html>
        """

        return await EmailService._send_email(
            to_email=recipient_email,
            subject=subject,
            body=body,
            is_html=True,
        )

    @staticmethod
    async def send_notification(
        recipient_email: str,
        subject: str,
        body: str,
        is_html: bool = True,
    ) -> bool:
        """
        Send a generic notification email.

        Args:
            recipient_email: Email address to send to
            subject: Email subject
            body: Email body (can be HTML or plain text)
            is_html: Whether body is HTML (True) or plain text (False)

        Returns:
            True if email sent successfully, False otherwise
        """
        return await EmailService._send_email(
            to_email=recipient_email,
            subject=subject,
            body=body,
            is_html=is_html,
        )

    @staticmethod
    async def _send_email(
        to_email: str,
        subject: str,
        body: str,
        is_html: bool = True,
        cc: Optional[List[str]] = None,
    ) -> bool:
        """
        Internal method to send email via configured transport.

        Routes to SMTP or mock based on settings.

        Args:
            to_email: Recipient email address
            subject: Email subject
            body: Email body
            is_html: Whether body is HTML
            cc: List of CC email addresses

        Returns:
            True if sent successfully, False otherwise
        """
        if settings.EMAIL_USE_MOCK:
            return await EmailService._send_email_mock(
                to_email=to_email,
                subject=subject,
                body=body,
                is_html=is_html,
            )
        else:
            return await EmailService._send_email_smtp(
                to_email=to_email,
                subject=subject,
                body=body,
                is_html=is_html,
                cc=cc,
            )

    @staticmethod
    async def _send_email_smtp(
        to_email: str,
        subject: str,
        body: str,
        is_html: bool = True,
        cc: Optional[List[str]] = None,
    ) -> bool:
        """
        Send email via SMTP.

        Args:
            to_email: Recipient email
            subject: Subject
            body: Email body
            is_html: Whether HTML or plain text
            cc: CC recipients

        Returns:
            True if successful, False otherwise
        """
        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart

            # Create message
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = settings.EMAIL_FROM
            msg["To"] = to_email

            if cc:
                msg["Cc"] = ", ".join(cc)

            # Attach body
            msg.attach(MIMEText(body, "html" if is_html else "plain"))

            # Send email
            with smtplib.SMTP(settings.EMAIL_SMTP_HOST, settings.EMAIL_SMTP_PORT) as server:
                if settings.EMAIL_SMTP_TLS:
                    server.starttls()
                if settings.EMAIL_SMTP_USER and settings.EMAIL_SMTP_PASSWORD:
                    server.login(settings.EMAIL_SMTP_USER, settings.EMAIL_SMTP_PASSWORD)

                server.send_message(msg)

            logger.info(f"Email sent successfully to {to_email}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {str(e)}")
            return False

    @staticmethod
    async def _send_email_mock(
        to_email: str,
        subject: str,
        body: str,
        is_html: bool = True,
    ) -> bool:
        """
        Mock email sending for development/testing.

        Logs email details instead of sending.

        Args:
            to_email: Recipient email
            subject: Subject
            body: Email body
            is_html: Whether HTML or plain text

        Returns:
            True (always succeeds in mock mode)
        """
        log_message = f"""
        ============ MOCK EMAIL ============
        To: {to_email}
        Subject: {subject}
        Content-Type: {"text/html" if is_html else "text/plain"}
        ====================================
        {body[:500]}...
        ====================================
        """
        logger.info(log_message)
        return True
