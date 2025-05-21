import unittest
import threading
import os
import time
import sys
import re # For checking log format
from datetime import datetime # For checking timestamp format

# Assuming logger.py is in the same directory or in PYTHONPATH
from logger import Logger, ConsoleSink, FileSink, Sink

# Log file names
BASIC_LOG_FILE = "test_basic.log"
MANAGEMENT_LOG_FILE = "test_management.log"
THREADED_LOG_FILE = "test_threaded.log"

# Regex to check the basic structure of a log line
# [YYYY-MM-DD HH:MM:SS.mmm] [LEVEL] [Thread-ID] Message
LOG_LINE_REGEX = re.compile(r"^\[\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3}\] \[\w+\] \[Thread-\d+\] .*")

class TestBasicLogging(unittest.TestCase):
    def setUp(self):
        self.logger = Logger()
        self.console_sink = ConsoleSink()
        self.file_sink = FileSink(BASIC_LOG_FILE)
        self.logger.add_sink(self.console_sink)
        self.logger.add_sink(self.file_sink)
        # Give a tiny moment for file sink to be ready if needed, though FileSink opens/closes on write
        time.sleep(0.01)


    def tearDown(self):
        # Try to remove sinks from logger - good practice although logger might be new each time
        self.logger.remove_sink(self.console_sink)
        self.logger.remove_sink(self.file_sink)
        if os.path.exists(BASIC_LOG_FILE):
            os.remove(BASIC_LOG_FILE)

    def test_simple_log_to_console_and_file(self):
        print("\nRunning test_simple_log_to_console_and_file (manual check for console output)")
        messages_to_log = {
            "INFO": "This is an info message.",
            "WARNING": "This is a warning message.",
            "ERROR": "This is an error message.",
            "DEBUG": "This is a debug message."
        }

        self.logger.info(messages_to_log["INFO"])
        self.logger.warning(messages_to_log["WARNING"])
        self.logger.error(messages_to_log["ERROR"])
        self.logger.debug(messages_to_log["DEBUG"])
        
        # Wait a bit for logs to be written, especially for file sink
        time.sleep(0.1) 

        self.assertTrue(os.path.exists(BASIC_LOG_FILE))
        with open(BASIC_LOG_FILE, 'r') as f:
            lines = f.readlines()

        self.assertEqual(len(lines), len(messages_to_log), "Number of logged messages mismatch")

        current_thread_id = threading.get_ident()
        for i, (level, msg_content) in enumerate(messages_to_log.items()):
            line = lines[i].strip()
            self.assertTrue(LOG_LINE_REGEX.match(line), f"Log line format incorrect: {line}")
            self.assertIn(f"[{level}]", line)
            self.assertIn(f"[Thread-{current_thread_id}]", line)
            self.assertIn(msg_content, line)
        print("Console output for test_simple_log_to_console_and_file should have shown 4 messages.")

class TestSinkManagement(unittest.TestCase):
    def setUp(self):
        self.logger = Logger()
        self.console_sink = ConsoleSink()
        self.file_sink = FileSink(MANAGEMENT_LOG_FILE)
        # Sinks are not added by default in this test's setup

    def tearDown(self):
        # Attempt to remove sinks if they were added
        try:
            self.logger.remove_sink(self.console_sink)
        except ValueError: # Sink might not have been in list
            pass
        try:
            self.logger.remove_sink(self.file_sink)
        except ValueError:
            pass
        if os.path.exists(MANAGEMENT_LOG_FILE):
            os.remove(MANAGEMENT_LOG_FILE)

    def test_add_remove_sinks(self):
        print("\nRunning test_add_remove_sinks (manual check for console output)")
        msg1 = "Message 1 (no sinks)"
        msg2 = "Message 2 (console sink only)"
        msg3 = "Message 3 (console and file sink)"
        msg4 = "Message 4 (file sink only)"
        msg5 = "Message 5 (no sinks again)"

        self.logger.info(msg1) # Should go nowhere
        time.sleep(0.05)
        self.assertFalse(os.path.exists(MANAGEMENT_LOG_FILE), "Log file should not exist yet")
        print(f"Console should NOT show: {msg1}")

        self.logger.add_sink(self.console_sink)
        self.logger.info(msg2) # Should go to console
        time.sleep(0.05)
        self.assertFalse(os.path.exists(MANAGEMENT_LOG_FILE), "Log file should still not exist")
        print(f"Console SHOULD show: {msg2}")

        self.logger.add_sink(self.file_sink)
        self.logger.info(msg3) # Should go to console and file
        time.sleep(0.05)
        self.assertTrue(os.path.exists(MANAGEMENT_LOG_FILE))
        print(f"Console SHOULD show: {msg3}")
        with open(MANAGEMENT_LOG_FILE, 'r') as f:
            lines = f.readlines()
        self.assertEqual(len(lines), 1)
        self.assertTrue(LOG_LINE_REGEX.match(lines[0].strip()))
        self.assertIn(msg3, lines[0])

        self.logger.remove_sink(self.console_sink)
        self.logger.info(msg4) # Should go to file only
        time.sleep(0.05)
        print(f"Console should NOT show: {msg4}")
        with open(MANAGEMENT_LOG_FILE, 'r') as f:
            lines = f.readlines()
        self.assertEqual(len(lines), 2)
        self.assertTrue(LOG_LINE_REGEX.match(lines[0].strip()))
        self.assertIn(msg3, lines[0])
        self.assertTrue(LOG_LINE_REGEX.match(lines[1].strip()))
        self.assertIn(msg4, lines[1])
        
        self.logger.remove_sink(self.file_sink)
        self.logger.info(msg5) # Should go nowhere
        time.sleep(0.05)
        print(f"Console should NOT show: {msg5}")
        with open(MANAGEMENT_LOG_FILE, 'r') as f:
            lines = f.readlines()
        # Content should be the same as before msg5
        self.assertEqual(len(lines), 2, "Message 5 should not have been written to file")


    def test_add_invalid_sink(self):
        with self.assertRaises(TypeError):
            self.logger.add_sink("not a sink object")

class TestThreadSafety(unittest.TestCase):
    NUM_THREADS = 50
    MESSAGES_PER_THREAD = 100

    def setUp(self):
        self.logger = Logger()
        self.file_sink = FileSink(THREADED_LOG_FILE)
        self.logger.add_sink(self.file_sink)
        time.sleep(0.01) # Ensure sink is ready

    def tearDown(self):
        self.logger.remove_sink(self.file_sink)
        if os.path.exists(THREADED_LOG_FILE):
            os.remove(THREADED_LOG_FILE)

    def log_messages_thread_function(self, logger_instance, thread_id_num, num_messages):
        for i in range(num_messages):
            logger_instance.info(f"Thread {thread_id_num} logging message {i}")
            # time.sleep(0.0001) # Optional small delay

    def test_concurrent_logging(self):
        print(f"\nRunning test_concurrent_logging with {self.NUM_THREADS} threads and {self.MESSAGES_PER_THREAD} messages each.")
        threads = []
        for i in range(self.NUM_THREADS):
            thread = threading.Thread(target=self.log_messages_thread_function, 
                                      args=(self.logger, i, self.MESSAGES_PER_THREAD))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()
        
        # Allow a bit more time for all writes to complete to the OS buffer and then to disk
        time.sleep(0.5)


        self.assertTrue(os.path.exists(THREADED_LOG_FILE))
        with open(THREADED_LOG_FILE, 'r') as f:
            lines = f.readlines()

        expected_lines = self.NUM_THREADS * self.MESSAGES_PER_THREAD
        self.assertEqual(len(lines), expected_lines, "Number of logged messages in threaded test mismatch")

        # Optional: Check for line integrity
        # This is a basic check. More sophisticated checks might look for message interleaving.
        for i, line in enumerate(lines):
            line = line.strip()
            self.assertTrue(LOG_LINE_REGEX.match(line), f"Log line {i+1} format incorrect: {line}")
            # Verify it's not an empty line that somehow got written
            self.assertTrue(len(line) > 0, f"Log line {i+1} is empty.")
        
        print(f"Threaded logging test completed. {expected_lines} lines written to {THREADED_LOG_FILE}.")


if __name__ == '__main__':
    unittest.main()
