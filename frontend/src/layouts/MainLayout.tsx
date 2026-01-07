import React from 'react';
import { Layout, Menu, Button, theme } from 'antd';
import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import {
    UserOutlined,
    LogoutOutlined,
    BookOutlined,
    ClusterOutlined,
    HistoryOutlined,
    TagsOutlined,
} from '@ant-design/icons';
import { authApi } from '../api/auth';

const { Header, Content, Sider } = Layout;

const MainLayout: React.FC = () => {
    const navigate = useNavigate();
    const location = useLocation();
    const {
        token: { colorBgContainer, borderRadiusLG },
    } = theme.useToken();

    const handleLogout = () => {
        authApi.logout();
    };

    const menuItems = [
        {
            key: '/entities',
            icon: <BookOutlined />,
            label: '实体管理',
        },
        {
            key: '/relations',
            icon: <ClusterOutlined />,
            label: '关系管理',
        },
        {
            key: '/versions',
            icon: <TagsOutlined />,
            label: '版本管理',
        },
        {
            key: '/users',
            icon: <UserOutlined />,
            label: '用户管理',
        },
        {
            key: '/audit',
            icon: <HistoryOutlined />,
            label: '审计日志',
        },
    ];

    return (
        <Layout style={{ minHeight: '100vh' }}>
            <Sider breakpoint="lg" collapsedWidth="0">
                <div style={{ padding: 16, textAlign: 'center', color: 'white', fontSize: 18, fontWeight: 'bold' }}>
                    KG Schema
                </div>
                <Menu
                    theme="dark"
                    mode="inline"
                    selectedKeys={[location.pathname]}
                    items={menuItems}
                    onClick={({ key }) => navigate(key)}
                />
            </Sider>
            <Layout>
                <Header style={{ padding: '0 16px', background: colorBgContainer, display: 'flex', justifyContent: 'flex-end', alignItems: 'center' }}>
                    <Button type="text" icon={<LogoutOutlined />} onClick={handleLogout}>
                        退出登录
                    </Button>
                </Header>
                <Content style={{ margin: '24px 16px 0' }}>
                    <div
                        style={{
                            padding: 24,
                            minHeight: 360,
                            background: colorBgContainer,
                            borderRadius: borderRadiusLG,
                        }}
                    >
                        <Outlet />
                    </div>
                </Content>
            </Layout>
        </Layout>
    );
};

export default MainLayout;
