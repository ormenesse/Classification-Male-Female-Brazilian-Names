from flask import Flask, request, redirect, url_for, flash, jsonify, abort
import pandas as pd
from lf_functions import *
import gc

app = Flask(__name__)
CORS(app) #Prevents CORS errors

@app.route('/etls/<legalName>/<legalRepresentatives>', methods=['GET'])

def lid_fem_class(legalName,legalRepresentatives):

    gc.collect()

    leg_rep = legalRepresentatives
    leg_name = legalName

    vogais = ['A','a','E','e','I','i','O','o','U','u']

        if leg_rep!=leg_rep:
            u = leg_name.split()[0]
            if len(u)>1 and '.' not in u and any(v in u for v in vogais):
                lid_fem = lid_fem(u)
            else:
                lid_fem = np.nan
        else:
            for x in leg_rep.split(','):
                u = x.split('-')[1].split()[0]
                if len(u)>1 and '.' not in u and any(v in u for v in vogais):
                    lid_fem = lid_fem(u)
                else:
                    lid_fem = np.nan
    
    return jsonify({'legalName' : leg_name, 'legalRepresentatives' : leg_rep, 'liderançaFeminina' : lid_fem})

    if __name__ == '__main__':
    app.run(host='0.0.0.0')