
:query:                S : method ENTITY_NAME WHERE where_clause sortby_clause slice_clause


:noop1:           method : GET
:noop1:           method : SELECT
:noop1:           method : EXISTS
:noop1:           method : COUNT


:noop1:     where_clause : or_expr
:orExpr:         or_expr : or_expr OR and_expr
:noop1:          or_expr : and_expr
:negate:         or_expr : NOT where_clause

:andExpr:      	and_expr : and_expr AND not_expr
:noop1:      	and_expr : not_expr

:negate:        not_expr : NOT rel_expr
:noop1:         not_expr : rel_expr

:between:       rel_expr : qty RANGE qty AND qty
:relExpr:      	rel_expr : qty OP qty
:paren:      	rel_expr : ( or_expr )
:exists:        rel_expr : qty


:intest:        rel_expr : attr_item IN in_rhs
:inrhsbv:  	  in_rhs : BINDVAR
:inrhs:  	  in_rhs : tuple_x
:intup:  	 tuple_x : ( list_o_shit )
:los_recur:  list_o_shit : qty , list_o_shit
:los_single: list_o_shit : qty

:relation_in:   rel_expr : BINDVAR IN ATTR

:dateconv:           qty : DATE ( QUOTESTR )


:noop1:              qty : attr_item
:attrdict2qty: attr_item : ATTR [ BINDVAR ]
:attr2qty:     attr_item : ATTR

:noop1:       	     qty : INT
:noop1:       	     qty : FLOAT
:noop1:       	     qty : QUOTESTR
:bind2qty:     	     qty : BINDVAR


:noop:     sortby_clause : SORTBY attr_list
:noop:     sortby_clause :

:noop:         attr_list : attr_spec
:attrl:        attr_list : attr_list, attr_spec

:attrsp:       attr_spec : attr_item descending

:descattr:    descending : DESC
:nodescattr:  descending : 


:slice:     slice_clause : SLICE ( slice_args )
:noop:     slice_clause : 

:slice_no_fudge: slice_args : INT , INT
:slice_fudge:    slice_args : INT , INT, INT
