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
```python
from runkeeper import Runkeeper
import keyring

email = "your@email.com"
password = keyring.get_password("runkeeper", email)

runkeeper = Runkeeper(email, password)
# Month is in abbreviated format. Year is an optional argument. Defaults to current year.
activities = runkeeper.get_activities_month("May", "2016")

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
```
