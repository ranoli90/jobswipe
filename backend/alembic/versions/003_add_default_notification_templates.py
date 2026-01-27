"""Add default notification templates

Revision ID: 003_add_default_notification_templates
Revises: 002_add_notification_models
Create Date: 2026-01-27 00:50:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "003_add_default_notification_templates"
down_revision: Union[str, None] = "002_add_notification_models"  # noqa: F841 - Required by Alembic
branch_labels: Union[str, Sequence[str], None] = None  # noqa: F841 - Required by Alembic
depends_on: Union[str, Sequence[str], None] = None  # noqa: F841 - Required by Alembic


def upgrade() -> None:
    """Insert default notification templates"""

    # Insert default notification templates
    op.execute("""
        INSERT INTO notification_templates (id, name, title_template, message_template, email_html_template, channels, is_active, created_at, updated_at) VALUES
        (
            '550e8400-e29b-41d4-a716-446655440001'::uuid,
            'application_submitted',
            'Application Submitted',
            'Your application for {{job_title}} at {{company}} has been submitted successfully.',
            '<!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <title>Application Submitted</title>
                <style>
                    body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }
                    .container { max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 10px; }
                    .header { background-color: #007bff; color: white; padding: 20px; border-radius: 10px 10px 0 0; text-align: center; }
                    .content { padding: 20px; }
                    .footer { text-align: center; color: #666; font-size: 12px; margin-top: 20px; }
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>JobSwipe</h1>
                        <h2>Application Submitted</h2>
                    </div>
                    <div class="content">
                        <p>Great news! Your application for <strong>{{job_title}}</strong> at <strong>{{company}}</strong> has been submitted successfully.</p>
                        <p>We''ll notify you when there''s any update on your application status.</p>
                    </div>
                    <div class="footer">
                        <p>You received this notification because you have notifications enabled for application submissions.</p>
                        <p>You can manage your notification preferences in the app.</p>
                    </div>
                </div>
            </body>
            </html>',
            '["push", "email"]',
            true,
            NOW(),
            NOW()
        ),
        (
            '550e8400-e29b-41d4-a716-446655440002'::uuid,
            'application_completed',
            'Application Completed',
            'Your application for {{job_title}} at {{company}} has been completed. Check your email for details.',
            '<!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <title>Application Completed</title>
                <style>
                    body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }
                    .container { max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 10px; }
                    .header { background-color: #28a745; color: white; padding: 20px; border-radius: 10px 10px 0 0; text-align: center; }
                    .content { padding: 20px; }
                    .footer { text-align: center; color: #666; font-size: 12px; margin-top: 20px; }
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>JobSwipe</h1>
                        <h2>Application Completed</h2>
                    </div>
                    <div class="content">
                        <p>Congratulations! Your application for <strong>{{job_title}}</strong> at <strong>{{company}}</strong> has been completed successfully.</p>
                        <p>Please check your email for any follow-up instructions or next steps from the employer.</p>
                    </div>
                    <div class="footer">
                        <p>You received this notification because you have notifications enabled for application completions.</p>
                        <p>You can manage your notification preferences in the app.</p>
                    </div>
                </div>
            </body>
            </html>',
            '["push", "email"]',
            true,
            NOW(),
            NOW()
        ),
        (
            '550e8400-e29b-41d4-a716-446655440003'::uuid,
            'application_failed',
            'Application Failed',
            'Unfortunately, your application for {{job_title}} at {{company}} could not be completed. {{error_message}}',
            '<!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <title>Application Failed</title>
                <style>
                    body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }
                    .container { max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 10px; }
                    .header { background-color: #dc3545; color: white; padding: 20px; border-radius: 10px 10px 0 0; text-align: center; }
                    .content { padding: 20px; }
                    .footer { text-align: center; color: #666; font-size: 12px; margin-top: 20px; }
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>JobSwipe</h1>
                        <h2>Application Issue</h2>
                    </div>
                    <div class="content">
                        <p>We encountered an issue with your application for <strong>{{job_title}}</strong> at <strong>{{company}}</strong>.</p>
                        <p><strong>Details:</strong> {{error_message}}</p>
                        <p>Don''t worry! You can try applying again or contact our support team for assistance.</p>
                    </div>
                    <div class="footer">
                        <p>You received this notification because you have notifications enabled for application failures.</p>
                        <p>You can manage your notification preferences in the app.</p>
                    </div>
                </div>
            </body>
            </html>',
            '["push", "email"]',
            true,
            NOW(),
            NOW()
        ),
        (
            '550e8400-e29b-41d4-a716-446655440004'::uuid,
            'captcha_detected',
            'Action Required',
            'We detected a CAPTCHA on {{company}}''s application form for {{job_title}}. Please complete it manually.',
            '<!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <title>Action Required</title>
                <style>
                    body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }
                    .container { max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 10px; }
                    .header { background-color: #ffc107; color: black; padding: 20px; border-radius: 10px 10px 0 0; text-align: center; }
                    .content { padding: 20px; }
                    .action-button { display: inline-block; background-color: #007bff; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; margin: 10px 0; }
                    .footer { text-align: center; color: #666; font-size: 12px; margin-top: 20px; }
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>JobSwipe</h1>
                        <h2>Action Required</h2>
                    </div>
                    <div class="content">
                        <p>We detected a CAPTCHA on <strong>{{company}}</strong>''s application form for <strong>{{job_title}}</strong>.</p>
                        <p>To complete your application, please visit the application page and complete the CAPTCHA manually.</p>
                        <a href="#" class="action-button">Complete Application</a>
                    </div>
                    <div class="footer">
                        <p>You received this notification because you have notifications enabled for CAPTCHA detection.</p>
                        <p>You can manage your notification preferences in the app.</p>
                    </div>
                </div>
            </body>
            </html>',
            '["push", "email"]',
            true,
            NOW(),
            NOW()
        ),
        (
            '550e8400-e29b-41d4-a716-446655440005'::uuid,
            'job_match_found',
            'New Job Match',
            'We found a new job match for you: {{job_title}} at {{company}} in {{location}}.',
            '<!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <title>New Job Match</title>
                <style>
                    body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }
                    .container { max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 10px; }
                    .header { background-color: #17a2b8; color: white; padding: 20px; border-radius: 10px 10px 0 0; text-align: center; }
                    .content { padding: 20px; }
                    .job-card { border: 1px solid #ddd; padding: 15px; margin: 10px 0; border-radius: 5px; }
                    .action-button { display: inline-block; background-color: #007bff; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; margin: 10px 0; }
                    .footer { text-align: center; color: #666; font-size: 12px; margin-top: 20px; }
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>JobSwipe</h1>
                        <h2>New Job Match Found!</h2>
                    </div>
                    <div class="content">
                        <p>Great news! We found a job that matches your profile:</p>
                        <div class="job-card">
                            <h3>{{job_title}}</h3>
                            <p><strong>Company:</strong> {{company}}</p>
                            <p><strong>Location:</strong> {{location}}</p>
                            <p><strong>Match Score:</strong> {{match_score}}%</p>
                        </div>
                        <a href="#" class="action-button">View Job Details</a>
                    </div>
                    <div class="footer">
                        <p>You received this notification because you have notifications enabled for job matches.</p>
                        <p>You can manage your notification preferences in the app.</p>
                    </div>
                </div>
            </body>
            </html>',
            '["push", "email"]',
            true,
            NOW(),
            NOW()
        ),
        (
            '550e8400-e29b-41d4-a716-446655440006'::uuid,
            'system_notification',
            'System Notification',
            '{{message}}',
            '<!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <title>System Notification</title>
                <style>
                    body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }
                    .container { max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 10px; }
                    .header { background-color: #6c757d; color: white; padding: 20px; border-radius: 10px 10px 0 0; text-align: center; }
                    .content { padding: 20px; }
                    .footer { text-align: center; color: #666; font-size: 12px; margin-top: 20px; }
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>JobSwipe</h1>
                        <h2>System Notification</h2>
                    </div>
                    <div class="content">
                        <p>{{message}}</p>
                    </div>
                    <div class="footer">
                        <p>You received this notification because you have system notifications enabled.</p>
                        <p>You can manage your notification preferences in the app.</p>
                    </div>
                </div>
            </body>
            </html>',
            '["push", "email"]',
            true,
            NOW(),
            NOW()
        )
    """)


def downgrade() -> None:
    """Remove default notification templates"""
    op.execute("""
        DELETE FROM notification_templates
        WHERE id IN (
            '550e8400-e29b-41d4-a716-446655440001'::uuid,
            '550e8400-e29b-41d4-a716-446655440002'::uuid,
            '550e8400-e29b-41d4-a716-446655440003'::uuid,
            '550e8400-e29b-41d4-a716-446655440004'::uuid,
            '550e8400-e29b-41d4-a716-446655440005'::uuid,
            '550e8400-e29b-41d4-a716-446655440006'::uuid
        )
    """)
