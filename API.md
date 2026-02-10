# API Documentation

## Overview

This API allows management of **Conversations** via standard CRUD operations.

**Base URL**: `http://localhost:3030/api`

## Response Format

All API responses follow a standard `APIOutput` structure:

```json
{
  "status_code": 200,
  "message": "Success",
  "data": { ... }
}
```

In case of error:

```json
{
  "status_code": 404,
  "message": "Conversation not found",
  "data": null
}
```

---

## Endpoints

### 1. Create Conversation

Creates a new conversation.

- **URL**: `/conversations`
- **Method**: `POST`
- **Request Body**:
    ```json
    {
      "user_id": 1,
      "agent": "support_bot",
      "title": "Help with login"
    }
    ```
- **Response**: `201 Created`
    ```json
    {
      "status_code": 201,
      "message": "Success",
      "data": {
        "id": 1,
        "user_id": 1,
        "agent": "support_bot",
        "title": "Help with login",
        "created_at": "2023-10-27T10:00:00Z",
        "last_message_at": null
      }
    }
    ```

### 2. Get Conversation

Retrieve a specific conversation by ID.

- **URL**: `/conversations/{id}`
- **Method**: `GET`
- **Response**: `200 OK`
    ```json
    {
      "status_code": 200,
      "message": "Success",
      "data": {
        "id": 1,
        "user_id": 1,
        "agent": "support_bot",
        "title": "Help with login",
        "created_at": "2023-10-27T10:00:00Z",
        "last_message_at": "2023-10-27T10:05:00Z"
      }
    }
    ```

### 3. List Conversations

Retrieve a list of conversations for a specific user.

- **URL**: `/conversations`
- **Method**: `GET`
- **Query Parameters**:
    - `user_id` (Required): ID of the user.
    - `limit` (Optional, Default: 10): Number of items to return.
    - `offset` (Optional, Default: 0): Pagination offset.
- **Example**: `/conversations?user_id=1&limit=5`
- **Response**: `200 OK`
    ```json
    {
      "status_code": 200,
      "message": "Success",
      "data": [
        {
          "id": 1,
          "user_id": 1,
          "agent": "support_bot",
          "title": "Help with login",
          "created_at": "2023-10-27T10:00:00Z",
          "last_message_at": "2023-10-27T10:05:00Z"
        }
      ]
    }
    ```

### 4. Update Conversation

Update an existing conversation.

- **URL**: `/conversations/{id}`
- **Method**: `PUT`
- **Request Body** (Fields are optional):
    ```json
    {
      "title": "Updated Title",
      "agent": "new_agent_name"
    }
    ```
- **Response**: `200 OK`
    ```json
    {
      "status_code": 200,
      "message": "Success",
      "data": {
        "id": 1,
        "user_id": 1,
        "agent": "new_agent_name",
        "title": "Updated Title",
        "created_at": "2023-10-27T10:00:00Z",
        "last_message_at": "2023-10-27T10:05:00Z"
      }
    }
    ```

### 5. Delete Conversation

Delete a conversation by ID.

- **URL**: `/conversations/{id}`
- **Method**: `DELETE`
- **Response**: `200 OK`
    ```json
    {
      "status_code": 200,
      "message": "Conversation deleted successfully",
      "data": null
    }
    ```
