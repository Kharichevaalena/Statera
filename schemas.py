from marshmallow import Schema, validate, fields, ValidationError

class BytesField(fields.Field):
    def _validate(self, value):
        if not isinstance(value, bytes):
            raise ValidationError('Invalid input type.')

        if value is None or value == b'':
            raise ValidationError('Invalid value')
class InfoSchema(Schema):
    id = fields.Integer(dump_only=True)
    user_id = fields.Integer(dump_only=True)
    filename = fields.String(required=True)
    type = fields.Integer()
    number = fields.Integer()
    is_correct = fields.Integer()
    file = BytesField(required=True)
    message = fields.String(dump_only=True)

class UserSchema(Schema):
    name = fields.String()
    email = fields.String(required=True)
    password = fields.String(load_only=True)
    information = fields.Nested(InfoSchema, many=True, dump_only=True)

class AuthSchema(Schema):
    access_token = fields.String(dump_only=True)
    message = fields.String(dump_only=True)
