import bcrypt
from flask import request
from flask_jwt_extended import jwt_required
from flask_restful import Resource
from http import HTTPStatus
from db.db import get_mysql_connection


class SignupResource(Resource):

    # 회원가입 api
    def post(self):
        data = request.get_json()

        # 필수값이 있는지 체크
        if 'loginId' not in data or 'password' not in data or 'name' not in data or 'nickname' not in data:
            return {'status' : HTTPStatus.BAD_REQUEST, 'message' : '필수값이 없습니다.'}, HTTPStatus.BAD_REQUEST

        # 비밀번호 암호화
        pw = data['password']
        hashed_pw = bcrypt.hashpw(pw.encode('utf-8'), bcrypt.gensalt())
        saved_pw = hashed_pw.decode('utf-8')

        # 데이터베이스에서 사용자 저장
        connection = get_mysql_connection()
        cursor = connection.cursor()
        query = """insert into user (loginId, password, name, nickname) 
                    values (%s, %s, %s, %s);"""
        param = (data['loginId'], saved_pw, data['name'], data['nickname'])

        cursor.execute(query, param)
        connection.commit()

        user_id = cursor.lastrowid

        cursor.close()
        connection.close()

        # 클라이언트에 응답하기
        return {'user_id' : user_id}, HTTPStatus.OK


class LoginidResource(Resource):

    # 로그인아이디 중복 확인 api
    def get(self, loginid):

        # 데이터베이스에서 로그인아이디 조회
        connection = get_mysql_connection()
        cursor = connection.cursor()
        query = """select * from user where loginId = %s;"""
        param = (loginid,)

        cursor.execute(query, param)
        result = cursor.fetchone()
        # print(result)

        cursor.close()
        connection.close()

        # 해당 로그인아이디가 중복인지 확인
        if result is not None:
            return {'status' : HTTPStatus.BAD_REQUEST, 'message' : '중복된 아이디입니다.'}, HTTPStatus.BAD_REQUEST

        return {}, HTTPStatus.OK

