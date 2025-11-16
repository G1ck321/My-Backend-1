from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy

from flask_cors import CORS

app = Flask(__name__)
CORS(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:Sampled321@localhost:5432/Dvd'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = 'False'

db = SQLAlchemy(app)
class Users(db.Model):
    __tablename__ = 'persons'
    id = db.Column(db.Integer, primary_key = True)
    lastname= db.Column(db.String(), unique = False, nullable = False) 
    firstname= db.Column(db.String(), unique = False, nullable = False) 
    address= db.Column(db.String(), unique = False, nullable = False) 
    hobby= db.Column(db.String(), unique = False, nullable = False) 
    
    # def __repr__(self):
    #     return(f"Person(''{self.id}' Lastname:  '{self.lastname}' firstname: '{self.firstname}' address: '{self.address}' hobby: '{self.hobby}'")
    
    
output = []
@app.route("/", methods = ['GET'])
#uses get method
def my_home():
    users = Users.query.all()
    
    
    for user in users:
        car_data = {'id':user.id,
                    'lastname' :user.lastname, 
                    'firstname:' :user.firstname ,
                    'address:' :user.address,
                    'hobby:' :user.hobby}
        output.append(car_data)
    print(type(car_data))
    print(output)
    print(type(output))
    return output
    

if __name__ == '__main__':
    app.run(port=2600, debug = True)