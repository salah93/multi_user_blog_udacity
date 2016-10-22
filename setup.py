from os.path import join, dirname
import webapp2
import hmac
import jinja2


template_dir = join(dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader=jinja2.FileSystemLoader(template_dir),
                               autoescape=True)
salt = 'fROUtlLGeD947zXM'


class Handler(webapp2.RequestHandler):
    def set_cookie(self, name, value):
        v = str("{0}={1};Path=/".format(name, value))
        self.response.headers.add_header('Set-Cookie', v)

    def isvalid(self):
        try:
            user_cookie = self.request.cookies.get('user', False)
            name, hname = user_cookie.split('|') if user_cookie else [None, None]
            if name and hmac.new(salt, name).hexdigest() == hname:
                return name
            else:
                raise(Exception)
        except:
            self.redirect('/signup')

    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)

    def render_str(self, template, **params):
        t = jinja_env.get_template(template)
        return t.render(params)

    def render(self, template, **params):
        self.write(self.render_str(template, **params))
