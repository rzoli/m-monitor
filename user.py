import sqlite3,unittest,hashlib,os,uuid,logging,time,data_storage



from flask.ext.login import UserMixin

class User(UserMixin,data_storage.DataStorage):
    '''
    User status, password etc can be checked in database
    '''
    def __init__(self, root_path, addtestuser=False):
        data_storage.DataStorage.__init__(self,root_path)
        if addtestuser:
            self.add_testuser
        
    def add(self,name, password, user_type='parent'):
        if self.user_exists(name):
            raise RuntimeError('{0} user already exists'.format(name))
        self.name=name
        self.cursor.execute("insert into users(name, password, type) values ('{0}','{1}','{2}')".format(self.name,self.hash_password(password),user_type))
        self.db.commit()
        logging.info('{0} user created'.format(self.name))
        
    def user_exists(self,username):
        self.cursor.execute("select name from users")
        for line in self.cursor.fetchall():
            if username in line:
                return True
        return False
        
    def hash_password(self, password):
        # uuid is used to generate a random number
        salt = uuid.uuid4().hex
        return hashlib.sha256(salt.encode() + password.encode()).hexdigest() + ':' + salt
    
    def check_password(self, name, password):
        self.cursor.execute("select password from users where name='{0}'".format(name))
        response=self.cursor.fetchall()
        if len(response)==1:
            hashed_password=str(response[0][0])
            password_hash, salt = hashed_password.split(':')
            return password_hash == hashlib.sha256(salt.encode() + password.encode()).hexdigest()
        else:
            return False
        
    def login(self,name, password, user_info=''):
        if self.check_password(name, password):
            self.cursor.execute("insert into sessions(name, info, login) values ('{0}','{1}','{2}')".format(name,user_info, int(time.time())))
            self.db.commit()
            return True
        else:
            return False
            
    def add_testuser(self):
        try:
            self.add('rz','1234')
        except:
            pass

        
class TestUser(unittest.TestCase):
    def test_01_new_database(self):
        u=User( '/tmp')
        u.add('rz','1234')
        u=User('/tmp')
        u.add('fk','12341')
        self.assertTrue(u.login('rz', '1234'))
        self.assertFalse(u.login('rz', '12345'))
        self.assertFalse(u.login('rz1', '12345'))
        os.remove(u.database_filename)
        
    
        
if __name__ == "__main__":
    unittest.main()
