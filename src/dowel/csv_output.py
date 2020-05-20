"""A `dowel.logger.LogOutput` for CSV files."""
import os
import csv
import warnings

from dowel import TabularInput
from dowel.simple_outputs import FileOutput
from dowel.utils import colorize


class CsvOutput(FileOutput):
    """CSV file output for logger.

    :param file_name: The file this output should log to.
    """

    def __init__(self, file_name):
        super().__init__(file_name)
        self._file_name = file_name
        self._file_sections = [file_name+'_0']
        self._writer = None
        self._fieldnames = None
        self._warned_once = set()
        self._disable_warnings = False

    @property
    def types_accepted(self):
        """Accept TabularInput objects only."""
        return (TabularInput, )

    def record(self, data, prefix=''):
        """Log tabular data to CSV."""
        if isinstance(data, TabularInput):
            to_csv = data.as_primitive_dict

            if not to_csv.keys() and not self._writer:
                return

            if not self._writer:
                self._fieldnames = set(to_csv.keys())
                self._init_writer()
                self._writer.writeheader()

            if to_csv.keys() != self._fieldnames:
                # self._warn('Inconsistent TabularInput keys detected. '
                #            'CsvOutput keys: {}. '
                #            'TabularInput keys: {}. '
                #            'Did you change key sets after your first '
                #            'logger.log(TabularInput)?'.format(
                #                set(self._fieldnames), set(to_csv.keys())))

                # new field appear
                new_fields = set(to_csv.keys()).union(set(self._fieldnames))
                if len(new_fields) > len(self._fieldnames):
                    self._fieldnames = new_fields
                    self._file_sections.append(self._file_name + f'_{len(self._file_sections)}')
                    self._log_file = open(self._file_sections[-1], 'w')
                    self._init_writer()
                    self._writer.writeheader()

            self._writer.writerow(to_csv)

            for k in to_csv.keys():
                data.mark(k)
        else:
            raise ValueError('Unacceptable type.')

    def dump(self, step=None):
        super().dump()
        if len(self._file_sections) > 1:
            self._merge_file_sections()
            self._file_sections = self._file_sections[:1]

    def _merge_file_sections(self):
        if len(self._file_sections) == 1:
            return
        os.rename(self._file_name, self._file_sections[0])
        self._log_file = open(self._file_name, 'w')
        self._init_writer()
        self._writer.writeheader()
        for sec_file_name in self._file_sections:
            with open(sec_file_name)as f:
                reader = csv.DictReader(f)
                for r in reader:
                    self._writer.writerow(r)
            os.remove(sec_file_name)

    def _init_writer(self):
        self._writer = csv.DictWriter(
            self._log_file,
            fieldnames=sorted(list(self._fieldnames)),
            extrasaction='ignore')

    def _warn(self, msg):
        """Warns the user using warnings.warn.

        The stacklevel parameter needs to be 3 to ensure the call to logger.log
        is the one printed.
        """
        if not self._disable_warnings and msg not in self._warned_once:
            warnings.warn(
                colorize(msg, 'yellow'), CsvOutputWarning, stacklevel=3)
        self._warned_once.add(msg)
        return msg

    def disable_warnings(self):
        """Disable logger warnings for testing."""
        self._disable_warnings = True


class CsvOutputWarning(UserWarning):
    """Warning class for CsvOutput."""

    pass
