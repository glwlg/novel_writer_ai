import apiClient from './apiClient';

class ProjectAPI {

    /**
     * 创建新项目
     * @param {object} projectData - 项目数据 (符合 ProjectCreate schema)
     * @returns {Promise<object>} - 创建的项目信息 (符合 ProjectRead schema)
     */
    createProject = async (projectData) => {
        return apiClient.post('/projects/', projectData);
    };

    /**
     * 获取项目列表
     * @param {object} params - 查询参数 (例如 { skip: 0, limit: 100 })
     * @returns {Promise<Array<object>>} - 项目列表 (符合 ProjectRead schema)
     */
    getProjects = async (params) => {
        return apiClient.get('/projects/', {params});
    };

    /**
     * 获取单个项目详情
     * @param {number} projectId - 项目 ID
     * @returns {Promise<object>} - 项目详情 (符合 ProjectRead schema)
     */
    getProject = async (projectId) => {
        return apiClient.get(`/projects/${projectId}`);
    };

    /**
     * 更新项目信息
     * @param {number} projectId - 项目 ID
     * @param {object} projectData - 要更新的项目数据 (符合 ProjectUpdate schema)
     * @returns {Promise<object>} - 更新后的项目信息 (符合 ProjectRead schema)
     */
    updateProject = async (projectId, projectData) => {
        return apiClient.patch(`/projects/${projectId}`, projectData);
    };

    /**
     * 删除项目
     * @param {number} projectId - 项目 ID
     * @returns {Promise<object>} - 被删除的项目信息 (符合 ProjectRead schema)
     */
    deleteProject = async (projectId) => {
        return apiClient.delete(`/projects/${projectId}`);
    };
}

const projectAPI = new ProjectAPI();
export {projectAPI};