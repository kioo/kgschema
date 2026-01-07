/**
 * Prompt Management page with version history support.
 */
import React, { useState } from 'react';
import {
    Card,
    Table,
    Button,
    Space,
    Input,
    Modal,
    Form,
    Tag,
    message,
    Popconfirm,
    Typography,
    Timeline,
    Tooltip,
    Drawer,
    Row,
    Col,
    Divider,
} from 'antd';
import {
    PlusOutlined,
    EditOutlined,
    DeleteOutlined,
    HistoryOutlined,
    RollbackOutlined,
    SearchOutlined,
    EyeOutlined,
} from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { promptApi, type Prompt, type PromptDetail, type PromptVersion } from '../api/prompt';

const { TextArea } = Input;
const { Text, Paragraph } = Typography;

const PromptList: React.FC = () => {
    const queryClient = useQueryClient();
    const [page, setPage] = useState(1);
    const [search, setSearch] = useState('');
    const [createModalOpen, setCreateModalOpen] = useState(false);
    const [editModalOpen, setEditModalOpen] = useState(false);
    const [detailDrawerOpen, setDetailDrawerOpen] = useState(false);
    const [selectedPrompt, setSelectedPrompt] = useState<PromptDetail | null>(null);
    const [createVersionOnEdit, setCreateVersionOnEdit] = useState(true);
    const [form] = Form.useForm();
    const [editForm] = Form.useForm();

    // Fetch prompts list
    const { data, isLoading } = useQuery({
        queryKey: ['prompts', page, search],
        queryFn: () => promptApi.list(page, 20, search || undefined),
    });

    // Create mutation
    const createMutation = useMutation({
        mutationFn: promptApi.create,
        onSuccess: () => {
            message.success('提示词创建成功');
            setCreateModalOpen(false);
            form.resetFields();
            queryClient.invalidateQueries({ queryKey: ['prompts'] });
        },
        onError: (err: any) => {
            message.error(err?.response?.data?.detail || '创建失败');
        },
    });

    // Update mutation
    const updateMutation = useMutation({
        mutationFn: ({ id, data }: { id: string; data: any }) => promptApi.update(id, data),
        onSuccess: () => {
            message.success('提示词更新成功');
            setEditModalOpen(false);
            queryClient.invalidateQueries({ queryKey: ['prompts'] });
            if (selectedPrompt) {
                queryClient.invalidateQueries({ queryKey: ['prompt', selectedPrompt.id] });
            }
        },
    });

    // Delete mutation
    const deleteMutation = useMutation({
        mutationFn: promptApi.delete,
        onSuccess: () => {
            message.success('提示词已删除');
            queryClient.invalidateQueries({ queryKey: ['prompts'] });
        },
    });

    // Rollback mutation
    const rollbackMutation = useMutation({
        mutationFn: ({ promptId, version }: { promptId: string; version: number }) =>
            promptApi.rollback(promptId, version),
        onSuccess: () => {
            message.success('已回滚到目标版本');
            queryClient.invalidateQueries({ queryKey: ['prompts'] });
            if (selectedPrompt) {
                queryClient.invalidateQueries({ queryKey: ['prompt', selectedPrompt.id] });
                refreshDetail(selectedPrompt.id);
            }
        },
    });

    // Fetch detail
    const refreshDetail = async (id: string) => {
        const detail = await promptApi.get(id);
        setSelectedPrompt(detail);
    };

    const handleViewDetail = async (record: Prompt) => {
        const detail = await promptApi.get(record.id);
        setSelectedPrompt(detail);
        setDetailDrawerOpen(true);
    };

    const handleEdit = (record: Prompt) => {
        editForm.setFieldsValue({
            content: record.content,
            description: record.description,
            change_note: '',
        });
        setSelectedPrompt(record as PromptDetail);
        setCreateVersionOnEdit(true);
        setEditModalOpen(true);
    };

    const columns = [
        {
            title: '标签',
            dataIndex: 'tag',
            key: 'tag',
            width: 150,
            render: (text: string) => <Tag color="blue">{text}</Tag>,
        },
        {
            title: '内容预览',
            dataIndex: 'content',
            key: 'content',
            ellipsis: true,
            render: (text: string) => (
                <Tooltip title={text.length > 100 ? text.substring(0, 200) + '...' : text}>
                    <Text>{text.substring(0, 60)}{text.length > 60 ? '...' : ''}</Text>
                </Tooltip>
            ),
        },
        {
            title: '版本',
            dataIndex: 'current_version',
            key: 'current_version',
            width: 80,
            render: (v: number) => <Tag color="purple">v{v}</Tag>,
        },
        {
            title: '描述',
            dataIndex: 'description',
            key: 'description',
            ellipsis: true,
            width: 200,
            render: (text: string | null) => text || <Text type="secondary">-</Text>,
        },
        {
            title: '更新时间',
            dataIndex: 'updated_at',
            key: 'updated_at',
            width: 180,
            render: (text: string) => new Date(text).toLocaleString(),
        },
        {
            title: '操作',
            key: 'action',
            width: 200,
            render: (_: any, record: Prompt) => (
                <Space size="small">
                    <Tooltip title="查看详情">
                        <Button type="text" icon={<EyeOutlined />} onClick={() => handleViewDetail(record)} />
                    </Tooltip>
                    <Tooltip title="编辑">
                        <Button type="text" icon={<EditOutlined />} onClick={() => handleEdit(record)} />
                    </Tooltip>
                    <Tooltip title="版本历史">
                        <Button type="text" icon={<HistoryOutlined />} onClick={() => handleViewDetail(record)} />
                    </Tooltip>
                    <Popconfirm title="确定删除此提示词?" onConfirm={() => deleteMutation.mutate(record.id)}>
                        <Tooltip title="删除">
                            <Button type="text" danger icon={<DeleteOutlined />} />
                        </Tooltip>
                    </Popconfirm>
                </Space>
            ),
        },
    ];

    return (
        <div>
            <Card
                title="提示词管理"
                extra={
                    <Space>
                        <Input
                            placeholder="搜索标签或描述"
                            prefix={<SearchOutlined />}
                            value={search}
                            onChange={(e) => setSearch(e.target.value)}
                            style={{ width: 200 }}
                            allowClear
                        />
                        <Button type="primary" icon={<PlusOutlined />} onClick={() => setCreateModalOpen(true)}>
                            新建提示词
                        </Button>
                    </Space>
                }
            >
                <Table
                    columns={columns}
                    dataSource={data?.items}
                    rowKey="id"
                    loading={isLoading}
                    pagination={{
                        current: page,
                        total: data?.total || 0,
                        pageSize: 20,
                        onChange: setPage,
                        showTotal: (t) => `共 ${t} 条`,
                    }}
                />
            </Card>

            {/* Create Modal */}
            <Modal
                title="新建提示词"
                open={createModalOpen}
                onOk={() => form.validateFields().then((v) => createMutation.mutate(v))}
                onCancel={() => setCreateModalOpen(false)}
                confirmLoading={createMutation.isPending}
                width={700}
            >
                <Form form={form} layout="vertical">
                    <Form.Item name="tag" label="标签" rules={[{ required: true, message: '请输入唯一标签' }]}>
                        <Input placeholder="例如: extraction_prompt, system_prompt" />
                    </Form.Item>
                    <Form.Item name="content" label="提示词内容" rules={[{ required: true, message: '请输入内容' }]}>
                        <TextArea rows={8} placeholder="输入提示词内容..." />
                    </Form.Item>
                    <Form.Item name="description" label="描述">
                        <TextArea rows={2} placeholder="描述此提示词的用途..." />
                    </Form.Item>
                </Form>
            </Modal>

            {/* Edit Modal */}
            <Modal
                title="编辑提示词"
                open={editModalOpen}
                onOk={() => {
                    editForm.validateFields().then((v) => {
                        if (selectedPrompt) {
                            updateMutation.mutate({
                                id: selectedPrompt.id,
                                data: { ...v, create_version: createVersionOnEdit },
                            });
                        }
                    });
                }}
                onCancel={() => setEditModalOpen(false)}
                confirmLoading={updateMutation.isPending}
                width={700}
            >
                <Form form={editForm} layout="vertical">
                    <Form.Item name="content" label="提示词内容" rules={[{ required: true }]}>
                        <TextArea rows={8} />
                    </Form.Item>
                    <Form.Item name="description" label="描述">
                        <TextArea rows={2} />
                    </Form.Item>
                    <Divider />
                    <Form.Item>
                        <Space>
                            <span>保存为新版本:</span>
                            <Button
                                type={createVersionOnEdit ? 'primary' : 'default'}
                                size="small"
                                onClick={() => setCreateVersionOnEdit(true)}
                            >
                                是
                            </Button>
                            <Button
                                type={!createVersionOnEdit ? 'primary' : 'default'}
                                size="small"
                                onClick={() => setCreateVersionOnEdit(false)}
                            >
                                否
                            </Button>
                        </Space>
                    </Form.Item>
                    {createVersionOnEdit && (
                        <Form.Item name="change_note" label="变更说明">
                            <Input placeholder="描述此次修改的内容..." />
                        </Form.Item>
                    )}
                </Form>
            </Modal>

            {/* Detail Drawer with Version History */}
            <Drawer
                title={selectedPrompt ? `提示词: ${selectedPrompt.tag}` : '详情'}
                placement="right"
                width={700}
                open={detailDrawerOpen}
                onClose={() => setDetailDrawerOpen(false)}
            >
                {selectedPrompt && (
                    <div>
                        <Row gutter={16}>
                            <Col span={12}>
                                <Text type="secondary">标签</Text>
                                <Paragraph>
                                    <Tag color="blue" style={{ fontSize: 14 }}>{selectedPrompt.tag}</Tag>
                                </Paragraph>
                            </Col>
                            <Col span={12}>
                                <Text type="secondary">当前版本</Text>
                                <Paragraph>
                                    <Tag color="purple">v{selectedPrompt.current_version}</Tag>
                                </Paragraph>
                            </Col>
                        </Row>

                        <Text type="secondary">描述</Text>
                        <Paragraph>{selectedPrompt.description || '无描述'}</Paragraph>

                        <Text type="secondary">当前内容</Text>
                        <Paragraph>
                            <pre style={{
                                background: '#f5f5f5',
                                padding: 12,
                                borderRadius: 4,
                                maxHeight: 200,
                                overflow: 'auto',
                                fontSize: 12,
                            }}>
                                {selectedPrompt.content}
                            </pre>
                        </Paragraph>

                        <Divider>版本历史</Divider>
                        <Timeline>
                            {selectedPrompt.versions?.map((v: PromptVersion) => (
                                <Timeline.Item key={v.id} color={v.version === selectedPrompt.current_version ? 'green' : 'gray'}>
                                    <Space>
                                        <Tag color={v.version === selectedPrompt.current_version ? 'green' : 'default'}>
                                            v{v.version}
                                        </Tag>
                                        <Text type="secondary">{new Date(v.created_at).toLocaleString()}</Text>
                                        {v.change_note && <Text italic>- {v.change_note}</Text>}
                                        {v.version !== selectedPrompt.current_version && (
                                            <Popconfirm
                                                title={`回滚到版本 v${v.version}?`}
                                                description="回滚将创建一个新版本，内容为目标版本的内容"
                                                onConfirm={() => rollbackMutation.mutate({ promptId: selectedPrompt.id, version: v.version })}
                                            >
                                                <Button type="link" size="small" icon={<RollbackOutlined />}>
                                                    回滚
                                                </Button>
                                            </Popconfirm>
                                        )}
                                    </Space>
                                </Timeline.Item>
                            ))}
                        </Timeline>
                    </div>
                )}
            </Drawer>
        </div>
    );
};

export default PromptList;
