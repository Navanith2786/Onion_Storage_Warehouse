import jwt
import datetime
from datetime import timezone
import os
from functools import wraps
from flask import request, jsonify

SECRET_KEY = os.getenv("SECRET_KEY", "fallback-secret")

def generate_token(username):
    payload = {
        'exp': datetime.datetime.now(timezone.utc) + datetime.timedelta(days=1),
        'iat': datetime.datetime.now(timezone.utc),
        'sub': username
    }
    return jwt.encode(payload, SECRET_KEY, algorithm='HS256')

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'msg': 'Token is missing!'}), 401
        
        try:
            if token.startswith('Bearer '):
                token = token.split(' ')[1]
            data = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        except Exception as e:
            return jsonify({'msg': 'Token is invalid!', 'error': str(e)}), 401
        
        return f(*args, **kwargs)
    return decorated
