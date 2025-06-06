import sqlalchemy

from config import DATABASE_URL
from elekto.models.sql import migrate

from sqlalchemy import INTEGER, VARCHAR, DATETIME, BLOB, CHAR, TEXT, BOOLEAN
from sqlalchemy.sql.type_api import TypeEngine as SQLAlchemyType


def assert_pk(schema, t: type[SQLAlchemyType] = INTEGER):
    assert schema[0]['name'] == 'id'
    assert schema[0]['autoincrement'] == 'auto'
    assert schema[0]['default'] is None
    assert schema[0]['nullable'] == False
    assert schema[0]['primary_key'] == 1
    assert type(schema[0]['type']) == t


def test_migrate():
    session = migrate(DATABASE_URL)

    schema_version = session.execute('select version from schema_version').scalar()
    assert schema_version == 2

    schema = sqlalchemy.inspect(sqlalchemy.create_engine(DATABASE_URL))
    assert schema.has_table('election')

    # model: Election
    election_schema = schema.get_columns('election')
    assert_pk(election_schema)

    assert election_schema[1]['name'] == 'key'
    assert election_schema[1]['autoincrement'] == 'auto'
    assert election_schema[1]['default'] is None
    assert election_schema[1]['nullable'] == False
    assert election_schema[1]['primary_key'] == 0
    assert type(election_schema[1]['type']) == VARCHAR

    assert election_schema[2]['name'] == 'name'
    assert election_schema[2]['autoincrement'] == 'auto'
    assert election_schema[2]['default'] is None
    assert election_schema[2]['nullable'] == True
    assert election_schema[2]['primary_key'] == 0
    assert type(election_schema[2]['type']) == VARCHAR

    for i, col_name in {3: 'created_at', 4: 'updated_at'}.items():
        assert election_schema[i]['name'] == col_name
        assert election_schema[i]['autoincrement'] == 'auto'
        assert election_schema[i]['default'] is None
        assert election_schema[i]['nullable'] == True
        assert election_schema[i]['primary_key'] == 0
        assert type(election_schema[i]['type']) == DATETIME

    # model: User
    user_schema = schema.get_columns('user')
    assert_pk(user_schema)

    assert schema.get_unique_constraints('user') == [{'column_names': ['username'], 'name': None}]

    for i, col_name in enumerate(('username', 'name', 'token')):
        assert user_schema[i + 1]['name'] == col_name
        assert user_schema[i + 1]['autoincrement'] == 'auto'
        assert user_schema[i + 1]['default'] is None
        assert user_schema[i + 1]['nullable'] == True
        assert user_schema[i + 1]['primary_key'] == 0
        assert type(user_schema[i + 1]['type']) == VARCHAR

    assert user_schema[4]['name'] == 'token_expires_at'
    assert user_schema[4]['autoincrement'] == 'auto'
    assert user_schema[4]['default'] is None
    assert user_schema[4]['nullable'] == True
    assert user_schema[4]['primary_key'] == 0
    assert type(user_schema[4]['type']) == DATETIME

    for i, col_name in {5: 'created_at', 6: 'updated_at'}.items():
        assert user_schema[i]['name'] == col_name
        assert user_schema[i]['autoincrement'] == 'auto'
        assert user_schema[i]['default'] is None
        assert user_schema[i]['nullable'] == True
        assert user_schema[i]['primary_key'] == 0
        assert type(user_schema[i]['type']) == DATETIME

    # model: Voter
    voter_schema = schema.get_columns('voter')
    assert_pk(voter_schema)

    voter_fks = schema.get_foreign_keys('voter')
    assert voter_fks[0] == {'constrained_columns': ['user_id'], 'name': None, 'options': {'ondelete': 'CASCADE'}, 'referred_columns': ['id'], 'referred_schema': None, 'referred_table': 'user'}
    assert voter_fks[1] == {'constrained_columns': ['election_id'], 'name': None, 'options': {'ondelete': 'CASCADE'}, 'referred_columns': ['id'], 'referred_schema': None, 'referred_table': 'election'}

    for i, col_name in {3: 'created_at', 4: 'updated_at'}.items():
        assert voter_schema[i]['name'] == col_name
        assert voter_schema[i]['autoincrement'] == 'auto'
        assert voter_schema[i]['default'] is None
        assert voter_schema[i]['nullable'] == True
        assert voter_schema[i]['primary_key'] == 0
        assert type(voter_schema[i]['type']) == DATETIME

    for i, col_name in {5: 'salt', 6: 'ballot_id'}.items():
        assert voter_schema[i]['name'] == col_name
        assert voter_schema[i]['autoincrement'] == 'auto'
        assert voter_schema[i]['default'] is None
        assert voter_schema[i]['nullable'] == True
        assert voter_schema[i]['primary_key'] == 0
        assert type(voter_schema[i]['type']) == BLOB

    # model: Ballot
    ballot_schema = schema.get_columns('ballot')
    assert_pk(ballot_schema, t=CHAR)

    ballot_fks = schema.get_foreign_keys('ballot')
    assert ballot_fks[0] == {'constrained_columns': ['election_id'], 'name': None, 'options': {'ondelete': 'CASCADE'},
                            'referred_columns': ['id'], 'referred_schema': None, 'referred_table': 'election'}

    assert ballot_schema[2]['name'] == 'rank'
    assert ballot_schema[2]['autoincrement'] == 'auto'
    assert ballot_schema[2]['default'] is None  # It seems `default=100000000` is ignored here.
    assert ballot_schema[2]['nullable'] == True
    assert ballot_schema[2]['primary_key'] == 0
    assert type(ballot_schema[2]['type']) == INTEGER

    for i, col_name in {3: 'candidate', 4: 'voter'}.items():
        assert ballot_schema[i]['name'] == col_name
        assert ballot_schema[i]['autoincrement'] == 'auto'
        assert ballot_schema[i]['default'] is None
        assert ballot_schema[i]['nullable'] == False
        assert ballot_schema[i]['primary_key'] == 0
        assert type(ballot_schema[i]['type']) == VARCHAR

    # model: Request
    request_schema = schema.get_columns('request')
    assert_pk(request_schema)

    request_fks = schema.get_foreign_keys('request')
    assert request_fks[0] == {'constrained_columns': ['user_id'], 'name': None, 'options': {'ondelete': 'CASCADE'},
                            'referred_columns': ['id'], 'referred_schema': None, 'referred_table': 'user'}
    assert request_fks[1] == {'constrained_columns': ['election_id'], 'name': None, 'options': {'ondelete': 'CASCADE'},
                            'referred_columns': ['id'], 'referred_schema': None, 'referred_table': 'election'}

    for i, details in {
        3: ('name', VARCHAR),
        4: ('email', VARCHAR),
        5: ('chat', VARCHAR),
        6: ('description', TEXT),
        7: ('comments', TEXT),
    }.items():
        assert request_schema[i]['name'] == details[0]
        assert request_schema[i]['autoincrement'] == 'auto'
        assert request_schema[i]['default'] is None
        assert request_schema[i]['nullable'] == True
        assert request_schema[i]['primary_key'] == 0
        assert type(request_schema[i]['type']) == details[1]

    assert request_schema[8]['name'] == 'reviewed'
    assert request_schema[8]['autoincrement'] == 'auto'
    assert request_schema[8]['default'] is None
    assert request_schema[8]['nullable'] == True
    assert request_schema[8]['primary_key'] == 0
    assert type(request_schema[8]['type']) == BOOLEAN

    for i, col_name in {9: 'created_at', 10: 'updated_at'}.items():
        assert request_schema[i]['name'] == col_name
        assert request_schema[i]['autoincrement'] == 'auto'
        assert request_schema[i]['default'] is None
        assert request_schema[i]['nullable'] == True
        assert request_schema[i]['primary_key'] == 0
        assert type(request_schema[i]['type']) == DATETIME
