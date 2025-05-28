import random
from datetime import datetime, timedelta
import datetime
from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import ForeignKey
from flask_login import LoginManager, UserMixin, current_user, login_user, logout_user, AnonymousUserMixin
import simpleaudio as sa
import soundfile
import pyttsx3
from backend import words_sorted, sents, words5
import unicodedata


#функция для приведения текста к одному стандарту
def normalize_text(text):
    #удаляем все неалфавитные символы и нормализуем строку
    text = unicodedata.normalize('NFKC', text)
    return text.strip()

#стимулы для задания с буквами
near_stims = 'фывапролджэё'
away_stims = 'фывапролджэёйцукенгшщзхъячсмитьбю'
all_stims = 'фывапролджэёйцукенгшщзхъячсмитьбю1234567890'
#типы заданий
ex_types = ['Задания с буквами', "Задания со слогами", "Задания со словами", "Задания с предложениями", "Случайные задания"]
#тексты с похвалой для того, чтобы выводить на сайт
good_words = ['Отлично! Ответ правильный.', "Вы ответили правильно, супер!", "Ответ правильный, молодец!"]

#гласные и согласные для заданий со слогами
wovels = 'уеыаоэёяию'
consonants = 'йцкнгшщзхфвпрлджчсмтб'

#задаем заранее значения стимулов для заданий с буквами и со слогами
stim = random.choice(near_stims)
stim2 = random.choice(consonants) + random.choice(wovels)

#создаем базу даннвых
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///answers.db"
app.config["SECRET_KEY"] = "ENTER YOUR SECRET KEY"
db = SQLAlchemy()


login_manager = LoginManager()
login_manager.init_app(app)
db.init_app(app)


#модели
class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column("id", db.Integer, primary_key=True)
    username = db.Column(db.String(250), unique=True, nullable=False)
    password = db.Column(db.String(250), nullable=False)
    words_to_go = db.Column("words_to_go", db.Text)
    sents_to_go = db.Column("sents_to_go", db.Text)


class Answer(db.Model):
    __tablename__ = "answers"
    answer_id = db.Column("answer_id", db.Integer, primary_key=True)
    time = db.Column("time", db.Float)
    type_of_exercise = db.Column("type_of_exercise", db.Text)
    exercise = db.Column("exercise", db.Text)
    answer = db.Column("answer", db.Text)
    mistake = db.Column("mistake", db.Boolean)
    user_id = db.Column('user', db.Integer, ForeignKey('users.id'))
    user = db.relationship('User')


with app.app_context():
    db.create_all()
    db.session.commit()

@login_manager.user_loader
def loader_user(user_id):
    return User.query.get(user_id)


#страница регистрации
@app.route('/register', methods=["GET", "POST"])
def register():
    if request.method == "POST":
        user = User(username=request.form.get("username"),
                     password=request.form.get("password"),
                    words_to_go=str(words_sorted)[2:-2],
                    sents_to_go=str(sents)[2:-2])
        db.session.add(user)
        db.session.commit()
        return redirect(url_for("login"))
    return render_template("sign_up.html")

#страница входа в аккунт
@app.route("/login", methods=["GET", "POST"])
def login():
    try:
        if request.method == "POST":
            user = User.query.filter_by(
                username=request.form.get("username")).first()
            if user.password == request.form.get("password"):
                login_user(user)
                return redirect(url_for("main"))
        return render_template("login.html")
    except AttributeError:
        return render_template("login_error.html")

#выход из аккаунта
@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("main"))

#переход на главную страницу
@app.route('/')
def index():
    return render_template('main.html')

#главная страница
@app.route('/main')
def main():
    if isinstance(current_user, AnonymousUserMixin):
        return render_template('main.html')
    else:
        return render_template('main.html', username=current_user.username)


###############################
#страница "буквы"
###############################
start = datetime.datetime.now()
previous_difference = []
previous_difference.append(timedelta(hours=0, minutes=0, seconds=0))
num_mists = 0
@app.route('/exercise', methods=['POST', "GET"])
def exercise():
    #задаем значения стимула и похвалу
    global num_mists
    global stim
    global good_words
    global near_stims
    global away_stims
    global all_stims
    message = ''

    if request.method == 'POST':
        #получаем ответ
        ans = request.form.get('exercise')
        #находим время, за которе ввели ответ
        diff = datetime.datetime.now() - start
        time_diff = diff - previous_difference[-1]
        previous_difference.append(diff)

        # приводим тексты к одному стандарту на всякий случай
        ans = normalize_text(ans)
        stim = normalize_text(stim)

        #если ответ правильный
        if ans == stim:
            num_mists = 0

            #выбираем похвалу, которая выведется на экран, и следующий стимул
            message = random.choice(good_words)

            #выбираем какую похвалу озвучиваем
            file_path = random.choice(["static/audio/good_result1.wav", "static/audio/good_result2.wav", "static/audio/good_result3.wav"])
            data, samplerate = soundfile.read(file_path)
            soundfile.write(file_path, data, samplerate)

            #проигрываем похвалу
            wave_obj = sa.WaveObject.from_wave_file(file_path)
            play = wave_obj.play()
            play.wait_done()
            play.stop()

            #если пользователь не зашел в аккаунт
            if isinstance(current_user, AnonymousUserMixin):
                #выбираем новый стимул случайно
                stim = random.choice(all_stims)
                # озвучка следующего задания
                try:
                    engine = pyttsx3.init()
                    engine.setProperty('rate', 130)
                    if stim in "кгнзврпджтб":
                        engine.say(f'Введите {stim}{stim}э')
                    elif stim == "ь":
                        engine.say(f'Введите мягкий знак')
                    elif stim == "ъ":
                        engine.say(f'Введите твердый знак')
                    else:
                        engine.say(f'Введите {stim}')
                    engine.startLoop()
                except RuntimeError:
                    engine.endLoop()
                    engine = pyttsx3.init()
                    engine.setProperty('rate', 130)
                    if stim in "кгнзврпджтб":
                        engine.say(f'Введите {stim}э')
                    else:
                        engine.say(f'Введите {stim}')
                    engine.runAndWait()


                return render_template('exercise.html', stim=stim, message=message)

            #если пользователь зашел в аккаунт
            else:
                # заносим информацию в базу данных
                answer = Answer(time=float(time_diff.total_seconds()),
                                type_of_exercise=ex_types[0],
                                exercise=stim,
                                answer=ans,
                                mistake=False,
                                user_id=current_user.id)
                db.session.add(answer)
                db.session.commit()

                #для назначения нового стимула проверяем, сколько времени пользователь занимается в блоке "буквы"
                users_answers = Answer.query.filter_by(user_id=current_user.id).all()
                time1 = 0
                for answ in users_answers:
                    if answ.type_of_exercise == ex_types[0]:
                        time1 += float(answ.time)
                #после 5 минут с буквами добавляем 2 ряды
                if time1 >= 300.0:
                    if time1 < 600.0:
                        stim = random.choice(away_stims)
                    #после 10 минут с буквами добавляем 3 ряды
                    elif time1 >= 600.0:
                        stim = random.choice(all_stims)
                else:
                    stim = random.choice(near_stims)

                #озвучка следующего задания
                try:
                    engine = pyttsx3.init()
                    engine.setProperty('rate', 130)
                    if stim in "кгнзврпджтб":
                        engine.say(f'Введите {stim}э')
                    elif stim == "ь":
                        engine.say(f'Введите мягкий знак')
                    elif stim == "ъ":
                        engine.say(f'Введите твердый знак')
                    else:
                        engine.say(f'Введите {stim}')
                    engine.startLoop()
                except RuntimeError:
                    engine.endLoop()
                    engine = pyttsx3.init()
                    engine.setProperty('rate', 130)
                    if stim in "кгнзврпджтб":
                        engine.say(f'Введите {stim}э')
                    elif stim == "ь":
                        engine.say(f'Введите мягкий знак')
                    elif stim == "ъ":
                        engine.say(f'Введите твердый знак')
                    else:
                        engine.say(f'Введите {stim}')
                    engine.runAndWait()

                return render_template('exercise.html', stim=stim, message=message)

        #если ответ неправильный
        else:
            num_mists += 1
            message = "К сожалению, неверно."

            # выбираем какую похвалу ощвучиваем
            file_path = random.choice(
                ["static/audio/bad_result1.wav", "static/audio/bad_result2.wav"])
            data, samplerate = soundfile.read(file_path)
            soundfile.write(file_path, data, samplerate)

            # проигрываем похвалу
            wave_obj = sa.WaveObject.from_wave_file(file_path)
            play = wave_obj.play()
            play.wait_done()
            play.stop()

            #если пользователь не вошел в аккаунт
            if isinstance(current_user, AnonymousUserMixin):
                #если еще не совершено 3 ошибок в одном месте
                if num_mists <= 2:
                # озвучка следующего задания
                    try:
                        engine = pyttsx3.init()
                        engine.setProperty('rate', 130)
                        if stim in "кгнзврпджтб":
                            engine.say(f'Введите {stim}э')
                        else:
                            engine.say(f'Введите {stim}')
                        engine.startLoop()
                    except RuntimeError:
                        engine.endLoop()
                        engine = pyttsx3.init()
                        engine.setProperty('rate', 130)
                        if stim in "кгнзврпджтб":
                            engine.say(f'Введите {stim}э')
                        else:
                            engine.say(f'Введите {stim}')
                        engine.runAndWait()

                    return render_template('exercise.html', stim=stim, message=message)
                #если ошибок слишком много
                else:
                    num_mists = 0
                    #назначается новый стимул
                    stim = random.choice(all_stims)

                    # озвучка следующего задания
                    try:
                        engine = pyttsx3.init()
                        engine.setProperty('rate', 130)
                        if stim in "кгнзврпджтб":
                            engine.say(f'Введите {stim}э')
                        else:
                            engine.say(f'Введите {stim}')
                        engine.startLoop()

                    except RuntimeError:
                        engine.endLoop()
                        engine = pyttsx3.init()
                        engine.setProperty('rate', 130)
                        if stim in "кгнзврпджтб":
                            engine.say(f'Введите {stim}э')
                        else:
                            engine.say(f'Введите {stim}')
                        engine.runAndWait()

                    return render_template('exercise.html', stim=stim, message=message)

            #если пользователь зашел в аккаунт
            else:
                #записываем информацию об ошибке в базу
                answer = Answer(time=float(time_diff.total_seconds()),
                                type_of_exercise=ex_types[0],
                                exercise=stim,
                                answer=ans,
                                mistake=True,
                                user_id=current_user.id)
                db.session.add(answer)
                db.session.commit()

                #если ошибок с этим стимулом не слишком много
                if num_mists <= 2:
                    # озвучка следующего задания
                    try:
                        engine = pyttsx3.init()
                        engine.setProperty('rate', 130)
                        if stim in "кгнзврпджтб":
                            engine.say(f'Введите {stim}э')
                        else:
                            engine.say(f'Введите {stim}')
                        engine.startLoop()
                    except RuntimeError:
                        engine.endLoop()

                        engine = pyttsx3.init()
                        engine.setProperty('rate', 130)

                        if stim in "кгнзврпджтб":
                            engine.say(f'Введите {stim}э')
                        else:
                            engine.say(f'Введите {stim}')
                        engine.runAndWait()
                    return render_template('exercise.html', stim=stim, message=message)
                #если ошибок слишком много выбирается новый стимул
                else:
                    #проверка сколько времени пользователь выполняет упражнения с буквами
                    users_answers = Answer.query.filter_by(user_id=current_user.id).all()
                    time1 = 0
                    for answ in users_answers:
                        if answ.type_of_exercise == ex_types[0]:
                            time1 += float(answ.time)
                    if time1 >= 300.0:
                        if time1 < 600.0:
                            stim = random.choice(away_stims)
                        elif time1 >= 600.0:
                            stim = random.choice(all_stims)
                    else:
                        stim = random.choice(near_stims)

                    # озвучка следующего задания
                    try:
                        engine = pyttsx3.init()
                        engine.setProperty('rate', 130)
                        if stim in "кгнзврпджтб":
                            engine.say(f'Введите {stim}э')
                        else:
                            engine.say(f'Введите {stim}')
                        engine.startLoop()

                    except RuntimeError:
                        engine.endLoop()
                        engine = pyttsx3.init()
                        engine.setProperty('rate', 130)
                        if stim in "кгнзврпджтб":
                            engine.say(f'Введите {stim}э')
                        else:
                            engine.say(f'Введите {stim}')
                        engine.runAndWait()

                    num_mists = 0
                    return render_template('exercise.html', stim=stim, message=message)
    # озвучка задания
    try:
        engine = pyttsx3.init()
        engine.setProperty('rate', 130)
        if stim in "кгнзврпджтб":
            engine.say(f'Введите {stim}э')
        else:
            engine.say(f'Введите {stim}')
        engine.startLoop()

    except RuntimeError:
        engine.endLoop()
        engine = pyttsx3.init()
        engine.setProperty('rate', 130)
        if stim in "кгнзврпджтб":
            engine.say(f'Введите {stim}э')
        else:
            engine.say(f'Введите {stim}')
        engine.runAndWait()

    return render_template('exercise.html', stim=stim, message=message)


###############################
#страница "слоги"
###############################
start = datetime.datetime.now()
previous_difference = []
previous_difference.append(timedelta(hours=0, minutes=0, seconds=0))
num_mists2 = 0
@app.route('/exercise2', methods=['POST', "GET"])
def exercise2():
    #задаем значения стимула и похвалу
    global stim2
    global good_words
    global wovels
    global consonants
    global num_mists2
    message = ''

    if request.method == 'POST':
        #получаем ответ
        ans = request.form.get('exercise')
        #находим время, за которе ввели ответ
        diff = datetime.datetime.now() - start
        time_diff = diff - previous_difference[-1]
        previous_difference.append(diff)


        # приводим тексты к одному стандарту на всякий случай
        ans = normalize_text(ans)
        stim2 = normalize_text(stim2)

        #если ответ правильный
        if ans == stim2:
            num_mists2 = 0

            #выбираем похвалу, которая выведется на экран, и следующий стимул
            message = random.choice(good_words)
            stim2 = random.choice(consonants) + random.choice(wovels)

            #выбираем какую похвалу озвучиваем
            file_path = random.choice(["static/audio/good_result1.wav", "static/audio/good_result2.wav", "static/audio/good_result3.wav"])
            data, samplerate = soundfile.read(file_path)
            soundfile.write(file_path, data, samplerate)

            #проигрываем похвалу
            wave_obj = sa.WaveObject.from_wave_file(file_path)
            play = wave_obj.play()
            play.wait_done()
            play.stop()

            #если пользователь не зашел в аккаунт
            if isinstance(current_user, AnonymousUserMixin):
                # озвучка следующего задания
                try:
                    engine = pyttsx3.init()
                    engine.setProperty('rate', 130)
                    engine.say(f'Введите {stim2}')
                    engine.startLoop()

                except RuntimeError:
                    engine.endLoop()
                    engine = pyttsx3.init()
                    engine.setProperty('rate', 130)
                    engine.say(f'Введите {stim2}')
                    engine.runAndWait()
                return render_template('exercise2.html', stim=stim2, message=message)

            #если пользователь зашел в аккаунт
            else:
                # заносим информацию в базу данных
                answer = Answer(time=float(time_diff.total_seconds()),
                                type_of_exercise=ex_types[1],
                                exercise=stim2,
                                answer=ans,
                                mistake=False,
                                user_id=current_user.id)
                db.session.add(answer)
                db.session.commit()

                # озвучка следующего задания
                try:
                    engine = pyttsx3.init()
                    engine.setProperty('rate', 130)
                    engine.say(f'Введите {stim2}')
                    engine.startLoop()

                except RuntimeError:
                    engine.endLoop()
                    engine = pyttsx3.init()
                    engine.setProperty('rate', 130)
                    engine.say(f'Введите {stim2}')
                    engine.runAndWait()

                return render_template('exercise2.html', stim=stim2, message=message)

        #если ответ неправильный
        else:
            num_mists2 += 1
            message = "К сожалению, неверно."

            # выбираем какую похвалу озвучиваем
            file_path = random.choice(
                ["static/audio/bad_result1.wav", "static/audio/bad_result2.wav"])
            data, samplerate = soundfile.read(file_path)
            soundfile.write(file_path, data, samplerate)

            # проигрываем похвалу
            wave_obj = sa.WaveObject.from_wave_file(file_path)
            play = wave_obj.play()
            play.wait_done()
            play.stop()

            #если пользователь не зашел в аккаунт
            if isinstance(current_user, AnonymousUserMixin):
                #если ошибок с нынешним стимулом не слишком много
                if num_mists2 <= 2:

                # озвучка следующего задания
                    try:
                        engine = pyttsx3.init()
                        engine.setProperty('rate', 130)
                        engine.say(f'Введите {stim2}')
                        engine.startLoop()

                    except RuntimeError:
                        engine.endLoop()
                        engine = pyttsx3.init()
                        engine.setProperty('rate', 130)
                        engine.say(f'Введите {stim2}')
                        engine.runAndWait()
                    return render_template('exercise2.html', stim=stim2, message=message)

                #если ошибок с нынешним стимулом слишком много
                else:
                    stim2 = random.choice(consonants) + random.choice(wovels)
                    # озвучка следующего задания
                    try:
                        engine = pyttsx3.init()
                        engine.setProperty('rate', 130)
                        engine.say(f'Введите {stim2}')
                        engine.startLoop()

                    except RuntimeError:
                        engine.endLoop()
                        engine = pyttsx3.init()
                        engine.setProperty('rate', 130)
                        engine.say(f'Введите {stim2}')
                        engine.runAndWait()
                    return render_template('exercise2.html', stim=stim2, message=message)

            #если пользователь зашел в аккаунт
            else:
                #заносим информацию в базу данных
                answer = Answer(time=float(time_diff.total_seconds()),
                                type_of_exercise=ex_types[1],
                                exercise=stim2,
                                answer=ans,
                                mistake=True,
                                user_id=current_user.id)
                db.session.add(answer)
                db.session.commit()

                #если ошибок с нынешним стимулом не слишком много
                if num_mists2 <= 2:
                    # озвучка следующего задания
                    try:
                        engine = pyttsx3.init()
                        engine.setProperty('rate', 130)
                        engine.say(f'Введите {stim2}')
                        engine.startLoop()

                    except RuntimeError:
                        engine.endLoop()
                        engine = pyttsx3.init()
                        engine.setProperty('rate', 130)
                        engine.say(f'Введите {stim2}')
                        engine.runAndWait()
                    return render_template('exercise2.html', stim=stim2, message=message)

                #если ошибок с нынешним стимулом было три, то назначаем новый стимул
                else:
                    num_mists2 = 0
                    stim2 = random.choice(consonants) + random.choice(wovels)

                    # озвучка следующего задания
                    try:
                        engine = pyttsx3.init()
                        engine.setProperty('rate', 130)
                        engine.say(f'Введите {stim2}')
                        engine.startLoop()

                    except RuntimeError:
                        engine.endLoop()
                        engine = pyttsx3.init()
                        engine.setProperty('rate', 130)
                        engine.say(f'Введите {stim2}')
                        engine.runAndWait()
                    return render_template('exercise2.html', stim=stim2, message=message)
    #озвучка задания
    try:
        engine = pyttsx3.init()
        engine.setProperty('rate', 130)
        engine.say(f'Введите {stim2}')
        engine.startLoop()

    except RuntimeError:
        engine.endLoop()
        engine = pyttsx3.init()
        engine.setProperty('rate', 130)
        engine.say(f'Введите {stim2}')
        engine.runAndWait()
    return render_template('exercise2.html', stim=stim2, message=message)



###############################
#страница "слова"
###############################
start = datetime.datetime.now()
previous_difference = []
previous_difference.append(timedelta(hours=0, minutes=0, seconds=0))
num_mists3 = 0
stim3 = random.choice(words_sorted)
@app.route('/exercise3', methods=['POST', "GET"])
def exercise3():
    # задаем значения стимула и похвалу
    global good_words
    global num_mists3
    global stim3
    #если пользователь зашел в аккаунт, то берем его список слов
    if not isinstance(current_user, AnonymousUserMixin):
        w_t_g = current_user.words_to_go
        #если список закончился, то обновляем его переменной words_sorted
        if current_user.words_to_go == "":
            current_user.words_to_go = str(words_sorted)[2:-2]
            db.session.commit()
        #стимулом выбираем первое слово из списка
        stim3 = w_t_g.split("', '")[0]

    message = ''

    if request.method == 'POST':
        # получаем ответ
        ans = request.form.get('exercise')
        # находим время, за которе ввели ответ
        diff = datetime.datetime.now() - start
        time_diff = diff - previous_difference[-1]
        previous_difference.append(diff)

        #приводим тексты к одному стандарту на всякий случай
        ans = normalize_text(ans)
        stim3 = normalize_text(stim3)

        # если ответ правильный
        if ans == stim3:
            num_mists3 = 0

            # выбираем похвалу, которая выведется на экран, и следующий стимул
            message = random.choice(good_words)

            # выбираем какую похвалу озвучиваем
            file_path = random.choice(
                ["static/audio/good_result1.wav", "static/audio/good_result2.wav", "static/audio/good_result3.wav"])
            data, samplerate = soundfile.read(file_path)
            soundfile.write(file_path, data, samplerate)

            # проигрываем похвалу
            wave_obj = sa.WaveObject.from_wave_file(file_path)
            play = wave_obj.play()
            play.wait_done()
            play.stop()

            #если пользователь не вошел в аккаунт, даем случайный следующий стимул
            if isinstance(current_user, AnonymousUserMixin):
                stim3 = random.choice(words_sorted)
                # озвучка следующего задания
                try:
                    engine = pyttsx3.init()
                    engine.setProperty('rate', 130)
                    engine.say(f'Введите {stim3}')
                    engine.startLoop()

                except RuntimeError:
                    engine.endLoop()
                    engine = pyttsx3.init()
                    engine.setProperty('rate', 130)
                    engine.say(f'Введите {stim3}')
                    engine.runAndWait()
                return render_template('exercise3.html', stim=stim3, message=message)

            #если пользователь вошел в аккаунт
            else:

                #обновляем переменную words_to_go - убираем правильно введенное слово
                current_user.words_to_go = str(current_user.words_to_go.split("', '")[1:])[2:-2]
                db.session.commit()

                #если список закончился, записываем в переменную весь список words_sorted
                if current_user.words_to_go == "":
                    current_user.words_to_go = str(words_sorted)[2:-2]
                    db.session.commit()


                # заносим информацию в базу данных
                answer = Answer(time=float(time_diff.total_seconds()),
                                type_of_exercise=ex_types[2],
                                exercise=stim3,
                                answer=ans,
                                mistake=False,
                                user_id=current_user.id)
                db.session.add(answer)
                db.session.commit()

                #следующим стимулом даем первое слово из words_to_go
                w_t_g = current_user.words_to_go
                stim3 = w_t_g.split("', '")[0]

                # озвучка следующего задания
                try:
                    engine = pyttsx3.init()
                    engine.setProperty('rate', 130)
                    engine.say(f'Введите {stim3}')
                    engine.startLoop()

                except RuntimeError:
                    engine.endLoop()
                    engine = pyttsx3.init()
                    engine.setProperty('rate', 130)
                    engine.say(f'Введите {stim3}')
                    engine.runAndWait()

                return render_template('exercise3.html', stim=stim3, message=message)

        # если ответ неправильный
        else:
            num_mists3 += 1
            message = "К сожалению, неверно."

            # выбираем какую похвалу ощвучиваем
            file_path = random.choice(
                ["static/audio/bad_result1.wav", "static/audio/bad_result2.wav"])
            data, samplerate = soundfile.read(file_path)
            soundfile.write(file_path, data, samplerate)

            # проигрываем похвалу
            wave_obj = sa.WaveObject.from_wave_file(file_path)
            play = wave_obj.play()
            play.wait_done()
            play.stop()

            #если пользователь не зашел в аккаунт, выдаем следующий стимул случайно
            if isinstance(current_user, AnonymousUserMixin):
                stim3 = random.choice(words_sorted)

                # озвучка следующего задания
                try:
                    engine = pyttsx3.init()
                    engine.setProperty('rate', 130)
                    engine.say(f'Введите {stim3}')
                    engine.startLoop()

                except RuntimeError:
                    engine.endLoop()
                    engine = pyttsx3.init()
                    engine.setProperty('rate', 130)
                    engine.say(f'Введите {stim3}')
                    engine.runAndWait()
                return render_template('exercise3.html', stim=stim3, message=message)

            #если пользователь зашел в аккаунт
            else:
                #заносим информацию об ошибке в базу
                answer = Answer(time=float(time_diff.total_seconds()),
                                type_of_exercise=ex_types[2],
                                exercise=stim3,
                                answer=ans,
                                mistake=True,
                                user_id=current_user.id)
                db.session.add(answer)
                db.session.commit()

                #если ошибок не много
                if num_mists3 <= 2:

                    # озвучка следующего задания
                    try:
                        engine = pyttsx3.init()
                        engine.setProperty('rate', 130)
                        engine.say(f'Введите {stim3}')
                        engine.startLoop()

                    except RuntimeError:
                        engine.endLoop()
                        engine = pyttsx3.init()
                        engine.setProperty('rate', 130)
                        engine.say(f'Введите {stim3}')
                        engine.runAndWait()
                    return render_template('exercise3.html', stim=stim3, message=message)

                #если ошибки уже три, то записываем текущий стимул в конец списка words_to_go
                else:
                    num_mists3 = 0

                    left_words = current_user.words_to_go.split("', '")[1:]
                    left_words.append(stim3)

                    current_user.words_to_go = str(left_words)[2:-2]
                    db.session.commit()

                    #новым стимулом назначаем следующее слово из words_to_go
                    w_t_g = current_user.words_to_go
                    stim3 = w_t_g.split("', '")[0]

                    # озвучка следующего задания
                    try:
                        engine = pyttsx3.init()
                        engine.setProperty('rate', 130)
                        engine.say(f'Введите {stim3}')
                        engine.startLoop()

                    except RuntimeError:
                        engine.endLoop()
                        engine = pyttsx3.init()
                        engine.setProperty('rate', 130)
                        engine.say(f'Введите {stim3}')
                        engine.runAndWait()


                    return render_template('exercise3.html', stim=stim3, message=message)

    # озвучка следующего задания
    try:
        engine = pyttsx3.init()
        engine.setProperty('rate', 130)
        engine.say(f'Введите {stim3}')
        engine.startLoop()

    except RuntimeError:
        engine.endLoop()
        engine = pyttsx3.init()
        engine.setProperty('rate', 130)
        engine.say(f'Введите {stim3}')
        engine.runAndWait()
    return render_template('exercise3.html', stim=stim3, message=message)



###############################
#страница "предложения"
###############################
start = datetime.datetime.now()
previous_difference = []
previous_difference.append(timedelta(hours=0, minutes=0, seconds=0))
num_mists4 = 0
stim4 = random.choice(sents)
@app.route('/exercise4', methods=['POST', "GET"])
def exercise4():
    # задаем значения стимула и похвалу
    global good_words
    global num_mists4
    global stim4
    global sents

    #если пользователь зашел в аккаунт, то стимул — первое предложения из переменной sents_to_go
    if not isinstance(current_user, AnonymousUserMixin):
        s_t_g = current_user.sents_to_go

        if current_user.sents_to_go == "":
            current_user.sents_to_go = str(sents)[2:-2]
            db.session.commit()
        stim4 = s_t_g.split("', '")[0]

    message = ''

    if request.method == 'POST':
        # получаем ответ
        ans = request.form.get('exercise')
        # находим время, за которе ввели ответ
        diff = datetime.datetime.now() - start
        time_diff = diff - previous_difference[-1]
        previous_difference.append(diff)

        ans = normalize_text(ans)
        stim4 = normalize_text(stim4)

        # если ответ правильный
        if ans == stim4:
            num_mists4 = 0

            # выбираем похвалу, которая выведется на экран, и следующий стимул
            message = random.choice(good_words)

            # выбираем какую похвалу озвучиваем
            file_path = random.choice(
                ["static/audio/good_result1.wav", "static/audio/good_result2.wav", "static/audio/good_result3.wav"])
            data, samplerate = soundfile.read(file_path)
            soundfile.write(file_path, data, samplerate)

            # проигрываем похвалу
            wave_obj = sa.WaveObject.from_wave_file(file_path)
            play = wave_obj.play()
            play.wait_done()
            play.stop()

            #если пользователь не зашел в аккаунт, выбираем стимулом случайное предложение
            if isinstance(current_user, AnonymousUserMixin):
                stim4 = random.choice(sents)

                # озвучка следующего задания
                try:
                    engine = pyttsx3.init()
                    engine.setProperty('rate', 130)
                    engine.say(f'Введите {stim4}')
                    engine.startLoop()

                except RuntimeError:
                    engine.endLoop()
                    engine = pyttsx3.init()
                    engine.setProperty('rate', 130)
                    engine.say(f'Введите {stim4}')
                    engine.runAndWait()

                return render_template('exercise4.html', stim=stim4, message=message)

            # если пользователь зашел в аккаунт
            else:
                #убираем правильно введенное предложения из списка sents_to_go
                current_user.sents_to_go = str(current_user.sents_to_go.split("', '")[1:])[2:-2]
                db.session.commit()
                if current_user.sents_to_go == "":
                    current_user.sents_to_go = str(sents)[2:-2]
                    db.session.commit()

                # заносим информацию в базу данных
                answer = Answer(time=float(time_diff.total_seconds()),
                                type_of_exercise=ex_types[3],
                                exercise=stim4,
                                answer=ans,
                                mistake=False,
                                user_id=current_user.id)
                db.session.add(answer)
                db.session.commit()

                s_t_g = current_user.sents_to_go
                stim4 = s_t_g.split("', '")[0]

                # озвучка следующего задания
                try:
                    engine = pyttsx3.init()
                    engine.setProperty('rate', 130)
                    engine.say(f'Введите {stim4}')
                    engine.startLoop()

                except RuntimeError:
                    engine.endLoop()
                    engine = pyttsx3.init()
                    engine.setProperty('rate', 130)
                    engine.say(f'Введите {stim4}')
                    engine.runAndWait()

                return render_template('exercise4.html', stim=stim4, message=message)

        # если ответ неправильный
        else:
            num_mists4 += 1
            message = "К сожалению, неверно."

            # выбираем какую похвалу ощвучиваем
            file_path = random.choice(
                ["static/audio/bad_result1.wav", "static/audio/bad_result2.wav"])
            data, samplerate = soundfile.read(file_path)
            soundfile.write(file_path, data, samplerate)

            # проигрываем похвалу
            wave_obj = sa.WaveObject.from_wave_file(file_path)
            play = wave_obj.play()
            play.wait_done()
            play.stop()

            #если пользователь не зашел в аккаунт, выбираем следующий стимул случайно
            if isinstance(current_user, AnonymousUserMixin):
                stim4 = random.choice(sents)
                # озвучка следующего задания
                try:
                    engine = pyttsx3.init()
                    engine.setProperty('rate', 130)
                    engine.say(f'Введите {stim4}')
                    engine.startLoop()

                except RuntimeError:
                    engine.endLoop()
                    engine = pyttsx3.init()
                    engine.setProperty('rate', 130)
                    engine.say(f'Введите {stim4}')
                    engine.runAndWait()
                return render_template('exercise4.html', stim=stim4, message=message)

            #если пользоваттель зашел в аккаунт
            else:
                #заносим информацию об ответе в базу данных
                answer = Answer(time=float(time_diff.total_seconds()),
                                type_of_exercise=ex_types[3],
                                exercise=stim4,
                                answer=ans,
                                mistake=True,
                                user_id=current_user.id)
                db.session.add(answer)
                db.session.commit()

                #если не больше 2 ошибок с этим предложением, оставляем этот стимул
                if num_mists4 <= 2:
                    # озвучка следующего задания
                    try:
                        engine = pyttsx3.init()
                        engine.setProperty('rate', 130)
                        engine.say(f'Введите {stim4}')
                        engine.startLoop()

                    except RuntimeError:
                        engine.endLoop()
                        engine = pyttsx3.init()
                        engine.setProperty('rate', 130)
                        engine.say(f'Введите {stim4}')
                        engine.runAndWait()
                    return render_template('exercise4.html', stim=stim4, message=message)

                #если слишком много ошибок, то переходим кследующему стимулу в списке sents_to_go
                else:
                    num_mists4 = 0

                    left_sents = current_user.sents_to_go.split("', '")[1:]
                    left_sents.append(stim4)

                    current_user.sents_to_go = str(left_sents)[2:-2]
                    db.session.commit()

                    if current_user.sents_to_go == "":
                        current_user.sents_to_go = str(sents)[2:-2]
                        db.session.commit()

                    s_t_g = current_user.sents_to_go
                    stim4 = s_t_g.split("', '")[0]

                    # озвучка следующего задания
                    try:
                        engine = pyttsx3.init()
                        engine.setProperty('rate', 130)
                        engine.say(f'Введите {stim4}')
                        engine.startLoop()

                    except RuntimeError:
                        engine.endLoop()
                        engine = pyttsx3.init()
                        engine.setProperty('rate', 130)
                        engine.say(f'Введите {stim4}')
                        engine.runAndWait()

                    return render_template('exercise4.html', stim=stim4, message=message)

    # озвучка задания
    try:
        engine = pyttsx3.init()
        engine.setProperty('rate', 130)
        engine.say(f'Введите {stim4}')
        engine.startLoop()

    except RuntimeError:
        engine.endLoop()
        engine = pyttsx3.init()
        engine.setProperty('rate', 130)
        engine.say(f'Введите {stim4}')
        engine.runAndWait()

    return render_template('exercise4.html', stim=stim4, message=message)

###############################
#страница "случайно"
###############################
start = datetime.datetime.now()
previous_difference = []
previous_difference.append(timedelta(hours=0, minutes=0, seconds=0))
num_mists5 = 0
stim5 = random.choice(words5)

@app.route('/exercise5', methods=['POST', "GET"])
def exercise5():
    # задаем значения стимула и похвалу
    global good_words
    global num_mists5
    global stim5
    message = ''

    if request.method == 'POST':
        # получаем ответ
        ans5 = request.form.get('exercise')
        # находим время, за которе ввели ответ
        diff = datetime.datetime.now() - start
        time_diff = diff - previous_difference[-1]
        previous_difference.append(diff)
        ans5 = normalize_text(ans5)
        stim5 = normalize_text(stim5)

        # если ответ правильный
        if ans5.strip().lower() == stim5.strip().lower():
            num_mists5 = 0

            # выбираем похвалу, которая выведется на экран, и следующий стимул
            message = random.choice(good_words)

            # выбираем какую похвалу озвучиваем
            file_path = random.choice(
                ["static/audio/good_result1.wav", "static/audio/good_result2.wav", "static/audio/good_result3.wav"])
            data, samplerate = soundfile.read(file_path)
            soundfile.write(file_path, data, samplerate)

            # проигрываем похвалу
            wave_obj = sa.WaveObject.from_wave_file(file_path)
            play = wave_obj.play()
            play.wait_done()
            play.stop()

            #если пользователь не вошел в аккаунт, даем случайный следующий стимул
            if isinstance(current_user, AnonymousUserMixin):
                stim5 = random.choice(words5)
                # озвучка следующего задания
                try:
                    engine = pyttsx3.init()
                    engine.setProperty('rate', 130)
                    engine.say(f'Введите {stim5}')
                    engine.startLoop()

                except RuntimeError:
                    engine.endLoop()
                    engine = pyttsx3.init()
                    engine.setProperty('rate', 130)
                    engine.say(f'Введите {stim5}')
                    engine.runAndWait()
                return render_template('exercise5.html', stim=stim5, message=message)

            #если пользователь вошел в аккаунт
            else:
                #заносим информацию в базу данных
                answer = Answer(time=float(time_diff.total_seconds()),
                                type_of_exercise=ex_types[4],
                                exercise=stim5,
                                answer=ans5,
                                mistake=False,
                                user_id=current_user.id)
                db.session.add(answer)
                db.session.commit()

                stim5 = random.choice(words5)
                # озвучка следующего задания
                try:
                    engine = pyttsx3.init()
                    engine.setProperty('rate', 130)
                    engine.say(f'Введите {stim5}')
                    engine.startLoop()

                except RuntimeError:
                    engine.endLoop()
                    engine = pyttsx3.init()
                    engine.setProperty('rate', 130)
                    engine.say(f'Введите {stim5}')
                    engine.runAndWait()

                return render_template('exercise5.html', stim=stim5, message=message)

        # если ответ неправильный
        else:
            message = "К сожалению, неверно."

            # выбираем какую похвалу ощвучиваем
            file_path = random.choice(
                ["static/audio/bad_result1.wav", "static/audio/bad_result2.wav"])
            data, samplerate = soundfile.read(file_path)
            soundfile.write(file_path, data, samplerate)

            # проигрываем похвалу
            wave_obj = sa.WaveObject.from_wave_file(file_path)
            play = wave_obj.play()
            play.wait_done()
            play.stop()

            #если пользователь не зашел в аккаунт, выдаем следующий стимул случайно
            if isinstance(current_user, AnonymousUserMixin):
                stim5 = random.choice(words5)

                # озвучка следующего задания
                try:
                    engine = pyttsx3.init()
                    engine.setProperty('rate', 130)
                    engine.say(f'Введите {stim5}')
                    engine.startLoop()

                except RuntimeError:
                    engine.endLoop()
                    engine = pyttsx3.init()
                    engine.setProperty('rate', 130)
                    engine.say(f'Введите {stim5}')
                    engine.runAndWait()

                return render_template('exercise5.html', stim=stim5, message=message)

            #если пользователь зашел в аккаунт
            else:
                num_mists5 += 1
                #заносим информацию об ошибке в базу
                answer = Answer(time=float(time_diff.total_seconds()),
                                type_of_exercise=ex_types[4],
                                exercise=stim5,
                                answer=ans5,
                                mistake=True,
                                user_id=current_user.id)
                db.session.add(answer)
                db.session.commit()

                #если ошибок не много
                if num_mists5 <= 2:

                    # озвучка следующего задания
                    try:
                        engine = pyttsx3.init()
                        engine.setProperty('rate', 130)
                        engine.say(f'Введите {stim5}')
                        engine.startLoop()

                    except RuntimeError:
                        engine.endLoop()
                        engine = pyttsx3.init()
                        engine.setProperty('rate', 130)
                        engine.say(f'Введите {stim5}')
                        engine.runAndWait()

                    return render_template('exercise5.html', stim=stim5, message=message)

                #если ошибки уже три, то записываем текущий стимул в конец списка words_to_go
                else:
                    num_mists5 = 0

                    stim5 = random.choice(words5)

                    # озвучка следующего задания
                    try:
                        engine = pyttsx3.init()
                        engine.setProperty('rate', 130)
                        engine.say(f'Введите {stim5}')
                        engine.startLoop()

                    except RuntimeError:
                        engine.endLoop()
                        engine = pyttsx3.init()
                        engine.setProperty('rate', 130)
                        engine.say(f'Введите {stim5}')
                        engine.runAndWait()

                    return render_template('exercise5.html', stim=stim5, message=message)

    # озвучка следующего задания
    try:
        engine = pyttsx3.init()
        engine.setProperty('rate', 130)
        engine.say(f'Введите {stim5}')
        engine.startLoop()

    except RuntimeError:
        engine.endLoop()
        engine = pyttsx3.init()
        engine.setProperty('rate', 130)
        engine.say(f'Введите {stim5}')
        engine.runAndWait()
    return render_template('exercise5.html', stim=stim5, message=message)








#страница прогресса
@app.route('/progress')
def progress():
    #если пользователь не зашел в аккаунт, то показываем страницу no_progress.html
    if isinstance(current_user, AnonymousUserMixin):
        return render_template('no_progress.html')

    #считаем время для каждого типа заданий
    users_answers = Answer.query.filter_by(user_id = current_user.id).all()
    time_all = 0
    time1 = 0
    time2 = 0
    time3 = 0
    time4 = 0
    time5 = 0
    len5 = 1
    time5all = 0
    for answ in users_answers:
        time_all += float(answ.time)
        if answ.type_of_exercise == ex_types[0]:
            time1 += float(answ.time)
        elif answ.type_of_exercise == ex_types[1]:
            time2 += float(answ.time)
        elif answ.type_of_exercise == ex_types[2]:
            time3 += float(answ.time)
        elif answ.type_of_exercise == ex_types[3]:
            time4 += float(answ.time)
        elif answ.type_of_exercise == ex_types[4]:
            time5 = float(answ.time)
            len5 = len(str(answ.exercise))
            time5all += float(answ.time)


    if time5 > 0:
        speed = str(round(len5/time5, 3)) + "знаков в секунду"
    else:
        speed = "Вы пока не печатали случайные слова"


    return render_template('progress.html',
                           username=current_user.username,
                           id=current_user.id,
                           time_all=int(time_all/60),
                           time1=int(time1/60),
                           time2=int(time2/60),
                           time3=int(time3/60),
                           time4=int(time4/60),
                           time5=int(time5all/60),
                           speed=speed
                           )


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=15555, debug=True)