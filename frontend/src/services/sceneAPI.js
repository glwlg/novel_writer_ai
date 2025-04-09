import apiClient from './apiClient';

class SceneAPI {

    /**
     * 创建新场景
     * @param {object} sceneData - 场景数据 (符合 SceneCreate schema)
     * @returns {Promise<object>} - 创建的场景信息 (符合 SceneRead schema)
     */
    createScene = async (sceneData) => {
        return apiClient.post('/scenes', sceneData);
    };

    /**
     * 获取指定章节的场景列表
     * @param {number} chapterId - 章节 ID
     * @param {object} params - 查询参数 (例如 { skip: 0, limit: 100 })
     * @returns {Promise<Array<object>>} - 场景列表 (符合 SceneReadMinimal schema)
     */
    getScenesByChapter = async (chapterId, params) => {
        return apiClient.get(`/chapters/${chapterId}/scenes`, {params});
    };

    /**
     * 获取项目中未分配给任何章节的场景列表
     * @param {number} projectId - 项目 ID
     * @param {object} params - 查询参数 (例如 { skip: 0, limit: 100 })
     * @returns {Promise<Array<object>>} - 场景列表 (符合 SceneReadMinimal schema)
     */
    getUnassignedScenesByProject = async (projectId, params) => {
        return apiClient.get(`/projects/${projectId}/scenes/unassigned`, {params});
    };

    /**
     * 获取单个场景详情
     * @param {number} sceneId - 场景 ID
     * @returns {Promise<object>} - 场景详情 (符合 SceneRead schema)
     */
    getScene = async (sceneId) => {
        return apiClient.get(`/scenes/${sceneId}`);
    };

    /**
     * 更新场景元数据 (不包括生成内容)
     * @param {number} sceneId - 场景 ID
     * @param {object} sceneData - 要更新的场景元数据 (符合 SceneUpdate schema)
     * @returns {Promise<object>} - 更新后的场景信息 (符合 SceneRead schema)
     */
    updateScene = async (sceneId, sceneData) => {
        return apiClient.patch(`/scenes/${sceneId}`, sceneData);
    };

    /**
     * 删除场景
     * @param {number} sceneId - 场景 ID
     * @returns {Promise<object>} - 被删除的场景信息
     */
    deleteScene = async (sceneId) => {
        return apiClient.delete(`/scenes/${sceneId}`);
    };

}

const sceneAPI = new SceneAPI();

export {sceneAPI};