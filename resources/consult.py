
import requests
from flask import request
from flask_restful import Resource
from http import HTTPStatus
from db.db import get_mysql_connection
from flask_jwt_extended import jwt_required, get_jwt_identity
from gensim.models import Doc2Vec
from konlpy.tag import Komoran
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
        kom = Komoran()
        doc2vec_model = Doc2Vec.load('doc2vec_model/d2v_judge_size200_min5_epoch20.model')

        test = data['content']

        tokened_test = ['/'.join(word) for word in kom.pos(test)]

        topn = 5
        test_vector = doc2vec_model.infer_vector(tokened_test)
        result_list = doc2vec_model.docvecs.most_similar([test_vector], topn=topn)

        index_list = []
        for i in range(topn):
            print("{}위, 유사도 :{}, 인덱스 :{} ".format(i + 1, result_list[i][1], result_list[i][0]))
            index_list.append(int(result_list[i][0]))

        # 데이터베이스에서 판례 조회
        connection = get_mysql_connection()
        cursor = connection.cursor()
        query = """select * from case_law c where c.case_serial_id in ({list}) """.format(
            list=', '.join(str(i) for i in index_list))

        cursor.execute(query)
        result = cursor.fetchall()
        print("result : ", result)

        cursor.close()
        connection.close()

        # 조회한 판례의 url을 통해 데이터 가져오기
        case_list = []

        for i in range(len(result)):
            url = result[i][2]
            response = requests.get(url)
            xd = XMLtoDict()
            parse_response = xd.parse(response.content)
            print("parse_response : ", parse_response)

            a = parse_response['PrecService']['법원명']
            b = parse_response['PrecService']['선고일자']
            c = parse_response['PrecService']['선고']
            d = parse_response['PrecService']['사건번호']
            e = parse_response['PrecService']['판결유형']
            f = parse_response['PrecService']['사건명']
            g = parse_response['PrecService']['판례정보일련번호']

            case = {'법원명': a, '선고일자': b, '선고': c, '사건번호': d, '판결유형': e, '사건명': f, 'case_serial_id': g, 'url': url}
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
        param = (consult_id, )

        cursor.execute(query, param)
        content = cursor.fetchone()

        cursor.close()
        connection.close()

        # doc2vec 모델로 유사한 판례 인덱스 찾기
        # 지금 모델은 임시용 -> 추후에 모델 다시 학습해야 함
        # 모델 학습시킬 때랑 똑같은 방법으로 전처리 진행해야 함
        kom = Komoran()
        doc2vec_model = Doc2Vec.load('doc2vec_model/d2v_judge_size200_min5_epoch20.model')

        test = content[0]
        tokened_test = ['/'.join(word) for word in kom.pos(test)]

        topn = 5
        test_vector = doc2vec_model.infer_vector(tokened_test)
        result_list = doc2vec_model.docvecs.most_similar([test_vector], topn=topn)

        index_list = []
        for i in range(topn):
            print("{}위, 유사도 :{}, 인덱스 :{} ".format(i + 1, result_list[i][1], result_list[i][0]))
            index_list.append(int(result_list[i][0]))

        # 데이터베이스에서 판례 조회
        connection = get_mysql_connection()
        cursor = connection.cursor()
        query = """select * from case_law c where c.case_serial_id in ({list}) """.format(
            list=', '.join(str(i) for i in index_list))

        cursor.execute(query)
        cases = cursor.fetchall()
        print("cases : ", cases)

        cursor.close()
        connection.close()

        # 조회한 판례의 url을 통해 데이터 가져오기
        case_list = []

        for i in range(len(cases)):
            url = cases[i][2]
            response = requests.get(url)
            xd = XMLtoDict()
            parse_response = xd.parse(response.content)

            a = parse_response['PrecService']['법원명']
            b = parse_response['PrecService']['선고일자']
            c = parse_response['PrecService']['선고']
            d = parse_response['PrecService']['사건번호']
            e = parse_response['PrecService']['판결유형']
            f = parse_response['PrecService']['사건명']
            g = parse_response['PrecService']['판례정보일련번호']

            case = {'법원명': a, '선고일자': b, '선고': c, '사건번호': d, '판결유형': e, '사건명': f, 'case_serial_id': g, 'url': url}
            case_list.append(case)

        # 클라이언트에 응답
        return {"consult_id": consult_id, "cases": case_list}, HTTPStatus.OK