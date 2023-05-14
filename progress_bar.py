from events import EventCounter
from tqdm import tqdm


class ProgressBar:
    def __init__(self, interface=None, widget=None):
        """Create new progress bar"""

        self.handler = ProgressBarHandler(self)
        self.interface = interface
        if interface == "cli" and widget is None:
            self.widget = tqdm(range(
                self.handler.event_counter.total_events))
            self.widget_iter = iter(self.widget)
        elif interface == "gui" and widget is not None:
            widget.progress_bar.setValue(0)
            self.widget = widget
        else:
            self.widget = None

    def update(self):
        """Update progress"""

        if self.interface == "cli":
            self.widget.set_description(
                "{:<25}".format(self.handler.event_counter.event.name))
            try:
                next(self.widget_iter)
            except StopIteration:
                pass
            self.widget.refresh()
        elif self.widget is not None:
            self.widget.task.update.emit(
                self.handler.event_counter.get_progress(),
                self.handler.event_counter.event.name)

    def increment(self):
        """Increment Counter"""

        self.handler.event_counter.increment()
        self.update()

    def set_sub_progress(self, progress):
        """Set Progress of sub task"""

        if self.interface == "gui":
            self.handler.event_counter.set_sub_progress(progress)
            self.update()


class ProgressBarHandler:

    def __init__(self, progress_bar: ProgressBar):
        """Initiate new ProgressBar"""

        self.progress_bar = progress_bar
        self.event_counter = EventCounter()

    def increment_event(self):
        """Increment events completed"""

        self.event_counter.increment()
        self.update()

    def update(self):
        """Update progress bar"""
