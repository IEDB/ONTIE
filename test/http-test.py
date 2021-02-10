#!/usr/bin/env python3

import csv
import http.client
import json
import logging
import os
import sys
import re
import requests

logging.basicConfig(level=logging.INFO)


def main(args):
    '''Usage: ./http-test.py base_url api.md'''
    base = args[1]
    api_doc = args[2]
    get_tests = parse_get_test_strings(get_test_strings(api_doc))
    post_tests = parse_post_test_strings(post_test_strings(api_doc))
    success = run_tests(base, get_tests, post_tests)
    if not success:
        logging.error(' http-test failed')
        sys.exit(1)
    else:
        logging.info(' http-test passed')


def run_tests(base, get_tests, post_tests):
    '''Given a set of get tests and a set of post tests, run the tests by
    comparing the actual response to the expected repsonse. Return true if all
    tests pass.'''
    success = True
    # run the GET tests
    for pair in get_tests:
        path = pair[0]
        expected = pair[1]
        result = get(base, path)
        success = compare(path, expected, result, 'GET')
    # run the POST tests
    for tpl in post_tests:
        path = tpl[0]
        body = tpl[1]
        expected = tpl[2]
        result = post(base, path, body)
        success = compare(
            path,
            expected,
            result,
            'POST (%s)' % body.replace('\n', '\\n'))
    return success


def get(base, path):
    '''Perform a GET request on a path in ontology.iedb.org. Return the response
    as a string.'''
    if 'localhost' in base or '127.0.0.1' in base:
        # use requests for local
        os.environ['NO_PROXY'] = '127.0.0.1'
        r = requests.get(base + path)
        return fix_result(r.content)
    # use http client for HTTPS
    c = http.client.HTTPSConnection(base, timeout=10)
    c.request('GET', path)
    resp = c.getresponse()
    return fix_result(resp.read())


def post(base, path, body):
    '''Perform a POST request on a path in ontology.iedb.org with a body. Return
    the response as a string.'''
    if 'localhost' in base or '127.0.0.1' in base:
        # use requests for local
        os.environ['NO_PROXY'] = '127.0.0.1'
        r = requests.post(base + path, body)
        return fix_result(r.content)
    # use http client for HTTPS
    c = http.client.HTTPSConnection(base, timeout=10)
    c.request('POST', path, body)
    resp = c.getresponse()
    return fix_result(resp.read())


def fix_result(result):
    '''Given an HTTP GET result, strip extra characters and maybe fix
    newlines/tabs if not in JSON format.'''
    result = str(result)
    result = result.lstrip('b\'').rstrip('\'')
    if re.search(r'\{.*\}', result):
        # changing tabs and newlines might break JSON
        return result
    if '\\t' in result:
        result = result.replace('\\t', '\t')
    if '\\n' in result:
        result = result.replace('\\n', '\n')
    return result


def compare(path, expected, result, method):
    '''Given a path tested, the expected output, the actual result, and the
    method (GET or POST), compare the expected and the result. Return true if
    the result contains the expected.'''
    if re.search(r'\{.*\}', result):
        ok = compare_json(path, expected, result, method)
    elif re.search(r'[^\t]+\t', result):
        ok = compare_tsv(path, expected, result, method)
    else:
        logging.error(' %s unknown result format' % path)
        return False
    return ok


def compare_tsv(path, expected, result, method):
    '''Given the path used, the expected output in TSV, and the actual result
    in TSV, determine if the result contains the expected output. If not, return
    false.'''
    expected_tsv = []
    reader = csv.reader(expected.splitlines(), delimiter='\t')
    for row in reader:
        for item in row:
            if "|" in item:
                item = item.split("|")
                item = "|".join(sorted(item))
            expected_tsv.append(item)
    result_tsv = []
    reader = csv.reader(result.splitlines(), delimiter='\t')
    for row in reader:
        for item in row:
            if "|" in item:
                item = item.split("|")
                item = "|".join(sorted(item))
            result_tsv.append(item)
    diff = [x for x in expected_tsv if x not in result_tsv]
    if not diff:
        logging.info(' OK %s %s' % (method, path))
        return True
    else:
        err_string = ''' {0} unknown {1} results: {2}
        --- EXPECTED ---\n{3}
        --- ACTUAL ---\n{4}'''.format(
            path, 
            method, 
            ', '.join(diff), 
            expected,
            result)
        logging.error(err_string)
        return False


def compare_json(path, expected, result, method):
    '''Given the path used, the expected output in JSON, and the actual result
    in JSON, determine if the result contains the expected output. If not,
    return false.'''
    j_expected = json.loads(expected)
    j_result = json.loads(result.replace("\\n", "\n"))
    if "@context" in j_result:
        del j_result["@context"]
    diff = [x for x in j_expected.items() if x not in j_result.items()]

    if not diff:
        logging.info(' OK %s %s' % (method, path))
        return True
    else:
        err_string = ''' {0} unknown {1} results: {2}
        --- EXPECTED ---\n{3}
        --- ACTUAL ---\n{4}'''.format(
            path, 
            method, 
            str(diff), 
            json.dumps(j_expected, indent=4, sort_keys=True), 
            json.dumps(j_result, indent=4, sort_keys=True))
        logging.error(err_string)
        return False


def get_test_strings(api_doc):
    '''Given the api markdown doc, extract the contents between the test markers
    and return a list of those strings.'''
    return test_strings(api_doc, '<!-- GET TEST -->', '<!-- END GET TEST -->')


def parse_get_test_strings(test_strings):
    '''Given a list of test strings, parse each string to create a path-expected
    result pair. Return the set of these pairs.'''
    tests = []
    for t in test_strings:
        path = re.findall(r'\[.*\]\((.*)\)', t)[0]
        result = re.findall(r'```\n([^`]+)\n```', t)[0]
        tests.append((path, result))
    return tests


def post_test_strings(api_doc):
    '''Given the api markdown doc, extract the contents between the test markers
    and return a list of those strings.'''
    return test_strings(api_doc, '<!-- POST TEST -->', '<!-- END POST TEST -->')


def parse_post_test_strings(test_strings):
    '''Given a set of test strings, parse each string to find the path to test,
    the body of the POST request, and the expected result. Return the set of
    these tuples.'''
    tests = []
    for t in test_strings:
        path = re.findall(r'\[.*\]\((.*)\)', t)[0]
        body_and_expected = re.findall(r'```\n([^`]+)\n```', t)[:2]
        tests.append((path, body_and_expected[0], body_and_expected[1]))
    return tests


def test_strings(api_doc, start, end):
    '''Given the path to the API doc, a start flag for tests, and an end flag
    for tests, return the strings between the flags.'''
    tests = []
    test_str = ''
    with open(api_doc, 'r') as f:
        test = False
        test_str = ''
        for line in f:
            if start in line:
                test = True
                continue
            elif end in line:
                tests.append(test_str)
                test_str = ''
                test = False
            if test:
                test_str += line
    return tests


if __name__ == '__main__':
    main(sys.argv)
