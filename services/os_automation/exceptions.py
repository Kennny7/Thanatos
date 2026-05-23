class SafetyCheckRequired(Exception):
    """Raised when an operation requires explicit user confirmation."""
    def __init__(self, window_title: str = ""):
        self.window_title = window_title
        super().__init__(f"Safety check required for window: {window_title!r}. Please confirm the action.")