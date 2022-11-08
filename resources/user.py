import bcrypt
from flask import request
from flask_restful import Resource
from http import HTTPStatus
from db.db import get_mysql_connection
from flask_jwt_extended import jwt_required, get_jwt_identity


class UserResource(Resource):

    # 프로필 수정
    @jwt_required()
    def post(self):
        data = request.get_json()

        # jwt에서 user_id 뽑아오기
        user_id = get_jwt_identity()

        # 데이터베이스에서 유저 프로필 수정
        connection = get_mysql_connection()
        cursor = connection.cursor()

        # 존재하지 않는 유저면 에러
        query = """select * from user where id = %s"""
        param = (user_id,)
        cursor.execute(query, param)
        result = cursor.fetchone()
        if result is None:
            return {"message": "존재하지 않는 사용자입니다."}, HTTPStatus.BAD_REQUEST

        # 유저 프로필 업데이트
        query = """update user set name = %s, nickname = %s where id =%s"""
        param = (data['name'], data['nickname'], user_id)

        cursor.execute(query, param)
        connection.commit()

        cursor.close()
        connection.close()

        # 클라이언트에 응답
        return {}, HTTPStatus.OK


class PasswordResource(Resource):

    # 비밀번호 변경
    @jwt_required()
    def post(self):
        data = request.get_json()

        # jwt에서 user_id 뽑아오기
        user_id = get_jwt_identity()

        # 데이터베이스에서 비밀번호 변경
        connection = get_mysql_connection()
        cursor = connection.cursor()

        # 존재하지 않는 유저면 에러
        query = """select * from user where id = %s"""
        param = (user_id,)
        cursor.execute(query, param)
        result = cursor.fetchone()
        if result is None:
            return {"message": "존재하지 않는 사용자입니다."}, HTTPStatus.BAD_REQUEST

        # 비밀번호랑 비밀번호확인이 다르면 변경 불가능
        if data['pwd'] != data['pwd_check']:
            return {"message" : "비밀번호와 비밀번호 확인이 다릅니다. "}, HTTPStatus.BAD_REQUEST

        # 비밀번호 암호화
        pw = data['pwd']
        hashed_pw = bcrypt.hashpw(pw.encode('utf-8'), bcrypt.gensalt())
        saved_pw = hashed_pw.decode('utf-8')

        # 비밀번호 변경
        query = """update user set password = %s where id =%s"""
        param = (saved_pw, user_id)

        cursor.execute(query, param)
        connection.commit()

        cursor.close()
        connection.close()

        # 클라이언트에 응답
        return {}, HTTPStatus.OK