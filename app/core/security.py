"""Password hashing and related crypto boundaries.

* **Password verification / hashing** for registered users is handled by
  **fastapi-users** (passlib) via :class:`app.core.auth.UserManager`.
* **JWT** issuance and validation strategies are defined in :mod:`app.core.auth`.
"""
