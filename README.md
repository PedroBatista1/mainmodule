# Thread-Safe Logger

A flexible and thread-safe logging utility implemented in Python.

## Features

-   **Thread-Safe**: Designed for use in multi-threaded applications. Each sink handles its own locking.
-   **Multiple Sinks**: Log messages to various outputs simultaneously (e.g., console, file).
-   **Customizable Sinks**: Easily extendable by creating new sink classes inheriting from `Sink`.
-   **Configurable Formatting**: Each sink can define its own message format.
-   **Standard Log Levels**: Supports common log levels (DEBUG, INFO, WARNING, ERROR).

## Requirements

-   Python 3.6+ (due to f-strings and `datetime` usage, threading module)

## Files

-   `logger.py`: Contains the `Logger` class and sink implementations (`ConsoleSink`, `FileSink`, `SerialSink` placeholder).
-   `test_logger.py`: Contains unit tests for the logger.

## How to Use

### 1. Import Classes
```python
from logger import Logger, ConsoleSink, FileSink, SerialSink
```

### 2. Initialize the Logger
```python
logger = Logger()
```

### 3. Create and Add Sinks
```python
# Console Sink
console_sink = ConsoleSink()
logger.add_sink(console_sink)

# File Sink
# Log messages will be appended to 'app.log'
file_sink = FileSink("app.log")
logger.add_sink(file_sink)

# (Optional) Serial Sink Placeholder
# serial_sink = SerialSink(port="/dev/ttyUSB0", baudrate=115200)
# logger.add_sink(serial_sink)
```

### 4. Log Messages
```python
logger.info("This is an informational message.")
logger.warning("This is a warning message.")
logger.error("This is an error message.")
logger.debug("This is a debug message (often for developers).")

# Example in a threaded environment
import threading

def worker_function(worker_id):
    for i in range(5):
        logger.info(f"Message from worker {worker_id}: {i}")
        # time.sleep(0.01) # Simulate some work

threads = []
for i in range(3): # Create 3 worker threads
    thread = threading.Thread(target=worker_function, args=(i,))
    threads.append(thread)
    thread.start()

for thread in threads:
    thread.join()
```

### 5. Removing Sinks (Optional)
```python
# logger.remove_sink(console_sink)
# logger.info("This message will only go to file_sink (and serial_sink if added).")
```

## Creating Custom Sinks

To create a new sink, inherit from the `Sink` base class and implement the `write` and `format` methods:

```python
from logger import Sink, get_ident # get_ident for thread_id
import datetime # For timestamp

class CustomSink(Sink):
    def __init__(self, custom_param):
        super().__init__() # Important: Initializes the lock
        self.custom_param = custom_param
        # Initialize any resources for your sink

    def format(self, level: str, thread_id: int, message: str) -> str:
        # Implement your custom formatting logic
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        return f"[{timestamp}] [{level.upper()}] [Thread-{thread_id}] (Custom: {self.custom_param}) {message}"

    def write(self, message_content: str):
        self.lock.acquire()
        try:
            # Implement your writing logic (e.g., send to network, database, etc.)
            print(f"CUSTOM_SINK_OUTPUT: {message_content}")
            # Example: with open("custom_log.txt", "a") as f:
            # f.write(message_content + "\n")
        finally:
            self.lock.release()

# Usage:
# custom_sink_instance = CustomSink(custom_param="my_value")
# logger.add_sink(custom_sink_instance)
# logger.info("This message will also go to the custom sink.")
```

## Running Tests
```bash
python -m unittest test_logger.py
```
