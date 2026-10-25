from contextlib import redirect_stdout
from io import StringIO
from unittest.mock import patch

from django.test import SimpleTestCase

from hs_tracking.management.commands.stats import Command


class StatsCommandTests(SimpleTestCase):
    def test_detail_exports_have_no_lookback_warning(self):
        for option, method in (
            ('--resources-details', 'resources_details'),
            ('--users-details', 'users_details'),
        ):
            with self.subTest(option=option):
                command = Command()
                parser = command.create_parser('manage.py', 'stats')
                options = vars(parser.parse_args([option]))
                output = StringIO()
                errors = StringIO()
                command.stderr = errors
                with patch.object(command, method) as export, redirect_stdout(output):
                    export.side_effect = lambda **kwargs: print('csv-header')
                    command.handle(**options)
                self.assertEqual(output.getvalue(), 'csv-header\n')
                self.assertEqual(errors.getvalue(), '')

    def test_lookback_is_preserved_when_date_options_are_present(self):
        command = Command()
        parser = command.create_parser('manage.py', 'stats')
        options = vars(parser.parse_args([
            '--yesterdays-variables', '--start-date', '2026-10-01', '7',
        ]))
        output = StringIO()
        with patch.object(command, 'yesterdays_variables') as report, redirect_stdout(output):
            command.handle(**options)
        report.assert_called_once_with(lookback=7)
        self.assertEqual(output.getvalue(), '')
