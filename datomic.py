# -*- coding: utf-8 -*-
import httplib
import urllib
from urlparse import urljoin
from edn import loads
import requests

def get_line_iterator(line_iterator):
    lines = []
    last_line_name = None
    for line in line_iterator:
        line = line.strip("\n")
        if line == "":
            if lines:
                yield lines
            lines = []
            last_line_name = None
            continue
        line_name,line_data = line.split(":",1)
        line_data = line_data[1:]
        line_name = line_name.strip()
        if line_name == "":
            pass
        elif line_name == last_line_name:
            lines[-1][1] = lines[-1][1] + line_data
        else:
            last_line_name = line_name
            lines.append((line_name, line_data))

def get_db_event_iterator(line_iterator):
    for line in get_line_iterator(line_iterator):
        assert len(line) == 1
        yield loads(line[0][1])

class Database(object):
    def __init__(self, name, conn):
        self.name = name
        self.conn = conn

    def __getattr__(self, name):
        def f(*args, **kwargs):
            return getattr(self.conn, name)(self.name, *args, **kwargs)
        return f

class Datomic(object):
    def __init__(self, location, storage):
        self.location = location
        self.storage = storage

    def db_url(self, dbname, path = 'data'):
        return urljoin(self.location, path + '/') + self.storage + '/' + dbname

    def create_database(self, dbname):
        r = requests.post(self.db_url(''), data={'db-name':dbname})
        assert r.status_code in (200, 201), r.text
        return Database(dbname, self)

    def transact(self, dbname, data):
        if type(data) == list:
            data = '[%s\n]' % '\n'.join(data)
        r = requests.post(self.db_url(dbname)+'/', data={'tx-data':data},
                          headers={'Accept':'application/edn'})
        assert r.status_code in (200, 201), (r.status_code, r.text)
        return loads(r.content)

    def query(self, dbname, query, extra_args=[], history=False, offset = None, limit = None):
        args = '[{:db/alias ' + self.storage + '/' + dbname
        if history:
            args += ' :history true'
        args += '} ' + ' '.join(str(a) for a in extra_args) + ']'
        params={'args' : args, 'q':query}
        if not offset == None:
            params['offset'] = offset
        if not limit == None:
            params['limit'] = limit
        r = requests.get(urljoin(self.location, 'api/query'),
                         params = params,
                         headers={'Accept':'application/edn'})
        assert r.status_code == 200, r.text
        return loads(r.content)

    def entity(self, dbname, eid):
        r = requests.get(self.db_url(dbname) + '/-/entity', params={'e':eid},
                         headers={'Accept':'application/edn'})
        assert r.status_code == 200
        return loads(r.content)

    def events(self, dbname):
        r = requests.get(self.db_url(dbname, path = "events"),
        headers = {'Accept':"text/event-stream"},
        stream = True)
        assert r.status_code == 200
        lines_iter = get_db_event_iterator(r.iter_lines(chunk_size = 1))
        return lines_iter

if __name__ == '__main__':
    q = """[{
  :db/id #db/id[:db.part/db]
  :db/ident :person/name
  :db/valueType :db.type/string
  :db/cardinality :db.cardinality/one
  :db/doc "A person's name"
  :db.install/_attribute :db.part/db}]"""

    conn = Datomic('http://localhost:3000/', 'tdb')
    db = conn.create_database('cms')
    db.transact(q)
    db.transact('[{:db/id #db/id[:db.part/user] :person/name "Peter"}]')
    r = db.query('[:find ?e ?n :where [?e :person/name ?n]]')
    print r
    eid = r[0][0]
    print db.query('[:find ?n :in $ ?e :where [?e :person/name ?n]]', [eid], history=True)
    print db.entity(eid)
