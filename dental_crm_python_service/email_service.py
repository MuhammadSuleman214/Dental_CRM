import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from config import config

class EmailService:
    def __init__(self):
        # Email configuration - you can update these in your .env file
        self.sender_email = getattr(config, 'EMAIL_SENDER', None) or "your-email@gmail.com"
        self.sender_password = getattr(config, 'EMAIL_PASSWORD', None) or "your-app-password"
        self.clinic_name = "Dental Care Clinic"
        
        # Auto-detect SMTP settings based on email provider
        self.smtp_server, self.smtp_port = self._get_smtp_settings(self.sender_email)
    
    def _get_smtp_settings(self, email):
        """Auto-detect SMTP settings based on email provider"""
        email_domain = email.lower().split('@')[-1] if '@' in email else ''
        
        smtp_settings = {
            'gmail.com': ('smtp.gmail.com', 587),
            'googlemail.com': ('smtp.gmail.com', 587),
            'yahoo.com': ('smtp.mail.yahoo.com', 587),
            'yahoo.co.uk': ('smtp.mail.yahoo.co.uk', 587),
            'outlook.com': ('smtp-mail.outlook.com', 587),
            'hotmail.com': ('smtp-mail.outlook.com', 587),
            'live.com': ('smtp-mail.outlook.com', 587),
            'zoho.com': ('smtp.zoho.com', 587),
            'protonmail.com': ('smtp.protonmail.com', 587),
            'icloud.com': ('smtp.mail.me.com', 587),
            'me.com': ('smtp.mail.me.com', 587),
            'mac.com': ('smtp.mail.me.com', 587),
        }
        
        # Check for exact match first
        if email_domain in smtp_settings:
            server, port = smtp_settings[email_domain]
            print(f"📧 Auto-detected SMTP: {server}:{port} for {email_domain}")
            return server, port
        
        # Check for partial matches (for custom domains)
        for domain, settings in smtp_settings.items():
            if domain in email_domain:
                server, port = settings
                print(f"📧 Auto-detected SMTP: {server}:{port} for {email_domain}")
                return server, port
        
        # Default to Gmail if no match found
        print(f"📧 No SMTP settings found for {email_domain}, using Gmail as default")
        return 'smtp.gmail.com', 587
        
    def send_appointment_confirmation(self, user_email, user_name, appointment_date, appointment_time, appointment_type="General Checkup"):
        """Send appointment confirmation email"""
        print(f"📧 Attempting to send email to {user_email}")
        print(f"📧 Sender: {self.sender_email}")
        print(f"📧 SMTP: {self.smtp_server}:{self.smtp_port}")
        
        # Check if email is configured
        if self.sender_email == "your-email@gmail.com" or self.sender_password == "your-app-password":
            print(f"⚠️ EMAIL NOT CONFIGURED!")
            print(f"⚠️ Please create a .env file in dental_crm_python_service/ with:")
            print(f"⚠️ EMAIL_SENDER=your-email@gmail.com")
            print(f"⚠️ EMAIL_PASSWORD=your-gmail-app-password")
            print(f"⚠️ See EMAIL_SETUP.md for detailed instructions")
            return False
            
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.sender_email
            msg['To'] = user_email
            msg['Subject'] = f"Appointment Confirmation - {self.clinic_name}"
            
            # Email body
            body = f"""
Dear {user_name},

Thank you for scheduling your appointment with {self.clinic_name}!

📅 Appointment Details:
• Date: {appointment_date}
• Time: {appointment_time}
• Service: {appointment_type}

📍 Location:
{self.clinic_name}
123 Main Street, City, State 12345

📞 Contact: (555) 123-4567

Please arrive 15 minutes early for your appointment. If you need to reschedule or cancel, please contact us at least 24 hours in advance.

We look forward to seeing you!

Best regards,
{self.clinic_name} Team

---
This is an automated message. Please do not reply to this email.
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Create SMTP session
            context = ssl.create_default_context()
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls(context=context)
                server.login(self.sender_email, self.sender_password)
                text = msg.as_string()
                server.sendmail(self.sender_email, user_email, text)
                
            print(f"✅ Confirmation email sent to {user_email}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to send email to {user_email}: {e}")
            return False
    
    def send_reschedule_confirmation(self, user_email, user_name, old_date, old_time, new_date, new_time, appointment_type="General Checkup"):
        """Send reschedule confirmation email"""
        try:
            msg = MIMEMultipart()
            msg['From'] = self.sender_email
            msg['To'] = user_email
            msg['Subject'] = f"Appointment Rescheduled - {self.clinic_name}"
            
            body = f"""
Dear {user_name},

Your appointment with {self.clinic_name} has been successfully rescheduled!

🔄 Reschedule Details:
• Previous: {old_date} at {old_time}
• New: {new_date} at {new_time}
• Service: {appointment_type}

📍 Location:
{self.clinic_name}
123 Main Street, City, State 12345

📞 Contact: (555) 123-4567

Please arrive 15 minutes early for your appointment. If you need any further changes, please contact us at least 24 hours in advance.

Thank you for your patience!

Best regards,
{self.clinic_name} Team

---
This is an automated message. Please do not reply to this email.
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            context = ssl.create_default_context()
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls(context=context)
                server.login(self.sender_email, self.sender_password)
                text = msg.as_string()
                server.sendmail(self.sender_email, user_email, text)
                
            print(f"✅ Reschedule confirmation email sent to {user_email}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to send reschedule email to {user_email}: {e}")
            return False
    
    def send_password_reset_email(self, user_email, user_name, reset_token):
        """Send password reset email"""
        print(f"📧 Attempting to send password reset email to {user_email}")
        print(f"📧 Sender: {self.sender_email}")
        print(f"📧 SMTP: {self.smtp_server}:{self.smtp_port}")
        
        # Check if email is configured
        if self.sender_email == "your-email@gmail.com" or self.sender_password == "your-app-password":
            print(f"⚠️ EMAIL NOT CONFIGURED!")
            print(f"⚠️ Please create a .env file in dental_crm_python_service/ with:")
            print(f"⚠️ EMAIL_SENDER=your-email@gmail.com")
            print(f"⚠️ EMAIL_PASSWORD=your-gmail-app-password")
            print(f"⚠️ See EMAIL_SETUP.md for detailed instructions")
            return False
            
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.sender_email
            msg['To'] = user_email
            msg['Subject'] = f"Password Reset Request - {self.clinic_name}"
            
            # Create reset link (you'll need to update this with your frontend URL)
            reset_link = f"http://localhost:3000/reset-password?token={reset_token}"
            
            # Email body
            body = f"""
Dear {user_name},

We received a request to reset your password for your {self.clinic_name} account.

🔐 To reset your password, please click the link below:
{reset_link}

⚠️ Important Security Information:
• This link will expire in 1 hour for security reasons
• If you didn't request this password reset, please ignore this email
• Your password will remain unchanged until you create a new one

📞 Need Help?
If you're having trouble with the link above, please contact us:
• Phone: (555) 123-4567
• Email: support@{self.clinic_name.lower().replace(' ', '')}.com

Best regards,
{self.clinic_name} Team

---
This is an automated message. Please do not reply to this email.
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Create SMTP session
            context = ssl.create_default_context()
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls(context=context)
                server.login(self.sender_email, self.sender_password)
                text = msg.as_string()
                server.sendmail(self.sender_email, user_email, text)
                
            print(f"✅ Password reset email sent to {user_email}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to send password reset email to {user_email}: {e}")
            return False

    def send_test_email(self, user_email):
        """Send test email to verify email configuration"""
        try:
            msg = MIMEMultipart()
            msg['From'] = self.sender_email
            msg['To'] = user_email
            msg['Subject'] = f"Test Email - {self.clinic_name}"
            
            body = f"""
Hello!

This is a test email from {self.clinic_name} chatbot service.

If you receive this email, the email configuration is working correctly!

Best regards,
{self.clinic_name} Team
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            context = ssl.create_default_context()
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls(context=context)
                server.login(self.sender_email, self.sender_password)
                text = msg.as_string()
                server.sendmail(self.sender_email, user_email, text)
                
            print(f"✅ Test email sent to {user_email}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to send test email to {user_email}: {e}")
            return False

# Singleton instance
email_service = EmailService()
