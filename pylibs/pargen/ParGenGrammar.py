#  
#  Copyright (C) 2001 Andrew T. Csillag <drew_csillag@geocities.com>
#  
#      This program is free software; you can redistribute it and/or modify
#      it under the terms of the GNU General Public License as published by
#      the Free Software Foundation; either version 2 of the License, or
#      (at your option) any later version.
#  
#      This program is distributed in the hope that it will be useful,
#      but WITHOUT ANY WARRANTY; without even the implied warranty of
#      MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#      GNU General Public License for more details.
#  
#      You should have received a copy of the GNU General Public License
#      along with this program; if not, write to the Free Software
#      Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111, USA.
#   
rules = [{'funcName': 'noop', 'ruleString': 'S -> RuleList', 'lhs': 'S', 'lenrhs': 1}, {'funcName': 'noop', 'ruleString': 'RuleList -> Rule RuleList', 'lhs': 'RuleList', 'lenrhs': 2}, {'funcName': 'noop', 'ruleString': 'RuleList -> ', 'lhs': 'RuleList', 'lenrhs': 0}, {'funcName': 'RuleLine', 'ruleString': 'Rule -> COLON id COLON TokItem COLON TokList', 'lhs': 'Rule', 'lenrhs': 6}, {'funcName': 'TTtoTokList', 'ruleString': 'TokList -> Token TokList', 'lhs': 'TokList', 'lenrhs': 2}, {'funcName': 'TTtoTokList', 'ruleString': 'TokList -> id TokList', 'lhs': 'TokList', 'lenrhs': 2}, {'funcName': 'NullToTokList', 'ruleString': 'TokList -> ', 'lhs': 'TokList', 'lenrhs': 0}, {'funcName': 'TokenToTokItem', 'ruleString': 'TokItem -> Token', 'lhs': 'TokItem', 'lenrhs': 1}, {'funcName': 'idToTokItem', 'ruleString': 'TokItem -> id', 'lhs': 'TokItem', 'lenrhs': 1}]
gotos = {16: {}, 15: {}, 14: {'TokList': 16}, 13: {'TokList': 15}, 12: {}, 11: {'TokList': 12}, 10: {}, 9: {}, 8: {}, 7: {'TokItem': 8}, 6: {}, 5: {}, 4: {}, 3: {}, 2: {}, 1: {'Rule': 1, 'RuleList': 5}, 0: {'RuleList': 2, 'S': 3, 'Rule': 1}}
terminals = ['id', '$', 'COLON', 'Token']
states = {16: {'$': ('r', 4), 'COLON': ('r', 4)}, 15: {'$': ('r', 5), 'COLON': ('r', 5)}, 14: {'id': ('s', 13), '$': ('r', 6), 'Token': ('s', 14), 'TokList': ('s', 16), 'COLON': ('r', 6)}, 13: {'id': ('s', 13), '$': ('r', 6), 'Token': ('s', 14), 'TokList': ('s', 15), 'COLON': ('r', 6)}, 12: {'$': ('r', 3), 'COLON': ('r', 3)}, 11: {'id': ('s', 13), '$': ('r', 6), 'Token': ('s', 14), 'TokList': ('s', 12), 'COLON': ('r', 6)}, 10: {'COLON': ('r', 7)}, 9: {'COLON': ('r', 8)}, 8: {'COLON': ('s', 11)}, 7: {'Token': ('s', 10), 'id': ('s', 9), 'TokItem': ('s', 8)}, 6: {'COLON': ('s', 7)}, 5: {'$': ('r', 1)}, 4: {'id': ('s', 6)}, 3: {'$': ('a', -1)}, 2: {'$': ('r', 0)}, 1: {'RuleList': ('s', 5), 'Rule': ('s', 1), '$': ('r', 2), 'COLON': ('s', 4)}, 0: {'Rule': ('s', 1), 'RuleList': ('s', 2), '$': ('r', 2), 'COLON': ('s', 4), 'S': ('s', 3)}}
