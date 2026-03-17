# Database Logic - Chef-AI Architecture

## Why MongoDB for Recipes

• **Flexible Schema**: Recipes have varying structures - different ingredient counts, steps, and nutritional data
• **Document Model**: Natural fit for nested recipe data without complex JOINs
• **Scalability**: Horizontal scaling for growing recipe database
• **Performance**: Efficient indexing on ingredients, cuisine, cooking time
• **JSON Integration**: Direct API responses without transformation overhead

## Ingredient Scaling Strategy

### Linear Scaling
• **Used For**: Main ingredients (flour, sugar, butter, vegetables)
• **Formula**: `scaledAmount = baseAmount × (targetServings / originalServings)`
• **Why**: These ingredients maintain proportional relationships
• **Examples**: Dough, sauces, proteins, most produce

### Sublinear Scaling  
• **Used For**: Leavening agents, spices, seasonings
• **Formula**: `scaledAmount = baseAmount × Math.pow(targetServings / originalServings, 0.7)`
• **Why**: Prevents over-seasoning in large batches
• **Examples**: Baking soda, salt, herbs, spices

### Threshold Scaling
• **Used For**: Critical flavorings and preservatives
• **Minimum Amounts**: Maintained regardless of batch size
• **Maximum Limits**: Prevent concentration issues
• **Examples**: Salt, yeast, certain preservatives

## Performance Considerations

• **Pre-computed Tables**: Cache common serving multiples (2x, 4x, 6x)
• **Density Storage**: Ingredient densities for accurate unit conversions
• **Compound Indexes**: Fast queries on ingredients + amounts
• **Aggregation Pipelines**: Server-side calculations reduce client load
