#!/usr/bin/env python
# -*- coding: utf-8 -*-

from flask import Flask
import random
import json

app = Flask(__name__)

@app.route('/')
def index():
    return json.dumps([random.randint(0,100000) for r in xrange(1000)])

@app.route('/lucky-number-<int:number>/')
def lucky_number(number):
    return 'Your lucky number is %d' % number


if __name__ == '__main__':
    app.run(debug=True)
