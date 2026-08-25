import datetime,  json, pytest
from fastapi.encoders import jsonable_encoder

@pytest.fixture
def data():
    return datetime.datetime.now()

def test_json_jump(data):
    with pytest.raises(Exception):
        _ = json.dumps(data)

def test_encoder(data):
    out = jsonable_encoder(data)
    assert out

    json_out = json.dumps(out)
    assert json_out

test_encoder("Fore")