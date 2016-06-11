#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import math
from flask import Flask
from flask import jsonify
from flask import request
import time
import xmltodict, json
import urllib2
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from pymongo import MongoClient
from bson.json_util import dumps
import logging
from HTMLParser import HTMLParser
from logging.handlers import RotatingFileHandler

from flask.ext.cors import CORS  # The typical way to import flask-cors


app = Flask(__name__)
CORS(app)

try:
  client = MongoClient(DB_STR)
  db = client['jobs-api']
  stackoverflow = db["stackoverflow-careers"]
except Exception, e:
  print e

class MLStripper(HTMLParser):
    def __init__(self):
        self.reset()
        self.fed = []
    def handle_data(self, d):
        self.fed.append(d)
    def get_data(self):
        return ''.join(self.fed)

print 'init has been run'

################ Routes ################

@app.errorhandler(500)
def internal_error(exception):
  app.logger.exception(exception)
  return exception

@app.route('/')
def hello_world():
  app.logger.info('hello called')
  return 'Hello! This is a test api developedby Rick Shukla.'

@app.route('/jobs', methods=['GET'])
def fetch_job_listings():
  page = request.args.get('page')
  jobs_count = stackoverflow.find({}).count()
  if (page < str(math.ceil(float(jobs_count)/50))):
    jobs = stackoverflow.find({}).sort('a10:updated', -1).skip(int(page)*50).limit(50)
    app.logger.info('jobs called')
    return dumps(jobs, indent=4)
  else:
    return '[]'
  # return 'ok'

@app.route('/count', methods=['GET'])
def job_listings_count():
  app.logger.info('job listings count method called')
  jobs_count = stackoverflow.find({}).count()
  return str(jobs_count)


if __name__ == '__main__':
  app.run(debug=True, use_reloader=False)