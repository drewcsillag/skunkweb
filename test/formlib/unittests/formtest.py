import unittest
from formlib import *
from formlib.form import FieldProxy, CompositeField

class FieldUnitTest(unittest.TestCase):
    def __init__(self, aStr):
        self.noDefault = Field('nodefault', 'Field lacking a default value')
        self.hasDefault = Field('hasdefault', 'Field with a default value of "quilt"', default="quilt")
        self.notMultiple = Field('notmultiple', 'Field which does not accept lists of values', multiple=0)
        self.isMultiple = Field('ismultiple', 'Field accepting multiple values', multiple=1)
        unittest.TestCase.__init__(self, aStr)
        
    """\
    Test basic characteristics of form.Field: get/set/clear value, default value, checking value
    """
    def setup(self):
        pass

    def tearDown(self):
        pass

    def testDefault(self):
        #assert self.noDefault.default is None, 'No default field  had a default value!'
        assert self.hasDefault.default is not None, 'Default field had no default value!'

        #now test clearing of default
        self.hasDefault.clearDefault()
        assert self.hasDefault.default is None, 'Clearing default failed'

    def testMultiple(self):
        try:
            self.assertRaises(ValueError, self.notMultiple.checkValue(['1','2']))
        except ValueError:
            pass #expected
        assert isinstance(self.isMultiple.checkValue('1'), list), "multiple checkValue failed to convert '1' to list"

        
class FieldProxyUnitTest(unittest.TestCase):
    def __init__(self, aStr):
        unittest.TestCase.__init__(self, aStr)
        self.proxyName = 'proxyjoe'
        self.fieldName = 'joe'
        self.tstField = Field(self.fieldName, 'joe field', default='1')
        self.tstProxy = FieldProxy(self.proxyName, self.tstField)

    def testName(self):
        """\
        Ensures that the name of a field proxy is distinct from the proxied field's name\
        """
        assert self.tstProxy.name == self.proxyName
        # check to make sure proxy name hasn't magically overridden field name 
        assert self.tstField.name == self.fieldName 

    def testFieldProxying(self):
        """\
        Ensures that all field attributes outside of the field name are accessible via the proxy\
        """
        assert self.tstProxy.description == self.tstField.description
        assert self.tstProxy.default == self.tstField.default

        
class DomainFieldUnitTest(unittest.TestCase):
    """Test the notion of domain values within a form.DomainField"""
    def setUp(self):
        self.defaultDomain = DomainField('defaultdomain', ['apple', 'orange', 'peach'],
                                         'Domain based field defaulting to "peach"', default="peach")

    def tearDown(self):
        pass
    
    def testDomain(self):
        bogusVl = '@mxyzptlk!' # value  not likely to be in any domain\
        try:
            self.assertRaises(ValueError, self.defaultDomain.checkValue(bogusVl))
        except ValueError:
            pass # expected
        #ensure that the default is in the domain
        defVal = self.defaultDomain.default
        assert self.defaultDomain.checkValue(defVal) == defVal, "Default domain value not in domain!: %s" % (defaultDomain.default)

            
class CompositeFieldUnitTest(unittest.TestCase):
    """\
    Tests the characteristics of a form.CompositeField: proxied component fields, default composite value, ability to
    assign an arbitrary value composer, read only nature of composite value
    """
    def myValueComposer(self, fldList):
        retInt = 0
        for fld in fldList:
            try:
                retInt = retInt + int(fld.value)
            except:
                continue
        return retInt


    def __init__(self, aStr):
        self.tstFields = [
            Field('1', 'The first component', default='1'),
            Field('2', 'The second component', default='2'),
            Field('3', 'The third component', default='3')
            ]
        # uses the default value composer
        self.dfltCmpFld = CompositeField('composite', 'I am a composite of many fields', componentFields=self.tstFields)
        self.intCmpFld = CompositeField('composite', 'I am a composite of many fields which compose to an int value', componentFields=self.tstFields, valueComposer=self.myValueComposer)
        unittest.TestCase.__init__(self, aStr)


    def testComponentNames(self):
        for fld in self.dfltCmpFld.components:
            assert fld.name in ['composite_1', 'composite_2', 'composite_3']

        for fld in self.intCmpFld.components:
            assert fld.name in ['composite_1', 'composite_2', 'composite_3']

    def testImmutableValue(self):
        try:
            self.dfltCmpFld.value='bogus'
        except AttributeError:
            return

        raise "CompositeField had assignable value"
        

    def testValueComposer(self):
        print self.dfltCmpFld.value, self.intCmpFld.value
        assert self.dfltCmpFld.value == "1" + '\n' + "2" + '\n' + "3" + '\n'
        assert self.intCmpFld.value == 6
        

class FormUnitTest(unittest.TestCase):
    """\
    Tests the basic characteristics of a form.Form: submission, resetting, get/set data, and validation.
    This form will pass validation. 
    """
    
    def setUp(self):
        #fields contained within the form
        self.tstFlds = [
            Field('nodefault', 'Field lacking a default value'),
            Field('hasdefault', 'Field with a default value of "quilt"', default="quilt"),
            Field('notmultiple', 'Field which does not accept lists of values', multiple=0),
            Field('ismultiple', 'Field accepting multiple values', multiple=1),
            DomainField('defaultdomain', ['apple', 'orange', 'peach'], 'Domain based field defaulting to "peach"', default="peach")
            ]
        # set of test values for form updates
        self.valMp = {'nodefault':'val1', 'hasdefault':'val2', 'notmultiple':'val3', 'ismultiple':'val4', 'defaultdomain':'apple' }
        self.form = Form('formunittest', 'POST', '', '', fields=self.tstFlds)

    def tearDown(self):
        pass

    def testSubmit(self):
        self.form.submit(self.valMp)
        assert self.form.submitted, 'Form.submitted not true after submission'
        updMp = self.form.getData()
        for ky in self.valMp.keys():
            if not self.form.fields[ky].multiple:
                assert updMp[ky] == self.valMp[ky], "Update of value failed for submitted field: %s" % (ky)
            else:
                assert updMp[ky] == [self.valMp[ky]], "Update of value failed for submitted multiple field: %s" % (ky)

    def testReset(self):
        self.form.reset()
        assert not self.form.submitted, 'Form.submitted still true after reset'
        for fld in self.form.fields:
            if fld.value == fld.default:
                continue # this is a special case
            assert not fld.value, "Field %s still has value %s after form.reset()" % (fld.name, fld.value)

    def testGetData(self):
        """Ensures that the return of form.getData() is a mapping from all field names to their values"""
        dt = self.form.getData()
        assert isinstance(dt, dict), 'form.getData() returned non-mapping!'
        for fld in self.tstFlds:
            fldnm = fld.name
            fldval = fld.value
            assert dt.has_key(fldnm), "form.getData() mapping missing field name:%s" % (fldnm)
            assert dt[fldnm] ==  fldval, "form.getData() had incorrect field value for field name: %s" % (fldnm)
           
        
    def testSetData(self):
        """Ensures that updating the data map for a form results in the new mapping being available from getData()"""
        self.form.setData(self.valMp)
        updMp = self.form.getData()
        for ky in self.valMp.keys():
            if not self.form.fields[ky].multiple:
                assert updMp[ky] == self.valMp[ky]
            else:
                # multple field values are wrapped in lists
                tstVal = self.valMp[ky]
                if not isinstance(tstVal, list):
                    tstVal = [tstVal]
                assert tstVal == [self.valMp[ky]]
        

    def testValidate(self):
        """\
        Verifies that invalid domain values cannot be submitted as part of a form
        NOTE: should  add a more detailed validation test when validate components [such as IntField] are added
        """
        bogusValMp = {'defaultdomain':'gingersnap'}
        try:
            self.assertRaises(ValueError, self.form.submit(bogusValMp))
        except ValueError:
            pass #expected


def suite():
    """\
    The standard set of form tests to execute to validate form behavior
    """
    suite = unittest.TestSuite()
    suite.addTest(FieldUnitTest('testDefault'))
    suite.addTest(FieldUnitTest('testMultiple'))
    suite.addTest(DomainUnitTest('testDomain'))
    suite.addTest(FormUnitTest('testSubmit'))
    suite.addTest(FormUnitTest('testReset'))
    suite.addTest(FormUnitTest('testGetData'))
    suite.addTest(FormUnitTest('testSetData'))
    suite.addTest(FormUnitTest('testValidate'))
    suite.addTest(FieldProxyUnitTest('testName'))
    suite.addTest(FieldProxyUnitTest('testFieldProxying'))
    suite.addTest(CompositeFieldUnitTest('testComponentNames'))
    suite.addTest(CompositeFieldUnitTest('testImmutableValue'))    
    suite.addTest(CompositeFieldUnitTest('testValueComposer'))
    return suite
    
if __name__ == "__main__":
    unittest.main()   
