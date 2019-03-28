from flask import Flask, request, jsonify
from cassandra.cluster import Cluster
import urllib.request
import json


cluster = Cluster(['cassandra'])
session = cluster.connect()
app = Flask(__name__)

#url of external api
crime_url_template ='https://data.police.uk/api/crimes-street/all-crime?lat={lat}&lng={lng}&date={data}'
my_latitude = '51.52369'
my_longitude = '-0.0395857'
my_date = '2018-11'
crime_url = crime_url_template.format(lat = my_latitude, lng = my_longitude, data = my_date)

#open the external api as a variable called 'data'
with urllib.request.urlopen(crime_url) as url:
    data = json.loads(url.read().decode())

'''
crime_data = open('crime_data.csv', 'w')
count = 0

for crime in data:
    if count < 300:
        if count == 0:
            header = "ID,category,loc_lat,loc_lon,St_id,St_name,outcome\n"
            crime_data.write(header)
        ID = str(crime["id"])
        cate = str(crime["category"])
        lat = str(crime["location"]["latitude"])
        lon = str(crime["location"]["longitude"])
        stid = str(crime["location"]["street"]["id"])
        stname = str(crime["location"]["street"]["name"])
        out = str(crime["outcome_status"])
        row = "{},{},{},{},{},{},{}\n".format(ID, cate, lat, lon, stid, stname, out)
        crime_data.write(row)
    count += 1

crime_data.close()


#session.execute("CREATE KEYSPACE crime WITH REPLICATION = {'class' : 'SimpleStrategy', 'replication_factor' : 2}")
#session.execute("CREATE TABLE crime.statistic (ID int PRIMARY KEY, category text, loc_lat text, loc_lon text, St_id int, St_name text, outcome text)")

count = 0
for rec in data:
    if count < 100:
        ID = rec["id"]
        cate = rec["category"]
        lat = rec["location"]["latitude"]
        lon = rec["location"]["longitude"]
        stid = rec["location"]["street"]["id"]
        stname = rec["location"]["street"]["name"]
        out = rec["outcome_status"]
        stmt = session.prepare("INSERT INTO crime.statistic (ID, category, loc_lat, loc_lon, St_id, St_name, outcome)VALUES (?, ?, ?, ?, ?, ?, ?)IF NOT EXISTS")
        session.execute(stmt, [ID, cate, lat, lon, stid, stname, out])
        count += 1
'''
#home page
@app.route('/')
def hello():
    name = request.args.get("name","World")
    return('<h1>Hello hello, {}!</h1>'.format(name))

#Get all crime records from the external api results
@app.route('/crimes', methods=['GET'])
def crimes():
    return jsonify(data), 200

#Search a record by id from external api results
@app.route('/crimes/<id>', methods=['GET'])
def get_rec_by_id(id):
    #check if the id of a record matches the user input
    record = [rec for rec in data if str(rec['id']) == id]
    if len(record) == 0:
        return jsonify({'error': 'Record does not exist!'}), 404
    else:
        return jsonify(record), 200

#get a chosen record from external api and save it to database
@app.route('/crimes/save/<cid>', methods=['GET'])
def save_rec_by_id(cid):
    record = [rec for rec in data if str(rec['id']) == cid]
    if len(record) == 0:
        return jsonify({'error': 'Record does not exist!'}), 404
    else:
        for rec in record:
            idint = int(cid)
            cate = str(rec["category"])
            lat = str(rec["location"]["latitude"])
            lon = str(rec["location"]["longitude"])
            stid = int(rec["location"]["street"]["id"])
            stname = str(rec["location"]["street"]["name"])
            out = str(rec["outcome_status"])
            #session.execute("INSERT INTO crime.statistic (id, category, loc_lat, loc_lon, st_id, st_name, outcome) values ({0},{1},{2},{3},{4},{5},{6}) IF NOT EXISTS".format(ID, cate, lat,lon,stid,stname,out))
            #stmt = "INSERT INTO crime.sta JSON '{""id"": {}, ""category"": {}, ""loc_lat"": {}, ""loc_lon"": {}}'".format(idint,cate,lat,lon)
            stmt = "INSERT INTO crime.sta (id, category) VALUES ({},{})".format(idint,cate)
            session.execute(stmt)

        return jsonify(record), 200

#delete a record from both external results and database if exists
@app.route('/crimes/<id>', methods=['DELETE'])
def delete_a_rec(id):
    matching_records = [rec for rec in data if str(rec['id']) == id]
    if len(matching_records) == 0:
        return jsonify({'error': 'Record id not found!'}), 404
    data.remove(matching_records[0])
    stmt = """DELETE FROM crime.sta WHERE id = {} IF EXISTS""".format(int(id))
    session.execute(stmt)
    return jsonify({'success': True}), 202

#add a record to external api results
@app.route('/crimes', methods=['POST'])
def add_a_record():
    if not request.json or not 'id' in request.json:
        return jsonify({'Error': 'the new record needs to have an id!'}), 400
    new_record = {'id': request.json['id'], 'category': request.json.get('category',""), 'location': {'latitude': request.json.get('latitude',""), 'longtitude': request.json.get('longtitude',"")}}
    data.append(new_record)
    return jsonify({'message': 'created: /crimes/{}'.format(new_record['id'])}), 201

#search a record saved in the database by id
@app.route('/db/<id>')
def crime_by_id(id):
    rows = session.execute("""Select * From crime.sta where ID = {}""".format(id))
    for rec in rows:
        return(("<h1>id: {}, category: {}, locations: latitude: {}, longtitude: {}, street_id: {}, street_name: {}, outcome_status: {}</h1>".format(id, rec.category, rec.loc_lat, rec.loc_lon, rec.st_id, rec.st_name, rec.outcome)))
    return('<h1>That crime record does not exist!</h1>')

#get all records saved in the database
@app.route('/db')
def get_db():
    rows = session.execute("Select * From crime.sta")
    recs = ""
    for rec in rows:
        recs += "<p>id: {}, category: {}, locations: latitude: {}, longtitude: {}, street_id: {}, street_name: {}, outcome_status: {}</p>".format(rec.id, rec.category, rec.loc_lat, rec.loc_lon, rec.st_id, rec.st_name, rec.outcome)

    return recs


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
