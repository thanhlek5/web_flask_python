from flask import Flask, render_template, url_for, redirect,flash, abort ,request 
from flask_login import LoginManager,login_user, logout_user,login_required,current_user,UserMixin
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
from datetime import *
from functools import wraps 
import re
import os
# ------------------------------------------------------------------------------setup app------------------------------------------
app = Flask(__name__)
app.config['SECRET_KEY'] = 'tetirgjkslvo1324314hh43hbhf4345j3h4gh5'
# app.config['SQLALCHEMY_DATABASE_URI'] = r'sqlite:///D:\PYTHON\flask\NOTES_WEB\instance\user.db'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mssql+pyodbc://test01:123@localhost/NOTE?driver=ODBC+Driver+17+for+SQL+Server'
app.config['SQLALCHEMEMY_TRACK_MODIFICATIONS'] = False
# setup uploads file [txt, png,...]
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGHT'] = 16*1024*1024 # giới hạn file là 16MB
# ---------------------------------tạo database--------------------------------------------
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# bảng người dùng 
class User(UserMixin,db.Model):
    id = db.Column(db.Integer, primary_key = True)
    username = db.Column(db.String(150), unique = True)
    password = db.Column(db.String(200))
    email = db.Column(db.String(200))
    notes = db.relationship('Note', backref = 'author', lazy = True)
    role = db.Column(db.String(100),default = 'user')
    

# bảng trung gian giữa  Note và tag 
note_tag = db.Table('note_tag',
                    db.Column('note_id',db.Integer,db.ForeignKey('note.id')),
                    db.Column('Tag_id',db.Integer,db.ForeignKey('tag.id'))
                    )
# bảng Note
class Note(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    title = db.Column(db.Unicode(500))
    content = db.Column(db.UnicodeText)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
        # khóa ngoại trỏ tới user.id
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    
    tags = db.relationship('Tag', secondary = note_tag, backref = 'notes')
# bảng tag
class Tag(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(100), unique = True)

# --------------------------------------------------------------tải dữ liệu người dùng-------------------------------------
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

#  base
@app.route('/')
def home():
    return render_template('base.html')
# main
@app.route('/main')
@login_required
def main():
    return render_template('main.html')

# --------------------------------------------------------------đăng nhập-------------------------------------------
@app.route('/login', methods = ['GET','POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        pw = request.form.get('password')
        user = User.query.filter_by(username = username).first()
        if not user:
            flash('Tài khoản không tồn tại hoặc nhập sai tên tài khoản!')
            return render_template('login.html')
        if not check_password_hash(user.password,pw):
            flash('Nhập sai mật khẩu')
            return render_template('login.html')
        if user and check_password_hash(user.password,pw):
            login_user(user)
            return redirect(url_for('main'))
    return render_template('login.html')

#---------------------------------------------------------------đăng ký------------------------------------------------------
@app.route('/register', methods = ['GET','POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        pw = request.form.get('password')
        email = request.form.get('email')
        print(username)
        print(pw)
        print(email)
        hashed_pw = generate_password_hash(pw)
        user = User(username = username, password = hashed_pw, email = email)
        exiting_user = User.query.filter_by(username = username).first()
        if not username or not pw or not email:
            flash('Hãy điền đầy đủ thông tin')
            return render_template('register.html')
        if exiting_user:
            flash('Tên tài khoản đã tồn tại')
            return render_template('register.html')
        db.session.add(user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html')
#  đăng xuất
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

#  làm sạch chuỗi tag
def clear_tag(tags):
    return re.findall(r'#\w+', tags)
# ----------------------------------------------------------------chức năng ghi chú----------------------------------------------------------------- 
@app.route('/add', methods = ['GET','POST'])
@login_required
def add():
    if request.method == 'POST':
        title = request.form.get('note_title')
        tag = request.form.get('Tag')
        print(tag)
        tag_raw = clear_tag(tag)
        print(tag_raw)
        content = request.form.get('note_content')
        user_id = current_user.id
        note = Note(title = title, content = content, user_id = user_id)
        for tag_text in tag_raw:
            tag_name = tag_text.lstrip('#')
            tag = Tag.query.filter_by(name = tag_name).first()
            if not tag:
                tag = Tag(name = tag_name)
                db.session.add(tag)
                note.tags.append(tag)
                
        db.session.add(note)
        db.session.commit()
        return redirect(url_for('main'))
    return render_template('add.html')

# ------------------------------------------sửa note--------------------------------
@app.route('/note/<int:note_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_note(note_id):
    note = Note.query.get_or_404(note_id)
    tags =note.tags
    

    # Kiểm tra quyền truy cập
    if note.user_id != current_user.id:
        abort(403)

    if request.method == 'POST':
        note.title = request.form.get('title')
        note.content = request.form.get('content')
        tag_input = request.form.get('tag')
        
        if tag_input:
            note.tags.clear()
            
            tag_list = tag_input.strip().split()
            for raw_tag in tag_list:
                tag_name = raw_tag.lstrip('#')
                tag = Tag.query.filter_by(name=tag_name).first()
                if not tag:
                    tag = Tag(name=tag_name)
                note.tags.append(tag)
        db.session.commit() 
        return redirect(url_for('note'))
    return render_template('edit_note.html', note=note, tags =tags)


#  ----------------------------------------------xóa ghi chú------------------------------------------
@app.route('/note/<int:note_id>/remove')
@login_required
def remove(note_id):
    note =  Note.query.get_or_404(note_id)
    if current_user.id != note.user_id:
        abort(403)
    db.session.delete(note)
    db.session.commit()
    return redirect(url_for('note'))    

# ---------------------------------------------hiện ghi chú--------------------------------------------
@app.route('/note')
@login_required
def note():
    notes = Note.query.filter_by(user_id = current_user.id).all()
    return render_template('note.html', notes = notes)
# --------------------------------------- Dùng để tạo tài khoản admin<----------------------------------------
# @app.route('/create_admin')
# def create_admin():
#     user = User(username = 'admin',password = generate_password_hash('1234'),email = 'admin123@gmail.com' ,role = 'admin')
#     db.session.add(user)
#     db.session.commit()
#     return redirect(url_for('login'))

# vào trang admin
@app.route('/admin')
@login_required
def admin():
    if current_user.role != 'admin':
        abort(403)
    return render_template('admin.html')
# --------------------------------uploads---------------------------------
@app.route('/upload', methods = ['GET',"POST"])
@login_required
def file_upload():
    if request.method == 'POST':
        file = request.files['file']
        if file:
            filename = secure_filename(file.filename)
            user_folder = os.path.join(app.config['UPLOAD_FOLDER'],str(current_user.id))
            os.makedirs(user_folder, exist_ok=True)
            file.save(os.path.join(user_folder,filename))
            return redirect(url_for('files'))
    return render_template('upload.html')
            
@app.route('/files')
@login_required
def files():
    user_folder = os.path.join(app.config['UPLOAD_FOLDER'], str(current_user.id))
    try:
        files = os.listdir(user_folder)
    except FileExistsError:
        files =[]
    return render_template('files.html', files = files)



#  run app
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=8080)