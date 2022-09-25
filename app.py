from flask import Flask
from flask_restful import Api
from config.config import Config
# from flask_cors import CORS
from resources.test import TestResource

# Flask 객체 인스턴스 생성
app = Flask(__name__)


# CORS(app)

# 접속 url 설정
@app.route('/')
def hello_world():  # put application's code here
    return 'Hello World!'


# 1. 환경변수 설정
app.config.from_object(Config)
# 2. api설정
api = Api(app)  # API설정을 한다. 괄호안에는 위에서 받은 플라스크변수
# 3. 경로(Path)와 리소스(Resource)를 연결한다.
api.add_resource(TestResource, '/test')

if __name__ == '__main__':
    app.run()
