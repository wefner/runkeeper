#!/usr/bin/env python

from bs4 import BeautifulSoup as bfs
from runkeeperExceptions import *
from haversine import haversine
from datetime import datetime
from requests import Session, utils
import xml.etree.ElementTree as ET
import calendar
import json
import re


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
        hidden_elements = self.__get_hidden_elements('login')
        hidden_elements['email'] = self.email
        hidden_elements['password'] = self.password
        try:
            valid_authentication = self.session.post(url, data=hidden_elements)
        except:
            raise EndpointConnectionError

        if not valid_authentication.cookies.get('checker'):
            raise InvalidAuthentication

        return True

    def __get_hidden_elements(self, endpoint):
        """
        Retrieve all <hidden> parameters from requested form
        :return: dict
        """
        url = "{site}/{endpoint}".format(site=self.site,
                                         endpoint=endpoint)
        try:
            endpoint_form = self.session.get(url)
        except:
            raise EndpointConnectionError

        soup = bfs(endpoint_form.text, "html.parser")

        try:
            form = soup.find_all('input', {'type': 'hidden'})
        except:
            raise HiddenElementsNotFound

        hidden_elements = {element.attrs['name']: element.attrs['value'] for element in form}

        return hidden_elements

    @property
    def profile_username(self):
        """
        Get profile username or ID once logged in by using Session object
        :return: str
        """
        if not self.__profile_username:
            url = "{site}/home".format(site=self.site)
            try:
                home = self.session.get(url)
            except:
                raise EndpointConnectionError

            soup = bfs(home.text, "html.parser")
            profile_url = soup.find('a', {'href': re.compile('/user/[a-zA-Z]|[0-9]/profile')})

            try:
                self.__profile_username = profile_url.attrs['href'].split('/')[2]
            except IndexError:
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

        if int(year) > datetime.today().year:
            raise NoActivityInYear

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
            activity_details.append(activity)

        return [Activity(self, activity) for activity in activity_details]

    def get_activities_year(self, year):
        """
        Gets as many months that have activities in a year
        :param year: string
        :return: dictionary. Key is the month. Value is a list of month activity objects
        """
        months_abbr = [calendar.month_abbr[month] for month in range(1, 13)]
        valid_months = months_abbr[:datetime.today().month] if int(year) >= datetime.today().year else months_abbr
        year_activities = {}

        for month in valid_months:
            try:
                month_activities = self.get_activities_month(month, year)
            except (NoActivityInMonth, NoActivitiesFound):
                month_activities = []

            year_activities[month] = month_activities

        return year_activities

    def create_new_activity(self, activity_type, activity_file=None):
        activity_type = activity_type.upper()
        url = '{site}/new/activity'.format(site=self.site)

        with open(activity_file, 'r') as myfile:
            data_str = myfile.read().replace('\n', '')
        files = {'trackFile': (activity_file, open(activity_file, 'rb'), 'multipart/form-data')}
        try:
            new_activity_form = self.session.get(url)
        except:
            raise EndpointConnectionError

        soup = bfs(new_activity_form.text, "html.parser")
        activities_form = soup.find_all('li', {'class': 'activityTypeItem'})
        activity_types = [act_type.attrs['data-value'] for act_type in activities_form]
        hidden_elements = self.__get_hidden_elements('new/activity')

        if not activity_types:
            raise NoActivityTypesFound

        if activity_type not in activity_types:
            raise ActivityTypeUnknown

        hidden_elements['activityType'] = activity_type
        hidden_elements.update(self.__populate_activity_gpx(activity_file))

        file_hidden_elements = {k: v for k, v in hidden_elements.iteritems()}
        file_hidden_elements['trackFile'] = data_str
        file_hidden_elements['heartRateGraphJson'] = ''
        file_hidden_elements['route'] = ''
        file_hidden_elements['averageHeartRate'] = ''
        file_hidden_elements['hrmFile'] = ''
        file_hidden_elements['activityViewableBy'] = ''
        file_hidden_elements['calories'] = ''
        file_hidden_elements['notes'] = ''

        if activity_file.endswith('.gpx'):
            file_hidden_elements['uploadType'] = '.gpx'
        else:
            raise UnknownFileType
        try:
            if self.upload_activity(activity_file):
                new_activity_post = self.session.post(url, data=file_hidden_elements, files=files)
                return new_activity_post
        except Exception as e:
            raise ErrorUploadingTrack(e)

    def upload_activity(self, activity_file):
        track_params = {}

        if activity_file.endswith('.gpx'):
            track_params['uploadType'] = '.gpx'
        else:
            raise UnknownFileType

        files = {'trackFile': (activity_file, open(activity_file, 'rb'), 'multipart/form-data')}

        url = "{site}/trackFileUpload".format(site=self.site)
        try:
            track_upload = self.session.post(url, data=track_params, files=files)
        except:
            raise EndpointConnectionError

        upload_response = json.loads(track_upload.text)

        # Fix this
        if upload_response['error']:
            raise ErrorUploadingTrack

        if track_upload.ok:
            return True

        return False

    def __populate_activity_gpx(self, gpx_file):
        gpx_params = {}
        gpx_details = self.__parse_gpx(gpx_file)
        start = datetime.strptime(sorted(gpx_details['times'])[0], '%Y-%m-%dT%H:%M:%SZ')
        end = datetime.strptime(sorted(gpx_details['times'])[-1], '%Y-%m-%dT%H:%M:%SZ')
        duration = end - start
        duration = str(duration).split(':')

        gpx_params['uploadType'] = '.gpx'
        gpx_params['durationHours'] = "{0:02d}".format(int(duration[0]))
        gpx_params['durationMinutes'] = "{0:02d}".format(int(duration[1]))
        gpx_params['durationSeconds'] = "{0:02d}".format(int(duration[2]))
        gpx_params['importFormat'] = 'gpx'
        gpx_params['startHour'] = "{0:02d}".format(int(start.hour))
        gpx_params['startMinute'] = "{0:02d}".format(int(start.minute))
        gpx_params['distance'] = "{0:.2f}".format(self.__calculate_haversine(gpx_details['coordinates']))
        gpx_params['startTimeString'] = "{:%Y/%m/%d %H:%M:%S.000}".format(start)

        return gpx_params

    def __parse_gpx(self, gpx_file):
        # Find a better way..
        url_pattern = 'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'

        activity_times = []
        coordinates = []
        gpx_details = {}

        with open(gpx_file, 'r') as f:
            upload_gpx = f.read().replace('\n', '')

        root = ET.fromstring(upload_gpx)
        try:
            # GPX input has namespaces
            xmlns = re.findall(url_pattern, root.tag)
            xmlns = ''.join(xmlns)
            ns = {'gpx': xmlns}
        except:
            raise NameSpaceInGPXnotFound

        try:
            for trk in root.find('gpx:trk', ns):
                for trkpt in trk.findall('gpx:trkpt', ns):
                    coordinates.append((trkpt.attrib['lat'], trkpt.attrib['lon']))
                    for time in trkpt.findall('gpx:time', ns):
                        activity_times.append(time.text)
        except:
            raise ErrorParsingGPX

        gpx_details['coordinates'] = coordinates
        gpx_details['times'] = activity_times

        return gpx_details

    def __calculate_haversine(self, coordinates):
        coordinates_float = [(float(lat), float(lon)) for lat, lon in coordinates]

        total_distance = 0
        for coordinate in range(len(coordinates_float) - 1):
            two_distances = haversine(coordinates_float[coordinate], coordinates_float[coordinate + 1])
            total_distance += two_distances

        return total_distance


class Activity(object):
    def __init__(self, runkeeper_instance, info):
        self._runkeeper = runkeeper_instance
        self.session = runkeeper_instance.session
        try:
            self.username = info.get('username')
            self.distance = info.get('distance')
            self.activity_id = info.get('activity_id')
            self.distance_units = info.get('distanceUnits')
            self.elapsed_time = info.get('elapsedTime')
            self.live = info.get('live')
            self.caption = info.get('mainText')
            self.activity_type = info.get('type')
            self.__statsCalories = None
            self.__statsElevation = None
            self.__statsPace = None
            self.__statsSpeed = None
            self.__datetime = None
            self.__gpx_data = None
            self.__kml_data = None
        except KeyError:
            raise InvalidActivityId

    def _populate_details(self):
        """
        Stores activity value as object from dictionary key.
        Different endpoints so required if only needed.
        """
        activity_details = self.get_activity_details(self.activity_id)
        self.__statsCalories = activity_details.get('statsCalories')
        self.__statsElevation = activity_details.get('statsElevation')
        self.__statsPace = activity_details.get('statsPace')
        self.__statsSpeed = activity_details.get('statsSpeed')

    def _populate_gpx_export(self):
        self.__gpx_data = self.export_activity(self.activity_id, 'gpx')

    def _populate_googleEarth_export(self):
        self.__kml_data = self.export_activity(self.activity_id, 'googleEarth')

    def _populate_datetime(self):
        self.__datetime = self.get_activity_datetime(self.activity_id)

    def get_activity_details(self, activity_id):
        """
        Returns other useful information from a particular activity
        :param activity_id: String
        :return: JSON Object
        """
        url = "{site}/ajax/pointData".format(site=self._runkeeper.site)
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

    @property
    def calories(self):
        if not self.__statsCalories:
            self._populate_details()
        return self.__statsCalories

    @property
    def elevation(self):
        if not self.__statsElevation:
            self._populate_details()
        return self.__statsElevation

    @property
    def pace(self):
        if not self.__statsPace:
            self._populate_details()
        return self.__statsPace

    @property
    def speed(self):
        if not self.__statsSpeed:
            self._populate_details()
        return self.__statsSpeed

    def get_activity_datetime(self, activity_id):
        """
        :param activity_id: String
        :return: datetime object.
        """
        url = "{site}/user/{profile}/activity/{activity_id}".format(site=self._runkeeper.site,
                                                                    profile=self._runkeeper.profile_username,
                                                                    activity_id=activity_id)
        try:
            activity_datetime_session = self.session.get(url)
        except:
            raise EndpointConnectionError

        soup = bfs(activity_datetime_session.text, "html.parser")
        form = soup.find('div', {'class': 'micro-text activitySubTitle'})

        activity_datetime = [date_params.split('-')[0].rstrip() for date_params in form]
        activity_datetime = (''.join(activity_datetime))
        activity_datetime = datetime.strptime(activity_datetime, '%a %b %d %H:%M:%S %Z %Y')

        return activity_datetime

    @property
    def datetime(self):
        if not self.__datetime:
            self._populate_datetime()
        return self.__datetime

    def export_activity(self, activity_id, data_type):
        """
        Activity details as exportable in text format.
        Warning: Long output
        :param activity_id: string
        :param data_type: 'kml' for GoogleEarth. 'gpx' for GPS-XML schema
        :return: text of such file
        """
        url = "{site}/download/activity".format(site=self._runkeeper.site)
        params = {'activityId': activity_id, 'downloadType': data_type}
        try:
            exported_activity = self.session.get(url, params=params)
        except:
            raise EndpointConnectionError

        return exported_activity.text

    @property
    def gpx_data(self):
        if not self.__gpx_data:
            self._populate_gpx_export()
        return self.__gpx_data

    @property
    def kml_data(self):
        if not self.__kml_data:
            self._populate_googleEarth_export()
        return self.__kml_data


