from flask import Flask, render_template, url_for, redirect,flash, abort ,request 
from flask_login import LoginManager,login_user, logout_user,login_required,current_user,UserMixin
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import *
from functools import wraps 
# setup app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'tetirgjkslvo1324314hh43hbhf4345j3h4gh5'
app.config['SQLALCHEMY_DATABASE_URI'] = r'sqlite:///D:\PYTHON\flask\NOTES_WEB\instance\user.db'


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
    
    

# bảng Note
class Note(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    title = db.Column(db.String(100))
    content = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
        # khóa ngoại trỏ tới user.id
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

# tải dữ liệu người dùng
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

# đăng nhập
@app.route('/login', methods = ['GET','POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        pw = request.form.get('password')
        user = User.query.filter_by(username = username).first()
        if not check_password_hash(user.password,pw):
            flash('Nhập sai mật khẩu')
            return render_template('login.html')
        if user and check_password_hash(user.password,pw):
            login_user(user)
            return redirect(url_for('main'))
    return render_template('login.html')

#  đăng ký
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

#  chức năng ghi chú 
@app.route('/add', methods = ['GET','POST'])
@login_required
def add():
    if request.method == 'POST':
        title = request.form.get('note_title')
        content = request.form.get('note_content')
        user_id = current_user.id
        note = Note(title = title, content = content, user_id = user_id)
        db.session.add(note)
        db.session.commit()
        return redirect(url_for('main'))
    return render_template('add.html')

@app.route('/note/<int:note_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_note(note_id):
    note = Note.query.get_or_404(note_id)

    # Kiểm tra quyền truy cập
    if note.user_id != current_user.id:
        return "Không có quyền sửa ghi chú này", 403

    if request.method == 'POST':
        note.title = request.form.get('title')
        note.content = request.form.get('content')
        db.session.commit()  # 💾 Lưu lại thay đổi vào database
        # return redirect(url_for('note_detail', note_id=note.id))  # quay lại trang chi tiết
        return redirect(url_for('note'))
    return render_template('edit_note.html', note=note)


#  remove note 
@app.route('/note/<int:note_id>/remove')
@login_required
def remove(note_id):
    note =  Note.query.get_or_404(note_id)
    if current_user.id != note.user_id:
        return "Người dùng không thể xóa ghi chú này!!!"
    db.session.delete(note)
    db.session.commit()
    return redirect(url_for('note'))    


@app.route('/note')
@login_required
def note():
    notes = Note.query.filter_by(user_id = current_user.id).all()
    return render_template('note.html', notes = notes)




#  run app
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=8080)