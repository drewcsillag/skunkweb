:noop:      	       S : RuleList
:noop:      	RuleList : Rule RuleList
:noop:      	RuleList :
:RuleLine:  	    Rule : COLON id COLON TokItem COLON TokList
:TTtoTokList:    TokList : Token TokList
:TTtoTokList:    TokList : id TokList
:NullToTokList:  TokList :
:TokenToTokItem: TokItem : Token
:idToTokItem:    TokItem : id

