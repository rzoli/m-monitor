import sqlite3,unittest,os,logging,time
from visexpman.engine.generic import utils
import datetime,numpy

DBCONNECT_TIMEOUT=5
PLOT_NAPOK=62

class DataStorage(object):
    def __init__(self,root_path):
        self.root_path=root_path
        db_exists=os.path.exists(self.database_filename)
        self.connect()
        self.t0='201610301500'#2016 okt 30 3 ora
        if not db_exists:
            self.create_database()
        
    @property
    def database_filename(self):
        return os.path.join(self.root_path, 'mmu.db')#muci monitor users
        
    def connect(self):
        self.db=sqlite3.connect(self.database_filename,timeout=DBCONNECT_TIMEOUT)
        self.cursor=self.db.cursor()
        
    def create_database(self):
        '''
        Database name: user
        name (varchar), password (varchar), type (varchar)
        
        Database name: sessions
        user (varchar), login time (timestamp), logout time (timestamp)
        '''
        self.cursor.execute("create table users(name varchar(20), password varhar(100), type varchar(20))")
        self.cursor.execute("create table sessions(name varchar(20), login int, info varchar(100))")
        self.cursor.execute("create table events(timestamp int, category varchar(30), note varhar(200), user varchar(20), child varhcar(20))")
        self.db.commit()
        logging.info('database created')
        
    def add_event(self,timestamp, category='', note='',user='', child='Adel'):
        self.cursor.execute("insert into events(timestamp, category, note, user, child) values ('{0}','{1}','{2}','{3}','{4}')".format(int(timestamp), category, note, user, child))
        self.db.commit()
        logging.info('event added: {0}, {1}, {2}, {3}'.format(timestamp, category,note,user))
        
    def read_events(self, timespan=None):
        rawevents= self.read_raw_events()
        if timespan !=None:
            t0=time.time()-timespan
            rawevents=[re for re in rawevents if re[0]>t0]
        #Sort raw events first
        t=[re[0] for re in rawevents]
        t.sort()
        events_sorted=[]
        for ti in t:
            events_sorted.append([re for re in rawevents if re[0]==ti][0])
        events=[]
        for line in events_sorted:
            d,t=utils.timestamp2ymdhm(line[0]).split(' ')
            event=[d,t]
            event.extend(list(line[1:]))
            events.append(event)
        return events
        
    def read_raw_events(self):
        if not hasattr(self,'re'):
            self.cursor.execute("select * from events")
            rawevents= [line for line in self.cursor.fetchall()]
            self.re=rawevents
        else:
            rawevents=self.re
        return rawevents
        
    def calculate_timeleft(self):
        rawevents= self.read_raw_events()
        magzatkora_events=[re for re in rawevents if 'Magzat kora' in re[1]]
        if len(magzatkora_events)==0:
            return ''
        latest=max([me[0] for me in magzatkora_events])
        dt=int(time.time()-latest)/(7*86400)
        kor=[me[2] for me in magzatkora_events if me[0]==latest][0]
        kor=int(''.join([c for c in kor if c.isdigit()]))
        szuletesi_datum=[re for re in rawevents if 'megszuletett' in re[2].lower()]
        if len(szuletesi_datum)==0:
            return '{0} hetes, {1} het van hatra' .format(kor+dt,40-(kor+dt))
        else:
            return '{0} hetes'.format(int((time.time()-szuletesi_datum[0][0])/(7*86400)))

    def szopasi_ido(self):
        rawevents= self.read_raw_events()
        szopi=[re for re in rawevents if 'Szoptatas' in re[1] and 'vege' not in re[1]]
        latest=max([me[0] for me in szopi])
        dt=round((time.time()-latest)/60/60.,1)
        return 'Szoptatas ota {0} ora telt el'.format(dt)

    def utolso24ora(self):
        rawevents= self.read_raw_events()
        now=time.time()
        szopi=len([re for re in rawevents if 'Szoptatas' in re[1] and 'vege' not in re[1] and re[0]>now-86400])
        kaki=len([re for re in rawevents if 'kak' in re[1].lower() and re[0]>now-86400])
        ma=datetime.datetime.fromtimestamp(now)
        ma=time.mktime(datetime.datetime(ma.year,ma.month,ma.day,0,0,0).timetuple())
        tegnap=ma-86400
        alvas=0
        tegnapiesemenyek=[re for re in rawevents if re[0]>tegnap and re[0]<ma]
        tegnapiesemenyek.sort()
        maiesemenyek=[re for re in rawevents if re[0]>ma]
        maiesemenyek.sort()
        if tegnapiesemenyek[-1][1]=='Alvas':
            if len(maiesemenyek)>0:
                alvas+=self.timestamp2daytime(maiesemenyek[0][0])
            else:
                alvas+=self.timestamp2daytime(now)
        alvas_indexek=[i for i in range(len(maiesemenyek)) if maiesemenyek[i][1]=='Alvas']
        for i in alvas_indexek:
            if i==len(maiesemenyek)-1:
                alvas+=now-maiesemenyek[i][0]
            else:
                alvas+=maiesemenyek[i+1][0]-maiesemenyek[i][0]
        return 'Utobbi 24 oraban: {0} szoptatas | {1} kaki | Alvas mai nap {2:0.1f} ora | {3}'.format(szopi,kaki, alvas/3600.,self.szopasi_ido())
        
    def _utolso_het_szopi_kaki(self,t0):
        rawevents= self.read_raw_events()
        #Szoptatas, kaki over time
        szopi=[re[0] for re in rawevents if 'Szoptatas' in re[1] and 'vege' not in re[1] and re[0]>t0]
        szopi.sort()
        kaki=[re[0] for re in rawevents if 'kak' in re[1].lower() and re[0]>t0]
        kaki.sort()
        return szopi,kaki,rawevents,t0

    def plot(self):
        t0=time.time()-7*86400#Utolso 7 nap
        szopi,kaki,rawevents,t0=self._utolso_het_szopi_kaki(t0)
        #testsuly=numpy.array([[re[0], float(re[2].split(' ')[0])/1e3] for re in rawevents if 'testsuly' in re[1].lower() and re[0]>t0])
        szopi=(numpy.array(szopi))
        kaki=(numpy.array(kaki))
        m=max(kaki.max(),szopi.max())
        #kaki-=m
        #szopi-=m
        return kaki[1:],numpy.diff(kaki)/3600.,szopi[1:],numpy.diff(szopi)/3600.
        
    def napirend(self):
        now=time.time()
        t0=now-(int(now)%86400+3600)-6*86400
        szopi,kaki,rawevents,t0=self._utolso_het_szopi_kaki(t0)
        sz=numpy.array([t%86400+0*3600 for t in szopi])
        k=numpy.array([t%86400+0*3600 for t in kaki])
        sz=numpy.split(sz,numpy.where(numpy.diff(sz)<0)[0]+1)
        k=numpy.split(k,numpy.where(numpy.diff(k)<0)[0]+1)        
        szi=[numpy.arange(szii.shape[0]) for szii in sz]
        ki=[numpy.arange(kii.shape[0]) for kii in k]
        return sz, szi,k,ki
        
    def testsuly(self):
        rawevents= self.read_raw_events()
        t0=[re[0] for re in rawevents if re[2]=='megszuletett'][0]
        testsuly=numpy.array([[re[0], float(re[2].split(' ')[0])] for re in rawevents if 'testsuly' in re[1].lower() and 'Kinga' not in re[1] and re[0]>t0])
        return testsuly[:,0],testsuly[:,1]
        
    def pelenka(self):
        rawevents= self.read_raw_events()
        pelenkazas=numpy.array([re[0] for re in rawevents if 'pisi' in re[1].lower() or 'kaki' in re[1].lower() or 'kaka' in re[1].lower()])
        d0=pelenkazas.min()-pelenkazas.min()%86400
        now=time.time()
        now=now-now%86400
        t=numpy.arange((now-d0)/86400+2)*86400+d0
        pelenkazas_per_nap=[]
        for i in range(t.shape[0]-1):
            n=len([p for p in pelenkazas if p>t[i] and p< t[i+1]])
            pelenkazas_per_nap.append(n)
        return t[:-1], numpy.array(pelenkazas_per_nap)
        
    def alvas(self):
        rawevents= self.read_raw_events()
        event_ts= [re[0] for re in rawevents]
        event_ts.sort()
        alvasok=[]
        for i in range(len(rawevents)):
            re=rawevents[i]
            if 'alvas' in re[1].lower() and 'vege' not in re[1].lower() and 'leteve' not in re[1].lower():
                t=re[0]
                try:
                    next=event_ts[event_ts.index(t)+1]
                except IndexError:
                    continue
                idotartam=int((next-t)/60.)
                if self.timestamp2daytime(t)+idotartam*60>86400:
                    t1=t
                    idotartam1=(86400-self.timestamp2daytime(t))/60.
                    t2=t+86401-self.timestamp2daytime(t)
                    idotartam2=idotartam-idotartam1
                    alvasok.append([t1,idotartam1])
                    alvasok.append([t2,idotartam2])
                else:
                    alvasok.append([t,idotartam])
        alvasok.sort()
        alvasok=numpy.array(alvasok)
        #napokra bontas
        d0=alvasok[:,0].min()
        d0=d0-d0%86400-3600
        d1=alvasok[:,0].max()
        d1=d1-d1%86400+86400
        dd=(d1-d0)/86400.
        napok=numpy.arange(dd+1)*86400+d0
        alvasok_per_nap=[]
        for i in range(napok.shape[0]-1):
            v=[datetime.datetime.fromtimestamp(napok[i]), numpy.array([item-numpy.array([int(napok[i]),0]) for item in alvasok if item[0]>napok[i] and item[0]<napok[i+1]])]
            if v[1].shape[0]>0:
                v.append(round(v[1][:,1].sum()/60.,1))
                v[1][:,1]=v[1][:,1].cumsum()
                #y=numpy.insert(v[1][:,1],0,0)
                y=v[1][:,1]
                x=v[1][:,0]
#                x=numpy.insert(v[1][:,0],v[1][:,0].shape[0],86399)
                v[1]=numpy.array([x,y]).T
                alvasok_per_nap.append(v)
        return alvasok_per_nap
        
    def timestamp2daytime(self,ts):
        d=datetime.datetime.fromtimestamp(ts)
        return int(d.minute*60+d.hour*3600)
        
        
    def idoeloszlas(self):
        rawevents= self.read_raw_events()
        t0=time.time()-168*3600
        kaki=numpy.array([datetime.datetime.fromtimestamp(self.timestamp2daytime(re[0])) for re in rawevents if 'kaka' in re[1].lower() or 'kaki' in re[1].lower()])
        szopi=numpy.array([datetime.datetime.fromtimestamp(self.timestamp2daytime(re[0])) for re in rawevents if 'szoptatas' in re[1].lower()])
        alvas=numpy.array([datetime.datetime.fromtimestamp(self.timestamp2daytime(re[0])) for re in rawevents if 'alvas' in re[1].lower() and 'vege' not in re[1].lower()])
        return kaki,szopi,alvas
        
    def napi_kaki_szopi(self):
        rawevents= self.read_raw_events()
        t0=time.time()-PLOT_NAPOK*86400
        kaki=numpy.array([re[0] for re in rawevents if ('kaka' in re[1].lower() or 'kaki' in re[1].lower()) and re[0]>t0])
        szopi=numpy.array([re[0] for re in rawevents if 'szoptatas' in re[1].lower() and re[0]>t0])
        kaki=self.timestamp2daystat(kaki)
        szopi=self.timestamp2daystat(szopi)
        return kaki,szopi
        
    def timestamp2daystat(self,ts):
        napits=(ts/86400)*86400
        napok=list(set(napits))
        napok.sort()
        napok_count=[]
        for n in napok:
            napok_count.append([datetime.datetime.fromtimestamp(n),len([1 for nts in napits if nts == n])])
        return numpy.array(napok_count)
            

    def format_events(self,events):
        return [{'date': e[0], 'time': e[1], 'category': e[2], 'note': ' '.join(e[3:-1])} for e in events]
        
    def event_ids(self,events):
        return [e[0]+' '+e[1] for e in events]
        
    def remove_event(self,timestamp):
        self.cursor.execute('delete from events where timestamp={0}'.format(int(timestamp)))
        self.db.commit()
        logging.info('{0} event removed'.format(timestamp))
        
    def __del__(self):
        self.db.close()


class TestUser(unittest.TestCase):
    @unittest.skip('')
    def test_01_database(self):
        d=DataStorage('/tmp/1')
        t0=time.time()
        d.add_event(t0, note='proba')
        time.sleep(1)
        d.add_event(time.time(), note='proba2')
        len1=len(d.read_events())
        d.remove_event(t0)
        len2=len(d.read_events())
        self.assertEqual(len1-1,len2)
        d.format_events(d.read_events())
    
    def test_02_plot(self):
        d=DataStorage('')
        d.plot()
        d.utolso24ora()
        d.napirend()
        d.testsuly()
        d.pelenka()
        d.alvas()
        d.napi_kaki_szopi()
        pass
        
        
if __name__ == "__main__":
    unittest.main()
