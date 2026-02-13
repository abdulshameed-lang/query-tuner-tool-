/**
 * QueryList component - displays queries in a table with sorting, filtering, and pagination.
 */

import React, { useState } from 'react';
import { Table, Tag, Typography, Space, Alert, Spin, Input, Select, Button, Row, Col } from 'antd';
import type { ColumnsType, TablePaginationConfig } from 'antd/es/table';
import { FilterOutlined, ReloadOutlined } from '@ant-design/icons';
import { Query, QueryFilters, QuerySort, PaginationParams } from '../../types/query';
import { useQueries, formatElapsedTime, formatNumber } from '../../api/queries';

const { Text, Title } = Typography;
const { Search } = Input;

interface QueryListProps {
  onQueryClick?: (sqlId: string) => void;
}

const QueryList: React.FC<QueryListProps> = ({ onQueryClick }) => {
  // State for filters, sort, and pagination
  const [filters, setFilters] = useState<QueryFilters>({
    exclude_system_schemas: true,
  });
  const [sort, setSort] = useState<QuerySort>({
    sort_by: 'elapsed_time',
    order: 'desc',
  });
  const [pagination, setPagination] = useState<PaginationParams>({
    page: 1,
    page_size: 20,
  });

  // Fetch queries using React Query
  const { data, isLoading, isError, error, refetch } = useQueries(filters, sort, pagination);

  // Table columns configuration
  const columns: ColumnsType<Query> = [
    {
      title: 'SQL ID',
      dataIndex: 'sql_id',
      key: 'sql_id',
      width: 150,
      fixed: 'left',
      render: (sqlId: string) => (
        <Text code copyable={{ text: sqlId }}>
          {sqlId}
        </Text>
      ),
    },
    {
      title: 'Schema',
      dataIndex: 'parsing_schema_name',
      key: 'parsing_schema_name',
      width: 120,
    },
    {
      title: 'SQL Text',
      dataIndex: 'sql_text',
      key: 'sql_text',
      ellipsis: true,
      render: (text: string) => (
        <Text ellipsis={{ tooltip: text }} style={{ maxWidth: 300 }}>
          {text}
        </Text>
      ),
    },
    {
      title: 'Executions',
      dataIndex: 'executions',
      key: 'executions',
      width: 120,
      align: 'right',
      sorter: true,
      render: (value: number) => formatNumber(value),
    },
    {
      title: 'Elapsed Time',
      dataIndex: 'elapsed_time',
      key: 'elapsed_time',
      width: 140,
      align: 'right',
      sorter: true,
      render: (value: number) => formatElapsedTime(value),
    },
    {
      title: 'Avg Elapsed',
      dataIndex: 'avg_elapsed_time',
      key: 'avg_elapsed_time',
      width: 140,
      align: 'right',
      sorter: true,
      render: (value: number) => formatElapsedTime(value),
    },
    {
      title: 'CPU Time',
      dataIndex: 'cpu_time',
      key: 'cpu_time',
      width: 140,
      align: 'right',
      sorter: true,
      render: (value: number) => formatElapsedTime(value),
    },
    {
      title: 'Buffer Gets',
      dataIndex: 'buffer_gets',
      key: 'buffer_gets',
      width: 120,
      align: 'right',
      sorter: true,
      render: (value: number) => formatNumber(value),
    },
    {
      title: 'Disk Reads',
      dataIndex: 'disk_reads',
      key: 'disk_reads',
      width: 120,
      align: 'right',
      sorter: true,
      render: (value: number) => formatNumber(value),
    },
    {
      title: 'Impact Score',
      dataIndex: 'impact_score',
      key: 'impact_score',
      width: 120,
      align: 'right',
      sorter: true,
      render: (score: number, record: Query) => (
        <Space>
          <Text strong>{score.toFixed(2)}</Text>
          {record.needs_tuning && (
            <Tag color="red" style={{ margin: 0 }}>
              TUNE
            </Tag>
          )}
        </Space>
      ),
    },
  ];

  // Handle table change (pagination, sorting)
  const handleTableChange = (
    paginationConfig: TablePaginationConfig,
    _filters: any,
    sorter: any
  ) => {
    // Update pagination
    if (paginationConfig.current && paginationConfig.pageSize) {
      setPagination({
        page: paginationConfig.current,
        page_size: paginationConfig.pageSize,
      });
    }

    // Update sorting
    if (sorter.field) {
      setSort({
        sort_by: sorter.field,
        order: sorter.order === 'ascend' ? 'asc' : 'desc',
      });
    }
  };

  // Handle search
  const handleSearch = (value: string) => {
    setFilters((prev) => ({
      ...prev,
      sql_text_contains: value || undefined,
    }));
    setPagination((prev) => ({ ...prev, page: 1 }));
  };

  // Handle filter changes
  const handleFilterChange = (key: keyof QueryFilters, value: any) => {
    setFilters((prev) => ({
      ...prev,
      [key]: value,
    }));
    setPagination((prev) => ({ ...prev, page: 1 }));
  };

  // Handle row click
  const handleRowClick = (record: Query) => {
    if (onQueryClick) {
      onQueryClick(record.sql_id);
    }
  };

  return (
    <div style={{ padding: '24px' }}>
      <Space direction="vertical" size="large" style={{ width: '100%' }}>
        {/* Header */}
        <Row justify="space-between" align="middle">
          <Col>
            <Title level={3} style={{ margin: 0 }}>
              SQL Queries
            </Title>
          </Col>
          <Col>
            <Button icon={<ReloadOutlined />} onClick={() => refetch()}>
              Refresh
            </Button>
          </Col>
        </Row>

        {/* Filters */}
        <Row gutter={[16, 16]}>
          <Col xs={24} sm={12} md={8}>
            <Search
              placeholder="Search SQL text"
              allowClear
              onSearch={handleSearch}
              style={{ width: '100%' }}
            />
          </Col>
          <Col xs={24} sm={12} md={8}>
            <Input
              placeholder="Min elapsed time (μs)"
              type="number"
              min={0}
              onChange={(e) =>
                handleFilterChange(
                  'min_elapsed_time',
                  e.target.value ? parseFloat(e.target.value) : undefined
                )
              }
              prefix={<FilterOutlined />}
            />
          </Col>
          <Col xs={24} sm={12} md={8}>
            <Input
              placeholder="Min executions"
              type="number"
              min={0}
              onChange={(e) =>
                handleFilterChange(
                  'min_executions',
                  e.target.value ? parseInt(e.target.value) : undefined
                )
              }
              prefix={<FilterOutlined />}
            />
          </Col>
          <Col xs={24} sm={12} md={8}>
            <Input
              placeholder="Schema name"
              allowClear
              onChange={(e) => handleFilterChange('schema', e.target.value || undefined)}
              prefix={<FilterOutlined />}
            />
          </Col>
          <Col xs={24} sm={12} md={8}>
            <Select
              style={{ width: '100%' }}
              value={filters.exclude_system_schemas}
              onChange={(value) => handleFilterChange('exclude_system_schemas', value)}
            >
              <Select.Option value={true}>Exclude System Schemas</Select.Option>
              <Select.Option value={false}>Include System Schemas</Select.Option>
            </Select>
          </Col>
        </Row>

        {/* Error Alert */}
        {isError && (
          <Alert
            message="Error Loading Queries"
            description={
              error?.response?.data?.message ||
              error?.message ||
              'Failed to fetch queries from database'
            }
            type="error"
            showIcon
            closable
          />
        )}

        {/* Table */}
        <Spin spinning={isLoading}>
          <Table
            columns={columns}
            dataSource={data?.data || []}
            rowKey="sql_id"
            pagination={{
              current: pagination.page,
              pageSize: pagination.page_size,
              total: data?.pagination.total_items || 0,
              showTotal: (total, range) => `${range[0]}-${range[1]} of ${total} queries`,
              showSizeChanger: true,
              pageSizeOptions: ['10', '20', '50', '100'],
            }}
            onChange={handleTableChange}
            onRow={(record) => ({
              onClick: () => handleRowClick(record),
              style: { cursor: 'pointer' },
            })}
            scroll={{ x: 1500 }}
            loading={isLoading}
          />
        </Spin>

        {/* Summary Info */}
        {data && (
          <Text type="secondary">
            Showing {data.data.length} queries (page {data.pagination.page} of{' '}
            {data.pagination.total_pages})
          </Text>
        )}
      </Space>
    </div>
  );
};

export default QueryList;
