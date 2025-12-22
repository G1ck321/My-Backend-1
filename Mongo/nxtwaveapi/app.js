// console.log("Hello From app.js...... Here we will write our code.")
const express = require('express')
const {
    connectToDb,
    getDb
} = require('./db')
const port = 3001
//initialize app
const app = express()

//middleware to parse incoming json

app.use(express.json())
app.use((req, res, next) => {
    console.log(req.method, req.url);
    next();
})
let db;

connectToDb((err) => {
    if (!err) {
        app.listen(port, () => console.log(`Example app listening on port ${port}!`))
        db = getDb();
    }
})

app.get('/', (req, res) => res.sendFile(
    "./public/index.html",
    //__dirname is a built in Nodejs var
    //returns directory namof current module
    {
        root: __dirname
    }
))

//create RESTful API endpoints

//Defining API routes
//always remember forward slash /api at the begining
app.get("/api/students", (req, res) => {
    //we get a request from the user and send a response back
    //we have 120 rows we limit using pagination.
    // if sumn req http://127.0.0.1:3001/api/students ; page=0
    //is api/students?p=4; page = 4
    const page = req.query.p || 0;
    let students = [];
    const studentsPerPage = 10;
    db.collection('students')
        .find()
        .sort({
            "id": 1
        }) //one for ascending -1 for descending
        .skip(page * studentsPerPage) //0 means don't skip anything 1*10 skip first 10
        .limit(studentsPerPage)
        // .toArray()
        .forEach(student => students.push(student))
        .then(() => {
            res.status(200).json(students); //convert to JSON and send response
            console.log("See them")
        }).catch((err) => {
            res.status(500).json("Error getting studs")
            console.log("The error is ", err)
        });
})
app.get("/api/student/:id", (req, res) => {
    const studentId = parseInt(req.params.id)
    if (!isNaN(studentId)) {
        //show student info
        db.collection('students')
            .findOne({
                id: studentId
            })
            .then((student) => {
                if (student) {
                    res.status(200).json({
                        "Student found": student
                    })
                } else {
                    res.status(404).json({
                        "msg": "Student not found, Invalid Id"
                    })
                }
            })
    } else {
        //show an error
        res.status(400).json({
            Error: "Err student Id must be a Number"
        })
    }
})
app.get("/allstudents", (req, res) => {

    let allstuds = [];
    const allstudents = 120;

    db.collection("students")
        .find()
        .sort({
            "id": 1
        })
        .limit(allstudents)
        .forEach(student => allstuds.push(student))
        .then(() => {
            res.status(200).json(allstuds)
        })
        .catch(err => {
            res.status(404).json("Not found")
        })
})
app.post("/api/students", (req, res) => {

    const student = req.body; //req.get_json();
    db.collection("students")
        .insertOne(student)
        .then((result) => {
            console.log(result)
            //result is mongodb response
            res.status(200).json({
                result
            })
        })
        .catch(() => {
            res.status(500).json({
                "msg": "Error creating student"
            })
        })
})
app.put("/api/update/:id", (req, res) => {
    let update = req.body;
    const studentId = parseInt(req.params.id)
    if (!isNaN(studentId)) {
        //update
        db.collection('students')
            .updateOne({
                    id: studentId
                },
                // $inc     increment
                // $push    add to array
                // $pull    remove from array
                // $unset   remove field
                // $set     set value
                {
                    $set: update
                }
            )
            .then((result) => {
                console.log(result)
                res.status(200).json({
                    result
                })
            }).catch(() => {
                res.status(500).json({
                    "msg": "Error creating student"
                })
            })
    } else {
        res.status(400).json({
            "Error": "Student id must be a valid number."
        })
    }
})