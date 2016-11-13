#TODO: szoptatas idokozok vs datum, szoptatas/nap, szoptatasi osszido/nap,szeklet/vizelet kozotti idopont vs datum, pisi/kaka idokoz vs datum
ROOT='/home/rz/codes/m-monitor'
CATEGORIES=['Szoptatas / Stillen', 'Kaka, pisi / Stuhl und Urin','Szoptatas vege / Ende des Stillens', 'Kaka / Stuhl', 'Pisi / Urin', 'Alvas / Schlaf', 'Alvas vege / Ende des Schlafes', 'Ures pelenka', 'Testsuly / Korpergewicht', 'Homerseklet', 'Magassag', 'Kinga haskorfogat', 'Kinga testsuly', 'Magzat kora', 'Eves', 'Seta', 'Jatek', 'Pelenkazas']
from visexpman.engine.generic import utils
import user,numpy,logging,data_storage,os,time,datetime,sys
from flask import Flask,request,render_template,Response,redirect,url_for,abort,make_response
from flask_login import LoginManager, UserMixin, login_required, login_user, logout_user
logging.basicConfig(filename=os.path.join(ROOT,'server.txt'),level=logging.DEBUG,format='%(asctime)s %(levelname)s\t%(message)s')
app = Flask(__name__)
app.config.update(
    DEBUG = False,
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
                            szopas_ota=d.szopasi_ido(),utolso24ora=d.utolso24ora(),
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
        <title>Adel Monitor</title>
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

@app.route("/plot.png")
def plot():
    import datetime
    import StringIO
    import random

    from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
    from matplotlib.figure import Figure
    from matplotlib.dates import DateFormatter

    fig=Figure()
    ax=fig.add_subplot(1,1,1)
    x=[]
    y=[]
    now=datetime.datetime.now()
    delta=datetime.timedelta(days=1)
    d=data_storage.DataStorage(ROOT)
    tk,kaki,tsz,szopi,st,s=d.plot()
    tk=numpy.array([datetime.datetime.fromtimestamp(tki) for tki in tk])
    tsz=numpy.array([datetime.datetime.fromtimestamp(tszi) for tszi in tsz])
    st=numpy.array([datetime.datetime.fromtimestamp(tszi) for tszi in st])
    ax.plot_date(tk,kaki,'o-')
    ax.plot_date(tsz,szopi, 'v-')
    ax.plot_date(st,s, 'ro-')
    ax.legend(['Kaki', 'Szopi', 'Suly'])
#    ax.plot_date(x, y, '-')
    ax.xaxis.set_major_formatter(DateFormatter('%m.%d %Hh'))
    fig.autofmt_xdate()
    #ax=fig.add_subplot(2,1,2)
    #ax.ylabel('g')
    
    #ax.xaxis.set_major_formatter(DateFormatter('%m.%d %H:00'))
    
    canvas=FigureCanvas(fig)
    png_output = StringIO.StringIO()
    canvas.print_png(png_output)
    response=make_response(png_output.getvalue())
    response.headers['Content-Type'] = 'image/png'
    return response

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
        app.run(host= '0.0.0.0', port=2016)

