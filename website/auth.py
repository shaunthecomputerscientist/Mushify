from flask import Blueprint, render_template, request, flash, redirect, url_for,session, current_app
import os
from sqlalchemy import or_, desc, func, and_
from . import db,create_app
from flask_bcrypt import Bcrypt
from .models import User, Song, UserLike, Administratormushify, Album, Playlist, UserLikeAlbum, UserFollowsArtist, PlaylistSong, DailyUserActivity, UserSongInteraction
from flask_login import current_user, login_required, logout_user, login_user
import base64
from flask import jsonify
import requests
import razorpay
from werkzeug.utils import secure_filename
from datetime import datetime, date, time, timedelta, timezone
import calendar
# from . import cache
from flask_mail import Mail, Message
# mail= Mail(current_app)
from . import mail_sender, send_password_reset_email, saltkey, secretkey, send_email_verification_email, socketio
# print(mail)
# print(type(mail))
from flask_socketio import emit
from zerobouncesdk import ZeroBounce, ZBException

from dotenv import load_dotenv
load_dotenv()
from . import cache


auth = Blueprint('auth', __name__)

bcrypt= Bcrypt()



# app.config['UPLOAD_FOLDER_IMAGE'] = 'static/image'
# app.config['UPLOAD_FOLDER_MUSIC'] = 'static/music'


# @auth.login_manager.user_loader
# def load_user(user_id):
#         return User.query.get(int(user_id))

import random, string
from itsdangerous import URLSafeTimedSerializer
# import configparser
# import secrets

# def generate_random_string(length):
#     characters = string.ascii_letters + string.digits + string.punctuation
#     return ''.join(random.choice(characters) for char in range(length))
# print(generate_random_string(30))
def generate_password_reset_token(user_id):
    serializer = URLSafeTimedSerializer(secret_key=secretkey())
    return serializer.dumps(user_id, salt=saltkey())
def generate_email_verification_token(email):
    serializer = URLSafeTimedSerializer(secret_key=secretkey())
    return serializer.dumps(email, salt=saltkey())

from flask_mail import Message

import ast, json, re
def validate_email(email):
    zero_bounce = ZeroBounce(os.environ.get("ZERO_BOUNCE_EMAIL_VALIDATOR_API_KEY"))
    # ip_address = "127.0.0.1"    # The IP Address the email signed up from (Optional)
    # email='mrpolyathematica@gmail.com'
    try:
        response = zero_bounce.validate(email)
        print("ZeroBounce validate response: " + str(response))
        str_response=str(response)[19:]
        string_representation = str_response
        print(string_representation)

        # Extract key-value pairs using regular expression
        # pattern = r"'(.*?)': '(.*?)'"
        # pattern2=r"'(.*?)': (None|[^,}]+)"
        # # matches = re.findall(pattern, string_representation)
        # matches2 = re.findall(pattern2,string_representation)
        # print(matches2)

        # # Convert the extracted pairs to a dictionary
        # # dictionary_result = dict(matches)
        # dictionary_result2 = dict(matches2)
        # # print(dictionary_result, dictionary_result2)

        # status_representation = "'status': <ZBValidateStatus.invalid: 'valid'>"
        pattern3 = r"'status': <ZBValidateStatus.(valid|invalid): '(valid|invalid)'>"
        status_matches = re.search(pattern3, string_representation)
        print(status_matches)
        if status_matches:
            status = status_matches.group(1)
            print(status)
            if status == 'valid':
                print("Email is valid")
                return True
            elif status == 'invalid':
                print("Email is invalid")
                return False
            else:
                print(f"Unknown status: {status}")
    except ZBException as e:
        print("ZeroBounce validate error: " + str(e))
        return False
# validate_email()
@auth.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')

        if not email:
            flash('Email is required', category='error')
            return redirect(url_for('auth.forgot_password'))

        user = User.query.filter_by(email=email).first()

        if user:
            reset_token = generate_password_reset_token(user.id)

            send_password_reset_email(user.email, reset_token)

            flash('Password reset instructions sent to your email', category='success')
            return redirect(url_for('auth.loginuser'))
        elif not user:
            flash('Email address not found', category='error')
            return redirect(url_for('auth.forgot_password'))

        else:
            if not validate_email(email):
                flash('Email address not found', category='error')
                return redirect(url_for('auth.forgot_password'))

    return render_template('forgotdetails/forgot_password.html')

@auth.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    serializer = URLSafeTimedSerializer(secret_key=secretkey())
    try:
        user_id = serializer.loads(token, salt=saltkey(), max_age=3600)
    except:
        flash('Invalid or expired reset link', category='error')
        return redirect(url_for('auth.loginuser'))

    user = User.query.get(user_id)

    if request.method == 'POST' and user:
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')

        if new_password != confirm_password:
            flash('Passwords do not match', category='error')
        else:
            hashed_password = bcrypt.generate_password_hash(password=new_password)
            user.password = hashed_password
            db.session.commit()

            flash('Password reset successfully. You can now log in with your new password', category='success')
            return redirect(url_for('auth.loginuser'))

    return render_template('forgotdetails/reset-password.html', token=token)







@auth.route('/signupuser', methods=["GET", "POST"])
def signupuser():
    if request.method == "POST":
        email = request.form.get('email')
        firstname = request.form.get('firstname')
        lastname = request.form.get('lastname')
        password = request.form.get('password1')
        password2 = request.form.get('password2')

        existing_user = User.query.filter_by(email=email).first()

        if existing_user:
            flash('User already exists. Please use a different email.', category='error')
            return redirect(url_for('auth.loginuser'))

        if password != password2:
            flash('Passwords do not match', category='error')
        elif not password or not password2:
            flash('Password is required', category='error')
        else:
            hashed_password = bcrypt.generate_password_hash(password=password2)
            session['userpassword']=hashed_password
            user_name=firstname + " " + lastname
            session['username']=user_name
            session['email']=email
            # new_user = User(email=email, password=hashed_password, user_name=firstname + " " + lastname)
            # db.session.add(new_user)
            # db.session.commit()
            # login_user(new_user)
            # Generate a unique token for the password reset link
            if not validate_email(email):
                flash('Enter your actual email address', category='error')
                return redirect(url_for('auth.signupuser' , user="user"))
            else:

                verification_token = generate_email_verification_token(email)

                # Send the password reset email with a link containing the reset token
                send_email_verification_email(email, verification_token)

            
           
            # msg.body += "We're thrilled to have you as a member of our community. You can enjoy the best music here."
            # msg.body += "Now have access to a world of exciting features and content. Become creator to generate ai music.\n\n" 
            # print(msg)
            # mail.send(msg)
            # print(mail.send(msg))
                flash('Verification mail has been sent.', category='success')
                
                return redirect(url_for('auth.signupuser' , user="user"))

            # try:
            #     mail.send(msg)
               
            # except Exception as e:
            #     return f"An error occurred while sending the email: {str(e)}"
           
    return render_template('signup/signupuser.html')
@auth.route('/mushify/user-authentication/<token>', methods=["GET", "POST"])
def emailverification(token):
    serializer = URLSafeTimedSerializer(secret_key=secretkey())

    try:
        email = serializer.loads(token, salt=saltkey(), max_age=3600)
        print("You registered with"+ email)
        new_user = User(email=session['email'], password=session['userpassword'], user_name=session['username'])
        db.session.add(new_user)
        db.session.commit()
        print("reached")

        flash('Email verification successful. Account created. You can now log in.', category='success')
        mail_sender(name=session['username'],email=email)
        return redirect(url_for('auth.loginuser',user="user"))

    except:
        flash('Invalid or expired verification link', category='error')
        return redirect(url_for('auth.signupuser'))

@auth.route('/signupadmin', methods=["GET", "POST"])
def signupadmin():
    if request.method == "POST":
        email = request.form.get('email')
        firstname = request.form.get('firstname')
        lastname = request.form.get('lastname')
        password = request.form.get('password1')
        password2 = request.form.get('password2')
        secretkey= request.form.get('secretkey')
        app_secret=os.environ.get('SECRET_KEY')

        # Check if the email already exists in the database
        existing_user = Administratormushify.query.filter_by(email=email).first()

        if existing_user:
            flash('User already exists. Please use a different email.', category='error')
            return redirect(url_for('auth.loginadmin'))

        if password != password2:
            flash('Passwords do not match', category='error')
        elif not password or not password2:
            flash('Password is required', category='error')
        elif app_secret==secretkey and (password==password2):
            hashed_password = bcrypt.generate_password_hash(password=password2)
            new_admin = Administratormushify(email=email, password=hashed_password, user_name=firstname + " " + lastname , is_admin=True)
            db.session.add(new_admin)
            db.session.commit()
            flash('Account created successfully', category='success')
            return redirect(url_for('auth.loginadmin'))

    return render_template('signup/signupuser.html', admin="admin")





@auth.route('/loginuser', methods=["GET","POST"])
def loginuser():
    if request.method=="GET":
        user=True
        return render_template("login/login.html", user=user)

    if request.method=="POST":
        email=request.form.get('email')
        password=request.form.get('password1')
        
        existing_user=User.query.filter_by(email=email).first()
        if existing_user is None:
            # print("reached")
            flash("This account does not exist, create a new account", category="error")
            return redirect(url_for('auth.signupuser'))
        else:
            # isadmin= existing_user.is_admin
            if existing_user and bcrypt.check_password_hash(existing_user.password , password):
                login_user(existing_user)
                username=existing_user.user_name
                session['user-name']=username
                session['user-email']=email
                existing_user.last_login = datetime.now()
                existing_user.is_online = True
                db.session.commit()
                socketio.emit('update_user_status', {'user_id': existing_user.id, 'is_online': True}, namespace='/')
                if existing_user.is_creator:
                    return redirect(url_for("auth.creator"))
                # elif isadmin:
                #     return redirect(url_for("auth.admin"))
                # else:
                
                return redirect(url_for("auth.user"))
        
            elif bcrypt.check_password_hash(existing_user.password , password)==False:
                flash("check your password", category="error")
                return redirect(url_for("auth.loginuser"))
            else:
                return redirect(url_for("auth.loginuser"))
@auth.route("/user/dashboard/change-details", methods=["GET", "POST"])
@login_required
def changeuserdetails():
    if request.method=="GET":
        user=User.query.filter_by(id=current_user.id).first()
        print(user.id, user.email)
        return render_template('user/changeuserdetails.html', user=user)
    if request.method=="POST":
        user=User.query.filter_by(id=current_user.id).first()
        print(user.id, user.email)
        email=request.form.get('email')
        firstname=request.form.get('firstname')
        lastname=request.form.get('lastname')
        old_password=request.form.get('oldpassword')
        newpassword=request.form.get('newpassword')
        confirmpassword=request.form.get('password2')
        if user:
            if newpassword != confirmpassword:
                flash('Passwords do not match', category='error')
                return redirect(url_for('auth.changeuserdetails'))
            elif not old_password or not newpassword or not confirmpassword:
                flash('Password is required', category='error')
                return redirect(url_for('auth.changeuserdetails'))
            elif bcrypt.check_password_hash(user.password , old_password) and  newpassword == confirmpassword:
                hashed_password = bcrypt.generate_password_hash(password=confirmpassword)
                user.email=email
                user.user_name= firstname+""+lastname
                user.password=hashed_password

                db.session.commit()
                flash('Details Added', category='success')
                return render_template('user/changeuserdetails.html', user=user)
        else:
            flash('You never signed up', category='error')
            return redirect(url_for('auth.signupuser'))
        




            



@auth.route('/loginadmin', methods=["GET","POST"])
def loginadmin():
    if request.method=="POST":
        email=request.form.get('email')
        password=request.form.get('password1')
        
        existing_user=Administratormushify.query.filter_by(email=email).first()
        print(existing_user.is_admin)
        # print(email)
        # print(existing_user)
        # print(password)
        if existing_user is None:
            flash("This account does not exist, create a new account", category="error")
            return render_template("signup/signupadmin.html")
        elif existing_user:
            # iscreator=existing_user.is_creator
            # isadmin= existing_user.is_admin
            if existing_user and bcrypt.check_password_hash(existing_user.password , password):
                login_user(existing_user)
                username=existing_user.user_name
                session['user-name']=username
                session['user-email']=email
                # if not existing_user.is_admin or existing_user.is_admin==None:
                existing_user.is_admin=True
                db.session.commit()
                print(f"isdmin: {existing_user.is_admin} ")
                
                return redirect(url_for("auth.admin"))
        
            elif bcrypt.check_password_hash(existing_user.password , password)==False:
                flash("check your password", category="error")
                return redirect(url_for("auth.loginadmin"))
            else:
                return redirect(url_for("auth.loginadmin"))
    return render_template("login/login.html")

















@auth.route("/user/dashboard", methods=["GET", "POST"])
@login_required
def user():
    if "user-name" and "user-email" in session:
        username = session["user-name"]
        user = User.query.filter_by(id=current_user.id).first()
        allsongs= Song.query.all()
        ##################################################################################################################
        if user.is_creator==False:
            # songs=Song.query.order_by(desc(Song.likes)).limit(5).all()
            liked_song_ids = (
            db.session.query(UserLike.song_id)
            .filter(UserLike.user_id == current_user.id)
            .all()
            )
            # print(liked_song_ids)
            # for id in liked_song_ids:
            #     print(id)

        
            liked_song_ids = [song_id for (song_id,) in liked_song_ids]
            # print(liked_song_ids)

            # Retrieve the genres of liked songs
            liked_genres = (
                db.session.query(Song.genre)
                .filter(Song.id.in_(liked_song_ids))
                .all()
            )
            # print(liked_genres)

            
            preferred_genres = [genre.strip('') for (genre,) in liked_genres]
            # preferred_genres= [genre.rstrip('') for genre in preferred_genres]
            # preferred_genres = [genre for genres in preferred_genres for genre in genres.split('/')]
            # print(preferred_genres)
            new_preferred_genres_list=[]
            for genre in preferred_genres:

                newlist= genre.strip("'").strip(".").strip('/').split(",")
                new_preferred_genres_list+=newlist
                newlist=[]
            # print(new_preferred_genres_list)
            # print(type(new_preferred_genres_list))
            new_preferred_genres_list=[genre.lstrip() for genre in new_preferred_genres_list]
            new_preferred_genres_list=[genre.rstrip().lower() for genre in new_preferred_genres_list]
            # print(new_preferred_genres_list)
            filtered_songs = []
            count=0
            for song in Song.query.order_by(Song.likes.asc()).limit(10).all():
                # print(song.name)
                song_genres = [genre.strip() for genre in song.genre.split(',')]
                # print(song_genres)
                if any(genre for genre in song_genres if genre.lower() in new_preferred_genres_list):
                    # count+=1
                    # print(count)
                    filtered_songs.append(song)
            songs = filtered_songs
            # print(songs)

            ##################################################################################################################
            playlists = Playlist.query.filter_by(user_id=current_user.id)
            for artist in user.followed_artists:
                print(type(not artist), not artist)
                print(artist)
            
            return render_template("user/userdashboard.html", username=username, songs=songs, playlists=playlists , user=user, liked_song_ids=liked_song_ids, allsongs=allsongs)
        elif user.is_creator==True:
            return redirect(url_for('auth.creator'))

    else:
        return redirect(url_for("auth.loginuser"))


def update_daily_user_activity():
    last_month = datetime.now() - timedelta(days=30)
    print(last_month)
    active_users = User.query.filter(User.last_login >= last_month).all()
    num_active_users = len(active_users)
    today = datetime.utcnow().date()
    daily_activity = DailyUserActivity.query.filter_by(date=today).first()
    
    if daily_activity:
        daily_activity.active_user_count = num_active_users
    else:
        daily_activity = DailyUserActivity(date=today, active_user_count=num_active_users)
        db.session.add(daily_activity)

    db.session.commit()
    return num_active_users
# update_daily_user_activity()


@auth.route("/admin/dashboard", methods=["GET","POST"])
@login_required
def admin():
    if "user-name" and "user-email" in session:
        username = session["user-name"]
        normal_users=User.query.filter_by(is_creator=False).all()
        creators= User.query.filter_by(is_creator=True).all()
        songs= Song().query.all()
        albums=Album().query.all()
        usercount=len(normal_users)
        creatorcount=len(creators)
        songcount=len(songs)
        albumcount=len(albums)
        songlikes= sum([song.likes for song in songs])
        albumlikes= sum([album.like for album in albums])
        # last_month = datetime.now() - timedelta(days=30)
        # active_users = User.query.filter(User.last_login >= last_month).all()
        num_active_users = update_daily_user_activity()
        # daily_activities = DailyUserActivity.query.all()
        # daily_activities_dates= DailyUserActivity.query.filter(DailyUserActivity.date).all()
        # daily_activities_dates_user_count=DailyUserActivity.query.filter(DailyUserActivity.active_user_count).all()
        # print(daily_activities_dates_user_count,daily_activities_dates)
        daily_activities_dates = [
            {'date': activity.date.isoformat(), 'active_user_count': activity.active_user_count}
            for activity in DailyUserActivity.query.all()
            if activity.date and activity.active_user_count is not None
        ]
        print(daily_activities_dates)
        print(songs)
        print(type(songs))

        
        return render_template("administrator/admindashboard.html",daily_activities_dates=daily_activities_dates, username=username, normal_users=normal_users, creators=creators, songs=songs, albums=albums,usercount=usercount, creatorcount=creatorcount, songcount=songcount, albumcount=albumcount, songlikes=songlikes, albumlikes=albumlikes, num_active_users=num_active_users)
    else:
        return redirect(url_for("auth.loginadmin"))
    

def is_subscription_valid(user):
    # if user.subscription_end_date is None:
    #     return False
    current_date = datetime.now().date()
    if current_date <= user.subscription_end_date:
        return True
    else:
        if user.is_creator:
            user.is_creator = False
        if user.is_creator and user.premium:
            user.is_creator = False
            user.premium = False
        db.session.commit()
        return False

from .models import offersNdicounts
@auth.route('/user/dashboard/paymentgateway',methods=["POST"])
@login_required
def becomecreator():
    offer_code = os.environ.get('OFFERCODE')

    print(offer_code)
    if offer_code is not None:
        discount_amount = offersNdicounts.query.filter_by(offercode=offer_code).first()
    if request.method=="GET":
        return render_template('payment/paymentdetails.html' , discount_amount=discount_amount)
    if request.method=="POST":

        if current_user.is_creator and current_user.premium:
            flash('You are have already upgraded to Premium.', category="success")
            return redirect(url_for('auth.creator'))
        elif not current_user.premium and current_user.is_creator:


            if discount_amount:
                return redirect(url_for('auth.paymentdetails' , discount=discount_amount.discount))
            else:
                return redirect(url_for('auth.paymentdetails'))
               
        elif not current_user.is_creator:
            if discount_amount:
                return redirect(url_for('auth.paymentdetails' , discount=discount_amount.discount))
            else:
                return redirect(url_for('auth.paymentdetails'))
def get_usd_to_inr_exchange_rate():
    url = "https://open.er-api.com/v6/latest/USD"
    
    try:
        response = requests.get(url)
        data = response.json()
        
        # Extract the exchange rate for 1 USD in INR
        usd_to_inr_rate =int(data["rates"]["INR"])
        
        return usd_to_inr_rate
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return None
    except KeyError:
        print("Error: Unable to retrieve the exchange rate")
        return None


@auth.route('/user/dashboard/paymentdetails', methods=["GET","POST"])
@login_required
def paymentdetails():
    offer_code = os.environ.get('OFFERCODE')
    discount_amount = offersNdicounts.query.filter_by(offercode=offer_code).first()
    if discount_amount is not None:
        print(discount_amount.discount)
    if request.method=="GET":
    #    offer_code = os.environ.get('OFFERCODE')
    #    discount_amount = offersNdicounts.query.filter_by(offercode=offer_code).first()
    #    print(discount_amount.discount)
       if discount_amount is not None:
           session['discount_amount'] = discount_amount.discount
       
       
       return render_template('payment/paymentdetails.html' , discount_amount=discount_amount)
    
    if request.method=="POST":
       user = User.query.filter_by(id=current_user.id).first()
       print(request.form.get('amount'), type(request.form.get('amount')))
       amount = int(request.form.get('amount'))
       months = int(request.form.get('months'))
       session["amount"]=amount
       session['months']=months
       current_date = datetime.now().date()
       if user.subscription_end_date:
        if current_date <= user.subscription_end_date:
            remaining_days = (user.subscription_end_date - current_date).days
            if user.is_creator and not user.premium and remaining_days>10 and amount==99:
                flash("You can only take premium after your current creator subscription is over or is going to be over in 10 days.", category="error")
                return redirect(url_for("auth.creator"))
            elif user.is_creator and user.premium and remaining_days>1 and (amount==99 or amount==25):
                flash("Wait for the current subscription to get over.", category="error")
                return redirect(url_for("auth.creator"))

       
       print(discount_amount)
       if discount_amount:
                if discount_amount.discount:
                    amount_in_usd = amount * get_usd_to_inr_exchange_rate() * (discount_amount.discount/100)
       else:
           amount_in_usd = amount * get_usd_to_inr_exchange_rate()
       email= request.form.get('email')
       name= request.form.get('name')
       number = request.form.get('number')
       razorpay_key_id = os.getenv("RAZORPAY_KEY_ID")
       razorpay_key_secret = os.getenv("RAZORPAY_KEY_SECRET")
       client= razorpay.Client(auth=(razorpay_key_id, razorpay_key_secret))
       payment= client.order.create({'amount' : int(amount_in_usd)*100*months , 'currency': 'INR', 'payment_capture': '1'})
       print(amount, type(amount))
       print(amount_in_usd*months)
       return render_template('payment/payment.html', payment=payment, amount=amount, months=months, discount_amount=discount_amount)




def add_subscription(user, validity_months, amount):
    current_date = datetime.now().date()
    subscription_end_date = current_date + timedelta(days=validity_months * 30)

    if amount == 25:
        # User subscribes to $25/month plan
        user.is_creator = True
        user.creator_name = user.user_name
    elif amount == 99:
        # User subscribes to $99/month premium plan
        user.is_creator = True
        user.creator_name = user.user_name
        user.premium = True

    user.subscription_validity = validity_months
    user.subscription_start_date = current_date
    user.subscription_end_date = subscription_end_date

    db.session.commit()

    return "success"

def update_subscription(user, validity_months):
    current_date = datetime.now().date()
    if current_date <= user.subscription_end_date:
        remaining_days = (user.subscription_end_date - current_date).days
        subscription_end_date = current_date + timedelta(days=remaining_days + validity_months * 30)
    else:
        subscription_end_date = current_date + timedelta(days=validity_months * 30)
    user.subscription_validity = validity_months
    user.subscription_start_date = current_date
    user.subscription_end_date = subscription_end_date
    user.is_creator = True
    user.premium = True

    db.session.commit()
    return True

@auth.route('/user/dashboard/payment', methods=["GET","POST"])
@login_required
def payment():
    if request.method=="POST":
        amount = session.get('amount', None)
        months = session.get('months', None)

        user = User.query.filter_by(id=current_user.id).first()
        if user.is_creator and not user.premium:
            status = update_subscription(user, validity_months=months)
            if status:
                flash("You are upgraded to premium.", category="success")
                return redirect(url_for("auth.creator"))
            elif not status:
                flash("You can only take premium after your current creator subscription is over or when it is going to be over in 10 days.", category="error")
                return redirect(url_for("auth.creator"))
        else:
            success = add_subscription(user,months,amount)
            if success == "success":
        # if amount==25:
        #     user = User.query.filter_by(id=current_user.id).first()
        #     user.is_creator=True
        #     user.creator_name=user.user_name #creator name is user name by default...
        #     db.session.commit()
        #     return redirect(url_for("auth.creator"))
        # elif amount==99:
        #     user = User.query.filter_by(id=current_user.id).first()
        #     user.is_creator=True
        #     user.creator_name=user.user_name #creator name is user name by default...
        #     user.premium=True
        #     db.session.commit()
                return redirect(url_for("auth.creator"))

        


    
@auth.route("/creator/dashboard")
@login_required
def creator():
    if "user-name" and "user-email" in session:

        if current_user.is_creator and is_subscription_valid(current_user):
            username = session["user-name"]
            email = session["user-email"]
            currentTime = datetime.now().date()
            # currentTime = currentTime.strftime("%Y-%m-%d")
            # currentTime = datetime.strptime(currentTime, "%Y-%m-%d")
            user=User.query.filter_by(id=current_user.id).first()
            createdsongs = Song.query.filter_by(creator_id=current_user.id).all()
            allsongs= Song.query.all()
            albums = Album.query.filter_by(artist_id=current_user.id).all()
            playlists = Playlist.query.filter_by(user_id=current_user.id).all()
            savedsongs = UserFavoriteSong.query.filter_by(user_id=current_user.id).all()
            favsongs = [song for song in allsongs if song.id in [song.song_id for song in savedsongs]]
            print(favsongs)
            userflag= user.flag
            songflaglist = [{song.name:song.flag} for song in createdsongs if song.flag>0]
            # print(type(userflag))
            # print(type(songflag))
            for item in songflaglist:
                print(item)


            liked_song_ids = (
            db.session.query(UserLike.song_id)
            .filter(UserLike.user_id == current_user.id)
            .all()
            )
            # print(liked_song_ids)
            # for id in liked_song_ids:
            #     print(id)

        
            liked_song_ids = [song_id for (song_id,) in liked_song_ids]
            # print(liked_song_ids)

            # Retrieve the genres of liked songs
            liked_genres = (
                db.session.query(Song.genre)
                .filter(Song.id.in_(liked_song_ids))
                .all()
            )
            # print(liked_genres)

            
            preferred_genres = [genre.strip('') for (genre,) in liked_genres]
            # preferred_genres= [genre.rstrip('') for genre in preferred_genres]
            # preferred_genres = [genre for genres in preferred_genres for genre in genres.split('/')]
            # print(preferred_genres)
            new_preferred_genres_list=[]
            for genre in preferred_genres:

                newlist= genre.strip("'").strip(".").strip('/').split(",")
                new_preferred_genres_list+=newlist
                newlist=[]
            # print(new_preferred_genres_list)
            # print(type(new_preferred_genres_list))
            new_preferred_genres_list=[genre.lstrip().rstrip().lower() for genre in new_preferred_genres_list]
            # new_preferred_genres_list=[genre.rstrip() for genre in new_preferred_genres_list]
            print(new_preferred_genres_list)
            filtered_songs = []
            count=0
            tempgenre=[]
            for song in Song.query.order_by(Song.likes.asc()).limit(10).all():
                # print(song.name)
                song_genres = [genre.strip() for genre in song.genre.split(',')]
                tempgenre+=song_genres
                # print(song_genres)
                if any(genre for genre in song_genres if genre.lower() in new_preferred_genres_list):
                    # count+=1
                    # print(count)
                    # print((genre,song.name,song.genre), new_preferred_genres_list)
                    filtered_songs.append(song)
                
            # var=[genre for genre in tempgenre if genre.lower() in new_preferred_genres_list]
            # print(var)
            print(filtered_songs)
            preferredsongs=filtered_songs
            preferredsongs.sort(key=lambda song:song.likes, reverse=True)
            # print(preferredsongs)

            ##################################################################################################################
            following_count=len(list(user.followed_artists))
            number_of_followers = len(list(user.followers))
            total_likes_over_all_songs = sum([song.likes for song in createdsongs if song.category=="song"])
            total_likes_over_all_podcasts = sum([song.likes for song in createdsongs if song.category=="podcast"])
            total_likes_over_all_stories = sum([song.likes for song in createdsongs if song.category=="story"])
            total_likes_over_all_albums = sum([album.like for album in albums])
            print(total_likes_over_all_albums)
            total_song_count_on_platform = len([song for song in allsongs if song.category=="song"])
            total_podcast_count = len([song for song in createdsongs if song.category=="podcast"])
            total_story_count = len([song for song in createdsongs if song.category=="story"])
            total_song_count_by_user = len([song for song in createdsongs if song.category=="song"])

            
            # print(total_likes_over_all_albums)
            # print(total_likes_over_all_songs, total_likes_over_all_podcasts, total_likes_over_all_stories)
            print(songflaglist)
            user_count_corresponding_to_song={}
            for song in createdsongs:
                songinteractionobj=UserSongInteraction.query.filter_by(song_id=song.id).all()
                print(song.name, songinteractionobj)
                noofuserswhoplayed = [user.user_id for user in songinteractionobj]
                print(noofuserswhoplayed)
                user_count_corresponding_to_song[song.name]=len(noofuserswhoplayed)
            
            print(user_count_corresponding_to_song)

            song_watch_time = {}

            for song in createdsongs:
                song_interaction_obj = UserSongInteraction.query.filter_by(song_id=song.id).all()
                print(song_interaction_obj , "song_interactionobj")
                total_watch_time = sum((obj.accumulated_watch_time.total_seconds() for obj in song_interaction_obj), 0)
                print(total_watch_time)
                total_watch_time_timedelta = timedelta(seconds=total_watch_time)
                total_watch_time_minutes = (total_watch_time_timedelta.total_seconds()) / 60
                # total_watch_time_hours = total_watch_time_timedelta.total_seconds() / 3600
                song_watch_time[song.name] = str(total_watch_time_minutes)
            print(song_watch_time)



            return render_template("creator/creatordashboard.html", username=username, email=email, preferredsongs=preferredsongs, albums=albums, user=user, userflag=userflag, songflaglist=songflaglist, playlists = playlists, createdsongs=createdsongs, allsongs=allsongs, liked_song_ids=liked_song_ids, currentTime=currentTime,number_of_followers=number_of_followers,following_count=following_count,total_likes_over_all_stories=total_likes_over_all_stories,total_likes_over_all_podcasts=total_likes_over_all_podcasts, total_likes_over_all_songs=total_likes_over_all_songs, total_likes_over_all_albums=total_likes_over_all_albums, total_podcast_count=total_podcast_count,total_song_count=total_song_count_by_user,total_story_count=total_story_count, total_song_count_on_platform=total_song_count_on_platform, user_count_corresponding_to_song=user_count_corresponding_to_song, song_watch_time=song_watch_time , savedsongs=favsongs)
        elif not is_subscription_valid(current_user):
            flash('You are not Authorized to be a Creator. Your Subscription Ended.', category="error")
            return redirect(url_for('auth.user'))
    else:
        return redirect(url_for("auth.loginuser"))
    

@auth.route("/logout")
@login_required
def logout():
    if current_user.is_authenticated:
        current_user.is_online=False
        db.session.commit()
        print("Client Logges Out............................................................")
        socketio.emit('update_user_status', {'user_id': current_user.id, 'is_online': False}, namespace='/')
    logout_user()
    return redirect(url_for("auth.loginuser"))
@socketio.on('connect')
def handle_connect():
    print("Client Connected............................................................")
    emit_user_status()
@socketio.on('disconnect')
def handle_disconnect():
    if current_user.is_authenticated:
        current_user.is_online=False
        db.session.commit()
        print("Client Disconnected............................................................")

        emit_user_status()



def emit_user_status():
    with current_app.app_context():
        online_users = [{'user_id': user.id, 'is_online': user.is_online} for user in User.query.all()]    
        socketio.emit('update_user_status' , {'online_users' : online_users}, namespace='/')
        print(socketio.emit('update_user_status' , {'online_users' : online_users}, namespace='/'), "EMITUSERSTATUS")
# emit_user_status()

@auth.route('/follow_artist/<int:artist_id>', methods=['POST'])
@login_required
def follow_artist(artist_id):

    user = User.query.get(current_user.id)
    artist = User.query.get(artist_id)
    print("reached")

    for followed_artist in user.followed_artists:
        print(f"- {followed_artist.id}")

    # Check if the user already follows the artist
    if artist in user.followed_artists:
        # User is following the artist, so unfollow
        user.followed_artists.remove(artist)
        print("User unfollowed the artist.")
        for artist in user.followed_artists:
            print("hello")
            print(artist)
        db.session.commit()
        
    else:
        # User is not following the artist, so follow
        user.followed_artists.append(artist)
        for artist in user.followed_artists:
            print("moto")
            print(artist)
        db.session.commit()

    return redirect(url_for("auth.profilepage", user_id=artist_id))


@auth.route('/follow_artist_creator/<int:artist_id>', methods=['POST'])
@login_required
def follow_artist_creator(artist_id):

    user = User.query.get(current_user.id)
    artist = User.query.get(artist_id)
    print("reached")

    for followed_artist in user.followed_artists:
        print(f"- {followed_artist.creator_name}")

    # Check if the user already follows the artist
    if artist in user.followed_artists:
        # User is following the artist, so unfollow
        user.followed_artists.remove(artist)
        print("User unfollowed the artist.")
        for artist in user.followed_artists:
            print("hello")
            print(artist)
        db.session.commit()
        
    else:
        # User is not following the artist, so follow
        user.followed_artists.append(artist)
        for artist in user.followed_artists:
            print("moto")
            print(artist)
        db.session.commit()

    return redirect(url_for("auth.creator"))

@auth.route('/follow_artist_creatorr/<int:artist_id>', methods=['POST'])
@login_required
def follow_artist_creatorr(artist_id):
    user = User.query.get(current_user.id)
    artist = User.query.get(artist_id)

    # Check if the user already follows the artist
    if artist in user.followed_artists:
        # User is following the artist, so unfollow
        user.followed_artists.remove(artist)
        print(f"user unfollowed {artist}")
        # for artist in user.followed_artists:
        #     print("user unfollowed")
        #     print(artist)
        db.session.commit()
        response_data = {"status": "success", "action": "unfollowed"}
    else:
        # User is not following the artist, so follow
        user.followed_artists.append(artist)
        print(f"user followed {artist}")
        # for artist in user.followed_artists:
        #     print("user followed")
        #     print(artist)
        db.session.commit()
        response_data = {"status": "success", "action": "followed"}

    return jsonify(response_data)

# @auth.route("/creator/dashboard/upload-songs", methods=["GET", "POST"])
# @login_required
# def uploadsong():
#     if request.method=="GET":
        
#         return render_template("creator/uploadsong.html")
    

#     if request.method == 'POST':
#             email=session["user-email"]
#             print(email)
#             current_user= User.query.filter_by(email=email).first()
#             name = request.form['name']
#             artist = request.form['artist']
#             duration = request.form['duration']
#             lyrics = request.form['lyrics']
#             # genre= request.form['genre']
#             selected_genres = request.form.get('selectedGenres')
#             print(selected_genres)
#             print(current_user)

#             # Handle file uploads
#             song_file = request.files['file']
#             cover_image = request.files['cover_image']

#             if song_file and cover_image:
#                 # Save the uploaded song file and cover image to directories
#                 # song_file.save('uploads/' + song_file.filename)
#                 # cover_image.save('covers/' + cover_image.filename)
#                 song_file_path = os.path.join(current_app.config["UPLOADS_MUSIC_DEST"],secure_filename(song_file.filename))
#                 cover_image_path = os.path.join(current_app.config["UPLOADS_IMAGES_DEST"],secure_filename(cover_image.filename))
                
#                 print(song_file_path, cover_image_path)

#                 song_file.save(song_file_path)
#                 # print(song_file.save(song_file_path))
#                 cover_image.save(cover_image_path)

#                 # Create a new Song object and add it to the database

#                 song_file_path=song_file_path.replace('\\', '/')
#                 cover_image_path=cover_image_path.replace('\\', '/')
#                 print(song_file_path, cover_image_path)
#                 print(cover_image_path.split('/website')[1])

#                 # song_data = song_file.read()
#                 # cover_image_data = cover_image.read()
#                 new_song = Song(
#                     name=name,
#                     artist=artist,
#                     duration=duration,
#                     lyrics=lyrics,
#                     song_file_path=song_file_path,
#                     cover_image_path=cover_image_path,
#                     creator_id= current_user.id,
#                     genre=selected_genres,
#                     likes=0,
#                     category="song",
#                 )
#                 db.session.add(new_song)
#                 db.session.commit()

#                 flash('Song uploaded successfully!', category='success')
#                 return redirect(url_for('auth.uploadsong'))

#             elif not song_file or not cover_image:
#                 flash('Please provide both a song file and a cover image.', category='error')
#                 return redirect(url_for('auth.uploadsong'))
            

####################################################
# api for song operations...
@auth.route('/creator_dashboard/songs/upload', methods=['GET'])
@login_required
def uploadsongview():
    return render_template("creator/uploadsong.html")

@auth.route('/api/songs/upload', methods=['POST'])
def upload_song():
    # data = request.form
    if request.method == 'POST':
            email=session["user-email"]
            print(email)
            current_user= User.query.filter_by(email=email).first()
            name = request.form['name']
            artist = request.form['artist']
            duration = request.form['duration']
            lyrics = request.form['lyrics']
            # genre= request.form['genre']
            selected_genres = request.form.get('selectedGenres')
            print(selected_genres)
            print(current_user)

            # Handle file uploads
            song_file = request.files['file']
            cover_image = request.files['cover_image']

            if song_file and cover_image:
                # Save the uploaded song file and cover image to directories
                # song_file.save('uploads/' + song_file.filename)
                # cover_image.save('covers/' + cover_image.filename)
                song_file_path = os.path.join(current_app.config["UPLOADS_MUSIC_DEST"],secure_filename(song_file.filename))
                cover_image_path = os.path.join(current_app.config["UPLOADS_IMAGES_DEST"],secure_filename(cover_image.filename))
                
                print(song_file_path, cover_image_path)

                song_file.save(song_file_path)
                # print(song_file.save(song_file_path))
                cover_image.save(cover_image_path)

                # Create a new Song object and add it to the database

                song_file_path=song_file_path.replace('\\', '/')
                # all_songs=Song.query.all()
                created_songs = Song.query.filter_by(creator_id=current_user.id).all()
                if song_file_path in (existing_song.song_file_path for existing_song in created_songs) or ( name in [songs.name for songs in created_songs]):
                    print("song exists")
                    # flash("This song already exists", category='error')
                    return jsonify({"message": "Song Exists"})
                else:


                    cover_image_path=cover_image_path.replace('\\', '/')
                    print(song_file_path, cover_image_path)
                    print(cover_image_path.split('/website')[1])

                    # song_data = song_file.read()
                    # cover_image_data = cover_image.read()
                    new_song = Song(
                        name=name,
                        artist=artist,
                        duration=duration,
                        lyrics=lyrics,
                        song_file_path=song_file_path,
                        cover_image_path=cover_image_path,
                        creator_id= current_user.id,
                        genre=selected_genres,
                        likes=0,
                        category="song",
                    )
                    try:
                        db.session.add(new_song)
                        db.session.commit()
                        return jsonify({"message": "Successfull"})
                    except Exception as e:
                        db.session.rollback()
                        return jsonify({"message": "Unsuccessful"})
            
    return jsonify({"message": "Method Not Allowed"})

from flask import jsonify
from .models import SongComment
@auth.route('/post_comment/<int:song_id>', methods=['POST'])
@login_required

def post_comment(song_id):
    if request.method == 'POST':
        comment_text = request.form.get('comment')
        if comment_text:
            new_comment = SongComment(user_id=current_user.id, song_id=song_id, comment=comment_text)
            db.session.add(new_comment)
            db.session.commit()
            # Optionally, you can return the newly posted comment as JSON
            return jsonify({
                'success': True,
                'comment': {
                    'user_name': current_user.user_name,
                    'timestamp': new_comment.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                    'comment': new_comment.comment
                }
            })
    # If comment posting fails or the request is not a POST request
    return jsonify({'success': False}), 400


@auth.route("/creator/dashboard/uploadpodcast", methods=["GET", "POST"])
@login_required
def createpodcasts():
    if request.method == 'GET':
        return render_template('creator/uploadpodcast.html')
    if request.method == "POST":
        email=session["user-email"]
        print(email)
        current_user= User.query.filter_by(email=email).first()
        name = request.form['name']
        artist = request.form['artist']
        duration = request.form['duration']
        transcript = request.form['lyrics']
        genre= request.form['genre']
        print(current_user)

        podcast_file = request.files['file']
        cover_image = request.files['cover_image']

        if podcast_file and cover_image:
            # Save the uploaded song file and cover image to directories
            # song_file.save('uploads/' + song_file.filename)
            # cover_image.save('covers/' + cover_image.filename)
            podcast_file_path = os.path.join(current_app.config["UPLOADS_MUSIC_DEST"],secure_filename(podcast_file.filename))
            cover_image_path = os.path.join(current_app.config["UPLOADS_IMAGES_DEST"],secure_filename(cover_image.filename))
            
            print(podcast_file_path, cover_image_path)

            podcast_file.save(song_file_path)
            # print(song_file.save(song_file_path))
            cover_image.save(cover_image_path)

            # Create a new Song object and add it to the database

            song_file_path=song_file_path.replace('\\', '/')
            cover_image_path=cover_image_path.replace('\\', '/')
            print(song_file_path, cover_image_path)
            print(cover_image_path.split('/website')[1])

            # song_data = song_file.read()
            # cover_image_data = cover_image.read()
            new_podcast = Song(
                name=name,
                artist=artist,
                duration=duration,
                lyrics=transcript,
                song_file_path=podcast_file_path,
                cover_image_path=cover_image_path,
                creator_id= current_user.id,
                genre=genre,
                likes=0,
                category="podcast",
            )
            db.session.add(new_podcast)
            db.session.commit()

            flash('Podcast uploaded successfully!', category='success')
            return redirect(url_for('auth.createpodcasts'))

        elif not podcast_file or not cover_image:
            flash('Please provide both a podcast file and a cover image.', category='error')
            return redirect(url_for('auth.createpodcasts')) 




from operator import attrgetter

@auth.route('/discover-songs', methods=["GET","POST"])
@cache.cached(timeout=300)
@login_required
def discoversongs():
    user = User.query.filter_by(id=current_user.id).first()
    if request.method=="GET":
        songs=Song().query.all()
        # songs=Song.query.join(User).all()
        albums= Album().query.all()
        # for song in songs:
            # print(song.song_file_path)
        songs.sort(key=lambda song: song.likes, reverse=True)
        albums.sort(key=lambda album: album.like, reverse=True)

                # Sort songs in descending order of likes
        # sorted_songs = sorted(songs, key=attrgetter('likes'), reverse=True)

        # # Sort albums in descending order of likes
        # sorted_albums = sorted(albums, key=attrgetter('like'), reverse=True)
        return render_template("contentdashboard/discoversongs.html", songs=songs, albums=albums, user=user)
    
    if request.method=="POST":
        albums= Album().query.all()
        # if albums:
        #     print([album.creator.creator_name for album in albums])
        search_query= request.form.get("search-query")
        songs= Song.query.filter(or_(
            Song.genre.ilike(f"%{search_query}%"),
            Song.name.ilike(f"%{search_query}%"),
            Song.artist.ilike(f"%{search_query}%"),
            # Song.creator.ilike(f"%{search_query}%")
        )).all()
        albums= Album.query.filter(or_(
            Album.genre.ilike(f"%{search_query}%"),
            Album.name.ilike(f"%{search_query}%"),
            Album.creator_album.ilike(f"%{search_query}%"),
        )).all()

        songs.sort(key=lambda song: song.likes, reverse=True)
        albums.sort(key=lambda album: album.like, reverse=True)
        
        # user=User.query.filter_by(id=current_user.id).first()
        # if not user.is_creator:
        #     return render_template("user/userdashboard.html", songs=songs , username=user.user_name)

        return render_template("contentdashboard/discoversongs.html", songs=songs,albums=albums, user=user)
    


# @auth.route('/like-song/<int:song_id>', methods=["POST"])
# @login_required
# def like_song(song_id):
#     if request.method == "POST":
#         song = Song.query.get(song_id)
#         if song:
#             # Check if the user has already liked the song
#             user_like = UserLike.query.filter_by(user_id=current_user.id, song_id=song.id).first()
#             if user_like:
#                 db.session.delete(user_like)
#                 song.likes -= 1  # Decrement like count when unliking
#             else:
#                 new_user_like = UserLike(user_id=current_user.id, song_id=song.id)
#                 db.session.add(new_user_like)
#                 song.likes += 1  # Increment like count when liking
            
#             db.session.commit()
#             return redirect(url_for('auth.discoversongs'))
        
@auth.route('/like-song/<int:song_id>', methods=["POST"])
@login_required
def like_song(song_id):
    if request.method == "POST":
        song = Song.query.get(song_id)
        if song:
            user_like = UserLike.query.filter_by(user_id=current_user.id, song_id=song.id).first()
            if user_like:
                db.session.delete(user_like)
                print(f"user unliked song {song_id}")
                status="disliked"
                song.likes -= 1
            else:
                new_user_like = UserLike(user_id=current_user.id, song_id=song.id)
                db.session.add(new_user_like)
                status="liked"
                print(f"user liked song {song_id}")
                song.likes += 1

            db.session.commit()
            return jsonify({'likes': song.likes,  "status" : status})
        

@auth.route('/like_song_user/<int:song_id>', methods=["POST"])
@login_required
def like_song_user(song_id):
    if request.method == "POST":
        song = Song.query.get(song_id)
        if song:
            user_like = UserLike.query.filter_by(user_id=current_user.id, song_id=song.id).first()
            if user_like:
                db.session.delete(user_like)
                song.likes -= 1
            else:
                new_user_like = UserLike(user_id=current_user.id, song_id=song.id)
                db.session.add(new_user_like)
                song.likes += 1
            
            db.session.commit()
            return redirect(url_for('auth.user'))
        

# @auth.route('/like_song_creator/<int:song_id>', methods=["POST"])
# @login_required
# def like_song_creator(song_id):
#     if request.method == "POST":
#         song = Song.query.get(song_id)
#         if song:
#             user_like = UserLike.query.filter_by(user_id=current_user.id, song_id=song.id).first()
#             if user_like:
#                 db.session.delete(user_like)
#                 song.likes -= 1
#             else:
#                 new_user_like = UserLike(user_id=current_user.id, song_id=song.id)
#                 db.session.add(new_user_like)
#                 song.likes += 1
            
#             db.session.commit()
#             return redirect(url_for('auth.creator'))
        


@auth.route('/like_song_creator/<int:song_id>', methods=["POST"])
@login_required
def like_song_creator(song_id):
    if request.method == "POST":
        song = Song.query.get(song_id)
        if song:
            user_like = UserLike.query.filter_by(user_id=current_user.id, song_id=song.id).first()
            if user_like:
                db.session.delete(user_like)
                print(f"user unliked song {song_id}")
                status="disliked"
                song.likes -= 1
            else:
                new_user_like = UserLike(user_id=current_user.id, song_id=song.id)
                db.session.add(new_user_like)
                status="liked"
                print(f"user liked song {song_id}")
                song.likes += 1

            db.session.commit()
            return jsonify({'likes': song.likes,  "status" : status})



# @auth.route('/like_song_user_page/<int:song_id>', methods=["POST"])
# @login_required
# def like_song_user_page(song_id):
#     if request.method == "POST":
#         song = Song.query.get(song_id)
#         if song:
#             user_like = UserLike.query.filter_by(user_id=current_user.id, song_id=song.id).first()
#             if user_like:
#                 db.session.delete(user_like)
#                 if song.likes!=0:
#                     song.likes -= 1
#             else:
#                 new_user_like = UserLike(user_id=current_user.id, song_id=song.id)
#                 db.session.add(new_user_like)
#                 song.likes += 1
            
#             db.session.commit()
#             return redirect(url_for('auth.fullscreen_view' , song_id=song_id))
        
@auth.route('/like_song_user_page/<int:song_id>', methods=["POST"])
@login_required
def like_song_user_page(song_id):
    if request.method == "POST":
        song = Song.query.get(song_id)
        if song:
            user_like = UserLike.query.filter_by(user_id=current_user.id, song_id=song.id).first()
            if user_like:
                db.session.delete(user_like)
                status="disliked"
                if song.likes!=0:
                    song.likes -= 1
            else:
                new_user_like = UserLike(user_id=current_user.id, song_id=song.id)
                db.session.add(new_user_like)
                status="liked"
                song.likes += 1
            
            db.session.commit()
            return jsonify({'likes': song.likes ,  'status' : status})

        

@auth.route('/like_song_in_album/<int:song_id>/album/<int:album_id>', methods=["POST"])
@login_required
def like_song_in_album(song_id, album_id):
    if request.method == "POST":
        song = Song.query.get(song_id)
        all_songs=Song.query.all()
        album=Album.query.filter_by(id=album_id).first()
        songs=[song for song in all_songs if song in album.songs]
        user = User.query.filter_by(id=current_user.id).first()
        if song:
            # Check if the user has already liked the song
            user_like = UserLike.query.filter_by(user_id=current_user.id, song_id=song.id).first()
            if user_like:
                db.session.delete(user_like)
                song.likes -= 1  # Decrement like count when unliking
            else:
                new_user_like = UserLike(user_id=current_user.id, song_id=song.id)
                db.session.add(new_user_like)
                song.likes += 1  # Increment like count when liking

                
                
            
            db.session.commit()
        return render_template('user/album_songs.html', songs=songs, user=user, album_id=album_id)


            
# @auth.route('/like-album/<int:album_id>', methods=["POST"])
# @login_required  # Make sure the user is authenticated
# def like_album(album_id):
#     if request.method == "POST":
#         album = Album.query.get(album_id)  # Retrieve the album by its ID
#         if album:
#             user_like = UserLikeAlbum.query.filter_by(user_id=current_user.id, album_id=album.id).first()
#             if user_like:
#                 db.session.delete(user_like)
#             else:
#                 new_user_like = UserLikeAlbum(user_id=current_user.id, album_id=album.id)
#                 db.session.add(new_user_like)

#             db.session.commit()
#             return redirect(url_for('auth.discoversongs'))
        
# @auth.route('/like_album_user/<int:album_id>', methods=["POST"])
# @login_required  # Make sure the user is authenticated
# def like_album_user(album_id):
#     if request.method == "POST":
#         album = Album.query.get(album_id)  # Retrieve the album by its ID
#         if album:
#             user_like = UserLikeAlbum.query.filter_by(user_id=current_user.id, album_id=album.id).first()
#             if user_like:
#                 album.like-=1
#                 print(album.like)
#                 db.session.delete(user_like)
#             else:
#                 new_user_like = UserLikeAlbum(user_id=current_user.id, album_id=album.id)
#                 album.like+=1
#                 print(album.like)
#                 db.session.add(new_user_like)

#             db.session.commit()
#             return redirect(url_for('auth.discoversongs'))

@auth.route('/like_album_user/<int:album_id>', methods=["POST"])
@login_required
def like_album_user(album_id):
    if request.method == "POST":
        album = Album.query.get(album_id)
        if album:
            user_like = UserLikeAlbum.query.filter_by(user_id=current_user.id, album_id=album.id).first()
            if user_like:
                album.like-=1
                print(album.like)
                status="disliked"
                db.session.delete(user_like)
            else:
                new_user_like = UserLikeAlbum(user_id=current_user.id, album_id=album.id)
                album.like+=1
                status="liked"
                print(album.like)
                db.session.add(new_user_like)

            db.session.commit()
            return jsonify({'likes': album.like,  "status" : status})
        


@auth.route("/creator/dashboard/delete-song/<int:song_id>", methods=["POST"])
@login_required
def delete_song(song_id):
    song = Song.query.get(song_id)
    if song:
        # Check if the currently logged-in user is the creator of the song
        if current_user.id == song.creator_id:
            # Delete the song from the database
            try:
                userlikes = UserLike.query.filter_by(song_id=song_id).all()
                print(userlikes)
                if userlikes:
                    for userlike in userlikes:
                        print(userlike)
                        db.session.delete(userlike)

                db.session.delete(song)
                db.session.commit()
                # flash('Song deleted successfully!', category='success')
                return jsonify({'message' : 'Successfull'})

            except Exception as e:
                db.session.rollback()
                flash('An error occurred while deleting the song.', category='error')
                return jsonify({'message' : 'Unsuccessfull'})
        else:
            flash('You can only delete songs that you created.', category='error')
    else:
        flash('Song not found!', category='error')
        return jsonify({'message' : 'Unsuccessfull', 'error_type': "Song Not Found"})
    return jsonify({'message' : 'Successfull'})


# @auth.route('/creator/dashboard/edit-song/<int:song_id>', methods=["GET", "POST"])
# @login_required
# def edit_song(song_id):
#     # Get the song from the database
#     song = Song.query.get(song_id)

#     # if not song:
#     #     flash('Song not found', category='error')
#     #     return redirect(url_for('auth.'))  # Redirect to your dashboard route

#     if request.method == "POST":
#         # Update the song attributes based on the form data
#         song.name = request.form.get('name')
#         song.artist = request.form.get('artist')
#         song.duration = request.form.get('duration')
#         song.lyrics = request.form.get('lyrics')
#         song.genre = request.form.get('selectedGenres')
#         cover_image = request.files['cover_image']

#         if cover_image:
#             # Save the uploaded song file and cover image to directories
#             # song_file.save('uploads/' + song_file.filename)
#             # cover_image.save('covers/' + cover_image.filename)
#             # song_file_path = os.path.join(current_app.config["UPLOADS_MUSIC_DEST"],secure_filename(song_file.filename))
#             cover_image_path = os.path.join(current_app.config["UPLOADS_IMAGES_DEST"],secure_filename(cover_image.filename))
            
#             # print(song_file_path, cover_image_path)

#             # song_file.save(song_file_path)
#             # print(song_file.save(song_file_path))
#             cover_image.save(cover_image_path)

#             # Create a new Song object and add it to the database

#             # song_file_path=song_file_path.replace('\\', '/')
#             cover_image_path=cover_image_path.replace('\\', '/')
#             print(cover_image_path)
#             print(cover_image_path.split('/website')[1])
#             song.cover_image_path=cover_image_path

#         # Commit the changes to the database
#         db.session.commit()

#         flash('Song updated successfully', category='success')
#         return redirect(url_for('auth.creator'))  # Redirect to your dashboard route

#     # Render the edit song template with the song data
#     return render_template("creator/uploadsong.html", song=song)

@auth.route('/creator_dashboard/song/edit/<int:song_id>', methods=['GET'])
@login_required
def editsongview(song_id):
    song = Song.query.get(song_id)
    return render_template("creator/uploadsong.html", song=song)

@auth.route('/api/songs/edit/<int:song_id>', methods=['PUT'])
@login_required
def edit_song(song_id):
    # data = request.form
    if request.method == 'PUT':
        email=session["user-email"]
        print(email)
        song = Song.query.get(song_id)
        current_user= User.query.filter_by(email=email).first()
        song.name = request.form.get('name')
        song.artist = request.form.get('artist')
        song.duration = request.form.get('duration')
        song.lyrics = request.form.get('lyrics')
        song.genre = request.form.get('selectedGenres')
        cover_image = request.files['cover_image']

        if cover_image:
            # Save the uploaded song file and cover image to directories
            # song_file.save('uploads/' + song_file.filename)
            # cover_image.save('covers/' + cover_image.filename)
            # song_file_path = os.path.join(current_app.config["UPLOADS_MUSIC_DEST"],secure_filename(song_file.filename))
            cover_image_path = os.path.join(current_app.config["UPLOADS_IMAGES_DEST"],secure_filename(cover_image.filename))
            
            # print(song_file_path, cover_image_path)

            # song_file.save(song_file_path)
            # print(song_file.save(song_file_path))
            cover_image.save(cover_image_path)

            # Create a new Song object and add it to the database

            # song_file_path=song_file_path.replace('\\', '/')
            cover_image_path=cover_image_path.replace('\\', '/')
            print(cover_image_path)
            print(cover_image_path.split('/website')[1])
            song.cover_image_path=cover_image_path

        try:
            db.session.commit()
            return jsonify({"message": "Successful"})
        except Exception as e:
            db.session.rollback()
            return jsonify({"message": "Unsuccessful"})
    return jsonify({"message": "Method Not Allowed"})



@auth.route('/creator/dashboard/create-albums',methods=["GET","POST"])
@login_required
def createalbum():
    if request.method=="GET":
        songs=Song.query.filter_by(creator_id=current_user.id).all()
        album= Album.query.filter_by(artist_id=current_user.id).all()
        
        return render_template("creator/createalbum.html", songs=songs, album=album)
    if request.method == "POST":
        # Get album details from the form
        album_name = request.form.get('album_name')
        album_genre = request.form.get('selectedGenres')
        album_cover = request.files['album_cover']  # Assuming you have a file input with the name 'album_cover'
        selected_songs = request.form.getlist('selected_songs')  # Assuming 'selected_songs' is a list of selected song IDs

        # Perform album creation and data validation
        if not album_name or not album_genre or not album_cover or not selected_songs:
            flash('Please fill in all album details', category='error')
            return redirect(url_for("auth.createalbum"))
        

        cover_image_path = os.path.join(current_app.config["UPLOADS_IMAGES_DEST"],secure_filename(album_cover.filename))
        album_cover.save(cover_image_path)
        cover_image_path=cover_image_path.replace('\\', '/')

        
        # Create a new album record in the database
        new_album = Album(
            name=album_name,
            genre=album_genre,
            cover_image=cover_image_path,
            artist_id=current_user.id,
        )

        # Add selected songs to the album (you need to define this relationship in your models)
        for song_id in selected_songs:
            song = Song.query.get(song_id)
            if song:
                new_album.songs.append(song)

        db.session.add(new_album)
        db.session.commit()
        
        flash('Album created successfully', category='success')
        return redirect(url_for("auth.createalbum"))



@auth.route('/albums/<int:album_id>/songs', methods=['GET'])
@login_required
def album_songs(album_id):
    # Retrieve the album and its songs based on the album_id
    album = Album.query.get(album_id)
    user = User.query.filter_by(id=current_user.id).first()

    if album:
        songs = album.songs  # Assuming you have a relationship between Album and Song
        return render_template('user/album_songs.html', album=album, songs=songs, user=user, album_id=album_id)
    else:
        flash('Album not found', category='error')
        return redirect(url_for('auth.discoversongs'))  # Redirect to a suitable page if the album is not found
    

@auth.route('/albums/<int:album_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_album(album_id):
    # Retrieve the album from the database
    album = Album.query.get(int(album_id))
    songs = album.songs

    if request.method == 'POST':
        updated_name = request.form.get('album_name')
        album_cover = request.files['album_cover']
        updated_genre = request.form.get('selectedGenres')
        cover_image_path = os.path.join(current_app.config["UPLOADS_IMAGES_DEST"],secure_filename(album_cover.filename))
        album_cover.save(cover_image_path)
        cover_image_path=cover_image_path.replace('\\', '/')

        # Update album properties
        album.name = updated_name
        album.genre = updated_genre
        album.cover_image=cover_image_path

        # Commit changes to the database
        db.session.commit()

        # Flash a success message
        flash('Album updated successfully', category='success')

        # Redirect to the album display page
        return redirect(url_for('auth.creator'))
    return render_template('creator/createalbum.html', album=album, songs=songs)



@auth.route('/albums/<int:album_id>/delete', methods=["POST"])
@login_required
def delete_album(album_id):
    album = Album.query.get(int(album_id))

    if album and current_user.id==album.artist_id:
        userlikes = UserLikeAlbum.query.filter_by(album_id=album.id).all()
        print(userlikes)
        if userlikes:
            for userlike in userlikes:
                print(userlike)
                db.session.delete(userlike)
        db.session.delete(album)
        db.session.commit()

        flash('Album deleted successfully', 'success')
    else:
        flash('Album not found', 'error')

    return redirect(url_for('auth.creator'))



@auth.route('user/dashboard/create-playlist', methods=['GET','POST'])
@login_required
def createplaylist():
    if request.method=="GET":
        return render_template('user/createplaylist.html')
    
    
    if request.method=="POST":
        
            playlist_name = request.form.get('playlist_name')

            playlist = Playlist(name=playlist_name, user_id=current_user.id)
            db.session.add(playlist)
            db.session.commit()

            flash('Playlist created successfully', category='success')
            if current_user.is_creator:
                    return redirect(url_for('auth.creator'))
            else:
                return redirect(url_for('auth.user'))

    # Redirect back to the user dashboard
    if current_user.is_creator:
        return redirect(url_for('auth.creator'))
    else:
        return redirect(url_for('auth.user'))

@auth.route('user/dashboard/create-playlist2', methods=['GET', 'POST'])
@login_required
def createplaylist2():
    if request.method == "POST":
        playlist_name = request.form.get('playlist_name')

        playlist = Playlist(name=playlist_name, user_id=current_user.id)
        db.session.add(playlist)
        db.session.commit()

        flash('Playlist created successfully', category='success')

        # Get the created playlist data
        playlist_data = {
            'id': playlist.id,
            'name': playlist.name,
            'songs': [song for song in playlist.songs]  # You may need to populate this based on your data model
        }
        playlists=Playlist.query.filter_by(user_id=current_user.id)

        return jsonify({'success': True, 'playlist': playlist_data , 'html': render_template('creator/addtoplaylist.html' , playlists=playlists)})
    
@auth.route('user/dashboard/addtoplaylist/<int:song_id>', methods=['POST'])
@login_required
def addtoplaylist(song_id):
    song=Song.query.get(song_id)
    if song:
        if request.method=="POST":
            playlist_id = request.form.get('playlist_id')
            playlist = Playlist.query.get(playlist_id)

            if playlist and playlist.user_id==current_user.id:
                playlist.songs.append(song)
                db.session.commit()
                flash('Song added to the playlist successfully', category='success')
            else:
                flash('You need to create a playlist', category='error')


    return redirect(url_for('auth.discoversongs'))

@auth.route('user/dashboard/addtoplaylistuserpage/<int:song_id>', methods=['POST'])
@login_required
def addtoplaylistuserpage(song_id):
    song=Song.query.get(song_id)
    if song:
        if request.method=="POST":
            playlist_id = request.form.get('playlist_id')
            playlist = Playlist.query.get(playlist_id)

            if playlist and playlist.user_id==current_user.id:
                playlist.songs.append(song)
                db.session.commit()
                flash('Song added to the playlist successfully', category='success')
            else:
                flash('You need to create a playlist', category='error')


    return redirect(url_for('auth.user'))

# @auth.route('user/dashboard/addtoplaylistcreatorpage/<int:song_id>', methods=['POST'])
# @login_required
# def addtoplaylistcreatorpage(song_id):
#     song=Song.query.get(song_id)
#     if song:
#         if request.method=="POST":
#             playlist_id = request.form.get('playlist_id')
#             playlist = Playlist.query.get(playlist_id)

#             if playlist and playlist.user_id==current_user.id:
#                 playlist.songs.append(song)
#                 db.session.commit()
#                 flash('Song added to the playlist successfully', category='success')
#             else:
#                 flash('You need to create a playlist', category='error')


#     return redirect(url_for('auth.creator'))

@auth.route('user/dashboard/addtoplaylistcreatorpage/<int:song_id>', methods=['POST'])
@login_required
def addtoplaylistcreatorpage(song_id):
    song=Song.query.get(song_id)
    if song:
        if request.method=="POST":
            playlist_id = request.form.get('playlist_id')
            print(playlist_id, song_id)
            playlist = Playlist.query.get(playlist_id)
            songs_in_playlist=[song.name for song in playlist.songs]

            if playlist and playlist.user_id==current_user.id:
                if song not in playlist.songs:
                    playlist.songs.append(song)
                    db.session.commit()
                    status="success"
                    flash('Song added to the playlist successfully', category='success')
                elif song in playlist.songs:
                    status="already added"
            else:
                flash('You need to create a playlist', category='error')
                status="failure"

            print(status, song.name, songs_in_playlist)
        
        return jsonify({"status":status})




#adding to playlist from fullpage
@auth.route('user/dashboard/addtoplaylistsongpage/<int:song_id>', methods=['POST'])
@login_required
def addtoplaylistsongpage(song_id):
    song=Song.query.get(song_id)
    if song:
        if request.method=="POST":
            playlist_id = request.form.get('playlist_id')
            playlist = Playlist.query.get(playlist_id)

            if playlist and playlist.user_id==current_user.id:
                if song not in playlist.songs:
                    playlist.songs.append(song)
                    db.session.commit()
                    status="success"
                    flash('Song added to the playlist successfully', category='success')
                elif song in playlist.songs:
                    status="already added"
            else:
                flash('You need to create a playlist', category='error')
                status="failure"

            print(status)
        return jsonify({"status":status})


@auth.route('/delete_playlist/<int:playlist_id>', methods=['POST'])
@login_required
def delete_playlist(playlist_id):
    playlist = Playlist.query.get(playlist_id)

    if playlist:
        # Check if the current user owns the playlist
        if playlist.user_id == current_user.id:
            db.session.delete(playlist)
            db.session.commit()
            flash('Playlist deleted successfully', category='success')
        else:
            flash('You do not have permission to delete this playlist', category='error')
    else:
        flash('Playlist not found', category='error')

    # Redirect back to the user dashboard
    return redirect(url_for('auth.user'))



from flask import jsonify

@auth.route('/delete_playlist2/<int:playlist_id>', methods=['POST'])
@login_required
def delete_playlist2(playlist_id):
    playlist = Playlist.query.get(playlist_id)

    if playlist:
        # Check if the current user owns the playlist
        if playlist.user_id == current_user.id:
            db.session.delete(playlist)
            db.session.commit()
            flash('Playlist deleted successfully', category='success')
            return jsonify({"success": True})
        else:
            flash('You do not have permission to delete this playlist', category='error')
            return jsonify({"success": False, "message": "Permission denied"})
    else:
        flash('Playlist not found', category='error')
        return jsonify({"success": False, "message": "Playlist not found"})




@auth.route('/creator/uploaddetails', methods=["GET", "POST"])
@login_required
def uploaddetails():
    if request.method=="GET":

        user= User.query.filter_by(id=current_user.id).first()
        if user.is_creator:
            return render_template("creator/uploaddetails.html", user=user)
        

    if request.method=="POST":
        user= User.query.filter_by(id=current_user.id).first()
        profile_picture = request.files['profilepicture']
        creator_name = request.form.get('creatorName')
        description = request.form.get('description')
        dob = request.form.get('dob')
        dob = datetime.strptime(dob, '%Y-%m-%d').date()
        #strptime takes in date string and converts to datetime object while 
        #strftime formats given datetime object to string.
        

        contact_info = str(request.form.get('contactinfo'))
        social_media_platform = request.form.get('platformSelect')
        social_media_liinks = request.form.get('socialmedia')
        if user:
            print(user)

            profile_picture_path = os.path.join(current_app.config["UPLOADS_IMAGES_DEST"], secure_filename(profile_picture.filename))

            profile_picture.save(profile_picture_path)

            profile_picture_path=profile_picture_path.replace('\\', '/')

            user.profile_image_path=profile_picture_path
            user.creator_name=creator_name
            user.description=description
            user.dob=dob
            user.contact_info=contact_info
            user.social_media_links=social_media_platform+":"+social_media_liinks

            db.session.commit()
            flash('Profile details updated succesfully!',category="success")
            return redirect(url_for('auth.creator'))
        else:
            flash('Error updating your profile! Please try again.',category="error")
            return redirect(url_for('auth.uploaddetails'))


@auth.route('/creator/profilepage/<int:user_id>', methods=["GET", "POST"])
@login_required
def profilepage(user_id):
    if request.method=="GET":
        user=User.query.get(user_id)
        songs=Song.query.filter_by(creator_id=user_id).all()
        # print(songs)
        total_creations=len((songs))
        # print(total_creations)
        following_count=len(list(user.followed_artists))
        followers_count = len(list(user.followers))
        admin=Administratormushify.query.all()
        socketio.emit('update_user_status', {'user_id': user.id, 'is_online': user.is_online}, namespace='/https://e95c-2405-201-8013-881f-8941-6f9f-e6d5-1a2c.ngrok-free.app/')
        print(socketio.emit('update_user_status', {'user_id': user.id, 'is_online': user.is_online}, namespace='/')
)
        print(current_user.email in admin)
        print(current_user, admin)
        # print(admin.user_name)

        if user.dob==None:
            month=None
        else:
            month=calendar.month_name[int(user.dob.month)]
        print(user.is_authenticated , "user")

        return render_template('creator/creatorprofile.html',admin=admin, user=user, month=month, following_count=following_count, followers_count=followers_count, total_creations=total_creations, songs=songs)

@auth.route('/user/discovercreators', methods=["GET", "POST"])
@login_required
def discover_creators():
    if request.method=="GET":
        creators = User.query.filter_by(is_creator=True).limit(3).all()
        creators.sort(key=lambda creator: len(list(creator.followers)) , reverse=True)
        print(creators)
        print(type(creators))
        return render_template('contentdashboard/discovercreators.html', creators=creators)



@auth.route('/search-creators',methods=["POST"])
@login_required
def searchcreators():
    if request.method=="POST":
        search_query = request.form.get('search-query', '')
        search_criteria = request.form.get('search-criteria')
        if search_criteria == 'creator_name':
            creators = User.query.filter(or_ (User.creator_name.ilike(f'%{search_query}%'),)).all()
            print("hello")
        elif search_criteria == 'email':
            creators = User.query.filter(or_(User.email.ilike(f'%{search_query}%'),)).all()
            print("hello1")
        else:
            creators=User.query.filter(and_(or_(User.email.ilike(f'%{search_query}%'), User.creator_name.ilike(f'%{search_query}%'))), User.is_creator==True).all()
            print("hello2")

        return render_template('contentdashboard/discovercreators.html', creators=creators)
    
@auth.route('/search-creatorsindashboard',methods=["POST"])
@login_required
def searchcreators2():
    if request.method=="POST":
        search_query = request.form.get('search-query', '')
        search_criteria = request.form.get('search-criteria', 'creator_name')
        if search_criteria == 'creator_name':
            creators = User.query.filter(or_ (User.creator_name.ilike(f'%{search_query}%'),
                                         
                                         )).all()
            print("hello")
        elif search_criteria == 'email':
            creators = User.query.filter(User.email.ilike(f'%{search_query}%')).all()
            print("hello1")
        else:
            creators=User.query.filter_by(is_creator=True).all()
            print("hello2")
        return render_template('creator/creatordashboard.html', user=creators)
    
from .models import UserFavoriteSong
@auth.route('/fullscreen-view/<int:song_id>')
@login_required
def fullscreen_view(song_id):
    song = Song.query.get(song_id)
    if Song.query.get(song_id+1):
        next_song=song_id+1
    else:
        next_song=song_id
    user = User.query.get(current_user.id)
    userfavsong = UserFavoriteSong.query.filter_by(song_id=song_id,user_id=current_user.id).first()
    if userfavsong:
        status="present"
    else:
        status="absent"
    return render_template('contentdashboard/songfullscreen.html', song=song, user=user , status=status, next_song=next_song)

           
        
@auth.route('/update_song_interaction', methods=['POST'])
@login_required
def update_song_interaction():
    data = request.get_json()
    user_id = data.get('userId')
    song_id = data.get('songId')
    timestamp_type = data.get('type')
    timestamp = datetime.fromisoformat(data.get('timestamp'))
    user = User.query.get(user_id)
    song = Song.query.get(song_id)
    if user is None or song is None:
        return jsonify({'status': 'error', 'message': 'User or song not found'})
    interaction = UserSongInteraction.query.filter_by(user_id=user_id, song_id=song_id).first()

    if timestamp_type == 'start':
        if interaction is None:
            interaction = UserSongInteraction(user_id=user_id, song_id=song_id, start_time=timestamp)
            db.session.add(interaction)
        else:
            interaction.start_time = timestamp
            print("added starting timestamp")
    elif timestamp_type == 'end':
        if interaction is not None:
            interaction.end_time = timestamp
            print("added ending timestamp")
            if interaction.start_time.tzinfo is None:
                interaction.start_time = interaction.start_time.replace(tzinfo=timezone.utc)
            
            # Ensure interaction.end_time is offset-aware
            if interaction.end_time.tzinfo is None:
                interaction.end_time = interaction.end_time.replace(tzinfo=timezone.utc)

            if interaction.accumulated_watch_time is None:
                interaction.accumulated_watch_time = timedelta(0)

            watch_time_interval = interaction.end_time - interaction.start_time
            print(watch_time_interval)

            interaction.accumulated_watch_time += watch_time_interval
    db.session.commit()

    return jsonify({'status': 'success', 'message': f'Timestamp updated ({timestamp_type}): {timestamp}'})


from .models import UserFavoriteSong
@auth.route('/addtofav/<int:song_id>', methods=['POST'])
@login_required
def addtofav(song_id):
    # song = Song.query.get(song_id)
    # user = User.query.get(current_user.id)
    favorite_song = UserFavoriteSong.query.filter_by(song_id=song_id,user_id=current_user.id).first()
    if favorite_song:
        try:

            db.session.delete(favorite_song)
            db.session.commit()
            print(favorite_song, 'removed')
            return jsonify({'status':'success','type':'removed'})
        except Exception as e:
            print(e)
            return jsonify({'status':'unsuccessful'})
        
    else:
        try:
            favorite_song = UserFavoriteSong(song_id=song_id, user_id=current_user.id)
            db.session.add(favorite_song)
            db.session.commit()
            print(favorite_song, 'added')
            return jsonify({'status': 'success', 'type': 'added'})
        except Exception as e:
            print(e)
            return jsonify({'status': 'unsuccessful'})

#Admin Functions



#1:Song Operations
@auth.route('/administrator/flagsong/<int:song_id>', methods=['POST'])
@login_required
def flag_song(song_id):
    if request.method == 'POST':
        song=Song.query.get(song_id)
        if song:
            song.flag = 0 if song.flag is None else song.flag
            song.flag+=1

            if song.flag > 3:
                return redirect(url_for('auth.admindeletesong', song_id=song_id))

            db.session.commit()

        return redirect(url_for('auth.admin'))
    



@auth.route('/administrator/removeflagsong/<int:song_id>', methods=['POST'])
@login_required
def remove_flag_song(song_id):
    if request.method == 'POST':
        song=Song.query.get(song_id)
        
        if song:
            song.flag = 0 if song.flag is None else song.flag 
            if song.flag <= 3:
               song.flag-=1
            if song.flag<0:
                song.flag=0
            elif song.flag>=3:
                song.flag=3


            db.session.commit()

        return redirect(url_for('auth.admin'))


@auth.route('/administrator/deletesong/<int:song_id>', methods=['POST'])
@login_required
def deleteadminsong(song_id):
    if request.method == 'POST':
        song=Song.query.get(song_id)
        print(song)
        if song:
            userlikes = UserLike.query.filter_by(song_id=song_id).all()
            print(userlikes)
            if userlikes:
                for userlike in userlikes:
                    print(userlike)
                    db.session.delete(userlike)

                db.session.delete(song)

            db.session.commit()

        return redirect(url_for('auth.admin'))
    


@auth.route('/administrator/flagcreator/<int:creator_id>', methods=['POST'])
@login_required
def flag_creator(creator_id):
    if request.method == 'POST':
        creator = User.query.get(creator_id)
        if creator:
            creator.flag = 0 if creator.flag is None else creator.flag
            creator.flag += 1

            if creator.flag >3:
            

                return redirect(url_for('auth.delete_admin_creator', creator_id=creator_id))
            db.session.commit()

        return redirect(url_for('auth.admin'))

@auth.route('/administrator/removeflagcreator/<int:creator_id>', methods=['POST'])
@login_required
def remove_flag_creator(creator_id):
    if request.method == 'POST':
        creator = User.query.get(creator_id)
        if creator:
            creator.flag = 0 if creator.flag is None else creator.flag
            if creator.flag > 0:
                creator.flag -= 1
            if creator.flag<=0:
                creator.flag=0
            elif creator.flag>=3:
                creator.flag=3

            db.session.commit()

        return redirect(url_for('auth.admin'))

@auth.route('/administrator/deletecreator/<int:creator_id>', methods=['POST'])
@login_required
def delete_admin_creator(creator_id):
    if request.method == 'POST':
        creator = User.query.get(creator_id)
        songs = Song.query.filter_by(creator_id=creator_id).all()
        albums = Album.query.filter_by(artist_id=creator_id).all()
        playlists = Playlist.query.filter_by(user_id=creator_id).all()
        userlikes = UserLike.query.filter_by(user_id=creator_id).all()
        
        albumlikes = UserLikeAlbum.query.filter_by(user_id=creator_id).all()
        song_ids = [song.id for song in creator.songs]
        UserLike.query.filter(UserLike.song_id.in_(song_ids)).delete(synchronize_session=False)



        if creator:
            
            for userlike in userlikes:
                
                db.session.delete(userlike)
            
            for song in songs:
                    if song in userlikes:

                        db.session.delete(song)
            for song in songs:
                if song:
                    db.session.delete(song)

                db.session.delete(song)
            for albumlike in albumlikes:
                db.session.delete(albumlike)
            for album in albums:

                db.session.delete(album)
            db.session.commit()
            for playlist in playlists:
                db.session.delete(playlist)
            db.session.delete(creator)

        db.session.commit()

        return redirect(url_for('auth.admin'))
    
@auth.route('/creator/deletecreator/<int:creator_id>', methods=['POST'])
@login_required
def delete_creator(creator_id):
    if request.method == 'POST':
        creator = User.query.get(creator_id)
        songs = Song.query.filter_by(creator_id=creator_id).all()
        albums = Album.query.filter_by(artist_id=creator_id).all()
        playlists = Playlist.query.filter_by(user_id=creator_id).all()
        userlikes = UserLike.query.filter_by(user_id=creator_id).all()
        
        albumlikes = UserLikeAlbum.query.filter_by(user_id=creator_id).all()
        song_ids = [song.id for song in creator.songs]
        UserLike.query.filter(UserLike.song_id.in_(song_ids)).delete(synchronize_session=False)



        if creator:
            
            for userlike in userlikes:
                
                db.session.delete(userlike)
            
            for song in songs:
                    if song in userlikes:

                        db.session.delete(song)
            for song in songs:
                if song:
                    db.session.delete(song)

                db.session.delete(song)
            for albumlike in albumlikes:
                db.session.delete(albumlike)
            for album in albums:

                db.session.delete(album)
            db.session.commit()
            for playlist in playlists:
                db.session.delete(playlist)
            db.session.delete(creator)

        db.session.commit()
        flash("Your account is deleted successfully.",category='error')
        return redirect(url_for('views.home'))


# @auth.route('/administrator/flagalbum/<int:album_id>', methods=['POST'])
# @login_required
# def flag_album(album_id):
#     if request.method == 'POST':
#         album = Album.query.get(album_id)
#         if album:
#             album.flag = 0 if album.flag is None else album.flag
#             album.flag += 1
#             if album.flag > 3:
#                 db.session.delete(album)
#             db.session.commit()

#         return redirect(url_for('auth.admin'))
    


# @auth.route('/administrator/removeflagalbum/<int:album_id>', methods=['POST'])
# @login_required
# def remove_flag_album(album_id):
#     if request.method == 'POST':
#         album = Album.query.get(album_id)
#         if album:
#             album.flag = 0 if album.flag is None else album.flag
#             if album.flag > 0:
#                 album.flag -= 1

#             db.session.commit()

#         return redirect(url_for('auth.admin'))
    

@auth.route('/administrator/deletealbum/<int:album_id>', methods=['POST'])
@login_required
def delete_album_admin(album_id):
    album = Album.query.get(int(album_id))

    if album and current_user.id==album.artist_id:
        userlikes = UserLikeAlbum.query.filter_by(album_id=album.id).all()
        print(userlikes)
        if userlikes:
            for userlike in userlikes:
                print(userlike)
                db.session.delete(userlike)
            db.session.delete(album)
            db.session.commit()

        flash('Album deleted successfully', 'success')
    else:
        flash('Album not found', 'error')
    return redirect(url_for('auth.admin'))

