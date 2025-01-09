from flask import Blueprint

defect_bp = Blueprint('defect', __name__)

# Placeholder route
@defect_bp.route('/test', methods=['GET'])
def test_defect():
    return "Defect routes are working!"
