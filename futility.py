import os
import re

'''Futility: the file utility package'''


def get_filename_extension(filename):
    # Modify to alternatively take path object or relative path as str?
    # Do I need to state `else: return None` in docstring?
    '''Gets the file extension from a filename.

    Parameters
    ----------
    filename : str
        A filename (including its extension)

    Returns
    -------
    str
        Returns the file extension (inluding the preceding dot) if the passed
        file has an extension; else returns None.
    '''

    file_extension = re.findall(r'(\.[\w]+)', filename)
    if file_extension:
        return file_extension[-1]


def check_filename(file_to_check, target_folder):
    '''Checks if a file exists in a directory and renames to avoid duplicates.

    Checks if a file exists in a target directory and returns a new file name
    in order to avoid duplicates.

    Parameters
    ----------
    file_to_check : str
        Name of the file to check
    target_folder : str
        Path of the directory in which to check if the file exists

    Returns
    -------
    str
        The filename, which may be renamed with '_n' before the file extension
        if it is found to exist within the target directory.
    '''

    file = file_to_check
    i = 0
    while True:
        if os.path.isfile(f'{target_folder}/{file}'):
            i += 1
            fh, ext = file.split('.', 1)[0], file.split('.', 1)[1]
            fh_trimmed = re.search(r'.*[^(_\d+)$]', fh).group()
            file = f'{fh_trimmed}_{i}.{ext}'
        else:
            break
    return file
