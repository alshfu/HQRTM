"""Async-poller: HomeQ-bevakning → FCFS-detektering → matchning → kö av aviseringar.

Separat långlivad process (inte inuti Flask). Kommunikation med web — via MongoDB.
"""
