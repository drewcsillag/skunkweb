import unittest
from formlib import *

class IntegerFieldUnitTest(unittest.TestCase):
    def __init__(self, aStr):
        self.intField = IntegerField('intTest', 'int field for testing')
        unittest.TestCase.__init__(self, aStr)
        

    def testValidateSucceeds(self):
        # there should be no error messages for valid int field values
        self.intField.value='123'
        retVal = self.intField.validate()
        assert len(retVal) < 1

        self.intField.value='0'
        retVal = self.intField.validate()
        assert len(retVal) < 1

        self.intField.value='-392874937'
        retVal = self.intField.validate()
        assert len(retVal) < 1

        self.intField.value='+123456789'
        retVal = self.intField.validate()
        assert len(retVal) < 1
        

    def testValidateFails(self):
        # errors must be generated for invalid integer literals
        self.intField.value='lsjkfds'
        retVal = self.intField.validate()
        assert len(retVal) > 0

        self.intField.value="123kl"
        retVal = self.intField.validate()
        assert len(retVal) > 0

        self.intField.value='-JK45'
        retVal = self.intField.validate()
        assert len(retVal) > 0 
        

class DoubleFieldUnitTest(unittest.TestCase):
    def __init__(self, aStr):
        self.dblField = DoubleField('doubleTest', 'double field for testing')
        unittest.TestCase.__init__(self, aStr)

    def testValidateSucceeds(self):
        # there should be no error messages for valid dbl field values
        self.dblField.value='123.1'
        retVal = self.dblField.validate()
        assert len(retVal) < 1

        self.dblField.value='0.0'
        retVal = self.dblField.validate()
        assert len(retVal) < 1

        self.dblField.value='-392874937'
        retVal = self.dblField.validate()
        assert len(retVal) < 1

        self.dblField.value='+123456789.45'
        retVal = self.dblField.validate()
        assert len(retVal) < 1

        self.dblField.value='-123456789.45'
        retVal = self.dblField.validate()
        assert len(retVal) < 1
        

    def testValidateFails(self):
        # errors must be generated for invalid double literals
        self.dblField.value='lsjkfds'
        retVal = self.dblField.validate()
        assert len(retVal) > 0

        self.dblField.value="123kl.05"
        retVal = self.dblField.validate()
        assert len(retVal) > 0

        self.dblField.value='-JK45'
        retVal = self.dblField.validate()
        assert len(retVal) > 0

        self.dblField.value='0.as89'
        retVal = self.dblField.validate()
        assert len(retVal) > 0

        
class DateFieldUnitTest(unittest.TestCase):
    def __init__(self, aStr):
        self.dfltDtField = DateField('defaultDateTest', 'date field for testing using default date format')
        self.cstmDtField = DateField('customDateTest', 'date field for testing using custom date format', formatString='%Y%d%m' )
        # default field uses %m/%d/%Y format
        self.defaultTests = ['11/02/2002','01/01/1750','01/01/0001','12/30/2041','01/01/1970','02/02/1901','04/19/2011','06/09/1999']
        # custom field uses %Y%d%m format
        self.customTests = ['19993002','20011303','20000101','00010101','19700101','23003001','19000205','04951010','05270101','11272304']
        self.defaultFails = ['bogus', '19993002', '1900/01/01', '12ad/12/12', '0']
        self.customFails = ['bogus', '993002', '1900/01/01', '12/12/12', '0']
        unittest.TestCase.__init__(self, aStr)


    def testValidateSucceeds(self):
        for aTst in self.defaultTests:
            self.dfltDtField.value = aTst
            retVal = self.dfltDtField.validate()
            assert len(retVal) < 1

        for aTst in self.customTests:
            self.cstmDtField.value = aTst
            retVal = self.cstmDtField.validate()
            assert len(retVal) < 1
                

    def testValidateFails(self):
        for aTst in self.defaultFails:
            self.dfltDtField.value = aTst
            retVal = self.dfltDtField.validate()
            assert len(retVal) > 0

        for aTst in self.customFails:
            self.cstmDtField.value = aTst
            retVal = self.cstmDtField.validate()
            assert len(retVal) > 0

    

def suite():
    suite = unittest.TestSuite()
    suite.addTest(IntegerFieldUnitTest('testValidateSucceeds'))
    suite.addTest(IntegerFieldUnitTest('testValidateFails'))
    suite.addTest(DoubleFieldUnitTest('testValidateSucceeds'))
    suite.addTest(DoubleFieldUnitTest('testValidateFails'))    
    suite.addTest(DateFieldUnitTest('testValidateSucceeds'))
    suite.addTest(DateFieldUnitTest('testValidateFails'))    
    return suite

if __name__ == "__main__":
    unittest.main()
                  
