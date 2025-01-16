from flask import Flask, render_template, request, url_for, jsonify, flash, redirect, session
from werkzeug.security import generate_password_hash, check_password_hash
import os
from models import DBManager
from datetime import datetime
from functools import wraps

###수정 테스트!!!


app = Flask(__name__)
app.secret_key = 'your_secret_key'
app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static', 'uploads')
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

manager = DBManager()

@app.route('/')
def index():
    # 현재 페이지 번호 가져오기 (기본값 1)
    page = int(request.args.get('page', 1))
    per_page = 5  # 페이지당 게시글 수
    
    # 게시글 목록과 전체 페이지 수 가져오기
    posts, total_pages = manager.get_all_posts(page, per_page)
    
    # 세션에서 로그인 정보 가져오기
    uid = session.get('uid')
    uname = session.get('uname')
    
    return render_template('index.html', 
                         posts=posts,
                         uid=uid,
                         uname=uname,
                         current_page=page,
                         total_pages=total_pages)



@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        uid = request.form['uid']         # 사용자 아이디
        password = request.form['password']  # 입력된 비밀번호

        # 사용자 정보 가져오기
        user = manager.get_user_by_uid(uid)

        if user and user['password'] == password:  # 비밀번호 검증
        #if user and check_password_hash(user['password'], password):  # 비밀번호 검증
            session['uid'] = user['uid']  # 세션에 사용자 아이디 저장
            session['uname'] = user['uname']
            session['is_admin'] = user.get('is_admin', False)  # 관리자 여부 저장
            flash("로그인 성공!", "success")
            return redirect(url_for('index'))
        else:
            flash("로그인 실패: 아이디 또는 비밀번호를 확인하세요.", "danger")
            return redirect(url_for('login'))

    return render_template('login.html')




def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'uid' not in session:  # 세션 키를 'uid'로 통일
            flash("로그인이 필요합니다.", "danger")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


@app.route('/logout')
def logout():
    session.pop('uid', None)
    session.pop('uname', None)
    return redirect(url_for('index'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # 폼 데이터 가져오기
        uname = request.form['uname']  # 사용자 이름
        uid = request.form['uid']      # 사용자 아이디
        password = request.form['password']  # 비밀번호
        confirm_password = request.form['confirm_password']  # 비밀번호 확인

        # 비밀번호 확인
        if password != confirm_password:
            flash("비밀번호가 일치하지 않습니다.", "danger")
            return redirect(url_for('register'))

        # 비밀번호 해싱
        hashed_password = password

        # 데이터베이스에 사용자 추가
        if manager.insert_member(uid, hashed_password, uname):
            flash("회원가입이 완료되었습니다.", "success")
            return redirect(url_for('login'))
        else:
            flash("회원가입에 실패했습니다. 아이디가 중복되었을 수 있습니다.", "danger")
            return redirect(url_for('register'))

    return render_template('register.html')




@app.route('/post/<int:id>')
def view_post(id):
    post = manager.get_post_by_id(id)
    if not post:
        flash("게시글을 찾을 수 없습니다.", "danger")
        return redirect(url_for('index'))
    uid = session.get('uid')
    uname = session.get('uname')
    return render_template('view.html', post=post, uid=uid, uname=uname)


@app.route('/post/add', methods=['GET', 'POST'])
def add_post():
    user = session.get('uid')
    if not user:
        return redirect(url_for('login'))
        
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        file = request.files['file']
        filename = file.filename if file else None
        
        if filename:
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        
        # 사용자 정보 가져오기
        user_info = manager.get_user_by_uid(user)
        if manager.insert_post(title, content, filename, user_info['idx']):
            return redirect(url_for('index'))
        return "게시글 추가 실패", 400
    
    return render_template('add.html', user=user)

@app.route('/post/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_post(id):
    uid = session.get('uid')
    if not manager.check_post_permission(uid, id):
        flash("수정 권한이 없습니다.", "danger")
        return redirect(url_for('view_post', id=id))
    
    post = manager.get_post_by_id(id)
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        file = request.files['file']
        filename = file.filename if file else None
        
        if filename:
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        
        if manager.update_post(id, title, content, filename):
            return redirect(url_for('index'))
        return "게시글 수정 실패", 400
    
    return render_template('edit.html', post=post, uid=uid)


@app.route('/post/delete/<int:id>')
def delete_post(id):
    uid = session.get('uid')
    if not uid:
        return redirect(url_for('login'))
        
    if manager.delete_post(id):
        return redirect(url_for('index'))
    return "게시글 삭제 실패", 400


# 관리자 확인 데코레이터
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        uid = session.get('uid')
        if not uid or not is_admin(uid):
            flash("관리자 권한이 필요합니다.", "danger")
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

# 관리자 여부 확인 함수
def is_admin(uid):
    user = manager.get_user_by_uid(uid)
    return user and user.get('is_admin', False)

# 관리자 페이지 라우트
def is_admin(uid):
    user = manager.get_user_by_uid(uid)
    return user and user.get('is_admin', False)

@app.route('/admin')
@login_required
def admin_page():
    uid = session.get('uid')
    if not is_admin(uid):
        flash("관리자 권한이 필요합니다.", "danger")
        return redirect(url_for('index'))
    
    members = manager.get_all_members()
    return render_template('admin.html', members=members, uid=uid)

# 회원 상태 업데이트 API
@app.route('/admin/update_status', methods=['POST'])
@admin_required
def update_member_status():
    data = request.get_json()
    member_id = data.get('member_id')
    status = data.get('status')
    
    if manager.update_member_status(member_id, status):
        return jsonify({'success': True})
    return jsonify({'success': False})

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5005, debug=True)


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
