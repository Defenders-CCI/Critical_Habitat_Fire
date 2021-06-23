# -*- coding: utf-8 -*-
"""
Created on Wed Jun 16 14:55:22 2021

@author: MEvans
"""

from flask import Flask
app = Flask(__name__)

@app.route("/")
def hello():
    return "<h1 style='color:blue'>Hello There!</h1>"

if __name__ == "__main__":
    app.run(host = '0.0.0.0')
