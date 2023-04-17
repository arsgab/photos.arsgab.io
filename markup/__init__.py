from contextvars import ContextVar

from jinja2 import Environment

renderer_ref: ContextVar[Environment] = ContextVar('renderer')
