# Description
Python library to get RK user data

# Contributing
```bash
$ git clone https://github.com/wefner/runkeeper.git
$ mkvirtualenv runkeeper
$ pip install -r requirements.txt
```

# Catches
For simplicity and a pinch of privacy, it is suggested to add your **runkeeper** `password` into your Keychain. You can
always replace it for your plain password as a string.
`email` should be filled accordingly as well.

# Usage
## Basic
```python
from runkeeper import Runkeeper
import keyring

email = "your@email.com"
password = keyring.get_password("runkeeper", email) or "MyPassword"

runkeeper = Runkeeper(email, password)
```

## Methods
```python
# Month is in abbreviated format. Year is an optional argument. Defaults to current year.
month_activities = runkeeper.get_activities_month("May", "2016")
for activity in month_activities:
    print "Datetime: {}".format(activity.datetime)
    print "Username: {}".format(activity.username)
    print "Distance: {} {}".format(activity.distance, activity.distance_units)
    print "Activity ID: {}".format(activity.activity_id)
    print "Elapsed Time: {}".format(activity.elapsed_time)
    print "Live Activity: {}".format(activity.live)
    print "Caption: {}".format(activity.caption)
    print "Activity Type: {}".format(activity.activity_type)
    print "Calories Burned: {}".format(activity.calories)
    print "Average Pace: {} min/{}".format(activity.pace, activity.distance_units)
    print "Average Speed: {} {}/h".format(activity.speed, activity.distance_units)
    print "Elevation Climb: {}".format(activity.elevation)
    print ""
```

```python
# All activity objects in year will be returned in a list
year_activities = runkeeper.get_activities_year("2015")
for month, month_activities in year_activities.iteritems():
    print "Month: {}".format(month)
    for activity in month_activities:
        print "\tDatetime: {}".format(activity.datetime)
        print "\tUsername: {}".format(activity.username)
        print "\tDistance: {} {}".format(activity.distance, activity.distance_units)
        print "\tActivity ID: {}".format(activity.activity_id)
        print "\tElapsed Time: {}".format(activity.elapsed_time)
        print "\tLive Activity: {}".format(activity.live)
        print "\tCaption: {}".format(activity.caption)
        print "\tActivity Type: {}".format(activity.activity_type)
        print "\tCalories Burned: {}".format(activity.calories)
        print "\tAverage Pace: {} min/{}".format(activity.pace, activity.distance_units)
        print "\tAverage Speed: {} {}/h".format(activity.speed, activity.distance_units)
        print "\tElevation Climb: {}".format(activity.elevation)
        print ""
```

```python
# Upload GPX activity
runkeeper.create_new_activity('RUN', '/my_files/Morning_Run.gpx')
```

### Activity Types
```
['RUN', 'WALK', 'BIKE', 'SWIMMING', 'ELLIPTICAL', 'STRENGTH_TRAINING', 'CIRCUIT_TRAINING', 'CORE_STRENGTHENING',
 'ARC_TRAINER', 'ROWING', 'HIKE', 'MOUNTAINBIKE', 'SKATE', 'NORDIC_WALKING', 'XC_SKI', 'DH_SKI', 'SNOWBOARD',
 'WHEELCHAIR', 'YOGA', 'PILATES', 'CROSSFIT', 'SPINNING', 'ZUMBA', 'BARRE', 'GROUP_WORKOUT', 'DANCE', 'BOOTCAMP',
 'BOXING_MMA', 'MEDITATION', 'STAIRMASTER_STEPWELL', 'SPORTS', 'OTHER']
 ```

### Other objects
```python
# Export activities for month. Example:
# GPX = GPS-XML
# KML = Google Earth
activities = runkeeper.get_activities_month("Jan", "2015")
for activity in activities:
    kml_activity = open("activity-{datetime}.kml".format(datetime=activity.datetime), 'w')
    kml_activity.write(activity.kml_data)
```
