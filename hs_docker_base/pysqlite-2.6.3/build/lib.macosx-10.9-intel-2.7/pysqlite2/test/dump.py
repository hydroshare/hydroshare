# Author: Paul Kippes <kippesp@gmail.com>

import unittest
from pysqlite2 import dbapi2 as sqlite

class DumpTests(unittest.TestCase):
    def setUp(self):
        self.cx = sqlite.connect(":memory:")
        self.cu = self.cx.cursor()

    def tearDown(self):
        self.cx.close()

    def CheckTableDump(self):
        expected_sqls = [
                "CREATE TABLE t1(id integer primary key, s1 text, " \
                "t1_i1 integer not null, i2 integer, unique (s1), " \
                "constraint t1_idx1 unique (i2));"
                ,
                "INSERT INTO \"t1\" VALUES(1,'foo',10,20);"
                ,
                "INSERT INTO \"t1\" VALUES(2,'foo2',30,30);"
                ,
                "CREATE TABLE t2(id integer, t2_i1 integer, " \
                "t2_i2 integer, primary key (id)," \
                "foreign key(t2_i1) references t1(t1_i1));"
                ,
                "CREATE TRIGGER trigger_1 update of t1_i1 on t1 " \
                "begin " \
                "update t2 set t2_i1 = new.t1_i1 where t2_i1 = old.t1_i1; " \
                "end;"
                ,
                "CREATE VIEW v1 as select * from t1 left join t2 " \
                "using (id);"
                ]
        [self.cu.execute(s) for s in expected_sqls]
        i = self.cx.iterdump()
        actual_sqls = [s for s in i]
        expected_sqls = ['BEGIN TRANSACTION;'] + expected_sqls + \
            ['COMMIT;']
        [self.assertEqual(expected_sqls[i], actual_sqls[i])
            for i in xrange(len(expected_sqls))]

def suite():
    return unittest.TestSuite(unittest.makeSuite(DumpTests, "Check"))

def test():
    runner = unittest.TextTestRunner()
    runner.run(suite())

if __name__ == "__main__":
    test()
