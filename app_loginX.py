from flask import Flask, render_template,request, url_for,jsonify,redirect,send_from_directory
import os
import json
from datetime import datetime
from models import DBManager

app = Flask(__name__)
# 상대 경로 app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path,'static','uploads')

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

manager = DBManager()


# 목록 보기 
@app.route('/')
def index():
    posts = manager.get_all_posts()
    return render_template('index.html', posts=posts)


# 내용 보기 
@app.route('/post/<int:id>')
def view_post(id):
    post = manager.get_post_by_id(id)
    return render_template('view.html', post=post)




# 내용 추가
# 파일 업로드 : enctype="multipart/form-data", method = 'POST', type='file', accecpt = ".png,.jpg,.gif"
@app.route('/post/add', methods=['GET','POST'])
def add_post():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        
        # 첨부파일 한 개
        file = request.files['file']
        filename = file.filename if file else None
        
        if filename:
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
      
        
        if manager.insert_post(title, content, filename):
            return redirect("/")
        return "게시글 추가 실패", 400
    return render_template('add.html')
        
@app.route('/post/edit/<int:id>', methods= ['GET','POST'])
def edit_post(id):
    post = manager.get_post_by_id(id)
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        
        # 첨부파일 한 개
        file = request.files['file']
        filename = file.filename if file else None
        
        if filename:
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            
        if manager.update_post(id,title,content,filename):
            return redirect("/")
        return "게시글 추가 실패",400
    return render_template('edit.html',post=post)
            

@app.route('/post/delete/<int:id>')
def delete_post(id):
    if manager.delete_post(id):
        return redirect(url_for('index'))
    return "게시글 삭제 실패",40            
            



if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5005, debug=True)