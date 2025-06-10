#!/usr/bin/env python3
"""
Notification Sending Script for n8n Integration

This script provides a unified interface for sending notifications through various channels
and can be executed directly from n8n workflows using the Execute Command node.

Usage:
  python3 send_notification.py --input '{"type": "email", "to": "user@example.com", "subject": "Test", "message": "Hello World"}'
  python3 send_notification.py --input-file notification.json --type slack
"""

import argparse
import json
import sys
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import time
from datetime import datetime, timezone
import base64
import mimetypes

# Add shared libs to path
sys.path.append(str(Path(__file__).parent.parent.parent / 'libs'))
from common import (
    handle_errors, setup_logging, validate_input, safe_json_loads,
    create_success_response, create_error_response, measure_execution_time,
    safe_read_file, safe_write_file
)
from config import get_config

# Setup logging
logger = setup_logging()
config = get_config()


@measure_execution_time
@handle_errors
def send_notification(
    notification_type: str,
    message: str,
    recipients: Union[str, List[str]],
    subject: Optional[str] = None,
    attachments: Optional[List[Dict[str, Any]]] = None,
    options: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Send notifications through various channels."""
    
    logger.info(f"Sending {notification_type} notification")
    
    if notification_type == "email":
        return send_email(recipients, subject, message, attachments, options)
    elif notification_type == "slack":
        return send_slack_message(recipients, message, attachments, options)
    elif notification_type == "discord":
        return send_discord_message(recipients, message, attachments, options)
    elif notification_type == "teams":
        return send_teams_message(recipients, subject, message, attachments, options)
    elif notification_type == "telegram":
        return send_telegram_message(recipients, message, attachments, options)
    elif notification_type == "sms":
        return send_sms(recipients, message, options)
    elif notification_type == "push":
        return send_push_notification(recipients, subject, message, options)
    elif notification_type == "webhook":
        return send_webhook_notification(recipients, message, options)
    elif notification_type == "desktop":
        return send_desktop_notification(subject, message, options)
    else:
        return create_error_response(
            f"Unknown notification type: {notification_type}",
            "ValueError",
            {"available_types": [
                "email", "slack", "discord", "teams", "telegram", 
                "sms", "push", "webhook", "desktop"
            ]}
        )


def send_email(
    recipients: Union[str, List[str]], subject: Optional[str], message: str,
    attachments: Optional[List[Dict[str, Any]]], options: Optional[Dict[str, Any]]
) -> Dict[str, Any]:
    """Send email notification."""
    
    try:
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        from email.mime.base import MIMEBase
        from email import encoders
        
        # Get email configuration
        email_config = options.get('email_config', {}) if options else {}
        smtp_server = email_config.get('smtp_server', os.getenv('SMTP_SERVER', 'localhost'))
        smtp_port = email_config.get('smtp_port', int(os.getenv('SMTP_PORT', '587')))
        smtp_username = email_config.get('username', os.getenv('SMTP_USERNAME'))
        smtp_password = email_config.get('password', os.getenv('SMTP_PASSWORD'))
        from_email = email_config.get('from_email', os.getenv('FROM_EMAIL', smtp_username))
        use_tls = email_config.get('use_tls', os.getenv('SMTP_USE_TLS', 'true').lower() == 'true')
        
        if not smtp_username or not smtp_password:
            return create_error_response(
                "SMTP credentials not configured",
                "ConfigurationError",
                {"required_env_vars": ["SMTP_USERNAME", "SMTP_PASSWORD"]}
            )
        
        # Prepare recipients
        if isinstance(recipients, str):
            recipients = [recipients]
        
        # Create message
        msg = MIMEMultipart()
        msg['From'] = from_email
        msg['To'] = ', '.join(recipients)
        msg['Subject'] = subject or "Notification from n8n"
        
        # Add message body
        is_html = options.get('is_html', False) if options else False
        body_type = 'html' if is_html else 'plain'
        msg.attach(MIMEText(message, body_type, 'utf-8'))
        
        # Add attachments
        if attachments:
            for attachment in attachments:
                file_path = attachment.get('file_path')
                filename = attachment.get('filename') or os.path.basename(file_path)
                
                if file_path and os.path.exists(file_path):
                    with open(file_path, 'rb') as f:
                        part = MIMEBase('application', 'octet-stream')
                        part.set_payload(f.read())
                        encoders.encode_base64(part)
                        part.add_header(
                            'Content-Disposition',
                            f'attachment; filename= {filename}'
                        )
                        msg.attach(part)
                elif attachment.get('content'):
                    # Inline attachment from content
                    content = attachment['content']
                    if attachment.get('encoding') == 'base64':
                        content = base64.b64decode(content)
                    
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(content)
                    encoders.encode_base64(part)
                    part.add_header(
                        'Content-Disposition',
                        f'attachment; filename= {filename}'
                    )
                    msg.attach(part)
        
        # Send email
        start_time = time.time()
        
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            if use_tls:
                server.starttls()
            server.login(smtp_username, smtp_password)
            server.send_message(msg)
        
        end_time = time.time()
        
        result = {
            "email": {
                "from": from_email,
                "to": recipients,
                "subject": subject,
                "message_length": len(message),
                "attachments_count": len(attachments) if attachments else 0,
                "smtp_server": smtp_server,
                "send_time_seconds": end_time - start_time,
                "timestamp": datetime.now(timezone.utc).isoformat()
            },
            "success": True
        }
        
        return create_success_response(result, {
            "notification_type": "email",
            "recipients_count": len(recipients),
            "sent": True
        })
    
    except ImportError:
        return create_error_response(
            "Email sending requires built-in email libraries",
            "ImportError",
            {"note": "Email libraries should be available in Python standard library"}
        )
    except Exception as e:
        logger.error(f"Error sending email: {e}")
        return create_error_response(
            f"Email sending failed: {str(e)}",
            type(e).__name__
        )


def send_slack_message(
    channels: Union[str, List[str]], message: str,
    attachments: Optional[List[Dict[str, Any]]], options: Optional[Dict[str, Any]]
) -> Dict[str, Any]:
    """Send Slack message."""
    
    try:
        import requests
        
        # Get Slack configuration
        slack_config = options.get('slack_config', {}) if options else {}
        webhook_url = slack_config.get('webhook_url', os.getenv('SLACK_WEBHOOK_URL'))
        bot_token = slack_config.get('bot_token', os.getenv('SLACK_BOT_TOKEN'))
        
        if not webhook_url and not bot_token:
            return create_error_response(
                "Slack webhook URL or bot token not configured",
                "ConfigurationError",
                {"required_env_vars": ["SLACK_WEBHOOK_URL or SLACK_BOT_TOKEN"]}
            )
        
        # Prepare channels
        if isinstance(channels, str):
            channels = [channels]
        
        results = []
        
        for channel in channels:
            if webhook_url:
                # Use webhook
                payload = {
                    "text": message,
                    "channel": channel if channel.startswith('#') or channel.startswith('@') else f"#{channel}",
                    "username": options.get('username', 'n8n-bot') if options else 'n8n-bot',
                    "icon_emoji": options.get('icon_emoji', ':robot_face:') if options else ':robot_face:'
                }
                
                # Add attachments in Slack format
                if attachments:
                    slack_attachments = []
                    for attachment in attachments:
                        slack_attachment = {
                            "fallback": attachment.get('fallback', 'Attachment'),
                            "color": attachment.get('color', 'good'),
                            "title": attachment.get('title'),
                            "text": attachment.get('text'),
                            "image_url": attachment.get('image_url')
                        }
                        slack_attachments.append(slack_attachment)
                    payload["attachments"] = slack_attachments
                
                response = requests.post(webhook_url, json=payload, timeout=30)
                
            else:
                # Use bot token
                headers = {
                    'Authorization': f'Bearer {bot_token}',
                    'Content-Type': 'application/json'
                }
                
                payload = {
                    "channel": channel,
                    "text": message,
                    "username": options.get('username', 'n8n-bot') if options else 'n8n-bot'
                }
                
                response = requests.post(
                    'https://slack.com/api/chat.postMessage',
                    headers=headers,
                    json=payload,
                    timeout=30
                )
            
            result = {
                "channel": channel,
                "status_code": response.status_code,
                "success": response.ok,
                "response": response.text
            }
            results.append(result)
        
        successful_sends = sum(1 for r in results if r['success'])
        
        summary = {
            "slack": {
                "channels": channels,
                "message_length": len(message),
                "successful_sends": successful_sends,
                "failed_sends": len(channels) - successful_sends,
                "results": results,
                "timestamp": datetime.now(timezone.utc).isoformat()
            },
            "success": successful_sends > 0
        }
        
        if successful_sends > 0:
            return create_success_response(summary, {
                "notification_type": "slack",
                "channels_count": len(channels),
                "successful_sends": successful_sends
            })
        else:
            return create_error_response(
                "All Slack messages failed to send",
                "SlackError",
                summary
            )
    
    except ImportError:
        return create_error_response(
            "Slack messaging requires requests library",
            "ImportError",
            {"required_packages": ["requests"]}
        )
    except Exception as e:
        logger.error(f"Error sending Slack message: {e}")
        return create_error_response(
            f"Slack messaging failed: {str(e)}",
            type(e).__name__
        )


def send_discord_message(
    channels: Union[str, List[str]], message: str,
    attachments: Optional[List[Dict[str, Any]]], options: Optional[Dict[str, Any]]
) -> Dict[str, Any]:
    """Send Discord message."""
    
    try:
        import requests
        
        # Get Discord configuration
        discord_config = options.get('discord_config', {}) if options else {}
        webhook_url = discord_config.get('webhook_url', os.getenv('DISCORD_WEBHOOK_URL'))
        
        if not webhook_url:
            return create_error_response(
                "Discord webhook URL not configured",
                "ConfigurationError",
                {"required_env_vars": ["DISCORD_WEBHOOK_URL"]}
            )
        
        # Prepare payload
        payload = {
            "content": message,
            "username": options.get('username', 'n8n-bot') if options else 'n8n-bot',
            "avatar_url": options.get('avatar_url') if options else None
        }
        
        # Add embeds (Discord's rich attachments)
        if attachments:
            embeds = []
            for attachment in attachments:
                embed = {
                    "title": attachment.get('title'),
                    "description": attachment.get('description'),
                    "color": int(attachment.get('color', '0x00ff00').replace('#', '').replace('0x', ''), 16),
                    "image": {"url": attachment.get('image_url')} if attachment.get('image_url') else None,
                    "thumbnail": {"url": attachment.get('thumbnail_url')} if attachment.get('thumbnail_url') else None
                }
                # Remove None values
                embed = {k: v for k, v in embed.items() if v is not None}
                embeds.append(embed)
            payload["embeds"] = embeds
        
        # Remove None values
        payload = {k: v for k, v in payload.items() if v is not None}
        
        start_time = time.time()
        
        response = requests.post(webhook_url, json=payload, timeout=30)
        
        end_time = time.time()
        
        result = {
            "discord": {
                "webhook_url": webhook_url.split('/')[-2] + '/***',  # Mask token
                "message_length": len(message),
                "embeds_count": len(attachments) if attachments else 0,
                "send_time_seconds": end_time - start_time,
                "status_code": response.status_code,
                "timestamp": datetime.now(timezone.utc).isoformat()
            },
            "success": response.ok
        }
        
        if response.ok:
            return create_success_response(result, {
                "notification_type": "discord",
                "sent": True
            })
        else:
            return create_error_response(
                f"Discord message failed: HTTP {response.status_code}",
                "DiscordError",
                result
            )
    
    except ImportError:
        return create_error_response(
            "Discord messaging requires requests library",
            "ImportError",
            {"required_packages": ["requests"]}
        )
    except Exception as e:
        logger.error(f"Error sending Discord message: {e}")
        return create_error_response(
            f"Discord messaging failed: {str(e)}",
            type(e).__name__
        )


def send_teams_message(
    channels: Union[str, List[str]], subject: Optional[str], message: str,
    attachments: Optional[List[Dict[str, Any]]], options: Optional[Dict[str, Any]]
) -> Dict[str, Any]:
    """Send Microsoft Teams message."""
    
    try:
        import requests
        
        # Get Teams configuration
        teams_config = options.get('teams_config', {}) if options else {}
        webhook_url = teams_config.get('webhook_url', os.getenv('TEAMS_WEBHOOK_URL'))
        
        if not webhook_url:
            return create_error_response(
                "Teams webhook URL not configured",
                "ConfigurationError",
                {"required_env_vars": ["TEAMS_WEBHOOK_URL"]}
            )
        
        # Prepare Teams message card
        payload = {
            "@type": "MessageCard",
            "@context": "http://schema.org/extensions",
            "themeColor": options.get('theme_color', '0076D7') if options else '0076D7',
            "summary": subject or "Notification from n8n",
            "sections": [
                {
                    "activityTitle": subject or "n8n Notification",
                    "activitySubtitle": datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC'),
                    "text": message,
                    "markdown": True
                }
            ]
        }
        
        # Add potential actions
        if options and options.get('actions'):
            payload["potentialAction"] = options['actions']
        
        start_time = time.time()
        
        response = requests.post(webhook_url, json=payload, timeout=30)
        
        end_time = time.time()
        
        result = {
            "teams": {
                "webhook_url": webhook_url.split('/')[-2] + '/***',  # Mask token
                "subject": subject,
                "message_length": len(message),
                "send_time_seconds": end_time - start_time,
                "status_code": response.status_code,
                "timestamp": datetime.now(timezone.utc).isoformat()
            },
            "success": response.ok
        }
        
        if response.ok:
            return create_success_response(result, {
                "notification_type": "teams",
                "sent": True
            })
        else:
            return create_error_response(
                f"Teams message failed: HTTP {response.status_code}",
                "TeamsError",
                result
            )
    
    except ImportError:
        return create_error_response(
            "Teams messaging requires requests library",
            "ImportError",
            {"required_packages": ["requests"]}
        )
    except Exception as e:
        logger.error(f"Error sending Teams message: {e}")
        return create_error_response(
            f"Teams messaging failed: {str(e)}",
            type(e).__name__
        )


def send_telegram_message(
    chat_ids: Union[str, List[str]], message: str,
    attachments: Optional[List[Dict[str, Any]]], options: Optional[Dict[str, Any]]
) -> Dict[str, Any]:
    """Send Telegram message."""
    
    try:
        import requests
        
        # Get Telegram configuration
        telegram_config = options.get('telegram_config', {}) if options else {}
        bot_token = telegram_config.get('bot_token', os.getenv('TELEGRAM_BOT_TOKEN'))
        
        if not bot_token:
            return create_error_response(
                "Telegram bot token not configured",
                "ConfigurationError",
                {"required_env_vars": ["TELEGRAM_BOT_TOKEN"]}
            )
        
        # Prepare chat IDs
        if isinstance(chat_ids, str):
            chat_ids = [chat_ids]
        
        base_url = f"https://api.telegram.org/bot{bot_token}"
        results = []
        
        for chat_id in chat_ids:
            # Send text message
            payload = {
                "chat_id": chat_id,
                "text": message,
                "parse_mode": options.get('parse_mode', 'Markdown') if options else 'Markdown',
                "disable_web_page_preview": options.get('disable_preview', False) if options else False
            }
            
            response = requests.post(
                f"{base_url}/sendMessage",
                json=payload,
                timeout=30
            )
            
            result = {
                "chat_id": chat_id,
                "status_code": response.status_code,
                "success": response.ok,
                "response": response.json() if response.ok else response.text
            }
            results.append(result)
            
            # Send attachments if any
            if attachments and response.ok:
                for attachment in attachments:
                    if attachment.get('type') == 'photo' and attachment.get('url'):
                        photo_payload = {
                            "chat_id": chat_id,
                            "photo": attachment['url'],
                            "caption": attachment.get('caption', '')
                        }
                        requests.post(f"{base_url}/sendPhoto", json=photo_payload, timeout=30)
                    
                    elif attachment.get('type') == 'document' and attachment.get('file_path'):
                        with open(attachment['file_path'], 'rb') as f:
                            files = {'document': f}
                            data = {
                                'chat_id': chat_id,
                                'caption': attachment.get('caption', '')
                            }
                            requests.post(f"{base_url}/sendDocument", files=files, data=data, timeout=30)
        
        successful_sends = sum(1 for r in results if r['success'])
        
        summary = {
            "telegram": {
                "chat_ids": chat_ids,
                "message_length": len(message),
                "successful_sends": successful_sends,
                "failed_sends": len(chat_ids) - successful_sends,
                "results": results,
                "timestamp": datetime.now(timezone.utc).isoformat()
            },
            "success": successful_sends > 0
        }
        
        if successful_sends > 0:
            return create_success_response(summary, {
                "notification_type": "telegram",
                "chats_count": len(chat_ids),
                "successful_sends": successful_sends
            })
        else:
            return create_error_response(
                "All Telegram messages failed to send",
                "TelegramError",
                summary
            )
    
    except ImportError:
        return create_error_response(
            "Telegram messaging requires requests library",
            "ImportError",
            {"required_packages": ["requests"]}
        )
    except Exception as e:
        logger.error(f"Error sending Telegram message: {e}")
        return create_error_response(
            f"Telegram messaging failed: {str(e)}",
            type(e).__name__
        )


def send_sms(
    phone_numbers: Union[str, List[str]], message: str, options: Optional[Dict[str, Any]]
) -> Dict[str, Any]:
    """Send SMS notification."""
    
    try:
        import requests
        
        # Get SMS configuration
        sms_config = options.get('sms_config', {}) if options else {}
        provider = sms_config.get('provider', os.getenv('SMS_PROVIDER', 'twilio'))
        
        if provider == 'twilio':
            return send_twilio_sms(phone_numbers, message, sms_config)
        elif provider == 'nexmo':
            return send_nexmo_sms(phone_numbers, message, sms_config)
        else:
            return create_error_response(
                f"Unsupported SMS provider: {provider}",
                "ValueError",
                {"supported_providers": ["twilio", "nexmo"]}
            )
    
    except Exception as e:
        logger.error(f"Error sending SMS: {e}")
        return create_error_response(
            f"SMS sending failed: {str(e)}",
            type(e).__name__
        )


def send_twilio_sms(
    phone_numbers: Union[str, List[str]], message: str, sms_config: Dict[str, Any]
) -> Dict[str, Any]:
    """Send SMS via Twilio."""
    
    try:
        from twilio.rest import Client
        
        account_sid = sms_config.get('account_sid', os.getenv('TWILIO_ACCOUNT_SID'))
        auth_token = sms_config.get('auth_token', os.getenv('TWILIO_AUTH_TOKEN'))
        from_number = sms_config.get('from_number', os.getenv('TWILIO_FROM_NUMBER'))
        
        if not all([account_sid, auth_token, from_number]):
            return create_error_response(
                "Twilio credentials not configured",
                "ConfigurationError",
                {"required_env_vars": ["TWILIO_ACCOUNT_SID", "TWILIO_AUTH_TOKEN", "TWILIO_FROM_NUMBER"]}
            )
        
        client = Client(account_sid, auth_token)
        
        if isinstance(phone_numbers, str):
            phone_numbers = [phone_numbers]
        
        results = []
        for phone_number in phone_numbers:
            try:
                message_obj = client.messages.create(
                    body=message,
                    from_=from_number,
                    to=phone_number
                )
                
                result = {
                    "phone_number": phone_number,
                    "message_sid": message_obj.sid,
                    "status": message_obj.status,
                    "success": True
                }
            except Exception as e:
                result = {
                    "phone_number": phone_number,
                    "error": str(e),
                    "success": False
                }
            
            results.append(result)
        
        successful_sends = sum(1 for r in results if r['success'])
        
        summary = {
            "sms": {
                "provider": "twilio",
                "phone_numbers": phone_numbers,
                "message_length": len(message),
                "successful_sends": successful_sends,
                "failed_sends": len(phone_numbers) - successful_sends,
                "results": results,
                "timestamp": datetime.now(timezone.utc).isoformat()
            },
            "success": successful_sends > 0
        }
        
        if successful_sends > 0:
            return create_success_response(summary, {
                "notification_type": "sms",
                "provider": "twilio",
                "successful_sends": successful_sends
            })
        else:
            return create_error_response(
                "All SMS messages failed to send",
                "SMSError",
                summary
            )
    
    except ImportError:
        return create_error_response(
            "Twilio SMS requires twilio library",
            "ImportError",
            {"required_packages": ["twilio"]}
        )


def send_nexmo_sms(
    phone_numbers: Union[str, List[str]], message: str, sms_config: Dict[str, Any]
) -> Dict[str, Any]:
    """Send SMS via Nexmo/Vonage."""
    
    try:
        import requests
        
        api_key = sms_config.get('api_key', os.getenv('NEXMO_API_KEY'))
        api_secret = sms_config.get('api_secret', os.getenv('NEXMO_API_SECRET'))
        from_number = sms_config.get('from_number', os.getenv('NEXMO_FROM_NUMBER'))
        
        if not all([api_key, api_secret, from_number]):
            return create_error_response(
                "Nexmo credentials not configured",
                "ConfigurationError",
                {"required_env_vars": ["NEXMO_API_KEY", "NEXMO_API_SECRET", "NEXMO_FROM_NUMBER"]}
            )
        
        if isinstance(phone_numbers, str):
            phone_numbers = [phone_numbers]
        
        results = []
        for phone_number in phone_numbers:
            payload = {
                "api_key": api_key,
                "api_secret": api_secret,
                "to": phone_number,
                "from": from_number,
                "text": message
            }
            
            response = requests.post(
                "https://rest.nexmo.com/sms/json",
                json=payload,
                timeout=30
            )
            
            if response.ok:
                response_data = response.json()
                message_data = response_data.get('messages', [{}])[0]
                
                result = {
                    "phone_number": phone_number,
                    "message_id": message_data.get('message-id'),
                    "status": message_data.get('status'),
                    "success": message_data.get('status') == '0'
                }
            else:
                result = {
                    "phone_number": phone_number,
                    "error": f"HTTP {response.status_code}",
                    "success": False
                }
            
            results.append(result)
        
        successful_sends = sum(1 for r in results if r['success'])
        
        summary = {
            "sms": {
                "provider": "nexmo",
                "phone_numbers": phone_numbers,
                "message_length": len(message),
                "successful_sends": successful_sends,
                "failed_sends": len(phone_numbers) - successful_sends,
                "results": results,
                "timestamp": datetime.now(timezone.utc).isoformat()
            },
            "success": successful_sends > 0
        }
        
        if successful_sends > 0:
            return create_success_response(summary, {
                "notification_type": "sms",
                "provider": "nexmo",
                "successful_sends": successful_sends
            })
        else:
            return create_error_response(
                "All SMS messages failed to send",
                "SMSError",
                summary
            )
    
    except ImportError:
        return create_error_response(
            "Nexmo SMS requires requests library",
            "ImportError",
            {"required_packages": ["requests"]}
        )


def send_push_notification(
    device_tokens: Union[str, List[str]], title: Optional[str], message: str,
    options: Optional[Dict[str, Any]]
) -> Dict[str, Any]:
    """Send push notification."""
    
    try:
        import requests
        
        # Get push notification configuration
        push_config = options.get('push_config', {}) if options else {}
        provider = push_config.get('provider', os.getenv('PUSH_PROVIDER', 'firebase'))
        
        if provider == 'firebase':
            return send_firebase_push(device_tokens, title, message, push_config)
        else:
            return create_error_response(
                f"Unsupported push provider: {provider}",
                "ValueError",
                {"supported_providers": ["firebase"]}
            )
    
    except Exception as e:
        logger.error(f"Error sending push notification: {e}")
        return create_error_response(
            f"Push notification failed: {str(e)}",
            type(e).__name__
        )


def send_firebase_push(
    device_tokens: Union[str, List[str]], title: Optional[str], message: str,
    push_config: Dict[str, Any]
) -> Dict[str, Any]:
    """Send push notification via Firebase."""
    
    try:
        import requests
        
        server_key = push_config.get('server_key', os.getenv('FIREBASE_SERVER_KEY'))
        
        if not server_key:
            return create_error_response(
                "Firebase server key not configured",
                "ConfigurationError",
                {"required_env_vars": ["FIREBASE_SERVER_KEY"]}
            )
        
        if isinstance(device_tokens, str):
            device_tokens = [device_tokens]
        
        headers = {
            'Authorization': f'key={server_key}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            "registration_ids": device_tokens,
            "notification": {
                "title": title or "Notification",
                "body": message,
                "icon": push_config.get('icon', 'default'),
                "sound": push_config.get('sound', 'default')
            },
            "data": push_config.get('data', {})
        }
        
        response = requests.post(
            "https://fcm.googleapis.com/fcm/send",
            headers=headers,
            json=payload,
            timeout=30
        )
        
        result = {
            "push": {
                "provider": "firebase",
                "device_tokens_count": len(device_tokens),
                "title": title,
                "message_length": len(message),
                "status_code": response.status_code,
                "response": response.json() if response.ok else response.text,
                "timestamp": datetime.now(timezone.utc).isoformat()
            },
            "success": response.ok
        }
        
        if response.ok:
            return create_success_response(result, {
                "notification_type": "push",
                "provider": "firebase",
                "sent": True
            })
        else:
            return create_error_response(
                f"Firebase push failed: HTTP {response.status_code}",
                "PushError",
                result
            )
    
    except ImportError:
        return create_error_response(
            "Firebase push requires requests library",
            "ImportError",
            {"required_packages": ["requests"]}
        )


def send_webhook_notification(
    webhook_urls: Union[str, List[str]], message: str, options: Optional[Dict[str, Any]]
) -> Dict[str, Any]:
    """Send webhook notification."""
    
    try:
        import requests
        
        if isinstance(webhook_urls, str):
            webhook_urls = [webhook_urls]
        
        results = []
        
        for webhook_url in webhook_urls:
            payload = {
                "message": message,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "source": "n8n-notification"
            }
            
            # Add custom data if provided
            if options and options.get('data'):
                payload.update(options['data'])
            
            headers = {
                'Content-Type': 'application/json',
                'User-Agent': 'n8n-notification-webhook/1.0'
            }
            
            # Add custom headers if provided
            if options and options.get('headers'):
                headers.update(options['headers'])
            
            response = requests.post(
                webhook_url,
                json=payload,
                headers=headers,
                timeout=30
            )
            
            result = {
                "webhook_url": webhook_url,
                "status_code": response.status_code,
                "success": response.ok,
                "response": response.text
            }
            results.append(result)
        
        successful_sends = sum(1 for r in results if r['success'])
        
        summary = {
            "webhook": {
                "webhook_urls_count": len(webhook_urls),
                "message_length": len(message),
                "successful_sends": successful_sends,
                "failed_sends": len(webhook_urls) - successful_sends,
                "results": results,
                "timestamp": datetime.now(timezone.utc).isoformat()
            },
            "success": successful_sends > 0
        }
        
        if successful_sends > 0:
            return create_success_response(summary, {
                "notification_type": "webhook",
                "webhooks_count": len(webhook_urls),
                "successful_sends": successful_sends
            })
        else:
            return create_error_response(
                "All webhook notifications failed to send",
                "WebhookError",
                summary
            )
    
    except ImportError:
        return create_error_response(
            "Webhook notifications require requests library",
            "ImportError",
            {"required_packages": ["requests"]}
        )
    except Exception as e:
        logger.error(f"Error sending webhook notification: {e}")
        return create_error_response(
            f"Webhook notification failed: {str(e)}",
            type(e).__name__
        )


def send_desktop_notification(
    title: Optional[str], message: str, options: Optional[Dict[str, Any]]
) -> Dict[str, Any]:
    """Send desktop notification."""
    
    try:
        import platform
        import subprocess
        
        system = platform.system().lower()
        
        if system == "windows":
            # Use Windows toast notifications
            try:
                from plyer import notification
                notification.notify(
                    title=title or "n8n Notification",
                    message=message,
                    timeout=options.get('timeout', 10) if options else 10
                )
                success = True
            except ImportError:
                # Fallback to PowerShell
                ps_script = f"""
                Add-Type -AssemblyName System.Windows.Forms
                [System.Windows.Forms.MessageBox]::Show('{message}', '{title or "n8n Notification"}')
                """
                subprocess.run(["powershell", "-Command", ps_script], check=True)
                success = True
        
        elif system == "darwin":  # macOS
            subprocess.run([
                "osascript", "-e", 
                f'display notification "{message}" with title "{title or "n8n Notification"}"'
            ], check=True)
            success = True
        
        elif system == "linux":
            subprocess.run([
                "notify-send", 
                title or "n8n Notification", 
                message
            ], check=True)
            success = True
        
        else:
            return create_error_response(
                f"Desktop notifications not supported on {system}",
                "PlatformError",
                {"supported_platforms": ["windows", "darwin", "linux"]}
            )
        
        result = {
            "desktop": {
                "platform": system,
                "title": title,
                "message_length": len(message),
                "timestamp": datetime.now(timezone.utc).isoformat()
            },
            "success": success
        }
        
        return create_success_response(result, {
            "notification_type": "desktop",
            "platform": system,
            "sent": True
        })
    
    except subprocess.CalledProcessError as e:
        return create_error_response(
            f"Desktop notification command failed: {e}",
            "CommandError"
        )
    except Exception as e:
        logger.error(f"Error sending desktop notification: {e}")
        return create_error_response(
            f"Desktop notification failed: {str(e)}",
            type(e).__name__
        )


def main():
    """Main function for command-line usage."""
    
    parser = argparse.ArgumentParser(
        description="Send notifications through various channels",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Send email
  python3 send_notification.py --input '{"type": "email", "recipients": "user@example.com", "subject": "Test", "message": "Hello World"}'
  
  # Send Slack message
  python3 send_notification.py --input '{"type": "slack", "recipients": "#general", "message": "Deployment completed!"}'
  
  # Send SMS
  python3 send_notification.py --input '{"type": "sms", "recipients": "+1234567890", "message": "Alert: System down"}'
  
  # Send with attachments
  python3 send_notification.py --input '{"type": "email", "recipients": "user@example.com", "subject": "Report", "message": "Please find attached", "attachments": [{"file_path": "/path/to/file.pdf"}]}'
"""
    )
    
    # Input options
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument('--input', help='JSON input data as string')
    input_group.add_argument('--input-file', help='Path to JSON input file')
    
    # Notification type
    parser.add_argument(
        '--type', 
        choices=[
            'email', 'slack', 'discord', 'teams', 'telegram', 
            'sms', 'push', 'webhook', 'desktop'
        ],
        help='Notification type (can also be specified in input data)'
    )
    
    # Output options
    parser.add_argument('--output-file', help='Path to save output JSON file')
    parser.add_argument('--pretty', action='store_true', help='Pretty print JSON output')
    
    args = parser.parse_args()
    
    try:
        # Parse input data
        if args.input:
            input_data = safe_json_loads(args.input)
        else:
            with open(args.input_file, 'r', encoding='utf-8') as f:
                input_data = json.load(f)
        
        # Validate input structure
        schema = {
            "type": {"type": "string", "required": True},
            "recipients": {"type": ["string", "array"], "required": True},
            "message": {"type": "string", "required": True},
            "subject": {"type": "string", "required": False},
            "attachments": {"type": "array", "required": False},
            "options": {"type": "object", "required": False}
        }
        
        validate_input(input_data, schema)
        
        # Extract parameters
        notification_type = input_data.get("type") or args.type
        recipients = input_data["recipients"]
        message = input_data["message"]
        subject = input_data.get("subject")
        attachments = input_data.get("attachments")
        options = input_data.get("options")
        
        if not notification_type:
            raise ValueError("Notification type must be specified")
        
        # Send notification
        result = send_notification(
            notification_type=notification_type,
            message=message,
            recipients=recipients,
            subject=subject,
            attachments=attachments,
            options=options
        )
        
        # Output result
        output_json = json.dumps(result, indent=2 if args.pretty else None, ensure_ascii=False)
        
        if args.output_file:
            with open(args.output_file, 'w', encoding='utf-8') as f:
                f.write(output_json)
            logger.info(f"Results saved to {args.output_file}")
        else:
            print(output_json)
    
    except Exception as e:
        error_result = create_error_response(str(e), type(e).__name__)
        print(json.dumps(error_result), file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()