# -*- coding: utf-8 -*-
from flask import Blueprint, request, render_template, jsonify

errors_bp = Blueprint('errors', __name__)


@errors_bp.app_errorhandler(400)
def forbidden():
    if request.accept_mimetypes.accept_json and not request.accept_mimetypes.accept_html:
        response = jsonify({'error': 'forbidden'})
        response.status_code = 400
        return response
    return render_template('error/400.html'), 400


@errors_bp.app_errorhandler(401)
def forbidden():
    if request.accept_mimetypes.accept_json and not request.accept_mimetypes.accept_html:
        response = jsonify({'error': 'forbidden'})
        response.status_code = 401
        return response
    return render_template('error/401.html'), 401


@errors_bp.app_errorhandler(403)
def forbidden():
    if request.accept_mimetypes.accept_json and not request.accept_mimetypes.accept_html:
        response = jsonify({'error': 'forbidden'})
        response.status_code = 403
        return response
    return render_template('error/403.html'), 403


@errors_bp.app_errorhandler(404)
def page_not_found():
    if request.accept_mimetypes.accept_json and not request.accept_mimetypes.accept_html:
        response = jsonify({'error': 'not found'})
        response.status_code = 404
        return response
    return render_template('error/404.html'), 404


@errors_bp.app_errorhandler(500)
def internal_server_error():
    if request.accept_mimetypes.accept_json and not request.accept_mimetypes.accept_html:
        response = jsonify({'error': 'internal server error'})
        response.status_code = 500
        return response
    return render_template('error/500.html'), 500

