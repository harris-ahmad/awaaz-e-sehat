from flask import Blueprint, make_response, render_template

main = Blueprint("main", __name__, template_folder="templates")


# error handlers
@main.app_errorhandler(code=404)
def page_not_found(e):
    response = make_response(
        """
    <h1>404</h1>
    <p>The resource could not be found.</p>
    """,
        404,
    )
    response.headers["Content-Type"] = "text/html"
    return response


@main.app_errorhandler(code=500)
def internal_server_error(e):
    response = make_response(
        """
    <h1>500</h1>
    <p>The server encountered an internal error and was unable to complete your request.</p>
    """,
        500,
    )
    response.headers["Content-Type"] = "text/html"
    return response


@main.app_errorhandler(code=403)
def forbidden(e):
    response = make_response(
        """
    <h1>403</h1>
    <p>You do not have permission to access this resource.</p>
    """,
        403,
    )
    response.headers["Content-Type"] = "text/html"
    return response


@main.route("/")
@main.route("/home")
def index():
    response = make_response(render_template("index.html"), 200)
    response.headers["Content-Type"] = "text/html"
    return response
