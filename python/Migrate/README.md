# Migration
* Migration is a two step process you create the migration then push it.
Check python/Flask2
why does data = request.get_json() do bad request
flask-migrate allows us keep track of migrations
*  create all does not update the tables if they are already in the database. If you change a model's column use `Alembic`, `Flask-Alembic`, `Flask-Migrate`

## Flask Migrate:
- Is an extension that handles SQLAlchemy Database migration for Flask
applications using ALembic as the engine. It is like Git for your database, it tracks every change made to your database structure (schema) 

In real world scenerio you rarely delete and recreate your database due to losing user data.
### Flask Migrate is useful for:
- `Zero Data Loss:` Adding a new column, to a table containing thousand of users without deleting them.
- `Team Collaboration:` Sharing a migrations\ folder via git so everyone has the same database structure.
- `Safe Deployments:` Automating schema updates during production deployments to ensure live database matches new code
- `Rollback:` Reverting the database to a previous state instantly if a new update causes bugs.
###  Run:

