from sqlalchemy.orm import relationship
from flask_jwt_extended import create_access_token
from datetime import timedelta
from main import db, session, Base
from passlib.hash import bcrypt

class Info(Base):
    __tablename__ = 'info'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    filename = db.Column(db.String(250), nullable=False)
    type = db.Column(db.Integer, nullable=False)
    number = db.Column(db.Integer, nullable=False)
    is_correct = db.Column(db.Integer, nullable=False)
    file = db.Column(db.BLOB, nullable=False)

    @classmethod
    def get_user_list(cls, user_id):
        try:
            info = cls.query.filter(Info.user_id == user_id)
            session.commit()
        except Exception:
            session.rollback()
            raise
        return info

    def save(self):
        try:
            session.add(self)
            session.commit()
        except Exception:
            session.rollback()
            raise

    @classmethod
    def get(cls, id, user_id):
        try:
            info = cls.query.filter(
                cls.id == id,
                cls.user_id == user_id
            ).first()
            if not info:
                raise Exception('No info with this id')
        except Exception:
            session.rollback()
            raise
        return info

    def update(self, **kwargs):
        try:
            for key, value in kwargs.items():
                setattr(self, key, value)
            session.commit()
        except Exception:
            session.rollback()
            raise

    def delete(self):
        try:
            session.delete(self)
            session.commit()
        except Exception:
            session.rollback()
            raise


class User(Base):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(250), nullable=False)
    email = db.Column(db.String(250), nullable=False, unique=True )
    password = db.Column(db.String(50), nullable=False)
    info = relationship('Info', backref='user', lazy=True)

    def __init__(self, **kwargs):
        self.name = kwargs.get('name')
        self.email = kwargs.get('email')
        self.password = bcrypt.hash(kwargs.get('password'))

    def get_token(self, expire_time=24):
        expire_delta = timedelta(expire_time)
        token = create_access_token(
            identity=self.id, expires_delta=expire_delta)
        return token

    @classmethod
    def authenticate(cls, email, password):
        user = cls.query.filter(cls.email == email).one()
        if not bcrypt.verify(password, user.password):
            raise Exception('No user with this password')
        return user

