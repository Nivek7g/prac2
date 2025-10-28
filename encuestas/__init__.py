from flask import Blueprint

encuestas_bp = Blueprint('encuestas', __name__, url_prefix='/encuestas')

from . import routes