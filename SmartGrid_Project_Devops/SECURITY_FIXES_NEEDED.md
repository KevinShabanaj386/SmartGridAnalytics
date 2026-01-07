# Problemet e Sigurisë që Duhen Rregulluar

## 🔴 Problemet Kritike

### 1. JWT Signature Verification Missing
**Problem**: Në `zero_trust.py`, JWT token verifikohet pa signature verification (`verify_signature: False`). Kjo lejon që çdokush të krijojë tokens të rreme.

**Vendndodhja**: `docker/api_gateway/zero_trust.py:52`

**Rreziku**: HIGH - Çdokush mund të krijojë tokens të rreme dhe të aksesojë sistemin.

### 2. Hardcoded JWT Secrets në OAuth2
**Problem**: `oauth2.py` përdor hardcoded JWT secret (`'your-secret-key-change-in-production'`) në 3 vende në vend që të përdorë nga Vault.

**Vendndodhja**: 
- `docker/user-management-service/oauth2.py:68`
- `docker/user-management-service/oauth2.py:102`
- `docker/user-management-service/oauth2.py:113`

**Rreziku**: MEDIUM - Nëse kodi ekspozohet, secrets janë të dukshëm.

### 3. Hardcoded OAuth2 Client Secrets
**Problem**: OAuth2 client secrets janë hardcoded në kod.

**Vendndodhja**: `docker/user-management-service/oauth2.py:18, 24`

**Rreziku**: MEDIUM - Client secrets duhet të jenë në Vault.

### 4. Zero Trust JWT Verification pa Secret
**Problem**: Zero Trust nuk verifikon JWT signature sepse nuk merr secret nga Vault.

**Vendndodhja**: `docker/api_gateway/zero_trust.py:52`

**Rreziku**: HIGH - Tokens mund të falsifikohen.

## 🟡 Problemet e Mesme

### 5. Input Validation
**Problem**: Duhet të kontrolloj nëse të gjitha endpoints kanë input validation.

**Rreziku**: MEDIUM - SQL injection, XSS, dhe të tjera vulnerabilities.

### 6. Rate Limiting Memory Leak
**Problem**: `_request_counts` dictionary nuk pastrohet më shpesh, mund të rritet pa kufi.

**Vendndodhja**: `docker/api_gateway/zero_trust.py:139`

**Rreziku**: LOW - Memory leak në production.

## 📋 Plan për Rregullim

1. ✅ Rregulloj JWT signature verification në Zero Trust
2. ✅ Integro OAuth2 me Vault për JWT secret
3. ✅ Lëviz OAuth2 client secrets në Vault
4. ✅ Përmirësoj rate limiting cleanup
5. ✅ Shto input validation ku mungon

