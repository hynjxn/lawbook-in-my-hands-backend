import requests
from flask import request
from flask_restful import Resource
from http import HTTPStatus
from db.db import get_mysql_connection
from flask_jwt_extended import jwt_required, get_jwt_identity
from gensim.models import Doc2Vec
from konlpy.tag import *
from xml_to_dict import XMLtoDict


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

        # 데이터베이스에서 상담 저장
        connection = get_mysql_connection()
        cursor = connection.cursor()
        query = """insert into consult (content, user_id) values (%s, %s);"""
        param = (data['content'], user_id)

        cursor.execute(query, param)
        connection.commit()

        consult_id = cursor.lastrowid

        cursor.close()
        connection.close()

        # doc2vec 모델로 유사한 판례 인덱스 찾기
        # 지금 모델은 임시용 -> 추후에 모델 다시 학습해야 함
        # 모델 학습시킬 때랑 똑같은 방법으로 전처리 진행해야 함

        # kom = Komoran()
        m = Mecab()
        doc2vec_model = Doc2Vec.load('doc2vec_model_mecab/vec_300_window_8_dm.model')

        inf_vector = doc2vec_model.infer_vector(m.nouns(data['content']))
        topn = 5
        result_list = doc2vec_model.docvecs.most_similar([inf_vector], topn=topn)

        id_list = []
        for i in range(topn):
            print("{}위, 유사도 :{}, tagID :{} ".format(i + 1, result_list[i][1], result_list[i][0]))
            id_list.append(int(result_list[i][0]))

        # print("유사도 높은 순으로 id 리스트 : ", id_list)

        # 데이터베이스에서 판례 조회
        connection = get_mysql_connection()
        cursor = connection.cursor()
        query = """select * from case_law c where c.id in ({list}) """.format(
            list=', '.join(str(i) for i in id_list))

        cursor.execute(query)
        result = cursor.fetchall()
        # print("old : ", result)  # 현재 result 리스트는 유사도 높은순이 아님

        cursor.close()
        connection.close()

        # 유사도 높은 순으로 result 리스트 생성
        new_result = []
        for i in range(len(result)):
            for j in range(len(result)):
                if result[j][0] == id_list[i]:
                    new_result.append(result[j])

        # print("new : ", new_result)

        # 조회한 판례의 url을 통해 데이터 가져오기
        case_list = []

        for i in range(len(new_result)):
            url = new_result[i][2]
            response = requests.get(url)
            xd = XMLtoDict()
            parse_response = xd.parse(response.content)
            # print("parse_response : ", parse_response)

            a = parse_response['PrecService']['법원명']
            b = parse_response['PrecService']['선고일자']
            c = parse_response['PrecService']['선고']
            d = parse_response['PrecService']['사건번호']
            e = parse_response['PrecService']['판결유형']
            f = parse_response['PrecService']['사건명']
            g = parse_response['PrecService']['판례정보일련번호']
            case_id = new_result[i][0]
            similarity = result_list[i][1]

            case = {'법원명': a, '선고일자': b, '선고': c, '사건번호': d, '판결유형': e, '사건명': f, 'case_id': case_id,
                    'case_serial_id': g, 'url': url, '유사도': similarity}
            case_list.append(case)

        # 클라이언트에 응답
        return {"consult_id": consult_id, "cases": case_list}, HTTPStatus.OK


class ConsultGetResource(Resource):

    # 이미 작성한 상담글로 판례 재검색 api
    @jwt_required()
    def get(self, consult_id):
        # 데이터베이스에서 consult_id로 상담글 조회
        connection = get_mysql_connection()
        cursor = connection.cursor()
        query = """select content from consult where id = %s;"""
        param = (consult_id,)

        cursor.execute(query, param)
        content = cursor.fetchone()

        cursor.close()
        connection.close()

        # doc2vec 모델로 유사한 판례 인덱스 찾기
        # 지금 모델은 임시용 -> 추후에 모델 다시 학습해야 함
        # 모델 학습시킬 때랑 똑같은 방법으로 전처리 진행해야 함
        m = Mecab()
        doc2vec_model = Doc2Vec.load('doc2vec_model_mecab/vec_300_window_8_dm.model')

        inf_vector = doc2vec_model.infer_vector(m.nouns(content[0]))
        topn = 5
        result_list = doc2vec_model.docvecs.most_similar([inf_vector], topn=topn)

        id_list = []
        for i in range(topn):
            print("{}위, 유사도 :{}, tagID :{} ".format(i + 1, result_list[i][1], result_list[i][0]))
            id_list.append(int(result_list[i][0]))
        # print("유사도 높은 순으로 id 리스트 : ", id_list)

        # 데이터베이스에서 판례 조회
        connection = get_mysql_connection()
        cursor = connection.cursor()
        query = """select * from case_law c where c.id in ({list}) """.format(
            list=', '.join(str(i) for i in id_list))

        cursor.execute(query)
        result = cursor.fetchall()
        # print("old : ", result)  # 현재 result 리스트는 유사도 높은순이 아님

        cursor.close()
        connection.close()

        # 유사도 높은 순으로 new result 리스트 생성
        new_result = []
        for i in range(len(result)):
            for j in range(len(result)):
                if result[j][0] == id_list[i]:
                    new_result.append(result[j])

        # print("new : ", new_result)

        # 조회한 판례의 url을 통해 데이터 가져오기
        case_list = []

        for i in range(len(new_result)):
            url = new_result[i][2]
            response = requests.get(url)
            xd = XMLtoDict()
            parse_response = xd.parse(response.content)
            # print("parse_response : ", parse_response)

            a = parse_response['PrecService']['법원명']
            b = parse_response['PrecService']['선고일자']
            c = parse_response['PrecService']['선고']
            d = parse_response['PrecService']['사건번호']
            e = parse_response['PrecService']['판결유형']
            f = parse_response['PrecService']['사건명']
            g = parse_response['PrecService']['판례정보일련번호']
            case_id = new_result[i][0]
            similarity = result_list[i][1]

            case = {'법원명': a, '선고일자': b, '선고': c, '사건번호': d, '판결유형': e, '사건명': f, 'case_id': case_id,
                    'case_serial_id': g, 'url': url, '유사도': similarity}
            case_list.append(case)

        # 클라이언트에 응답
        return {"consult_id": consult_id, "cases": case_list}, HTTPStatus.OK

    # 상담 삭제
    @jwt_required()
    def delete(self, consult_id):
        # 데이터베이스에서 consult_id로 상담글 삭제
        connection = get_mysql_connection()
        cursor = connection.cursor()

        query = """delete from bookmark where consult_id = %s;"""
        param = (consult_id,)
        cursor.execute(query, param)

        query = """delete from consult where id = %s;"""
        param = (consult_id,)
        cursor.execute(query, param)

        connection.commit()

        cursor.close()
        connection.close()

        # 클라이언트에 응답
        return {}, HTTPStatus.OK
