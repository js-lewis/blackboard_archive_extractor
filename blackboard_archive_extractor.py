#!/usr/bin/env python3

import glob
import os
import re
import subprocess
import sys
from zipfile import ZipFile

"""
Use get_submissions to extract a dictionary of the form
  submissions[username] : {archive:<val>, sub_date<val>)}
from default path of ./ and filter of *.zip.

The extract_files method will call unzip with the -d option defaulted to "./"
"""
class SubmissionExtractor(object):
    def __init__(self):
        self.submissions = dict()
        #  default Blackboard submission download naming format
        self.__regex = "[^_]+_" # skip anything other than _ until first _
        self.__regex += "([a-z]+[0-9]*)" # username group
        self.__username_group = 1
        self.__regex += "_.+_" # skip _<anything>_
        self.__regex += "([0-9]{4}-[0-9]{2}-[0-9]{2})" # date group
        self.__sub_date_group = 2
        self.__regex += "-.*" # skip rest of name


    def get_submissions(self, path="", file_filter="*.zip"):
        dfa = re.compile(self.__regex)  # compile regex for fname parsing

        for fname in glob.glob(path + file_filter):  # get list of files
          matches = dfa.match(fname)  # parse name
          assert(matches.lastindex == 2)  # sanity check
    
          # store zip archive fname and submission date with username key
          self.submissions[matches.group(self.__username_group)] = { \
            "archive" : fname, \
            "sub_date" : matches.group(self.__sub_date_group)
          }
    
        return self.submissions


    def extract_files(
            self, archive, expected, target="./", exact=False, pre=""):
        """
        Extracts files from archive into target directory
        - parameters:
          - archive: path and name of zip archive
          - expected: expected path and name of target file in archive
          - target: target path to where extracted file should be created
          - exact: whether method should use fuzzy logic
      
        - returns: true if path is exactly correct, false otherwise
        """
        with ZipFile(archive, 'r') as zipfile:  # open zip archive
          best_path = None
          best_dist = sys.float_info.max
          fname = os.path.basename(expected)

          target_path = os.path.join(target, fname)
          if os.path.exists(target_path):
              os.remove(target_path)

          for name in zipfile.namelist():  # find file in the archive
            if "test" in name:
              continue
            if name.endswith(fname):  # when found, extract as directed
              if name == expected:  # when looking for exact path
                str_file = zipfile.read(name)
                if pre:
                  fname = pre + fname
                with open(target_path, 'w') as tar_file:
                  tar_file.write(str_file.decode('utf-8'))
                  
                return True, expected

              elif not exact:  # using fuzzy logic
                tmp_dist = self.__str_dist(expected, name)  # diffence in names 
                if tmp_dist < best_dist:  # update distance shorter is found
                  best_dist = tmp_dist
                  best_path = name

          if not exact:
            if best_path is not None:
              str_file = zipfile.read(best_path)
              fname = pre + fname
              with open(os.path.join(target, fname), 'w') as tar_file:
                tar_file.write(str_file.decode('utf-8'))
            else:
              raise FileNotFoundError(fname + " not found in " + archive)

          return False, best_path

        assert(False) # sanity check when archive is incorrect
        return False


    def __str_dist(self, s1, s2):
        '''
        Taken from:
            https://en.wikibooks.org/wiki/Algorithm_Implementation/Strings/
                Levenshtein_distance#Python
        '''
        if len(s1) < len(s2):
            return self.__str_dist(s2, s1)
        if len(s2) == 0:
            return len(s1)

        previous_row = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                # j+1 instead of j since previous_row and current_row are one
                #     character longer
                insertions = previous_row[j + 1] + 1 
                deletions = current_row[j] + 1  # than s2
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row

        return previous_row[-1]


    def extract_into_dir(self, files: list, make_dir: str="", path=""):
        if make_dir:
            os.makedirs(make_dir)  # make any parent and leaf dirs

        archives = self.get_submissions(path)
        for username in archives:
            for fname in files:
                try:
                    self.extract_files(
                        archives[username]['archive'], fname, make_dir, False,
                        f"{username}_")
                except Exception as exc:
                    print(exc)


def main():
  extractor = SubEx()

  if len(sys.argv) < 4:
    print("""proc_name <make_dir> <file_path> <file1>, <file2>, ... <file_n>""")
    return

  i = 3
  file_names = []
  while i < len(sys.argv):
      file_names.append(sys.argv[i])
      i += 1

  extractor.extract_into_dir(
      sys.argv[3:len(sys.argv)], sys.argv[1], sys.argv[2])


if __name__ == "__main__":
  main()
