from flask import Flask
app = Flask(__name__)

@app.route('/')
def hello():
    return '임시3 (main 생성)'


if __name__ == '__main__':
    app.run(debug=True)