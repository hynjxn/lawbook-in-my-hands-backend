from flask import request
from flask_restful import Resource
from http import HTTPStatus
from db.db import get_mysql_connection


class SignupResource(Resource):

    def post(self):
        # 클라이언트가 요청한 request의 body에 있는 json 가져오기
        data = request.get_json()

        # 필수값이 있는지 체크
        if 'loginId' not in data:
            return {'status' : HTTPStatus.BAD_REQUEST, 'message' : '필수값이 없습니다.'}, HTTPStatus.BAD_REQUEST

        # 데이터베이스 커넥션
        connection = get_mysql_connection()

        # 커서 가져오기
        cursor = connection.cursor(dictionary=True)

        # 쿼리문 작성
        query = """insert into user (loginId, password, name, nickname) values (%s, %s, %s, %s);"""
        param = (data['loginId'], data['password'], data['name'], data['nickname'])

        # 쿼리문 실행
        cursor.execute(query, param)
        connection.commit()

        # 커서와 커넥션 닫기
        cursor.close()
        connection.close()

        # 클라이언트에 응답하기
        return {}, HTTPStatus.OK
