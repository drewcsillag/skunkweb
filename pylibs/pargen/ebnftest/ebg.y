:_OPTEXISTS:_temp1:sortby_clause
:_OPTMISSING:_temp1:
:_OPTEXISTS:_temp2:slice_clause
:_OPTMISSING:_temp2:
:noop:S:method ENTITY_NAME WHERE where_clause _temp1 _temp2
:_ALTPASS:_temp3:EXISTS
:_ALTPASS:_temp3:COUNT
:_ALTPASS:_temp4:SELECT
:_ALTPASS:_temp4:_temp3
:_ALTPASS:_temp5:GET
:_ALTPASS:_temp5:_temp4
:noop:method:_temp5
:noop:where_clause:or_expr
:_PARENPASS:_temp6:or_expr OR and_expr
:_ALTPASS:_temp7:_temp6
:_ALTPASS:_temp7:and_expr
:noop:or_expr:_temp7
:_PARENPASS:_temp8:and_expr AND not_expr
:_ALTPASS:_temp9:_temp8
:_ALTPASS:_temp9:not_expr
:noop:and_expr:_temp9
:_PARENPASS:_temp10:NOT rel_expr
:_ALTPASS:_temp11:_temp10
:_ALTPASS:_temp11:rel_expr
:noop:not_expr:_temp11
:_PARENPASS:_temp12:qty RANGE qty AND qty
:_PARENPASS:_temp13:qty OP qty
:_PARENPASS:_temp14:( or_expr )
:_ALTPASS:_temp15:BINDVAR
:_ALTPASS:_temp15:tuple
:_PARENPASS:_temp16:_temp15
:_PARENPASS:_temp17:attr_item IN _temp16
:_PARENPASS:_temp18:BINDVAR IN ATTR
:_ALTPASS:_temp19:_temp17
:_ALTPASS:_temp19:_temp18
:_ALTPASS:_temp20:qty
:_ALTPASS:_temp20:_temp19
:_ALTPASS:_temp21:_temp14
:_ALTPASS:_temp21:_temp20
:_ALTPASS:_temp22:_temp13
:_ALTPASS:_temp22:_temp21
:_ALTPASS:_temp23:_temp12
:_ALTPASS:_temp23:_temp22
:noop:rel_expr:_temp23
:_PARENPASS:_temp24:, qty
:_STARRECUR:_temp25:_temp24 _temp25
:_STARANCHOR:_temp25:
:noop:tuple:( qty _temp25 )
:_PARENPASS:_temp26:DATE ( QUOTESTR )
:_ALTPASS:_temp27:QUOTESTR
:_ALTPASS:_temp27:BINDVAR
:_ALTPASS:_temp28:FLOAT
:_ALTPASS:_temp28:_temp27
:_ALTPASS:_temp29:INT
:_ALTPASS:_temp29:_temp28
:_ALTPASS:_temp30:attr_item
:_ALTPASS:_temp30:_temp29
:_ALTPASS:_temp31:_temp26
:_ALTPASS:_temp31:_temp30
:noop:qty:_temp31
:_ALTPASS:_temp32:BINDVAR
:_ALTPASS:_temp32:QUOTESTR
:_PARENPASS:_temp33:_temp32
:_OPTEXISTS:_temp34:[ _temp33 ]
:_OPTMISSING:_temp34:
:noop:attr_item:ATTR _temp34
:_PARENPASS:_temp35:, attr_spec
:_STARRECUR:_temp36:_temp35 _temp36
:_STARANCHOR:_temp36:
:noop:sortby_clause:SORTBY attr_spec _temp36
:_OPTEXISTS:_temp37:DESC
:_OPTMISSING:_temp37:
:noop:attr_spec:attr_item _temp37
:noop:slice_clause:SLICE ( slice_args )
:_PARENPASS:_temp38:INT , INT
:_PARENPASS:_temp39:INT , INT , INT
:_ALTPASS:_temp40:_temp38
:_ALTPASS:_temp40:_temp39
:noop:slice_args:_temp40
