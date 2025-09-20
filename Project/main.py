from flask import Flask, render_template, request, g, redirect, session
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.secret_key = "mysecretkey"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///blog.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class Result(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    mileage = db.Column(db.Float, nullable=False)
    electricity = db.Column(db.Float, nullable=False)
    meat = db.Column(db.Float, nullable=False)
    co2 = db.Column(db.Float, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return f"<Result {self.id}: {self.co2} кг СО2>"

def to_float(value):
    try:
        return float(value)
    except (ValueError, TypeError):
        return 0.0

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    results = db.relationship('Result', backref='user', lazy=True)

@app.before_request
def load_logged_in_user():
    user_id = session.get('user_id')
    if user_id is None:
        g.user = None
    else:
        g.user = User.query.get(user_id)


@app.route('/', methods=['GET', 'POST'])
def login():
    error =''
    if request.method == 'POST':
        form_login = request.form['username']
        form_password = request.form['password']

        users_db = User.query.all()
        for user in users_db:
            if form_login == user.username and form_password == user.password:
                session.clear()
                session['user_id'] = user.id
                return redirect('/index')
        else:
            error = 'Неверный логин или пароль'
            return render_template('login.html', error=error)
    else:
        return render_template('login.html')
    

@app.route('/reg', methods=['GET', 'POST'])
def reg():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if User.query.filter_by(username=username).first():
            return "Пользователь с таким именем уже существует!"
        
        user = User(username=username, password=password)
        db.session.add(user)
        db.session.commit()
        return redirect('/')
    
    else:
        return render_template('registration.html')

@app.route('/index', methods=['GET', 'POST'])
def index():
    if g.user is None:
        return redirect('/')

    result = None

    if request.method == 'POST':
        mileage = to_float(request.form.get('mileage'))
        electricity = to_float(request.form.get('electricity'))
        meat = to_float(request.form.get('meat'))

        co2_transport = mileage * 0.2
        co2_electricity = electricity * 0.4 * 12
        co2_diet = meat * 27 * 0.1
        co2_total = co2_transport + co2_electricity + co2_diet

        new_result = Result(
            mileage=mileage,
            electricity=electricity,
            meat=meat,
            co2=co2_total,
            user_id=g.user.id
        )
        db.session.add(new_result)
        db.session.commit()

    recent = Result.query.filter_by(user_id=g.user.id).order_by(Result.id.desc()).limit(5).all()

    if recent:
        last = recent[0]
        result ={
            'total': round(last.co2, 2),
            'transport': round(last.mileage * 0.2, 2),
            'electricity': round(last.electricity * 0.4 * 12, 2),
            'diet': round(last.meat * 27 * 0.1, 2)
        }
        mileage = last.mileage
        electricity = last.electricity
        meat = last.meat
    else:
        mileage = electricity = meat = 0.0

    return render_template(
        'index.html',
        result=result,
        mileage=mileage,
        electricity=electricity,
        meat=meat,
        recent=recent,
        username=g.user.username
    )

@app.route('/info')
def info():
    if g.user is None:
        return redirect('/')
    return render_template('info.html')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)