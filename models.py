import mysql.connector
from datetime import datetime

class DBManager:
    def __init__(self):
        self.connection = None
        self.cursor = None

    def connect(self):
        self.connection = mysql.connector.connect(
            host='52.198.46.183',
            user='root',
            password='1234',
            database='board c_db2'
        )
        self.cursor = self.connection.cursor(dictionary=True)

    def disconnect(self):
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()

    def insert_member(self, uid, password, uname):
        """회원 정보 삽입"""
        try:
            self.connect()
            sql = """
                INSERT INTO members (uid, password, uname)
                VALUES (%s, %s, %s)
            """
            self.cursor.execute(sql, (uid, password, uname))
            self.connection.commit()
            return True
        except mysql.connector.Error as error:
            print(f"회원 정보 삽입 실패: {error}")
            return False
        finally:
            self.disconnect()

    def get_post_by_id(self, id):
        try:
            self.connect()
            sql = """
                SELECT p.*, m.uname, m.uid as author_uid, m.idx as author_idx
                FROM posts p 
                LEFT JOIN members m ON p.author_id = m.idx 
                WHERE p.id = %s
            """
            self.cursor.execute(sql, (id,))
            post = self.cursor.fetchone()
            if post:
                update_sql = "UPDATE posts SET views = views + 1 WHERE id = %s"
                self.cursor.execute(update_sql, (id,))
                self.connection.commit()
            return post
        finally:
            self.disconnect()




    def get_all_posts(self, page=1, per_page=10):
        try:
            self.connect()
            # 전체 게시글 수 조회
            self.cursor.execute("SELECT COUNT(*) as total FROM posts")
            total = self.cursor.fetchone()['total']
            
            # 페이지에 해당하는 게시글 조회
            offset = (page - 1) * per_page
            sql = """
                SELECT p.*, m.uname, m.uid as author_uid
                FROM posts p 
                LEFT JOIN members m ON p.author_id = m.idx 
                ORDER BY p.created_at DESC
                LIMIT %s OFFSET %s
            """
            self.cursor.execute(sql, (per_page, offset))
            posts = self.cursor.fetchall()
            
            # 전체 페이지 수 계산
            total_pages = (total + per_page - 1) // per_page
            
            return posts, total_pages
        except mysql.connector.Error as error:
            print(f"게시글 목록 조회 실패: {error}")
            return [], 0
        finally:
            self.disconnect()





    def insert_post(self, title, content, filename=None, author_id=None):
        try:
            self.connect()
            sql = """
                INSERT INTO posts (title, content, filename, author_id, created_at, updated_at, views)
                VALUES (%s, %s, %s, %s, NOW(), NOW(), 0)
            """
            values = (title, content, filename, author_id)
            self.cursor.execute(sql, values)
            self.connection.commit()
            return True
        except mysql.connector.Error as error:
            print(f"게시글 추가 실패: {error}")
            return False
        finally:
            self.disconnect()



    def update_post(self, id, title, content, filename=None):
        """게시글 수정"""
        try:
            self.connect()
            if filename:
                sql = "UPDATE posts SET title = %s, content = %s, filename = %s, updated_at = NOW() WHERE id = %s"
                values = (title, content, filename, id)
            else:
                sql = "UPDATE posts SET title = %s, content = %s, updated_at = NOW() WHERE id = %s"
                values = (title, content, id)
            
            self.cursor.execute(sql, values)
            self.connection.commit()
            return True
        except mysql.connector.Error as error:
            print(f"게시글 수정 실패: {error}")
            return False
        finally:
            self.disconnect()

    def delete_post(self, id):
        """게시글 삭제"""
        try:
            self.connect()
            sql = "DELETE FROM posts WHERE id = %s"
            self.cursor.execute(sql, (id,))
            self.connection.commit()
            return True
        except mysql.connector.Error as error:
            print(f"게시글 삭제 실패: {error}")
            return False
        finally:
            self.disconnect()

    def get_user_by_credentials(self, uid, password):
        """사용자 인증"""
        try:
            self.connect()
            sql = "SELECT idx, uid FROM members WHERE uid = %s AND password = %s"
            values = (uid, password)
            self.cursor.execute(sql, values)
            return self.cursor.fetchone()
        except mysql.connector.Error as error:
            print(f"사용자 인증 실패: {error}")
            return None
        finally:
            self.disconnect()


    def get_user_by_uid(self, uid):
        """아이디로 사용자 정보 가져오기"""
        try:
            self.connect()
            sql = "SELECT * FROM members WHERE uid=%s"
            self.cursor.execute(sql, (uid,))
            return self.cursor.fetchone()
        except mysql.connector.Error as error:
            print(f"사용자 조회 실패: {error}")
            return None
        finally:
            self.disconnect()


    def get_all_members(self):
        try:
            self.connect()
            sql = """
                SELECT idx, uid, uname, regdate 
                FROM members 
                ORDER BY regdate DESC
            """
            self.cursor.execute(sql)
            return self.cursor.fetchall()
        finally:
            self.disconnect()


    def update_member_status(self, member_id, status):
        try:
            self.connect()
            sql = "UPDATE members SET status = %s WHERE idx = %s"
            self.cursor.execute(sql, (status, member_id))
            self.connection.commit()
            return True
        except Exception as e:
            print(f"상태 업데이트 실패: {e}")
            return False
        finally:
            self.disconnect()

# models.py에 추가
    def create_admin_account(self):
        try:
            self.connect()
            # admin 계정 존재 여부 확인
            sql = "SELECT * FROM members WHERE uid = 'admin'"
            self.cursor.execute(sql)
            if not self.cursor.fetchone():
                # admin 계정 생성
                sql = """
                    INSERT INTO members (uid, password, uname, is_admin)
                    VALUES ('admin', 'admin', '관리자', TRUE)
                """
                self.cursor.execute(sql)
                self.connection.commit()
            return True
        except Exception as e:
            print(f"관리자 계정 생성 실패: {e}")
            return False
        finally:
            self.disconnect()



    # 게시글 수정/삭제 권한 확인 메서드
    def check_post_permission(self, user_id, post_id):
        try:
            self.connect()
            # 관리자 확인
            sql = "SELECT is_admin FROM members WHERE uid = %s"
            self.cursor.execute(sql, (user_id,))
            user = self.cursor.fetchone()
            return user and user['is_admin']
        finally:
            self.disconnect()
