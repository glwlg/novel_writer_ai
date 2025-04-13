import apiClient from './apiClient';

class VolumeAPI {

    /**
     * 为指定项目创建新章节
     * @param {number} projectId - 项目 ID
     * @param {object} volumeData - 章节数据 (符合 VolumeCreate schema)
     * @returns {Promise<object>} - 创建的章节信息 (符合 VolumeRead schema)
     */
    createVolume = async (projectId, volumeData) => {
        // 确保 volumeData 中的 project_id 与 projectId 一致 (后端也会校验)
        if (volumeData.project_id !== projectId) {
            console.warn('Volume data project_id does not match path project_id. Using path project_id.');
            // 可以选择修正或让后端处理
            // volumeData.project_id = projectId;
        }
        return apiClient.post(`/projects/${projectId}/volumes`, volumeData);
    };

    /**
     * 获取指定项目的所有章节
     * @param {number} projectId - 项目 ID
     * @param {object} params - 查询参数 (例如 { skip: 0, limit: 100 })
     * @returns {Promise<Array<object>>} - 章节列表 (符合 VolumeRead schema)
     */
    getVolumesByProject = async (projectId, params) => {
        return apiClient.get(`/projects/${projectId}/volumes`, {params});
    };

    /**
     * 获取单个章节详情
     * @param {number} volumeId - 章节 ID
     * @returns {Promise<object>} - 章节详情 (符合 VolumeRead schema)
     */
    getVolume = async (volumeId) => {
        return apiClient.get(`/volumes/${volumeId}`);
    };

    /**
     * 更新章节信息
     * @param {number} volumeId - 章节 ID
     * @param {object} volumeData - 要更新的章节数据 (符合 VolumeUpdate schema)
     * @returns {Promise<object>} - 更新后的章节信息 (符合 VolumeRead schema)
     */
    updateVolume = async (volumeId, volumeData) => {
        return apiClient.patch(`/volumes/${volumeId}`, volumeData);
    };

    /**
     * 删除章节
     * @param {number} volumeId - 章节 ID
     * @returns {Promise<void>} - 成功则无返回内容 (状态码 204)
     */
    deleteVolume = async (volumeId) => {
        // 对于 204 No Content，axios 默认返回 undefined
        return apiClient.delete(`/volumes/${volumeId}`);
    };
}

const volumeAPI = new VolumeAPI();
export {volumeAPI};