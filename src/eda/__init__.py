"""Endpoint Detection Assurance (EDA).

The project measures a claim defenders usually assume: that their sensors see
the attacks that hit a host. It keeps two questions strictly apart:

- Visibility: did any sensor record a trace of what happened?
- Detection: did a rule fire an alert about it?

An attack can be visible and still undetected. That gap is the whole subject.
"""

__version__ = "0.1.0"
