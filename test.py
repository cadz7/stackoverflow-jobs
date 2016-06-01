#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
from flask import Flask
from flask import jsonify
from flask import request
import time
import math
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

handler = RotatingFileHandler('foo.log')
handler.setLevel(logging.INFO)
app.logger.addHandler(handler)

req = urllib2.Request("http://careers.stackoverflow.com/jobs/feed")
req.add_header("User-agent", "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_8_2) AppleWebKit/537.17 (KHTML, like Gecko) Chrome/24.0.1309.0 Safari/537.17")
# with open('testDump.json') as data_file:    
#   data = json.load(data_file)

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

def fetch_jobs():
    print("fetch jobs called!" )
    try:
      count_added = 0
      res = urllib2.urlopen(req)
      # convert the xml feed to json
      dump = json.dumps(xmltodict.parse(res)["rss"]["channel"]["item"], indent=4)
      #Load the data in json format
      json_data = json.loads(dump)
      print stackoverflow.find({}).count()
      print len(json_data)
      for job in json_data:
        if(stackoverflow.find({"title" : job["title"] }).count() == 0):
          # Do the magic here
          s = MLStripper()
          s.feed(job["description"])
          clean_data = s.get_data()

          job["description"] = clean_data.strip(' \t\n\r')
          # Removes \n from string
          job["description"] = job["description"].replace('\n', '')
          # Replaces whitespace in between words with single space.
          job["description"] = ' '.join(job["description"].split())

          stackoverflow.insert(job)
          count_added += 1
          print count_added
        else:
          print "job already in db" + str(job["link"])
          pass
      app.logger.info(str(count_added) + " jobs added")
    except Exception, e:
      print e


scheduler = BackgroundScheduler()
scheduler.add_job(fetch_jobs, 'interval', seconds=10)
scheduler.start()

################ Routes ################

@app.errorhandler(500)
def internal_error(exception):
  app.logger.exception(exception)
  return exception

@app.route('/')
def hello_world():
  return 'Hi! This is API to fetch job listings posted on Stackoverflow Careers.'

@app.route('/jobs', methods=['GET'])
def fetch_job_listings():
  # Pages start with 0
  page = request.args.get('page')
  if page == None:
    page = 1
  jobs_count = stackoverflow.find({}).count()
  if (page < str(math.ceil(float(jobs_count)/50))):
    jobs = stackoverflow.find({}).sort('a10:updated', -1).skip(int(page)*50).limit(50)
    app.logger.info('jobs called')
    return dumps(jobs, indent=4)
  else:
    return '[]'

@app.route('/count', methods=['GET'])
def job_listings_count():
  app.logger.info('job listings count method called')
  jobs_count = stackoverflow.find({}).count()
  return str(jobs_count)


if __name__ == '__main__':
  app.run(debug=True, use_reloader=False)