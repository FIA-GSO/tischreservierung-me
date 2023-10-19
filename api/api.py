import flask
from flask import request   # wird benötigt, um die HTTP-Parameter abzufragen
from flask import jsonify   # übersetzt python-dicts in json
import sqlite3
import urllib.parse

app = flask.Flask(__name__)
app.config["DEBUG"] = True  # Zeigt Fehlerinformationen im Browser, statt nur einer generischen Error-Message


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


@app.route('/api/tische/', methods=['GET'])
def api_tische():
    conn = sqlite3.connect('../buchungssystem.sqlite')
    conn.row_factory = dict_factory
    cur = conn.cursor()
    all_books = cur.execute('SELECT * FROM tische;').fetchall()

    return jsonify(all_books)

@app.route('/api/tische/free', methods=['GET'])
def api_free_tables():
    query_parameters = request.args
    conn = sqlite3.connect('../buchungssystem.sqlite')
    conn.row_factory = dict_factory
    cur = conn.cursor()

    argsDate = "2022-02-02 18:30:00"
    zeitpunkt = query_parameters.get('zeitpunkt')

    query = f'SELECT t.tischnummer, t.anzahlPlaetze FROM tische t LEFT JOIN reservierungen r ON t.tischnummer = r.tischnummer AND r.zeitpunkt = \'{argsDate}\' AND r.storniert = "False" WHERE r.tischnummer IS NULL;'



    free_tables= cur.execute(query).fetchall()

    return jsonify(free_tables)


@app.route('/api/tische/freeN', methods=['GET'])
def api_free_tablesN():
    query_parameters = request.args

    zeitpunkt = query_parameters.get('zeitpunkt')

    query = f'SELECT t.tischnummer, t.anzahlPlaetze FROM tische t LEFT JOIN reservierungen r ON t.tischnummer = r.tischnummer AND r.zeitpunkt = ? AND r.storniert = "False" WHERE r.tischnummer IS NULL;'
    to_filter = []

    if zeitpunkt:
        query += ' zeitpunkt=? AND'
        to_filter.append(zeitpunkt)

    query = query[:-4] + ';'

    conn = sqlite3.connect('../buchungssystem.sqlite')
    conn.row_factory = dict_factory
    cur = conn.cursor()

    result= cur.execute(query, to_filter).fetchall()

    return jsonify(result)



@app.errorhandler(404)
def page_not_found(e):
    return "<h1>404</h1><p>The resource could not be found.</p>", 404


app.run()