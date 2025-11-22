# JWT: JSON Web Token

An open standard that defines a compact and self-contained way to securely transmit information as a JSON object.

See https://jwt.io to look at a JWT structure.

## HEADER

```json
{
    "alg": "HS256",
    "typ": "JWT",
    "kid": "000"  # Key ID (optional), so the server can identify the key used to sign the token
}
```

## PAYLOAD (claims - key/value pairs)

- **REGISTERED CLAIMS:** Defined by the JWT specification  
- **CUSTOM CLAIMS:** Not defined by the JWT specification, used to store any type of info that we want to include in the JWT

```json
{
    # REGISTERED CLAIMS
    "iss": "https://example.com",     # Issuer of the JWT
    "sub": "1dfe8d8-98a5-4314-b4ae",  # Subject of the JWT (the identifier of the subject)
    "aud": "api://my-api",            # Audience of the JWT
    "exp": 1516239022,                # Expired at
    "iat": 1516239022,                # Issued at
    # CUSTOM CLAIMS
    "name": "John Doe",
    "email": "john@doe",
    "role": "user"
}
```

## SIGNATURE

```
HMAC-SHA256( base64UrlEncode(HEADER) + "." + base64UrlEncode(PAYLOAD), SECRET_KEY )
```

## TOKEN STRUCTURE

```
[Base64Url(HEADER)].[Base64Url(PAYLOAD)].[Base64Url(SIGNATURE)]
```

---

# SESSION-BASED AUTHENTICATION

1. The user sends their login credentials to the server.  
2. The server verifies these credentials. If valid, it creates a new session.  
3. The server stores the session data (DB or Redis).  
4. Session data usually includes user ID, expiration time and other metadata.  
5. Server returns a unique **session ID**, usually as a cookie.  
6. On each request the client sends the **session ID** cookie.  
7. The server looks up session data and authenticates.  

### **Characteristics**

- Requires separate storage for sessions.  
- Easy invalidation: server deletes/invalidates session.  
- Scaling requires centralized session store.

---

# JWT-BASED AUTHENTICATION

1. User sends credentials.  
2. Server validates them and creates a **JWT**.  
3. Server signs JWT with secret key. This signature ensures the integrity of the token, preventing tampering. 
4. Server returns JWT (body or cookie).  
5. Client stores JWT (localStorage, cookie, etc.).  
6. Client sends JWT on each request.  
7. Server verifies JWT signature. If it is valid, the server trusts the data in the token and uses it for authentication and authorization.

### **Characteristics**

- Pure access-token–only JWT authentication does not require server-side storage. 
- Real-world setups require additional storage (refresh tokens, blacklists, key rotation).  
- JWT invalidation is hard.  
- Scaling is easy unless refresh tokens/blacklists add state.  
- Signing can be symmetric (HMAC) or asymmetric (RSA/ECDSA).

---

# THINGS TO KNOW ABOUT JWT

- If someone steals a JWT, they can impersonate the user. TLS is mandatory.  
- Use **refresh tokens** with **short-lived access tokens**:  
  - The Access token is the actual JWT, used for authentication on each request
  - Access token = short-lived (≈15 min)  
  - Refresh token = long-lived, stored server-side  
  - When AT expires, client sends RT to a special token endpoint on the server
  - Server validates RT and issues new AT  
- Never store sensitive info inside the JWT.  
- JWT ensures **authenticity**, not **confidentiality**.  
- JWT is **signed and encoded**, NOT encrypted.

---

# WHERE TO STORE JWT IN THE BROWSER FRONTEND?

## 1. In a Cookie

- Up to 4kb  
- Automatically sent with each request  
- Vulnerable to CSRF and XSS  

### Recommended Security Flags
- `SameSite=Lax` or `Strict`  
- Anti-CSRF tokens if `SameSite=None`  
- `httpOnly` (protects against XSS), making the cookie inaccessible to the JS document.cookie API. 
- `secure` (HTTPS only), so the cookie is sent to the server only with an encrypted request over HTTPS protocol.

---

## 2. In Web Storage (Local/Session Storage)

- **LocalStorage:**  
  - Up to 10mb  
  - Accessible from any window  
  - Never expires automatically  

- **SessionStorage:**  
  - Up to 5mb  
  - Same tab only  
  - Expires on tab close  

- Storage is origin-restricted.  
- JWT must be sent via `Authorization` header.

---

## 3. In Memory (JS Variables)

- Tab-scoped  
- JWT must be sent via `Authorization` header`

