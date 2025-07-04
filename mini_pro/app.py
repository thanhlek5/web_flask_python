from flask import Flask, render_template, url_for, redirect,flash ,request 
from flask_login import LoginManager,login_user, logout_user,login_required,UserMixin
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash


# setup cấu hình
app = Flask(__name__)
app.config['SECRET_KEY'] = 'THNHAFgffb1342456'
app.config['SQLALCHEMY_DATABASE_URI'] = r'sqlite:///D:\PYTHON\flask\mini_pro\instance\user.db'

#  setup CSDL
db=SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# create users table
class User(UserMixin,db.Model):
    id = db.Column(db.Integer, primary_key = True)
    username = db.Column(db.String(150), unique = True)
    password = db.Column(db.String(200))

# get user in users table
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

#  home
@app.route('/')
@login_required
def home():
    return render_template('home.html')
# register function
@app.route('/register', methods = ['GET','POST'])
def register():  
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        exit_user = User.query.filter_by(username = username).first()
        #  check exting user
        if exit_user:
            flash('Tên đăng nhập đã tồn tại xin vui lòng nhập tên khác')
            return render_template('register.html')
        
        hashed_pw = generate_password_hash(password)
        user = User(username = username, password = hashed_pw)
        db.session.add(user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html')


# login fuction
@app.route('/login', methods = ['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username = username).first()
        if user is None:
            flash('Sai tên tài khoản, xin vui lòng nhập lại.')
            return render_template('login.html')
        if not check_password_hash(user.password, password):
            flash('Sai mật khẩu đăng nhập, xin vui lòng nhập lại mật khẩu.')
        login_user(user)
        return redirect(url_for('home'))
    return render_template('login.html')


# query user account
def select_all_user():
    users = db.session.query(User).all()
    user_dic = {}
    for user in users:
        user_dic[user.id] = user.username
    return user_dic

# user function
@app.route('/user')
@login_required
def user():
    users= select_all_user()
    print(users)
    return render_template('user.html', users = users )

# logout fuction
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))



if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug= True, port = 8080)