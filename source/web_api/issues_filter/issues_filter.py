from antlr4 import *
from jqlLexer import jqlLexer
from jqlParser import jqlParser
from jqlListener import jqlListener
from antlr4.error.ErrorListener import ErrorListener
from antlr4.tree.Trees import Trees
from query_parameters import QueryParameters
import json

class JQLPrintListener(jqlListener):
    def __init__(self):
        self.date_field_interval = set()
        self.issue_type_field_interval = set()
        self.order_by_interval = set()
        
    def enterField(self, ctx):
        datetime_fields = ['created','createdDate','date','due','dueDate','lastViewed','resolutionDate','resolved','updated','updatedDate']
        issue_type_fields = ['issuetype', 'type', 'status']
        
        for field in datetime_fields:
            if field.lower() in ctx.getText().lower():
                parent_ctx = ctx.__dict__['parentCtx']
                self.date_field_interval.add(parent_ctx.getSourceInterval())
                
        for field in issue_type_fields:
            if field.lower() in ctx.getText().lower():
                parent_ctx = ctx.__dict__['parentCtx']
                self.issue_type_field_interval.add(parent_ctx.getSourceInterval())
            
    def enterKeyword(self, ctx):
        if ctx.getText().lower() == 'changed':
            parent_ctx = ctx.__dict__['parentCtx']
            self.issue_type_field_interval.add(parent_ctx.getSourceInterval())

    def enterCompare_dates(self, ctx):
        self.date_field_interval.add(ctx.getSourceInterval())
        
    def enterOrdering_term(self, ctx):
        self.order_by_interval.add(ctx.getSourceInterval())

def get_warning_index(jql, interval_type):
    input = InputStream(jql)
    lexer = jqlLexer(input)
    tokens = CommonTokenStream(lexer)
    parser = jqlParser(tokens)
    tree = parser.parse()
    printer = JQLPrintListener()
    walker = ParseTreeWalker()
    walker.walk(printer, tree)
    
    if interval_type == 'date':
        intervals = printer.date_field_interval
    elif interval_type == 'issue_type':
        intervals = printer.issue_type_field_interval

    parsed_warning = []
    for interval in intervals:
        start_index = len(jql)
        stop_index = 0
        for i in range(interval[0], interval[1]+1):
            token = tokens.get(i) # antlr4.Token.CommonToken
            start_index = min(start_index, token.__dict__['start'])
            stop_index = max(stop_index, token.__dict__['stop']) + 1
        parsed_warning.append([start_index, stop_index])

    return parsed_warning # returns index of strings that might be problematic
    
def get_order_by_index(jql):
    input = InputStream(jql)
    lexer = jqlLexer(input)
    tokens = CommonTokenStream(lexer)
    parser = jqlParser(tokens)
    tree = parser.parse()
    printer = JQLPrintListener()
    walker = ParseTreeWalker()
    walker.walk(printer, tree)
    start_index = None
    stop_index = None
    for interval in printer.order_by_interval:
        start_index = len(jql)
        stop_index = 0
        for i in range(interval[0], interval[1]+1):
            token = tokens.get(i) # antlr4.Token.CommonToken
            start_index = min(start_index, token.__dict__['start'])
            stop_index = max(stop_index, token.__dict__['stop']) + 1

    return [start_index,stop_index] # returns [start, end] index of order by clause

def response_formatter(status_code='400', body={'message': 'error'}):
    api_response = {
        'statusCode': status_code,
        'headers': {
            'Access-Control-Allow-Origin' : '*',
            'Access-Control-Allow-Credentials' : True
        },
        'body': json.dumps(body)
    }
    return api_response

def handler(event, context):
    try:
        queryParameters = QueryParameters(event)
        jql = queryParameters.getJQL()
    except Exception as e:
        payload = {"message": "Query parameter not given"}
        return response_formatter(status_code='400', body=payload)

    date_field_index = get_warning_index(jql, 'date')
    issue_type_field_index = get_warning_index(jql, 'issue_type')
    order_by_index = get_order_by_index(jql)
    issue_filter = {}
    issue_filter['dateFieldIndex'] = date_field_index
    issue_filter['issueTypeFieldIndex'] = issue_type_field_index

    if order_by_index[0] and order_by_index[1]:
        issue_filter['filteredJQL'] = jql[:order_by_index[0]] + jql[order_by_index[1]:]
    else:
        issue_filter['filteredJQL'] = jql

    return response_formatter(status_code='200', body=issue_filter)

    