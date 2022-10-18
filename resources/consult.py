from flask import request
from flask_restful import Resource
from http import HTTPStatus
from db.db import get_mysql_connection
from flask_jwt_extended import jwt_required, get_jwt_identity
from gensim.models import Doc2Vec
from konlpy.tag import Komoran

# 신은수
kom = Komoran()
# df = pd.read_csv("data.csv")
doc2vec_model = Doc2Vec.load('/Users/minah/PycharmProjects/lawbook/lawbook-in-my-hands-backend/resources/d2v_judge_size200_min5_epoch20.model')

test = '방송사가 술에 취해 길에 쓰러졌던 40대 남자가 정신병원에 4년간이나 강제수용된 사실을 보도하면서, 정신보건법령상 제도의 운영상 문제점을 부각시키기 위하여 사실관계를 단순화시켜 그 일부 측면만을 강조하는 과정에서 취재된 정신병원의 사정을 방송 내용에 포함시키지 않았다 하더라도, 전체적인 맥락에서 방송 내용의 중요 부분이 진실에 합치함을 이유로 정정보도청구의 요건을 갖추지 못하였다고 한 사례'
print(test)
tokened_test = ['/'.join(word) for word in kom.pos(test)]

test = tokened_test
print(test)

topn = 5
test_vector = doc2vec_model.infer_vector(test)
result_list = doc2vec_model.docvecs.most_similar([test_vector], topn=topn)

for i in range(topn):
    print("{}위. {}, {}".format(i + 1, result_list[i][1], result_list[i][0]))


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
