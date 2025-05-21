import abc
import threading
import sys
import datetime
from threading import get_ident # Import get_ident

class Sink(abc.ABC):
    """Abstract base class for log sinks."""

    def __init__(self):
        """Initializes a lock for the sink."""
        self.lock = threading.Lock()

    @abc.abstractmethod
    def write(self, message_content: str):
        """Writes the message content to the sink.

        Args:
            message_content: The content to write.
        """
        pass

    @abc.abstractmethod
    def format(self, level: str, thread_id: int, message: str) -> str:
        """Formats the log message.

        Args:
            level: The log level (e.g., "INFO", "WARNING").
            thread_id: The ID of the thread generating the log message.
            message: The log message content.

        Returns:
            The formatted log message string.
        """
        pass

class ConsoleSink(Sink):
    """A log sink that writes messages to the console."""

    def write(self, message_content: str):
        """Writes the message content to sys.stdout.

        Args:
            message_content: The content to write.
        """
        self.lock.acquire()
        try:
            sys.stdout.write(message_content + '\n')
            sys.stdout.flush()
        finally:
            self.lock.release()

    def format(self, level: str, thread_id: int, message: str) -> str:
        """Formats the log message for console output.

        Args:
            level: The log level (e.g., "INFO", "WARNING").
            thread_id: The ID of the thread generating the log message.
            message: The log message content.

        Returns:
            The formatted log message string.
        """
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        return f"[{timestamp}] [{level}] [Thread-{thread_id}] {message}"

class FileSink(Sink):
    """A log sink that writes messages to a file."""

    def __init__(self, filename: str):
        """Initializes the FileSink with a filename.

        Args:
            filename: The name of the file to write logs to.
        """
        super().__init__()
        self.filename = filename

    def write(self, message_content: str):
        """Writes the message content to the specified file.

        Args:
            message_content: The content to write.
        """
        self.lock.acquire()
        try:
            with open(self.filename, 'a') as f:
                f.write(message_content + '\n')
        finally:
            self.lock.release()

    def format(self, level: str, thread_id: int, message: str) -> str:
        """Formats the log message for file output.

        Args:
            level: The log level (e.g., "INFO", "WARNING").
            thread_id: The ID of the thread generating the log message.
            message: The log message content.

        Returns:
            The formatted log message string.
        """
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        return f"[{timestamp}] [{level}] [Thread-{thread_id}] {message}"

class SerialSink(Sink):
    """A placeholder log sink that simulates writing to a serial port."""

    def __init__(self, port: str, baudrate: int = 9600):
        """Initializes the SerialSink.

        Args:
            port: The serial port identifier.
            baudrate: The baud rate for serial communication.
        """
        super().__init__()
        self.port = port
        self.baudrate = baudrate
        # Optional: print initialization message
        print(f"SerialSink initialized for port {self.port} at {self.baudrate} baud. (Simulation)")

    def write(self, message_content: str):
        """Simulates writing the message content to a serial port.

        Args:
            message_content: The content to write.
        """
        self.lock.acquire()
        try:
            # Simulate serial write
            print(f"SIMULATED SERIAL WRITE to {self.port}: {message_content}")
        finally:
            self.lock.release()

    def format(self, level: str, thread_id: int, message: str) -> str:
        """Formats the log message for simulated serial output.

        Args:
            level: The log level (e.g., "INFO", "WARNING").
            thread_id: The ID of the thread generating the log message.
            message: The log message content.

        Returns:
            The formatted log message string.
        """
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        return f"[{timestamp}] [{level}] [Thread-{thread_id}] (Serial:{self.port}) {message}"

class Logger:
    """A logger class that distributes log messages to multiple sinks."""

    def __init__(self):
        """Initializes the Logger."""
        self._sinks: list[Sink] = []
        self._sinks_lock = threading.Lock()

    def add_sink(self, sink: Sink):
        """Adds a sink to the logger.

        Args:
            sink: The sink to add. Must be an instance of Sink.

        Raises:
            TypeError: If the sink is not an instance of Sink.
        """
        self._sinks_lock.acquire()
        try:
            if not isinstance(sink, Sink):
                raise TypeError("Provided sink is not an instance of Sink.")
            if sink not in self._sinks:
                self._sinks.append(sink)
        finally:
            self._sinks_lock.release()

    def remove_sink(self, sink: Sink):
        """Removes a sink from the logger.

        Args:
            sink: The sink to remove.
        """
        self._sinks_lock.acquire()
        try:
            if sink in self._sinks:
                self._sinks.remove(sink)
        finally:
            self._sinks_lock.release()

    def log(self, message: str, level: str = "INFO"):
        """Logs a message to all registered sinks.

        Args:
            message: The message to log.
            level: The log level (e.g., "INFO", "DEBUG").
        """
        thread_id = get_ident()
        
        self._sinks_lock.acquire()
        try:
            # Create a copy for thread-safe iteration
            sinks_to_log = list(self._sinks)
        finally:
            self._sinks_lock.release()

        for sink_item in sinks_to_log:
            try:
                formatted_message = sink_item.format(level, thread_id, message)
                sink_item.write(formatted_message)
            except Exception as e:
                # Print error to stderr if a sink fails
                sys.stderr.write(f"Error processing sink {type(sink_item).__name__}: {e}\n")
                sys.stderr.flush()

    def debug(self, message: str):
        """Logs a debug message."""
        self.log(message, level="DEBUG")

    def info(self, message: str):
        """Logs an info message."""
        self.log(message, level="INFO")

    def warning(self, message: str):
        """Logs a warning message."""
        self.log(message, level="WARNING")

    def error(self, message: str):
        """Logs an error message."""
        self.log(message, level="ERROR")
