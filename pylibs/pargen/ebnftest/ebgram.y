:noop:                S : method ENTITY_NAME WHERE where_clause 
                           [sortby_clause] [slice_clause]

:noop:           method : GET | SELECT | EXISTS | COUNT

:noop:     where_clause : or_expr

:noop:         or_expr : or_expr OR and_expr
                           | and_expr

:noop:      	and_expr : and_expr AND not_expr
                           | not_expr

:noop:        not_expr : NOT rel_expr
                           | rel_expr

:noop:       rel_expr :  qty RANGE qty AND qty 
                           | qty OP qty
                           | '(' or_expr ')' 
                           | qty
                           | attr_item IN (BINDVAR | tuple)
                           | BINDVAR IN ATTR

:noop:  	   tuple : '(' qty (',' qty)* ')'

:noop:           qty : DATE '(' QUOTESTR ')'  
                           | attr_item 
                           | INT 
                           | FLOAT 
                           | QUOTESTR 
                           | BINDVAR

:noop: attr_item : ATTR [ '[' ( BINDVAR | QUOTESTR ) ']' ]

:noop:     sortby_clause : SORTBY attr_spec ( ',' attr_spec)*

:noop:       attr_spec : attr_item [DESC]

:noop:     slice_clause : SLICE '(' slice_args ')'

:noop: slice_args : INT ',' INT [ ',' INT]
#:noop: slice_args : (INT ',' INT) | (INT ',' INT ',' INT)

