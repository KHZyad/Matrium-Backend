from flask import Blueprint, request, jsonify
from app.models.user import User, is_fingerprint_registered
from app.models.db import db

user_bp = Blueprint('user', __name__)

# Register a new user
@user_bp.route('/register', methods=['POST'])
def register_new_user():
    data = request.json
    username = data['username']
    password = data['password']
    user_role = data['user_role']
    mac_address = data['mac_address']

    if is_fingerprint_registered(mac_address):
        return jsonify({"message": "This device is already registered."}), 400

    new_user = User(username=username, password=password, user_role=user_role, fingerprint=mac_address)
    db.session.add(new_user)
    db.session.commit()
    return jsonify({"message": "New user registered successfully."}), 201

# Check user access based on fingerprint (MAC address)
@user_bp.route('/checkAccess', methods=['POST'])
def check_user_access():
    mac_address = request.json['mac_address']
    user = User.query.filter_by(fingerprint=mac_address).first()

    if user:
        return jsonify({"message": "Access granted."}), 200
    else:
        return jsonify({"message": "Access denied."}), 403

# Authenticate admin (for example, a manager)
@user_bp.route('/authenticateAdmin', methods=['POST'])
def authenticate_admin():
    data = request.json
    username = data['username']
    password = data['password']

    admin = User.query.filter_by(username=username, user_role='manager').first()

    if admin and admin.check_password(password):
        return jsonify({'status': 'success', 'admin_data': admin.to_dict()}), 200
    else:
        return jsonify({'status': 'error', 'message': 'Incorrect username or password!'}), 401
