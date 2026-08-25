import fastapi, datetime, uvicorn, sqlite3
import services.data as service
from main5 import Tag, TagIn, TagOut



app = fastapi.FastAPI()
def create_relation():
    with sqlite3.connect("mock.db") as conn:
        db = conn.cursor()
    # AUTO INCREMENT not needed
        
        db.execute("""
            CREATE TABLE IF NOT EXISTS tag( id INTEGER PRIMARY KEY , 
            tag VARCHAR(200));
            """)
      
        conn.commit()
        conn.close
        return db, conn
    



@app.post("/")
def create(tag_in: TagIn, secret)->TagIn:
    tag: Tag = Tag(tag=tag_in.tag, created=datetime.MAXYEAR, secret=secret)
    service.create(tag)
    with sqlite3.connect("mock.db") as conn:
        db = conn.cursor()

        db.execute(
            """
            INSERT INTO tag (tag, created, secret)
            VALUES (?, ?, ?)
            """,
            (
                tag_in.tag,
                str(datetime.datetime.now()),
                secret
            )
        )

        conn.commit()

    return tag_in
    return tag_in

@app.get('/out/{tag_id}', response_model=TagOut)
def get_one(tag_id: str)->TagOut :
    tag: Tag = service.get(tag_id)
    with sqlite3.connect("mock.db") as conn:
        db = conn.cursor()

        row = db.execute(
            """
            SELECT id, tag, date, secret
            FROM tag
            WHERE id = ?
            """,
            (tag_id,)
        ).fetchone()

    if row is None:
        return {"error": "Tag not found"}

    return tag
    # return {
    #     "id": row[0],
    #     "tag": row[1],
    #     "date": row[2],
    #     "secret": row[3]
    # }

@app.get("/create")
def createTb():
    create_relation()
    return "Yhh"

if __name__ =="__main__":

    uvicorn.run("main6:app", port=8000, host="0.0.0.0", reload=True)