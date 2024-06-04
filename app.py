from website import create_app,db
from flask import render_template
from flask_migrate import upgrade, init, Migrate
from flask_login import LoginManager
from website.models import User
import base64
from flask_ngrok import start_ngrok, run_with_ngrok
from flask_mail import Mail, Message
# from flask_cors import CORS
# import uvicorn
# import hypercorn
# import subprocess
# import webbrowser
from flask_socketio import SocketIO

app=create_app()
socketio = SocketIO(app=app)
# @app.template_filter('b64encode_custom')
# def b64encode_custom(data):
#     return base64.b64encode(data).decode('utf-8')




login_manager = LoginManager()
login_manager.login_view = 'auth.loginuser'
# login_manager.login_view = 'auth.loginadmin'
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    if user_id is not None or user_id != 'None':
        return User.query.get(int(user_id))
    return None



migrate=Migrate(app, db)


# Create or update the database schema with migrations
with app.app_context():
    db.create_all()
   
    migrate.init_app(app, db)
if __name__=='__main__':
    
    # run_with_ngrok(app=app)
    app.run(debug=True)
    # socketio.run(app,debug=True)
    # hypercorn.run(app, debug=True)