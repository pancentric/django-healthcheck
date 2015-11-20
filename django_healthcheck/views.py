import json
import psycopg2

from django.http import HttpResponse
from django.conf import settings
from django.db import connections
from elasticsearch import Elasticsearch
from django.test.client import Client
import newrelic.agent

import redis
from redis import ConnectionError

def what_to_check():
    try:
        elastic_search = settings.HEALTHCHECK_ELASTICSEARCH
    except:
        elastic_search = False

    try:
        database = settings.HEALTHCHECK_DATABASE
    except:
        database = False

    try:
        redis = settings.HEALTHCHECK_REDIS
    except:
        redis = False

    try:
        homepage = settings.HEALTHCHECK_HOMEPAGE
    except:
        homepage = False

    return elastic_search, database, redis, homepage


def healthcheckview(request):

    # Before we do anything, make sure that NewRelic will treat this
    # as a background task.
    newrelic.agent.set_background_task()

    # Set up variables
    statuses = {}
    status_code = 200

    # Inspect the settings file to see what we need to check the status of
    check_es, check_db, check_redis, homepage = what_to_check()

    # Do the checking
    if check_db:
        try:
            conn = connections['default']
            conn.cursor()
            statuses['Database'] = 'OK'
        except:
            status_code = 500
            statuses['Database'] = 'NOT OK'

    if check_es:
        es = Elasticsearch()
        if es.ping():
            statuses['ElasticSearch'] = 'OK'
        else:
            status_code = 500
            statuses['ElasticSearch'] = 'NOT OK'


    if check_redis:
        try:
            rs = redis.Redis('localhost')
            response = rs.client_list()
            statuses['Redis'] = 'OK'
        except redis.ConnectionError:
            status_code = 500
            statuses['Redis'] = 'NOT OK'

    if homepage:
        client = Client()
        try:
            response = client.get('/')
            statuses['Home page status'] = response.status_code
            if response.status_code != 200:
                status_code = 500
        except:
            status_code = 500
            statuses['Home page status'] = 'NOT OK'

    # Add the status code to the payload
    payload = {
        'status_code': status_code,
        }

    # Add all other data to the payload
    payload.update(statuses)

    # Return a response
    return HttpResponse(
        json.dumps(payload),
        status=status_code,
        content_type="application/json"
        )