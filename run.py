from main import create_app
import os

os.environ['PYTHONDONTWRITEBYTECODE'] = ''

app = create_app()

if __name__ == '__main__':
    app.run(debug=True)