from flask import Flask, request, redirect, url_for, flash, jsonify, abort
import pandas as pd
from lf_functions import *
import gc

app = Flask(__name__)
#CORS(app) #Prevents CORS errors

@app.route('/lidfem', methods=['GET'])

def lid_fem_class():

    gc.collect()
    
    return lid_class(request)

if __name__ == '__main__':
    
    app.run(host='localhost')