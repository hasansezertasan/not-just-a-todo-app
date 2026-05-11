# Copyright 2024 Hasan Sezer Taşan <hasansezertasan@gmail.com>
"""Service layer.

Pulls data-access and domain operations out of Flask-Admin views so views
stay thin. Each service is a stateless module of functions that takes the
acting user (or just IDs) and returns models.

Why a service layer in a Flask-Admin app:
- Views are decorated routes — hard to unit-test in isolation.
- Service functions are plain Python — testable without an HTTP client.
- Keeps Flask-Admin coupling concentrated in `views/` only.
"""
