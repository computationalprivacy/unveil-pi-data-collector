"""
Tests for dumpcap observer
"""
import os
import tempfile
from os import write
from time import sleep
from unittest.mock import MagicMock, patch, ANY, call

from src.dumpcap_observer import DumpcapObserver


def test_data_posted_when_new_file_created():
    mock_session = MagicMock()
    with tempfile.TemporaryDirectory() as tempdir:
        with patch("src.dumpcap_observer.os.mkdir"):
            observer = DumpcapObserver(
                mock_session,
                0,
                "MY MAC",
                "http://localhost:8000/ap/analyze",
                path=tempdir,
            )
            observer.start_observer()

            file1 = open(tempdir + "/file1", "w+")
            file1.write("Data1\n")
            file1.close()
            mock_session.post.assert_not_called()

            file2 = open(tempdir + "/file2", "w+")
            file2.write("Data2\n")
            file2.close()

            sleep(1)  # Sleep 1 second to ensure thread executes
            mock_session.post.assert_called_once()

            file3 = open(tempdir + "/file3", "w+")
            file3.write("Data3\n")
            file3.close()

            sleep(1)  # Sleep 1 second to ensure thread executes
            mock_session.post.assert_has_calls(
                [
                    call(
                        "http://localhost:8000/ap/analyze",
                        data={
                            "mac": "MY MAC",
                            "name": file1.name,
                            "session_id": 0,
                        },
                        files={"data": ANY},
                    ),
                    call(
                        "http://localhost:8000/ap/analyze",
                        data={
                            "mac": "MY MAC",
                            "name": file2.name,
                            "session_id": 0,
                        },
                        files={"data": ANY},
                    ),
                ]
            )
