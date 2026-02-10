# API Documentation

## Overview

This API allows management of **Conversations** and **Messages** via standard CRUD operations.

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
  "message": "Not found",
  "data": null
}
```

---

## Conversations

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

### 2. Get Conversation

Retrieve a specific conversation by ID.

- **URL**: `/conversations/{id}`
- **Method**: `GET`
- **Response**: `200 OK`

### 3. List Conversations

Retrieve a list of conversations for a specific user.

- **URL**: `/conversations`
- **Method**: `GET`
- **Query Parameters**:
    - `user_id` (Required): ID of the user.
    - `limit` (Optional, Default: 10): Number of items to return.
    - `offset` (Optional, Default: 0): Pagination offset.

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

### 5. Delete Conversation

Delete a conversation by ID.

- **URL**: `/conversations/{id}`
- **Method**: `DELETE`
- **Response**: `200 OK`

---

## Messages

### 1. Create Message

Create a new message in a conversation.

- **URL**: `/conversations/{conversation_id}/messages`
- **Method**: `POST`
- **Request Body**:
    ```json
    {
      "conversation_id": 1,
      "role": "user",
      "content": "Hello world",
      "metadata": { "source": "web" }
    }
    ```
- **Response**: `201 Created`
    ```json
    {
      "status_code": 201,
      "message": "Success",
      "data": {
        "id": 1,
        "conversation_id": 1,
        "role": "user",
        "content": "Hello world",
        "metadata": { "source": "web" },
        "timestamp": "2023-10-27T10:05:00Z"
      }
    }
    ```

### 2. List Messages

Retrieve a history of messages for a specific conversation.

- **URL**: `/conversations/{conversation_id}/messages`
- **Method**: `GET`
- **Query Parameters**:
    - `limit` (Optional, Default: 50): Number of items to return.
    - `offset` (Optional, Default: 0): Pagination offset.
- **Response**: `200 OK`
    ```json
    {
      "status_code": 200,
      "message": "Success",
      "data": [
        {
          "id": 1,
          "conversation_id": 1,
          "role": "user",
          "content": "Hello world",
          "metadata": null,
          "timestamp": "2023-10-27T10:05:00Z"
        }
      ]
    }
    ```

### 3. Get Message

Retrieve a specific message by ID.

- **URL**: `/messages/{id}`
- **Method**: `GET`
- **Response**: `200 OK`

### 4. Update Message

Update an existing message.

- **URL**: `/messages/{id}`
- **Method**: `PUT`
- **Request Body** (Fields are optional):
    ```json
    {
      "content": "Updated content",
      "metadata": { "edited": true }
    }
    ```
- **Response**: `200 OK`

### 5. Delete Message

Delete a message by ID.

- **URL**: `/messages/{id}`
- **Method**: `DELETE`
- **Response**: `200 OK`
