from flask import Flask, jsonify, request, render_template
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

users1 = {
    "1":{"name":"James Paul","age":"44","Job":"Data Analyst"},
    "2":{"name":"Flora Bell","age":"34","Job":"UI/UX Designer"}
    
}
@app.route('/')
def serve():
    return render_template("index.html")
@app.route('/api/users1/<int:user_id>',methods=['PUT'])
def update_users(user_id):
    user_id_str = str(user_id)
    
    if user_id_str not in users1:
        return(jsonify({"error":"User not found"})),404
    data = request.get_json()
    
    #Updat User fields
    if "name" in data:
        users1[user_id_str]["name"] = data["name"]
    if "age" in data:
        users1[user_id_str]["age"] = data["age"]
    if "job" in data:    
        users1[user_id_str]["Job"] = data["Job"]
        
    return(jsonify(users1[user_id_str])),200

@app.route('/api/users1',methods=['GET'])
def get_users1():
    return jsonify(users1)

if __name__ =="__main__":
    app.run(debug=True,port=5002)