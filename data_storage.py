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
        
    def add_event(self,timestamp, category='', note='',user='', child='Kismuci'):
        self.cursor.execute("insert into events(timestamp, category, note, user, child) values ('{0}','{1}','{2}','{3}','{4}')".format(int(timestamp), category, note, user, child))
        self.db.commit()
        logging.info('event added: {0}, {1}, {2}, {3}'.format(timestamp, category,note,user))
        
    def read_events(self):
        self.cursor.execute("select * from events")
        events=[]
        for line in self.cursor.fetchall():
            d,t=utils.timestamp2ymdhm(line[0]).split(' ')
            event=[d,t]
            event.extend(list(line[1:]))
            events.append(event)
        return events
        
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
