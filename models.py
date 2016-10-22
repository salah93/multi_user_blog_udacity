from google.appengine.ext import db


class User(db.Model):
    username = db.StringProperty(required=True)
    password = db.StringProperty(required=True)
    email = db.StringProperty(required=False)


class Post(db.Model):
    title = db.StringProperty(required=True)
    post = db.TextProperty(required=True)
    author = db.ReferenceProperty(User, required=True)
    datetime = db.DateTimeProperty(auto_now_add=True)


class Likes(db.Model):
    user = db.ReferenceProperty(User, required=True)
    post = db.ReferenceProperty(Post, required=True)

