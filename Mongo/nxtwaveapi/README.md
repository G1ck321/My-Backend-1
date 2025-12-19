================ MONGODB NODE.JS CHEATSHEET ================

DATABASE
db.collection("students")

------------------------------------------------------------

READ
.find(filter)                → cursor
.findOne(filter)             → single document or null

------------------------------------------------------------

CURSOR METHODS
.sort({ field: 1 })           → ascending
.sort({ field: -1 })          → descending
.skip(n)                      → skip n docs
.limit(n)                     → limit result count
.toArray()                    → convert cursor to array

------------------------------------------------------------

FILTER OPERATORS
$gt   >      $gte  >=
$lt   <      $lte  <=
$ne   !=
$in   in array
$and  logical AND
$or   logical OR

Example:
{ age: { $gt: 18 } }

------------------------------------------------------------

INSERT
.insertOne(doc)
.insertMany([docs])

------------------------------------------------------------

UPDATE
.updateOne(filter, update)
.updateMany(filter, update)

UPDATE OPERATORS
$set     set value
$inc     increment
$push    add to array
$pull    remove from array
$unset   remove field

------------------------------------------------------------

DELETE
.deleteOne(filter)
.deleteMany(filter)

------------------------------------------------------------

COUNT
.countDocuments(filter)

------------------------------------------------------------

INDEX
.createIndex({ field: 1 })

------------------------------------------------------------

PAGINATION
.skip(page * limit).limit(limit)

============================================================
