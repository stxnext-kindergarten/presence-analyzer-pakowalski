# -*- coding: utf-8 -*-
"""
Defines views.
"""

import calendar
import mako
from flask import abort, redirect
from flask.ext.mako import render_template

from presence_analyzer.main import app
from presence_analyzer.utils import (
    get_data,
    group_by_weekday,
    group_start_end_weekday,
    group_top5_weeks,
    jsonify,
    mean,
    users_xmldata
)

import logging
log = logging.getLogger(__name__)  # pylint: disable=invalid-name


@app.route('/')
def mainpage():
    """
    Redirects to front page.
    """
    return redirect('/presence_weekday.html')


@app.route('/api/v1/users', methods=['GET'])
@jsonify
def users_view():
    """
    Users listing for dropdown.
    """
    data = get_data()
    return [
        {'user_id': i, 'name': 'User {0}'.format(str(i))}
        for i in data.keys()
    ]


@app.route('/api/v2/users', methods=['GET'])
@jsonify
def users_xml():
    """
    Users listing from XML file.
    """
    data = users_xmldata()
    return data


@app.route('/api/v2/users/<int:user_id>', methods=['GET'])
@jsonify
def users_xml_view(user_id):
    """
    Returns mean presence time of given user grouped by weekday.
    """
    data = users_xmldata()
    data = dict(data)
    if (str(user_id)) not in data:
        log.debug('User %s not found!', user_id)
        abort(404)

    return data[str(user_id)]


@app.route('/api/v1/mean_time_weekday/<int:user_id>', methods=['GET'])
@jsonify
def mean_time_weekday_view(user_id):
    """
    Returns mean presence time of given user grouped by weekday.
    """
    data = get_data()
    if user_id not in data:
        log.debug('User %s not found!', user_id)
        abort(404)

    weekdays = group_by_weekday(data[user_id])
    result = [
        (calendar.day_abbr[weekday], mean(intervals))
        for weekday, intervals in enumerate(weekdays)
    ]

    return result


@app.route('/api/v1/presence_weekday/<int:user_id>', methods=['GET'])
@jsonify
def presence_weekday_view(user_id):
    """
    Returns total presence time of given user grouped by weekday.
    """
    data = get_data()
    if user_id not in data:
        log.debug('User %s not found!', user_id)
        abort(404)

    weekdays = group_by_weekday(data[user_id])
    result = [
        (calendar.day_abbr[weekday], sum(intervals))
        for weekday, intervals in enumerate(weekdays)
    ]

    result.insert(0, ('Weekday', 'Presence (s)'))
    return result


@app.route('/api/v1/presence_start_end/<int:user_id>', methods=['GET'])
@jsonify
def presence_start_end_view(user_id):
    """
    Returns interval from start to end work.
    """
    data = get_data()
    if user_id not in data:
        log.debug('User %s not found!', user_id)
        abort(404)

    weekdays = group_start_end_weekday(data[user_id])

    for day in weekdays:
        day['start'] = mean(day['start'])
        day['end'] = mean(day['end'])

    result = [
        (calendar.day_abbr[weekday], value['start'], value['end'])
        for weekday, value in enumerate(weekdays)
    ]
    return result


@app.route('/api/v1/top5/<int:user_id>', methods=['GET'])
@jsonify
def top5_weeks_view(user_id):
    """
    Returns top 5 weeks in work.
    """
    data = get_data()
    if user_id not in data:
        log.debug('User %s not found!', user_id)
        abort(404)

    weekdays = group_top5_weeks(data[user_id])
    result = sorted(weekdays.items(), key=lambda x: x[1], reverse=True)

    return result[0:5]


@app.route('/<string:temp_name>', methods=['GET'])
def render_all(temp_name):
    """
    Render templates.
    """
    try:
        return render_template(temp_name, selected=temp_name)
    except mako.exceptions.TopLevelLookupException:
        abort(404)
