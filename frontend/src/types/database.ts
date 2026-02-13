/**
 * Database types and interfaces
 */

export enum DatabaseType {
  ORACLE = 'oracle',
  POSTGRESQL = 'postgresql',
  SQLSERVER = 'sqlserver',
  MYSQL = 'mysql',
  MONGODB = 'mongodb',
  REDIS = 'redis',
}

export interface DatabaseConnection {
  id?: number;
  connection_name: string;
  database_type: DatabaseType;
  host: string;
  port: number;
  database_name?: string;
  service_name?: string;
  sid?: string;
  username: string;
  password: string;
  connection_string?: string;
  ssl_enabled?: boolean;
  description?: string;
  is_default: boolean;
  is_active?: boolean;
  created_at?: string;
  last_connected_at?: string;
}

export interface DatabaseFeatures {
  supportsQueryTuning: boolean;
  supportsBugDetection: boolean;
  supportsAWR: boolean;
  supportsExecutionPlans: boolean;
  supportsWaitEvents: boolean;
  supportsDeadlockDetection: boolean;
}

export const DATABASE_FEATURES: Record<DatabaseType, DatabaseFeatures> = {
  [DatabaseType.ORACLE]: {
    supportsQueryTuning: true,
    supportsBugDetection: true,
    supportsAWR: true,
    supportsExecutionPlans: true,
    supportsWaitEvents: true,
    supportsDeadlockDetection: true,
  },
  [DatabaseType.POSTGRESQL]: {
    supportsQueryTuning: true,
    supportsBugDetection: true,
    supportsAWR: false,
    supportsExecutionPlans: true,
    supportsWaitEvents: true,
    supportsDeadlockDetection: true,
  },
  [DatabaseType.SQLSERVER]: {
    supportsQueryTuning: true,
    supportsBugDetection: true,
    supportsAWR: false,
    supportsExecutionPlans: true,
    supportsWaitEvents: true,
    supportsDeadlockDetection: true,
  },
  [DatabaseType.MYSQL]: {
    supportsQueryTuning: true,
    supportsBugDetection: false,
    supportsAWR: false,
    supportsExecutionPlans: true,
    supportsWaitEvents: false,
    supportsDeadlockDetection: true,
  },
  [DatabaseType.MONGODB]: {
    supportsQueryTuning: true,
    supportsBugDetection: false,
    supportsAWR: false,
    supportsExecutionPlans: true,
    supportsWaitEvents: false,
    supportsDeadlockDetection: false,
  },
  [DatabaseType.REDIS]: {
    supportsQueryTuning: false,
    supportsBugDetection: false,
    supportsAWR: false,
    supportsExecutionPlans: false,
    supportsWaitEvents: false,
    supportsDeadlockDetection: false,
  },
};

export const DATABASE_ICONS: Record<DatabaseType, string> = {
  [DatabaseType.ORACLE]: '🔶',
  [DatabaseType.POSTGRESQL]: '🐘',
  [DatabaseType.SQLSERVER]: '🔷',
  [DatabaseType.MYSQL]: '🐬',
  [DatabaseType.MONGODB]: '🍃',
  [DatabaseType.REDIS]: '⚡',
};

export const DATABASE_LABELS: Record<DatabaseType, string> = {
  [DatabaseType.ORACLE]: 'Oracle Database',
  [DatabaseType.POSTGRESQL]: 'PostgreSQL',
  [DatabaseType.SQLSERVER]: 'SQL Server',
  [DatabaseType.MYSQL]: 'MySQL',
  [DatabaseType.MONGODB]: 'MongoDB',
  [DatabaseType.REDIS]: 'Redis',
};

export const DATABASE_DEFAULT_PORTS: Record<DatabaseType, number> = {
  [DatabaseType.ORACLE]: 1521,
  [DatabaseType.POSTGRESQL]: 5432,
  [DatabaseType.SQLSERVER]: 1433,
  [DatabaseType.MYSQL]: 3306,
  [DatabaseType.MONGODB]: 27017,
  [DatabaseType.REDIS]: 6379,
};
