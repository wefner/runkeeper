#!/usr/bin/env python

import keyring
import logging
import re
import json
from requests import Session
from bs4 import BeautifulSoup as bfs
from datetime import datetime
from runkeeperExceptions import InvalidAuhentication, NoActivityInMonth

email = ""
password = keyring.get_password("runkeeper", email)

logger = logging.basicConfig(level=logging.DEBUG)

class Runkeeper(object):
    def __init__(self, email, password):
        self.email = email
        self.password = password
        self.session = Session()
        self.site = 'https://runkeeper.com'
        self.__hidden_username = ''
        self.__authenticate()

    def __authenticate(self):
        url = "{site}/login".format(site=self.site)
        valid_authentication = self.session.post(url, data=self.__get_hidden_elements())
        if not valid_authentication.cookies.get('checker'):
            raise InvalidAuhentication

        return True

    def __get_hidden_elements(self):
        data = {'password': self.password, 'email': self.email}
        url = "{site}/login".format(site=self.site)
        auth = self.session.post(url, data=data)

        soup = bfs(auth.text, "html.parser")
        form = soup.find_all('input', {'type': 'hidden'})
        hidden_elements = { element.attrs['name'] : element.attrs['value'] for element in form}
        hidden_elements['email'] = self.email
        hidden_elements['password'] = self.password

        return hidden_elements

    def get_activities_month(self, month, year=None):
        year = year or str(datetime.today().year)

        startDate = "{month}-01-{year}".format(month=month, year=year)
        payload = {"userName": self.hidden_username, "startDate":startDate}
        url = "{site}/activitiesByDateRange".format(site=self.site)
        request = self.session.get(url, params=payload)
        activities = json.loads(request.text)['activities']

        if not activities:
            raise NoActivityInMonth

        return [Activity(activity) for activity in activities[year][month]]


    @property
    def hidden_username(self):
        url = "{site}/home".format(site=self.site)
        auth = self.session.get(url)
        soup = bfs(auth.text, "html.parser")
        h_user = soup.find('a', {'href':re.compile('/user/[a-zA-Z]|[0-9]/profile')})
        self.__hidden_username = h_user.attrs['href'].split('/')[2]

        return self.__hidden_username


class Activity(object):
    def __init__(self, info):
        self.info = info
        self.activity = ''
        self.username = ''
        self.distance = ''
        self.activity_id = ''
        self.distance_units = ''
        self.elapsed_time = ''
        self.live = ''
        self.caption = ''
        self.activity_type = ''
        self.date = ''
        self._parse()

    def _parse(self):
        self.date = datetime(int(self.info.get('year')),
                             int(self.info.get('monthNum')),
                             int(self.info.get('dayOfMonth')))
        self.username = self.info.get('username')
        self.distance = self.info.get('distance')
        self.activity_id = self.info.get('activity_id')
        self.distance_units = self.info.get('distanceUnits')
        self.elapsed_time = self.info.get('elapsedTime')
        self.live = self.info.get('live')
        self.caption = self.info.get('mainText')
        self.activity_type = self.info.get('type')

if __name__ == '__main__':
    runkeeper = Runkeeper(email, password)
    activities = runkeeper.get_activities_month("Apr", "2015")

    for activity in activities:
        print "Date: {date}".format(date=activity.date)
        print "Username: {username}".format(username=activity.username)
        print "Distance: {distance} {distance_units}".format(distance=activity.distance,
                                                             distance_units=activity.distance_units)
        print "Activity ID: {activity_id}".format(activity_id=activity.activity_id)
        print "Elapsed Time: {elapsed_time}".format(elapsed_time=activity.elapsed_time)
        print "Live Activity: {live}".format(live=activity.live)
        print "Caption: {caption}".format(caption=activity.caption)
        print "Activity Type: {activity_type}".format(activity_type=activity.activity_type)
        print ""



