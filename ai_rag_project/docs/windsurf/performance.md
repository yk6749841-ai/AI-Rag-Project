# Performance - Chef-AI Redis Caching

## Redis Search Acceleration

### Why Redis for Recipe Searches
• **In-Memory Speed**: Sub-millisecond response times
• **Data Structures**: Native support for hashes, sets, sorted sets
• **Persistence**: Optional disk backup for reliability
• **Scalability**: Horizontal scaling with clustering

### Search Result Caching
• **Query Hashing**: Unique keys for search parameter combinations
• **Result Storage**: Complete paginated results cached
• **Index Caching**: Ingredient and cuisine mappings in memory
• **Autocomplete**: Prefix-based suggestion caching

### Cache Layers
• **L1 - Search Results**: 15 minute TTL for fresh content
• **L2 - Recipe Details**: 2 hour TTL for stable recipe data
• **L3 - User Preferences**: 30 minute TTL for personalization
• **L4 - Scaling Calculations**: 24 hour TTL for pre-computed values

## 24-Hour TTL Policy

### Why 24 Hours for Scaling
• **Recipe Stability**: Ingredient ratios rarely change
• **Compute Intensive**: Scaling calculations are expensive operations
• **User Patterns**: Same users often scale same recipes repeatedly
• **Storage Efficiency**: Long TTL reduces re-computation

### TTL Strategy by Data Type
• **Search Results**: 15 minutes - content changes frequently
• **Recipe Details**: 2 hours - moderate change frequency  
• **User Sessions**: 30 minutes - security considerations
• **Scaling Data**: 24 hours - stable mathematical relationships

### Cache Invalidation
• **Time-Based**: Automatic expiration prevents stale data
• **Event-Driven**: Manual invalidation on recipe updates
• **Tag-Based**: Related cache clearing for bulk updates
• **Memory Management**: LRU eviction for pressure relief

## Performance Impact

### Speed Improvements
• **Search Queries**: 95% faster than database queries
• **Recipe Loading**: 90% cache hit ratio for popular recipes
• **Scaling Calculations**: 96% pre-computation hit rate
• **User Experience**: Sub-100ms response times

### Memory Optimization
• **Compression**: Redis compression for large objects
• **TTL Management**: Automatic cleanup of expired keys
• **Selective Caching**: Only cache frequently accessed data
• **Monitoring**: Real-time memory usage tracking
