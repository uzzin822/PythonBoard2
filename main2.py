from flask import Flask
app = Flask(__name__)

@app.route('/')
def hello():
    return '안뇽하세용(ver2에서 생성)'


if __name__ == '__main__':
    app.run(debug=True)