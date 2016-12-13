#!/usr/bin/env python


class InvalidAuthentication:
    def __init__(self):
        pass


class NoActivityInMonth:
    def __init__(self):
        pass


class EndpointConnectionError:
    def __init__(self):
        pass


class ProfileNotFound:
    def __init__(self):
        pass


class InvalidActivityId:
    def __init__(self):
        pass


class NoActivitiesFound:
    def __init__(self):
        pass


class NoActivityInYear:
    def __init__(self):
        pass


class ActivityTypeUnknown:
    def __init__(self):
        pass


class HiddenElementsNotFound:
    def __init__(self):
        pass


class NoActivityTypesFound:
    def __init__(self):
        pass


class ErrorParsingGPX:
    def __init__(self):
        pass


class NameSpaceInGPXnotFound:
    def __init__(self):
        pass


class ErrorUploadingTrack(Exception):
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return self.message


class UnknownFileType:
    def __init__(self):
        pass

