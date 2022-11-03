from flask import request
from flask_restful import Resource
from http import HTTPStatus
from db.db import get_mysql_connection
from flask_jwt_extended import jwt_required, get_jwt_identity


class ScrapResource(Resource):

    # 판결문 스크랩 여부 조회 api
    @jwt_required()
    def get(self, case_serial_id):
        # jwt에서 user_id 뽑아오기
        user_id = get_jwt_identity()

        # 데이터베이스에서 스크랩 여부 확인
        connection = get_mysql_connection()
        cursor = connection.cursor()
        query = """select * from bookmark where user_id = %s and case_id = %s;"""
        param = (user_id, case_serial_id,)

        cursor.execute(query, param)
        result = cursor.fetchone()

        cursor.close()
        connection.close()

        # 스크랩 여부로 flag 보내기
        if result is None:
            return {"scrap": False}, HTTPStatus.OK

        return {"scrap": True}, HTTPStatus.OK

    # 판결문 스크랩 생성 api
    @jwt_required()
    def post(self, case_serial_id):
        data = request.get_json()

        # jwt에서 user_id 뽑아오기
        user_id = get_jwt_identity()

        # 데이터베이스에서 스크랩 생성하기
        connection = get_mysql_connection()
        cursor = connection.cursor()

        # 이미 스크랩한 판결문이면 에러
        query = """select * from bookmark where user_id = %s and case_id = %s"""
        param = (user_id, case_serial_id,)
        cursor.execute(query, param)
        result = cursor.fetchone()
        if result is not None:
            return {"message": "이미 스크랩한 판결문입니다. "}, HTTPStatus.BAD_REQUEST

        # 스크랩 생성하기
        query = """insert into bookmark (consult_id, user_id, case_id) values (%s, %s, %s)"""
        param = (data['consult_id'], user_id, case_serial_id)

        cursor.execute(query, param)
        connection.commit()

        scrap_id = cursor.lastrowid

        cursor.close()
        connection.close()

        # 클라이언트에 응답
        return {'scrap_id': scrap_id}, HTTPStatus.OK

    # 판결문 스크랩 취소 api
    @jwt_required()
    def delete(self, case_serial_id):

        # jwt에서 user_id 뽑아오기
        user_id = get_jwt_identity()

        # 데이터베이스에서 스크랩 삭제하기
        connection = get_mysql_connection()
        cursor = connection.cursor()

        # 아직 판결문을 스크랩하지 않았으면 에러
        query = """select * from bookmark where user_id = %s and case_id = %s"""
        param = (user_id, case_serial_id,)
        cursor.execute(query, param)
        result = cursor.fetchone()
        if result is None:
            return {"message": "아직 판결문을 스크랩하지 않았습니다."}, HTTPStatus.BAD_REQUEST

        # 스크랩 삭제하기
        query = """delete from bookmark where user_id = %s and case_id = %s"""
        param = (user_id, case_serial_id)

        cursor.execute(query, param)
        connection.commit()

        cursor.close()
        connection.close()

        # 클라이언트에 응답
        return {}, HTTPStatus.OK