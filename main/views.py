from flask import Blueprint, make_response, render_template

main = Blueprint('main', __name__, template_folder='templates')

@main.route('/')
@main.route('/home')
def index():
    response = make_response(render_template('index.html'), 200)
    response.headers['Content-Type'] = 'text/html'
    return response