### Field Errors:

```json
{
  "result": [],
  "status": 400,
  "success": false,
  "error_messages": {
    "name": "This field is required.",
    "description": "This field is required.",
    "country": "this field is required.",
    "city": "Invalid pk \"1000\" - object does not exist."
  }
}
```

### Validation Errors:

```json
{
  "result": [],
  "status": 400,
  "success": false,
  "error_messages": {
    "non_field_errors": "The phone number you entered is alreay in use."
  }
}
```

### Not Found Errors:

http://localhost:8088/api/language/v1/d/

```json
{
  "result": [],
  "status": 404,
  "success": false,
  "error_messages": {
    "non_field_errors": "No Language matches the given query."
  }
}
```

### Response without Pagination:

http://localhost:8088/api/users/

```json
{
  "result": [
    {
      "id": 1,
      "name": "first user",
      "created_at": "2023-11-04T13:14:32.889228+03:30"
    },
    {
      "id": 2,
      "name": "first user",
      "created_at": "2023-11-04T13:14:32.889228+03:30"
    }
  ],
  "status": 200,
  "success": true,
  "error_messages": []
}
```

### Response with Pagination:

http://localhost:8088/api/experts/?limit=2&offset=2

```json
{
  "result": {
    "count": 12,
    "next": "http://localhost:8088/api/experts/?limit=2&offset=4",
    "previous": "http://localhost:8088/api/experts/?limit=2",
    "results": [
      {
        "id": 4,
        "name": "first expert",
        "created_at": "2023-11-04T13:14:46.658669+03:30"
      },
      {
        "id": 5,
        "name": "second expert",
        "created_at": "2023-11-04T13:14:56.701491+03:30"
      }
    ]
  },
  "status": 200,
  "success": true,
  "error_messages": []
}
```

### Successful Informative Responses

http://localhost:8088/api/auth/v1/send-otp/

```json
{
  "result": {
    "message": "Your authentication code has been sent.",
    "otp_time_remaining": 119
  },
  "status": 202,
  "success": true,
  "error_messages": {}
}
```