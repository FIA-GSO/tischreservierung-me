import flask
from flask import request   # wird benötigt, um die HTTP-Parameter abzufragen
from flask import jsonify   # übersetzt python-dicts in json
import sqlite3
import random
import string
from datetime import datetime
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


@app.route('/api/res/create', methods=['POST'])
def api_res_create():

    # example url: http://127.0.0.1:5000/api/res/pseudo?zeitpunkt=2022-02-02%2018:30:00&anzahlPlaetze=6

    conn = sqlite3.connect('../buchungssystem.sqlite')
    conn.row_factory = dict_factory
    cur = conn.cursor()

    jsonData = request.json

    zeitpunkt = jsonData.get('zeitpunkt')
    anzahl_plaetze = jsonData.get('anzahlPlaetze')

    if jsonData.keys() != {'zeitpunkt', 'anzahlPlaetze'}:
        return jsonify({'error': 'Bad Request: Zeitpunkt and anzahlPlaetze are the only parameters allowed'}), 400

    if not datetime_valid(zeitpunkt):
        return jsonify({'error': 'Bad Request: Zeitpunkt parameter does not fullfill iso standart date'}), 400

    if not datetime_time_validate(zeitpunkt):
        return jsonify({'error': 'Bad Request: Zeitpunkt parameter has to be at full or half hour values'}), 400

    # ---------------------------
    # check free tables at selected date

    free = '''SELECT t.tischnummer, t.anzahlPlaetze
                   FROM tische t LEFT JOIN reservierungen r
                   ON t.tischnummer = r.tischnummer
                   AND r.zeitpunkt = :zeitpunkt
                   AND r.storniert = "False"
                   WHERE r.tischnummer IS NULL;'''

    params = {'zeitpunkt': zeitpunkt, 'anzahlPlaetze': anzahl_plaetze}

    free_tables = cur.execute(free, params).fetchall()

    if not free_tables:
        return jsonify({'error': 'Conflict: There are no free tables at the selected time'}), 409

    # ---------------------------
    # sort and filter the table
    sorted_table_by_anzahlplaetze = sorted(free_tables, key=lambda x: x['anzahlPlaetze'])

    # filters out any entry that is below the user request anzahlPlaetze
    sorted_filtered_list = [entry for entry in sorted_table_by_anzahlplaetze if entry['anzahlPlaetze'] >= int(anzahl_plaetze)]

    if not sorted_filtered_list:
        return jsonify({'error': 'Conflict: There are free tables but not enough anzahlPlaetze'}), 409

    # ---------------------------
    # book the first table from the result list
    first_row = sorted_filtered_list[0]
    booking_params = {'zeitpunkt': zeitpunkt, 'tischnummer': first_row['tischnummer'], 'pin': random.randint(1000, 9999)}

    booking_query = '''INSERT INTO reservierungen (zeitpunkt, tischnummer, pin, storniert)
                       VALUES (:zeitpunkt, :tischnummer, :pin, 'False');'''

    obj = cur.execute(booking_query, booking_params)
    conn.commit()

    return jsonify(sorted_filtered_list[0])


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

    if not datetime_valid(zeitpunkt):
        return jsonify({'error': 'Bad Request: Zeitpunkt parameter does not fullfill iso standart date'}), 400

    query = '''SELECT t.tischnummer, t.anzahlPlaetze
               FROM tische t LEFT JOIN reservierungen r
               ON t.tischnummer = r.tischnummer
               AND r.zeitpunkt = ?
               AND r.storniert = "False"
               WHERE r.tischnummer IS NULL;'''

    free_tables = cur.execute(query, (zeitpunkt,)).fetchall()

    return jsonify(free_tables)


@app.errorhandler(404)
def page_not_found(e):
    return "<h1>404</h1><p>The resource could not be found.</p>", 404


def datetime_valid(dt_str):
    try:
        datetime.fromisoformat(dt_str)
    except:
        return False
    return True


def datetime_time_validate(zeitpunkt):
    try:
        # Parse the input string as a datetime object
        dt = datetime.strptime(zeitpunkt, '%Y-%m-%d %H:%M:%S')

        # Check if seconds are 0 and minutes are either 0 or 30
        if dt.second != 0 or dt.minute not in [0, 30]:
            return False

        return True

    except ValueError:
        # If parsing fails, it's not a valid datetime format
        return False


app.run()