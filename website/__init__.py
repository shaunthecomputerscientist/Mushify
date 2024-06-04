from flask import Flask, url_for
from flask_sqlalchemy import SQLAlchemy
# from flask_bcrypt import Bcrypt
# from flask_migrate import Migrate
# from flask_uploads import UploadSet, configure_uploads, IMAGES, TEXT
# from flask_login import login_manager, LoginManager
from flask_mail import Mail, Message
from flask_restful import Api
# from flask_share import Share
# from flask_bootstrap import Bootstrap
# from werkzeug.utils import import_string
# import werkzeug
# werkzeug.import_string = import_string
# from flask_cache import Cache
# from .models import User
import configparser
import secrets
from flask_caching import Cache

from flask_socketio import SocketIO, emit

app = Flask(__name__)



db=SQLAlchemy()
DB_NAME= "database.db"
def create_cache():
    cache = Cache(config={'CACHE_TYPE': 'filesystem', 'CACHE_DIR': '/tmp'})
    cache.init_app(app)
    return cache
cache = create_cache()


import os
from dotenv import load_dotenv
load_dotenv()

current_path = os.getcwd()
current_path=current_path.replace('\\' , '\\\\')
# relative_path1='\\website\\static\\images'
# path=os.path.join(current_path,relative_path1)
# print(path)
app = Flask(__name__)
api = Api(app=app)
socketio = SocketIO(app)

###########################################################################################
secret_key = secrets.token_hex(32)

salt = secrets.token_hex(16)

# Write the generated values to the config file
config = configparser.ConfigParser()
config.read('config.txt')

# Update the 'EMAIL' section with the new secret key and salt
config.set('EMAIL', 'SECRET_KEY', secret_key)
config.set('EMAIL', 'SALT', salt)

# Save the changes to the config file
with open('config.txt', 'w') as config_file:
    config.write(config_file)

def saltkey():
    return salt
def secretkey():
    return secret_key
###########################################################################################
def create_app():
    app = Flask(__name__)

    app.config["SQLALCHEMY_DATABASE_URI"] = f'sqlite:///{DB_NAME}' #declear database uri
    # app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:postgreshellomoto143!!!@localhost/mushifydb'

    #cache memory
    # app.config['CACHE_TYPE'] = 'simple'
    # cache.init_app(app)

    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')



    
    db.init_app(app)
    
    from .views import views
    from .auth import auth
    # images = UploadSet('images', extensions=IMAGES)
    # music = UploadSet('music', extensions=('mp3','wav'))
    absolute_path1='\\website\\static\\images'
    absolute_path2='\\website\\static\\music'
    
    app.config['UPLOADS_DEFAULT_DEST'] = os.path.join(app.root_path, 'website', 'static')
    app.config['UPLOADS_IMAGES_DEST'] = current_path+absolute_path1
    # os.path.join(app.config['UPLOADS_DEFAULT_DEST'], 'images')
    app.config['UPLOADS_MUSIC_DEST'] = current_path+absolute_path2
    # os.path.join(app.config['UPLOADS_DEFAULT_DEST'], 'music')




    

    # configure_uploads(app, (images, music))
    
    
    

    # app.config['SECRET_KEY'] = "iodscimcsisimdmj"
    app.register_blueprint(views,url_prefix='/')
    app.register_blueprint(auth, url_prefix='/')

    return app


def mail_sender(name,email):
    app = Flask(__name__)
    import configparser
    config = configparser.ConfigParser()
    config.read('config.txt')
    mail_password = config.get('EMAIL', 'MAIL_PASSWORD')
    # print(mail_password)
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_SERVER'] = 'smtp.gmail.com'
    app.config['MAIL_PORT'] = 587
    app.config['MAIL_USE_SSL'] = False
    app.config['MAIL_USERNAME'] = 'mrpolymathematica@gmail.com'
    app.config['MAIL_PASSWORD'] = mail_password
    msg = Message('Thank You For Signing Up.', sender='mrpolymathematica@gmail.com', recipients=[email])
    msg.body = f"Name: {name}\n Email: {email} \n"
    msg.body+="Thank you for Joining our Mushify community, we are thrilled to announce that you are now a part of a community with spectacular music taste. You can choose to become a creator and use our ai tools to take your music career forward. Enjoy your time here.\n"
    msg.body += "\n Best regards,\n Team Mushify."
    msg.html=msg.body.encode("utf-8")
    mail = Mail(app)
    mail.send(msg)
    return msg
def send_password_reset_email(email, reset_token):
    app = Flask(__name__)
    import configparser
    config = configparser.ConfigParser()
    config.read('config.txt')
    mail_password = config.get('EMAIL', 'MAIL_PASSWORD')
    # print(mail_password)
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_SERVER'] = 'smtp.gmail.com'
    app.config['MAIL_PORT'] = 587
    app.config['MAIL_USE_SSL'] = False
    app.config['MAIL_USERNAME'] = 'mrpolymathematica@gmail.com'
    app.config['MAIL_PASSWORD'] = mail_password
    reset_link = url_for('auth.reset_password', token=reset_token, _external=True)

    subject = 'Password Reset Request (Mushify)'
    body = f'Click the following button to reset your password:\n'\
           f'{reset_link} \n'\
           f'Note: If you do not intend to reset password or did not ask for this mail ignore it and no changes will be made.'
        #f'<p><a href="{reset_link}" style="background-color: #4CAF50; color: white; padding: 10px 15px; text-align: center; text-decoration: none; display: inline-block; border-radius: 5px;">Reset Password</a></p>' \
    msg = Message(subject, recipients=[email], body=body, sender='mrpolymathematica@gmail.com')
    mail = Mail(app)
    mail.send(msg)
    return msg

def send_email_verification_email(email, reset_token):
    app = Flask(__name__)
    import configparser
    config = configparser.ConfigParser()
    config.read('config.txt')
    mail_password = config.get('EMAIL', 'MAIL_PASSWORD')
    # print(mail_password)
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_SERVER'] = 'smtp.gmail.com'
    app.config['MAIL_PORT'] = 587
    app.config['MAIL_USE_SSL'] = False
    app.config['MAIL_USERNAME'] = 'mrpolymathematica@gmail.com'
    app.config['MAIL_PASSWORD'] = mail_password
    print(email)
    reset_link = url_for('auth.emailverification', token=reset_token, _external=True)

    subject = 'Verify Your Email (Mushify)'
    body = f'Click the following button to confirm your mushify email:\n'\
           f'{reset_link} \n'\
           f'Note: If you do not intend to signup or did not ask for this mail ignore it and no changes will be made.'
        #f'<p><a href="{reset_link}" style="background-color: #4CAF50; color: white; padding: 10px 15px; text-align: center; text-decoration: none; display: inline-block; border-radius: 5px;">Reset Password</a></p>' \
    msg = Message(subject, recipients=[email], body=body, sender='mrpolymathematica@gmail.com')
    mail = Mail(app)
    mail.send(msg)
    return msg

