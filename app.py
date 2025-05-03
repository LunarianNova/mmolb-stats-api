from flask import Flask, request, render_template, jsonify, redirect
from flask_cors import CORS
from sqlite_handler import *

app = Flask(__name__)
CORS(app)

