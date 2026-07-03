To install all required and optional packages

    pip install fastapi [all]

To install standard package

    pip install fastapi "uvicorn[standard]"

for query item do, python converts your dict to Json and does proper validation

    @app.get("/item/{item_id}")
    def funct(item_id:int)-> returnType


for query parameters ?=

    @app.get("/items/")
    def funct( prop:datatype | None = None(optional))