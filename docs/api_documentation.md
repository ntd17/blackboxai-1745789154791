# API Documentation

## Overview

This document provides a comprehensive overview of all JSON/RESTful API endpoints available in the project. The endpoints are grouped by functional areas for easier navigation and understanding.

### Environment Variables

The following environment variables are required for proper API operation and authentication:

- `JWT_SECRET`: Secret key for JWT token generation and validation.
- `STORACHA_API_KEY`: API key for Storacha file storage service.
- `OPENWEATHER_API_KEY`: API key for weather data service.
- `ML_MODEL_PATH`: Path to the machine learning model used for predictions.
- `REDIS_URL`: Redis connection URL for caching and rate limiting.

### Authentication

Most endpoints require authentication via JWT tokens. Include the following header in your requests:

```
Authorization: Bearer <access_token>
```

---

# Authentication Endpoints

## POST /login

- **Description**: Authenticate user and return access and refresh JWT tokens.
- **Authentication**: Not required.
- **Request Body**:
  ```json
  {
    "email": "user@example.com",
    "password": "password123"
  }
  ```
- **Success Response**:

  Status: 200 OK

  Body:
  ```json
  {
    "success": true,
    "access_token": "...",
    "refresh_token": "...",
    "user": {
      "id": 1,
      "email": "user@example.com",
      "name": "User Name"
    }
  }
  ```

- **Error Responses**:

  - 400 Bad Request (Missing or invalid fields)
  - 401 Unauthorized (Invalid credentials)

- **Example Test**:

```bash
curl -X POST http://localhost:5000/login -H "Content-Type: application/json" -d '{"email":"user@example.com","password":"password123"}'
```

---

## POST /refresh

- **Description**: Refresh access token using a valid refresh token.
- **Authentication**: Requires valid refresh token in Authorization header.
- **Success Response**:

  Status: 200 OK

  Body:
  ```json
  {
    "success": true,
    "access_token": "new_access_token"
  }
  ```

- **Error Responses**:

  - 401 Unauthorized (Invalid or expired refresh token)

- **Example Test**:

```bash
curl -X POST http://localhost:5000/refresh -H "Authorization: Bearer <refresh_token>"
```

---

## POST /logout

- **Description**: Logout user (token invalidation handled client-side).
- **Authentication**: Requires valid access token.
- **Success Response**:

  Status: 200 OK

  Body:
  ```json
  {
    "success": true,
    "message": "Logout successful"
  }
  ```

- **Example Test**:

```bash
curl -X POST http://localhost:5000/logout -H "Authorization: Bearer <access_token>"
```

---

## GET /me

- **Description**: Get current authenticated user information.
- **Authentication**: Requires valid access token.
- **Success Response**:

  Status: 200 OK

  Body:
  ```json
  {
    "success": true,
    "user": {
      "id": 1,
      "email": "user@example.com",
      "name": "User Name"
    }
  }
  ```

- **Example Test**:

```bash
curl -X GET http://localhost:5000/me -H "Authorization: Bearer <access_token>"
```

---

## POST /change-password

- **Description**: Change password for authenticated user.
- **Authentication**: Requires valid access token.
- **Request Body**:
  ```json
  {
    "current_password": "oldpass123",
    "new_password": "newpass456"
  }
  ```
- **Success Response**:

  Status: 200 OK

  Body:
  ```json
  {
    "success": true,
    "message": "Password changed successfully"
  }
  ```

- **Error Responses**:

  - 400 Bad Request (Missing fields or new password too short)
  - 401 Unauthorized (Invalid current password)

- **Example Test**:

```bash
curl -X POST http://localhost:5000/change-password -H "Authorization: Bearer <access_token>" -H "Content-Type: application/json" -d '{"current_password":"oldpass123","new_password":"newpass456"}'
```

---

# User Endpoints

## POST /usuarios or /api/usuarios

- **Description**: Register a new user.
- **Authentication**: Not required.
- **Request Body**:
  ```json
  {
    "name": "User Name",
    "email": "user@example.com",
    "password": "password123"
  }
  ```
- **Success Response**:

  Status: 201 Created

  Body:
  ```json
  {
    "message": "User registered successfully",
    "user": {
      "id": 1,
      "name": "User Name",
      "email": "user@example.com"
    }
  }
  ```

- **Error Responses**:

  - 400 Bad Request (Missing or invalid fields)
  - 409 Conflict (Email already registered)

- **Example Test**:

```bash
curl -X POST http://localhost:5000/usuarios -H "Content-Type: application/json" -d '{"name":"User Name","email":"user@example.com","password":"password123"}'
```

---

## GET /usuarios or /api/usuarios

- **Description**: Get list of all users.
- **Authentication**: Requires valid access token.
- **Success Response**:

  Status: 200 OK

  Body:
  ```json
  {
    "users": [
      {
        "id": 1,
        "name": "User Name",
        "email": "user@example.com"
      }
    ]
  }
  ```

- **Example Test**:

```bash
curl -X GET http://localhost:5000/usuarios -H "Authorization: Bearer <access_token>"
```

---

## GET /usuarios/<user_id> or /api/usuarios/<user_id>

- **Description**: Get user details by user ID.
- **Authentication**: Requires valid access token.
- **Path Parameters**:
  - `user_id` (integer): ID of the user.
- **Success Response**:

  Status: 200 OK

  Body:
  ```json
  {
    "id": 1,
    "name": "User Name",
    "email": "user@example.com"
  }
  ```

- **Error Responses**:

  - 404 Not Found (User not found)

- **Example Test**:

```bash
curl -X GET http://localhost:5000/usuarios/1 -H "Authorization: Bearer <access_token>"
```

---

# Storage Endpoints

## POST /upload

- **Description**: Upload a file to Storacha and register its CID.
- **Authentication**: Requires valid access token.
- **Request**: Multipart/form-data with fields:
  - `file` (file): File to upload (max 16MB).
  - `user_id` (integer): ID of the uploading user.
- **Success Response**:

  Status: 201 Created

  Body:
  ```json
  {
    "success": true,
    "message": "File uploaded successfully",
    "data": {
      "cid": "Qm...",
      "filename": "example.pdf",
      "mime_type": "application/pdf",
      "file_size": 123456
    }
  }
  ```

- **Error Responses**:

  - 400 Bad Request (Validation errors)
  - 413 Payload Too Large (File size exceeds limit)
  - 429 Too Many Requests (Rate limit exceeded)
  - 500 Internal Server Error (Storage or blockchain errors)

- **Example Test**:

```bash
curl -X POST http://localhost:5000/upload -H "Authorization: Bearer <access_token>" -F "file=@/path/to/file.pdf" -F "user_id=1"
```

---

## GET /cids

- **Description**: List all CIDs with optional filters.
- **Authentication**: Requires valid access token.
- **Query Parameters**:
  - `user_id` (integer, optional): Filter by user ID.
  - `page` (integer, optional): Page number (default 1).
  - `per_page` (integer, optional): Items per page (default 20, max 100).
- **Success Response**:

  Status: 200 OK

  Body:
  ```json
  {
    "success": true,
    "data": {
      "items": [ ... ],
      "pagination": {
        "page": 1,
        "per_page": 20,
        "total": 100,
        "pages": 5
      }
    }
  }
  ```

- **Example Test**:

```bash
curl -X GET "http://localhost:5000/cids?user_id=1&page=1&per_page=20" -H "Authorization: Bearer <access_token>"
```

---

## GET /cids/<cid>

- **Description**: Get information about a specific CID.
- **Authentication**: Requires valid access token.
- **Path Parameters**:
  - `cid` (string): IPFS CID.
- **Success Response**:

  Status: 200 OK

  Body:
  ```json
  {
    "success": true,
    "data": {
      "cid": "Qm...",
      "ipfs_available": true,
      "blockchain_status": { ... }
    }
  }
  ```

- **Error Responses**:

  - 404 Not Found (CID not found)

- **Example Test**:

```bash
curl -X GET http://localhost:5000/cids/Qm... -H "Authorization: Bearer <access_token>"
```

---

## GET /cids/<cid>/verify

- **Description**: Verify CID integrity across storage and blockchain.
- **Authentication**: Requires valid access token.
- **Path Parameters**:
  - `cid` (string): IPFS CID.
- **Success Response**:

  Status: 200 OK

  Body:
  ```json
  {
    "success": true,
    "data": {
      "cid": "Qm...",
      "verification": {
        "ipfs": { "available": true, "timestamp": "..." },
        "blockchain": { ... }
      }
    }
  }
  ```

- **Example Test**:

```bash
curl -X GET http://localhost:5000/cids/Qm.../verify -H "Authorization: Bearer <access_token>"
```

---

# Signature Endpoints

## POST /contrato/solicitar/<cid>

- **Description**: Request contract signature.
- **Authentication**: Requires valid access token.
- **Path Parameters**:
  - `cid` (string): Contract CID.
- **Success Response**:

  Status: 200 OK

  Body:
  ```json
  {
    "success": true,
    "message": "Signature request sent successfully",
    "data": {
      "contract": { ... },
      "transaction_hash": "0x..."
    }
  }
  ```

- **Error Responses**:

  - 404 Not Found (Contract not found)
  - 429 Too Many Requests (Rate limit exceeded)

- **Example Test**:

```bash
curl -X POST http://localhost:5000/contrato/solicitar/Qm... -H "Authorization: Bearer <access_token>"
```

---

## GET /contrato/metodos

- **Description**: Get available signature methods.
- **Authentication**: Requires valid access token.
- **Success Response**:

  Status: 200 OK

  Body:
  ```json
  {
    "success": true,
    "data": {
      "methods": {
        "signature_click_only": "Simple Click Signature",
        "signature_token_email": "Email Token Verification",
        "signature_icp_upload": "ICP-Brasil Certificate Upload",
        "signature_icp_direct": "ICP-Brasil Direct Signature"
      },
      "default_method": "signature_click_only"
    }
  }
  ```

- **Example Test**:

```bash
curl -X GET http://localhost:5000/contrato/metodos -H "Authorization: Bearer <access_token>"
```

---

## POST /contrato/token/solicitar

- **Description**: Request email verification token.
- **Authentication**: Requires valid access token.
- **Request Body**:
  ```json
  {
    "cid": "Qm...",
    "email": "user@example.com",
    "cpf": "12345678900"
  }
  ```
- **Success Response**:

  Status: 200 OK

  Body:
  ```json
  {
    "success": true,
    "message": "Token sent successfully",
    "data": {
      "expiry": "2024-01-01T00:00:00Z"
    }
  }
  ```

- **Error Responses**:

  - 400 Bad Request (Validation errors)
  - 403 Forbidden (Unauthorized email address)

- **Example Test**:

```bash
curl -X POST http://localhost:5000/contrato/token/solicitar -H "Authorization: Bearer <access_token>" -H "Content-Type: application/json" -d '{"cid":"Qm...","email":"user@example.com","cpf":"12345678900"}'
```

---

## POST /contrato/token/validar

- **Description**: Validate email token.
- **Authentication**: Requires valid access token.
- **Request Body**:
  ```json
  {
    "token": "token_string"
  }
  ```
- **Success Response**:

  Status: 200 OK

  Body:
  ```json
  {
    "success": true,
    "message": "Token validated successfully",
    "data": {
      "contract": { ... },
      "token_data": { ... }
    }
  }
  ```

- **Error Responses**:

  - 400 Bad Request (Missing or invalid token)

- **Example Test**:

```bash
curl -X POST http://localhost:5000/contrato/token/validar -H "Authorization: Bearer <access_token>" -H "Content-Type: application/json" -d '{"token":"token_string"}'
```

---

## POST /contrato/assinar/<cid> and /api/contrato/assinar/<cid>

- **Description**: Sign a contract using various signature methods.
- **Authentication**: Requires valid access token.
- **Path Parameters**:
  - `cid` (string): Contract CID.
- **Request Body**:
  ```json
  {
    "signer_email": "user@example.com",
    "signature_method": "signature_click_only",
    "signature_data": "...",
    "token": "...",  // if required
    "certificate_data": "...",  // if required
    "certificate_password": "..."
  }
  ```
- **Success Response**:

  Status: 200 OK

  Body:
  ```json
  {
    "success": true,
    "message": "Contract signed successfully",
    "data": {
      "contract": { ... },
      "transaction_hash": "0x..."
    }
  }
  ```

- **Error Responses**:

  - 400 Bad Request (Validation errors)
  - 403 Forbidden (Unauthorized signer email)
  - 404 Not Found (Contract not found)
  - 429 Too Many Requests (Rate limit exceeded)

- **Example Test**:

```bash
curl -X POST http://localhost:5000/contrato/assinar/Qm... -H "Authorization: Bearer <access_token>" -H "Content-Type: application/json" -d '{"signer_email":"user@example.com","signature_method":"signature_click_only","signature_data":"..."}'
```

---

## POST /contrato/cancelar/<cid>

- **Description**: Cancel a contract.
- **Authentication**: Requires valid access token.
- **Path Parameters**:
  - `cid` (string): Contract CID.
- **Success Response**:

  Status: 200 OK

  Body:
  ```json
  {
    "success": true,
    "message": "Contract cancelled successfully",
    "data": {
      "contract": { ... },
      "transaction_hash": "0x..."
    }
  }
  ```

- **Error Responses**:

  - 404 Not Found (Contract not found)
  - 429 Too Many Requests (Rate limit exceeded)

- **Example Test**:

```bash
curl -X POST http://localhost:5000/contrato/cancelar/Qm... -H "Authorization: Bearer <access_token>"
```

---

## GET /contrato/status/<cid>

- **Description**: Get signature status and details.
- **Authentication**: Requires valid access token.
- **Path Parameters**:
  - `cid` (string): Contract CID.
- **Success Response**:

  Status: 200 OK

  Body:
  ```json
  {
    "success": true,
    "data": {
      "contract": { ... },
      "blockchain_details": { ... },
      "events": [ ... ],
      "ipfs_status": { ... }
    }
  }
  ```

- **Error Responses**:

  - 404 Not Found (Contract not found)
  - 429 Too Many Requests (Rate limit exceeded)

- **Example Test**:

```bash
curl -X GET http://localhost:5000/contrato/status/Qm... -H "Authorization: Bearer <access_token>"
```

---

## GET /contrato/validar/<cid>

- **Description**: Validate contract signature.
- **Authentication**: Requires valid access token.
- **Path Parameters**:
  - `cid` (string): Signed contract CID.
- **Success Response**:

  Status: 200 OK

  Body:
  ```json
  {
    "success": true,
    "data": {
      "contract_details": { ... },
      "signature_details": { ... },
      "ipfs_status": { ... },
      "validation": {
        "is_valid": true
      }
    }
  }
  ```

- **Error Responses**:

  - 404 Not Found (Contract not found)
  - 429 Too Many Requests (Rate limit exceeded)

- **Example Test**:

```bash
curl -X GET http://localhost:5000/contrato/validar/Qm... -H "Authorization: Bearer <access_token>"
```

---

# Machine Learning Endpoints

## POST /predict_rain

- **Description**: Predict painting duration based on weather forecast.
- **Authentication**: Requires valid access token.
- **Request Body**:
  ```json
  {
    "weather_data": [ ... ],
    "location": { ... },
    "original_duration": 10
  }
  ```
- **Success Response**:

  Status: 200 OK

  Body:
  ```json
  {
    "success": true,
    "data": {
      "delay_days": 2,
      "recommended_duration": 12,
      "confidence_score": 0.95,
      "rain_probability": 0.8,
      "metadata": { ... },
      "warnings": []
    }
  }
  ```

- **Error Responses**:

  - 400 Bad Request (Validation errors)
  - 429 Too Many Requests (Rate limit exceeded)
  - 500 Internal Server Error

- **Example Test**:

```bash
curl -X POST http://localhost:5000/predict_rain -H "Authorization: Bearer <access_token>" -H "Content-Type: application/json" -d '{"weather_data":[...],"location":{...},"original_duration":10}'
```

---

## GET /model/status

- **Description**: Get current ML model status.
- **Authentication**: Requires valid access token.
- **Success Response**:

  Status: 200 OK

  Body:
  ```json
  {
    "success": true,
    "data": {
      "status": "healthy",
      "version": "1.0.0",
      "last_updated": "2024-01-01T00:00:00Z",
      "total_predictions": 1000
    }
  }
  ```

- **Example Test**:

```bash
curl -X GET http://localhost:5000/model/status -H "Authorization: Bearer <access_token>"
```

---

## POST /model/retrain

- **Description**: Retrain the ML model with new data.
- **Authentication**: Requires valid access token.
- **Request Body**:
  ```json
  {
    "training_data": [ ... ]
  }
  ```
- **Success Response**:

  Status: 200 OK

  Body:
  ```json
  {
    "success": true,
    "message": "Model successfully retrained",
    "new_version": "1.1.0"
  }
  ```

- **Error Responses**:

  - 500 Internal Server Error

- **Example Test**:

```bash
curl -X POST http://localhost:5000/model/retrain -H "Authorization: Bearer <access_token>" -H "Content-Type: application/json" -d '{"training_data":[...]}'
```

---

# Contracts Endpoints

## POST /contrato/gerar, /api/contrato/gerar, /generate

- **Description**: Generate a new painting contract with weather-based duration prediction.
- **Authentication**: Requires valid access token.
- **Request Body**:
  ```json
  {
    "creator_id": 1,
    "title": "Contract Title",
    "location": "City, Country",
    "planned_start_date": "2024-01-01",
    "planned_duration_days": 10,
    "contractor_details": {
      "name": "Contractor Name",
      "email": "contractor@example.com"
    },
    "provider_details": {
      "name": "Provider Name",
      "email": "provider@example.com"
    },
    "payment_details": {
      "amount": 1000,
      "method": "credit_card"
    }
  }
  ```
- **Success Response**:

  Status: 201 Created

  Body:
  ```json
  {
    "success": true,
    "message": "Contract generated successfully",
    "data": {
      "contract": { ... },
      "weather_prediction": { ... }
    }
  }
  ```

- **Error Responses**:

  - 400 Bad Request (Validation errors)
  - 429 Too Many Requests (Rate limit exceeded)
  - 500 Internal Server Error

- **Example Test**:

```bash
curl -X POST http://localhost:5000/contrato/gerar -H "Authorization: Bearer <access_token>" -H "Content-Type: application/json" -d '{"creator_id":1,"title":"Contract Title","location":"City, Country","planned_start_date":"2024-01-01","planned_duration_days":10,"contractor_details":{"name":"Contractor Name","email":"contractor@example.com"},"provider_details":{"name":"Provider Name","email":"provider@example.com"},"payment_details":{"amount":1000,"method":"credit_card"}}'
```

---

## GET /template

- **Description**: Get contract template structure.
- **Authentication**: Requires valid access token.
- **Success Response**:

  Status: 200 OK

  Body:
  ```json
  {
    "template": "<html>...</html>"
  }
  ```

- **Example Test**:

```bash
curl -X GET http://localhost:5000/template -H "Authorization: Bearer <access_token>"
```

---

## GET /contrato/status/<cid>, /api/status/<cid>

- **Description**: Get contract status by CID.
- **Authentication**: Requires valid access token.
- **Path Parameters**:
  - `cid` (string): Contract CID.
- **Success Response**:

  Status: 200 OK

  Body:
  ```json
  {
    "success": true,
    "data": {
      "ipfs_status": true,
      "blockchain_status": { ... },
      "weather_prediction": { ... },
      ...
    }
  }
  ```

- **Error Responses**:

  - 404 Not Found (Contract not found)

- **Example Test**:

```bash
curl -X GET http://localhost:5000/contrato/status/Qm... -H "Authorization: Bearer <access_token>"
```

---

## GET /custo/<cid>, /api/custo/<cid>

- **Description**: Estimate gas cost for contract operations.
- **Authentication**: Requires valid access token.
- **Path Parameters**:
  - `cid` (string): Contract CID.
- **Success Response**:

  Status: 200 OK

  Body:
  ```json
  {
    "success": true,
    "data": {
      "gas_estimates": {
        "register_contract": 21000,
        "update_signature": 15000
      }
    }
  }
  ```

- **Error Responses**:

  - 404 Not Found (Contract not found)

- **Example Test**:

```bash
curl -X GET http://localhost:5000/custo/Qm... -H "Authorization: Bearer <access_token>"
```

---

# Admin Endpoints

## GET /api/users/<user_id>

- **Description**: Get user details (Admin only).
- **Authentication**: Requires valid admin access token.
- **Path Parameters**:
  - `user_id` (integer): User ID.
- **Success Response**:

  Status: 200 OK

  Body:
  ```json
  {
    "id": 1,
    "name": "User Name",
    "email": "user@example.com",
    ...
  }
  ```

- **Error Responses**:

  - 403 Forbidden (Admin access required)
  - 404 Not Found (User not found)

- **Example Test**:

```bash
curl -X GET http://localhost:5000/api/users/1 -H "Authorization: Bearer <admin_access_token>"
```

---

## POST /api/users/<user_id>/toggle-status

- **Description**: Toggle user active status (Admin only).
- **Authentication**: Requires valid admin access token.
- **Path Parameters**:
  - `user_id` (integer): User ID.
- **Success Response**:

  Status: 200 OK

  Body:
  ```json
  {
    "status": true
  }
  ```

- **Error Responses**:

  - 403 Forbidden (Admin access required)
  - 404 Not Found (User not found)

- **Example Test**:

```bash
curl -X POST http://localhost:5000/api/users/1/toggle-status -H "Authorization: Bearer <admin_access_token>"
```

---

## GET /api/users/filter

- **Description**: Filter users based on search criteria (Admin only).
- **Authentication**: Requires valid admin access token.
- **Query Parameters**:
  - `search` (string, optional): Search term.
  - `role` (string, optional): Role filter (e.g., "admin").
  - `status` (string, optional): Status filter (e.g., "active").
- **Success Response**:

  Status: 200 OK

  Body:
  ```json
  [
    {
      "id": 1,
      "name": "User Name",
      "email": "user@example.com",
      ...
    }
  ]
  ```

- **Example Test**:

```bash
curl -X GET "http://localhost:5000/api/users/filter?search=John&role=admin&status=active" -H "Authorization: Bearer <admin_access_token>"
```

---

## GET /api/contracts/<cid>

- **Description**: Get contract details (Admin only).
- **Authentication**: Requires valid admin access token.
- **Path Parameters**:
  - `cid` (string): Contract CID.
- **Success Response**:

  Status: 200 OK

  Body:
  ```json
  {
    "id": 1,
    "title": "Contract Title",
    ...
  }
  ```

- **Error Responses**:

  - 403 Forbidden (Admin access required)
  - 404 Not Found (Contract not found)

- **Example Test**:

```bash
curl -X GET http://localhost:5000/api/contracts/Qm... -H "Authorization: Bearer <admin_access_token>"
```

---

## POST /api/contracts/<cid>/cancel

- **Description**: Cancel a contract (Admin only).
- **Authentication**: Requires valid admin access token.
- **Path Parameters**:
  - `cid` (string): Contract CID.
- **Success Response**:

  Status: 200 OK

  Body:
  ```json
  {
    "status": "cancelled"
  }
  ```

- **Error Responses**:

  - 403 Forbidden (Admin access required)
  - 400 Bad Request (Cannot cancel non-draft contracts)
  - 404 Not Found (Contract not found)

- **Example Test**:

```bash
curl -X POST http://localhost:5000/api/contracts/Qm.../cancel -H "Authorization: Bearer <admin_access_token>"
```

---

## GET /api/contracts/filter

- **Description**: Filter contracts based on search criteria (Admin only).
- **Authentication**: Requires valid admin access token.
- **Query Parameters**:
  - `search` (string, optional): Search term.
  - `status` (string, optional): Status filter.
  - `date` (string, optional): Date filter (e.g., "today", "week", "month").
- **Success Response**:

  Status: 200 OK

  Body:
  ```json
  [
    {
      "id": 1,
      "title": "Contract Title",
      ...
    }
  ]
  ```

- **Example Test**:

```bash
curl -X GET "http://localhost:5000/api/contracts/filter?search=Painting&status=active&date=week" -H "Authorization: Bearer <admin_access_token>"
```

---

# Additional Notes

- For further testing and exploration, refer to the existing Postman collection file: `painting_contract_api.postman_collection.json`.
- Ensure all required environment variables are set before running tests.
- Use valid JWT tokens for authenticated endpoints.
- Rate limiting is applied on many endpoints; avoid excessive requests during testing.

---

# End of API Documentation
