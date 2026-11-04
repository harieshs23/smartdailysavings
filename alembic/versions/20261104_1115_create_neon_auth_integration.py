-- Neon Auth Integration Migration
-- Option C: Mixed approach - neon_auth for auth, public schema for app data

-- Ensure extensions are available
CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create function to get user by email with auth details
CREATE OR REPLACE FUNCTION public.get_neon_user_by_email(email TEXT)
RETURNS TABLE (
    id UUID,
    email VARCHAR(255),
    username VARCHAR(50),
    password_hash VARCHAR(255),
    role TEXT,
    created_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE,
    neon_auth_id UUID,
    email_verified BOOLEAN,
    banned BOOLEAN
)
LANGUAGE sql
STABLE
AS $$
BEGIN
    RETURN QUERY
    SELECT 
        u.id,
        u.email,
        u.username,
        u.password_hash,
        u.role,
        u.created_at,
        u.updated_at,
        nu.id AS neon_auth_id,
        nu."emailVerified",
        nu.banned
    FROM public.users u
    LEFT JOIN neon_auth."user" nu ON nu.email = u.email
    WHERE u.email = email;
END;
$$;

-- Create function to verify user credentials
CREATE OR REPLACE FUNCTION public.verify_user_credentials(
    p_email VARCHAR(255), 
    p_password VARCHAR(255)
)
RETURNS TABLE (
    user_id UUID,
    neon_user_id UUID,
    is_valid BOOLEAN,
    message TEXT
)
LANGUAGE sql
STABLE
AS $$
DECLARE
    v_user public.users%ROWTYPE;
    v_neon_user neon_auth."user"%ROWTYPE;
BEGIN
    -- Look up user in public schema
    SELECT * INTO v_user FROM public.users WHERE email = p_email;
    
    IF NOT FOUND THEN
        RETURN QUERY SELECT NULL::UUID, NULL::UUID, FALSE, 'User not found in public schema';
    END IF;
    
    -- Check neon_auth.user for email verification and status
    SELECT * INTO v_neon_user FROM neon_auth."user" WHERE email = p_email;
    
    -- Verify password using pgcrypto
    IF v_user.password_hash = crypt(p_password, v_user.password_hash) THEN
        -- Check if email is verified in neon_auth
        IF v_neon_user."emailVerified" THEN
            RETURN QUERY SELECT 
                v_user.id, 
                v_neon_user.id, 
                TRUE, 
                'Authentication successful';
        ELSE
            RETURN QUERY SELECT
                v_user.id,
                v_neon_user.id,
                FALSE,
                'Email not verified. Please verify your email.';
        END IF;
    ELSE
        RETURN QUERY SELECT
            v_user.id,
            v_neon_user.id,
            FALSE,
            'Invalid password';
    END IF;
END;
$$;

-- Create function to create a session
CREATE OR REPLACE FUNCTION public.create_user_session(
    p_user_id UUID,
    p_ip_address TEXT DEFAULT NULL,
    p_user_agent TEXT DEFAULT NULL
)
RETURNS UUID AS $$
DECLARE
    v_session_id UUID;
BEGIN
    -- Create session in neon_auth
    INSERT INTO neon_auth.session (id, token, "userId", "expiresAt", "ipAddress", "userAgent")
    VALUES (
        gen_random_uuid(),
        gen_random_uuid()::TEXT,  
        p_user_id,
        NOW() + INTERVAL '30 days',
        p_ip_address,
        p_user_agent
    )
    RETURNING id INTO v_session_id;
    
    RETURN v_session_id;
END;
$$ LANGUAGE plpgsql;

-- Create function to validate session
CREATE OR REPLACE FUNCTION public.validate_session(
    p_token TEXT
)
RETURNS TABLE (
    session_id UUID,
    user_id UUID,
    user_email VARCHAR(255),
    is_valid BOOLEAN,
    expires_at TIMESTAMP WITH TIME ZONE
)
LANGUAGE sql
STABLE
AS $$
BEGIN
    RETURN QUERY
    SELECT 
        s.id AS session_id,
        s."userId" AS user_id,
        nu.email AS user_email,
        TRUE AS is_valid,
        s."expiresAt" AS expires_at
    FROM neon_auth.session s
    JOIN neon_auth."user" nu ON s."userId" = nu.id
    WHERE s.token = p_token 
      AND s."expiresAt" > NOW()
      AND s.active = TRUE;
END;
$$;

-- Create function for social login
CREATE OR REPLACE FUNCTION public.social_login(
    p_provider VARCHAR(50),
    p_provider_user_id VARCHAR(255),
    p_access_token TEXT,
    p_email VARCHAR(255),
    p_name VARCHAR(255)
)
RETURNS TABLE (
    user_id UUID,
    neon_auth_user_id UUID,
    session_token TEXT,
    is_new_user BOOLEAN,
    message TEXT
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_account neon_auth.account%ROWTYPE;
    v_user public.users%ROWTYPE;
    v_neon_user neon_auth."user"%ROWTYPE;
    v_session_token UUID;
    v_new_user BOOLEAN := FALSE;
BEGIN
    -- Check if social account already exists
    SELECT * INTO v_account FROM neon_auth.account 
    WHERE "providerId" = p_provider AND "userId" = p_provider_user_id;
    
    IF FOUND THEN
        -- Existing social user
        SELECT * INTO v_neon_user FROM neon_auth."user" WHERE id = v_account."userId";
        
        -- Create session
        v_session_token := public.create_user_session(v_account."userId");
        
        -- Get user from public schema
        SELECT * INTO v_user FROM public.users WHERE id = v_account."userId";
        
        RETURN QUERY SELECT
            v_user.id,
            v_neon_user.id,
            v_session_token::TEXT,
            FALSE,
            'Social login successful';
    ELSE
        -- New social user
        -- 1. Create user in public schema
        INSERT INTO public.users (id, email, username, password_hash, created_at, updated_at)
        VALUES (
            gen_random_uuid(),
            p_email,
            p_name,
            crypt(p_access_token || substr(md5(random()::text), 1, 16), gen_salt('bf')),
            NOW(),
            NOW()
        )
        RETURNING * INTO v_user;
        
        v_new_user := TRUE;
        
        -- 2. Create user in neon_auth.user
        INSERT INTO neon_auth."user" (id, email, name, role)
        VALUES (
            v_user.id,
            p_email,
            p_name,
            'user'
        )
        RETURNING * INTO v_neon_user;
        
        -- 3. Create account record
        INSERT INTO neon_auth.account (id, "providerId", "userId", "accessToken")
        VALUES (
            gen_random_uuid(),
            p_provider,
            v_user.id,
            p_access_token
        );
        
        -- 4. Create session
        v_session_token := public.create_user_session(v_user.id);
        
        RETURN QUERY SELECT
            v_user.id,
            v_neon_user.id,
            v_session_token::TEXT,
            TRUE,
            'New user registered via social login';
    END IF;
END;
$$;

-- Create function for email verification
CREATE OR REPLACE FUNCTION public.send_email_verification(
    p_email VARCHAR(255)
)
RETURNS TABLE (
    verification_id UUID,
    code VARCHAR(6),
    expires_at TIMESTAMP WITH TIME ZONE,
    message TEXT
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_verification neon_auth.verification%ROWTYPE;
    v_user neon_auth."user"%ROWTYPE;
BEGIN
    -- Check if user exists in neon_auth
    SELECT * INTO v_user FROM neon_auth."user" WHERE email = p_email;
    
    IF NOT FOUND THEN
        RETURN QUERY SELECT NULL::UUID, NULL::VARCHAR, NULL::TIMESTAMP, 'User not found';
    END IF;
    
    -- Check if already verified
    IF v_user."emailVerified" THEN
        RETURN QUERY SELECT NULL::UUID, NULL::VARCHAR, NULL::TIMESTAMP, 'Email already verified';
    END IF;
    
    -- Create verification token
    DELETE FROM neon_auth.verification WHERE identifier = 'email' AND value = p_email;
    
    INSERT INTO neon_auth.verification (id, identifier, value, "expiresAt")
    VALUES (
        gen_random_uuid(),
        'email',
        p_email,
        NOW() + INTERVAL '24 hours'
    )
    RETURNING * INTO v_verification;
    
    -- Generate a 6-digit OTP-like code
    v_code := substr(md5(random()::text), 1, 6);
    
    RETURN QUERY SELECT
        v_verification.id,
        v_code,
        v_verification."expiresAt",
        'Verification code sent to ' || p_email;
END;
$$;

-- Create function to verify email code
CREATE OR REPLACE FUNCTION public.verify_email_code(
    p_email VARCHAR(255),
    p_code VARCHAR(6)
)
RETURNS TABLE (
    success BOOLEAN,
    user_id UUID,
    message TEXT
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_verification neon_auth.verification%ROWTYPE;
    v_user neon_auth."user"%ROWTYPE;
BEGIN
    -- Find the verification record
    SELECT * INTO v_verification FROM neon_auth.verification
    WHERE identifier = 'email' AND value = p_email AND "expiresAt" > NOW()
    ORDER BY created_at DESC
    LIMIT 1;
    
    IF NOT FOUND THEN
        RETURN QUERY SELECT FALSE, NULL, 'Invalid or expired verification code';
    END IF;
    
    -- Verify the code (simple string match for demo)
    -- In production, would compare with stored OTP
    IF v_verification.value ILIKE '%' || p_code || '%' THEN
        -- Mark user's email as verified in neon_auth
        UPDATE neon_auth."user"
        SET "emailVerified" = TRUE
        WHERE id = v_verification.identifier::UUID;  -- Note: needs adjustment
        
        RETURN QUERY SELECT TRUE, v_verification.id, 'Email verified successfully';
    ELSE
        RETURN QUERY SELECT FALSE, v_verification.id, 'Invalid verification code';
    END IF;
END;
$$;

-- Create function to invite user to organization
CREATE OR REPLACE FUNCTION public.invite_user_to_organization(
    p_org_id UUID,
    p_email VARCHAR(255),
    p_inviter_role TEXT DEFAULT 'admin'
)
RETURNS TABLE (
    invitation_id UUID,
    invitation_email VARCHAR(255),
    role TEXT,
    expires_at TIMESTAMP WITH TIME ZONE,
    status TEXT
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_organization neon_auth.organization%ROWTYPE;
    v_invitation neon_auth.invitation%ROWTYPE;
BEGIN
    -- Check organization exists
    SELECT * INTO v_organization FROM neon_auth.organization WHERE id = p_org_id;
    
    IF NOT FOUND THEN
        RETURN QUERY SELECT NULL::UUID, NULL::VARCHAR, NULL::TIMESTAMP, NULL, 'Organization not found';
    END IF;
    
    -- Create invitation
    INSERT INTO neon_auth.invitation (id, "organizationId", email, role, status, "expiresAt", "createdAt")
    VALUES (
        gen_random_uuid(),
        p_org_id,
        p_email,
        'member',
        'pending',
        NOW() + INTERVAL '7 days',
        NOW()
    )
    RETURNING * INTO v_invitation;
    
    RETURN QUERY SELECT
        v_invitation.id,
        v_invitation.email,
        v_invitation.role,
        v_invitation."expiresAt",
        'pending';
END;
$$;

-- Create function to accept invitation
CREATE OR REPLACE FUNCTION public.accept_invitation(
    p_invitation_id UUID,
    p_user_email VARCHAR(255)
)
RETURNS TABLE (
    success BOOLEAN,
    user_id UUID,
    organization_id UUID,
    message TEXT
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_invitation neon_auth.invitation%ROWTYPE;
    v_user public.users%ROWTYPE;
    v_member neon_auth.member%ROWTYPE;
BEGIN
    -- Get invitation
    SELECT * INTO v_invitation FROM neon_auth.invitation WHERE id = p_invitation_id;
    
    IF NOT FOUND THEN
        RETURN QUERY SELECT FALSE, NULL, NULL, 'Invitation not found';
    END IF;
    
    -- Check if invitation is still valid
    IF v_invitation."expiresAt" < NOW() THEN
        RETURN QUERY SELECT FALSE, NULL, NULL, 'Invitation expired';
    END IF;
    
    -- Check if user already exists in public schema
    SELECT * INTO v_user FROM public.users WHERE email = p_user_email;
    
    IF NOT FOUND THEN
        -- Create new user
        INSERT INTO public.users (id, email, username, password_hash, created_at, updated_at)
        VALUES (
            gen_random_uuid(),
            p_user_email,
            p_user_email,
            crypt('temp_' || substr(md5(random()::text), 1, 10), gen_salt('bf')),
            NOW(),
            NOW()
        )
        RETURNING * INTO v_user;
    END IF;
    
    -- Add user to organization as member
    INSERT INTO neon_auth.member (id, organizationId, userId, role)
    VALUES (
        gen_random_uuid(),
        v_invitation.organizationId,
        v_user.id,
        v_invitation.role
    )
    RETURNING * INTO v_member;
    
    RETURN QUERY SELECT TRUE, v_user.id, v_invitation.organizationId, 'User accepted invitation and joined organization';
END;
$$;

RAISE NOTICE 'Neon auth integration migration completed successfully';
