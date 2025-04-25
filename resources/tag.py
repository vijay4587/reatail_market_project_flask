from flask import Flask, render_template, request
from flask_jwt_extended import jwt_required, get_jwt
from flask_smorest import abort, Blueprint
from flask.views import MethodView
from scheams import TagSchema, TagAndItemSchema
from db import db
from models import TagModel, StoreModel, ItemModel, Itemtags
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

blp = Blueprint("tags", __name__, description="operations on tags")


@blp.route("/store/<int:store_id>/tag")
class TagsInStore(MethodView):
    @jwt_required()
    @blp.response(200, TagSchema(many=True))
    def get(self, store_id):
        store = StoreModel.query.get_or_404(store_id)
        return store.tags.all()

    @jwt_required(fresh=True)
    @blp.arguments(TagSchema)
    @blp.response(201, TagSchema)
    def post(self, tag_data, store_id):
        tag = TagModel(store_id=store_id, **tag_data)
        try:
            db.session.add(tag)
            db.session.commit()
        except SQLAlchemyError:
            abort(500, message="error while inserting tag data")
        return tag


@blp.route("/item/<int:item_id>/tag/<int:tag_id>")
class LinkTagsToItem(MethodView):
    @jwt_required(fresh=True)
    @blp.response(201, TagSchema)
    def post(self, item_id, tag_id):
        item = ItemModel.query.get_or_404(item_id)
        tag = TagModel.query.get_or_404(tag_id)
        item.tags.append(tag)
        try:
            db.session.add(item)
            db.session.commit()
        except SQLAlchemyError:
            abort(500, message="an error occured while inserting a tag.")
        return tag

    @jwt_required(fresh=True)
    @blp.response(200, TagAndItemSchema)
    def delete(self, item_id, tag_id):
        item = ItemModel.query.get_or_404(item_id)
        tag = TagModel.query.get_or_404(tag_id)
        jwt = get_jwt()
        if not jwt.get('is_admin'):
            abort(401, message="Admin privilages is required")
        item.tags.remove(tag)
        try:
            db.session.add(item)
            db.session.commit()
        except SQLAlchemyError:
            abort(500, message="an error occured while removing a tag.")
        return {"message": "Item removed from the tag", "item": item, "tag": tag}


@blp.route("/tag/<int:tag_id>")
class Tag(MethodView):
    @jwt_required()
    @blp.response(200, TagSchema)
    def get(self, tag_id):
        tag = TagModel.query.get_or_404(tag_id)
        return tag

    @jwt_required(fresh=True)
    @blp.response(202,
                  description="tag is deleted if no item is assigned to it",
                  example="Tag Deleted!")
    @blp.alt_response(404,
                      description="Tag not Found!")
    @blp.alt_response(400,
                      description="Tag is not deleted returns tag if items is not present")
    def delete(self, tag_id):
        tag = TagModel.query.get_or_404(tag_id)
        jwt = get_jwt()
        if not jwt.get('is_admin'):
            abort(401, message="Admin privilages is required")

        if not tag.items:
            db.session.delete(tag)
            db.session.commit()
            return {"message": "tag deleted"}
        abort(400, message="Could not delete tag, make sure tag is not associated with any items, then try again")
