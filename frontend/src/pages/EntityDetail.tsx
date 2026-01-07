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
} from 'antd';
import { ArrowLeftOutlined, PlusOutlined, EditOutlined } from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useParams, useNavigate } from 'react-router-dom';
import { entityApi } from '../api/entity';
import type { EntityProperty, EntityUpdateParams, PropertyCreateParams, PropertyUpdateParams } from '../api/entity';

const { TextArea } = Input;

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

    const propColumns = [
        { title: 'Code', dataIndex: 'prop_code', key: 'prop_code' },
        { title: 'Name', dataIndex: 'prop_name', key: 'prop_name' },
        { title: 'Type', dataIndex: 'data_type', key: 'data_type', render: (t: string) => <Tag>{t}</Tag> },
        { title: 'Required', dataIndex: 'is_required', key: 'is_required', render: (r: boolean) => r ? 'Yes' : 'No' },
        { title: 'Order', dataIndex: 'display_order', key: 'display_order' },
        {
            title: 'Actions',
            key: 'action',
            render: (_: any, record: EntityProperty) => (
                <Space>
                    <Button type="link" icon={<EditOutlined />} onClick={() => handleEditProp(record)}>Edit</Button>
                    <Popconfirm title="Delete this property?" onConfirm={() => deletePropMutation.mutateAsync(record.id)}>
                        <Button type="link" danger>Delete</Button>
                    </Popconfirm>
                </Space>
            ),
        },
    ];

    if (isLoading) return <Spin size="large" />;
    if (!entity) return <div>Entity not found</div>;

    return (
        <div>
            <Space style={{ marginBottom: 16 }}>
                <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/entities')}>Back</Button>
            </Space>

            <Card
                title={`Entity: ${entity.entity_code}`}
                extra={<Button type="primary" onClick={handleEditEntity}>Edit</Button>}
            >
                <Descriptions column={2}>
                    <Descriptions.Item label="Entity Code">{entity.entity_code}</Descriptions.Item>
                    <Descriptions.Item label="Status">
                        <Tag color={entity.status === 'ACTIVE' ? 'success' : 'default'}>{entity.status}</Tag>
                    </Descriptions.Item>
                    <Descriptions.Item label="Entity Name">{entity.entity_name}</Descriptions.Item>
                    <Descriptions.Item label="Entity Name (EN)">{entity.entity_name_en || '-'}</Descriptions.Item>
                    <Descriptions.Item label="Description" span={2}>{entity.description || '-'}</Descriptions.Item>
                    <Descriptions.Item label="Created At">{new Date(entity.created_at).toLocaleString()}</Descriptions.Item>
                    <Descriptions.Item label="Updated At">{new Date(entity.updated_at).toLocaleString()}</Descriptions.Item>
                </Descriptions>
            </Card>

            <Card
                title="Properties"
                style={{ marginTop: 16 }}
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
                <Table columns={propColumns} dataSource={entity.properties} rowKey="id" pagination={false} />
            </Card>

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
                    <Form.Item name="prop_code" label="Property Code" rules={[{ required: true }]}>
                        <Input disabled={!!editingProp} />
                    </Form.Item>
                    <Form.Item name="prop_name" label="Property Name" rules={[{ required: true }]}>
                        <Input />
                    </Form.Item>
                    <Form.Item name="prop_name_en" label="Property Name (EN)">
                        <Input />
                    </Form.Item>
                    <Form.Item name="data_type" label="Data Type" initialValue="STRING">
                        <Select>
                            <Select.Option value="STRING">STRING</Select.Option>
                            <Select.Option value="INTEGER">INTEGER</Select.Option>
                            <Select.Option value="FLOAT">FLOAT</Select.Option>
                            <Select.Option value="BOOLEAN">BOOLEAN</Select.Option>
                            <Select.Option value="ENUM">ENUM</Select.Option>
                        </Select>
                    </Form.Item>
                    <Form.Item name="is_required" label="Required" valuePropName="checked">
                        <Switch />
                    </Form.Item>
                    <Form.Item name="display_order" label="Display Order" initialValue={0}>
                        <Input type="number" />
                    </Form.Item>
                </Form>
            </Modal>
        </div>
    );
};

export default EntityDetail;
