python3 -m venv venv
source venv/bin/activate

#alembic init alembic

alembic revision \
    --autogenerate \
    -m "create users and deposits"

uvicorn app.main:app --reload
