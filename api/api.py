import flask
from flask import request   # wird benötigt, um die HTTP-Parameter abzufragen
from flask import jsonify   # übersetzt python-dicts in json
import sqlite3
import random
import string
import urllib.parse

app = flask.Flask(__name__)
app.config["DEBUG"] = True  # Zeigt Fehlerinformationen im Browser, statt nur einer generischen Error-Message


def generate_pin():
    return ''.join(random.choices(string.digits, k=4))


def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d


@app.route('/', methods=['GET'])
def home():
    return "<h1>Tischreservierung</h1>"


@app.route('/api/res/', methods=['GET'])
def api_res():
    conn = sqlite3.connect('../buchungssystem.sqlite')
    conn.row_factory = dict_factory
    cur = conn.cursor()
    all_books = cur.execute('SELECT * FROM reservierungen;').fetchall()

    return jsonify(all_books)


@app.route('/api/res/create', methods=['GET'])
def api_res_create():
    # example url: 127.0.0.1:5000/api/tische/free?zeitpunkt=2022-02-02%2018:30:00
    # %20 for space

    query_parameters = request.args

    print(query_parameters)
    conn = sqlite3.connect('../buchungssystem.sqlite')
    conn.row_factory = dict_factory
    cur = conn.cursor()

    zeitpunkt = query_parameters.get('zeitpunkt')
    anzahlPlaetze = query_parameters.get('anzahlPlaetze')

    if query_parameters.keys() != {'zeitpunkt'}:
        return jsonify({'error': 'Bad Request: Zeitpunkt parameter is the onyl parameter allowed'}), 400

    free = '''SELECT t.tischnummer, t.anzahlPlaetze
               FROM tische t LEFT JOIN reservierungen r
               ON t.tischnummer = r.tischnummer
               AND r.zeitpunkt = :zeitpunkt
               AND r.storniert = "False"
               WHERE r.tischnummer IS NULL;'''

    params = {'zeitpunkt': zeitpunkt, 'anzahlPlaetze': anzahlPlaetze}

    free_tables = cur.execute(free, params).fetchone()

    if free_tables:
        x = free_tables['tischnummer']
        y = free_tables['anzahlPlaetze']
        print(x,y)
    else:
        return jsonify({'error': 'Conflict: There are no free tables at the selected time'}), 409

    return jsonify(free_tables)


@app.route('/api/tische/', methods=['GET'])
def api_tische():
    conn = sqlite3.connect('../buchungssystem.sqlite')
    conn.row_factory = dict_factory
    cur = conn.cursor()
    all_books = cur.execute('SELECT * FROM tische;').fetchall()

    return jsonify(all_books)


@app.route('/api/tische/free', methods=['GET'])
def api_free_tables():
    # example url: 127.0.0.1:5000/api/tische/free?zeitpunkt=2022-02-02%2018:30:00
    # %20 for space

    query_parameters = request.args

    print(query_parameters)
    conn = sqlite3.connect('../buchungssystem.sqlite')
    conn.row_factory = dict_factory
    cur = conn.cursor()

    zeitpunkt = query_parameters.get('zeitpunkt')


    if query_parameters.keys() != {'zeitpunkt'}:
        return jsonify({'error': 'Bad Request: Zeitpunkt parameter is the onyl parameter allowed'}), 400

    query = '''SELECT t.tischnummer, t.anzahlPlaetze
               FROM tische t LEFT JOIN reservierungen r
               ON t.tischnummer = r.tischnummer
               AND r.zeitpunkt = ?
               AND r.storniert = "False"
               WHERE r.tischnummer IS NULL;'''

    free_tables = cur.execute(query, (zeitpunkt,)).fetchall()

    return jsonify(free_tables)


# example of how to include multiple params that don't have to be in a specific order
@app.route('/api/tische/free/UNKNOWN', methods=['GET'])
def api_free_tables_multi_params():

    query_parameters = request.args
    conn = sqlite3.connect('../buchungssystem.sqlite')
    conn.row_factory = dict_factory
    cur = conn.cursor()

    zeitpunkt = query_parameters.get('zeitpunkt')
    other_param = query_parameters.get('other_param')  # more params can be added here

    query = '''SELECT t.tischnummer, t.anzahlPlaetze
               FROM tische t LEFT JOIN reservierungen r ON
               t.tischnummer = r.tischnummer
               AND r.zeitpunkt = :zeitpunkt
               AND r.other_param = :other_param
               AND r.storniert = "False"
               WHERE r.tischnummer IS NULL;'''

    params = {'zeitpunkt': zeitpunkt, 'other_param': other_param}  # maps request args to their placeholder
    free_tables = cur.execute(query, params).fetchall()

    return jsonify(free_tables)


@app.errorhandler(404)
def page_not_found(e):
    return "<h1>404</h1><p>The resource could not be found.</p>", 404


app.run()