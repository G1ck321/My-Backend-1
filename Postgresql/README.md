# SQL-ALCHEMY
## Migration
* Migration is a two step process you create the migration then push it.
Check python/Flask2
why does data = request.get_json() do bad request
flask-migrate allows us keep track of migrations
*  create all does not update the tables if they are already in the database. If you change a model's column use `Alembic`, `Flask-Alembic`, `Flask-Migrate`

* db.session.add(obj) adds an object to the session, to be inserted. 
- modifying an objects attributes, updates the object 
- db.session.delete(obj) deletes an object remember to call db.session.commit() after adding, modifying or deleting data.
- db.session.execute(db.select(...)) conducts a query to select data from the database. You'll usually use the result Result.scalars() to get a list of results and Result.scalar() for a single
