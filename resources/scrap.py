import requests
from flask import request
from flask_restful import Resource
from http import HTTPStatus

from xml_to_dict import XMLtoDict

from db.db import get_mysql_connection
from flask_jwt_extended import jwt_required, get_jwt_identity


class ScrapResource(Resource):

    # 판결문 스크랩 여부 조회 api
    @jwt_required()
    def get(self, case_serial_id):
        args = request.args
        consult_id = args.get("consult_id")

        # jwt에서 user_id 뽑아오기
        user_id = get_jwt_identity()

        # 데이터베이스에서 스크랩 여부 확인
        connection = get_mysql_connection()
        cursor = connection.cursor()
        query = """select * from bookmark where user_id = %s and case_id = %s and consult_id = %s;"""
        param = (user_id, case_serial_id, consult_id)

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
        args = request.args
        consult_id = args.get("consult_id")

        # jwt에서 user_id 뽑아오기
        user_id = get_jwt_identity()

        # 데이터베이스에서 스크랩 생성하기
        connection = get_mysql_connection()
        cursor = connection.cursor()

        # 이미 스크랩한 판결문이면 에러
        query = """select * from bookmark where user_id = %s and case_id = %s and consult_id = %s"""
        param = (user_id, case_serial_id, consult_id)
        cursor.execute(query, param)
        result = cursor.fetchone()
        if result is not None:
            return {"message": "이미 스크랩한 판결문입니다. "}, HTTPStatus.BAD_REQUEST

        # 스크랩 생성하기
        query = """insert into bookmark (consult_id, user_id, case_id) values (%s, %s, %s)"""
        param = (consult_id, user_id, case_serial_id)

        cursor.execute(query, param)
        connection.commit()

        cursor.close()
        connection.close()

        # 클라이언트에 응답
        return {}, HTTPStatus.OK

    # 판결문 스크랩 취소 api
    @jwt_required()
    def delete(self, case_serial_id):
        args = request.args
        consult_id = args.get("consult_id")

        # jwt에서 user_id 뽑아오기
        user_id = get_jwt_identity()

        # 데이터베이스에서 스크랩 삭제하기
        connection = get_mysql_connection()
        cursor = connection.cursor()

        # 아직 판결문을 스크랩하지 않았으면 에러
        query = """select * from bookmark where user_id = %s and case_id = %s and consult_id = %s"""
        param = (user_id, case_serial_id, consult_id)
        cursor.execute(query, param)
        result = cursor.fetchone()
        if result is None:
            return {"message": "아직 판결문을 스크랩하지 않았습니다."}, HTTPStatus.BAD_REQUEST

        # 스크랩 삭제하기
        query = """delete from bookmark where user_id = %s and case_id = %s and consult_id = %s"""
        param = (user_id, case_serial_id, consult_id)

        cursor.execute(query, param)
        connection.commit()

        cursor.close()
        connection.close()

        # 클라이언트에 응답
        return {}, HTTPStatus.OK


class ScrapListResource(Resource):

    # 스크랩 목록 조회 api
    @jwt_required()
    def get(self):
        # jwt에서 user_id 뽑아오기
        user_id = get_jwt_identity()

        # 데이터베이스에서
        connection = get_mysql_connection()
        cursor = connection.cursor()
        query = """select c.id as consult_id, c.content, cl.case_serial_id, cl.case_link as url
                    from lawbook.consult c
                        left join lawbook.bookmark b on c.id = b.consult_id
                        left join lawbook.case_law cl on b.case_id = cl.case_serial_id
                    where c.user_id = %s
                    order by consult_id desc"""
        param = (user_id,)
        cursor.execute(query, param)
        consults = cursor.fetchall()

        cursor.close()
        connection.close()

        consult_list = []

        # 상담글 리스트 만들기
        tmp_consult_id = -1
        for i in range(len(consults)):
            if consults[i][0] == tmp_consult_id:
                continue
            consult = {"consult_id": consults[i][0], "consult_content": consults[i][1], "scrap_list": []}
            consult_list.append(consult)

            tmp_consult_id = consults[i][0]

        # 상담글에 스크랩 리스트 만들기
        tmp_consult_id = -1
        consult_num = 0
        for i in range(len(consults)):
            if consult_num == len(consult_list):
                break

            if consults[i][0] != tmp_consult_id:
                if consults[i][2] is not None:
                    consult_num = consult_num + 1

                    response = requests.get(consults[i][3])
                    xd = XMLtoDict()
                    parse_response = xd.parse(response.content)

                    a = parse_response['PrecService']['법원명']
                    b = parse_response['PrecService']['선고일자']
                    c = parse_response['PrecService']['선고']
                    d = parse_response['PrecService']['사건번호']
                    e = parse_response['PrecService']['판결유형']
                    f = parse_response['PrecService']['사건명']

                    case = {'법원명': a, '선고일자': b, '선고': c, '사건번호': d, '판결유형': e, '사건명': f,
                            'case_serial_id': consults[i][2],
                            'url': consults[i][3]}

                    consult_list[consult_num - 1]["scrap_list"].append(case)
                else:
                    consult_num = consult_num + 1
            else:
                if consults[i][2] is not None:
                    response = requests.get(consults[i][3])
                    xd = XMLtoDict()
                    parse_response = xd.parse(response.content)

                    a = parse_response['PrecService']['법원명']
                    b = parse_response['PrecService']['선고일자']
                    c = parse_response['PrecService']['선고']
                    d = parse_response['PrecService']['사건번호']
                    e = parse_response['PrecService']['판결유형']
                    f = parse_response['PrecService']['사건명']

                    case = {'법원명': a, '선고일자': b, '선고': c, '사건번호': d, '판결유형': e, '사건명': f,
                            'case_serial_id': consults[i][2],
                            'url': consults[i][3]}

                    consult_list[consult_num - 1]["scrap_list"].append(case)

            tmp_consult_id = consults[i][0]

        # 클라이언트에 응답
        return {"consult_list": consult_list}, HTTPStatus.OK
