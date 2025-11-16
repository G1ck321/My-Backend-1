from flask import Flask, jsonify, request
from flask_cors import CORS
import psycopg2

app = Flask(__name__)
CORS (app)

def get_connected():
    conn = psycopg2.connect(
        host = "localhost",
        database = "Dvd",
        user = 'postgres',
        password = "Sample@321"
    )
    return conn
@app.get("/")
#uses get method
def my_home():
    conn = get_connected()
    cur = conn.cursor()
    cur.execute("Select * from cars")
    rows = cur.fetchall()
    output = []
    id = 0
    for row in rows:
        car_data = {'id':[id],'brand':row[0],'model':row[1],'year':row[2]}
        id+=1
        output.append(car_data)
    conn.close()
    return output
    

app.run(port=2500)