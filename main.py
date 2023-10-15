from flask import Flask, jsonify, request
import sqlalchemy as db
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from flask_jwt_extended import JWTManager, jwt_required, get_jwt_identity
from config import Config
from apispec.ext.marshmallow import MarshmallowPlugin
from apispec import APISpec
from flask_apispec.extension import FlaskApiSpec
from schemas import InfoSchema, UserSchema, AuthSchema
from flask_apispec import use_kwargs, marshal_with
import logging
import os

app = Flask(__name__)
app.config.from_object(Config)

client = app.test_client()

engine = create_engine('sqlite:///db.sqlite')
session = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))

Base = declarative_base()
Base.query = session.query_property()

jwt = JWTManager(app)

docs = FlaskApiSpec()
docs.init_app(app)

app.config.update({
        'APISPEC_SPEC': APISpec(
        title='NeuralNetwork',
        version='v1',
        openapi_version='2.0',
        plugins=[MarshmallowPlugin()],
    ),
    'APISPEC_SWAGGER_URL': '/swagger/'

})

from models import *

Base.metadata.create_all(bind=engine)

def setup_logger():
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)

    formatter = logging.Formatter(
        '%(asctime)s:%(name)s:%(levelname)s:%(message)s')
    file_handler = logging.FileHandler('log/api.log')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger

logger = setup_logger()



@app.route('/hackathon', methods=['GET'])
@jwt_required()
@marshal_with(InfoSchema(many=True))
def get_list():
    try:
        user_id = get_jwt_identity()
        information = Info.get_user_list(user_id=user_id)
    except Exception as e:
        logger.warning(
            f'user:{user_id}  - read action failed with errors: {e}')
        return {'message': str(e)} , 400
    return information


@app.route('/hackathon', methods=['POST'])
@jwt_required()
@use_kwargs(InfoSchema)
@marshal_with(InfoSchema)
def update_list(**kwargs):
    try:
        user_id = get_jwt_identity()
        new_one = Info(user_id=user_id, **kwargs)
        new_one.save()
        session.add(new_one)
        session.commit()
    except Exception as e:
        logger.warning(
            f'user:{user_id}  - post action failed with errors: {e}')
        return {'message': str(e)} , 400
    return new_one

@app.route('/hackathon/predict', methods=['POST'])
#@jwt_required()
@use_kwargs(InfoSchema)
@marshal_with(InfoSchema)
def update(**kwargs):
    print(request.files)
    for key, value in request.files.items():
        value.save(os.path.join("text.txt", key))
        print(key, value)
    return 200


@app.route('/hackathon/<int:id>', methods=['PUT'])
#@jwt_required()
@use_kwargs(InfoSchema)
@marshal_with(InfoSchema)
def update_rows(id, **kwargs):
    try:
        user_id = get_jwt_identity()
        item = Info.get(id,user_id)
        item.update(**kwargs)
    except Exception as e:
        logger.warning(
            f'user:{user_id} - update action failed with errors: {e}')
        return {'message': str(e)} , 400
    return item


@app.route('/hackathon/<int:id>', methods=['DELETE'])
@jwt_required()
@marshal_with(InfoSchema)
def delete_rows(id):
    try:
        user_id = get_jwt_identity()
        item = Info.get(id, user_id)
        item.delete()
        if not item:
            return ({'message': 'No item found with this id'}, 400)
        session.delete(item)
        session.commit()
    except Exception as e:
        logger.warning(
            f'user:{user_id}  - delete action failed with errors: {e}')
        return {'message': str(e)} , 400
    return '', 204

@app.route('/register', methods=['POST'])
@use_kwargs(UserSchema)
@marshal_with(AuthSchema)
def register(**kwargs):
    try:
        user = User(**kwargs)
        session.add(user)
        session.commit()
        token = user.get_token()
    except Exception as e:
        logger.warning(
            f'registration failed with errors: {e}')
        return {'message': str(e)} , 400
    return {'access_token': token}


@app.route('/login', methods=['POST'])
@use_kwargs(UserSchema(only=('email', 'password')))
@marshal_with(AuthSchema)
def login(**kwargs):
    try:
        user = User.authenticate(**kwargs)
        token = user.get_token()
    except Exception as e:
        logger.warning(
            f'login with email {kwargs["email"]} failed with errors: {e}')
        return {'message': str(e)} , 400
    return {'access_token': token}



@app.teardown_appcontext
def shutdown_session(exception=None):
    session.remove()

@app.errorhandler(422)
def handle_error(err):
    headers = err.data.get('headers', None)
    messages = err.data.get('messages', ['Invalid Request.'])
    logger.warning(f'Invalid input params: {messages}')
    if headers:
        return jsonify({'message': messages}), 400, headers
    else:
        return jsonify({'message': messages}), 400



docs.register(get_list)
docs.register(update_list)
docs.register(update)
docs.register(update_rows)
docs.register(delete_rows)
docs.register(register)
docs.register(login)


if __name__ == '__main__':
    app.run(host='127.0.0.1', port='5000')
