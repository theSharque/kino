# API Documentation

## OpenAPI / Swagger UI

The Kino Backend API provides **automatic OpenAPI documentation** with Swagger UI.

### Access Documentation

Once the server is running, you can access:

- **Swagger UI**: [http://localhost:8000/api/docs](http://localhost:8000/api/docs)
- **OpenAPI Spec (JSON)**: [http://localhost:8000/api/docs/spec](http://localhost:8000/api/docs/spec)

### Using with Postman

1. **Import OpenAPI spec into Postman:**
   - Open Postman
   - Click "Import" button
   - Enter URL: `http://localhost:8000/api/docs/spec`
   - Postman will automatically create a collection with all endpoints

2. **Export spec file:**
   ```bash
   curl http://localhost:8000/api/docs/spec > kino-api-spec.json
   ```
   Then import this file into Postman or any other API client.

## API Versions

### API v1 (Legacy - Manual Routes)
- Original endpoints using standard aiohttp handlers
- Endpoints: `/api/v1/*`
- **Not auto-documented** in Swagger
- Still fully functional

### API v2 (Documented - PydanticView)
- New endpoints using `aiohttp-pydantic` with automatic documentation
- Endpoints: `/api/v2/*`
- **Automatically documented** in Swagger UI
- Type validation with Pydantic models

## Available Endpoints (v2)

### Projects

#### List Projects
```
GET /api/v2/projects
```
Returns all projects in the database.

**Response:**
```json
{
  "total": 5,
  "projects": [...]
}
```

#### Create Project
```
POST /api/v2/projects
Content-Type: application/json

{
  "name": "My Project",
  "width": 1920,
  "height": 1080,
  "fps": 30
}
```

**Response (201):**
```json
{
  "id": 1,
  "name": "My Project",
  "width": 1920,
  "height": 1080,
  "fps": 30,
  "created_at": "2025-10-11T...",
  "updated_at": "2025-10-11T..."
}
```

#### Get Project by ID
```
GET /api/v2/projects/{project_id}
```

**Response (200):**
```json
{
  "id": 1,
  "name": "My Project",
  ...
}
```

**Response (404):**
```json
{
  "error": "Not found",
  "message": "Project with id 999 not found"
}
```

#### Update Project
```
PUT /api/v2/projects/{project_id}
Content-Type: application/json

{
  "name": "Updated Name"
}
```

All fields are optional. Only provided fields will be updated.

**Response (200):**
```json
{
  "id": 1,
  "name": "Updated Name",
  ...
}
```

#### Delete Project
```
DELETE /api/v2/projects/{project_id}
```

**Response (200):**
```json
{
  "message": "Project deleted successfully"
}
```

**Note:** Deleting a project will cascade delete all associated frames.

## Adding New Documented Endpoints

To add new endpoints with automatic OpenAPI documentation:

### 1. Create a PydanticView class

```python
from aiohttp import web
from aiohttp_pydantic import PydanticView
from aiohttp_pydantic.oas.typing import r200, r404

from models.your_model import YourModel, YourResponse

class YourView(PydanticView):
    async def get(self) -> r200[YourResponse]:
        """
        Endpoint description

        Detailed description here.

        Tags:
            - Your Category

        Status Codes:
            200: Success description
            404: Not found description
        """
        # Your logic here
        return web.json_response({...})

    async def post(self, data: YourModel) -> r200[YourResponse]:
        """
        Create endpoint description

        Tags:
            - Your Category
        """
        # Your logic here
        return web.json_response({...}, status=201)
```

### 2. Register the view in routes.py

```python
app.router.add_view('/api/v2/your-endpoint', YourView)
```

### 3. Restart the server

The endpoint will automatically appear in Swagger UI!

## Status Code Types

Use these types for response annotations:

```python
from aiohttp_pydantic.oas.typing import (
    r200,  # 200 OK
    r201,  # 201 Created
    r204,  # 204 No Content
    r400,  # 400 Bad Request
    r401,  # 401 Unauthorized
    r403,  # 403 Forbidden
    r404,  # 404 Not Found
    r500,  # 500 Internal Server Error
)
```

**Example with multiple status codes:**
```python
async def get(self, id: int, /) -> r200[MyModel] | r404:
    """Endpoint that might return 200 or 404"""
    ...
```

## URL Parameters

Use `/` in method signature to indicate path parameters:

```python
async def get(self, project_id: int, /) -> r200[ProjectResponse]:
    """
    project_id comes from URL: /api/v2/projects/{project_id}
    """
    ...
```

## Request Body

Use Pydantic models as parameters for automatic validation:

```python
async def post(self, project: ProjectCreate) -> r200[ProjectResponse]:
    """
    project will be automatically validated from request JSON body
    """
    ...
```

## Query Parameters

```python
from pydantic import BaseModel

class QueryParams(BaseModel):
    page: int = 1
    limit: int = 10

async def get(self, query: QueryParams) -> r200[list[Item]]:
    """
    Handles: GET /endpoint?page=2&limit=20
    """
    ...
```

## Tags and Organization

Use tags in docstrings to organize endpoints in Swagger UI:

```python
"""
Your endpoint description

Tags:
    - Projects
    - Management
"""
```

## Testing

### Using curl
```bash
# List projects
curl http://localhost:8000/api/v2/projects

# Create project
curl -X POST http://localhost:8000/api/v2/projects \
  -H "Content-Type: application/json" \
  -d '{"name":"Test","width":1920,"height":1080,"fps":30}'

# Get specific project
curl http://localhost:8000/api/v2/projects/1

# Update project
curl -X PUT http://localhost:8000/api/v2/projects/1 \
  -H "Content-Type: application/json" \
  -d '{"name":"Updated Name"}'

# Delete project
curl -X DELETE http://localhost:8000/api/v2/projects/1
```

### Using Swagger UI

1. Go to http://localhost:8000/api/docs
2. Click on any endpoint
3. Click "Try it out"
4. Fill in parameters
5. Click "Execute"
6. View response

## Migration from v1 to v2

All v1 endpoints (`/api/v1/*`) continue to work. To migrate:

1. Keep v1 endpoints running
2. Create v2 versions using PydanticView
3. Update clients to use v2
4. Eventually deprecate v1

**Benefits of v2:**
- Automatic documentation
- Better type safety
- Automatic validation
- OpenAPI spec for code generation

## Resources

- [aiohttp-pydantic Documentation](https://github.com/Maillol/aiohttp-pydantic)
- [OpenAPI Specification](https://swagger.io/specification/)
- [Swagger UI](https://swagger.io/tools/swagger-ui/)
- [Pydantic Documentation](https://docs.pydantic.dev/)

