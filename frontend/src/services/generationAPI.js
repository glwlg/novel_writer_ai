import apiClient from './apiClient';

class GenerationAPI {

    /**
     * 触发指定章节 内容生成
     * @param {number} chapterId - 章节 ID
     * @returns {Promise<object>} - 更新后的章节信息 (符合 ChapterRead schema)
     */
    generateChapterScenes = async (chapterId) => {
        return apiClient.post(`/chapter/${chapterId}/generate_scenes`);
    };
    /**
     * 触发指定场景的 RAG 内容生成
     * @param {number} sceneId - 场景 ID
     * @returns {Promise<object>} - 更新后的场景信息 (符合 SceneRead schema)
     */
    generateSceneRAG = async (sceneId) => {
        return apiClient.post(`/scenes/${sceneId}/generate_rag`);
    };
    /**
     * 触发指定章节 内容生成
     * @param {number} chapterId - 章节 ID
     * @returns {Promise<object>} - 更新后的章节信息 (符合 ChapterRead schema)
     */
    generateChapterContent = async (chapterId) => {
        return apiClient.post(`/chapter/${chapterId}/generate`);
    };
}

const generationAPI = new GenerationAPI();
export {generationAPI};