"""
An observer to upload any new files produced by dumpcap
"""
import os
from concurrent.futures import ThreadPoolExecutor
from watchdog.events import PatternMatchingEventHandler
from watchdog.observers import Observer


class DumpcapObserver:  # pylint: disable=too-many-instance-attributes
    """Dumpcap output observer"""

    def __init__(  # pylint: disable=too-many-arguments
        self, req_session, session_id, mac, ap_analyze_path, path="/tmp/pi_sniffer_data"
    ):

        try:
            os.mkdir(path)
        except OSError:
            print("Creation of the directory %s failed" % path)

        patterns = "*"  # Need this to be the correct pattern for the file.
        ignore_patterns = ""
        ignore_directories = True
        case_sensitive = True
        self.my_event_handler = PatternMatchingEventHandler(
            patterns, ignore_patterns, ignore_directories, case_sensitive
        )

        self.my_event_handler.on_created = self.on_created

        self.path = path
        self.my_observer = Observer()
        self.my_observer.schedule(self.my_event_handler, path)

        self.finished_file = None
        self.req_session = req_session

        self.queue = ThreadPoolExecutor(max_workers=1)
        self.mac = mac
        self.session_id = session_id
        self.ap_analyze_path = ap_analyze_path

    def on_created(self, event):
        """Handle creation of new file"""
        # File created - add name to a temp variable
        # if name in temp variable - push name onto queue
        # put new name in temp variable.
        if self.finished_file is not None:
            self.push_to_queue(self.finished_file)
        self.finished_file = event.src_path

        # print(f"hey, {event.src_path} has been created!")

    @staticmethod
    def on_deleted(event):
        """Handle deletion of a file"""
        # TODO: Might want to keep track of number of created files vs deleted: if created -
        #  deleted > ~100 might want to stop capturing.

    @staticmethod
    def on_modified(event):
        """Handle modification of a file"""

    @staticmethod
    def on_moved(event):
        """Handle move of a file"""
        print(f"ok ok ok, someone moved {event.src_path} to {event.dest_path}")

    def start_observer(self):
        """Begin observation of directory"""
        self.my_observer.start()

    def shutdown_observer(self):
        """Stop observation of directory"""
        self.my_observer.stop()
        self.my_observer.join()

    def push_to_queue(self, finished_file):
        """Enqueue file for upload"""
        self.queue.submit(self.post_data, finished_file)

    def post_data(self, finished_file):
        """Upload file to backend"""
        print("Posting data")
        try:
            response = self.req_session.post(
                self.ap_analyze_path,
                data={
                    "mac": self.mac,
                    "name": finished_file,
                    "session_id": self.session_id,
                },
                files={"data": open(finished_file, "rb")},
            )
            print("Response was: " + str(response))
        except FileNotFoundError as error:
            print("Error: " + str(error))
        # if response.status_code == 200:
        #    os.remove(finished_file)
        # print("Removing file: " + str(finished_file))
        os.remove(finished_file)


if __name__ == "__main__":
    pass
