#!/usr/bin/env python

import keyring
import logging
import re
import json
from requests import Session
from bs4 import BeautifulSoup as bfs
from datetime import datetime
from runkeeperExceptions import InvalidAuhentication, NoActivityInMonth, EndpointConnectionError, ProfileNotFound, InvalidActivityId, NoActivitiesFound

email = ""
password = keyring.get_password("runkeeper", email)

logger = logging.basicConfig(level=logging.DEBUG)


class Runkeeper(object):
    def __init__(self, email, password):
        self.email = email
        self.password = password
        self.session = Session()
        self.site = 'https://runkeeper.com'
        self.__profile_username = ''
        self.__authenticate()

    def __authenticate(self):
        """
        Send all POST parameters and check for login validation cookie
        :return: bool
        """
        url = "{site}/login".format(site=self.site)
        try:
            valid_authentication = self.session.post(url, data=self.__get_hidden_elements())
        except:
            raise EndpointConnectionError

        if not valid_authentication.cookies.get('checker'):
            raise InvalidAuhentication

        return True

    def __get_hidden_elements(self):
        """
        Retrieve all POST parameters
        :return: dict
        """
        data = {'password': self.password, 'email': self.email}
        url = "{site}/login".format(site=self.site)
        try:
            hidden_session = self.session.post(url, data=data)
        except:
            raise EndpointConnectionError

        soup = bfs(hidden_session.text, "html.parser")
        form = soup.find_all('input', {'type': 'hidden'})
        hidden_elements = {element.attrs['name']: element.attrs['value'] for element in form}
        hidden_elements['email'] = self.email
        hidden_elements['password'] = self.password

        return hidden_elements

    @property
    def profile_username(self):
        """
        Get profile username or ID once logged in by using Session object
        :return: str
        """
        url = "{site}/home".format(site=self.site)
        try:
            home = self.session.get(url)
        except:
            raise EndpointConnectionError

        soup = bfs(home.text, "html.parser")
        profile_url = soup.find('a', {'href': re.compile('/user/[a-zA-Z]|[0-9]/profile')})

        self.__profile_username = profile_url.attrs['href'].split('/')[2]

        if not self.__profile_username:
            raise ProfileNotFound

        return self.__profile_username

    def get_activities_month(self, month, year=None):
        """
        Get activities in specified month and year
        :param month: str (month abbreviated)
        :param year: str (YYYY)
        :return: Activity object
        """
        activity_details = []
        year = year or str(datetime.today().year)

        start_date = "{month}-01-{year}".format(month=month, year=year)
        payload = {"userName": self.profile_username, "startDate": start_date}
        url = "{site}/activitiesByDateRange".format(site=self.site)

        try:
            activities_month_request = self.session.get(url, params=payload)
        except:
            raise EndpointConnectionError

        try:
            activities_month = json.loads(activities_month_request.text)['activities']
        except:
            raise NoActivitiesFound

        if not activities_month:
            raise NoActivityInMonth

        for activity in activities_month[year][month]:
            activity['details'] = self.get_activity_details(activity['activity_id'])
            activity['datetime'] = self.get_activity_datetime(activity['activity_id'])
            activity_details.append(activity)

        return [Activity(activity) for activity in activity_details]

    def get_activity_datetime(self, activity_id):
        """
        :param activity_id: String
        :return: Locale appropriate date and time representation.
        """
        url = "{site}/user/{profile}/activity/{activity_id}".format(site=self.site,
                                                                    profile=self.profile_username,
                                                                    activity_id=activity_id)
        try:
            activity_datetime_session = self.session.get(url)
        except:
            raise EndpointConnectionError

        soup = bfs(activity_datetime_session.text, "html.parser")
        form = soup.find('div', {'class': 'micro-text activitySubTitle'})
        activity_datetime = [date_params.split('-')[0].rstrip() for date_params in form]
        activity_datetime = (''.join(activity_datetime))

        return activity_datetime

    def get_activity_details(self, activity_id):
        """
        Returns other useful information from a particular activity
        :param activity_id: String
        :return: JSON Object
        """
        url = "{site}/ajax/pointData".format(site=self.site)
        activity_params = {"activityId": activity_id}
        try:
            activity_request = self.session.get(url, params=activity_params)
        except:
            raise EndpointConnectionError

        try:
            activity_details = json.loads(activity_request.text)
        except:
            raise InvalidActivityId

        return activity_details

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
        self.datetime = ''
        self.calories = ''
        self.pace = ''
        self.speed = ''
        self.elevation = ''
        self._parse()

    def _parse(self):
        """
        Stores activity value as object from dictionary key in a variable
        """
        self.datetime = datetime.strptime(self.info.get('datetime'), '%a %b %d %H:%M:%S %Z %Y')
        self.username = self.info.get('username')
        self.distance = self.info.get('distance')
        self.activity_id = self.info.get('activity_id')
        self.distance_units = self.info.get('distanceUnits')
        self.elapsed_time = self.info.get('elapsedTime')
        self.live = self.info.get('live')
        self.caption = self.info.get('mainText')
        self.activity_type = self.info.get('type')
        self.calories = self.info.get('details', {}).get('statsCalories')
        self.pace = self.info.get('details', {}).get('statsPace')
        self.speed = self.info.get('details', {}).get('statsSpeed')
        self.elevation = self.info.get('details', {}).get('statsElevation')

if __name__ == '__main__':
    runkeeper = Runkeeper(email, password)
    activities = runkeeper.get_activities_month("Apr", "2015")

    for activity in activities:
        print "Datetime: {datetime}".format(datetime=activity.datetime)
        print "Username: {username}".format(username=activity.username)
        print "Distance: {distance} {distance_units}".format(distance=activity.distance,
                                                             distance_units=activity.distance_units)
        print "Activity ID: {activity_id}".format(activity_id=activity.activity_id)
        print "Elapsed Time: {elapsed_time}".format(elapsed_time=activity.elapsed_time)
        print "Live Activity: {live}".format(live=activity.live)
        print "Caption: {caption}".format(caption=activity.caption)
        print "Activity Type: {activity_type}".format(activity_type=activity.activity_type)
        print "Calories Burned: {calories}".format(calories=activity.calories)
        print "Average Pace: {avg_pace} min/{distance_units}".format(avg_pace=activity.pace,
                                                                     distance_units=activity.distance_units)
        print "Average Speed: {avg_speed} {distance_units}/h".format(avg_speed=activity.speed,
                                                                     distance_units=activity.distance_units)
        print "Elevation Climb: {elevation}".format(elevation=activity.elevation)
        print ""
