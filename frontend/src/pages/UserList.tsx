import React, { useState } from 'react';
import {
  Table,
  Button,
  Space,
  Tag,
  Modal,
  Form,
  Input,
  Select,
  message,
  Popconfirm,
} from 'antd';
import { PlusOutlined } from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { userApi } from '../api/user';
import type { CreateUserParams, UpdateUserParams } from '../api/user';
import type { User } from '../api/auth';

const UserList: React.FC = () => {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [form] = Form.useForm();
  const queryClient = useQueryClient();
  const [pagination, setPagination] = useState({ page: 1, size: 20 });

  // Fetch Users
  const { data, isLoading } = useQuery({
    queryKey: ['users', pagination],
    queryFn: () => userApi.list(pagination),
  });

  // Create User Mutation
  const createMutation = useMutation({
    mutationFn: userApi.create,
    onSuccess: () => {
      message.success('User created');
      setIsModalOpen(false);
      form.resetFields();
      queryClient.invalidateQueries({ queryKey: ['users'] });
    },
  });

  // Update User Mutation
  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: UpdateUserParams }) =>
      userApi.update(id, data),
    onSuccess: () => {
      message.success('User updated');
      setIsModalOpen(false);
      setEditingId(null);
      form.resetFields();
      queryClient.invalidateQueries({ queryKey: ['users'] });
    },
  });

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();
      if (editingId) {
        // Update mode (only role and is_active)
        await updateMutation.mutateAsync({ id: editingId, data: values });
      } else {
        // Create mode
        await createMutation.mutateAsync(values as CreateUserParams);
      }
    } catch (error) {
      // Validate error
    }
  };

  const handleEdit = (record: User) => {
    setEditingId(record.id);
    form.setFieldsValue({
      username: record.username,
      role: record.role,
      is_active: record.is_active,
    });
    setIsModalOpen(true);
  };

  const columns = [
    {
      title: 'Username',
      dataIndex: 'username',
      key: 'username',
    },
    {
      title: 'Role',
      dataIndex: 'role',
      key: 'role',
      render: (role: string) => (
        <Tag color={role === 'ADMIN' ? 'volcano' : 'blue'}>{role}</Tag>
      ),
    },
    {
      title: 'Status',
      dataIndex: 'is_active',
      key: 'is_active',
      render: (active: boolean) => (
        <Tag color={active ? 'success' : 'error'}>
          {active ? 'Active' : 'Disabled'}
        </Tag>
      ),
    },
    {
      title: 'Actions',
      key: 'action',
      render: (_: any, record: User) => (
        <Space size="middle">
          <Button type="link" onClick={() => handleEdit(record)}>
            Edit
          </Button>
          <Popconfirm
            title={
              record.is_active
                ? 'Disable this user?'
                : 'Enable this user?'
            }
            onConfirm={() =>
              updateMutation.mutateAsync({
                id: record.id,
                data: { is_active: !record.is_active },
              })
            }
          >
            <Button type="link" danger={record.is_active}>
              {record.is_active ? 'Disable' : 'Enable'}
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div>
      <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between' }}>
        <h2>User Management</h2>
        <Button
          type="primary"
          icon={<PlusOutlined />}
          onClick={() => {
            setEditingId(null);
            form.resetFields();
            setIsModalOpen(true);
          }}
        >
          Create User
        </Button>
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
        }}
      />

      <Modal
        title={editingId ? 'Edit User' : 'Create User'}
        open={isModalOpen}
        onOk={handleSubmit}
        onCancel={() => setIsModalOpen(false)}
        confirmLoading={createMutation.isPending || updateMutation.isPending}
      >
        <Form form={form} layout="vertical">
          <Form.Item
            name="username"
            label="Username"
            rules={[{ required: true, message: 'Please enter a username.' }]}
          >
            <Input disabled={!!editingId} />
          </Form.Item>

          {!editingId && (
            <Form.Item
              name="password"
              label="Password"
              rules={[{ required: true, message: 'Please enter a password.' }]}
            >
              <Input.Password />
            </Form.Item>
          )}

          <Form.Item
            name="role"
            label="Role"
            initialValue="USER"
            rules={[{ required: true }]}
          >
            <Select>
              <Select.Option value="USER">USER</Select.Option>
              <Select.Option value="ADMIN">ADMIN</Select.Option>
            </Select>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default UserList;
