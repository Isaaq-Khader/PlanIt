# Copyright 2016 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import webapp2
import jinja2
import os
from google.appengine.api import users

from google.appengine.api import users

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)

def root_parent():
    '''A single key to be used as the ancestor for all dog entries.

    Allows for strong consistency at the cost of scalability.'''
    return ndb.Key('Parent', 'default_parent')

#class Invites(ndb.Model):
    #'''A database entry representing a single user.'''
    #email = ndb.StringProperty()


class MainPage(webapp2.RequestHandler):
    def get(self):
        user = users.get_current_user()
        template = JINJA_ENVIRONMENT.get_template('templates/index.html')
        data = {
          'user': user,
          'login_url': users.create_login_url(self.request.uri),
          'logout_url': users.create_logout_url(self.request.uri),

        }
        self.response.headers['Content-Type'] = 'text/html'
        self.response.write(template.render(data))


class InvitePage(webapp2.RequestHandler):
    def get(self):
        template = JINJA_ENVIRONMENT.get_template('templates/invite.html')
        self.response.headers['Content-Type'] = 'text/html'
        self.response.write(template.render())

class DayPage(webapp2.RequestHandler):
    def get(self):
        template = JINJA_ENVIRONMENT.get_template('templates/day.html')
        self.response.headers['Content-Type'] = 'text/html'
        self.response.write(template.render())

class PlanningPage(webapp2.RequestHandler):
    def get(self):
        template = JINJA_ENVIRONMENT.get_template('templates/planning.html')
        self.response.headers['Content-Type'] = 'text/html'
        self.response.write(template.render())
class ContactPage(webapp2.RequestHandler):
    def get(self):
        template = JINJA_ENVIRONMENT.get_template('templates/contact.html')
        self.response.headers['Content-Type'] = 'text/html'
        self.response.write(template.render())

# The App Config
app = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/invite', InvitePage),
    ('/day', DayPage),
    ('/planning', PlanningPage),
    ('/contact', ContactPage),
    

], debug=True)
