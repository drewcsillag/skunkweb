%token ENTITY_NAME
%token WHERE
%token GET
%token SELECT
%token EXISTS
%token COUNT
%token OR
%token AND
%token NOT
%token OP
%token RANGE
%token IN
%token BINDVAR
%token DATE
%token QUOTESTR
%token ATTR
%token FLOAT
%token INT
%token SORTBY
%token DESC
%token SLICE

%%
S : method ENTITY_NAME WHERE where_clause sortby_clause slice_clause ;

method : GET ;
method : SELECT ;
method : EXISTS ;
method : COUNT ;


where_clause : or_expr ; 
or_expr : and_expr OR or_expr ;
or_expr : and_expr ;
/*or_expr : NOT where_clause ;*/

and_expr : not_expr AND and_expr ;
and_expr : not_expr ;

not_expr : NOT rel_expr ;
not_expr : rel_expr ; 

rel_expr : qty RANGE qty AND qty ;
rel_expr : qty OP qty ;
rel_expr : '(' or_expr ')' ;
rel_expr : qty ;


rel_expr : attr_item IN in_rhs ;
in_rhs : BINDVAR ;
in_rhs : tuple_x ;
tuple_x : '(' list_o_shit ')' ;
list_o_shit : qty ',' list_o_shit ;
list_o_shit : qty ;

rel_expr : BINDVAR IN ATTR ;

qty : DATE '(' QUOTESTR ')' ;


qty : attr_item ;
attr_item : ATTR '[' BINDVAR ']' ;
attr_item : ATTR ;

qty : INT ;
qty : FLOAT ;
qty : QUOTESTR ;
qty : BINDVAR ;


sortby_clause : SORTBY attr_list ;
sortby_clause : ;

attr_list : attr_spec ;
attr_list : attr_list ',' attr_spec;

attr_spec : attr_item descending ;

descending : DESC ;
descending : ;


slice_clause : SLICE '(' slice_args ')' ;
slice_clause : ;

slice_args : INT ',' INT ;
slice_args : INT ',' INT ',' INT ;
