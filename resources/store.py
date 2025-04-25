import uuid
from flask import Flask, render_template, request
from flask_jwt_extended import jwt_required, get_jwt
from flask_smorest import abort, Blueprint
from flask.views import MethodView
from scheams import StoreSchema
from db import db
from models import StoreModel
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

blp = Blueprint("stores", __name__, description="operations on stores")


@blp.route("/store/<int:store_id>")
class Store(MethodView):
    @jwt_required()
    @blp.response(200, StoreSchema)
    def get(self, store_id):
        store = StoreModel.query.get_or_404(store_id)
        return store

    @jwt_required(fresh=True)
    def delete(self, store_id):
        store = StoreModel.query.get_or_404(store_id)
        jwt = get_jwt()
        if not jwt.get('is_admin'):
            abort(401, message="Admin privilages is required")
        db.session.delete(store)
        db.session.commit()
        return {"message": "store got deleted"}


@blp.route("/store")
class StoreList(MethodView):
    @jwt_required()
    @blp.response(200, StoreSchema(many=True))
    def get(self):
        return StoreModel.query.all()

    @jwt_required(fresh=True)
    @blp.arguments(StoreSchema)
    @blp.response(201, StoreSchema)
    def post(self, store_data):
        store = StoreModel(**store_data)
        try:
            db.session.add(store)
            db.session.commit()
        except IntegrityError:
            abort(500, message="A store with same name already exists")
        except SQLAlchemyError:
            abort(500, message="An error occured while inserting an store")
        return store
