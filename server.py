#TODO: 
#TODO: prio2 user session timeout, atnevez: csaladi egeszsegmonitor, szemely kivalaszthato legyen
ROOT='/tmp'
CATEGORIES=['Kinga haskorfogat', 'Kinga testsuly', 'Magzat kora', 'Testsuly', 'Magassag', 'Szoptatas', 'Eves', 'Seta', 'Jatek', 'Pelenkazas']
from visexpman.engine.generic import utils
import user,numpy,logging,data_storage,os,time,datetime,sys
from flask import Flask,request,render_template,Response,redirect,url_for,abort
from flask_login import LoginManager, UserMixin, login_required, login_user, logout_user
logging.basicConfig(filename=os.path.join(ROOT,'server.txt'),level=logging.DEBUG,format='%(asctime)s %(levelname)s\t%(message)s')
app = Flask(__name__)
app.config.update(
    DEBUG = True,
    SECRET_KEY = 'Hejdejo1'
)


login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

@login_manager.user_loader
def load_user(userid):
    u=user.User( ROOT)
    u.id=userid
    return u


@app.route('/',methods=["GET", "POST"])
@login_required
def index():
    app.logger.info(request.method)
    app.logger.info([[i, request.form[i]] for i in request.form])
    d=data_storage.DataStorage(ROOT)
    if 'kilepes' in request.form:
        return redirect(url_for('logout'))
    if 'rogzit' in request.form:
        timestamp=time.mktime(datetime.datetime.strptime(request.form['datum']+' '+request.form['ido'], '%Y-%m-%d %H:%M').timetuple())
        d.add_event(timestamp, category=request.form['kategoria'], note=request.form['bejegyzes'],user=request.form['elvegezte'])
    elif 'torol' in request.form:
        timestamp=time.mktime(datetime.datetime.strptime(request.form['sorszam'], '%Y-%m-%d %H:%M').timetuple())
        d.remove_event(timestamp)
    events=d.read_events()[::-1]
    now=time.time()
    return render_template('muci.html', name='Adel', age=d.calculate_timeleft(),#, weight='3000 g', height='15 cm', 
                           today=utils.timestamp2ymd(now), now=utils.timestamp2hm(now),
                           categories=CATEGORIES,
                           events=d.format_events(events), eventids=d.event_ids(events))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']        
        u=user.User( ROOT)
        if u.login(username,password):
            u.id=int(numpy.random.random()*1e6)
            login_user(u)
            return redirect(url_for('index'))
        else:
            return abort(401)
    else:
        return Response('''
        <title>Muci Monitor</title>
        <form action="" method="post">
            <p><input type=text name=username>
            <p><input type=password name=password>
            <p><input type=submit value=Login>
        </form>
        ''')

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

if __name__ == "__main__":
    if len(sys.argv)>1:
        if '--reset' in sys.argv:
            d=data_storage.DataStorage( ROOT)
            os.remove(d.database_filename)
            d=data_storage.DataStorage( ROOT)
        elif '--adduser' in sys.argv:
            u=user.User( ROOT)
            u.add(sys.argv[2],sys.argv[3])
    else:
        app.logger.info('Server started')
        app.run(host= '0.0.0.0',port=2016)

