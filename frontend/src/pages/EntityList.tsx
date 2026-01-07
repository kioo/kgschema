import React, { useState } from 'react';
import {
    Table,
    Button,
    Space,
    Tag,
    Modal,
    Form,
    Input,
    message,
    Popconfirm,
    Select,
} from 'antd';
import { PlusOutlined, SearchOutlined } from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { entityApi } from '../api/entity';
import type { Entity, EntityCreateParams } from '../api/entity';

const { TextArea } = Input;

const EntityList: React.FC = () => {
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [form] = Form.useForm();
    const queryClient = useQueryClient();
    const navigate = useNavigate();
    const [pagination, setPagination] = useState({ page: 1, size: 20 });
    const [search, setSearch] = useState('');
    const [statusFilter, setStatusFilter] = useState<string | undefined>(undefined);

    // Fetch Entities
    const { data, isLoading } = useQuery({
        queryKey: ['entities', pagination, search, statusFilter],
        queryFn: () => entityApi.list({ ...pagination, search, status: statusFilter as any }),
    });

    // Create Entity Mutation
    const createMutation = useMutation({
        mutationFn: entityApi.create,
        onSuccess: () => {
            message.success('Entity created');
            setIsModalOpen(false);
            form.resetFields();
            queryClient.invalidateQueries({ queryKey: ['entities'] });
        },
    });

    // Delete Entity Mutation
    const deleteMutation = useMutation({
        mutationFn: entityApi.delete,
        onSuccess: () => {
            message.success('Entity deleted');
            queryClient.invalidateQueries({ queryKey: ['entities'] });
        },
    });

    const handleSubmit = async () => {
        const values = await form.validateFields();
        await createMutation.mutateAsync(values as EntityCreateParams);
    };

    const columns = [
        {
            title: 'Entity Code',
            dataIndex: 'entity_code',
            key: 'entity_code',
            render: (text: string, record: Entity) => (
                <Button type="link" onClick={() => navigate(`/entities/${record.id}`)}>
                    {text}
                </Button>
            ),
        },
        {
            title: 'Entity Name',
            dataIndex: 'entity_name',
            key: 'entity_name',
        },
        {
            title: 'Status',
            dataIndex: 'status',
            key: 'status',
            render: (status: string) => (
                <Tag color={status === 'ACTIVE' ? 'success' : 'default'}>{status}</Tag>
            ),
        },
        {
            title: 'Created At',
            dataIndex: 'created_at',
            key: 'created_at',
            render: (text: string) => new Date(text).toLocaleString(),
        },
        {
            title: 'Actions',
            key: 'action',
            render: (_: any, record: Entity) => (
                <Space size="middle">
                    <Button type="link" onClick={() => navigate(`/entities/${record.id}`)}>
                        View
                    </Button>
                    <Popconfirm
                        title="Delete this entity?"
                        onConfirm={() => deleteMutation.mutateAsync(record.id)}
                    >
                        <Button type="link" danger>
                            Delete
                        </Button>
                    </Popconfirm>
                </Space>
            ),
        },
    ];

    return (
        <div>
            <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <h2>Entity Management</h2>
                <Space>
                    <Input
                        placeholder="Search..."
                        prefix={<SearchOutlined />}
                        value={search}
                        onChange={(e) => setSearch(e.target.value)}
                        style={{ width: 200 }}
                        allowClear
                    />
                    <Select
                        placeholder="Status"
                        value={statusFilter}
                        onChange={setStatusFilter}
                        style={{ width: 120 }}
                        allowClear
                    >
                        <Select.Option value="DRAFT">DRAFT</Select.Option>
                        <Select.Option value="ACTIVE">ACTIVE</Select.Option>
                    </Select>
                    <Button
                        type="primary"
                        icon={<PlusOutlined />}
                        onClick={() => {
                            form.resetFields();
                            setIsModalOpen(true);
                        }}
                    >
                        Create Entity
                    </Button>
                </Space>
            </div>

            <Table
                columns={columns}
                dataSource={data?.items}
                rowKey="id"
                loading={isLoading}
                pagination={{
                    current: data?.page,
                    pageSize: data?.size,
                    total: data?.total,
                    onChange: (p, s) => setPagination({ page: p, size: s }),
                    showSizeChanger: true,
                }}
            />

            <Modal
                title="Create Entity"
                open={isModalOpen}
                onOk={handleSubmit}
                onCancel={() => setIsModalOpen(false)}
                confirmLoading={createMutation.isPending}
            >
                <Form form={form} layout="vertical">
                    <Form.Item
                        name="entity_code"
                        label="Entity Code"
                        rules={[
                            { required: true, message: 'Please enter entity code' },
                            { pattern: /^[a-zA-Z0-9_]+$/, message: 'Only letters, numbers, and underscores allowed' },
                        ]}
                    >
                        <Input placeholder="e.g., Person" />
                    </Form.Item>

                    <Form.Item
                        name="entity_name"
                        label="Entity Name"
                        rules={[{ required: true, message: 'Please enter entity name' }]}
                    >
                        <Input placeholder="e.g., 人物" />
                    </Form.Item>

                    <Form.Item name="entity_name_en" label="Entity Name (EN)">
                        <Input placeholder="e.g., Person" />
                    </Form.Item>

                    <Form.Item name="description" label="Description">
                        <TextArea rows={3} placeholder="Description..." />
                    </Form.Item>
                </Form>
            </Modal>
        </div>
    );
};

export default EntityList;
