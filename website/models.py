from website import db
from flask_login import UserMixin
from sqlalchemy import LargeBinary, Interval
from sqlalchemy.sql import func, table
# from flask_wtf import wtforms

# from wtforms import StringField, PasswordField, SubmitField

# from wtforms.validators import InputRequired, Length, ValidationError

from datetime import datetime




class UserFollowsArtist(db.Model):
    __tablename__ = 'user_follows_artist'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    artist_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
class User(db.Model, UserMixin):
    __tablename__ = 'user'
    is_online=db.Column(db.Boolean,default=False)
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True)
    password = db.Column(db.String(150))
    user_name = db.Column(db.String(150))
    is_creator = db.Column(db.Boolean, default=False)
    is_verified = db.Column(db.Boolean, default=False)
    is_admin = db.Column(db.Boolean, default=False)

    playlists = db.relationship('Playlist', backref='user', lazy=True)
    songs = db.relationship('Song', backref='user', lazy=True)
    
    premium = db.Column(db.Boolean, default=False)
    albums = db.relationship('Album', backref='creator', lazy=True)
    # creatorr_name=db.relationship('Song', backref='creatorr', lazy=True)

    # songs = db.relationship('Song', back_populates='creator')

    liked_songs = db.relationship(
        'Song',
        secondary='user_likes',
        back_populates='liked_by_users',
        overlaps="liked_songs"
    )
    profile_image_path = db.Column(db.String(255))
    description = db.Column(db.String(255))
    # liked_creators = db.relationship(
    #     'User',
    #     secondary='user_like_creator',
    #     primaryjoin='User.id == user_like_creator.c.user_id',
    #     secondaryjoin='User.id == user_like_creator.c.creator_id',
    #     backref=db.backref('liked_by_users', lazy='dynamic'),
    #     lazy='dynamic',
    # )
    creator_name = db.Column(db.String(150))
    bio = db.Column(db.Text)
    dob = db.Column(db.Date)
    contact_info = db.Column(db.String(255))
    portfolio = db.Column(db.String(255))
    social_media_links = db.Column(db.String(255))

    flag= db.Column(db.Integer, default=0)

    liked_albums = db.relationship('Album', secondary='user_like_album', back_populates='users_who_liked_album')
    last_login = db.Column(db.DateTime, default=None)

    subscription_validity = db.Column(db.Integer, default=0)
    subscription_start_date = db.Column(db.Date, default=None)
    subscription_end_date = db.Column(db.Date, default=None)

    followed_artists = db.relationship(
        'User',
        secondary='user_follows_artist',
        primaryjoin='User.id == UserFollowsArtist.user_id',
        secondaryjoin='User.id == UserFollowsArtist.artist_id',
        backref=db.backref('followers', lazy='dynamic'),
        lazy='dynamic'
    )
    users_favorite_song = db.relationship('Song', secondary='user_favorite_song', back_populates='song_favorite_user')

    # def is_subscription_active(self):
    #     if self.subscription_end_date is None:
    #         return False
    #     current_date = datetime.now().date()
    #     if current_date <= self.subscription_end_date:
    #         return True
    #     else:
    #         # Subscription has ended, update user attributes
    #         if self.is_creator:
    #             self.is_creator = False
    #         if self.is_creator and self.premium:
    #             self.is_creator = False
    #             self.premium = False
    #         db.session.commit()
    #         return False


    

class UserLikeCreator(db.Model):
    __tablename__ = 'user_like_creator'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    creator_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)




class Administratormushify(db.Model, UserMixin):
    __tablename__ = 'administratormushify'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True)
    password = db.Column(db.String(150))
    user_name = db.Column(db.String(150))
    is_admin = db.Column(db.Boolean, default=True)



class Playlist(db.Model, UserMixin):
    __tablename__ = 'playlist'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    songs = db.relationship('Song', secondary='playlist_songs', lazy='subquery', backref=db.backref('playlists', lazy=True))

class Song(db.Model):
    __tablename__ = 'song'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150))
    artist = db.Column(db.String(150))
    category = db.Column(db.String(150))
    duration = db.Column(db.String(20))
    lyrics = db.Column(db.Text)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    likes = db.Column(db.Integer, default=0)
    album_id = db.Column(db.Integer, db.ForeignKey('album.id'))
    creator_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    genre = db.Column(db.Text)
    creator = db.relationship('User', foreign_keys=[creator_id], back_populates='songs')
    song_file_path = db.Column(db.String(255))
    cover_image_path = db.Column(db.String(255))

    @property
    def creator_name(self):
        return self.creator.creator_name

    liked_by_users = db.relationship(
        'User',
        secondary='user_likes',
        back_populates='liked_songs',
        overlaps="liked_songs"
    )
    
    albums = db.relationship('Album', secondary='album_songs', back_populates='songs')
    song_favorite_user = db.relationship('User', secondary='user_favorite_song', back_populates='users_favorite_song')

    flag= db.Column(db.Integer, default=0)
class PlaylistSong(db.Model):
    __tablename__ = 'playlist_songs'
    playlist_id = db.Column(db.Integer, db.ForeignKey('playlist.id'), primary_key=True)
    song_id = db.Column(db.Integer, db.ForeignKey('song.id'), primary_key=True)

class Album(db.Model):
    __tablename__ = 'album'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150))
    genre = db.Column(db.String(100))
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    artist_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    cover_image= db.Column(db.String(255))
    songs = db.relationship('Song', secondary='album_songs', back_populates='albums')
    like = db.Column(db.Integer, default=0)

    user_associated_with_album = db.relationship('User', backref="album_user" , lazy=True)
    flag= db.Column(db.Integer, default=0)
    users_who_liked_album = db.relationship('User', secondary='user_like_album', back_populates='liked_albums')
    creator_album = db.relationship('User', foreign_keys=[artist_id], back_populates='albums')
    @property
    def creator_name(self):
        return self.creator_album.creator_name



class UserLike(db.Model):
    __tablename__ = 'user_likes'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    song_id = db.Column(db.Integer, db.ForeignKey('song.id'), nullable=False)

    user = db.relationship('User', backref=db.backref('liked_songs_by_userlikes', lazy=True))
    song = db.relationship('Song', backref=db.backref('users_who_liked', lazy=True))


class AlbumSongAssociation(db.Model):
    __tablename__ = 'album_songs'
    album_id = db.Column(db.Integer, db.ForeignKey('album.id'), primary_key=True)
    song_id = db.Column(db.Integer, db.ForeignKey('song.id'), primary_key=True)

    # album = db.relationship('Album', back_populates='songs')
    # song = db.relationship('Song', back_populates='albums')


class UserLikeAlbum(db.Model):
    __tablename__ = 'user_like_album'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    album_id = db.Column(db.Integer, db.ForeignKey('album.id'), nullable=False)

    # user = db.relationship('User', backref=db.backref('liked_albums_by_user', lazy=True))
    # album = db.relationship('Album', backref=db.backref('users_who_liked_album', lazy=True))



# UserLikeAlbum = db.Table('user_like_album',
#     db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
#     db.Column('album_id', db.Integer, db.ForeignKey('album.id'), primary_key=True)
# )



class DailyUserActivity(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, default=datetime.utcnow().date())
    active_user_count = db.Column(db.Integer, default=0)




class UserSongInteraction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    song_id = db.Column(db.Integer, db.ForeignKey('song.id'), nullable=False)
    start_time = db.Column(db.DateTime, default=datetime.utcnow)
    end_time = db.Column(db.DateTime, default=None)
    accumulated_watch_time = db.Column(Interval, default=datetime.utcnow() - datetime.utcnow())


class UserFavoriteSong(db.Model):
    __tablename__ = 'user_favorite_song'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    song_id = db.Column(db.Integer, db.ForeignKey('song.id'), nullable=False)
    user = db.relationship('User', backref=db.backref('favorite_songs', lazy=True))
    song = db.relationship('Song', backref=db.backref('favorited_by_users', lazy=True))

class offersNdicounts(db.Model):
    __tablename__='offersNdiscounts'
    id=db.Column(db.Integer,primary_key=True)
    offercode = db.Column(db.String(128), nullable=False)
    discount = db.Column(db.Integer, nullable=False)


class SongComment(db.Model):
    __tablename__ = 'song_comment'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    song_id = db.Column(db.Integer, db.ForeignKey('song.id'), nullable=False)
    comment = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    parent_comment_id = db.Column(db.Integer, db.ForeignKey('song_comment.id'))

    user = db.relationship('User', backref=db.backref('comments', lazy=True))
    song = db.relationship('Song', backref=db.backref('comments', lazy=True))
    parent_comment = db.relationship('SongComment', remote_side=[id], backref='replies', uselist=False)