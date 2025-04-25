
from flask import Flask, jsonify
import os
from flask_smorest import Api
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from resources.store import blp as StoreBluePrint
from resources.item import blp as ItemBluePrint
from resources.tag import blp as TagBluePrint
from resources.user import blp as UserBluePrint
from db import db
from models import BlockListModel
import models


def create_app(db_url=None):
    app = Flask(__name__)
    app.config["PROPAGATE_EXCEPTIONS"] = True
    app.config["API_TITLE"] = "Stores REST API"
    app.config["API_VERSION"] = "V1"
    app.config["OPENAPI_VERSION"] = "3.0.3"
    app.config["OPENAPI_URL_PREFIX"] = "/"
    app.config["OPENAPI_SWAGGER_UI_PATH"] = "/swagger-ui"
    app.config["OPENAPI_SWAGGER_UI_URL"] = "https://cdn.jsdelivr.net/npm/swagger-ui-dist/"
    basedir = os.path.abspath(os.path.dirname(__file__))
    app.config["SQLALCHEMY_DATABASE_URI"] = db_url or os.getenv(
        "DATABASE_URL", "sqlite:///" + os.path.join(basedir, 'instance', 'data.db'))
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db.init_app(app)
    migrate = Migrate(app, db)
    api = Api(app)
    app.config["JWT_SECRET_KEY"] = "jose"
    jwt = JWTManager(app)

    @jwt.token_in_blocklist_loader
    def token_in_block_list(jwt_header, jwt_payload):
        jti = jwt_payload["jti"]
        token = BlockListModel.query.filter_by(block_set=jti).first()
        return token is not None

    @jwt.revoked_token_loader
    def revoked_token_callback(jwt_header, jwt_payload):
        return (
            jsonify(
                {"description": "token has been revoked", "error": "token revoked!"},
            ), 401
        )

    @jwt.needs_fresh_token_loader
    def fresh_token_callback(jwt_header, jwt_payload):
        return (jsonify(
            {
                "description": "The token is not fresh",
                "error": "fresh token required"
            }
        ), 401
        )

    @jwt.additional_claims_loader
    def add_claims_to_jwt(identity):
        if identity == 1:
            return {"is_admin": True}
        else:
            return {"is_admin": False}

    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return (jsonify({'message': 'token has expired', 'error': 'token expired!'}), 401,)

    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return (jsonify({'message': 'Signature verification failed', 'error': 'invalid token'}), 401,)

    @jwt.unauthorized_loader
    def missing_token_callback(error):
        return (jsonify({
            'description': "requested body doesn't consists of authorization token",
            'error': 'Authorization error!'
        }), 401,)

    # with app.app_context():
    #     db.create_all()

    api.register_blueprint(StoreBluePrint)
    api.register_blueprint(ItemBluePrint)
    api.register_blueprint(TagBluePrint)
    api.register_blueprint(UserBluePrint)

    return app
