from flask import Flask, render_template, jsonify, request
from config import app
from models import db, User
import os
from sqlalchemy import text
import datetime

#status code
#env
#structure, 
#presentation 
# JWT Authentication, deploy on render, github
# storage bucket  and external storage bucket for file, pagination, git

now = datetime.datetime.now().strftime("%D %H:%M")

with app.app_context():
    db.init_app(app)
    #binds the sqlalchemy to app
    db.create_all()
    #creates table

@app.route("/hello")
def home():
    return "hello world"

@app.route("/")
def renderPage():
    return render_template("test.html")

@app.route("/api/allnotes")
def displayNotes():
    all_notes = User.query.all()
    list_notes = []
    for note in all_notes:
        notes_list = {'id':note.name,'content':note.email}
        # if notes_list["id"] ==22:
        #     print(notes_list["content"])
        
        list_notes.append(notes_list)   
        #sort in a particular order
    list_notes.sort(key=lambda user_key:user_key["email"],reverse=True)
    print(notes_list)
    
    # print(list_notes)
    return jsonify(list_notes), 200

@app.route("/create_notes", methods=["POST"])
def createData():
    data = request.get_json()
    name = data.get("name")
    email = data.get("email")
    if not name or email:
        return jsonify({"message": "Content required"}), 400
    user = User(name=name, email = email)
    
    db.session.add(user)
    db.session.commit()
    return jsonify({"message": "Note created", "note": user.to_dictionary()}), 201
        
        
    


@app.route("/update_notes/<int:note_id>", methods=["PUT"])
def updateUser(note_id):
    data = request.get_json()
    print(data)
    if not data or 'content' not in data:
        return jsonify({'error':f"note with id {note_id} has no content"}),404
    
    note = db.session.get(Note, note_id)
    note.content= data['content'].strip()
    note.updated_at =datetime.datetime.utcnow()
    db.session.commit()
    print(note.content)
    return jsonify({"message":"updated"}),200

# @app.route("/get_notes", methods=["GET"])
# def displayData():
#     return jsonify(notes), 200

@app.route("/api/search",methods = ['GET'])
def searchNotes():
    query = request.args.get('q','')
    print(query,'lk')
    try:
        note_list = []
        all_result = db.session.execute(text(f"SELECT * FROM note WHERE content LIKE '%{query}%'"))
        result = all_result.fetchall()
        for note in result:
            each_note = {"id":note.id, "content":note.content,"update":note.updated_at}
            note_list.append(each_note)    
            print(note_list)    
        note_list.sort(key=lambda each_note:each_note["update"], reverse=True)
        if note_list:
            return jsonify(note_list),200
        else:
            print(note_list)
            return jsonify(""),200
    except:
        return jsonify("Not found"),404

@app.route("/api/delete_note/<int:note_id>", methods = ['DELETE'])

def deleteNotes(note_id):
    note = db.session.get(Note, note_id)
    if  not  note:
        return jsonify({'error':f"note with id {note_id} does not exist"}),404
    db.session.delete(note)
    db.session.commit()
    
    return jsonify(''),204
if __name__ == "__main__":
    port = int(os.environ.get("PORT",3000))
    app.run(host = "0.0.0.0",port=port, debug=True)
