######################################################################## 
#  Copyright (C) 2002 Jacob Smullyan <smulloni@smullyan.org>
#                     Drew Csillag <drew_csillag@yahoo.com>
#  
#      You may distribute under the terms of either the GNU General
#      Public License or the SkunkWeb License, as specified in the
#      README file.
########################################################################

########################################################################
# This module kindly contributed by James Richards.
########################################################################

from form import FormErrorMessage, _defaultValueComposer
from views import TextField, ViewableCompositeField, SelectField
import time
import operator

__all__=['IntegerField',
         'DoubleField',
         'DateField',
         'InternationalAddressField',
         'ISBNField']

########################################################################
# Validating fields
########################################################################

class ValidatingMixin:
    def __init__(self, error_format):
        self.error_format=error_format

    def formatError(self, **kw):
        if callable(self.error_format):
            return FormErrorMessage(self, self.error_format(**kw))
        return FormErrorMessage(self, self.error_format % kw)

class ValidatingTextField(TextField, ValidatingMixin):
    def __init__(self,
                 name,
                 description=None,
                 default=None,
                 required=0,
                 setable=1,
                 error_format="%(error)s",
                 **view_attrs):
        ValidatingMixin.__init__(self, error_format)
        TextField.__init__(self,
                           name,
                           description,
                           default,
                           required,
                           setable,
                           **view_attrs)
    
    

class IntegerField(ValidatingTextField):
    "Restricts validated input to integer values"
                           
    def validate(self, form=None):
        errorlist= TextField.validate(self) or []
        if self.value:
            try:
                int(self.value)
            except ValueError, ve:
                errorlist.append(self.formatError(error=ve))
        return errorlist
        

class DoubleField(ValidatingTextField):
    "Restricts validated input to double values"
    
    def validate(self, form=None):
        errorlist=TextField.validate(self) or []
        if self.value:
            try:
                float(self.value)
            except ValueError, ve:
                errorlist.append(self.formatError(error=ve))
        return errorlist


class DateField(ValidatingTextField):
    "Restricts validated input to a string which parseable according to"\
    "a specified format."
    def __init__(self,
                 name,
                 description=None,
                 default=None,
                 required=0,
                 setable=1,
                 error_format="%(error)s: Expected format: %(format)s",
                 formatString='%m/%d/%Y',
                 **view_attrs):
        """\
        Accepts an optional string which represents the date format
        which the instance will validate against,
        defaults to mm/dd/yyyy format ['%m/%d/%Y']
        """
        ValidatingTextField.__init__(self,
                                     name,
                                     description,
                                     default,
                                     required,
                                     setable,
                                     error_format,
                                     **view_attrs)
        self.format=formatString

    def validate(self, form=None):
        errorlist=TextField.validate(self) or []

        if self.value:
            try:
                time.strptime(self.value, self.format)
            except ValueError, ve:
                errorlist.append(self.formatError(error=ve, format=self.format))
        return errorlist


class InternationalAddressField(ViewableCompositeField):
    def __init__(self,
                 name,
                 description,
                 defaultState=None,
                 defaultCountry=None,
                 multiple=1,
                 setable=1,
                 componentFieldDelimiter='_',
                 valueComposer=_defaultValueComposer,
                 layout=None):
        if not defaultCountry:
            defaultCountry = 'US'
            
        # an international address field consists of two address lines,
        # a city, a state, a province, a postal code and a country
        add1 = TextField('address1', description='Address 1', size='40')
        add2 = TextField('address2', description='Address 2', size='40')
        cty = TextField('city', description='City', size='40')
        st = SelectField('state',
                         STATE_LIST,
                         default=defaultState,
                         description='Your State',
                         multiple=0,
                         size=1)
        prov = TextField('province',
                         description='Province (if outside US)',
                         size='40')
        cntry = SelectField('country',
                            COUNTRY_CODES,
                            description='Your Country',
                            default=defaultCountry,
                            multiple=0,
                            size=1)
        pstl = TextField('postal', description='Postal Code', size='40')

        # keep a reference to the fields to make validation simpler
        # [no looping over fields]
        self._address1 = add1
        self._address2 = add2
        self._city = cty
        self._state = st
        self._province = prov
        self._country = cntry
        self._postal = pstl

        #This address field maintains a set list of fields
        componentFields = [add1, add2, cty, st, prov, cntry, pstl]
        
        ViewableCompositeField.__init__(self,
                                name,
                                description,
                                None,
                                multiple,
                                setable,
                                componentFields,
                                componentFieldDelimiter)

    def validate(self, form=None):
        errorlist = []
        if not self._address1.value and not self._address2.value:
            # at least one address line must be filled out
            s='Please enter at least one line of address information.'
            errorlist.append(FormErrorMessage(self,s ))
        if not self._city.value:
            errorlist.append(FormErrorMessage(self, 'Please enter a city.'))
        if not self._postal.value:
            s='Please enter a postal code.'
            errorlist.append(FormErrorMessage(self, s))
        if not self._country.value:
            errorlist.append(FormErrorMessage(self, 'Please entery a country.'))
        else:
            # for US residents, a state must be chosen,
            # otherwise a province must be filled out
            if self._country.value == 'US' and not self._state.value:
                s='Please enter a state for US residents.'
                errorlist.append(FormErrorMessage(self, s))
            elif self._country.value != 'US' and not self._province.value:
                s='Please enter a province for non-US residents.'
                errorlist.append(FormErrorMessage(self, s))
        return errorlist    
                                

STATE_LIST = [
            ('Alabama', 'AL'),
            ('Alaska', 'AK'),
            ('Arizona', 'AZ'),
            ('Arkansas', 'AR'),
            ('California', 'CA'),
            ('Colorado', 'CO'),
            ('Connecticut', 'CT'),
            ('Delaware', 'DE'),
            ('District of Columbia', 'DC'),
            ('Florida', 'FL'),
            ('Georgia', 'GA'),
            ('Hawaii', 'HI'),
            ('Idaho', 'ID'),
            ('Illinois', 'IL'),
            ('Indiana', 'IN'),
            ('Iowa', 'IA'),
            ('Kansas', 'KS'),
            ('Kentucky', 'KY'),
            ('Louisiana', 'LA'),
            ('Maine', 'ME'),
            ('Maryland', 'MD'),
            ('Massachusetts', 'MA'),
            ('Michigan', 'MI'),
            ('Minnesota', 'MN'),
            ('Mississippi', 'MS'),
            ('Missouri', 'MO'),
            ('Montana', 'MT'),
            ('Nebraska', 'NE'),
            ('Nevada', 'NV'),
            ('New Hampshire', 'NH'),
            ('New Jersey', 'NJ'),
            ('New Mexico', 'NM'),
            ('New York', 'NY'),
            ('North Carolina', 'NC'),
            ('North Dakota', 'ND'),
            ('Ohio', 'OH'),
            ('Oklahoma', 'OK'),
            ('Oregon', 'OR'),
            ('Pennsylvania', 'PA'),
            ('Rhode Island', 'RI'),
            ('South Carolina', 'SC'),
            ('South Dakota', 'SD'),
            ('Tennessee', 'TN'),
            ('Texas', 'TX'),
            ('Utah', 'UT'),
            ('Vermont', 'VT'),
            ('Virginia', 'VA'),
            ('Washington', 'WA'),
            ('West Virginia', 'WV'),
            ('Wisconsin', 'WI'),
            ('Wyoming', 'WY'),
            ]


COUNTRY_CODES = [
            ('Albania', 'AL'),
            ('Algeria', 'DZ'),
            ('Amerian Samoa', 'AS'),
            ('Andorra', 'AD'),
            ('Angola', 'AO'),
            ('Anguilla', 'AI'),
            ('Antigua/Baruda', 'AG'),
            ('Argentina', 'AR'),
            ('Armenia', 'AM'),
            ('Aruba', 'AW'),
            ('Australia', 'AU'),
            ('Austria', 'AT'),
            ('Azerbaijan', 'AZ'),
            ('Bahamas', 'BS'),
            ('Bahrain', 'BH'),
            ('Bangladesh', 'BD'),
            ('Barbados', 'BB'),
            ('Belarus', 'BY'),
            ('Belgium', 'BE'),
            ('Belize', 'BZ'),
            ('Benin', 'BJ'),
            ('Bermuda', 'BM'),
            ('Bhutan', 'BT'),
            ('Bolivia', 'BO'),
            ('Bonaire', 'AN'),
            ('Botswana', 'BW'),
            ('Brazil', 'BR'),
            ('British Virgin Islands', 'VG'),
            ('Brunei', 'BN'),
            ('Bulgaria', 'BG'),
            ('Burkina Faso', 'BF'),
            ('Burundi', 'BI'),
            ('Cambodia', 'KH'),
            ('Cameroon', 'CM'),
            ('Canada', 'CA'),
            ('Cape Verde', 'CV'),
            ('Cayman Islands', 'KY'),
            ('Cen. African Republic', 'CF'),
            ('Chad', 'TD'),
            ('Channel Islands', 'GB'),
            ('Chile', 'CL'),
            ('China', 'CN'),
            ('Colombia', 'CO'),
            ('Congo', 'CG'),
            ('Cook Islands', 'CK'),
            ('Costa Rica', 'CR'),
            ('Croatia', 'HR'),
            ('Curacao', 'AN'),
            ('Cyprus', 'CY'),
            ('Czech Republic', 'CZ'),
            ('Denmark', 'DK'),
            ('Djibouti', 'DJ'),
            ('Dominica', 'DM'),
            ('Dominican Republic', 'DO'),
            ('Ecuador', 'EC'),
            ('Egypt', 'EG'),
            ('El Salvador', 'SV'),
            ('Equatorial Guinea', 'GQ'),
            ('Eritrea', 'ER'),
            ('Estonia', 'EE'),
            ('Ethiopia', 'ET'),
            ('Faroe Islands', 'FO'),
            ('Fiji', 'FJ'),
            ('Finland', 'FI'),
            ('France', 'FR'),
            ('French Guinea', 'GF'),
            ('French Polynesia', 'PF'),
            ('Gabon', 'GA'),
            ('Gambia', 'GM'),
            ('Georgia', 'GE'),
            ('Germany', 'DE'),
            ('Ghana', 'GH'),
            ('Gibraltar', 'GI'),
            ('Greece', 'GR'),
            ('Greenland', 'GL'),
            ('Grenada', 'GD'),
            ('Guam', 'GU'),
            ('Guatemala', 'GT'),
            ('Guinea', 'GN'),
            ('Guinea-Bissau', 'GW'),
            ('Guyana', 'GY'),
            ('Haiti', 'HT'),
            ('Honduras', 'HN'),
            ('Hong Kong', 'HK'),
            ('Hungary', 'HU'),
            ('Iceland', 'IS'),
            ('India', 'IN'),
            ('Indonesia', 'ID'),
            ('Iran', 'IR'),
            ('Iraq', 'IQ'),
            ('Israel', 'IL'),
            ('Italy', 'IT'),
            ('Ivory Coast', 'CI'),
            ('Jamaica', 'JM'),
            ('Japan', 'JP'),
            ('Jordan', 'JO'),
            ('Kazakhstan', 'KZ'),
            ('Kenya', 'KE'),
            ('Kuwait', 'KW'),
            ('Kyrgyzstan', 'KG'),
            ('Latvia', 'LV'),
            ('Lebanon', 'LB'),
            ('Lesotho', 'LS'),
            ('Liberia', 'LR'),
            ('Liechtenstein', 'LI'),
            ('Lithuania', 'LT'),
            ('Luxembourg', 'LU'),
            ('Macao', 'MO'),
            ('Macedonia', 'MK'),
            ('Madagascar', 'MG'),
            ('Malawi', 'MW'),
            ('Malaysia', 'MY'),
            ('Maldives', 'MV'),
            ('Malta', 'ML'),
            ('Marshall Islands', 'MH'),
            ('Martinique', 'MQ'),
            ('Mauritania', 'MR'),
            ('Mauritius', 'MU'),
            ('Mexico', 'MX'),
            ('Micronesia', 'FM'),
            ('Moldova', 'MD'),
            ('Monaco', 'MC'),
            ('Mongolia', 'MN'),
            ('Montserrat', 'MS'),
            ('Morocco', 'MA'),
            ('Mozambique', 'MZ'),
            ('Myanmar (Burma)', 'MM'),
            ('Namibia', 'NA'),
            ('Nepal', 'NP'),
            ('Netherlands', 'NL'),
            ('New Caledonia', 'NC'),
            ('New Zealand', 'NZ'),
            ('Nicaragua', 'NI'),
            ('Niger', 'NE'),
            ('Nigeria', 'NG'),
            ('Northern Ireland', 'GB'),
            ('Norway', 'NO'),
            ('Oman', 'OM'),
            ('Pakistan', 'PK'),
            ('Palau', 'PW'),
            ('Panama', 'PA'),
            ('Papua New Guinea', 'PG'),
            ('Paraguay', 'PY'),
            ('Peru', 'PE'),
            ('Philippines', 'PH'),
            ('Poland', 'PL'),
            ('Portugal', 'PT'),
            ('Puerto Rico', 'PR'),
            ('Qatar', 'QA'),
            ('Republic of Ireland', 'IE'),
            ('Reunion Islands', 'RE'),
            ('Romania', 'RO'),
            ('Russia', 'RU'),
            ('Rwanda', 'RW'),
            ('Saba', 'AN'),
            ('Saipan', 'MP'),
            ('San Marino', 'IT'),
            ('Saudi Arabia', 'SA'),
            ('Scotland', 'GB'),
            ('Senegal', 'SN'),
            ('Seychelles', 'SC'),
            ('Sierra Leone', 'SL'),
            ('Singapore', 'SG'),
            ('Slovakia', 'SK'),
            ('Slovenia', 'SI'),
            ('Somalia', 'SO'),
            ('South Africa', 'ZA'),
            ('South Korea', 'KR'),
            ('Spain', 'ES'),
            ('Sri Lanka', 'LK'),
            ('St. Croix', 'VI'),
            ('St. Eustasius', 'AN'),
            ('St. John', 'VI'),
            ('St. Kitts and Nevis', 'KN'),
            ('St. Lucia', 'LC'),
            ('St. Maarten', 'AN'),
            ('St. Martin', 'AN'),
            ('St. Thomas', 'VI'),
            ('St. Vincent', 'VC'),
            ('Sudan', 'SD'),
            ('Suriname', 'SR'),
            ('Swaziland', 'SZ'),
            ('Sweden', 'SE'),
            ('Switzerland', 'CH'),
            ('Syria', 'SY'),
            ('Taiwan', 'TW'),
            ('Tanzania', 'TZ'),
            ('Thailand', 'TH'),
            ('Togo', 'TG'),
            ('Trinidad And Tobago', 'TT'),
            ('Tunisia', 'TN'),
            ('Turkey', 'TR'),
            ('Turkmenistan', 'TM'),
            ('Turks And Caicos Islands', 'TC'),
            ('Uganda', 'UG'),
            ('Ukraine', 'UA'),
            ('United Arab Emirates', 'AE'),
            ('United Kingdom', 'GB'),
            ('United States', 'US'),
            ('Uruguay', 'UY'),
            ('Uzbekistan', 'UZ'),
            ('Vanuatu', 'VU'),
            ('Vatican City', 'VA'),
            ('Venezuela', 'VE'),
            ('Vietnam', 'VN'),
            ('Wales', 'GB'),
            ('Wallis and Futuna', 'WF'),
            ('Yemen', 'YE'),
            ('Zaire', 'ZR'),
            ('Zambia', 'ZM'),
            ('Zimbabwe', 'ZW'),
        ]

def check_isbn(isbn):
	isbn=filter(lambda c: c != '-', isbn)
	if len(isbn)!=10:
		return
	weights=range(2, 11)
	weights.reverse()
	l=[z * int(c) for c, z in zip(isbn, weights)]
	x=reduce(operator.add, l) % 11
	checkdigit='0123456789X0'[(11-x)]
	return checkdigit==isbn[-1]


class ISBNField(ValidatingTextField):
    "Restricts validated input to legal ISBNs"
    def validate(self, form=None):
        errorlist= TextField.validate(self) or []
        if self.value:
            if not check_isbn(self.value):
                errorlist.append(self.formatError(error="invalid ISBN"))
        return errorlist    
