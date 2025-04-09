import apiClient from './apiClient';

class RelationshipAPI {
    /**
     * 为指定项目创建新的人物关系
     * @param {number} projectId - 项目 ID
     * @param {object} relationshipData - 关系数据 (符合 CharacterRelationshipCreate schema)
     * @returns {Promise<object>} - 创建的关系信息 (符合 CharacterRelationshipRead schema)
     */
    createRelationship = async (projectId, relationshipData) => {
        // 确保 relationshipData 中的 project_id 与 projectId 一致
        if (relationshipData.project_id !== projectId) {
            console.warn('Relationship data project_id does not match path project_id.');
            // relationshipData.project_id = projectId;
        }
        return apiClient.post(`/projects/${projectId}/relationships/`, relationshipData);
    };

    /**
     * 获取指定项目下的人物关系列表
     * @param {number} projectId - 项目 ID
     * @param {object} params - 查询参数 (例如 { skip: 0, limit: 100, character_id: Optional[int] })
     * @returns {Promise<Array<object>>} - 关系列表 (符合 CharacterRelationshipRead schema)
     */
    getRelationshipsByProject = async (projectId, params) => {
        return apiClient.get(`/projects/${projectId}/relationships/`, {params});
    };

    /**
     * 获取单个人物关系详情
     * @param {number} relationshipId - 关系 ID
     * @returns {Promise<object>} - 关系详情 (符合 CharacterRelationshipRead schema)
     */
    getRelationship = async (relationshipId) => {
        return apiClient.get(`/relationships/${relationshipId}`);
    };

    /**
     * 更新人物关系信息
     * @param {number} relationshipId - 关系 ID
     * @param {object} relationshipData - 要更新的关系数据 (符合 CharacterRelationshipUpdate schema)
     * @returns {Promise<object>} - 更新后的关系信息 (符合 CharacterRelationshipRead schema)
     */
    updateRelationship = async (relationshipId, relationshipData) => {
        return apiClient.patch(`/relationships/${relationshipId}`, relationshipData);
    };

    /**
     * 删除人物关系
     * @param {number} relationshipId - 关系 ID
     * @returns {Promise<object>} - 被删除的关系信息 (符合 CharacterRelationshipRead schema)
     */
    deleteRelationship = async (relationshipId) => {
        return apiClient.delete(`/relationships/${relationshipId}`);
    };
}

const relationshipAPI = new RelationshipAPI();
export {relationshipAPI}