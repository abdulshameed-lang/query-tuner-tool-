# TypeScript Style Guide

## Overview

This guide defines TypeScript and React coding standards for the Oracle Database Performance Tuning Tool frontend.

## TypeScript Version

- **Required**: TypeScript 5.0+
- **Strict Mode**: Enabled

## Code Formatting

### Line Length
- **Maximum**: 100 characters
- **Rationale**: Comfortable for side-by-side code viewing

### Indentation
- **Use**: 2 spaces (standard for JavaScript/TypeScript)
- **Never**: Tabs

### Semicolons
- **Required**: Use semicolons
- **Enforced by**: ESLint and Prettier

```typescript
// Good
const result = calculateMetrics(data);
return result;

// Bad
const result = calculateMetrics(data)
return result
```

## Imports

### Order
1. React and React-related imports
2. Third-party library imports
3. Internal absolute imports
4. Internal relative imports
5. Type imports (separate section)

```typescript
// React
import React, { useState, useEffect } from 'react';

// Third-party
import { Button, Table } from 'antd';
import axios from 'axios';

// Internal absolute
import { QueryService } from '@/api/queries';
import { formatElapsedTime } from '@/utils/formatters';

// Internal relative
import { QueryCard } from './QueryCard';

// Types
import type { Query, ExecutionPlan } from '@/types/query';
```

### Import Style
- Use named imports when possible
- Avoid default exports for utilities
- Use type-only imports for types

```typescript
// Good
import type { Query } from '@/types/query';
import { fetchQueries } from '@/api/queries';

// Bad
import { Query } from '@/types/query'; // Don't import types as values
```

## Type Annotations

### Always Use TypeScript Types
- **Function parameters**: Always typed
- **Function returns**: Always typed
- **React component props**: Always typed via interfaces
- **State variables**: Type inferred or explicitly typed

```typescript
// Function with types
function calculateQueryImpact(
  elapsedTime: number,
  executions: number
): number {
  return elapsedTime * executions;
}

// Component with typed props
interface QueryCardProps {
  query: Query;
  onClick: (sqlId: string) => void;
  isSelected?: boolean;
}

export const QueryCard: React.FC<QueryCardProps> = ({
  query,
  onClick,
  isSelected = false
}) => {
  // Component implementation
};
```

### Type vs Interface
- **Use Interface**: For object shapes, especially React props
- **Use Type**: For unions, intersections, primitives

```typescript
// Interface for objects
interface Query {
  sqlId: string;
  sqlText: string;
  elapsedTime: number;
}

// Type for unions and complex types
type QueryStatus = 'running' | 'completed' | 'failed';
type QueryResult = Query | null;
type Nullable<T> = T | null;
```

### Avoid `any`
- Use `unknown` for truly unknown types
- Use generics for flexible types
- Use union types for multiple possible types

```typescript
// Bad
function processData(data: any): any {
  return data.value;
}

// Good
function processData<T extends { value: unknown }>(data: T): T['value'] {
  return data.value;
}

// Also good
function processResponse(response: unknown): Query[] {
  if (!isQueryArrayResponse(response)) {
    throw new Error('Invalid response format');
  }
  return response.queries;
}
```

## Naming Conventions

### Variables and Functions
- **Style**: `camelCase`
- **Constants**: `UPPER_SNAKE_CASE`
- **Private methods**: Prefix with underscore (optional in TS)

```typescript
// Variables
const queryList = fetchQueries();
const isLoading = false;

// Functions
function calculateTotalTime(queries: Query[]): number {
  return queries.reduce((sum, q) => sum + q.elapsedTime, 0);
}

// Constants
const MAX_QUERIES_PER_PAGE = 50;
const DEFAULT_TIMEOUT_MS = 5000;
```

### React Components
- **Style**: `PascalCase`
- **File names**: Match component name

```typescript
// QueryList.tsx
export const QueryList: React.FC<QueryListProps> = ({ queries }) => {
  return <div>{/* Component */}</div>;
};

// ExecutionPlanTree.tsx
export const ExecutionPlanTree: React.FC<ExecutionPlanTreeProps> = ({ plan }) => {
  return <div>{/* Component */}</div>;
};
```

### Interfaces and Types
- **Style**: `PascalCase`
- **Props interfaces**: Suffix with `Props`
- **Event handler types**: Prefix with `on` or `handle`

```typescript
interface QueryCardProps {
  query: Query;
  onQuerySelect: (sqlId: string) => void;
}

type HandleQueryClick = (sqlId: string) => void;
```

### Files and Folders
- **Components**: `PascalCase.tsx`
- **Utilities**: `camelCase.ts`
- **Hooks**: `use[Something].ts`
- **Types**: `camelCase.ts` or `PascalCase.ts`

```
components/
  QueryList.tsx
  QueryCard.tsx
utils/
  formatters.ts
  validators.ts
hooks/
  useQueries.ts
  useWebSocket.ts
types/
  query.ts
  executionPlan.ts
```

## React Component Patterns

### Functional Components Only
- Use functional components with hooks
- No class components

```typescript
// Good
export const QueryDetails: React.FC<QueryDetailsProps> = ({ sqlId }) => {
  const [query, setQuery] = useState<Query | null>(null);

  useEffect(() => {
    fetchQuery(sqlId).then(setQuery);
  }, [sqlId]);

  return <div>{query?.sqlText}</div>;
};

// Bad - Don't use class components
class QueryDetails extends React.Component {
  // ...
}
```

### Props Destructuring
- Destructure props in function signature
- Provide default values when appropriate

```typescript
// Good
interface ButtonProps {
  label: string;
  onClick: () => void;
  disabled?: boolean;
  variant?: 'primary' | 'secondary';
}

export const Button: React.FC<ButtonProps> = ({
  label,
  onClick,
  disabled = false,
  variant = 'primary'
}) => {
  return (
    <button onClick={onClick} disabled={disabled}>
      {label}
    </button>
  );
};
```

### Component Structure
```typescript
// 1. Imports
import React, { useState, useEffect } from 'react';
import type { Query } from '@/types/query';

// 2. Types/Interfaces
interface QueryListProps {
  queries: Query[];
  onQuerySelect: (sqlId: string) => void;
}

// 3. Component
export const QueryList: React.FC<QueryListProps> = ({ queries, onQuerySelect }) => {
  // 3a. Hooks
  const [selectedId, setSelectedId] = useState<string | null>(null);

  // 3b. Derived state
  const sortedQueries = queries.sort((a, b) => b.elapsedTime - a.elapsedTime);

  // 3c. Event handlers
  const handleSelect = (sqlId: string) => {
    setSelectedId(sqlId);
    onQuerySelect(sqlId);
  };

  // 3d. Effects
  useEffect(() => {
    // Effect logic
  }, [queries]);

  // 3e. Render helpers (if needed)
  const renderQuery = (query: Query) => (
    <div key={query.sqlId}>{query.sqlText}</div>
  );

  // 3f. Return JSX
  return (
    <div>
      {sortedQueries.map(renderQuery)}
    </div>
  );
};

// 4. Display name (optional, for debugging)
QueryList.displayName = 'QueryList';
```

### Custom Hooks

```typescript
// useQueries.ts
import { useState, useEffect } from 'react';
import type { Query } from '@/types/query';

interface UseQueriesResult {
  queries: Query[];
  isLoading: boolean;
  error: Error | null;
  refetch: () => void;
}

export function useQueries(connectionId: string): UseQueriesResult {
  const [queries, setQueries] = useState<Query[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  const fetchQueries = async () => {
    setIsLoading(true);
    try {
      const data = await queryService.getQueries(connectionId);
      setQueries(data);
      setError(null);
    } catch (err) {
      setError(err as Error);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchQueries();
  }, [connectionId]);

  return { queries, isLoading, error, refetch: fetchQueries };
}
```

### React Query / TanStack Query Patterns

```typescript
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { queryService } from '@/api/queries';

// Query hook
export function useQueryDetails(sqlId: string) {
  return useQuery({
    queryKey: ['query', sqlId],
    queryFn: () => queryService.getQueryDetails(sqlId),
    staleTime: 30000, // 30 seconds
    enabled: !!sqlId,
  });
}

// Mutation hook
export function useQueryAnalysis() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (sqlId: string) => queryService.analyzeQuery(sqlId),
    onSuccess: (data, sqlId) => {
      // Invalidate and refetch
      queryClient.invalidateQueries({ queryKey: ['query', sqlId] });
    },
  });
}
```

## State Management

### useState for Local State
```typescript
const [isOpen, setIsOpen] = useState(false);
const [selectedQuery, setSelectedQuery] = useState<Query | null>(null);
```

### Context for Global State
```typescript
// ConnectionContext.tsx
interface ConnectionContextValue {
  connectionId: string | null;
  setConnectionId: (id: string) => void;
  isConnected: boolean;
}

const ConnectionContext = createContext<ConnectionContextValue | undefined>(
  undefined
);

export function ConnectionProvider({ children }: { children: React.ReactNode }) {
  const [connectionId, setConnectionId] = useState<string | null>(null);
  const isConnected = connectionId !== null;

  const value = { connectionId, setConnectionId, isConnected };

  return (
    <ConnectionContext.Provider value={value}>
      {children}
    </ConnectionContext.Provider>
  );
}

export function useConnection() {
  const context = useContext(ConnectionContext);
  if (!context) {
    throw new Error('useConnection must be used within ConnectionProvider');
  }
  return context;
}
```

## Event Handlers

### Naming
- **Props**: `on[EventName]`
- **Handlers**: `handle[EventName]`

```typescript
interface QueryCardProps {
  query: Query;
  onQueryClick: (sqlId: string) => void;
  onQueryDelete: (sqlId: string) => void;
}

export const QueryCard: React.FC<QueryCardProps> = ({
  query,
  onQueryClick,
  onQueryDelete
}) => {
  const handleClick = () => {
    onQueryClick(query.sqlId);
  };

  const handleDelete = (e: React.MouseEvent) => {
    e.stopPropagation();
    onQueryDelete(query.sqlId);
  };

  return (
    <div onClick={handleClick}>
      <button onClick={handleDelete}>Delete</button>
    </div>
  );
};
```

## Async Operations

### Use async/await
```typescript
// Good
async function fetchQueryDetails(sqlId: string): Promise<Query> {
  try {
    const response = await axios.get(`/api/queries/${sqlId}`);
    return response.data;
  } catch (error) {
    console.error('Failed to fetch query:', error);
    throw new QueryFetchError(`Failed to fetch query ${sqlId}`);
  }
}

// Bad
function fetchQueryDetails(sqlId: string): Promise<Query> {
  return axios.get(`/api/queries/${sqlId}`)
    .then(response => response.data)
    .catch(error => {
      console.error('Failed to fetch query:', error);
      throw new QueryFetchError(`Failed to fetch query ${sqlId}`);
    });
}
```

### Error Handling
```typescript
// Custom error classes
class QueryFetchError extends Error {
  constructor(message: string, public sqlId: string) {
    super(message);
    this.name = 'QueryFetchError';
  }
}

// Component error handling
const QueryDetails: React.FC<{ sqlId: string }> = ({ sqlId }) => {
  const { data, error, isLoading } = useQuery({
    queryKey: ['query', sqlId],
    queryFn: () => fetchQuery(sqlId),
  });

  if (isLoading) return <Loading />;
  if (error) return <ErrorDisplay error={error} />;
  if (!data) return <NoData />;

  return <div>{data.sqlText}</div>;
};
```

## Type Guards and Validation

```typescript
// Type guard
function isQuery(value: unknown): value is Query {
  return (
    typeof value === 'object' &&
    value !== null &&
    'sqlId' in value &&
    'sqlText' in value &&
    'elapsedTime' in value
  );
}

// Array type guard
function isQueryArray(value: unknown): value is Query[] {
  return Array.isArray(value) && value.every(isQuery);
}

// Usage
const processResponse = (response: unknown) => {
  if (!isQueryArray(response)) {
    throw new Error('Invalid response format');
  }
  // response is now typed as Query[]
  return response.map(q => q.sqlId);
};
```

## Comments and Documentation

### JSDoc for Complex Functions
```typescript
/**
 * Calculates the performance impact score for a query.
 *
 * The score is calculated based on elapsed time, executions, and
 * resource consumption (CPU, I/O). Higher scores indicate queries
 * that should be prioritized for tuning.
 *
 * @param query - The query to analyze
 * @param weights - Optional weights for score calculation
 * @returns Performance impact score (0-100)
 *
 * @example
 * ```ts
 * const score = calculateImpactScore(query, { elapsed: 0.5, cpu: 0.3, io: 0.2 });
 * console.log(score); // 85.5
 * ```
 */
function calculateImpactScore(
  query: Query,
  weights?: { elapsed: number; cpu: number; io: number }
): number {
  // Implementation
}
```

### Component Documentation
```typescript
/**
 * Displays an execution plan as an interactive tree.
 *
 * Highlights costly operations and allows drilling down into
 * operation details. Supports plan comparison when a historical
 * plan is provided.
 */
export const ExecutionPlanTree: React.FC<ExecutionPlanTreeProps> = ({
  plan,
  historicalPlan,
  onOperationClick,
}) => {
  // Implementation
};
```

## Performance Optimization

### React.memo for Expensive Components
```typescript
export const QueryCard = React.memo<QueryCardProps>(({ query, onClick }) => {
  return (
    <div onClick={() => onClick(query.sqlId)}>
      {query.sqlText}
    </div>
  );
});

QueryCard.displayName = 'QueryCard';
```

### useCallback for Functions
```typescript
const QueryList: React.FC<QueryListProps> = ({ queries }) => {
  // Memoize callback to prevent child re-renders
  const handleQuerySelect = useCallback((sqlId: string) => {
    console.log('Selected:', sqlId);
  }, []); // Empty deps - function never changes

  return (
    <div>
      {queries.map(q => (
        <QueryCard key={q.sqlId} query={q} onSelect={handleQuerySelect} />
      ))}
    </div>
  );
};
```

### useMemo for Expensive Computations
```typescript
const QueryAnalysis: React.FC<{ queries: Query[] }> = ({ queries }) => {
  const sortedQueries = useMemo(() => {
    return [...queries].sort((a, b) => b.elapsedTime - a.elapsedTime);
  }, [queries]);

  const totalImpact = useMemo(() => {
    return sortedQueries.reduce((sum, q) => sum + calculateImpact(q), 0);
  }, [sortedQueries]);

  return <div>{/* Render */}</div>;
};
```

## Testing

### Component Tests
```typescript
import { render, screen, fireEvent } from '@testing-library/react';
import { QueryCard } from './QueryCard';

describe('QueryCard', () => {
  const mockQuery: Query = {
    sqlId: 'abc123',
    sqlText: 'SELECT * FROM users',
    elapsedTime: 1000,
    executions: 10,
  };

  it('renders query text', () => {
    render(<QueryCard query={mockQuery} onClick={jest.fn()} />);
    expect(screen.getByText(/SELECT \* FROM users/)).toBeInTheDocument();
  });

  it('calls onClick when clicked', () => {
    const handleClick = jest.fn();
    render(<QueryCard query={mockQuery} onClick={handleClick} />);

    fireEvent.click(screen.getByRole('button'));
    expect(handleClick).toHaveBeenCalledWith('abc123');
  });
});
```

### Hook Tests
```typescript
import { renderHook, waitFor } from '@testing-library/react';
import { useQueries } from './useQueries';

describe('useQueries', () => {
  it('fetches queries on mount', async () => {
    const { result } = renderHook(() => useQueries('conn-123'));

    expect(result.current.isLoading).toBe(true);

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.queries).toHaveLength(5);
  });
});
```

## ESLint Configuration

```json
{
  "extends": [
    "eslint:recommended",
    "plugin:react/recommended",
    "plugin:react-hooks/recommended",
    "plugin:@typescript-eslint/recommended",
    "plugin:@typescript-eslint/recommended-requiring-type-checking",
    "prettier"
  ],
  "rules": {
    "@typescript-eslint/explicit-function-return-type": "warn",
    "@typescript-eslint/no-explicit-any": "error",
    "@typescript-eslint/no-unused-vars": ["error", { "argsIgnorePattern": "^_" }],
    "react/react-in-jsx-scope": "off",
    "react/prop-types": "off"
  }
}
```

## Resources

- [TypeScript Documentation](https://www.typescriptlang.org/docs/)
- [React TypeScript Cheatsheet](https://react-typescript-cheatsheet.netlify.app/)
- [Airbnb JavaScript Style Guide](https://github.com/airbnb/javascript)
- [React Query Documentation](https://tanstack.com/query/latest/docs/react/overview)
