import os
from fastapi import BackgroundTasks
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from dotenv import load_dotenv

load_dotenv('.env')

class Envs:
    MAIL_USERNAME = os.getenv('MAIL_USERNAME')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
    MAIL_FROM = os.getenv('MAIL_FROM')
    MAIL_PORT = int(os.getenv('MAIL_PORT'))
    MAIL_SERVER = os.getenv('MAIL_SERVER')
    MAIL_FROM_NAME = os.getenv('MAIL_FROM_NAME')

conf = ConnectionConfig(
    MAIL_USERNAME=Envs.MAIL_USERNAME,
    MAIL_PASSWORD=Envs.MAIL_PASSWORD,
    MAIL_FROM=Envs.MAIL_FROM,
    MAIL_PORT=Envs.MAIL_PORT,
    MAIL_SERVER=Envs.MAIL_SERVER,
    MAIL_FROM_NAME=Envs.MAIL_FROM_NAME,
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
)

async def send_email_async(subject: str, email_to: str, body: dict):
    # Convert the body dictionary to a string (HTML formatted)
    body_str = f"""
    <html>
    <body style="margin: 0; padding: 0; box-sizing: border-box; font-family: Arial, Helvetica, sans-serif;">
    <div style="width: 100%; background: #efefef; border-radius: 10px; padding: 10px;">
      <div style="margin: 0 auto; width: 90%; text-align: center;">
        <h1 style="background-color: rgba(0, 53, 102, 1); padding: 5px 10px; border-radius: 5px; color: white;">{body.get('title')}</h1>
        <div style="margin: 30px auto; background: white; width: 40%; border-radius: 10px; padding: 50px; text-align: center;">
          <h3 style="margin-bottom: 100px; font-size: 24px;">Hi {body.get('name')}!</h3>
          <p style="margin-bottom: 30px;">Your password reset token is:</p>
          <h1 style="font-size: 42px; letter-spacing: 2px; margin-bottom: 20px;">{body.get('token')}</h1>
          <p style="margin-bottom: 30px;">The token is valid for 60 seconds.</p>
        </div>
      </div>
    </div>
    </body>
    </html>
    """

    message = MessageSchema(
        subject=subject,
        recipients=[email_to],
        body=body_str,
        subtype='html',
    )
    
    fm = FastMail(conf)
    await fm.send_message(message)

def send_email_background(background_tasks: BackgroundTasks, subject: str, email_to: str, body: dict):
    body_str = f"""
    <html>
    <body style="margin: 0; padding: 0; box-sizing: border-box; font-family: Arial, Helvetica, sans-serif;">
    <div style="width: 100%; background: #efefef; border-radius: 10px; padding: 10px;">
      <div style="margin: 0 auto; width: 90%; text-align: center;">
        <h1 style="background-color: rgba(0, 53, 102, 1); padding: 5px 10px; border-radius: 5px; color: white;">{body.get('title')}</h1>
        <div style="margin: 30px auto; background: white; width: 40%; border-radius: 10px; padding: 50px; text-align: center;">
          <h3 style="margin-bottom: 100px; font-size: 24px;">Hi {body.get('name')}!</h3>
          <p style="margin-bottom: 30px;">Your password reset token is:</p>
          <h1 style="font-size: 42px; letter-spacing: 2px; margin-bottom: 20px;">{body.get('token')}</h1>
          <p style="margin-bottom: 30px;">The token is valid for 60 seconds.</p>
        </div>
      </div>
    </div>
    </body>
    </html>
    """

    message = MessageSchema(
        subject=subject,
        recipients=[email_to],
        body=body_str,
        subtype='html',
    )
    fm = FastMail(conf)
    background_tasks.add_task(fm.send_message, message)
