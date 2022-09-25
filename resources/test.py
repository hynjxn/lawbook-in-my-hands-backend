from flask import request
from flask_restful import Resource  # 리소스 위한 .
from http import HTTPStatus  # HTTP 상태코드 전송위한.
from db.db import get_mysql_connection


# 이 파일에서 작성하는 클래스는, 플라스크 프레임워크에서 경로랑 연결시킬 클래스이다.
# 따라서 클래스명 뒤에 상속한다는 Resource 클래스를 상속받아야한다.
# 플라스크 프레임워크의 레퍼런스에 나옴.
class TestResource(Resource):  # 괄호안에는 꼭 Resource로 상속받아야한다. 문법상!

    # get 메소드로 연결시킬 함수 작성
    def get(self):
        # 1. DB 커넥션을 가져온다
        connection = get_mysql_connection()  # 작성한 함수 사용

        # 2. 커넥션에서 커서를 가져온다.
        cursor = connection.cursor(dictionary=True)

        # 3. 쿼리문을 가져온다.
        query = """select * from user;"""  # user테이블에서 모든 정보 가져옴.

        # 4. sql 실행
        cursor.execute(query)

        # 5. 데이터를 페치
        records = cursor.fetchall()
        print(records)

        ret = []
        for row in records:
            ret.append(row)

        # 6. 커서와 커넥션을 닫아준다.
        cursor.close()
        connection.close()

        # 7. 클라이언트에 리스펀스 한다.
        return {'count': len(ret), 'ret': ret}, HTTPStatus.OK