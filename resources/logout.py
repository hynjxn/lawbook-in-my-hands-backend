from flask_restful import Resource
from http import HTTPStatus
from flask_jwt_extended import get_jti, jwt_required

jwt_blocklist = set()  # 로그아웃을 위한


# 로그아웃 api
class LogoutResource(Resource):

    @jwt_required()
    def post(self):
        jti = get_jti()['jti']
        jwt_blocklist.add(jti)

        return {}, HTTPStatus.OK