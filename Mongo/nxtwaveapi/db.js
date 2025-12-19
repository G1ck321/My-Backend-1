const {MongoClient} = require('mongodb')

let dbConnection;

let uri = 'mongodb://0.0.0.0:27017/dbNxtWave'

//define two methods
module.exports = {
    connectToDb: (callback) => {
        //.then once successful connection
        MongoClient.connect(uri).then((client) => {
            dbConnection = client.db();
            return callback();
        })
        .catch(err => {
            console.log(err);
            return callback(err);
        })
        
    },
    getDb: () => dbConnection,

}