import apiClient from './apiClient';

class ChapterAPI {

    /**
     * 为指定项目卷创建新章节
     * @param {number} projectId - 项目 ID
     * @param {number} volumeId - 卷 ID
     * @param {object} chapterData - 章节数据 (符合 ChapterCreate schema)
     * @returns {Promise<object>} - 创建的章节信息 (符合 ChapterRead schema)
     */
    createChapter = async (projectId,volumeId, chapterData) => {
        // 确保 chapterData 中的 project_id 与 projectId 一致 (后端也会校验)
        if (chapterData.project_id !== projectId) {
            console.warn('Chapter data project_id does not match path project_id. Using path project_id.');
            // 可以选择修正或让后端处理
            // chapterData.project_id = projectId;
        }
        if (chapterData.volume_id !== volumeId) {
            console.warn('Chapter data volume_id does not match path volume_id. Using path volume_id.');
            // 可以选择修正或让后端处理
            // chapterData.volume_id = projectId;
        }
        return apiClient.post(`/projects/${projectId}/${volumeId}/chapters`, chapterData);
    };

    /**
     * 获取指定项目的所有章节
     * @param {number} projectId - 项目 ID
     * @param {object} params - 查询参数 (例如 { skip: 0, limit: 100 })
     * @returns {Promise<Array<object>>} - 章节列表 (符合 ChapterRead schema)
     */
    getChaptersByProject = async (projectId, params) => {
        return apiClient.get(`/projects/${projectId}/chapters`, {params});
    };

    /**
     * 获取指定卷的所有章节
     * @param {number} volumeId - 项目 ID
     * @param {object} params - 查询参数 (例如 { skip: 0, limit: 100 })
     * @returns {Promise<Array<object>>} - 章节列表 (符合 ChapterRead schema)
     */
    getChaptersByVolume = async (volumeId, params) => {
        return apiClient.get(`/volumes/${volumeId}/chapters`, {params});
    };

    /**
     * 获取单个章节详情
     * @param {number} chapterId - 章节 ID
     * @returns {Promise<object>} - 章节详情 (符合 ChapterRead schema)
     */
    getChapter = async (chapterId) => {
        return apiClient.get(`/chapters/${chapterId}`);
    };

    /**
     * 更新章节信息
     * @param {number} chapterId - 章节 ID
     * @param {object} chapterData - 要更新的章节数据 (符合 ChapterUpdate schema)
     * @returns {Promise<object>} - 更新后的章节信息 (符合 ChapterRead schema)
     */
    updateChapter = async (chapterId, chapterData) => {
        return apiClient.patch(`/chapters/${chapterId}`, chapterData);
    };

    /**
     * 删除章节
     * @param {number} chapterId - 章节 ID
     * @returns {Promise<object>} - 被删除的章节信息
     */
    deleteChapter = async (chapterId) => {
        return apiClient.delete(`/chapters/${chapterId}`);
    };
}

const chapterAPI = new ChapterAPI();
export {chapterAPI};