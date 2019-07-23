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

# WEBSITE: https://planit-247516.appspot.com

from google.appengine.ext import vendor

# Add any libraries install in the "lib" folder.
vendor.add('lib')

import httplib2
import webapp2
import jinja2
import os
import pickle

from google.appengine.api import users
from googleapiclient import discovery
from oauth2client import client
from oauth2client.contrib import appengine
from google.appengine.api import memcache
from google.appengine.ext import ndb

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)

CLIENT_SECRETS = os.path.join(os.path.dirname(__file__), 'client_secrets.json')

http = httplib2.Http(memcache)
service = discovery.build("calendar", "v3", http=http)
decorator = appengine.oauth2decorator_from_clientsecrets(
    CLIENT_SECRETS,
    scope='https://www.googleapis.com/auth/calendar')

def root_parent():
    '''Allows for strong consistency at the cost of scalability.'''
    return ndb.Key('Parent', 'default_parent')

class Event(ndb.Model):
    '''A database entry representing a single user.'''
    place = ndb.StringProperty()
    title = ndb.StringProperty()
    description = ndb.StringProperty()
    startTime = ndb.StringProperty()
    endTime = ndb.StringProperty()

class Invite(ndb.Model):
    '''A database entry representing a single user.'''
    email = ndb.StringProperty()
    event_key = ndb.KeyProperty(Event)


class MainPage(webapp2.RequestHandler):
    # @decorator.oauth_required
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
        # try:
        #     http = decorator.http()
        #     calendarList = service.calendarList().list(pageToken=None).execute(http=http)
        #     for calendar_list_entry in calendarList['items']:
        #         print(calendar_list_entry['summary'])
        # except client.AccessTokenRefreshError:
        #     self.redirect(decorator.authorize_url())

class InvitePage(webapp2.RequestHandler):
    def get(self):
        event_key = self.request.get('event_key')
        if event_key == "":
            new_event = Event().put()
            self.redirect('/invite?event_key='+new_event.urlsafe())
            return
        template = JINJA_ENVIRONMENT.get_template('templates/invite.html')
        self.response.headers['Content-Type'] = 'text/html'
        print event_key
        emails = Invite.query(Invite.event_key == ndb.Key(urlsafe=event_key), ancestor=root_parent()).fetch()
        data = {
            'invites': emails
        }
        self.response.write(template.render(data))

    def post(self):
        new_invite = Invite(parent=root_parent())
        new_invite.email = self.request.get('email')

        new_invite.event_key = ndb.Key(urlsafe=self.request.get('event_key'))
        new_invite.put()

        self.redirect('/invite?event_key='+self.request.get('event_key'))

class DayPage(webapp2.RequestHandler):
    def get(self):
        template = JINJA_ENVIRONMENT.get_template('templates/day.html')
        self.response.headers['Content-Type'] = 'text/html'
        data = {
            'invites': Invite.query(ancestor=root_parent()).fetch()
        }
        self.response.write(template.render(data))

class PlanningPage(webapp2.RequestHandler):
    def get(self):
        template = JINJA_ENVIRONMENT.get_template('templates/planning.html')
        sum_param = self.request.get('event_title')
        location_param = self.request.get('event_place')
        des_param = self.request.get('event_des')
        event_start_param = self.request.get('event_start')
        event_end_param = self.request.get('event_end')
        attending_param = self.request.get('emails')
        event = {
          'summary': sum_param,
          'location': location_param,
          'description': des_param,
          'start': {
            'dateTime': '2015-05-28T09:00:00-07:00',
            'timeZone': 'America/Los_Angeles',
          },
          'end': {
            'dateTime': '2015-05-28T17:00:00-07:00',
            'timeZone': 'America/Los_Angeles',
          },
          'attendees': [
            {'email': 'attending_param'}
          ],
          'reminders': {
            'useDefault': False,
            'overrides': [
              {'method': 'email', 'minutes': 24 * 60},
              {'method': 'popup', 'minutes': 10},
            ],
          },
        }

        # event = service.events().insert(calendarId='primary', body=event).execute()
        # print 'Event created: %s' % (event.get('htmlLink'))
        self.response.headers['Content-Type'] = 'text/html'
        self.response.write(template.render(event))

class ContactPage(webapp2.RequestHandler):
    def get(self):
        template = JINJA_ENVIRONMENT.get_template('templates/contact.html')
        self.response.headers['Content-Type'] = 'text/html'
        self.response.write(template.render())

class DeleteInvites(webapp2.RequestHandler):
    '''The handler for deleting invites.'''
    def post(self):
        to_delete = self.request.get('to_delete', allow_multiple=True)
        for entry in to_delete:
            key = ndb.Key(urlsafe=entry)
            key.delete()
        # redirect to '/' so that the MainPage.get() handler will run and show
        # the list of dogs.
        self.redirect('/invite')

class Confirmation(webapp2.RequestHandler):
    def get(self):
        template = JINJA_ENVIRONMENT.get_template('templates/confirmation.html')
        self.response.headers['Content-Type'] = 'text/html'
        data = {
            'invites': Invite.query(ancestor=root_parent()).fetch()
        }
        self.response.write(template.render(data))

    def post(self):
        # INVITIES HAS NOT BEEN TESTED!!!
        new_invite = Invite(parent=root_parent())
        invities = CreateEvent(parent=root_parent())
        new_invite.email = self.request.get('email')
        invities.attendees.email = self.request.get('email')
        new_invite.put()
        invities.put()

        self.redirect('/invite')

# The App Config
app = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/invite', InvitePage),
    ('/day', DayPage),
    ('/delete_invites', DeleteInvites),
    ('/contact',ContactPage),
    ('/planning',PlanningPage),
    #('confirmation',Confirmation),
    (decorator.callback_path, decorator.callback_handler()),

], debug=True)
