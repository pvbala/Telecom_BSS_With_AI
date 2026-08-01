"""
In-process pub/sub event bus (Section 4/7 of the design: the "event
backbone", scaled down from Kafka to a single-process signal bus for the
laptop deployment profile).

Every module publishes domain events here (e.g. "customer_created",
"order_placed", "service_provisioned", "invoice_raised", "alarm_raised",
"usage_recorded"). Other modules / the AI event_subscribers / the LLM
narrator can all subscribe without any of them needing to know about
each other directly.
"""
from blinker import signal
import logging

log = logging.getLogger("event_bus")

_signals = {}


def _get_signal(event_name: str):
    if event_name not in _signals:
        _signals[event_name] = signal(event_name)
    return _signals[event_name]


def publish(event_name: str, **payload):
    log.info("EVENT %s: %s", event_name, payload)
    _get_signal(event_name).send(event_name, **payload)


def subscribe(event_name: str, handler):
    _get_signal(event_name).connect(handler, weak=False)
