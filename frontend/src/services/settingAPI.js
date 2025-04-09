import apiClient from './apiClient';

class SettingAPI {
    /**
     * 为指定项目创建新设定元素
     * @param {number} projectId - 项目 ID
     * @param {object} settingData - 设定数据 (符合 SettingElementCreate schema)
     * @returns {Promise<object>} - 创建的设定信息 (符合 SettingElementRead schema)
     */
    createSetting = async (projectId, settingData) => {
        // 确保 settingData 中的 project_id 与 projectId 一致
        if (settingData.project_id !== projectId) {
            console.warn('Setting data project_id does not match path project_id.');
            // settingData.project_id = projectId;
        }
        return apiClient.post(`/projects/${projectId}/settings/`, settingData);
    };

    /**
     * 获取指定项目下的设定元素列表
     * @param {number} projectId - 项目 ID
     * @param {object} params - 查询参数 (例如 { skip: 0, limit: 100 })
     * @returns {Promise<Array<object>>} - 设定列表 (符合 SettingElementRead schema)
     */
    getSettingsByProject = async (projectId, params) => {
        return apiClient.get(`/projects/${projectId}/settings/`, {params});
    };

    /**
     * 获取单个设定元素详情
     * @param {number} settingId - 设定元素 ID
     * @returns {Promise<object>} - 设定详情 (符合 SettingElementRead schema)
     */
    getSetting = async (settingId) => {
        return apiClient.get(`/settings/${settingId}`);
    };

    /**
     * 更新设定元素信息
     * @param {number} settingId - 设定元素 ID
     * @param {object} settingData - 要更新的设定数据 (符合 SettingElementUpdate schema)
     * @returns {Promise<object>} - 更新后的设定信息 (符合 SettingElementRead schema)
     */
    updateSetting = async (settingId, settingData) => {
        return apiClient.patch(`/settings/${settingId}`, settingData);
    };

    /**
     * 删除设定元素
     * @param {number} settingId - 设定元素 ID
     * @returns {Promise<object>} - 被删除的设定信息 (符合 SettingElementRead schema)
     */
    deleteSetting = async (settingId) => {
        return apiClient.delete(`/settings/${settingId}`);
    };
}

const settingAPI = new SettingAPI();
export {settingAPI};