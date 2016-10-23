# - * - coding: utf-8 - *
import hmac
import json
import re
from datetime import datetime
from models import User, Post, Like, Comment
from setup import Handler, salt, webapp2


class Base(Handler):
    def get(self):
        self.redirect('/welcome')


class Signup(Handler):
    def get(self):
        self.render("signup.html")

    def post(self):
        VALID_PATTERN = re.compile(r"^[a-zA-Z1-9-_]{6,20}$")

        def valid(tag):
            return VALID_PATTERN.match(tag)

        errors = {}
        email = self.request.get("email").strip()
        username = self.request.get("username").strip()
        errors['user_error'] = True if not valid(username) else False
        if not errors['user_error']:
            # check against db
            users = User.all().filter('username =', username).get()
            if users:
                errors['unique_error'] = True
                return self.render('signup.html',
                                   email=email, **errors)
        password = self.request.get("password").strip()
        errors['password_error'] = True if not valid(password) else False
        verify = self.request.get("verify").strip()
        errors['verify_error'] = True if password != verify else False
        if any(errors.values()):
            return self.render('signup.html',
                               user=username,
                               email=email,
                               **errors)
        else:
            hash_string = hmac.new(salt, username).hexdigest()
            self.set_cookie(self.user_cookie, '{0}|{1}'.format(
                                username, hash_string))
            # add to db
            hpass = hmac.new(salt, password).hexdigest()
            user = User(username=username, password=hpass, email=email)
            user.put()
            return self.redirect('/login')


class Welcome(Handler):
    def get(self):
        name = self.isvalid()
        error = self.request.cookies.get(self.error_cookie, False)
        if error:
            self.set_cookie(self.error_cookie, '')
        user = User.all().filter('username =', name).get()
        posts = Post.all().order('-datetime')
        user_liked = {}
        for l in Like.all().filter('user =', user):
            pid = l.post.key().id()
            user_liked[pid] = 'liked'
        self.render("welcome.html",
                    liked=user_liked,
                    user=name,
                    posts=posts,
                    error=error)


class ShowPost(Handler):
    def get(self, post_id):
        name = self.isvalid()
        post = Post.get_by_id(int(post_id))
        user = User.all().filter('username =', name).get()
        comments = Comment.all().filter('post =', post).order('-datetime')
        total_likes = Like.all().filter('post =', post).count()
        liked = 'liked' if Like.all().filter(
                            'post =', post).filter(
                                'user =', user).get() else None
        if post:
            self.render("show.html",
                        post=post,
                        likes=total_likes,
                        liked=liked,
                        username=name,
                        comments=comments)
        else:
            self.render("show.html", error="No post lives here :(")

    def post(self, post_id):
        name = self.isvalid()
        user = User.all().filter('username =', name).get()
        post = Post.get_by_id(int(post_id))
        user_comment = self.request.get('comment').strip()
        timestamp = datetime.now()
        comment = Comment(user=user, post=post, body=user_comment)
        comment.put()
        comments = Comment.all().filter('datetime >=', timestamp)
        # datastore is sometimes slow to add objects to set
        l = [c for c in comments if c != comment] + [comment]
        return self.write(json.dumps({'comments': [{'body': c.body,
                                                   'id': c.key().id(),
                                                    'datetime':
                                                    str(c.datetime),
                                                    'username':
                                                    c.user.username}
                                                   for c in l],
                                      'currentUser': name}))


class EditComment(Handler):
    def post(self, comment_id):
        name = self.isvalid()
        comment = Comment.get_by_id(int(comment_id))
        if comment and name == comment.user.username:
            comment.body = self.request.get('comment')
            comment.put()
            return self.write(json.dumps({'body': comment.body,
                                          'datetime':
                                          str(comment.datetime),
                                          'username':
                                          comment.user.username}))
        else:
            # show error
            self.write("forbidden access")


class DeleteComment(Handler):
    def post(self, comment_id):
        name = self.isvalid()
        comment = Comment.get_by_id(int(comment_id))
        if comment and name == comment.user.username:
            comment.delete()
            return self.write("success")
        else:
            # show error
            self.write("forbidden access")


class EditPost(Handler):
    def get(self, post_id):
        name = self.isvalid()
        post = Post.get_by_id(int(post_id))
        if post.author.username == name:
            self.render('edit.html', post=post)
        else:
            self.set_cookie(self.error_cookie, True)
            self.redirect('/welcome')

    def post(self, post_id):
        name = self.isvalid()
        post = Post.get_by_id(int(post_id))
        if post.author.username == name:
            post.post = self.request.get('post').strip()
            post.title = self.request.get('title').strip()
            post.put()
        else:
            self.set_cookie(self.error_cookie, True)
        self.redirect('/welcome')


class DeletePost(Handler):
    def post(self, post_id):
        name = self.isvalid()
        post = Post.get_by_id(int(post_id))
        if post.author.username == name:
            likes = Like.all().filter('post = ', post)
            comments = Like.all().filter('post = ', post)
            [l.delete() for l in likes]
            [c.delete() for c in comments]
            post.delete()
        else:
            self.set_cookie(self.error_cookie, True)
        self.redirect('/welcome')


class PostPage(Handler):
    def get(self):
        self.isvalid()
        self.render("post.html")

    def post(self):
        username = self.isvalid()
        title = self.request.get("subject")
        body = self.request.get("content")
        user = User.all().filter('username =', username).get()
        if user and body and title:
            post = Post(title=title, author=user, post=body)
            post.put()
        self.redirect("/welcome")


class Login(Handler):
    def get(self):
        self.render("login.html")

    def post(self):
        username = self.request.get("username").strip()
        password = self.request.get("password").strip()
        hpass = hmac.new(salt, password).hexdigest()
        valid = User.all().filter('username =', username).filter(
                        'password =', hpass).get()
        if valid:
            hname = hmac.new(salt, username).hexdigest()
            self.set_cookie(self.user_cookie, '{0}|{1}'.format(username, hname))
            return self.redirect('/welcome')
        else:
            return self.render('login.html', login_error=True)


class Logout(Handler):
    def get(self):
        self.set_cookie(self.user_cookie, '')
        self.redirect('/signup')


class LikePost(Handler):
    def post(self, post_id):
        name = self.isvalid()
        post = Post.get_by_id(int(post_id))
        if name != post.author.username:
            user = User.all().filter('username = ', name).get()
            like = Like.all().filter(
                    'post =', post).filter(
                        'user =', user).get()
            if like:
                like.delete()
            else:
                like = Like(user=user, post=post)
                like.put()
            return self.write('success')
        else:
            return self.write('failed')


app = webapp2.WSGIApplication([(r'/?', Base),
                               (r'/signup', Signup),
                               (r'/welcome/?', Welcome),
                               (r'/logout/?', Logout),
                               (r'/newpost/?', PostPage),
                               (r'/([0-9]+)/?', ShowPost),
                               (r'/edit/([0-9]+)/?', EditPost),
                               (r'/delete/([0-9]+)/?', DeletePost),
                               (r'/edit/comment/([0-9]+)/?', EditComment),
                               (r'/delete/comment/([0-9]+)/?', DeleteComment),
                               (r'/like/([0-9]+)/?', LikePost),
                               (r'/login/?', Login)],
                              debug=True)
