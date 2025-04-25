from db import db


class BlockListModel(db.Model):
    block_set = db.Column(db.String(1000), primary_key=True)
