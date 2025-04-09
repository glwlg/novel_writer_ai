import apiClient from './apiClient';


class CharacterAPI {
    /**
     * 为指定项目创建新角色
     * @param {number} projectId - 项目 ID
     * @param {object} characterData - 角色数据 (符合 CharacterCreate schema)
     * @returns {Promise<object>} - 创建的角色信息 (符合 CharacterRead schema)
     */
    createCharacter = async (projectId, characterData) => {
        // 确保 characterData 中的 project_id 与 projectId 一致
        if (characterData.project_id !== projectId) {
            console.warn('Character data project_id does not match path project_id.');
            characterData.project_id = projectId;
        }
        return apiClient.post(`/projects/${projectId}/characters/`, characterData);
    };

    /**
     * 获取指定项目下的角色列表
     * @param {number} projectId - 项目 ID
     * @param {object} params - 查询参数 (例如 { skip: 0, limit: 100 })
     * @returns {Promise<Array<object>>} - 角色列表 (符合 CharacterRead schema)
     */
    getCharactersByProject = async (projectId, params) => {
        return apiClient.get(`/projects/${projectId}/characters/`, {params});
    };

    /**
     * 获取单个角色详情
     * @param {number} characterId - 角色 ID
     * @returns {Promise<object>} - 角色详情 (符合 CharacterRead schema)
     */
    getCharacter = async (characterId) => {
        return apiClient.get(`/characters/${characterId}`);
    };

    /**
     * 更新角色信息
     * @param {number} characterId - 角色 ID
     * @param {object} characterData - 要更新的角色数据 (符合 CharacterUpdate schema)
     * @returns {Promise<object>} - 更新后的角色信息 (符合 CharacterRead schema)
     */
    updateCharacter = async (characterId, characterData) => {
        return apiClient.patch(`/characters/${characterId}`, characterData);
    };

    /**
     * 删除角色
     * @param {number} characterId - 角色 ID
     * @returns {Promise<object>} - 被删除的角色信息 (符合 CharacterRead schema)
     */
    deleteCharacter = async (characterId) => {
        return apiClient.delete(`/characters/${characterId}`);
    };
}

const characterAPI = new CharacterAPI();

// 将这个实例导出，以便其他模块可以导入并直接使用
export {characterAPI};
