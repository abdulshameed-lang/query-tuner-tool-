# Query Tuner Tool - Frontend

React + TypeScript frontend for Oracle Database Performance Tuning Tool.

## Setup

### Prerequisites

- Node.js 18+
- npm or yarn

### Installation

```bash
# Install dependencies
npm install

# or
yarn install
```

### Development

```bash
# Start development server
npm run dev

# The app will be available at http://localhost:3000
```

### Building

```bash
# Build for production
npm run build

# Preview production build
npm run preview
```

### Code Quality

```bash
# Lint code
npm run lint

# Fix lint issues
npm run lint:fix

# Format code
npm run format

# Type check
npm run type-check
```

### Testing

```bash
# Run tests
npm test

# Run tests with coverage
npm run test:coverage
```

## Project Structure

```
frontend/
├── public/              # Static assets
├── src/
│   ├── api/            # API client
│   ├── components/     # React components
│   │   ├── common/     # Common UI components
│   │   ├── queries/    # Query-related components
│   │   └── ...
│   ├── pages/          # Page components
│   ├── hooks/          # Custom React hooks
│   ├── types/          # TypeScript types
│   ├── utils/          # Utility functions
│   ├── App.tsx         # Root component
│   ├── main.tsx        # Entry point
│   └── index.css       # Global styles
├── package.json
├── tsconfig.json       # TypeScript configuration
├── vite.config.ts      # Vite configuration
└── README.md
```

## Technology Stack

- **React 18** - UI library
- **TypeScript** - Type safety
- **Vite** - Build tool
- **React Query** - Server state management
- **Ant Design** - UI components
- **Recharts** - Data visualization
- **React Router** - Routing
- **Axios** - HTTP client

## Contributing

See [../docs/development/CONTRIBUTING.md](../docs/development/CONTRIBUTING.md) for contribution guidelines.
