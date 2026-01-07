import React, { useState } from 'react';
import {
    Card,
    Descriptions,
    Button,
    Space,
    Tag,
    Table,
    Modal,
    Form,
    Input,
    Select,
    Switch,
    message,
    Popconfirm,
    Spin,
    Row,
    Col,
    Typography,
    Tooltip,
    Divider,
} from 'antd';
import {
    ArrowLeftOutlined,
    PlusOutlined,
    EditOutlined,
    DeleteOutlined,
    CodeOutlined,
    GlobalOutlined,
} from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useParams, useNavigate } from 'react-router-dom';
import { entityApi } from '../api/entity';
import type { EntityProperty, EntityUpdateParams, PropertyCreateParams, PropertyUpdateParams } from '../api/entity';

const { TextArea } = Input;
const { Title, Text, Paragraph } = Typography;

const EntityDetail: React.FC = () => {
    const { id } = useParams<{ id: string }>();
    const navigate = useNavigate();
    const queryClient = useQueryClient();
    const [editModalOpen, setEditModalOpen] = useState(false);
    const [propModalOpen, setPropModalOpen] = useState(false);
    const [editingProp, setEditingProp] = useState<EntityProperty | null>(null);
    const [entityForm] = Form.useForm();
    const [propForm] = Form.useForm();

    // Fetch Entity Detail
    const { data: entity, isLoading } = useQuery({
        queryKey: ['entity', id],
        queryFn: () => entityApi.get(id!),
        enabled: !!id,
    });

    // Update Entity Mutation
    const updateMutation = useMutation({
        mutationFn: (data: EntityUpdateParams) => entityApi.update(id!, data),
        onSuccess: () => {
            message.success('Entity updated');
            setEditModalOpen(false);
            queryClient.invalidateQueries({ queryKey: ['entity', id] });
        },
    });

    // Create Property Mutation
    const createPropMutation = useMutation({
        mutationFn: (data: PropertyCreateParams) => entityApi.createProperty(id!, data),
        onSuccess: () => {
            message.success('Property created');
            setPropModalOpen(false);
            propForm.resetFields();
            queryClient.invalidateQueries({ queryKey: ['entity', id] });
        },
    });

    // Update Property Mutation
    const updatePropMutation = useMutation({
        mutationFn: ({ propId, data }: { propId: string; data: PropertyUpdateParams }) =>
            entityApi.updateProperty(id!, propId, data),
        onSuccess: () => {
            message.success('Property updated');
            setPropModalOpen(false);
            setEditingProp(null);
            propForm.resetFields();
            queryClient.invalidateQueries({ queryKey: ['entity', id] });
        },
    });

    // Delete Property Mutation
    const deletePropMutation = useMutation({
        mutationFn: (propId: string) => entityApi.deleteProperty(id!, propId),
        onSuccess: () => {
            message.success('Property deleted');
            queryClient.invalidateQueries({ queryKey: ['entity', id] });
        },
    });

    const handleEditEntity = () => {
        entityForm.setFieldsValue({
            entity_name: entity?.entity_name,
            entity_name_en: entity?.entity_name_en,
            description: entity?.description,
            status: entity?.status,
        });
        setEditModalOpen(true);
    };

    const handleEditProp = (prop: EntityProperty) => {
        setEditingProp(prop);
        propForm.setFieldsValue({
            prop_code: prop.prop_code,
            prop_name: prop.prop_name,
            prop_name_en: prop.prop_name_en,
            data_type: prop.data_type,
            is_required: prop.is_required,
            display_order: prop.display_order,
        });
        setPropModalOpen(true);
    };

    const handlePropSubmit = async () => {
        const values = await propForm.validateFields();
        if (editingProp) {
            await updatePropMutation.mutateAsync({ propId: editingProp.id, data: values });
        } else {
            await createPropMutation.mutateAsync(values as PropertyCreateParams);
        }
    };

    const getDataTypeColor = (type: string) => {
        switch (type) {
            case 'STRING': return 'blue';
            case 'INTEGER': return 'cyan';
            case 'FLOAT': return 'geekblue';
            case 'BOOLEAN': return 'green';
            case 'ENUM': return 'purple';
            default: return 'default';
        }
    };

    const propColumns = [
        {
            title: 'Code',
            dataIndex: 'prop_code',
            key: 'prop_code',
            render: (text: string) => <Text strong>{text}</Text>
        },
        {
            title: 'Name',
            dataIndex: 'prop_name',
            key: 'prop_name',
            render: (text: string, record: EntityProperty) => (
                <Space direction="vertical" size={0}>
                    <Text>{text}</Text>
                    {record.prop_name_en && <Text type="secondary" style={{ fontSize: 12 }}>{record.prop_name_en}</Text>}
                </Space>
            )
        },
        {
            title: 'Type',
            dataIndex: 'data_type',
            key: 'data_type',
            render: (t: string) => <Tag color={getDataTypeColor(t)}>{t}</Tag>
        },
        {
            title: 'Required',
            dataIndex: 'is_required',
            key: 'is_required',
            render: (r: boolean) => r ? <Tag color="red">Required</Tag> : <Tag color="default">Optional</Tag>
        },
        {
            title: 'Order',
            dataIndex: 'display_order',
            key: 'display_order',
            width: 80,
            align: 'center' as const,
        },
        {
            title: 'Actions',
            key: 'action',
            width: 120,
            render: (_: any, record: EntityProperty) => (
                <Space size="small">
                    <Tooltip title="Edit">
                        <Button type="text" icon={<EditOutlined />} onClick={() => handleEditProp(record)} />
                    </Tooltip>
                    <Popconfirm title="Delete this property?" onConfirm={() => deletePropMutation.mutateAsync(record.id)}>
                        <Tooltip title="Delete">
                            <Button type="text" danger icon={<DeleteOutlined />} />
                        </Tooltip>
                    </Popconfirm>
                </Space>
            ),
        },
    ];

    if (isLoading) return <Spin size="large" style={{ display: 'block', margin: '40px auto' }} />;
    if (!entity) return <div>Entity not found</div>;

    return (
        <div style={{ padding: '0 12px' }}>
            {/* Header Section */}
            <div style={{ marginBottom: 24, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Space align="start" size={16}>
                    <Button
                        icon={<ArrowLeftOutlined />}
                        onClick={() => navigate('/entities')}
                        style={{ border: 'none', background: 'transparent', boxShadow: 'none', padding: 0 }}
                    />
                    <div>
                        <Space align="center">
                            <Title level={3} style={{ margin: 0 }}>{entity.entity_name}</Title>
                            <Tag color={entity.status === 'ACTIVE' ? 'success' : 'warning'}>{entity.status}</Tag>
                        </Space>
                        <Space size={8} style={{ marginTop: 4 }}>
                            <Text type="secondary"><CodeOutlined /> {entity.entity_code}</Text>
                            {entity.entity_name_en && (
                                <>
                                    <Divider type="vertical" />
                                    <Text type="secondary"><GlobalOutlined /> {entity.entity_name_en}</Text>
                                </>
                            )}
                        </Space>
                    </div>
                </Space>
                <Space>
                    <Button icon={<EditOutlined />} onClick={handleEditEntity}>Edit Entity</Button>
                </Space>
            </div>

            <Row gutter={24}>
                {/* Left Column: Main Content */}
                <Col span={16}>
                    {/* Basic Info Card */}
                    <Card bordered={false} style={{ marginBottom: 24, boxShadow: '0 2px 8px rgba(0,0,0,0.05)' }}>
                        <Descriptions title="Basic Information" column={1} labelStyle={{ width: '140px', color: '#8c8c8c' }}>
                            <Descriptions.Item label="Description">
                                {entity.description ? (
                                    <Paragraph style={{ margin: 0 }}>{entity.description}</Paragraph>
                                ) : (
                                    <Text type="secondary" italic>No description provided.</Text>
                                )}
                            </Descriptions.Item>
                        </Descriptions>
                    </Card>

                    {/* Properties Card */}
                    <Card
                        title="Entity Properties"
                        bordered={false}
                        style={{ boxShadow: '0 2px 8px rgba(0,0,0,0.05)' }}
                        extra={
                            <Button type="primary" icon={<PlusOutlined />} onClick={() => {
                                setEditingProp(null);
                                propForm.resetFields();
                                setPropModalOpen(true);
                            }}>
                                Add Property
                            </Button>
                        }
                    >
                        <Table
                            columns={propColumns}
                            dataSource={entity.properties}
                            rowKey="id"
                            pagination={false}
                            size="middle"
                        />
                    </Card>
                </Col>

                {/* Right Column: Metadata */}
                <Col span={8}>
                    <Card title="System Metadata" bordered={false} style={{ marginBottom: 24, boxShadow: '0 2px 8px rgba(0,0,0,0.05)' }}>
                        <Descriptions column={1} size="small" layout="vertical">
                            <Descriptions.Item label="Entity ID">
                                <Paragraph copyable style={{ margin: 0 }} type="secondary">{entity.id}</Paragraph>
                            </Descriptions.Item>
                            <Descriptions.Item label="Created At">
                                <Text strong>{new Date(entity.created_at).toLocaleString()}</Text>
                            </Descriptions.Item>
                            <Descriptions.Item label="Last Updated">
                                <Text strong>{new Date(entity.updated_at).toLocaleString()}</Text>
                            </Descriptions.Item>
                        </Descriptions>
                    </Card>

                    <Card title="Statistics" bordered={false} style={{ boxShadow: '0 2px 8px rgba(0,0,0,0.05)' }}>
                        <Row gutter={16}>
                            <Col span={12}>
                                <div style={{ textAlign: 'center' }}>
                                    <Text type="secondary">Properties</Text>
                                    <Title level={2} style={{ margin: '8px 0' }}>{entity.properties.length}</Title>
                                </div>
                            </Col>
                            {/* Potential future stats: Relations count */}
                        </Row>
                    </Card>
                </Col>
            </Row>

            {/* Edit Entity Modal */}
            <Modal
                title="Edit Entity"
                open={editModalOpen}
                onOk={() => entityForm.validateFields().then(v => updateMutation.mutateAsync(v))}
                onCancel={() => setEditModalOpen(false)}
                confirmLoading={updateMutation.isPending}
            >
                <Form form={entityForm} layout="vertical">
                    <Form.Item name="entity_name" label="Entity Name" rules={[{ required: true }]}>
                        <Input />
                    </Form.Item>
                    <Form.Item name="entity_name_en" label="Entity Name (EN)">
                        <Input />
                    </Form.Item>
                    <Form.Item name="description" label="Description">
                        <TextArea rows={3} />
                    </Form.Item>
                    <Form.Item name="status" label="Status">
                        <Select>
                            <Select.Option value="DRAFT">DRAFT</Select.Option>
                            <Select.Option value="ACTIVE">ACTIVE</Select.Option>
                        </Select>
                    </Form.Item>
                </Form>
            </Modal>

            {/* Property Modal */}
            <Modal
                title={editingProp ? 'Edit Property' : 'Add Property'}
                open={propModalOpen}
                onOk={handlePropSubmit}
                onCancel={() => { setPropModalOpen(false); setEditingProp(null); }}
                confirmLoading={createPropMutation.isPending || updatePropMutation.isPending}
            >
                <Form form={propForm} layout="vertical">
                    <Row gutter={16}>
                        <Col span={12}>
                            <Form.Item name="prop_code" label="Property Code" rules={[{ required: true }]}>
                                <Input disabled={!!editingProp} prefix={<CodeOutlined />} />
                            </Form.Item>
                        </Col>
                        <Col span={12}>
                            <Form.Item name="prop_name" label="Property Name" rules={[{ required: true }]}>
                                <Input />
                            </Form.Item>
                        </Col>
                    </Row>

                    <Row gutter={16}>
                        <Col span={12}>
                            <Form.Item name="prop_name_en" label="Property Name (EN)">
                                <Input />
                            </Form.Item>
                        </Col>
                        <Col span={12}>
                            <Form.Item name="data_type" label="Data Type" initialValue="STRING">
                                <Select>
                                    <Select.Option value="STRING">STRING</Select.Option>
                                    <Select.Option value="INTEGER">INTEGER</Select.Option>
                                    <Select.Option value="FLOAT">FLOAT</Select.Option>
                                    <Select.Option value="BOOLEAN">BOOLEAN</Select.Option>
                                    <Select.Option value="ENUM">ENUM</Select.Option>
                                </Select>
                            </Form.Item>
                        </Col>
                    </Row>

                    <Row gutter={16}>
                        <Col span={12}>
                            <Form.Item name="display_order" label="Display Order" initialValue={0}>
                                <Input type="number" />
                            </Form.Item>
                        </Col>
                        <Col span={12}>
                            <Form.Item name="is_required" label="Required" valuePropName="checked">
                                <Switch />
                            </Form.Item>
                        </Col>
                    </Row>
                </Form>
            </Modal>
        </div>
    );
};

export default EntityDetail;
