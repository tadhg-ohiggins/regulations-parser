from datetime import date
import os
from time import time
from unittest import TestCase

import click
from click.testing import CliRunner
from mock import patch

from regparser.commands import annual_editions
from regparser.history.versions import Version
from regparser.index import dependency, entry
from regparser.tree.struct import Node


class CommandsAnnualEditionsTests(TestCase):
    def setUp(self):
        self.cli = CliRunner()

    def test_last_versions_raises_exception(self):
        """If there are no versions available, we should receive an
        exception"""
        with self.cli.isolated_filesystem():
            with self.assertRaises(click.UsageError):
                list(annual_editions.last_versions('12', '1000'))

    @patch('regparser.commands.annual_editions.annual.find_volume')
    def test_last_versions_multiple_versions(self, find_volume):
        """If multiple versions affect the same annual edition, we should only
        receive the last"""
        find_volume.return_value = True
        with self.cli.isolated_filesystem():
            path = entry.Version('12', '1000')
            (path / '1111').write(Version('1111', date(2000, 12, 1),
                                          date(2000, 12, 1)))
            (path / '2222').write(Version('2222', date(2000, 12, 2),
                                          date(2000, 12, 2)))
            (path / '3333').write(Version('3333', date(2001, 12, 1),
                                          date(2001, 12, 1)))

            results = list(annual_editions.last_versions(12, 1000))
            self.assertEqual(results, [
                annual_editions.LastVersionInYear('2222', 2001),
                annual_editions.LastVersionInYear('3333', 2002)])

    @patch('regparser.commands.annual_editions.annual.find_volume')
    def test_last_versions_not_printed(self, find_volume):
        """We should only find the annual editions which have been published
        already"""
        # 2001 exists; no other years do
        find_volume.side_effect = lambda year, title, part: year == 2001
        with self.cli.isolated_filesystem():
            path = entry.Version('12', '1000')
            (path / '1111').write(Version('1111', date(2000, 12, 1),
                                          date(2000, 12, 1)))
            (path / '2222').write(Version('2222', date(2001, 12, 1),
                                          date(2001, 12, 1)))

            results = list(annual_editions.last_versions(12, 1000))
            self.assertEqual(results, [
                annual_editions.LastVersionInYear('1111', 2001)])

    def test_process_if_needed_missing_dependency_error(self):
        """If the annual XML or version isn't present, we should see a
        dependency error."""
        with self.cli.isolated_filesystem():
            last_versions = [annual_editions.LastVersionInYear('1111', 2000)]

            with self.assertRaises(dependency.Missing):
                annual_editions.process_if_needed('12', '1000', last_versions)

            entry.Version('12', '1000', '1111').write(
                Version('1111', date(2000, 1, 1), date(2000, 1, 1)))

            with self.assertRaises(dependency.Missing):
                annual_editions.process_if_needed('12', '1000', last_versions)

    @patch("regparser.commands.annual_editions.xml_parser")
    def test_process_if_needed_missing_writes(self, xml_parser):
        """If output isn't already present, we should process. If it is
        present, we don't need to, unless a dependency has changed."""
        with self.cli.isolated_filesystem():
            build_tree = xml_parser.reg_text.build_tree
            build_tree.return_value = Node()
            last_versions = [annual_editions.LastVersionInYear('1111', 2000)]
            entry.Version('12', '1000', '1111').write(
                Version('1111', date(2000, 1, 1), date(2000, 1, 1)))
            entry.Entry('annual', '12', '1000', 2000).write(
                b'<ROOT></ROOT>')

            annual_editions.process_if_needed('12', '1000', last_versions)
            self.assertTrue(build_tree.called)

            build_tree.reset_mock()
            entry.Entry('tree', '12', '1000', '1111').write(b'tree-here')
            annual_editions.process_if_needed('12', '1000', last_versions)
            self.assertFalse(build_tree.called)

            # Simulate a change to an input file
            os.utime(str(entry.Annual('12', '1000', '2000')),
                     (time() + 1000, time() + 1000))
            annual_editions.process_if_needed('12', '1000', last_versions)
            self.assertTrue(build_tree.called)
