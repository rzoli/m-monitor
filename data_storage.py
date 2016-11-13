import sqlite3,unittest,os,logging,time
from visexpman.engine.generic import utils

DBCONNECT_TIMEOUT=5

class DataStorage(object):
    def __init__(self,root_path):
        self.root_path=root_path
        db_exists=os.path.exists(self.database_filename)
        self.connect()
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
        
    def read_events(self):
        rawevents= self.read_raw_events()
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
        self.cursor.execute("select * from events")
        rawevents= [line for line in self.cursor.fetchall()]
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
        pisi=len([re for re in rawevents if 'pisi' in re[1].lower() and re[0]>now-86400])
        kaki=len([re for re in rawevents if 'kaka' in re[1].lower() and re[0]>now-86400])
        return 'Utobbi 24 oraban/Im Letzten 24 Stunden: {0} szoptatas/Stillen, {1} kaki/Stuhl, {2} pisi/Urin'.format(szopi,kaki,pisi)

    def plot(self):
        rawevents= self.read_raw_events()
        #Szoptatas, kaki over time
        t0='201610301500'#2016 okt 30 3 ora
        import time,datetime,numpy
        t0=time.mktime(datetime.datetime.strptime(t0, '%Y%m%d%H%M%S').timetuple())
        t0=time.time()-7*86400#Utolso 3 nap
        szopi=[re[0] for re in rawevents if 'Szoptatas' in re[1] and 'vege' not in re[1] and re[0]>t0]
        szopi.sort()
        kaki=[re[0] for re in rawevents if 'kaka' in re[1].lower() and re[0]>t0]
        kaki.sort()        
        testsuly=numpy.array([[re[0], float(re[2].split(' ')[0])/1e3] for re in rawevents if 'testsuly' in re[1].lower() and re[0]>t0])
        szopi=(numpy.array(szopi))
        kaki=(numpy.array(kaki))
        m=max(kaki.max(),szopi.max())
        #kaki-=m
        #szopi-=m
        return kaki[1:],numpy.diff(kaki)/3600.,szopi[1:],numpy.diff(szopi)/3600.,testsuly[:,0],testsuly[:,1]

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
        pass
        
        
if __name__ == "__main__":
    unittest.main()
