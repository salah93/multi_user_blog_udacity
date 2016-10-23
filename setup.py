from os.path import join, dirname
import webapp2
import hmac
import jinja2
from sensitive import salt
from models import User


class InvalidUserException(Exception):
    pass

template_dir = join(dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader=jinja2.FileSystemLoader(template_dir),
                               autoescape=True)


class Handler(webapp2.RequestHandler):
    def __init__(self, request, response):
        self.initialize(request, response)
        self.user_cookie = 'user'
        self.error_cookie = 'error'

    def set_cookie(self, name, value):
        v = str("{0}={1};Path=/".format(name, value))
        self.response.headers.add_header('Set-Cookie', v)

    def isvalid(self):
        try:
            user_cookie = self.request.cookies.get('user', False)
            name, hname = (user_cookie.split('|')
                           if user_cookie
                           else [None, None])
            if (name and hmac.new(salt, name).hexdigest() == hname):
                if not User.all().filter('username =', name).get():
                    self.set_cookie(self.user_cookie, '')
                    raise(InvalidUserException)
                return name
            else:
                raise(InvalidUserException)
        except InvalidUserException:
            self.redirect('/signup')

    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)

    def render_str(self, template, **params):
        t = jinja_env.get_template(template)
        return t.render(params)

    def render(self, template, **params):
        self.write(self.render_str(template, **params))
