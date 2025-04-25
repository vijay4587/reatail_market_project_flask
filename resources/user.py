from flask import Flask, render_template, request
from flask_smorest import abort, Blueprint
from flask.views import MethodView
from flask_jwt_extended import create_access_token, jwt_required, get_jwt, get_jwt_identity
from scheams import UserSchema, BlockListSchema
from db import db
from models import UserModel, BlockListModel
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from passlib.hash import pbkdf2_sha256

blp = Blueprint("Users", "users", description="operations on tags")


@blp.route("/register")
class CreateUser(MethodView):
    @blp.arguments(UserSchema)
    def post(self, user_data):
        if UserModel.query.filter(UserModel.username == user_data['username']).first():
            abort(409, message="A user with the name already exists")
        user = UserModel(
            username=user_data['username'],
            password=pbkdf2_sha256.hash(user_data['password'])
        )
        db.session.add(user)
        db.session.commit()
        return {"message": "User created successfully!"}, 201


@blp.route("/login")
class UserLogin(MethodView):
    @blp.arguments(UserSchema)
    def post(self, user_data):
        user = UserModel.query.filter(
            UserModel.username == user_data["username"]).first()

        if user and pbkdf2_sha256.verify(user_data["password"], user.password):
            access_token = create_access_token(
                identity=str(user.id), fresh=True)
            refresh_token = create_access_token(identity=str(user.id))
            return {"access_token": access_token, "refresh_token": refresh_token}
        abort(404, message="Invalid Credentials!")


@blp.route("/user/<int:user_id>")
class User(MethodView):
    @blp.response(200, UserSchema)
    def get(self, user_id):
        user = UserModel.query.get_or_404(user_id)
        return user

    def delete(self, user_id):
        user = UserModel.query.get_or_404(user_id)
        db.session.delete(user)
        db.session.commit()
        return {"message": "User is successfully deleted"}, 200


@blp.route("/logout")
class UserLogout(MethodView):
    @jwt_required()
    def post(self):
        jti = get_jwt()["jti"]
        block_list = BlockListModel(block_set=jti)
        db.session.add(block_list)
        db.session.commit()
        return {"message": "Successfully logged out"}, 200


@blp.route('/refresh')
class TokenRefresh(MethodView):
    @jwt_required()
    def post(self):
        currentuser = get_jwt_identity()
        new_token = create_access_token(
            identity=str(currentuser), fresh=False)
        return {"access_token": new_token}
