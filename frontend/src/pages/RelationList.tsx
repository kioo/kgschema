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
import { relationApi } from '../api/relation';
import { entityApi } from '../api/entity';
import type { Relation, RelationCreateParams } from '../api/relation';

const { TextArea } = Input;

const RelationList: React.FC = () => {
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [form] = Form.useForm();
    const queryClient = useQueryClient();
    const navigate = useNavigate();
    const [pagination, setPagination] = useState({ page: 1, size: 20 });
    const [search, setSearch] = useState('');
    const [statusFilter, setStatusFilter] = useState<string | undefined>(undefined);

    // Fetch Relations
    const { data, isLoading } = useQuery({
        queryKey: ['relations', pagination, search, statusFilter],
        queryFn: () => relationApi.list({ ...pagination, search, status: statusFilter as any }),
    });

    // Fetch Entities for select
    const { data: entitiesData } = useQuery({
        queryKey: ['entities-select'],
        queryFn: () => entityApi.list({ page: 1, size: 100 }),
    });

    // Create Relation Mutation
    const createMutation = useMutation({
        mutationFn: relationApi.create,
        onSuccess: () => {
            message.success('Relation created');
            setIsModalOpen(false);
            form.resetFields();
            queryClient.invalidateQueries({ queryKey: ['relations'] });
        },
    });

    // Delete Relation Mutation
    const deleteMutation = useMutation({
        mutationFn: relationApi.delete,
        onSuccess: () => {
            message.success('Relation deleted');
            queryClient.invalidateQueries({ queryKey: ['relations'] });
        },
    });

    const handleSubmit = async () => {
        const values = await form.validateFields();
        await createMutation.mutateAsync(values as RelationCreateParams);
    };

    const columns = [
        {
            title: 'Relation Code',
            dataIndex: 'relation_code',
            key: 'relation_code',
            render: (text: string, record: Relation) => (
                <Button type="link" onClick={() => navigate(`/relations/${record.id}`)}>
                    {text}
                </Button>
            ),
        },
        {
            title: 'Relation Name',
            dataIndex: 'relation_name',
            key: 'relation_name',
        },
        {
            title: 'Head → Tail',
            key: 'entities',
            render: (_: any, record: Relation) => (
                <span>
                    <Tag color="blue">{record.head_entity_code}</Tag>
                    →
                    <Tag color="green">{record.tail_entity_code}</Tag>
                </span>
            ),
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
            title: 'Actions',
            key: 'action',
            render: (_: any, record: Relation) => (
                <Space size="middle">
                    <Button type="link" onClick={() => navigate(`/relations/${record.id}`)}>
                        View
                    </Button>
                    <Popconfirm
                        title="Delete this relation?"
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
                <h2>Relation Management</h2>
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
                        Create Relation
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
                title="Create Relation"
                open={isModalOpen}
                onOk={handleSubmit}
                onCancel={() => setIsModalOpen(false)}
                confirmLoading={createMutation.isPending}
                width={600}
            >
                <Form form={form} layout="vertical">
                    <Form.Item
                        name="relation_code"
                        label="Relation Code"
                        rules={[
                            { required: true, message: 'Please enter relation code' },
                            { pattern: /^[a-zA-Z0-9_]+$/, message: 'Only letters, numbers, and underscores allowed' },
                        ]}
                    >
                        <Input placeholder="e.g., WORKS_AT" />
                    </Form.Item>

                    <Form.Item
                        name="relation_name"
                        label="Relation Name"
                        rules={[{ required: true, message: 'Please enter relation name' }]}
                    >
                        <Input placeholder="e.g., 就职于" />
                    </Form.Item>

                    <Form.Item name="relation_name_en" label="Relation Name (EN)">
                        <Input placeholder="e.g., Works At" />
                    </Form.Item>

                    <Form.Item
                        name="head_entity_id"
                        label="Head Entity"
                        rules={[{ required: true, message: 'Please select head entity' }]}
                    >
                        <Select placeholder="Select head entity" showSearch optionFilterProp="children">
                            {entitiesData?.items.map((e) => (
                                <Select.Option key={e.id} value={e.id}>
                                    {e.entity_code} - {e.entity_name}
                                </Select.Option>
                            ))}
                        </Select>
                    </Form.Item>

                    <Form.Item
                        name="tail_entity_id"
                        label="Tail Entity"
                        rules={[{ required: true, message: 'Please select tail entity' }]}
                    >
                        <Select placeholder="Select tail entity" showSearch optionFilterProp="children">
                            {entitiesData?.items.map((e) => (
                                <Select.Option key={e.id} value={e.id}>
                                    {e.entity_code} - {e.entity_name}
                                </Select.Option>
                            ))}
                        </Select>
                    </Form.Item>

                    <Form.Item name="description" label="Description">
                        <TextArea rows={3} placeholder="Description..." />
                    </Form.Item>
                </Form>
            </Modal>
        </div>
    );
};

export default RelationList;
