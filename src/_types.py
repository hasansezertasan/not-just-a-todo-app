import enum


class UserRole(str, enum.Enum):
    BLOCKED = "BLOCKED"
    USER = "USER"
    ADMIN = "ADMIN"
    SUPERUSER = "SUPERUSER"
