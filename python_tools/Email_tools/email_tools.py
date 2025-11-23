# email_tools.py
"""
Email Tools for WatsonX Orchestrate Agent
Supports Gmail, Outlook, and generic SMTP email operations
"""

import os
import smtplib
import imaplib
import email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime, timedelta
from dotenv import load_dotenv
from ibm_watsonx_orchestrate.agent_builder.tools import tool
import json


# Load environment variables
load_dotenv()


# Email configuration helper class
class EmailConfig:
    def __init__(self, provider="gmail"):
        self.provider = provider.lower()
        self.email_address = os.getenv('EMAIL_ADDRESS')
        self.email_password = os.getenv('EMAIL_PASSWORD')  # App password for Gmail
        
        # SMTP and IMAP configurations
        self.smtp_configs = {
            "gmail": {"server": "smtp.gmail.com", "port": 587},
            "outlook": {"server": "smtp-mail.outlook.com", "port": 587},
            "yahoo": {"server": "smtp.mail.yahoo.com", "port": 587},
            "custom": {"server": os.getenv('SMTP_SERVER'), "port": int(os.getenv('SMTP_PORT', 587))}
        }
        
        self.imap_configs = {
            "gmail": {"server": "imap.gmail.com", "port": 993},
            "outlook": {"server": "outlook.office365.com", "port": 993},
            "yahoo": {"server": "imap.mail.yahoo.com", "port": 993},
            "custom": {"server": os.getenv('IMAP_SERVER'), "port": int(os.getenv('IMAP_PORT', 993))}
        }
    
    def get_smtp_config(self):
        return self.smtp_configs.get(self.provider, self.smtp_configs["gmail"])
    
    def get_imap_config(self):
        return self.imap_configs.get(self.provider, self.imap_configs["gmail"])
    
    def validate_credentials(self):
        return bool(self.email_address and self.email_password)


# Helper function to send emails
def _send_email_helper(to_email, subject, body, cc_email=None, bcc_email=None, 
                      is_html=False, provider="gmail"):
    """
    Helper function to send emails using SMTP
    """
    try:
        config = EmailConfig(provider)
        
        if not config.validate_credentials():
            return {
                "success": False,
                "message": "Email credentials not configured. Check EMAIL_ADDRESS and EMAIL_PASSWORD environment variables."
            }
        
        # Create message
        msg = MIMEMultipart()
        msg['From'] = config.email_address
        msg['To'] = to_email
        msg['Subject'] = subject
        
        if cc_email:
            msg['Cc'] = cc_email
        
        # Attach body
        if is_html:
            msg.attach(MIMEText(body, 'html'))
        else:
            msg.attach(MIMEText(body, 'plain'))
        
        # Setup SMTP server
        smtp_config = config.get_smtp_config()
        server = smtplib.SMTP(smtp_config["server"], smtp_config["port"])
        server.starttls()  # Enable TLS encryption
        server.login(config.email_address, config.email_password)
        
        # Prepare recipient list
        recipients = [to_email]
        if cc_email:
            recipients.extend(cc_email.split(','))
        if bcc_email:
            recipients.extend(bcc_email.split(','))
        
        # Send email
        text = msg.as_string()
        server.sendmail(config.email_address, recipients, text)
        server.quit()
        
        return {
            "success": True,
            "message": f"Email sent successfully to {to_email}",
            "timestamp": datetime.now().isoformat()
        }
        
    except smtplib.SMTPAuthenticationError:
        return {
            "success": False,
            "message": "Authentication failed. Check your email credentials or use app-specific password."
        }
    except smtplib.SMTPException as e:
        return {
            "success": False,
            "message": f"SMTP error: {str(e)}"
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Unexpected error: {str(e)}"
        }


# Helper function to read emails
def _read_emails_helper(folder="INBOX", limit=5, unread_only=False, provider="gmail"):
    """
    Helper function to read emails using IMAP
    """
    try:
        config = EmailConfig(provider)
        
        if not config.validate_credentials():
            return {
                "success": False,
                "message": "Email credentials not configured.",
                "emails": []
            }
        
        # Connect to IMAP server
        imap_config = config.get_imap_config()
        mail = imaplib.IMAP4_SSL(imap_config["server"], imap_config["port"])
        mail.login(config.email_address, config.email_password)
        
        # Select folder
        mail.select(folder)
        
        # Search criteria
        search_criteria = "UNSEEN" if unread_only else "ALL"
        result, message_ids = mail.search(None, search_criteria)
        
        if result != 'OK':
            return {
                "success": False,
                "message": "Failed to search emails",
                "emails": []
            }
        
        email_ids = message_ids[0].split()
        email_ids = email_ids[-limit:]  # Get latest emails
        
        emails = []
        
        for email_id in reversed(email_ids):  # Reverse to get newest first
            result, message_data = mail.fetch(email_id, '(RFC822)')
            
            if result == 'OK':
                email_message = email.message_from_bytes(message_data[0][1])
                
                # Extract email details
                email_info = {
                    "id": email_id.decode(),
                    "subject": email_message["Subject"] or "No Subject",
                    "from": email_message["From"] or "Unknown Sender",
                    "date": email_message["Date"] or "Unknown Date",
                    "to": email_message["To"] or config.email_address
                }
                
                # Extract body
                body = ""
                if email_message.is_multipart():
                    for part in email_message.walk():
                        if part.get_content_type() == "text/plain":
                            body = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                            break
                else:
                    body = email_message.get_payload(decode=True).decode('utf-8', errors='ignore')
                
                email_info["body_preview"] = body[:200] + "..." if len(body) > 200 else body
                emails.append(email_info)
        
        mail.logout()
        
        return {
            "success": True,
            "message": f"Retrieved {len(emails)} emails from {folder}",
            "count": len(emails),
            "emails": emails
        }
        
    except imaplib.IMAP4.error as e:
        return {
            "success": False,
            "message": f"IMAP error: {str(e)}",
            "emails": []
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Unexpected error: {str(e)}",
            "emails": []
        }


# Helper function to test email connection
def _test_email_connection_helper(provider="gmail"):
    """
    Helper function to test email connection
    """
    try:
        config = EmailConfig(provider)
        
        if not config.validate_credentials():
            return {
                "success": False,
                "message": "Email credentials not configured",
                "provider": provider
            }
        
        # Test SMTP connection
        smtp_config = config.get_smtp_config()
        smtp_server = smtplib.SMTP(smtp_config["server"], smtp_config["port"])
        smtp_server.starttls()
        smtp_server.login(config.email_address, config.email_password)
        smtp_server.quit()
        
        # Test IMAP connection
        imap_config = config.get_imap_config()
        imap_server = imaplib.IMAP4_SSL(imap_config["server"], imap_config["port"])
        imap_server.login(config.email_address, config.email_password)
        imap_server.logout()
        
        return {
            "success": True,
            "message": "Email connection successful",
            "provider": provider,
            "email": config.email_address,
            "smtp_server": f"{smtp_config['server']}:{smtp_config['port']}",
            "imap_server": f"{imap_config['server']}:{imap_config['port']}"
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": f"Connection failed: {str(e)}",
            "provider": provider
        }


# WatsonX Orchestrate Tools
@tool()
def send_email(to_email: str, subject: str, body: str, cc_email: str = None) -> str:
    """Send an email to specified recipient.

    Args:
        to_email (str): Recipient's email address
        subject (str): Email subject line
        body (str): Email body content
        cc_email (str): Optional CC recipients (comma-separated)

    Returns:
        str: Result of the email sending operation
    """
    
    try:
        result = _send_email_helper(
            to_email=to_email,
            subject=subject,
            body=body,
            cc_email=cc_email
        )
        
        if result["success"]:
            return f"✅ Email sent successfully to {to_email}\n📧 Subject: {subject}\n⏰ Sent at: {result['timestamp']}"
        else:
            return f"❌ Failed to send email: {result['message']}"
            
    except Exception as e:
        return f"❌ Error sending email: {str(e)}"


@tool()
def read_recent_emails(limit: int = 5, unread_only: str = "false") -> str:
    """Read recent emails from inbox.

    Args:
        limit (int): Number of emails to retrieve (default: 5, max: 20)
        unread_only (str): Get only unread emails ("true" or "false", default: "false")

    Returns:
        str: List of recent emails with details
    """
    
    try:
        # Convert string to boolean and limit the count
        unread_filter = unread_only.lower() == "true"
        email_limit = min(max(1, limit), 20)  # Between 1 and 20
        
        result = _read_emails_helper(
            limit=email_limit,
            unread_only=unread_filter
        )
        
        if result["success"]:
            if result["count"] > 0:
                email_list = []
                for i, email_info in enumerate(result["emails"], 1):
                    email_summary = (
                        f"{i}. 📧 From: {email_info['from']}\n"
                        f"   📝 Subject: {email_info['subject']}\n"
                        f"   📅 Date: {email_info['date']}\n"
                        f"   💬 Preview: {email_info['body_preview']}\n"
                    )
                    email_list.append(email_summary)
                
                filter_text = " (unread only)" if unread_filter else ""
                return f"📬 Recent Emails{filter_text}:\n\n" + "\n".join(email_list)
            else:
                filter_text = "unread " if unread_filter else ""
                return f"📭 No {filter_text}emails found in inbox"
        else:
            return f"❌ Failed to read emails: {result['message']}"
            
    except Exception as e:
        return f"❌ Error reading emails: {str(e)}"


@tool()
def test_email_connection() -> str:
    """Test email connection and show configuration details.

    Returns:
        str: Email connection test results
    """
    
    try:
        result = _test_email_connection_helper()
        
        if result["success"]:
            return (f"✅ Email Connection Successful!\n"
                   f"📧 Email: {result['email']}\n"
                   f"🌐 Provider: {result['provider']}\n"
                   f"📤 SMTP: {result['smtp_server']}\n"
                   f"📥 IMAP: {result['imap_server']}")
        else:
            return f"❌ Email Connection Failed: {result['message']}"
            
    except Exception as e:
        return f"❌ Connection test error: {str(e)}"


@tool()
def send_quick_notification(recipient: str, message: str) -> str:
    """Send a quick notification email with timestamp.

    Args:
        recipient (str): Email address to send notification to
        message (str): Notification message content

    Returns:
        str: Result of sending the notification
    """
    
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        subject = f"Notification - {timestamp}"
        
        body = f"""
🔔 Notification from WatsonX Agent

📅 Time: {timestamp}
💬 Message: {message}

---
This is an automated notification sent by WatsonX Orchestrate Agent.
        """
        
        result = _send_email_helper(
            to_email=recipient,
            subject=subject,
            body=body.strip()
        )
        
        if result["success"]:
            return f"🔔 Notification sent successfully to {recipient}\n💬 Message: {message}"
        else:
            return f"❌ Failed to send notification: {result['message']}"
            
    except Exception as e:
        return f"❌ Error sending notification: {str(e)}"