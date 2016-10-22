# - * - coding: utf-8 - *
import hmac
import re
from models import User, Post, Likes
from setup import Handler, salt, webapp2


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
            self.set_cookie('user', '{0}|{1}'.format(username, hash_string))
            # add to db
            hpass = hmac.new(salt, password).hexdigest()
            user = User(username=username, password=hpass, email=email)
            user.put()
            return self.redirect('/welcome')


class Welcome(Handler):
    def get(self):
        name = self.isvalid()
        error = self.request.cookies.get('error', False)
        print self.request.cookies
        if error:
            self.set_cookie('error', '')
        user = User.all().filter('username =', name).get()
        posts = Post.all().order('-datetime')
        user_liked = {}
        for l in Likes.all().filter('user =', user):
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
        pid = int(post_id)
        post = Post.get_by_id(pid)
        user = User.all().filter('username =', name).get()
        total_likes = Likes.all().filter('post =', post)
        liked = True if total_likes.filter('user =', user) else False
        likes = len(list(total_likes))
        if post:
            self.render("show.html",
                        post=post,
                        liked=liked,
                        likes=likes)
        else:
            self.render("show.html", error="No such blog :(")


class EditPost(Handler):
    def get(self, post_id):
        name = self.isvalid()
        post = Post.get_by_id(int(post_id))
        if post.author.username == name:
            self.render('edit.html', post=post)
        else:
            self.set_cookie('error', True)
            self.redirect('/welcome')

    def post(self, post_id):
        name = self.isvalid()
        post = Post.get_by_id(int(post_id))
        if post.author.username == name:
            if self.request.get('delete'):
                likes = Likes.all().filter('post = ', post)
                if likes:
                    [l.delete() for l in likes]
                post.delete()
            else:
                post.post = self.request.get('post').strip()
                post.title = self.request.get('title').strip()
                post.put()
        else:
            self.set_cookie('error', True)
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
            self.set_cookie('user', '{0}|{1}'.format(username, hname))
            return self.redirect('/welcome')
        else:
            return self.render('login.html', login_error=True)


class Logout(Handler):
    def get(self):
        self.set_cookie('user', '')
        self.redirect('/signup')


class LikesPost(Handler):
    def post(self, post_id):
        name = self.isvalid()
        post = Post.get_by_id(int(post_id))
        if name != post.author.username:
            user = User.all().filter('username = ', name).get()
            like = Likes.all().filter(
                    'post =', post).filter(
                        'user =', user).get()
            if like:
                like.delete()
            else:
                like = Likes(user=user, post=post)
                like.put()
            return self.write('success')
        else:
            return self.write('failed')


app = webapp2.WSGIApplication([(r'/signup', Signup),
                               (r'/welcome/?', Welcome),
                               (r'/logout/?', Logout),
                               (r'/newpost/?', PostPage),
                               (r'/([0-9]+)/?', ShowPost),
                               (r'/edit/([0-9]+)/?', EditPost),
                               (r'/like/([0-9]+)/?', LikesPost),
                               (r'/login/?', Login)],
                              debug=True)
