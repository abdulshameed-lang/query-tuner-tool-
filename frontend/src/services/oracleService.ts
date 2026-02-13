/**
 * Oracle database operations service
 */

import apiClient from './apiClient';

export interface Query {
  sql_id: string;
  sql_text: string;
  elapsed_time: number;
  cpu_time: number;
  executions: number;
  disk_reads: number;
  buffer_gets: number;
  rows_processed: number;
  first_load_time: string;
  last_active_time: string;
}

export interface ExecutionPlan {
  sql_id: string;
  plan_hash_value: number;
  operations: any[];
  total_cost: number;
}

export interface WaitEvent {
  event: string;
  wait_class: string;
  total_waits: number;
  time_waited: number;
  average_wait: number;
}

export interface Bug {
  bug_number: string;
  title: string;
  severity: string;
  description: string;
  workaround: string;
  affected_versions: string[];
  sql_ids: string[];
}

export interface AWRSnapshot {
  snap_id: number;
  begin_time: string;
  end_time: string;
}

class OracleService {
  // Get current connection from localStorage
  private getConnectionParams() {
    const connections = JSON.parse(localStorage.getItem('database_connections') || '[]');
    const defaultConn = connections.find((c: any) => c.is_default) || connections[0];

    if (!defaultConn) {
      throw new Error('No database connection configured');
    }

    return {
      host: defaultConn.host,
      port: defaultConn.port,
      service_name: defaultConn.service_name,
      sid: defaultConn.sid,
      username: defaultConn.username,
      password: defaultConn.password,
    };
  }

  async testConnection(connectionId?: number) {
    const params = this.getConnectionParams();
    const response = await apiClient.post('/user-connections/test', params);
    return response.data;
  }

  // Query Tuning APIs
  async getTopQueries(limit = 20, orderBy = 'elapsed_time') {
    const response = await apiClient.get('/queries', {
      params: { limit, order_by: orderBy },
    });
    return response.data.queries || [];
  }

  async getQueryDetails(sqlId: string) {
    const response = await apiClient.get(`/queries/${sqlId}`);
    return response.data;
  }

  // Execution Plans
  async getExecutionPlan(sqlId: string) {
    const response = await apiClient.get(`/execution-plans/${sqlId}`);
    return response.data;
  }

  async compareExecutionPlans(sqlId: string, planHashValue1: number, planHashValue2: number) {
    const response = await apiClient.post('/plan-comparison/compare', {
      sql_id: sqlId,
      plan_hash_value_1: planHashValue1,
      plan_hash_value_2: planHashValue2,
    });
    return response.data;
  }

  // Wait Events
  async getSystemWaitEvents(limit = 20) {
    const response = await apiClient.get('/wait-events/current/system', {
      params: { top_n: limit },
    });
    return response.data.events || [];
  }

  async getSessionWaitEvents(sid: number) {
    const response = await apiClient.get(`/wait-events/session/${sid}`);
    return response.data;
  }

  // Bug Detection
  async detectBugs() {
    const response = await apiClient.get('/bugs');
    return response.data.bugs || [];
  }

  async getBugDetails(sqlId: string) {
    const response = await apiClient.get(`/bugs/${sqlId}`);
    return response.data;
  }

  // AWR/ASH Reports
  async getAWRSnapshots(daysBack = 7) {
    const response = await apiClient.get('/awr-ash/snapshots', {
      params: { days_back: daysBack },
    });
    return response.data.snapshots || [];
  }

  async generateAWRReport(beginSnapId: number, endSnapId: number) {
    const response = await apiClient.get('/awr-ash/report', {
      params: { begin_snap_id: beginSnapId, end_snap_id: endSnapId },
    });
    return response.data;
  }

  async getASHActivity(minutes = 60) {
    const response = await apiClient.get('/awr-ash/ash/activity', {
      params: { minutes },
    });
    return response.data;
  }

  // Deadlocks
  async getDeadlocks() {
    const response = await apiClient.get('/deadlocks');
    return response.data.deadlocks || [];
  }

  // Recommendations
  async getRecommendations(sqlId: string) {
    const response = await apiClient.get(`/recommendations/${sqlId}`);
    return response.data;
  }
}

export const oracleService = new OracleService();
