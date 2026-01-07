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
import { relationApi } from '../api/relation';
import { entityApi } from '../api/entity';
import type { RelationProperty, RelationUpdateParams, RelationPropertyCreateParams, RelationPropertyUpdateParams } from '../api/relation';

const { TextArea } = Input;

const RelationDetail: React.FC = () => {
    const { id } = useParams<{ id: string }>();
    const navigate = useNavigate();
    const queryClient = useQueryClient();
    const [editModalOpen, setEditModalOpen] = useState(false);
    const [propModalOpen, setPropModalOpen] = useState(false);
    const [editingProp, setEditingProp] = useState<RelationProperty | null>(null);
    const [relationForm] = Form.useForm();
    const [propForm] = Form.useForm();

    // Fetch Relation Detail
    const { data: relation, isLoading } = useQuery({
        queryKey: ['relation', id],
        queryFn: () => relationApi.get(id!),
        enabled: !!id,
    });

    // Fetch Entities for select
    const { data: entitiesData } = useQuery({
        queryKey: ['entities-select'],
        queryFn: () => entityApi.list({ page: 1, size: 100 }),
    });

    // Update Relation Mutation
    const updateMutation = useMutation({
        mutationFn: (data: RelationUpdateParams) => relationApi.update(id!, data),
        onSuccess: () => {
            message.success('Relation updated');
            setEditModalOpen(false);
            queryClient.invalidateQueries({ queryKey: ['relation', id] });
        },
    });

    // Property Mutations
    const createPropMutation = useMutation({
        mutationFn: (data: RelationPropertyCreateParams) => relationApi.createProperty(id!, data),
        onSuccess: () => {
            message.success('Property created');
            setPropModalOpen(false);
            propForm.resetFields();
            queryClient.invalidateQueries({ queryKey: ['relation', id] });
        },
    });

    const updatePropMutation = useMutation({
        mutationFn: ({ propId, data }: { propId: string; data: RelationPropertyUpdateParams }) =>
            relationApi.updateProperty(id!, propId, data),
        onSuccess: () => {
            message.success('Property updated');
            setPropModalOpen(false);
            setEditingProp(null);
            propForm.resetFields();
            queryClient.invalidateQueries({ queryKey: ['relation', id] });
        },
    });

    const deletePropMutation = useMutation({
        mutationFn: (propId: string) => relationApi.deleteProperty(id!, propId),
        onSuccess: () => {
            message.success('Property deleted');
            queryClient.invalidateQueries({ queryKey: ['relation', id] });
        },
    });

    const handleEditRelation = () => {
        relationForm.setFieldsValue({
            relation_name: relation?.relation_name,
            relation_name_en: relation?.relation_name_en,
            head_entity_id: relation?.head_entity_id,
            tail_entity_id: relation?.tail_entity_id,
            description: relation?.description,
            status: relation?.status,
        });
        setEditModalOpen(true);
    };

    const handleEditProp = (prop: RelationProperty) => {
        setEditingProp(prop);
        propForm.setFieldsValue(prop);
        setPropModalOpen(true);
    };

    const handlePropSubmit = async () => {
        const values = await propForm.validateFields();
        if (editingProp) {
            await updatePropMutation.mutateAsync({ propId: editingProp.id, data: values });
        } else {
            await createPropMutation.mutateAsync(values as RelationPropertyCreateParams);
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
            render: (_: any, record: RelationProperty) => (
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
    if (!relation) return <div>Relation not found</div>;

    return (
        <div>
            <Space style={{ marginBottom: 16 }}>
                <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/relations')}>Back</Button>
            </Space>

            <Card
                title={`Relation: ${relation.relation_code}`}
                extra={<Button type="primary" onClick={handleEditRelation}>Edit</Button>}
            >
                <Descriptions column={2}>
                    <Descriptions.Item label="Relation Code">{relation.relation_code}</Descriptions.Item>
                    <Descriptions.Item label="Status">
                        <Tag color={relation.status === 'ACTIVE' ? 'success' : 'default'}>{relation.status}</Tag>
                    </Descriptions.Item>
                    <Descriptions.Item label="Relation Name">{relation.relation_name}</Descriptions.Item>
                    <Descriptions.Item label="Relation Name (EN)">{relation.relation_name_en || '-'}</Descriptions.Item>
                    <Descriptions.Item label="Head Entity">
                        <Tag color="blue">{relation.head_entity_code}</Tag>
                    </Descriptions.Item>
                    <Descriptions.Item label="Tail Entity">
                        <Tag color="green">{relation.tail_entity_code}</Tag>
                    </Descriptions.Item>
                    <Descriptions.Item label="Description" span={2}>{relation.description || '-'}</Descriptions.Item>
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
                <Table columns={propColumns} dataSource={relation.properties} rowKey="id" pagination={false} />
            </Card>

            {/* Edit Relation Modal */}
            <Modal
                title="Edit Relation"
                open={editModalOpen}
                onOk={() => relationForm.validateFields().then(v => updateMutation.mutateAsync(v))}
                onCancel={() => setEditModalOpen(false)}
                confirmLoading={updateMutation.isPending}
                width={600}
            >
                <Form form={relationForm} layout="vertical">
                    <Form.Item name="relation_name" label="Relation Name" rules={[{ required: true }]}>
                        <Input />
                    </Form.Item>
                    <Form.Item name="relation_name_en" label="Relation Name (EN)">
                        <Input />
                    </Form.Item>
                    <Form.Item name="head_entity_id" label="Head Entity" rules={[{ required: true }]}>
                        <Select showSearch optionFilterProp="children">
                            {entitiesData?.items.map((e) => (
                                <Select.Option key={e.id} value={e.id}>{e.entity_code} - {e.entity_name}</Select.Option>
                            ))}
                        </Select>
                    </Form.Item>
                    <Form.Item name="tail_entity_id" label="Tail Entity" rules={[{ required: true }]}>
                        <Select showSearch optionFilterProp="children">
                            {entitiesData?.items.map((e) => (
                                <Select.Option key={e.id} value={e.id}>{e.entity_code} - {e.entity_name}</Select.Option>
                            ))}
                        </Select>
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

export default RelationDetail;
