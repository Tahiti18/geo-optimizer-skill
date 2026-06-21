"""Thin adapters over the open-source ``geo_optimizer`` engine.

This is the ONLY place the platform touches the engine. The engine is frozen;
these adapters call its public functions and translate dataclasses into
platform-friendly, JSON-safe payloads. No engine code is modified.
"""
