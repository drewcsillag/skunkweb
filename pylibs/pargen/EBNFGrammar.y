:noop:                 S : RuleList
:noop:          RuleList : Rule RuleList
:noop:          RuleList :
:buildRule:         Rule : COLON TOKEN COLON TOKEN COLON Exprs
:ExprRecur:        Exprs : ExprList | Exprs
:ExprSingle:       Exprs : ExprList
#:buildParens:      Exprs : ( Exprs )

:ELBuildRecur:  ExprList : Expr ExprList
:ELBuildAnchor: ExprList :

:noop1:             Expr : StarExpr 
	        	 
:buildStar:     StarExpr : PlusExpr *
:noop1:         StarExpr : PlusExpr
	        
:buildPlus:     PlusExpr : OptExpr +
:noop1:         PlusExpr : OptExpr
                
:buildOptional:  OptExpr : [ ExprList ]
:noop1:          OptExpr : ParenExpr

:buildParens:  ParenExpr : ( Exprs )
:noopToken:    ParenExpr : TOKEN

