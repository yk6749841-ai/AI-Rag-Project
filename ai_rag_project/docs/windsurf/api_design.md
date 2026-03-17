# API Design - Chef-AI Architecture

## Core REST Endpoints

### Recipe Management
• **GET /recipes**: Search with filters (cuisine, diet, time, difficulty)
• **GET /recipes/{id}**: Full recipe details with ingredients and steps
• **POST /recipes/{id}/scale**: Scale ingredients to different serving sizes
• **Why RESTful**: Predictable patterns, easy caching, standard HTTP methods

### User Favorites
• **GET /users/favorites**: Paginated user favorite recipes
• **POST /users/favorites**: Add recipe to favorites with categories
• **DELETE /users/favorites/{id}**: Remove recipe from favorites
• **Why Separate**: User-specific data needs different caching strategies

### Search & Discovery
• **GET /search/suggestions**: Autocomplete for recipe names
• **GET /search/ingredients**: Find recipes by specific ingredients
• **Why Dedicated**: Search requires specialized indexing and ranking

## JWT Security Implementation

### Why JWT Authentication
• **Stateless**: No server-side session storage needed
• **Scalable**: Works across multiple server instances
• **Mobile-Friendly**: Easy integration with mobile apps
• **Performance**: Token verification is faster than database lookups

### Token Structure
• **User ID**: Unique identifier for personalization
• **Role**: user/premium/admin for access control
• **Expiration**: Short-lived access tokens (1 hour)
• **Refresh Tokens**: Long-lived for seamless sessions

### Security Benefits
• **No Password Storage**: Hashed passwords only
• **Revocation**: Token blacklist for compromised sessions
• **Rate Limiting**: Prevent brute force attacks
• **CORS Protection**: Cross-origin request security

## API Performance Features

• **Pagination**: Prevents large response payloads
• **Field Selection**: Clients request only needed data
• **Compression**: Gzip responses for faster transfers
• **Versioning**: URL-based versioning (/v1/, /v2/)
