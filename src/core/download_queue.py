from gi.repository import GLib

class DownloadQueue:
    """
    FIFO download queue with configurable concurrency.
    Manages the lifecycle of book download + install jobs, allowing
    multiple books to be queued and started automatically as slots open.
    """

    def __init__(self, max_concurrent=2):
        self.max_concurrent = max_concurrent
        self._pending = []       # list of (book, local_path) in FIFO order
        self._active_ids = set() # book_ids currently downloading
        
        # Callbacks replacing pyqtSignal
        self.on_job_started = None    # func(book_id)
        self.on_job_finished = None   # func(book_id)
        self.on_queue_changed = None  # func(pending_count)

    def _emit_started(self, book_id):
        if self.on_job_started:
            GLib.idle_add(self.on_job_started, book_id)

    def _emit_finished(self, book_id):
        if self.on_job_finished:
            GLib.idle_add(self.on_job_finished, book_id)

    def _emit_changed(self):
        if self.on_queue_changed:
            GLib.idle_add(self.on_queue_changed, len(self._pending))

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def enqueue(self, book, local_path):
        """
        Add a download job to the queue.
        Returns True if enqueued, False if already queued or active.
        """
        book_id = book['id']
        if self.is_queued(book_id) or self.is_active(book_id):
            return False
        self._pending.append((book, local_path))
        self._emit_changed()
        self._try_start_next()
        return True

    def dequeue(self, book_id):
        """Remove a pending job from the queue (does not cancel active downloads)."""
        before = len(self._pending)
        self._pending = [(b, p) for (b, p) in self._pending if b['id'] != book_id]
        if len(self._pending) != before:
            self._emit_changed()

    def is_queued(self, book_id):
        """Returns True if the book is waiting in the pending queue."""
        return any(b['id'] == book_id for (b, _) in self._pending)

    def is_active(self, book_id):
        """Returns True if the book is currently downloading."""
        return book_id in self._active_ids

    def pending_count(self):
        """Number of jobs waiting to start."""
        return len(self._pending)

    def total_count(self):
        """Total jobs: pending + currently active."""
        return len(self._pending) + len(self._active_ids)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def on_download_started(self, book_id):
        """Called by MainWindow when a download worker actually starts."""
        self._active_ids.add(book_id)

    def on_download_completed(self, book_id):
        """
        Called by MainWindow when a download finishes (success or error).
        Frees the slot and starts the next job.
        """
        self._active_ids.discard(book_id)
        self._emit_finished(book_id)
        self._try_start_next()

    def _try_start_next(self):
        """Start as many pending jobs as allowed by max_concurrent."""
        while self._pending and len(self._active_ids) < self.max_concurrent:
            book, local_path = self._pending.pop(0)
            self._emit_changed()
            
            # Store the args so MainWindow can retrieve them before emitting the signal
            self._last_started = (book, local_path)
            
            self._emit_started(book['id'])
