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
import datetime
import logging
import json
from datetime import date
from datetime import time
from datetime import datetime

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
    date = ndb.StringProperty()
    location = ndb.StringProperty()
    startTime = ndb.StringProperty()
    endTime = ndb.StringProperty()


class Invite(ndb.Model):
    '''A database entry representing a single user.'''
    email = ndb.StringProperty()
    event_key = ndb.KeyProperty(Event)
    calenderId = ndb.StringProperty()

#class CalenderIds(ndb.Model):
    #'''A database entry representing calenderId of each user.'''
    #calenderId = ndb.StringProperty()
def importCalender():
    print 'Calender imported'

class MainPage(webapp2.RequestHandler):
    @decorator.oauth_aware
    def get(self):
        user = users.get_current_user()
        template = JINJA_ENVIRONMENT.get_template('templates/index.html')
        data = {
          'user': user,
          'login_url': users.create_login_url('/'),
          'logout_url': users.create_logout_url(self.request.uri),

        }
        self.response.headers['Content-Type'] = 'text/html'
        self.response.write(template.render(data))
        if user:
            if decorator.has_credentials():
                importCalender()
            else:
                self.redirect(decorator.authorize_url())
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
            'invites': emails,
            'event_key': event_key,
        }
        self.response.write(template.render(data))

    def post(self):
        new_invite = Invite(parent=root_parent())
        new_invite.email = self.request.get('email')
        new_invite.event_key = ndb.Key(urlsafe=self.request.get('event_key'))
        new_invite.put()

        self.redirect('/invite?event_key='+self.request.get('event_key'))

class DayPage(webapp2.RequestHandler):
    @decorator.oauth_required
    def get(self):
        template = JINJA_ENVIRONMENT.get_template('templates/day.html')
        self.response.headers['Content-Type'] = 'text/html'
        event_key = self.request.get('event_key')
        # dateTimeStart and dateTimeEnd must be for that certain day. So for example it is already set up
        # to be set for the day July 24th, 2019

        date_object = datetime.today()
        print(date_object)

        dateTimeStart = "2019-07-24T00:00:00-05:00"
        dateTimeEnd = "2019-07-24T23:59:00-05:00"
        getCalendar = {
          "timeMin": dateTimeStart,
          "timeMax": dateTimeEnd,
          "timeZone": "UTC",
          "items": [
            {
              "id": "primary"
            }
          ]
        }
        http = decorator.http()
        busy = service.freebusy().query(body=getCalendar).execute(http=http)

        #this allows pulls in data by each day

            # need to convert time to show other time besides what is considered "busy"
        if len(busy['calendars']['primary']['busy']) == 1:
            for e in busy['calendars']['primary']['busy']:
                start =  e['start']
                end = e['end']

                getDate = slice(10)
                start_date = start[getDate]
                end_date = end[getDate]

                getTime = slice(11,19)
                start_time = start[getTime]
                end_time = end[getTime]

                hr = slice(2)
                rest_of_time = slice(2,5)

                start_int = int(start_time[hr])
                end_int = int(end_time[hr])

                if start_int > 12:
                    start_int = start_int - 12
                    start_ending = "PM"
                elif start_int == 12:
                    start_ending = "PM"
                else:
                    start_ending = "AM"

                if end_int > 12:
                    end_int = end_int - 12
                    end_ending = "PM"
                elif end_int == 12:
                    end_ending = "PM"
                else:
                    end_ending = "AM"

                start = str(start_int) + start_time[rest_of_time] + " " + start_ending
                end = str(end_int) + end_time[rest_of_time] + " " + end_ending

                availability = "12:00 AM - "+ start + "   " + end + " - 11:59 PM"
                print availability

        elif len(busy['calendars']['primary']['busy']) > 1:
            times = []
            dates = []
            time = slice(11,16)
            hr = slice(2)
            min = slice(3,6)
            day_slice = slice(8,10)
            getDate = slice(10)


            for e in busy['calendars']['primary']['busy']:
                start =  e['start']
                end = e['end']

                start_date = start[getDate]
                end_date = end[getDate]
                start_time = start[time]
                end_time = end[time]

                dates.append(start_date)
                dates.append(end_date)

                times.append(start_time)
                times.append(end_time)
                counter = 0
                end_counter = len(times)

            hrs_into_min = []
            hrs_into_min2 = [600,780,900]

            for time in times:
                # gives integer versions of the times for conversation purposes
                time_hr = int(time[hr])
                ctime_hr = time_hr * 60
                time_min = int(time[min])
                ctime_min = ctime_hr + time_min
                hrs_into_min.append(ctime_min)
                print hrs_into_min

                if counter != 0:
                    current_date = dates[counter]
                    previous_date = dates[counter - 1]
                    current_day = int(current_date[day_slice])
                    initial_date = dates[0]
                    initial_day = int(initial_date[day_slice])

                # conversion to show in 12 hour time format
                if time_hr > 12:
                    time_hr = time_hr - 12
                    time_ending = "PM"
                elif time_hr == 12:
                    time_ending = "PM"
                else:
                    time_ending = "AM"

                if time_min == 0:
                    time_conversion = str(time_hr) + ":" + "00" + " " + time_ending
                else:
                    time_conversion = str(time_hr) + ":" + str(time_min) + " " + time_ending

                if counter == 0:
                    time_range = "12:00 AM - " + time_conversion
                elif current_day != initial_day:
                    if current_date != previous_date:
                        time_range = time_range + "11:59 PM"
                elif counter == end_counter - 1:
                    time_range = time_range + "   " + time_conversion + " - 11:59 PM"
                # elif runs if counter is odd
                elif counter % 2 == 1:
                    time_range = time_range + "   " + time_conversion + " - "
                # elif runs if the counter is even
                elif counter % 2 == 0:
                    time_range = time_range + time_conversion
                # elif counter%2 == 0:
                #     time_range = time_range + time + " - "
                else:
                    time_range = time_range + time_conversion
                counter = counter + 1

                # This is used to test if the print is working
                # |
                # V
                # print time_range
                # print "Counter % 2 ==",counter % 2
                # print "Counter: ",counter


            print time_range # This displays the final time range in which someone is free


            # elif start_date != end_date:
            #     hr = slice(2)
            #     rest_of_time = slice(2,5)
            #
            #     start_int = int(start_time[hr])
            #     end_int = int(end_time[hr])
            #
            #     if start_int > 12:
            #         start_int = start_int - 12
            #         start_ending = "PM"
            #     elif start_int == 0:
            #         start_int = 12
            #         start_ending = "AM"
            #     else:
            #         start_ending = "AM"
            #
            #     if end_int > 12:
            #         end_int = end_int - 12
            #         end_ending = "PM"
            #     elif end_int == 0:
            #         end_int = 12
            #         end_ending = "AM"
            #     else:
            #         end_ending = "AM"
            #
            #     start = str(start_int) + start_time[rest_of_time] + " " + start_ending
            #     end = str(end_int) + end_time[rest_of_time] + " " + end_ending
            #
            #     avaliable = "12:00 AM - " + start + " (" + start_date + ") - " + end + " (" + end_date + ")"
            #     print avaliable
            # else:
            #     print("Uh oh!")


        # if max - other_time > 0:
        #     other_time = end_time
        #     print end_time
        # if max - other_time == 0:
        #     max = end_time
        #     print end_time
        # if max - other_time < 0:
        #     max = end_time
        #     print end_time
        myKey = ndb.Key(urlsafe=event_key)
        emails = Invite.query(Invite.event_key == myKey, ancestor=root_parent()).fetch()

        sum_param = self.request.get('event_title')
        location_param = self.request.get('event_place')
        des_param = self.request.get('event_des')
        event_start_param = self.request.get('event_start')
        event_end_param = self.request.get('event_end')
        event_date_param = self.request.get('event_date')

        day_invites = {
            'title': sum_param,
            'description': location_param,
            'place':des_param,
            'start_time':event_start_param,
            'end_time':event_end_param,
            'date':event_date_param,
        }

        data = {
            'invites': emails,
            'event_key': event_key,
            'day_invites': day_invites
        }
        self.response.write(template.render(data))

    @decorator.oauth_required
    def post(self):
        print(self.request)
        event_key = self.request.get('event_key')
        print(event_key)
        invites = Invite.query(Invite.event_key == ndb.Key(urlsafe=event_key), ancestor=root_parent()).fetch()
        attendees = []
        for invite in invites:
            attendee = {
                'email': invite.email,
                'event_key': event_key,
            }
            attendees.append(attendee)


        sum_param = self.request.get('event_title')
        location_param = self.request.get('event_place')
        des_param = self.request.get('event_des')
        event_start_param = self.request.get('event_start')
        event_end_param = self.request.get('event_end')
        event_date_param = self.request.get('event_date')

        dateTimeStart = event_date_param + "T" + event_start_param + ":00-07:00"
        dateTimeEnd = event_date_param + "T" + event_end_param + ":00-07:00"

        new_event = ndb.Key(urlsafe=self.request.get('event_key')).get()
        new_event.title = self.request.get('event_title')
        new_event.description = self.request.get('event_des')
        new_event.place = self.request.get('event_place')
        new_event.date = self.request.get('event_date')
        new_event.startTime = dateTimeStart
        new_event.endTime = dateTimeEnd
        new_event.location= self.request.get('event_place')
        new_event.put()


        event = {
          'summary': sum_param,
          'location': location_param,
          'description': des_param,
          'start': {
            'dateTime': dateTimeStart, #'2019-07-23T17:00:00-07:00'
            'timeZone': 'America/Los_Angeles',
          },
          'end': {
            'dateTime': dateTimeEnd,
            'timeZone': 'America/Los_Angeles',
          },
          'attendees': attendees,
          'reminders': {
            'useDefault': False,
            'overrides': [
              {'method': 'email', 'minutes': 24 * 60},
              {'method': 'popup', 'minutes': 10},
            ],
          },
        }
        # try:
        #     http = decorator.http()
        #     calendarList = service.calendarList().list(pageToken=None).execute(http=http)
        #     for calendar_list_entry in calendarList['items']:
        #         print(calendar_list_entry['summary'])
        # except client.AccessTokenRefreshError:
        #     self.redirect(decorator.authorize_url())
        data = {
            'invites': invites,
            'event_key': event_key,

        }
        template = JINJA_ENVIRONMENT.get_template('templates/day.html')
        self.response.write(template.render(data))
        http = decorator.http()
        e = service.events().insert(calendarId='primary', body=event).execute(http=http)
        print 'Event created: %s' % (e.get('htmlLink'))
        print event_key
        self.redirect('/confirmation?event_key='+ self.request.get("event_key"))


class ContactPage(webapp2.RequestHandler):
    def get(self):
        template = JINJA_ENVIRONMENT.get_template('templates/contact.html')
        self.response.headers['Content-Type'] = 'text/html'
        self.response.write(template.render())

class DeleteInvites(webapp2.RequestHandler):
    '''The handler for deleting invites.'''
    def post(self):
        to_delete = self.request.get('to_delete', allow_multiple=True)
        event_key = None
        for entry in to_delete:
            key = ndb.Key(urlsafe=entry)
            invite=key.get()
            event_key = invite.event_key
            key.delete()
        self.redirect('/invite?event_key='+event_key.urlsafe())

class Confirmation(webapp2.RequestHandler):
    def get(self):
        event_key = self.request.get('event_key')
        key = ndb.Key(urlsafe = event_key)
        print(key)
        print(self.request)
        event = key.get()
        template = JINJA_ENVIRONMENT.get_template('templates/confirmation.html')
        self.response.headers['Content-Type'] = 'text/html'
        data = {
            'event': event,
            'event_key': event_key,
        }
        print(event_key)
        self.response.write(template.render(data))


# The App Config
app = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/invite', InvitePage),
    ('/day', DayPage),
    ('/delete_invites', DeleteInvites),
    ('/contact',ContactPage),
    ('/confirmation',Confirmation),
    (decorator.callback_path, decorator.callback_handler()),

], debug=True)
