'''Django Test Suite runner that also writes out JUnit-compatible XML

Based on the junitxml plugin from the unittest2 plugin experiments:
https://bitbucket.org/jpellerin/unittest2, unittest2.plugins.junitxml
'''
import time
from xml.etree import ElementTree as ET

from django.conf import settings
from django.test.runner import DiscoverRunner

try:
    # Django 1.6
    from django.utils.unittest import TextTestRunner, TextTestResult
except ImportError:
    # Django 1.7+ because bundled unittest is going away
    from unittest import TextTestRunner, TextTestResult

RESET = "\033[0m"
BOLD = "\033[1m"
RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"


class ERPTestResult(TextTestResult):
    def startTest(self, test):
        self.case_start_time = time.time()
        super(ERPTestResult, self).startTest(test)

    def _time(self, testcase, text, color):
        return '%s%s%s (%ss)%s' % (BOLD, color, text,
                                   testcase.get('time'), RESET)

    def addSuccess(self, test):
        pass
        # testcase = self._make_testcase_element(test)
        # if self.showAll:
        #     self.stream.writeln(self._time(testcase, 'OK', GREEN))
        # elif self.dots:
        #     self.stream.write('.')
        #     self.stream.flush()
        # super(TextTestResult, self).addSuccess(test)

    def addFailure(self, test, err):
        testcase = self._make_testcase_element(test)
        test_result = ET.SubElement(testcase, 'failure')
        self._add_tb_to_test(test, test_result, err)
        if self.showAll:
            self.stream.writeln(self._time(testcase, 'FAIL', YELLOW))
        elif self.dots:
            self.stream.write('F')
            self.stream.flush()
        super(TextTestResult, self).addFailure(test, err)

    def addError(self, test, err):
        testcase = self._make_testcase_element(test)
        test_result = ET.SubElement(testcase, 'error')
        self._add_tb_to_test(test, test_result, err)
        if self.showAll:
            self.stream.writeln(self._time(testcase, 'ERROR', RED))
        elif self.dots:
            self.stream.write('E')
            self.stream.flush()
        super(TextTestResult, self).addError(test, err)

    def addUnexpectedSuccess(self, test):
        pass
        # testcase = self._make_testcase_element(test)
        # test_result = ET.SubElement(testcase, 'skipped')
        # test_result.set('message', 'Test Skipped: Unexpected Success')
        # super(ERPTestResult, self).addUnexpectedSuccess(test)

    def addSkip(self, test, reason):
        testcase = self._make_testcase_element(test)
        test_result = ET.SubElement(testcase, 'skipped')
        test_result.set('message', 'Test Skipped: %s' % reason)
        super(ERPTestResult, self).addSkip(test, reason)

    def addExpectedFailure(self, test, err):
        testcase = self._make_testcase_element(test)
        test_result = ET.SubElement(testcase, 'skipped')
        self._add_tb_to_test(test, test_result, err)
        super(ERPTestResult, self).addExpectedFailure(test, err)

    def startTestRun(self):
        self.tree = ET.Element('testsuite')
        self.run_start_time = time.time()
        super(ERPTestResult, self).startTestRun()

    def stopTestRun(self):
        run_time_taken = time.time() - self.run_start_time
        self.tree.set('name', 'Django Project Tests')
        self.tree.set('errors', str(len(self.errors)))
        self.tree.set('failures', str(len(self.failures)))
        self.tree.set('skips', str(len(self.skipped)))
        self.tree.set('tests', str(self.testsRun))
        self.tree.set('time', "%.3f" % run_time_taken)

        output = ET.ElementTree(self.tree)
        root = output.getroot()
        with open(settings.ERP_FILENAME, 'w') as file:
            result = 'ClassName ,TestName ,Error or Failure , Error Type'
            file.write(result)
            file.write('\n')
            for child in root:
                result = '{} , {} ,'.format(child.attrib.get('classname'), child.attrib.get('name'))
                for c in child:
                    result += ' {} , {}'.format(c.tag, c.attrib.get('type'))
                    file.write(result)
                    file.write('\n')
        super(ERPTestResult, self).stopTestRun()

    def _make_testcase_element(self, test):
        time_taken = 0.0
        if hasattr(self, 'case_start_time'):
            time_taken = time.time() - self.case_start_time
        classname = ('%s.%s' % (test.__module__, test.__class__.__name__)).split('.')
        testcase = ET.SubElement(self.tree, 'testcase')
        testcase.set('time', "%.6f" % time_taken)
        testcase.set('classname', '.'.join(classname))
        name = getattr(test, '_testMethodName', None)
        if not name:
            name = getattr(test, 'description', None)
        if not name:
            name = 'ERROR in test class %s' % test.__class__.__name__
        testcase.set('name', name)
        return testcase

    def _add_tb_to_test(self, test, test_result, err):
        '''Add a traceback to the test result element'''
        exc_class, exc_value, tb = err
        # tb_str = self._exc_info_to_string(err, test)
        test_result.set('type', '%s.%s' % (exc_class.__module__, exc_class.__name__))
        # test_result.set('message', str(exc_value))
        # test_result.text = tb_str


class ERPTestRunner(TextTestRunner):
    resultclass = ERPTestResult


class ERPTestSuiteRunner(DiscoverRunner):
    def run_suite(self, suite, **kwargs):
        return ERPTestRunner(verbosity=self.verbosity, failfast=self.failfast).run(suite)
