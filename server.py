#TODO: plot tengelyekre felirat, gyors report:  homerseklet grafikonok napokra bontasa
#TODO: lassu az egesz, optimalizalas: ne olvassa be az egeszet, csak ha a megfelelo linkre klikkelunk, ami sokaig tart: osszes esemeny beolvasasa majd megjelenitese
ROOT='/home/rz/codes/m-monitor'
CATEGORIES=['Szoptatas', 'Kaka', 'Alvas', 'Alvashoz leteve', 'Alvas vege', 'Pisi', 'Kaka, pisi','Szoptatas vege','Ures pelenka', 'Testsuly', 'Homerseklet', 'Magassag', 'Kinga haskorfogat', 'Kinga testsuly', 'Magzat kora', 'Eves', 'Seta', 'Jatek', 'Pelenkazas']
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
    user=''
    n=-150
    if 'kilepes' in request.form:
        return redirect(url_for('logout'))
    if 'rogzit' in request.form:
        timestamp=time.mktime(datetime.datetime.strptime(request.form['datum']+' '+request.form['ido'], '%Y-%m-%d %H:%M').timetuple())
        d.add_event(timestamp, category=request.form['kategoria'], note=request.form['bejegyzes'],user=user)
    elif 'torol' in request.form:
        timestamp=time.mktime(datetime.datetime.strptime(request.form['sorszam'], '%Y-%m-%d %H:%M').timetuple())
        d.remove_event(timestamp)
    elif 'mutat' in request.form or 'plot_frissit' in request.form:
        return render_template('plot.html', name='Adel', age=d.calculate_timeleft(),#, weight='3000 g', height='15 cm', 
                            szopas_ota=d.szopasi_ido())
    elif 'vissza' in request.form:
        pass
    elif 'frissit' in request.form:
        pass
    elif 'szopi' in request.form:
        app.logger.info('sz')
        timestamp=time.mktime(datetime.datetime.strptime(request.form['datum']+' '+request.form['ido'], '%Y-%m-%d %H:%M').timetuple())
        d.add_event(timestamp, category='Szoptatas', note=request.form['bejegyzes'],user=user)
    elif 'kaki' in request.form:
        timestamp=time.mktime(datetime.datetime.strptime(request.form['datum']+' '+request.form['ido'], '%Y-%m-%d %H:%M').timetuple())
        d.add_event(timestamp, category='Kaki', note=request.form['bejegyzes'],user=user)
    elif 'alvashoz_le' in request.form:
        timestamp=time.mktime(datetime.datetime.strptime(request.form['datum']+' '+request.form['ido'], '%Y-%m-%d %H:%M').timetuple())
        d.add_event(timestamp, category='Alvashoz leteve', note=request.form['bejegyzes'],user=user)
    elif 'alvas' in request.form:
        timestamp=time.mktime(datetime.datetime.strptime(request.form['datum']+' '+request.form['ido'], '%Y-%m-%d %H:%M').timetuple())
        d.add_event(timestamp, category='Alvas', note=request.form['bejegyzes'],user=user)        
    elif 'vege' in request.form:
        timestamp=time.mktime(datetime.datetime.strptime(request.form['datum']+' '+request.form['ido'], '%Y-%m-%d %H:%M').timetuple())
        d.add_event(timestamp, category='Alvas vege', note=request.form['bejegyzes'],user=user)                
    elif 'osszes' in request.form:
        n=0
    #app.logger.info(1)
    events=d.read_events()[n:][::-1]
    #app.logger.info(2)
    now=time.time()
    return render_template('muci.html', name='Adel', age=d.calculate_timeleft(),#, weight='3000 g', height='15 cm', 
                            utolso24ora=d.utolso24ora(),
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
    
@app.route("/napirend.png")
def napirend():
    import datetime
    import StringIO,matplotlib

    from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
    from matplotlib.figure import Figure
    from matplotlib.dates import DateFormatter
    font = {'size'   : 6}

    matplotlib.rc('font', **font)
    nplots=8
    fig=Figure(dpi=120, figsize=(6,15))
    #fig.set_size_inches((20,5))
    d=data_storage.DataStorage(ROOT)
    
    ax=fig.add_subplot(nplots,1,1)
    tk,kaki,tsz,szopi=d.plot()
    tk=numpy.array([datetime.datetime.fromtimestamp(tki) for tki in tk])
    tsz=numpy.array([datetime.datetime.fromtimestamp(tszi) for tszi in tsz])
    ax.plot_date(tk,kaki,'o-')
    ax.plot_date(tsz,szopi, 'v-')
    ax.grid(True)
    ax.legend(['Kaki', 'Szopi'], loc='upper left', prop={'size':7})
    ax.xaxis.set_major_formatter(DateFormatter('%m.%d %Hh'))
    #fig.autofmt_xdate()
    
    ax=fig.add_subplot(nplots,1,2)
    sz,szi,k,ki=d.napirend()
    for i in range(len(sz)-1,0,-1):
        ss=numpy.array([datetime.datetime.fromtimestamp(s) for s in sz[i]])
        ax.plot_date(ss, szi[i],'o' if i == 0 else 'v-', ms=4)
    ax.legend( map(str,range(len(sz))), loc='upper left', prop={'size':7})
    ax.xaxis.set_major_formatter(DateFormatter('%H:00'))
    ax.grid(True)
    
    ax.set_title('Szopi idok',fontsize=12)
    ax=fig.add_subplot(nplots,1,3)
    ax.set_title('Kaki idok',fontsize=12)
    for i in range(len(k)-1,0,-1):
        ss=numpy.array([datetime.datetime.fromtimestamp(s) for s in k[i]])
        ax.plot_date(ss, ki[i],'o' if i == 0 else 'v-', ms=4)
    ax.legend(map(str,range(len(sz))), loc='upper left', prop={'size':7})
    ax.xaxis.set_major_formatter(DateFormatter('%H:00'))
    ax.grid(True)
    
    
    ax=fig.add_subplot(nplots,1,4)
    a=d.alvas()
    ax.set_title('Napi alvas idok',fontsize=12)
    for ai in a[::-1][:6]:
        ax.plot_date(map(datetime.datetime.fromtimestamp,ai[1][:,0]-3600), ai[1][:,1]/60., 'o-', ms=4)
        ax.grid(True)
    ax.xaxis.set_major_formatter(DateFormatter('%H:00'))
    ax=fig.add_subplot(nplots,1,5)
    ax.set_title('Napi alvas',fontsize=12)
    a=a[-62:]
    x=[i[0] for i in a]
    y=[i[2] for i in a]
    ax.plot_date(x, y, 'v-')
    ax.grid(True)
    ax.xaxis.set_major_formatter(DateFormatter('%m.%d'))
    ax=fig.add_subplot(nplots,1,6)
    ax.set_title('Testsuly',fontsize=12)
    t,s=d.testsuly()
    t=numpy.array([datetime.datetime.fromtimestamp(ti) for ti in t])
    ax.plot_date(t, s,'v-')
    ax.grid(True)
    ax.xaxis.set_major_formatter(DateFormatter('%m.%d.'))
    if 0:
        ax=fig.add_subplot(nplots,1,7)
        ax.set_title('Pelenka/nap',fontsize=12)
        t,s=d.pelenka()
        t=numpy.array([datetime.datetime.fromtimestamp(ti) for ti in t])
        ax.plot_date(t, s,'ro-')
        ax.grid(True)
        ax.xaxis.set_major_formatter(DateFormatter('%m.%d.'))
    
    ax=fig.add_subplot(nplots,1,7)
    ax.set_title('Szobahomerseklet',fontsize=12)
    
    t,temp=read_temp('/home/rz/codes/m-monitor/temp.txt')
    ax.plot_date(t,temp,'-')
    t,temp=read_temp('/home/rz/codes/m-monitor/temp_tisztaszoba.txt')
    ax.plot_date(t,temp,'-')
    ax.grid(True)
    ax.legend(['Haloszoba', 'Tisztaszoba'],loc='upper left',prop={'size':7})
    ax.xaxis.set_major_formatter(DateFormatter('%m.%d. %H:%M'))
    
    kaki,szopi=d.napi_kaki_szopi()
    ax=fig.add_subplot(nplots,1,8)
    ax.set_title('Kaki,szopi',fontsize=12)
    ax.xaxis.set_major_formatter(DateFormatter('%m.%d'))
    ax.plot_date(list(kaki[:,0]),list(kaki[:,1]),'o-')
    ax.plot_date(list(szopi[:,0]),list(szopi[:,1]),'o-')
    ax.grid(True)
    ax.legend(['Kaki','szopi'],loc='upper left',prop={'size':7})
    fig.tight_layout()
    canvas=FigureCanvas(fig)
    png_output = StringIO.StringIO()
    canvas.print_png(png_output)
    response=make_response(png_output.getvalue())
    response.headers['Content-Type'] = 'image/png'
    return response
    
def read_temp(fn):
    f=open(fn,'rt')
    txt=f.read()
    f.close()
    t0=time.time()-4*86400
    line_items=[line.split(' ') for line in txt.split('\n')[:-1]]
    temp_data=numpy.array([[float(l[0]),float(l[-1])] for l in line_items if float(l[0])>t0])    
    t=numpy.array([datetime.datetime.fromtimestamp(ti) for ti in temp_data[:,0]])
    return t,temp_data[:,1]


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
        app.run(host= '0.0.0.0', port=2016,threaded=True)

