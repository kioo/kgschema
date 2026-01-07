import React, { useState } from 'react';
import {
    Table,
    Button,
    Space,
    Modal,
    Form,
    Input,
    message,
    Card,
    Descriptions,
    Tag,
    Popconfirm,
    Upload,
    Collapse,
} from 'antd';
import {
    PlusOutlined,
    DownloadOutlined,
    UploadOutlined,
    RollbackOutlined,
    EyeOutlined,
    ExportOutlined,
} from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { versionApi, importExportApi } from '../api/version';
import type { Version, VersionDetail, PublishParams, ImportResult } from '../api/version';

const { TextArea } = Input;

const VersionList: React.FC = () => {
    const [publishModalOpen, setPublishModalOpen] = useState(false);
    const [detailModalOpen, setDetailModalOpen] = useState(false);
    const [importModalOpen, setImportModalOpen] = useState(false);
    const [selectedVersion, setSelectedVersion] = useState<VersionDetail | null>(null);
    const [importResult, setImportResult] = useState<ImportResult | null>(null);
    const [form] = Form.useForm();
    const queryClient = useQueryClient();
    const [pagination, setPagination] = useState({ page: 1, size: 20 });

    // Fetch Versions
    const { data, isLoading } = useQuery({
        queryKey: ['versions', pagination],
        queryFn: () => versionApi.list(pagination),
    });

    // Publish Mutation
    const publishMutation = useMutation({
        mutationFn: versionApi.publish,
        onSuccess: () => {
            message.success('Version published successfully');
            setPublishModalOpen(false);
            form.resetFields();
            queryClient.invalidateQueries({ queryKey: ['versions'] });
        },
        onError: (err: any) => {
            message.error(err.message || 'Failed to publish version');
        },
    });

    // Copy to Draft Mutation
    const copyToDraftMutation = useMutation({
        mutationFn: versionApi.copyToDraft,
        onSuccess: (data) => {
            message.success(`Rolled back: ${data.entities_created} entities, ${data.relations_created} relations`);
            queryClient.invalidateQueries({ queryKey: ['entities'] });
            queryClient.invalidateQueries({ queryKey: ['relations'] });
        },
        onError: (err: any) => {
            message.error(err.message || 'Failed to copy to draft');
        },
    });

    // View Version Detail
    const handleViewDetail = async (id: string) => {
        try {
            const detail = await versionApi.get(id);
            setSelectedVersion(detail);
            setDetailModalOpen(true);
        } catch (err: any) {
            message.error('Failed to load version details');
        }
    };

    // Download Template
    const handleDownloadTemplate = async () => {
        try {
            const response = await importExportApi.downloadTemplate();
            const blob = new Blob([response as any], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'import_template.xlsx';
            a.click();
            window.URL.revokeObjectURL(url);
        } catch (err) {
            message.error('Failed to download template');
        }
    };

    // Export Excel
    const handleExportExcel = async () => {
        try {
            const response = await importExportApi.exportExcel();
            const blob = new Blob([response as any], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `schema_export_${new Date().toISOString().slice(0, 10)}.xlsx`;
            a.click();
            window.URL.revokeObjectURL(url);
            message.success('Exported successfully');
        } catch (err) {
            message.error('Failed to export');
        }
    };

    // Import Excel
    const handleImport = async (file: File) => {
        try {
            const result = await importExportApi.importExcel(file);
            setImportResult(result);
            if (result.success) {
                message.success(`Imported: ${result.entities_count} entities, ${result.relations_count} relations`);
                queryClient.invalidateQueries({ queryKey: ['entities'] });
                queryClient.invalidateQueries({ queryKey: ['relations'] });
            }
        } catch (err: any) {
            message.error(err.message || 'Import failed');
        }
        return false; // Prevent default upload
    };

    const columns = [
        {
            title: 'Version',
            dataIndex: 'version',
            key: 'version',
            render: (v: number) => <Tag color="blue">v{v}</Tag>,
        },
        {
            title: 'Release Notes',
            dataIndex: 'release_notes',
            key: 'release_notes',
            ellipsis: true,
            render: (text: string) => text || '-',
        },
        {
            title: 'Published By',
            dataIndex: 'published_by_username',
            key: 'published_by_username',
            render: (text: string) => text || '-',
        },
        {
            title: 'Published At',
            dataIndex: 'published_at',
            key: 'published_at',
            render: (text: string) => new Date(text).toLocaleString(),
        },
        {
            title: 'Actions',
            key: 'action',
            render: (_: any, record: Version) => (
                <Space size="small">
                    <Button type="link" icon={<EyeOutlined />} onClick={() => handleViewDetail(record.id)}>
                        View
                    </Button>
                    <Popconfirm
                        title="Roll back to this version?"
                        description="This will replace current draft data with this version's snapshot."
                        onConfirm={() => copyToDraftMutation.mutateAsync(record.id)}
                    >
                        <Button type="link" icon={<RollbackOutlined />} danger>
                            Rollback
                        </Button>
                    </Popconfirm>
                </Space>
            ),
        },
    ];

    return (
        <div>
            <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <h2>Version Management</h2>
                <Space>
                    <Button icon={<DownloadOutlined />} onClick={handleDownloadTemplate}>
                        Download Template
                    </Button>
                    <Button icon={<ExportOutlined />} onClick={handleExportExcel}>
                        Export Excel
                    </Button>
                    <Button icon={<UploadOutlined />} onClick={() => { setImportResult(null); setImportModalOpen(true); }}>
                        Import Excel
                    </Button>
                    <Button type="primary" icon={<PlusOutlined />} onClick={() => setPublishModalOpen(true)}>
                        Publish Version
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

            {/* Publish Modal */}
            <Modal
                title="Publish New Version"
                open={publishModalOpen}
                onOk={() => form.validateFields().then(v => publishMutation.mutateAsync(v as PublishParams))}
                onCancel={() => setPublishModalOpen(false)}
                confirmLoading={publishMutation.isPending}
            >
                <Form form={form} layout="vertical">
                    <Form.Item name="release_notes" label="Release Notes">
                        <TextArea rows={4} placeholder="Describe changes in this version..." />
                    </Form.Item>
                </Form>
                <p style={{ color: '#888' }}>
                    This will create a snapshot of all current entities and relations.
                </p>
            </Modal>

            {/* Detail Modal */}
            <Modal
                title={`Version ${selectedVersion?.version} Details`}
                open={detailModalOpen}
                onCancel={() => setDetailModalOpen(false)}
                footer={null}
                width={800}
            >
                {selectedVersion && (
                    <>
                        <Descriptions bordered size="small" column={2}>
                            <Descriptions.Item label="Version">v{selectedVersion.version}</Descriptions.Item>
                            <Descriptions.Item label="Published At">
                                {new Date(selectedVersion.published_at).toLocaleString()}
                            </Descriptions.Item>
                            <Descriptions.Item label="Published By">
                                {selectedVersion.published_by_username || '-'}
                            </Descriptions.Item>
                            <Descriptions.Item label="Release Notes">
                                {selectedVersion.release_notes || '-'}
                            </Descriptions.Item>
                        </Descriptions>

                        <Collapse style={{ marginTop: 16 }} items={[
                            {
                                key: 'entities',
                                label: `Entities (${selectedVersion.snapshot_jsonb.entities.length})`,
                                children: (
                                    <pre style={{ maxHeight: 200, overflow: 'auto', fontSize: 12 }}>
                                        {JSON.stringify(selectedVersion.snapshot_jsonb.entities, null, 2)}
                                    </pre>
                                ),
                            },
                            {
                                key: 'relations',
                                label: `Relations (${selectedVersion.snapshot_jsonb.relations.length})`,
                                children: (
                                    <pre style={{ maxHeight: 200, overflow: 'auto', fontSize: 12 }}>
                                        {JSON.stringify(selectedVersion.snapshot_jsonb.relations, null, 2)}
                                    </pre>
                                ),
                            },
                        ]} />
                    </>
                )}
            </Modal>

            {/* Import Modal */}
            <Modal
                title="Import Excel"
                open={importModalOpen}
                onCancel={() => setImportModalOpen(false)}
                footer={null}
                width={600}
            >
                <Upload.Dragger
                    accept=".xlsx,.xls"
                    beforeUpload={handleImport}
                    showUploadList={false}
                >
                    <p className="ant-upload-drag-icon">
                        <UploadOutlined style={{ fontSize: 48, color: '#1890ff' }} />
                    </p>
                    <p className="ant-upload-text">Click or drag Excel file to import</p>
                    <p className="ant-upload-hint">Supports .xlsx, .xls files</p>
                </Upload.Dragger>

                {importResult && (
                    <Card size="small" style={{ marginTop: 16 }}>
                        {importResult.success ? (
                            <div style={{ color: 'green' }}>
                                ✅ Import successful!
                                <ul>
                                    <li>Entities: {importResult.entities_count}</li>
                                    <li>Relations: {importResult.relations_count}</li>
                                    <li>Entity Properties: {importResult.entity_properties_count}</li>
                                    <li>Relation Properties: {importResult.relation_properties_count}</li>
                                </ul>
                            </div>
                        ) : (
                            <div>
                                <div style={{ color: 'red', marginBottom: 8 }}>❌ Import failed with errors:</div>
                                <Table
                                    size="small"
                                    dataSource={importResult.errors}
                                    columns={[
                                        { title: 'Sheet', dataIndex: 'sheet', width: 80 },
                                        { title: 'Row', dataIndex: 'row', width: 50 },
                                        { title: 'Field', dataIndex: 'field', width: 100 },
                                        { title: 'Value', dataIndex: 'value', width: 80 },
                                        { title: 'Error', dataIndex: 'error' },
                                    ]}
                                    pagination={false}
                                    scroll={{ y: 200 }}
                                    rowKey={(_, i) => String(i)}
                                />
                            </div>
                        )}
                    </Card>
                )}
            </Modal>
        </div>
    );
};

export default VersionList;
