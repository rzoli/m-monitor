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
    def test_01_database(self):
        d=DataStorage( '/tmp/1')
        t0=time.time()
        d.add_event(t0, note='proba')
        time.sleep(1)
        d.add_event(time.time(), note='proba2')
        len1=len(d.read_events())
        d.remove_event(t0)
        len2=len(d.read_events())
        self.assertEqual(len1-1,len2)
        d.format_events(d.read_events())
        
if __name__ == "__main__":
    unittest.main()
