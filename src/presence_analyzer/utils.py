# -*- coding: utf-8 -*-
"""
Helper functions used in views.
"""

import csv
from datetime import datetime, timedelta
from functools import wraps
from json import dumps
from lxml import etree
from threading import Lock

from flask import Response

from presence_analyzer.main import app

import logging
log = logging.getLogger(__name__)  # pylint: disable=invalid-name


CACHE = {}


def cache(seconds):
    """
    Cache specified function.
    """
    lock = Lock()

    def _cache(function):
        def __cache(*args):
            func_name = function.__name__
            sec = timedelta(seconds=seconds)
            check = (
                func_name in CACHE and
                datetime.now() < CACHE[func_name]['time'] + sec
            )
            with lock:
                if check:
                    return CACHE[func_name]['result']

                result = function(*args)
                CACHE[func_name] = {
                    'time': datetime.now(),
                    'result': result
                }
                return result
        return __cache
    return _cache


def jsonify(function):
    """
    Creates a response with the JSON representation of wrapped function result.
    """
    @wraps(function)
    def inner(*args, **kwargs):
        """
        This docstring will be overridden by @wraps decorator.
        """
        return Response(
            dumps(function(*args, **kwargs)),
            mimetype='application/json'
        )
    return inner


def users_xmldata():
    """
    Extracts data from XML file and groups it by user_name.
    """
    data = {}
    with open(app.config['DATA_XML'], 'r') as xml_file:
        for event, element in etree.iterparse(xml_file, tag='server'):
            protocol = element.findtext('protocol')
            host = element.findtext('host')
            port = element.findtext('port')
        xml_file.seek(0)
        for event, element in etree.iterparse(xml_file, tag='user'):
            if element.tag == 'user':
                user_id = element.attrib.get('id')
            image = element.findtext('avatar')
            link_to_avatar = '{}://{}:{}{}'.format(protocol, host, port, image)
            user_name = element.findtext('name')
            user_name = user_name.encode('utf-8')

            data[user_id] = {
                'user_name': user_name,
                'link_to_avatar': link_to_avatar,
            }

    return data


@cache(600)
def get_data():
    """
    Extracts presence data from CSV file and groups it by user_id.

    It creates structure like this:
    data = {
        'user_id': {
            datetime.date(2013, 10, 1): {
                'start': datetime.time(9, 0, 0),
                'end': datetime.time(17, 30, 0),
            },
            datetime.date(2013, 10, 2): {
                'start': datetime.time(8, 30, 0),
                'end': datetime.time(16, 45, 0),
            },
        }
    }
    """
    data = {}
    with open(app.config['DATA_CSV'], 'r') as csvfile:
        presence_reader = csv.reader(csvfile, delimiter=',')
        for i, row in enumerate(presence_reader):
            if len(row) != 4:
                # ignore header and footer lines
                continue

            try:
                user_id = int(row[0])
                date = datetime.strptime(row[1], '%Y-%m-%d').date()
                start = datetime.strptime(row[2], '%H:%M:%S').time()
                end = datetime.strptime(row[3], '%H:%M:%S').time()
            except (ValueError, TypeError):
                log.debug('Problem with line %d: ', i, exc_info=True)

            data.setdefault(user_id, {})[date] = {'start': start, 'end': end}

    return data


def group_by_weekday(items):
    """
    Groups presence entries by weekday.
    """
    result = [[], [], [], [], [], [], []]  # one list for every day in week
    for date in items:
        start = items[date]['start']
        end = items[date]['end']
        result[date.weekday()].append(interval(start, end))
    return result


def seconds_since_midnight(time):
    """
    Calculates amount of seconds since midnight.
    """
    return time.hour * 3600 + time.minute * 60 + time.second


def interval(start, end):
    """
    Calculates inverval in seconds between two datetime.time objects.
    """
    return seconds_since_midnight(end) - seconds_since_midnight(start)


def mean(items):
    """
    Calculates arithmetic mean. Returns zero for empty lists.
    """
    return float(sum(items)) / len(items) if len(items) > 0 else 0


def group_start_end_weekday(items):
    """
    Interval from start to finish work.
    """
    result = []
    for x in range(7):
        result.append({'start': [], 'end': []})

    for date in items:
        start = items[date]['start']
        end = items[date]['end']
        result[date.weekday()]['start'].append(seconds_since_midnight(start))
        result[date.weekday()]['end'].append(seconds_since_midnight(end))

    return result


def group_top5_weeks(items):
    """
    Sum hours of top weeks.
    """
    value = {}
    result = {}

    for date in items:
        day_of_week = date.weekday()
        start_week = date - timedelta(days=day_of_week)
        end_week = date + timedelta(days=6 - day_of_week)
        string = "{} - {}".format(start_week, end_week)

        try:
            if value[string]:
                continue
        except KeyError:
            value[string] = 0

        for day in([start_week + timedelta(days=days) for days in range(7)]):
            if day in items:
                start = items[day]['start']
                end = items[day]['end']
                result[day.weekday()] = interval(start, end)
                value[string] += result[day.weekday()]

    return value
