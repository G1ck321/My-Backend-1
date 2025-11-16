from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
        

app = Flask(__name__)
CORS(app)

app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://googledeveloper:of1aTtbfExgy87T4Y3HeSmfob4i8syB3@dpg-d4cv3mggjchc73dlqgdg-a/notes_r71t'
#specifies a path to the database. 
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
#does not track modifications

