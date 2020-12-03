from datetime import datetime
import futility
from getpass import getuser
import json
import os
import re
import time
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer


class EventHandler(FileSystemEventHandler):
    '''Watches a directory for changes and performs cleanup of files.

    Watches a directory for changes and performs cleanup of files into
    subfolders. Inherits from watchdog.events.FileSystemEventHandler.
    '''

    def __init__(self, folder_to_track, subfolders, cleanup_function):
        # Modify to handle full path str/path object
        '''Assign the folder to watch, add subfolders, perform initial cleanup.

        Sets the folder to watch for changes, adds subfolders to this folder,
        and perform an execute an initial cleanup of existing files.

        Parameters
        ----------
        folder_to_track : str
            The directory in which to watch for changes.
        subfolders : str or list
            The name(s) of any subdirectory/subdirectories to add in the
            directory passed as `folder_to_track`.
        cleanup_function : func
            The function by which to sort files in `folder_to_track`. Takes one
            argument, `folder_to_track`.
        '''

        self.folder_to_track = folder_to_track
        self.subfolders = make_subdirectories(
                root=folder_to_track,
                subdirs=subfolders
                )

        self.cleanup = cleanup_function
        self.cleanup(root=folder_to_track)

    def on_modified(self, event):
        # Consider what to return; could return value from cleanup function
        '''Clean up files in a target folder when any changes are observed.

        Extended from `watchdog.FileSystemEventHandler.on_modified()`.
        Whenever the target folder is updated: 1) check if the desired
        subfolders still exist in the target folder, and if not re-add them;
        2) execute a function passed to the instance that cleans the directory.

        Parameters
        ----------
        event :

        Returns
        -------
        '''

        dirs_in_cwd = [
                dir for dir in os.listdir(self.folder_to_track)
                if os.path.isdir(dir)
                ]

        if not all(dir in dirs_in_cwd for dir in self.subfolders):
            self.subfolders = make_subdirectories(
                    root=self.folder_to_track,
                    subdirs=self.subfolders
                    )

        self.cleanup(root=self.folder_to_track)
        return True


def make_subdirectories(root, subdirs):
    # Modify to handle full path str/path object
    '''Make subfolders within an existing folder.

    Parameters
    ----------
    root : str
        Path to the directory in which to create subdirectories.
    subdirs : str or list
        Name(s) of the subdirectory/subdirectories to create.

    Returns
    -------
    '''

    if isinstance(subdirs, str):
        subdirs = [subdirs]
    for subdir in subdirs:
        destination = root + '/' + subdir
        if not os.path.isdir(destination):
            os.mkdir(destination)
    return subdirs


def sort_by_filetype(root):
    '''Sorts files in a given directory based on file type.

    Sorts files into subfolders based on file extension. The file type for each
    extension assigned in `futility.extensions`.

    Parameters
    ----------
    root : str
        Path to the directory in which to sort files.
    extensions: dict
        A dictionary of file extensions and associated file type.

    Returns
    -------
    '''
    with open('file_extensions.json') as fh:
        extensions = json.load(fh)

    for file in os.listdir(root):
        if os.path.isfile(f'{root}/{file}'):
            file_extension = futility.get_filename_extension(filename=file)

            try:
                file_type = extensions[file_extension]
            except KeyError:
                # Either no ext or not known extension; don't move to subfolder
                pass
            else:
                if file_type != 'Other':
                    file_name_checked = futility.check_filename(
                            file_to_check=file,
                            target_folder=f'{root}/{file_type}')
                    # I'd like to change this to optionally take a destination
                    # I.e. perform the check within the CWD

                    source = f'{root}/{file}'
                    destination = f'{root}/{file_type}/{file_name_checked}'

                    os.rename(source, destination)


def sort_screenshots(root):
    '''Sorts files in a given directory if it is a screenshot/screen recording.

    Checks if files in a given directory are apple screenshots/screen
    recordings, and if so moves them to a subdirectoy named 'Screenshots'.

    Returns
    -------
    '''

    apple_screengrab_filename = re.compile(
            r'(Screenshot|Screen\sRecording)\s(\d+-*)+\sat\s((\d+\.){2}\d+)'
            r'(\s\(\d\))*(\.(mov|png))'
            )

    for file in os.listdir(root):
        match_filename = apple_screengrab_filename.search(file)

        # Check that the item is a file (not a dir) and matches as screengrab:
        if os.path.isfile(f'{root}/{file}') and match_filename:
            datetime_now = datetime.now().strftime("%d-%m-%Y_%H-%M-%S")
            extension = futility.get_filename_extension(filename=file)
            new_filename = f'Screengrab_{datetime_now}_captured{extension}'
            # If this new filename is in destination, rename
            file_name_checked = futility.check_filename(
                    file_to_check=new_filename,
                    target_folder=f'{root}/Screenshots')

            source = f'{root}/{file}'
            destination = f'{root}/Screenshots/{file_name_checked}'

            os.rename(source, destination)


def main():
    def clean_dir(root, subfolders, cleanup_function):
        event_handler = EventHandler(
                folder_to_track=root,
                subfolders=subfolders,
                cleanup_function=cleanup_function
                )
        observer = Observer()
        observer.schedule(
                event_handler=event_handler,
                path=root,
                recursive=True
                )
        observer.start()
        return observer

    user = getuser()

    with open('file_extensions.json') as fh:
        extensions = json.load(fh)

    config_args = {
            'Downloads': {
                'Root': f'/Users/{user}/Downloads',
                'Subfolders': [
                    f for f in set(extensions.values()) if f != 'Other'
                    ],
                'Cleanup Function': sort_by_filetype
            },
            'Screenshots': {
                'Root': f'/Users/{user}/Desktop',
                'Subfolders': 'Screenshots',
                'Cleanup Function': sort_screenshots
            }
        }

    observer_downloads = clean_dir(
            *[param for param in config_args['Downloads'].values()]
            )
    observer_screenshots = clean_dir(
            *[param for param in config_args['Screenshots'].values()]
            )

    try:
        while True:
            time.sleep(10)
    except KeyboardInterrupt:
        observer_downloads.stop()
        observer_screenshots.stop()
    observer_downloads.join()
    observer_screenshots.join()


if __name__ == '__main__':
    main()
