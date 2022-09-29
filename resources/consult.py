from flask import request
from flask_restful import Resource
from http import HTTPStatus
from db.db import get_mysql_connection
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime


class ConsultResource(Resource):

    # 상담 작성 api
    @jwt_required()
    def post(self):
        data = request.get_json()

        # 필수값이 있는지 체크
        if 'content' not in data:
            return {'status': HTTPStatus.BAD_REQUEST, 'message': '필수값이 없습니다.'}, HTTPStatus.BAD_REQUEST

        # jwt에서 user_id 뽑아오기
        user_id = get_jwt_identity()
        print(user_id)

        # 데이터베이스에서 상담 저장
        connection = get_mysql_connection()
        cursor = connection.cursor()
        query = """insert into consult (content, user_id) 
                    values (%s, %s);"""
        param = (data['content'], user_id)

        cursor.execute(query, param)
        connection.commit()

        consult_id = cursor.lastrowid

        cursor.close()
        connection.close()

        # 클라이언트에 응답
        return {'consult_id': consult_id}, HTTPStatus.OK


class ConsultGetResource(Resource):

    # 상담 단건 조회 api
    @jwt_required()
    def get(self, consult_id):

        # 데이터베이스에서 상담 조회
        connection = get_mysql_connection()
        cursor = connection.cursor()
        query = """select * from consult where id = %s;"""
        param = (consult_id,)

        cursor.execute(query, param)
        result = cursor.fetchone()

        print(result)

        cursor.close()
        connection.close()

        return {'consult_id' : result[0], 'content' : result[1], 'created_at' : str(result[3])}, HTTPStatus.OK
