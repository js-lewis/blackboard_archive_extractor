#!/usr/bin/env python3
"""Module docstring"""


import glob
import os
import re
import sys
from zipfile import ZipFile


def _str_dist(string1, string2):
    """Taken from:
    https://en.wikibooks.org/wiki/Algorithm_Implementation/Strings/
        Levenshtein_distance#Python"""
    if len(string1) < len(string2):
        string1, string2 = string2, string1

    if len(string2) == 0:
        return len(string1)

    previous_row = range(len(string2) + 1)
    for i, char1 in enumerate(string1):
        current_row = [i + 1]
        for j, char2 in enumerate(string2):
            # j+1 instead of j since previous_row and current_row are one
            #     character longer
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1  # than string2
            substitutions = previous_row[j] + (char1 != char2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row

    return previous_row[-1]


class BlackboardArchiveExtractor:
    """
    Use get_submissions to extract a dictionary of the form
      submissions[username] : {archive:<val>, sub_date<val>)}
    from default path of ./ and filter of *.zip.

    The extract_files method will call unzip with the -d option
    defaulted to "./"
    """
    #  default Blackboard submission download naming format
    __REGEX = "[^_]+_" # skip anything other than _ until first _
    __REGEX += "([a-z]+[0-9]*)" # username group
    __USERNAME_GROUP = 1
    __REGEX += "_.+_" # skip _<anything>_
    __REGEX += "([0-9]{4}-[0-9]{2}-[0-9]{2})" # date group
    __SUB_DATE_GROUP = 2
    __REGEX += "-.*" # skip rest of name


    def __init__(self, target: str = "./"):
        self._submissions = dict()
        self._target = target


    def get_submissions(self, path="", file_filter="*.zip"):
        """Method docstring"""
        # compile regex for fname parsing
        dfa = re.compile(BlackboardArchiveExtractor.__REGEX)

        for fname in glob.glob(path + file_filter):  # get list of files
            matches = dfa.match(fname)  # parse name
            assert matches.lastindex == 2  # sanity check

            # store zip archive fname and submission date with username key
            self._submissions[
                matches.group(BlackboardArchiveExtractor.__USERNAME_GROUP)
            ] = {
                "archive" : fname,
                "sub_date" : matches.group(
                    BlackboardArchiveExtractor.__SUB_DATE_GROUP)
            }

        return self._submissions


    def extract_files(
            self, archive, expected, exact=False, pre=""):
        """
        Extracts files from archive into target directory
        - parameters:
          - archive: path and name of zip archive
          - expected: expected path and name of target file in archive
          - target: target path to where extracted file should be created
          - exact: whether method should use fuzzy logic
          - pre: a prefix added to extracted file, useful when extracting
                 copies of a file from multiple sources.

        - returns: true if path is exactly correct, false otherwise
        """
        with ZipFile(archive, 'r') as zipfile:  # open zip archive
            best_path = None
            best_dist = sys.float_info.max
            fname = os.path.basename(expected)

            target_path = os.path.join(self._target, pre + fname)
            if os.path.exists(target_path):
                os.remove(target_path)

            for name in zipfile.namelist():  # find file in the archive
                if "test" in name:  # TODO: change to exclude
                    continue        #     directories (this is a hack)

                if name.endswith(fname):  # when found, extract
                    if name == expected:  # when looking for exact path
                        extracted_file = zipfile.read(name)
                        with open(target_path, 'w') as target_file:
                            target_file.write(extracted_file.decode('utf-8'))
                        return True, expected

                    if not exact:  # calc shortest Levenshtein dist
                        tmp_dist = _str_dist(expected, name)
                        if tmp_dist < best_dist:
                            best_dist = tmp_dist
                            best_path = name

            if not exact:
                if not best_path:
                    raise FileNotFoundError(
                        fname + " not found in " + archive)

                str_file = zipfile.read(best_path)
                fname = pre + fname
                with open(os.path.join(self._target, fname),
                          'w') as target_file:
                    target_file.write(str_file.decode('utf-8'))

            return False, best_path

        assert False # sanity check when archive is incorrect
        return False



    def extract_into_dir(self, files: list, path=""):
        """method docstring"""
        archives = self.get_submissions(path)
        for username in archives:
            for fname in files:
                try:
                    self.extract_files(
                        archives[username]['archive'], fname, False,
                        f"{username}_")
                except FileNotFoundError as error:
                    print(error)


def main():
    """Function docstring"""
    usage = """proc_name <make_dir> <file_path> <file0>, ... <file_n>"""

    if len(sys.argv) < 4:
        print(usage)
        return

    extractor = BlackboardArchiveExtractor(sys.argv[1])
    extractor.extract_into_dir(sys.argv[3:len(sys.argv)], sys.argv[2])


if __name__ == "__main__":
    main()
