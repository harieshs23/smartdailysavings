from __future__ import annotations

import hashlib
import secrets
import uuid
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import text

from app.db import SessionLocal


def generate_verification_token() -> str:
    """Generate a secure random token for email verification."""
    return secrets.token_urlsafe(32)


def create_verification_token(neon_user_id: str, email: str) -> dict[str, Any]:
    """Create a verification token for a user's email."""
    token = generate_verification_token()
    expires_at = datetime.utcnow() + timedelta(hours=24)

    with SessionLocal() as db:
        # Delete any existing verification tokens for this user
        db.execute(
            text(
                """
                DELETE FROM neon_auth.email_verification
                WHERE "userId" = :user_id
                """
            ),
            {"user_id": neon_user_id},
        )

        token_id = str(uuid.uuid4())
        db.execute(
            text(
                """
                INSERT INTO neon_auth.email_verification (
                    id, token, "userId", email, "expiresAt", "createdAt", "updatedAt"
                )
                VALUES (:id, :token, :user_id, :email, :expires_at, NOW(), NOW())
                """
            ),
            {
                "id": token_id,
                "token": token,
                "user_id": neon_user_id,
                "email": email,
                "expires_at": expires_at,
            },
        )
        db.commit()

    return {
        "token": token,
        "expiresAt": expires_at.isoformat(),
        "userId": neon_user_id,
        "email": email,
    }


def verify_email_token(token: str) -> dict[str, Any] | None:
    """Verify an email verification token and mark the user as verified."""
    with SessionLocal() as db:
        row = db.execute(
            text(
                """
                SELECT v."userId", v.email, v."expiresAt", u."emailVerified"
                FROM neon_auth.email_verification v
                JOIN neon_auth."user" u ON u.id = v."userId"
                WHERE v.token = :token
                LIMIT 1
                """
            ),
            {"token": token},
        ).first()

        if row is None:
            return None

        user_id, email, expires_at, already_verified = row[0], row[1], row[2], bool(row[3])

        if datetime.utcnow() > expires_at:
            # Token expired - delete it
            db.execute(
                text("DELETE FROM neon_auth.email_verification WHERE token = :token"),
                {"token": token},
            )
            db.commit()
            return None

        # Mark user as verified
        db.execute(
            text(
                """
                UPDATE neon_auth."user"
                SET "emailVerified" = TRUE, "updatedAt" = NOW()
                WHERE id = :user_id
                """
            ),
            {"user_id": user_id},
        )

        # Delete the used token
        db.execute(
            text("DELETE FROM neon_auth.email_verification WHERE token = :token"),
            {"token": token},
        )

        db.commit()

        return {
            "userId": str(user_id),
            "email": email,
            "verified": True,
        }

    return None


def resend_verification_email(neon_user_id: str, email: str) -> dict[str, Any]:
    """Resend verification email by creating a new token."""
    return create_verification_token(neon_user_id, email)


def ensure_neon_user(email: str, name: str | None = None) -> str:
    with SessionLocal() as db:
        existing = db.execute(
            text(
                'SELECT id FROM neon_auth."user" WHERE LOWER(email) = LOWER(:email) LIMIT 1'
            ),
            {"email": email},
        ).scalar_one_or_none()
        if existing:
            return str(existing)

        neon_user_id = str(uuid.uuid4())
        db.execute(
            text(
                """
                INSERT INTO neon_auth."user" (
                    id,
                    email,
                    name,
                    "emailVerified",
                    role,
                    "createdAt",
                    "updatedAt"
                )
                VALUES (:id, :email, :name, FALSE, 'user', NOW(), NOW())
                """
            ),
            {
                "id": neon_user_id,
                "email": email,
                "name": name or email,
            },
        )
        db.commit()
        return neon_user_id


def create_email_password_account(email: str, password: str, name: str | None = None) -> dict[str, Any]:
    neon_user_id = ensure_neon_user(email, name=name)

    password_hash = hashlib.sha256(password.encode("utf-8")).hexdigest()

    with SessionLocal() as db:
        existing = db.execute(
            text(
                """
                SELECT id, "userId", "accountId"
                FROM neon_auth.account
                WHERE "providerId" = 'email-password' AND LOWER("accountId") = LOWER(:account_id)
                LIMIT 1
                """
            ),
            {"account_id": email},
        ).first()

        if existing is None:
            account_id = str(uuid.uuid4())
            db.execute(
                text(
                    """
                    INSERT INTO neon_auth.account (
                        id,
                        "accountId",
                        "providerId",
                        "userId",
                        password,
                        "createdAt",
                        "updatedAt"
                    )
                    VALUES (:id, :account_id, 'email-password', :user_id, :password_hash, NOW(), NOW())
                    """
                ),
                {
                    "id": account_id,
                    "account_id": email,
                    "user_id": neon_user_id,
                    "password_hash": password_hash,
                },
            )
            db.commit()

        user_row = db.execute(
            text(
                'SELECT id, email, name, role, "emailVerified" FROM neon_auth."user" WHERE id = :user_id LIMIT 1'
            ),
            {"user_id": neon_user_id},
        ).first()

    return {
        "id": str(user_row[0]),
        "email": user_row[1],
        "name": user_row[2],
        "role": user_row[3],
        "emailVerified": bool(user_row[4]),
    }


def create_session(neon_user_id: str, user_agent: str | None = None, ip_address: str | None = None) -> dict[str, Any]:
    token = secrets.token_urlsafe(32)
    expires_at = datetime.utcnow() + timedelta(days=30)

    with SessionLocal() as db:
        session_id = str(uuid.uuid4())
        db.execute(
            text(
                """
                INSERT INTO neon_auth.session (
                    id,
                    token,
                    "userId",
                    "expiresAt",
                    "userAgent",
                    "ipAddress",
                    "createdAt",
                    "updatedAt"
                )
                VALUES (:id, :token, :user_id, :expires_at, :user_agent, :ip_address, NOW(), NOW())
                """
            ),
            {
                "id": session_id,
                "token": token,
                "user_id": neon_user_id,
                "expires_at": expires_at,
                "user_agent": user_agent,
                "ip_address": ip_address,
            },
        )
        db.commit()

    return {
        "token": token,
        "expiresAt": expires_at.isoformat(),
        "userId": neon_user_id,
    }


def authenticate_email_password(email: str, password: str) -> dict[str, Any]:
    with SessionLocal() as db:
        account = db.execute(
            text(
                """
                SELECT a."userId", a.password, u.email, u.name, u.role, u."emailVerified"
                FROM neon_auth.account a
                JOIN neon_auth."user" u ON u.id = a."userId"
                WHERE a."providerId" = 'email-password'
                  AND LOWER(a."accountId") = LOWER(:email)
                LIMIT 1
                """
            ),
            {"email": email},
        ).first()

    if account is None:
        raise ValueError("Invalid credentials")

    stored_hash = account[1]
    provided_hash = hashlib.sha256(password.encode("utf-8")).hexdigest()
    if stored_hash != provided_hash:
        raise ValueError("Invalid credentials")

    user = {
        "id": str(account[0]),
        "email": account[2],
        "name": account[3],
        "role": account[4],
        "emailVerified": bool(account[5]),
    }
    session = create_session(user["id"])
    return {"user": user, **session}


def get_user_from_session_token(token: str) -> dict[str, Any] | None:
    with SessionLocal() as db:
        row = db.execute(
            text(
                """
                SELECT s."userId", s."expiresAt", u.email, u.name, u.role, u."emailVerified"
                FROM neon_auth.session s
                JOIN neon_auth."user" u ON u.id = s."userId"
                WHERE s.token = :token AND s."expiresAt" > NOW()
                LIMIT 1
                """
            ),
            {"token": token},
        ).first()

    if row is None:
        return None

    return {
        "id": str(row[0]),
        "email": row[2],
        "name": row[3],
        "role": row[4],
        "emailVerified": bool(row[5]),
        "sessionExpiresAt": row[1].isoformat() if row[1] else None,
    }
